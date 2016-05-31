import re
import requests
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
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

def sources(request):
    srclist = Source.objects.all()
    context = {}
    for cls in ('personal', 'repo', 'journal', 'blog'):
        context[cls] = [src for src in srclist if src.sourcetype == cls]
    return render(request, 'website/sourceslist.html', context)

@staff_member_required
@csrf_exempt
def sourcesadmin(request):
    if request.method == 'POST':
        try:
            src = Source.objects.get(source_id=request.POST.get('source_id'))
            if request.POST.get('new_url'):
                src.url = request.POST.get('new_url')
                src.status = 1
            elif request.POST.get('mark_gone'):
                src.status = 410
            src.save()
            return HttpResponse('OK')
        except Exception as e:
            return HttpResponse('Oh dear: {}'.format(e))

    srclist = Source.objects.all()
    context = {
        'moved': [src for src in srclist if src.status == 301],
        'gone': [src for src in srclist if src.status == 404],
        'broken': [src for src in srclist if src.status not in (0,1,301,404)]
    }
    for src in context['moved'][:40]:
        try:
            r = requests.head(src.url, allow_redirects=True, timeout=5)
            src.redir_url = r.url
        except Exception as e:
            src.redir_url = '[requests error: {}]'.format(e)
    return render(request, 'website/sourcesadmin.html', context)

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

