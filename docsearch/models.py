from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation


class Section(models.Model):
    section_name = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def __str__(self):
        return self.section_name

class Topic(models.Model):
    section = models.ForeignKey(Section, blank=True, null=True)
    topic_name = models.CharField(max_length=200, unique=True, blank=True, null=True)

    def __str__(self):
        return self.topic_name


class Country(models.Model):
    country_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.country_name

class Author(models.Model):
    country = models.ForeignKey(Country, blank=True, null=True)

    author_name = models.CharField(max_length=50, unique=True, blank=True, null=True)
    citation_index = models.IntegerField(default=0)


    review_index = models.IntegerField(default=0)

    def __str__(self):
        return self.author_name

class Tag(models.Model):
    tag_name = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def __str__(self):
        return self.tag_name

class Searcher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    country = models.ForeignKey(Country, blank=True, null=True)

    #user_name = models.CharField(max_length=20)
    num_of_visits = models.IntegerField(default=0, db_index=True)
    num_of_requests = models.IntegerField(default=0, db_index=True)


class Request(models.Model):
    user = models.ForeignKey(User)

    request_text = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField()

    def __str__(self):
        return self.request_text


class Comment(models.Model):
    comment_text = models.CharField(max_length=200)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    published_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.comment_text

class Document(models.Model):
   topic = models.ForeignKey(Topic, on_delete=models.CASCADE, db_index=True)
   authors = models.ManyToManyField(Author)
   tags = models.ManyToManyField(Tag)

   #count = models.IntegerField(blank=True, null=True)

   title = models.CharField(max_length=200, blank=True, null=True)
   published_at = models.DateTimeField(blank=True, null=True)
   description = models.CharField(max_length=255, blank=True, null=True)
   citation_index = models.IntegerField(default=0, blank=True, null=True, db_index=True)
   archive_url = models.CharField(max_length=50, blank=True, null=True)

   #archive_id = models.CharField(max_length=20, unique=True)

   comments = GenericRelation(Comment)

   def __str__(self):
       return self.title



