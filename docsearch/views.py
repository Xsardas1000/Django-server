from django.shortcuts import render
from django.http import Http404, JsonResponse
from django.core.cache import cache
from django.utils import timezone
from .models import Author, Document, Comment, Topic, Request, Result, Searcher
from .forms import SearchFileForm, SearchLineForm, PersonInfoForm
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from .vec_search import get_articles, process_pdf_file, process_txt_file
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
import os
import pickle
import django
import datetime

os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

ROOT = os.path.dirname(os.path.abspath(__file__))


@login_required
def home(request):
    searcher = Searcher.objects.get(user__id=request.user.id)
    print("Logged in user %s" % searcher.user)
    searcher.num_of_visits += 1
    searcher.save()
    # return  render(request, 'docsearch/home.html')
    return render(request, 'docsearch/main_page.html')


def about(request):
    return render(
        request, 'docsearch/about.html'
    )


@login_required
def personal(request):
    searcher = Searcher.objects.get(user__id=request.user.id)
    print(searcher.user)
    form = PersonInfoForm()

    return render(
        request, 'docsearch/personal.html',
        {
            'form': form,
            'searcher': searcher
        }
    )


@login_required
def topics(request):
    SECTIONS_CHART_PATH = os.path.join(ROOT, 'meta_archive_info/sections_chart.pickle')
    with open(SECTIONS_CHART_PATH, 'rb') as f:
        sections = pickle.load(f)

    sections_list = [(x[0], x[1]) for x in sections.items()]
    print(sections_list)
    return render(
        request, 'docsearch/topics.html',
        {'sections': sections_list}
    )


def main_view(request):
    return render(
        request, 'docsearch/main_page.html'
    )


def handle_uploaded_file(f):
    # process_pdf_file(f.name)
    return process_txt_file(f.name)


@login_required
def scroll_ajax(request):
    add_num = 3
    request_id = request.GET.get('value')
    print("request_id:", request_id)

    results = Result.objects.filter(request__id=request_id, shown=False).order_by('prior_value')[:add_num]
    articles = make_articles_list(results)
    #print(articles[0]['published_at'])
    data = {
        'value': articles
    }
    return JsonResponse(data)


'''формируем список статей, которые будем выдавать при исходном запросе'''
def make_articles_list(results):
    articles = []
    for result in results:
        doc_id = result.doc_id
        result.shown = True
        result.save()
        print(doc_id)
        try:
            document = Document.objects.get(archive_id=doc_id)
        except ObjectDoesNotExist:
            print("Document with doc_id %s does not exist" % doc_id)
        else:
            articles.append({'weight': result.weight,
                             'title': document.title,
                             'topic': document.topic.topic_name,
                             'published_at': str(document.published_at)[:10],
                             'archive_id': document.archive_id,
                             'description': document.description,
                             'citation_index': document.citation_index,
                             'prior_value': result.prior_value,
                             'id': document.id
                             })
    return articles

@login_required
def main_search(request):

    searcher, state = Searcher.objects.get_or_create(user__id=request.user.id)

    form = SearchLineForm()
    uploaded_file_name = None
    text_request = ""
    request_id = None
    articles = None

    num_of_found_docs = 100
    num_of_first_part = 10

    if request.method == 'POST':
        searcher.num_of_requests += 1
        searcher.save()

        check_ok = False
        file_request = False
        if 'text_button' in request.POST:
            form = SearchLineForm(request.POST)
            if form.is_valid():
                check_ok = True
                text_request = form.cleaned_data['text_request']
                print(text_request)
            else:
                print("wrong line form")
        elif 'file_button' in request.POST:
            form = SearchFileForm(request.POST, request.FILES)
            if form.is_valid():
                check_ok = True
                file_request = True
                file = request.FILES['file_request']
                fs = FileSystemStorage()
                filename = fs.save(file.name, file)
                uploaded_file_name = file.name
                #uploaded_file_url = fs.url(filename)
                text_request = handle_uploaded_file(file)
            else:
                print("wrong file form")
                form = SearchFileForm()
        if check_ok:
            found_docs, related_themes = get_articles(text_request, num_docs=num_of_found_docs)
            print("found", len(found_docs))

            for theme in related_themes:
                print(theme[0], theme[1])

            '''сохраняем в базу данных новую запись о поступившем запросе'''
            new_request = Request(searcher=searcher, created_at=timezone.now())
            new_request.save()
            request_id = new_request.id
            print("Request id = %d" % request_id)

            '''сохраняем в базу данных все id документов, выданных в ответ на запрос с доп. информацией'''
            for i, (doc_id, weight) in enumerate(found_docs):
                result = Result(request=new_request, doc_id=doc_id, prior_value=i, weight=weight, shown=False)
                result.save()

            results = Result.objects.filter(request__id=request_id, shown=False).order_by('prior_value')[:num_of_first_part]
            articles = make_articles_list(results)

            if file_request:
                text_request = ""

    return render(
        request, 'docsearch/search.html',
        {'form': form,
         'articles': articles,
         'uploaded_file_name': uploaded_file_name,
         'text_request': text_request,
         'request_id': request_id,
         'searcher_id': searcher.id
         }
    )


