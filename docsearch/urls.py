from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    url('^main/$', views.main_view, name='main_view'),
    url('^search/$', views.main_search, name='main_search'),
    url('^search/scroll/$', views.scroll_ajax, name='scroll_ajax'),

    url('^author/list/$', views.author_list, name='author_list'),
    url('^author/list/likes/$', views.author_like_ajax, name='author_like_ajax'),

    url('^document/list/$', views.document_list, name='document_list'),
    url('^document/(?P<document_id>\d+)/$', views.document_detail, name='document_detail'),
    url('^author/(?P<author_id>\d+)/$', views.author_detail, name='author_detail'),
    url('^topics/', views.topics, name='topics'),
    url('^about/', views.about, name='about'),
    url('^home/', views.home, name='home'),
    url('^personal/', views.personal, name='personal'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)