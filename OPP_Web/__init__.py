import pprint
import logging.handlers
from datetime import datetime
import re
import sys
from os.path import abspath, dirname, join
sys.path.insert(0, '../')
import MySQLdb.cursors
import config
from datetime import datetime
from flask import Flask, request, g, url_for, render_template, flash, redirect, abort
from flask.ext.mysql import MySQL
from classifier import BinaryClassifier, Doc

app = Flask(__name__)
app.config.from_object('config')

app.logger.setLevel(logging.DEBUG)
logfile = join(abspath(dirname(__file__)), '../error.log')
handler = logging.handlers.RotatingFileHandler(
    logfile,
    maxBytes=100000,
    backupCount=1
    )
app.logger.addHandler(handler)

mysql = MySQL()
mysql.init_app(app)

def get_db():
    if not hasattr(g, 'db'):
        g.db = mysql.connect()
    return g.db

@app.teardown_appcontext
def db_disconnect(exception=None):
    if hasattr(g, 'db'):
        g.db.close()

@app.before_request
def log_request():
    if 'text/html' in request.headers['Accept']:
        app.logger.info("\n".join([
            "\n=====",
            str(datetime.now()),
            request.url,
            request.method,
            request.remote_addr]))

@app.route("/")
def index():
    docs = get_docs('''SELECT D.*,
                       GROUP_CONCAT(T.label) AS topics,
                       GROUP_CONCAT(T.topic_id) AS topic_ids,
                       GROUP_CONCAT(COALESCE(M.strength, -1)) AS strengths
                       FROM (docs D CROSS JOIN
                             (SELECT * FROM topics WHERE is_default = 1) AS T)
                       LEFT JOIN docs2topics M ON (D.doc_id = M.doc_id AND M.topic_id = T.topic_id) 
                       GROUP BY D.doc_id
                       ORDER BY D.found_date DESC
                    ''')

    for doc in docs:
        app.logger.debug("retrieved doc {}".format(doc['doc_id']))
        doc['topics'] = dict(zip(doc['topics'].split(','), 
                                 map(float, doc['strengths'].split(','))))
        # unclassified topics have value -1 now (see COALESCE above)
        app.logger.debug("doc {}".format(doc['doc_id']))
        app.logger.debug(pprint.pformat(doc['topics']))

    if (docs):
        topics = zip(docs[0]['topics'].keys(), docs[0]['topic_ids'].split(','))
        for (topic, topic_id) in topics:
            unclassified = [doc for doc in docs if doc['topics'][topic] == -1]
            if unclassified:
                app.logger.debug("unclassified documents for {}".format(topic))
                classify(unclassified, topic, topic_id)

    # prepare for display:
    for doc in docs:
        doc['topics'] = sorted(
            [(t,int(s*10)) for (t,s) in doc['topics'].iteritems() if s > 0.4],
            key=lambda x:x[1], reverse=True)

    return render_template('list_docs.html', 
                           user=get_user(),
                           docs=docs,
                           next_offset=get_next_offset())


@app.route("/t/<topic>")
def list_topic(topic):
    min_p = float(request.args.get('min') or 0.4);
    # Get latest documents classified into <topic> or not yet
    # classified for <topic> at all, classify the unclassified ones,
    # and keep getting more documents until we have DOCS_PER_PAGE
    # many:
    docs = []
    offset = int(request.args.get('start') or 0)
    while True:
        batch = get_docs('''SELECT D.*, M.strength, T.label, T.topic_id
                            FROM topics T, docs D
                            LEFT JOIN docs2topics M USING (doc_id)
                            WHERE T.label = '{0}' AND M.topic_id = T.topic_id
                            AND (strength >= {1} OR strength IS NULL)
                            ORDER BY D.found_date DESC
                         '''.format(topic, min_p), offset=offset)
        if not batch:
            break
        docs += [row for row in batch if row['strength'] > min_p]
        unclassified = [row for row in batch if row['strength'] is None]
        if unclassified:
            app.logger.debug("{} unclassified docs".format(len(uncleassified)))
            classify(unclassified, batch[0]['label'], batch[0]['topic_id'])
            for doc in unclassified:
                doc['strength'] = "{0:.2f}".format(doc['strength'])
            docs += [row for row in unclassified if row['strength'] > min_p]
        if len(docs) >= app.config['DOCS_PER_PAGE']:
            docs = docs[:app.config['DOCS_PER_PAGE']]
            break
        # Previously unclassified entries are now classified, so to
        # get further candidates from DB, we need to look past the
        # first len(doc) matches to the above query:
        offset += len(docs)
        app.logger.debug("retrieving more docs")

    return render_template('list_docs.html', 
                           user=get_user(),
                           docs=docs,
                           topic=topic,
                           admin=is_admin(),
                           next_offset=get_next_offset())

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
    
