import os
import django
from collections import defaultdict
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from random import randint, sample
import time
import pickle
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib.auth.models import User
from docsearch.models import Document, Tag, Topic, Section, Request, Searcher, Author, Country, Comment

ROOT = os.path.dirname(os.path.abspath(__file__))

def generate_tags(number):
    start = time.time()
    DICTIONARY_PATH = os.path.join(ROOT, 'search_models/unique_words.pickle')
    with open(DICTIONARY_PATH, 'rb') as f:
        dictionary = pickle.load(f)

    if number > len(dictionary): number = len(dictionary)
    tag_names = map(lambda x: x[0], sorted(list(dictionary.items()), key=lambda item: -item[1])[:number])
    for name in tag_names:
        tag = Tag(tag_name=name)
        try:
            tag.save()
        except IntegrityError:
            print('Tag with name %s is already exist' % name)
    print("Generated %d tags in %f time" %(number, time.time() - start))

'''заполняем таблицу секций с уникальными именами, ловим ошибку если добавляется уже существующее имя'''
def add_sections(sections):
    for name in sections:
        section = Section(section_name=name)
        try:
            section.save()
        except IntegrityError:
            print('Section with name %s is already exist' % name)

def add_topics(section_topics):
    for s_name, t_names in section_topics.items():
        try:
            section = Section.objects.get(section_name=s_name)
        except ObjectDoesNotExist:
            print('Section with name %s does not exist' % s_name)

        for t_name in t_names:
            try:
                section.topic_set.create(topic_name=t_name)
            except IntegrityError:
                print('Topic with name %s is already exist' % t_name)


def add_countries():
    COUNTRIES_PATH = os.path.join(ROOT, 'search_models/countries.txt')
    with open(COUNTRIES_PATH, 'r') as file:
        for line in file:
            index = line.find('|')
            name = line[index + 1:-1]
            country = Country(country_name=name)
            try:
                country.save()
            except IntegrityError:
                print('Country with name %s is already exist' % name)


def add_authors(authors):
    start = time.time()
    country_objects_count = Country.objects.count()
    for name in authors:
        rand_id = randint(1, country_objects_count)
        country = Country.objects.get(id=rand_id)
        #print(country.country_name)
        author = Author(author_name=name, country=country)
        try:
            author.save()
        except IntegrityError:
            print("Author with name %s is already exist" % name)
    print("Added authors in %f time" %(time.time() - start))

def load_authors():
    AUTHORS_PATH = os.path.join(ROOT, 'search_models/authors.pickle')
    with open(AUTHORS_PATH, 'rb') as f:
        authors = pickle.load(f)
        return authors.keys()


def generate_searchers(amount):
    start = time.time()
    searchers = []
    country_objects_count = Country.objects.count()
    for i in range(1,amount + 1):
        num_of_visits = randint(1, 1000)
        num_of_requests = randint(1, 10000)
        username = "Name" + str(i)
        country_id = randint(1, country_objects_count)
        country = Country.objects.get(id=country_id)
        searchers.append(Searcher(num_of_requests=num_of_requests, num_of_visits=num_of_visits,
                                  user=User.objects.create_user(username=username), country=country))
    #print(searchers)
    #увеличивает скорость записи в 2 раза
    Searcher.objects.bulk_create(searchers)
    print("Generated %d searchers in %f time" %(amount, time.time() - start))


def generate_requests(amount):
    start = time.time()
    existing_searcher_ids = list(map(lambda x: x.id, Searcher.objects.filter()))
    searcher_objects_count = Searcher.objects.count()
    #print(existing_searcher_ids)
    requests = []
    for i in range(1, amount + 1):
        searcher_index = randint(0, len(existing_searcher_ids) - 1)
        searcher_id = existing_searcher_ids[searcher_index]
        request_text = "RequestText" + str(i)
        try:
            requests.append(Request(user=User.objects.get(id=searcher_id),
                                    request_text=request_text, created_at=timezone.now()))
        except ObjectDoesNotExist:
            #print("Does not exist id:", searcher_id)
            pass

    Request.objects.bulk_create(requests)
    print("Generated %d requests in %f time" %(len(requests), time.time() - start))


