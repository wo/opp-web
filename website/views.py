from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Doc

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

# user management

from django.contrib.auth import views

def change_password(request):
    template_response = views.password_change(request)
    # Do something with `template_response`
    return template_response
