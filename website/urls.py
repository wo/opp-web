from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    #url(r'^qa/$', views.qa, name='qa'),
    url(r'^t/(?P<topic_name>\w+)/$$', views.topic, name='topic'),
    url(r'^edit-source$$', views.edit_source, name='edit_source'),
]
