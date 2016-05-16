import re
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Doc, Source
from .forms import SourceForm

def index(request, page=1):
    doclist = Doc.objects.all()
    return list_docs(request, doclist, page=page)

def topic(request, topic_name, min_strength=50, page=1):
    doclist = Doc.objects.filter(
        cats__label=topic_name,
        doc2cat__strength__gte=min_strength
    )
    return list_docs(request, doclist, topic=topic_name, page=page)

def list_docs(request, doclist, topic=None, page=1):
    paginator = Paginator(doclist, 30) # 30 per page
    try:
        docs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page:
        docs = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results:
        docs = paginator.page(paginator.num_pages)
    context = { 'docs': docs, 'topic': topic }
    return render(request, 'website/doclist.html', context)

def qa(request):
    return render(request, 'website/qa.html')

# bookmarklet form:

def edit_source(request):
    form = SourceForm(request.POST or request.GET)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return HttpResponse('OK')
    context = { 'form': form, 'related': [] }
    if request.GET.get('default_author'):
        surname = request.GET.get('default_author').split()[-1]
        context['related'].extend(Source.objects.filter(default_author__endswith=surname))
    return render(request, 'website/edit_source.html', context)

# user management

from django.contrib.auth import views

def change_password(request):
    template_response = views.password_change(request)
    # Do something with `template_response`
    return template_response

# error handlers

def err404(request):
    return HttpResponse('404')
    
def err403(request):
    return HttpResponse('403')

def err500(request):
    return HttpResponse('500')

