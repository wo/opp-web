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
from flask import Flask, request, g, url_for, render_template, flash, redirect, abort, session
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, SubmitField
from wtforms.validators import Required, Email, Regexp, Length
from werkzeug import generate_password_hash, check_password_hash
from werkzeug.contrib.atom import AtomFeed

sys.path.insert(0, '../')
import config

app = Flask(__name__)
app.config.from_object('config')

app.logger.setLevel(logging.DEBUG)
logfile = join(abspath(dirname(__file__)), '../log/opp-web.log')
handler = logging.FileHandler(logfile)
app.logger.addHandler(handler)

db = SQLAlchemy()
db.init_app(app)

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String)
    email = db.Column(db.String)
    pwhash = db.Column(db.String)
    last_login = db.Column(db.DateTime)
    upvotes = db.Column(db.Integer)
    downvotes = db.Column(db.Integer)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email.lower()
        self.set_password(password)
        self.last_login = datetime.now()
        self.upvotes = 0
        self.downvotes = 0
    
    def set_password(self, password):
        self.pwhash = generate_password_hash(password)
   
    def check_password(self, password):
        return check_password_hash(self.pwhash, password)

class SignupForm(Form):
    username = TextField("Username", [
        Required(),
        Length(min=2, max=80),
        Regexp(r'[A-Za-z0-9_\-]', message="only letters and numbers please")
    ])
    email = TextField("Email", [
        Required(),
        Email()
    ])
    password = PasswordField('Password', [Required()])
    submit = SubmitField("Create account")
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        
    def validate(self):
        if not Form.validate(self):
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('That username is already taken')
            return False
        else:
            # add topic on backend server; at the moment, every user
            # has exactly one topic, whose label equals the username
            url = app.config['JSONSERVER_URL']+'init_topic?label={}'.format(self.username.data)
            try:
                r = requests.get(url)
                r.raise_for_status()
                json = r.json()
                if not json['msg'] == 'OK':
                    raise
            except:
                self.username.errors.append('Could not initialize topic on backend server, sorry!')
                return False
            return True

class LoginForm(Form):
    username = TextField('Username', [Required()])
    password = PasswordField('Password', [Required()])
    submit = SubmitField("Log in")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        
    def validate(self):
        if not Form.validate(self):
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user is None:
            self.username.errors.append('Unknown username')
            return False
        if not user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False
        user.last_login = datetime.now()
        db.session.commit()
        return True
        
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('signup.html', form=form)
        else: 
            newuser = User(form.username.data, form.email.data, form.password.data)
            db.session.add(newuser)
            db.session.commit()
            session.permanent = True
            session['username'] = newuser.username
            return redirect(url_for('index'))
    else: 
        return render_template('signup.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('login.html', form=form)
        else:
            session.permanent = True
            session['username'] = form.username.data
            return redirect(url_for('index'))
    else:
        return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))
    
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
    user = get_user()
    if user:
        return list_topic(user.username)
    else:
        return list_all()

@app.route("/all")
def list_all():
    offset = int(request.args.get('start') or 0)
    url = app.config['JSONSERVER_URL']+'doclist?offset={}'.format(offset)
    r = None
    app.logger.debug("fetching {}".format(url))
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
    except:
        return error(r)
    else:
        return render_template('list_docs.html', 
                               user=get_user(),
                               admin=is_admin(),
                               intro=get_intro(),
                               docs=json['docs'],
                               next_offset=get_next_offset())

@app.route("/t/<topic>")
def list_topic(topic):
    min_p = float(request.args.get('min') or (0.0 if is_admin() else 0.5))
    offset = int(request.args.get('start') or 0)
    url = app.config['JSONSERVER_URL']+'topiclist/{}?offset={}'.format(topic,offset)
    r = None
    app.logger.debug("fetching {}".format(url))
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
        app.logger.debug(json)
    except:
        return error(r)
    else:
        return render_template('list_docs.html', 
                               user=get_user(),
                               admin=is_admin(),
                               intro=get_intro(),
                               topic=topic,
                               topic_id=json['topic_id'],
                               docs=json['docs'],
                               next_offset=get_next_offset())

@app.route('/_editdoc', methods=['POST'])
def editdoc():
    if not is_admin():
        abort(401)
    url = app.config['JSONSERVER_URL']+'editdoc'
    data = request.form
    r = None
    try:
        r = requests.post(url, data)
        r.raise_for_status()
        json = r.json()
        return 'OK'
    except:
        return error(r)

@app.route("/train")
def train():
    query = request.query_string + '&user=' + get_username()
    url = app.config['JSONSERVER_URL']+'train?'+query
    r = None
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
    except:
        return error(r)
    user = get_user()
    if request.args.get('class') == '0':
        user.downvotes += 1
    else:
        user.upvotes += 1
    db.session.commit()
    return 'OK'

@app.route('/feed.xml')
def atom_feed():
    url = app.config['JSONSERVER_URL']+'feedlist'
    docs = []
    r = None
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
    r = None
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
    except:
        return error(r)
    else:
        srcs = json['sources']
        srcs1 = [src for src in srcs if src['type'] == 1]
        srcs2 = [src for src in srcs if src['type'] == 2]
        return render_template('list_sources.html', 
                               srcs1=srcs1,
                               srcs2=srcs2,
                               admin=is_admin())

@app.route("/opp-queue")
def list_uncertain_docs():
    offset = int(request.args.get('start') or 0)
    url = app.config['JSONSERVER_URL']+'opp-queue?offset={}'.format(offset)
    r = None
    try:
        r = requests.get(url)
        r.raise_for_status()
        json = r.json()
    except:
        return error(r)
    else:
        return render_template('list_docs.html', 
                               user=get_user(),
                               admin=is_admin(),
                               docs=json['docs'],
                               oppdocs=True,
                               next_offset=get_next_offset())

        
def get_user():
    username = get_username()
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return user
    return None

def get_username():
    if 'username' in session:
        return session['username']
    return None

def is_admin():
    return get_username() == 'wo'
    
def get_intro():
    user = get_user()
    if user:
        if user.upvotes == 0 and user.downvotes == 0:
            return 'user_new'
        if user.upvotes < 10 or user.downvotes < 10:
            return 'user_training'
        return 'user_trained'
    return 'general'

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
    debug_info = ['access to backend server failed']
    if r:
        debug_info.append('response status: {}'.format(r.status_code))
        debug_info.append(r.text)
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

