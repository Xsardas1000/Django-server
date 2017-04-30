from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    #url('^', include('django.contrib.auth.urls'), {'template_name': 'docsearch/login.html'}),
    url('^main/$', views.main_view, name='main_view'),
    url('^search/$', views.main_search, name='main_search'),
    url('^author/list/$', views.author_list, name='author_list'),
    url('^document/list/$', views.document_list, name='document_list'),
    url('^document/(?P<document_id>\d+)/$', views.document_detail, name='document_detail'),
    url('^author/(?P<author_id>\d+)/$', views.author_detail, name='author_detail'),
    url('^topics/', views.topics, name='topics'),
    url('^about/', views.about, name='about'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)