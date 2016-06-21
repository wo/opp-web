import re
import requests
from collections import defaultdict
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.timezone import utc
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Doc, Source
from .forms import SourceForm, DocEditForm
from django.utils.feedgenerator import Atom1Feed
from feedhandler import superfeedr

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

    blogsources = []
    subscribed_urls = superfeedr.subscribed_urls()
    for src in srclist:
        if src.sourcetype == 'blog':
            src.subscribed = (src.url in subscribed_urls)
            if src.url in subscribed_urls:
                subscribed_urls.remove(src.url)
            blogsources.append(src)
    for url in subscribed_urls:
        # any subscribed urls that aren't in our db:
        src = Source(url=url, name=url, sourcetype='blog')
        src.subscribed = True
        blogsources.append(src)

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
                'sources': blogsources, 
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
        src = form.save()
        if form.cleaned_data['sourcetype'] == 'blog':
            # register new blog subscription on superfeedr:
            callback = request.build_absolute_uri(reverse('new_post', args=[src.source_id]))
            try:
                superfeedr.subscribe(url=src.url, callback_url=callback)
            except Exception as e:
                msg = 'could not register blog on superfeedr! {}'.format(e)
                return HttpResponse(msg)
        return HttpResponse('OK')
        
    context = { 'form': form, 'related': [] }
    if request.GET.get('default_author'):
        surname = request.GET.get('default_author').split()[-1]
        context['related'].extend(Source.objects.filter(default_author__endswith=surname))
    return render(request, 'website/edit_source.html', context)

# atom feed:
def atom_feed(request):
    feed = Atom1Feed(
        title='Philosophical Progress',
        link='http://www.philosophicalprogress.org/',
        description='New online papers in philosophy',
        feed_url='http://www.philosophicalprogress.org/feed.xml'
    )
    docs = Doc.objects.filter(
        status=1,
        hidden=False,
        found_date__lt=datetime.now().date(),
        found_date__gte=datetime.now().date()-timedelta(days=7)
    )
    
    docs_per_day = defaultdict(list)
    for doc in docs:
        daystr = doc.found_date.strftime('%Y%m%d') # for sorting
        docs_per_day[daystr].append(doc)

    for k in sorted(docs_per_day.keys(), reverse=True):
        day_text = ''
        day_docs = sorted(docs_per_day[k], key=lambda doc: (doc.is_blogpost, doc.authors))
        for doc in day_docs:
            authors = doc.source_name if doc.is_blogpost else doc.authors
            day_text += '<b>{}: <a href="{}">{}</a></b>'.format(authors, doc.url, doc.title)
            day_text += ' ({}, {} words)<br />'.format(doc.filetype, doc.numwords)
            day_text += ' <div>{}</div><br />\n'.format(doc.abstract)
        d = day_docs[0].found_date
        pubdate = datetime(d.year, d.month, d.day, 23, 59)
        feed.add_item(
            author = 'Philosophical Progress',
            title = 'Articles and blog posts found on {}'.format(d.strftime('%d %B %Y')),
            link = 'http://www.philosophicalprogress.org/',
            description = day_text, 
            pubdate = pubdate,
            updateddate = pubdate
        )

    # TODO: cache?
    return HttpResponse(feed.writeString('utf-8'), content_type=feed.mime_type)

_illegal_xml_chars_RE = re.compile(u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]')
def escape_illegal_chars(val, replacement='?'):
    return _illegal_xml_chars_RE.sub(replacement, val)    


# error handlers

def err404(request):
    return HttpResponse('404')
    
def err403(request):
    return HttpResponse('403')

def err500(request):
    return HttpResponse('500')

