from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^new-post/(?P<source_id>\d+)$', views.new_post, name='new_post'),
    url(r'^subscribe/(?P<source_id>\d+)$', views.subscribe, name='subscribe'),
    url(r'^unsubscribe/(?P<source_id>\d+)$', views.unsubscribe, name='unsubscribe'),
]
