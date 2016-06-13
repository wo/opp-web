import re
import requests
import json
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.timezone import utc
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from .models import Doc, Source
from .forms import SourceForm, DocEditForm

def index(request, page=1):
    doclist = Doc.objects.all()
    if not request.user.is_staff:
        doclist = doclist.filter(hidden=False)
    return list_docs(request, doclist, page=page)

def topic(request, topic_name, min_strength=50, page=1):
    doclist = Doc.objects.filter(
        cats__label=topic_name,
        doc2cat__strength__gte=min_strength
    )
    if not request.user.is_staff:
        doclist = doclist.filter(hidden=False)
    return list_docs(request, doclist, topic=topic_name, page=page)

def list_docs(request, doclist, topic=None, page=1):
    paginator = Paginator(doclist, 30) # 30 per page
    try:
        MAX_PAGE = 10
        page = page if int(page) <= MAX_PAGE else 1
        docs = paginator.page(page)
    except:
        # no such page
        raise
        docs = paginator.page(1)
    for doc in docs:
        doc.deltadate = seconds_since(doc.found_date)
        doc.short_url = short_url(doc.url)
    context = { 'docs': docs, 'topic': topic }
    if request.user.is_staff:
        context['editform'] = DocEditForm()
    return render(request, 'website/doclist.html', context)

def seconds_since(date):
    if not date:
        return 1000000
    now = datetime.utcnow().replace(tzinfo=utc)
    timediff = now - date
    return timediff.total_seconds()

def short_url(url):
    if not url:
        return '#'
    url = re.sub(r'^https?://', '', url)
    if len(url) > 80:
        url = url[:38] + '...' + url[-39:]
    #url = re.sub(r'(\.\w+)$', r'<b>\1</b>', url)
    return url
    
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
            if request.POST.get('action') == 'get_new_url':
                try:
                    r = requests.head(src.url, allow_redirects=True, timeout=5)
                    return HttpResponse(r.url)
                except Exception as e:
                    return HttpResponse('[requests error: {}]'.format(e))
            elif request.POST.get('action') == 'change_url':
                src.url = request.POST.get('new_url')
                src.status = 1
                src.save()
                return HttpResponse('URL changed')
            elif request.POST.get('action') == 'remove':
                src.delete()
                return HttpResponse('Source deleted')
            return HttpResponse('Unknown action')
        except Exception as e:
            return HttpResponse('Oh dear: {}'.format(e))

    srclist = Source.objects.all()
    context = { 
        'sourcetypes': [
            { 
                'heading': 'Personal pages', 
                'sources': [src for src in srclist if src.sourcetype == 'personal'],
            },
            { 
                'heading': 'Repositories', 
                'sources': [src for src in srclist if src.sourcetype == 'repo'],
            },
            { 
                'heading': 'Open Access Journals', 
                'sources': [src for src in srclist if src.sourcetype == 'journal'],
            },
            { 
                'heading': 'Weblogs', 
                'sources': [src for src in srclist if src.sourcetype == 'blog'],
            },
        ]
    }
    return render(request, 'website/sourcesadmin.html', context)

def qa(request):
    return render(request, 'website/qa.html')

# edit doc popup form:
@staff_member_required
def edit_doc(request): 
    try:
        doc = Doc.objects.get(doc_id=request.POST['doc_id'])
    except:
        return HttpResponse('Doc object does not exist')
    doc_was_hidden = doc.hidden
    form = DocEditForm(instance=doc, data=request.POST)
    if form.is_valid():
        if form.cleaned_data.get('hidden'):
            # 'Discard Entry' was clicked -- remove doc from db:
            doc.delete()
            return HttpResponse('OK, entry deleted')
        else:
            doc = form.save(commit=False)
            if doc_was_hidden:
                doc.found_date = datetime.utcnow().replace(tzinfo=utc)
            doc.save()
            return HttpResponse('OK, entry updated')
    else:
        return HttpResponse('invalid form')
        
# bookmarklet form for adding source pages:
@staff_member_required
def edit_source(request):
    form = SourceForm(request.POST or request.GET)

    if request.method == 'POST' and form.is_valid():
        src = form.save(commit=False)
        if form.cleaned_data['source_type'] == 'blog':
            # register new blog subscription on superfeedr:
            from superscription import Superscription
            ss = Superscription(settings.SUPERFEEDR_USER, 
                                password=settings.SUPERFEEDR_PASSWORD)
            try:
                callback = '/superfeedr_ping/{}'.format(src.source_id)
                assert ss.subscribe(hub_topic=src.url, hub_callback=callback)
            except:
                msg = 'could not register blog on superfeedr!'
                if ss.response.status_code:
                    msg += ' status {}'.format(ss.response.status_code)
                else:
                    msg += ' no response from superfeedr server'
                return HttpResponse(msg)
        src.save()
        return HttpResponse('OK')
        
    context = { 'form': form, 'related': [] }
    if request.GET.get('default_author'):
        surname = request.GET.get('default_author').split()[-1]
        context['related'].extend(Source.objects.filter(default_author__endswith=surname))
    return render(request, 'website/edit_source.html', context)

# receive notifications from superfeedr about new blog posts:
def superfeedr_ping(request, source_id):
    try:
        src = Source.objects.get(pk=source_id)
    except:
        return HttpResponse('Unknown source!')
    try:
        feed = json.loads(request.body.decode("utf-8"))
        status = feed['status']['code']
        #source_url = feed['status']['feed']
        #app.logger.debug('superfeedr notification for {} (status {})'.format(source_url, status))
        #app.logger.debug(json.dumps(feed, indent=4, separators=(',',': ')))
        if status == '0' and not feed.get('items'):
            #app.logger.debug('superfeedr says feed is broken')
            return HttpResponse('Got it: feed is broken')
    except:
        return HttpResponse('Don\'t know how to handle this request')

    posts = []
    for item in feed.get('items', []):
        post = Doc(
            filetype = 'blogpost',
            source_url = src.url,
            source_name = src.name,
            source_id = source_id,
            author = src.default_author,
            url = item.get('permalinkUrl') or item.get('id'),
            title = item.get('title',''),
            content = item.get('content') or item.get('summary'),
            status = 0,
        )
        if not post.url or not post.title:
            #app.logger.error('ignoring superfeedr post without url or title')
            continue
        # RSS feeds sometimes only contain a summary of posts, and
        # often don't contain the author name on group blogs. So we'll
        # have to fetch content and author from the actual post url.
        posts.append(post)

    if not posts:
        #app.logger.warn('no posts to save')
        return HttpResponse('No posts received')

    return HttpResponse('OK')

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

