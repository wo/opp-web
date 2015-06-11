import pprint
import logging.handlers
from datetime import datetime, timedelta
import itertools
from collections import defaultdict
import re
import sys
import requests
from cStringIO import StringIO
from os.path import abspath, dirname, join
from flask import Flask, request, g, url_for, render_template, flash, redirect, abort
from werkzeug.contrib.atom import AtomFeed

sys.path.insert(0, '../')
import config

app = Flask(__name__)
app.config.from_object('config')

app.logger.setLevel(logging.DEBUG)
logfile = join(abspath(dirname(__file__)), '../log/opp-web.log')
handler = logging.FileHandler(logfile)
app.logger.addHandler(handler)

@app.before_request
def log_request():
    if '/static/' not in request.path:
        app.logger.info("\n".join([
            "\n=====",
            str(datetime.now()),
            request.url,
            request.method,
            request.remote_addr]))

@app.context_processor
def set_rootdir():
    rootdir = request.args.get('rootdir') or request.url_root
    rootdir = re.sub(r'^https?://[^/]+', '', rootdir)
    return dict(rootdir=rootdir)

@app.route("/")
def index():
    offset = int(request.args.get('start') or 0)
    url = app.config['JSONSERVER_URL']+'doclist?offset={}'.format(offset)
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
        return render_template('list_docs.html', 
                               user=get_user(),
                               admin=is_admin(),
                               docs=json['docs'],
                               next_offset=get_next_offset())
    except:
        return error(r)

@app.route("/t/<topic>")
def list_topic(topic):
    min_p = float(request.args.get('min') or (0.0 if is_admin() else 0.5))
    offset = int(request.args.get('start') or 0)
    url = app.config['JSONSERVER_URL']+'topiclist/{}?offset={}'.format(topic,offset)
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
        return render_template('list_docs.html', 
                               user=get_user(),
                               admin=is_admin(),
                               topic=topic,
                               topic_id=json['topic_id'],
                               docs=json['docs'],
                               next_offset=get_next_offset())
    except:
        return error(r)

@app.route('/_editdoc', methods=['POST'])
def editdoc():
    if not is_admin():
        abort(401)
    url = app.config['JSONSERVER_URL']+'editdoc'
    data = request.form
    try:
        r = requests.post(url, data)
        r.raise_for_status()
        json = r.json()
        return 'OK'
    except:
        return error(r)

@app.route("/train")
def train():
    if not is_admin():
        abort(401)
    url = app.config['JSONSERVER_URL']+'train?'+request.query_string
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
        return 'OK'
    except:
        return error(r)

@app.route('/feed.xml')
def atom_feed():
    url = app.config['JSONSERVER_URL']+'feedlist'
    docs = []
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
        docs = json['docs']
    except:
        return error(r)

    base_url = 'http://umsu.de/opp/'
    feed = AtomFeed('Philosophical Progress',
                    feed_url=base_url+'feed.xml', url=base_url)
   
    day = ''
    updated = None 
    day_text = u''
    for doc in docs:
        if doc['found_day'] != day:
            if day:
                feed.add('Articles found on {}'.format(day), 
                         escape_illegal_chars(day_text),
                         content_type='html',
                         author='Philosophical Progress',
                         url=base_url+'?'+str(updated)[:10],
                         updated=updated)
            day = doc['found_day']
            updated = doc['found_date']
            day_text = u''
        day_text += u'<b>{}: <a href="{}">{}</a></b>'.format(doc['authors'], doc['url'], doc['title'])
        day_text += u' ({}, {} words)<br />'.format(doc['filetype'], doc['numwords'])
        day_text += u' <div>{}</div><br />\n'.format(doc['abstract'])
        
    if day_text:
        feed.add('Articles found on {}'.format(day), 
                 escape_illegal_chars(day_text),
                 content_type='html',
                 author='Philosophical Progress',
                 url=base_url+'?'+str(updated)[:10],
                 updated=updated)
    return feed.get_response()

_illegal_xml_chars_RE = re.compile(u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]')
def escape_illegal_chars(val, replacement='?'):
    return _illegal_xml_chars_RE.sub(replacement, val)    

@app.route("/sources")
def list_sources():
    url = app.config['JSONSERVER_URL']+'sources'
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
        srcs = json['sources']
        srcs1 = [src for src in srcs if src['type'] == 1]
        srcs2 = [src for src in srcs if src['type'] == 2]
        return render_template('list_sources.html', 
                               srcs1=srcs1,
                               srcs2=srcs2,
                               admin=is_admin())
    except:
        return error(r)

@app.route("/opp-queue")
def list_uncertain_docs():
    offset = int(request.args.get('start') or 0)
    url = app.config['JSONSERVER_URL']+'opp-queue?offset={}'.format(offset)
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
        return render_template('list_docs.html', 
                               user=get_user(),
                               admin=is_admin(),
                               docs=json['docs'],
                               oppdocs=True,
                               next_offset=get_next_offset())
    except:
        return error(r)

@app.route("/about")
def about_page():
    return render_template('about.html', user=get_user())

        
def get_user():
    if app.debug:
        return 'wo'
    return request.args.get('user')

def is_admin():
    return get_user() == 'wo'

def get_next_offset():
    offset = int(request.args.get('start') or 0)
    limit = app.config['DOCS_PER_PAGE']
    return offset + limit

def prettify(doc):
    # Adds and modifies some values of document objects retrieved from
    # DB for pretty display
    doc['source_url'] = doc['source_url'].replace('&','&amp;')
    doc['short_url'] = short_url(doc['url'])
    doc['source_name'] = doc['source_name'].replace('&','&amp;')
    doc['filetype'] = doc['filetype'].upper()
    doc['reldate'] = relative_date(doc['found_date'])
    doc['deltadate'] = relative_date(doc['found_date'], 1)
    return doc

def short_url(url):
    if not url:
        return 'about:blank'
    url = re.sub(r'^https?://', '', url)
    if len(url) > 80:
        url = url[:38] + '...' + url[-39:]
    #url = re.sub(r'(\.\w+)$', r'<b>\1</b>', url)
    return url
    
def relative_date(time, diff=False):
    now = datetime.now()
    delta = now - time
    if diff:
        return int(delta.total_seconds())
    if delta.days > 730:
        return str(delta.days / 365) + "&nbsp;years ago"
    if delta.days > 60:
        return str(delta.days / 30) + "&nbsp;months ago"
    if delta.days > 14:
        return str(delta.days / 7) + "&nbsp;weeks ago"
    if delta.days > 1:
        return str(delta.days) + "&nbsp;days ago"
    if delta.days == 1:
        return "1&nbsp;day ago"
    if delta.seconds > 7200:
        return str(delta.seconds / 3600) + "&nbsp;hours ago"
    if delta.seconds > 3600:
        return "1&nbsp;hour ago"
    if delta.seconds > 119:
        return str(delta.seconds / 60) + "&nbsp;minutes ago"
    return "1&nbsp;minute ago"
    
def error(r):
    debug_info = ['access to backend server failed',
                  'response status: {}'.format(r.status_code),
                  r.text]
    if is_admin():
        debug_info.append('url: {}'.format(r.url))
    return render_template('error.html',
                           info=debug_info)

class Capturing(list):
    # capture stdout
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout

if __name__ == "__main__":
    app.run()

