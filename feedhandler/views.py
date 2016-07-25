import json
import logging
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from website.models import Source, Doc
from . import superfeedr

logger = logging.getLogger(__name__)

@csrf_exempt
def new_post(request, source_id):
    """
    superfeedr notification of new blog post(s), see
    https://documentation.superfeedr.com/schema.html#json
    
    RSS feeds sometimes only contain a summary of posts, and
    often don't contain the author name on group blogs. So we'll
    have to fetch content and author from the actual post url.
    """
    logger.info('notification: new blog post on source %s', source_id)
    msg = ''
    try:
        src = Source.objects.get(pk=source_id)
    except:
        return HttpResponse('Unknown source!')
    try:
        feed = json.loads(request.body.decode("utf-8"))
        status = int(feed['status']['code'])
        #source_url = feed['status']['feed']
        if settings.DEBUG:
            msg += 'notification for {} (status {})'.format(source_id, status)
            msg += '\n'+json.dumps(feed, indent=4, separators=(',',': '))+'\n'
            logger.debug(msg)
        if status != 200 and not feed.get('items'):
            src.status = status if status > 1 else 410
            msg += 'Got it: feed is broken'
            return HttpResponse(msg)
    except:
        return HttpResponse('Don\'t know how to handle this request')

    for item in feed.get('items', []):
        url = item.get('permalinkUrl') or item.get('id')
        if Doc.objects.filter(url=url).exists():
            # skip duplicate entry
            continue
        post = Doc(
            doctype = 'blogpost',
            source_url = src.url,
            source_name = src.name,
            source_id = source_id,
            authors = src.default_author,
            url = url, 
            title = item.get('title',''),
            content = item.get('content') or item.get('summary'),
            filetype = 'html',
            status = 0,
        )
        if not post.url or not post.title:
            #app.logger.error('ignoring superfeedr post without url or title')
            continue
        post.save()

    return HttpResponse(msg+'OK')

def subscribe(request, source_id):
    """
    subscribe to source on superfeedr
    """
    try:
        src = Source.objects.get(pk=source_id)
    except:
        return HttpResponse('Unknown source!')
    callback = request.build_absolute_uri(reverse('new_post', args=[src.source_id]))
    try:
        superfeedr.subscribe(url=src.url, callback_url=callback)
    except Exception as e:
        msg = 'could not register blog on superfeedr! {}'.format(e)
        return HttpResponse(msg)
    return HttpResponse('OK, subscribed')
    
def unsubscribe(request, source_id):
    """
    unsubscribe from source on superfeedr
    """
    try:
        src = Source.objects.get(pk=source_id)
    except:
        return HttpResponse('Unknown source!')
    try:
        superfeedr.unsubscribe(url=src.url)
    except Exception as e:
        msg = 'could not unsubscribe on superfeedr! {}'.format(e)
        return HttpResponse(msg)
    return HttpResponse('OK, unsubscribed')
    