def get_docs(select,
             limit=app.config['DOCS_PER_PAGE'],
             offset=None):
    if offset is None:
        offset = int(request.args.get('start') or 0)
    query = "{0} LIMIT {1} OFFSET {2}".format(select, limit, offset)
    app.logger.debug(query)
    cur = get_db().cursor(MySQLdb.cursors.DictCursor)
    cur.execute(query);
    rows = cur.fetchall()
    rows = [prettify(row) for row in rows]
    return rows

def get_default_topics():
    if not hasattr(g, 'default_topics'):
        query = "SELECT topic_id, label FROM topics WHERE is_default=1"
        cur = get_db().cursor()
        cur.execute(query);
        g.default_topics = cur.fetchall()
    return g.default_topics

def classify(rows, topic, topic_id):
    docs = [Doc(row) for row in rows]
    clf = BinaryClassifier(topic_id)
    clf.load()
    probs = clf.classify(docs)
    db = get_db()
    cursor = db.cursor()
    for i, (p_spam, p_ham) in enumerate(probs):
        app.logger.debug("{} classified for topic {}: {}".format(
            rows[i]['doc_id'], topic_id, p_ham))
        rows[i]['topics'][topic] = p_ham
        query = '''
            INSERT INTO docs2topics (doc_id, topic_id, strength)
            VALUES ({0},{1},{2})
            ON DUPLICATE KEY UPDATE strength={2}
        '''
        query = query.format(rows[i]['doc_id'], topic_id, p_ham);
        cursor.execute(query)
    db.commit()

@app.route("/train")
def train():
    if get_user() != 'wo':
        abort(401)
    app.logger.debug("/train")
    topic_id = int(request.args.get('topic_id'))
    topic = request.args.get('topic')
    doc_id = int(request.args.get('doc'))
    hamspam = int(request.args.get('class'))
    db = mysql.connect()
    cursor = db.cursor()
    query = '''
        INSERT INTO docs2topics (doc_id, topic_id, strength, is_training)
        VALUES ({0},{1},{2},1)
        ON DUPLICATE KEY UPDATE strength={2}, is_training=1
    '''
    query = query.format(doc_id, topic_id, hamspam);
    cursor.execute(query)
    db.commit()
    flash('retraining classifier and updating document labels...')
    return render_template('redirect.html',
                           target='update_classifier?topic_id={}&next={}'.format(topic_id, request.referrer))

@app.route("/update_classifier")
def update_classifier():
    if get_user() != 'wo':
        abort(401)

    app.logger.debug("/update_classifier")
    topic_id = int(request.args.get('topic_id'))
    db = mysql.connect()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    query = '''
         SELECT D.*, M.strength
         FROM docs D, docs2topics M
         WHERE M.doc_id = D.doc_id AND M.topic_id = {0} AND M.is_training = 1
         ORDER BY D.found_date DESC
         LIMIT 100
    '''
    cursor.execute(query.format(topic_id))
    rows = cursor.fetchall()
    docs = [Doc(row) for row in rows]
    classes = [row['strength'] for row in rows]
    if (0 in classes and 1 in classes):
        clf = BinaryClassifier(topic_id)
        clf.train(docs, classes)
        clf.save()

        # We might reclassify all documents now, but we postpone this step
        # until the documents are actually displayed (which may be never
        # for sufficiently old ones). So we simply undefine the topic
        # strengths to mark that no classification has yet been made.
        query = "UPDATE docs2topics SET strength = NULL WHERE topic_id = {0} AND is_training < 1"
        cursor.execute(query.format(topic_id))
        db.commit()
    else:
        app.log.debug("not updating because not enough training samples")

    return redirect(request.args.get('next'))

def prettify(doc):
    # Adds and modifies some values of document objects retrieved from
    # DB for pretty display
    doc['short_url'] = short_url(doc['url'])
    doc['short_src'] = short_url(doc['source_url'])
    doc['filetype'] = doc['filetype'].upper()
    doc['reldate'] = relative_date(doc['found_date'])
    if 'strength' in doc and doc['strength'] is not None:
        doc['strength'] = "{0:.2f}".format(doc['strength'])
    return doc