def author_like_ajax(request):
    print("Ajax")
    author_id = request.GET.get('value')
    print(author_id)
    data = {}
    try:
        author = Author.objects.get(id=author_id)
    except ObjectDoesNotExist:
        print("Author with id %d does not exist" % author_id)
    else:
        author.review_index += 1
        author.save()
        data = {
            'value': author.review_index
        }
    return JsonResponse(data)


def author_list(request):
    authors = Author.objects.all()[:30]
    auths = []
    for author in authors:
        auths.append({"author_name": author.author_name,
                      "country": author.country,
                      "id": author.id,
                      "review_index": author.review_index,
                      "num_of_docs": author.document_set.count()
                      })
    return render(
        request, 'docsearch/author_list.html',
        {'authors': auths}
    )


def document_list(request):
    # documents = list(Document.objects.order_by('citation_index').reverse()[:10])
    # document_ids = [doc.id for doc in documents]


    documents = Document.objects.all().annotate(count=models.Count('authors')).order_by('citation_index').reverse()[:10]

    # authors = list(Author.objects.filter(document__id__in=document_ids))
    # author_ids = [author.id for author in authors]
    # count = Document.objects.all().annotate(authors=models.Count('author'))


    docs = []
    for doc in documents:
        # authors = doc.authors.all()
        # auths = []
        # for author in authors[:5]:
        # auths.append({"author_name": author.author_name, "id": author.id})
        print(doc.count)
        docs.append({"title": doc.title, "published_at": doc.published_at, "id": doc.id, "count": doc.count,
                     "topic": doc.topic})

    return render(
        request, 'docsearch/document_list.html',
        {'documents': docs}
    )


def document_detail(request, document_id):
    searcher, state = Searcher.objects.get_or_create(user__id=request.user.id)
    print(searcher.user)

    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        raise Http404('No such document')

    maxlimit = 20
    if request.is_ajax():

        type = request.GET.get('type')
        if type == "check":
            comment_id = request.GET.get('value')
            searcher_comment_ids = [k.id for k in searcher.comment_set.all()]
            permission = "No"
            print(comment_id)
            print(searcher_comment_ids)
            if int(comment_id) in searcher_comment_ids:
                permission = "Yes"

            data = {
                'value': "test",
                'permission': permission
            }
            return JsonResponse(data)
        else:
            text = request.GET.get('value')

            if len(text) > maxlimit:
                data = {
                    'value': {}
                }
                return JsonResponse(data)
            comment = Comment(searcher=searcher, content_object=document, comment_text=text,
                              published_at=timezone.now())
            comment.save()
            print(str(comment.published_at)[:20])

            data = {
                'value': {
                    'comment_text': comment.comment_text,
                    'id': comment.id,
                    'published_at': str(comment.published_at)[:19]
                }
            }
            return JsonResponse(data)

    # get last 30 comments
    comments = document.comments.all().order_by('published_at').reverse()[:30]
    authors = document.authors.all()

    return render(
        request, 'docsearch/document_detail.html',
        {'document': document,
         'comments': comments,
         'searcher_name': searcher.user,
         }
    )


def author_detail(request, author_id):
    try:
        author = Author.objects.get(id=author_id)
    except Author.DoesNotExist:
        raise Http404('No such author')

    # получим список документов, написанных автором и будем выводить топ 10 из них
    documents = author.document_set.all()[:10]
    docs = []
    for doc in documents:
        docs.append({"id": doc.id, "title": doc.title})

    return render(
        request, 'docsearch/author_detail.html',
        {'author': author, 'documents': docs}
    )
