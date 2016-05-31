from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    #url(r'^qa/$', views.qa, name='qa'),
    url(r'^t/(?P<topic_name>\w+)/?$', views.topic, name='topic'),
    url(r'^sources$', views.sources, name='sources'),
    url(r'^sourcesadmin$', views.sourcesadmin, name='sourcesadmin'),
    url(r'^edit-source$', views.edit_source, name='edit_source'),
]

# error handlers

def err404(request):
    return HttpResponse('404')
    
def err403(request):
    return HttpResponse('403')

def err500(request):
    return HttpResponse('500')
