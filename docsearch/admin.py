from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Document, Tag, Topic, Section, Request, Searcher, Author, Country, Comment

admin.site.register(Document)
admin.site.register(Tag)
admin.site.register(Topic)
admin.site.register(Section)
admin.site.register(Request)
admin.site.register(Searcher)
admin.site.register(Author)
admin.site.register(Country)
admin.site.register(Comment)



