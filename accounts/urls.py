from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^signup_complete/$', views.signup_complete, name='signup_complete'),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login', 
        kwargs={'template_name': 'accounts/login.html'}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout',
        kwargs={'next_page': '/'}),
]