@app.route("/opp")
def list_opp_docs():
    user = request.args.get('user') or None;
    cursor = mysql.connect().cursor(MySQLdb.cursors.DictCursor)
    query = '''
         SELECT
            D.*,
            GROUP_CONCAT(L.location_id SEPARATOR ' ') as location_id,
            GROUP_CONCAT(L.url SEPARATOR ' ') as locs,
            GROUP_CONCAT(S.url SEPARATOR ' ') as srcs,
            MIN(L.filetype) as filetype,
            MIN(L.filesize) as filesize
         FROM
            documents D,
            locations L,
            sources S,
            links R
         WHERE
            D.document_id = L.document_id
            AND L.location_id = R.location_id
            AND S.source_id = R.source_id
            AND L.status = 1
            AND {0}
         GROUP BY D.document_id
         ORDER BY D.found_date DESC
         LIMIT {1}
         OFFSET {2}
    '''
    limit = app.config['DOCS_PER_PAGE']
    offset = int(request.args.get('start') or 0);
    max_spam = app.config['MAX_SPAM']
    min_confidence = app.config['MIN_CONFIDENCE']
    where = "spamminess <= {0} AND meta_confidence >= {1}".format(max_spam, min_confidence)
    # temporary hack to let me pass handmade queries for debugging:
    if user == 'wo' and request.args.get('where'):
        where = request.args.get('where')
    query = query.format(where, limit, offset)
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows: 
        row['src'] = row['srcs']
        row['url'] = row['locs']
        row['short_url'] = short_url(row['url'])
        row['short_src'] = short_url(row['src'])
        row['filetype'] = row['filetype'].upper()
        row['reldate'] = relative_date(row['found_date'])
 
    return render_template('list_docs.html', 
                           user=user,
                           docs=rows,
                           next_offset=offset+limit)

def short_url(url):
    url = re.sub(r'^https?://', '', url)
    if len(url) > 80:
        url = url[:38] + '...' + url[-39:]
    #url = re.sub(r'(\.\w+)$', r'<b>\1</b>', url)
    return url

def relative_date(time):
    now = datetime.now()
    delta = now - time
    if delta.days > 365:
        return str(delta.days / 365) + "&nbsp;years ago"
    if delta.days > 31:
        return str(delta.days / 30) + "&nbsp;months ago"
    if delta.days > 7:
        return str(delta.days / 7) + "&nbsp;weeks ago"
    if delta.days > 1:
        return str(delta.days) + "&nbsp;days ago"
    if delta.days == 1:
        return "Yesterday"
    if delta.seconds > 7200:
        return str(delta.seconds / 3600) + "&nbsp;hours ago"
    if delta.seconds > 3600:
        return "1&nbsp;hour ago"
    if delta.seconds > 120:
        return str(delta.seconds / 60) + "&nbsp;minutes ago"
    return "1&nbsp;minute ago"

@app.route("/opp-all")
def list_opp_locs():
    user = request.args.get('user') or None;
    cursor = mysql.connect().cursor(MySQLdb.cursors.DictCursor)
    limit = app.config['DOCS_PER_PAGE']
    offset = int(request.args.get('start') or 0);
    query = '''
         SELECT
            L.*,
            D.*,
            S.url as source_url,
            S.default_author as source_author
         FROM
            locations L
         LEFT JOIN
            documents D USING (document_id)
         INNER JOIN
            links USING (location_id)
         INNER JOIN
            sources S USING (source_id)
         WHERE L.status > 0
         ORDER BY L.last_checked DESC
         LIMIT %s
         OFFSET %s
    '''
    cursor.execute(query, (limit, offset))
    rows = cursor.fetchall()
    for row in rows: 
        row['short_url'] = short_url(row['url'])
        if row['status'] <= 1:
            row['error'] = ''
            if row['spamminess'] > app.config['MAX_SPAM']:
                row['type'] = 'spam'
            elif row['meta_confidence'] < app.config['MIN_CONFIDENCE']:
                row['type'] = 'unsure'
            else:
                row['type'] = 'normal'
        else:
            row['type'] = 'broken'
            row['error'] = error.get(str(row['status']), 'error {}'.format(row['status']))

    return render_template('list_locs.html', 
                           user=user,
                           locs=rows,
                           next_offset=offset+limit)

error = {
   '30': 'process_links terminated during processing',
   '42': 'cannot read local file',
   '43': 'cannot save local file',
   '49': 'Cannot allocate memory',
   '50': 'unknown parser failure',
   '51': 'unsupported filetype',
   '58': 'OCR failed',
   '59': 'gs failed',
   '60': 'pdftohtml produced garbage',
   '61': 'pdftohtml failed',
   '62': 'no text found in converted document',
   '63': 'rtf2pdf failed',
   '64': 'unoconv failed',
   '65': 'htmldoc failed',
   '66': 'wkhtmltopdf failed',
   '67': 'ps2pdf failed',
   '68': 'html2xml failed',
   '69': 'pdf conversion failed',
   '70': 'parser error',
   '71': 'non-UTF8 characters in metadata',
   '92': 'database error',
   '900': 'cannot fetch document',
   '901': 'document is empty',
   '950': 'steppingstone to already known location',
   '1000': 'subpage with more links'
}

@app.route("/opp-sources")
def list_sources():
    cursor = mysql.connect().cursor(MySQLdb.cursors.DictCursor)
    query = 'SELECT * FROM sources WHERE parent_id IS NULL ORDER BY default_author'
    cursor.execute(query)
    rows = cursor.fetchall()
    return render_template('list_sources.html', srcs=rows)


if __name__ == "__main__":
    app.run()

