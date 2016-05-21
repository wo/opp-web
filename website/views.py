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

def sources(request):
    srclist = Source.objects.all()
    #query = '''SELECT S.*, COUNT(document_id) AS num_papers
    #    FROM sources S
    #    LEFT JOIN links USING (source_id)
    #    LEFT JOIN locations L USING (location_id)
    #    LEFT JOIN documents D USING (document_id)
    #    WHERE D.document_id IS NULL OR (L.spamminess < 0.5 AND D.meta_confidence > 0.5)
    #    GROUP BY S.source_id
    #    ORDER BY S.default_author, S.name
    context = {}
    for cls in ('personal', 'repo', 'journal', 'blog'):
        context[cls] = [src for src in srclist if src.sourcetype == cls]
    return render(request, 'website/sourceslist.html', context)

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

