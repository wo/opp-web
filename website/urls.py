from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^page/(?P<page>\d+)$', views.index, name='index_page'),
    #url(r'^qa/$', views.qa, name='qa'),
    url(r'^t/(?P<topic_name>\w+)$', views.topic, name='topic'),
    url(r'^sources$', views.sources, name='sources'),
    url(r'^sourcesadmin$', views.sourcesadmin, name='sourcesadmin'),
    url(r'^edit-source$', views.edit_source, name='edit_source'),
    url(r'^edit-doc$', views.edit_doc, name='edit_doc'),
]

