from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, Http404, JsonResponse
from django.http import HttpResponse
from .models import Author, Document, Comment, Topic
from .forms import CommentForm, SearchFileForm, SearchLineForm, TopicForm
from django.db import models
from .vec_search import get_articles, process_pdf_file, process_txt_file
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage



def about(request):
    return render(
        request, 'docsearch/about.html'
    )


def topics(request):
    topic = "q-fin"
    topic_names = [topic.topic_name for topic in Topic.objects.all()]
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            print(topic)
            form = TopicForm()

    else:
        form = TopicForm()

    #находим документы по выбранной секции, топ 20
    #documents = Document.objects.filter(topic__topic_name=topic)[:20]
    documents = Document.objects.filter(topic__topic_name=topic)[:20].annotate(count=models.Count('authors'))

    print(len(documents))

    return render(
        request, 'docsearch/topics.html',
        {'form': form, 'documents': documents, 'topic_names': topic_names}
    )


def main_view(request):
    return render(
        request, 'docsearch/main_page.html'
    )


def handle_uploaded_file(f):
    #process_pdf_file(f.name)
    return process_txt_file(f.name)

count = 5
articles = []

def main_search(request):

    global articles
    form = SearchLineForm()
    uploaded_file_name = ""
    text_request = ""
    if request.is_ajax():

        global count
        print(count)
        print("Ajax")
        #value = request.GET.get('value')
        #print("value:", value)
        #print(type(value))
        print(len(articles))
        data = {
             'value': articles[count: count + 3],
             'count': count
        }
        count = count + 3
        return JsonResponse(data)

##memcache/ redis / mySQL
    if request.method == 'POST':
        count = 5
        if 'text_button' in request.POST:
            form = SearchLineForm(request.POST)
            if form.is_valid():
                text_request = form.cleaned_data['text_request']
                print(text_request)
                articles = get_articles(text_request)
                print("found", len(articles))
            else:
                print("wrong")
        elif 'file_button' in request.POST:
            print("file_button")
            form = SearchFileForm(request.POST, request.FILES)
            if form.is_valid():
                print("file_button")
                file = request.FILES['file_request']
                fs = FileSystemStorage()
                filename = fs.save(file.name, file)
                uploaded_file_name = file.name
                uploaded_file_url = fs.url(filename)
                articles = get_articles(handle_uploaded_file(file))
            else:
                print("wrong file form")
                form = SearchFileForm()
    else:
        articles = []

    return render(
        request, 'docsearch/search.html',
        {'form': form, 'articles': articles[:count], 'uploaded_file_name': uploaded_file_name, 'text_request': text_request}
    )


def author_list(request):
    authors = Author.objects.all()[:30]
    auths = []
    for author in authors:
        auths.append({"author_name": author.author_name, "country": author.country, "id": author.id,
                      "review_index": author.review_index})
    return render(
        request, 'docsearch/author_list.html',
        {'authors': auths}
    )

def document_list(request):
    #documents = list(Document.objects.order_by('citation_index').reverse()[:10])
    #document_ids = [doc.id for doc in documents]


    documents = Document.objects.all().annotate(count=models.Count('authors')).order_by('citation_index').reverse()[:10]

    #authors = list(Author.objects.filter(document__id__in=document_ids))
    #author_ids = [author.id for author in authors]
    #count = Document.objects.all().annotate(authors=models.Count('author'))


    docs = []
    for doc in documents:
        #authors = doc.authors.all()
        #auths = []
        #for author in authors[:5]:
            #auths.append({"author_name": author.author_name, "id": author.id})
        print(doc.count)
        docs.append({"title": doc.title, "published_at": doc.published_at, "id": doc.id, "count": doc.count,
                     "topic": doc.topic})

    return render(
        request, 'docsearch/document_list.html',
        {'documents': docs}
    )

def document_detail(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        raise Http404('No such document')

    comments = document.comments.all()
    commts = []
    for comment in comments:
        commts.append({"comment_text": comment.comment_text})
    authors = document.authors.all()
    for author in authors:
        author.review_index += 1
        author.save()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment_text = form.cleaned_data['comment_text']
            comment = Comment(content_object=document, comment_text=comment_text)
            comment.save()
            form = CommentForm()

    else:
        form = CommentForm()

    return render(
        request, 'docsearch/document_detail.html',
        {'document': document,
         'comments': commts,
         'form': form
        }
    )

def author_detail(request, author_id):
    try:
        author = Author.objects.get(id=author_id)
    except Author.DoesNotExist:
        raise Http404('No such author')

    #получим список документов, написанных автором и будем выводить топ 10 из них
    documents = author.document_set.all()[:10]
    docs = []
    for doc in documents:
        docs.append({"id": doc.id, "title": doc.title})

    return render(
        request, 'docsearch/author_detail.html',
        {'author': author, 'documents': docs}
    )