'''associate different number of comments with amount number of documents'''
def generate_document_comments(amount):
    existing_document_ids = list(map(lambda x: x.id, Document.objects.filter()))
    for i in range(1, amount + 1):
        document_index = randint(0, len(existing_document_ids) - 1)
        document_id = existing_document_ids[document_index]
        try:
            document = Document.objects.get(id=document_id)
        except ObjectDoesNotExist:
            print("Does not exist")
        else:
            num_comments = randint(1, 10)
            for j in range(1, num_comments + 1):
                comment_text = "Comment" + str(j)
                comment = Comment(content_object=document, comment_text=comment_text)
                comment.save()


def generate_documents(amount):
    start = time.time()

    topics_dict = defaultdict(Topic)
    for topic in Topic.objects.filter():
        topics_dict[topic.id] = topic

    authors_dict = defaultdict(Author)
    for author in Author.objects.filter():
        authors_dict[author.id] = author

    tags_dict = defaultdict(Tag)
    for tag in Tag.objects.filter():
        tags_dict[tag.id] = tag

    existing_author_ids = list(authors_dict.keys())
    existing_tag_ids = list(tags_dict.keys())
    existing_topic_ids = list(topics_dict.keys())

    documents = []
    existing_document_ids = [document.id for document in Document.objects.filter()]
    for i in range(1, amount + 1):
        title = "title" + str(i)
        description = "description" + str(i)
        citation_index = randint(0, 100)
        published_at = timezone.now()
        archive_url = "http://arxiv.org/abs/" + str(randint(1, 1000))
        topic_ids = sample(existing_topic_ids, 1)
        document = Document(title=title, description=description, published_at=published_at,
                            archive_url=archive_url, citation_index=citation_index, topic=topics_dict[topic_ids[0]])
        documents.append(document)

    Document.objects.bulk_create(documents)

    new_docs = Document.objects.exclude(id__in=existing_document_ids)

    for document in new_docs:
        num_authors = randint(1, 10)
        num_tags = randint(1, 10)

        #topic_ids = sample(existing_topic_ids, 1)
        author_ids = sample(existing_author_ids, num_authors)
        tag_ids = sample(existing_tag_ids, num_tags)

        #document.topic = topics_dict[topic_ids[0]]
        document.authors.add(*author_ids)
        document.tags.add(*tag_ids)
        document.save()

    print("Generated %d documents in %f time" % (amount, time.time() - start))
'''

def generate_documents(amount):
    start = time.time()

    topics_dict = defaultdict(Topic)
    for topic in Topic.objects.filter():
        topics_dict[topic.id] = topic

    authors_dict = defaultdict(Author)
    for author in Author.objects.filter():
        authors_dict[author.id] = author

    tags_dict = defaultdict(Tag)
    for tag in Tag.objects.filter():
        tags_dict[tag.id] = tag

    existing_author_ids = list(authors_dict.keys())
    existing_tag_ids = list(tags_dict.keys())
    existing_topic_ids = list(topics_dict.keys())

    for i in range(1, amount + 1):
        title = "title" + str(i)
        description = "description" + str(i)
        citation_index = randint(0, 100)
        published_at = timezone.now()
        archive_url = "http://arxiv.org/abs/" + str(randint(1, 1000))
        document = Document(title=title, description=description, published_at=published_at,
                            archive_url=archive_url, citation_index=citation_index)
        document.save()

        num_authors = randint(1, 10)
        num_tags = randint(1, 10)

        topic_ids = sample(existing_topic_ids, 1)
        author_ids = sample(existing_author_ids, num_authors)
        tag_ids = sample(existing_tag_ids, num_tags)

        document.topic = topics_dict[topic_ids[0]]
        document.authors.add(*author_ids)
        document.tags.add(*tag_ids)


    print("Generated %d documents in %f time" % (amount, time.time() - start))

'''
sections = ["Physics",
            "Mathematics",
            "Computer Science",
            "Quantitative Biology",
            "Quantitative Finance",
            "Statistics"]

section_topics = {"Physics": ["nucl-th", "hep-lat", "nucl-ex", "hep-ph", "quant-ph", "hep-th", "astro-ph", "hep-ex",
                              "cond-mat", "physics", "nlin", "math-ph", "gr-qc"],
                  "Statistics": ["stat"],
                  "Quantitative Biology": ["q-bio"],
                  "Quantitative Finance": ["q-fin"],
                  "Mathematics": ["math"],

                  "Computer Science": ["cs"]
                  }

if __name__ == '__main__':
    #add_sections(sections)
    #generate_tags(100000)
    #add_topics(section_topics)
    #add_countries()
    #add_authors(load_authors())
    #generate_documents(20000)
    #generate_searchers(100000)
    #generate_requests(20000)
    generate_document_comments(10000)
    pass

