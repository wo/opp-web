import re
import MySQLdb.cursors
import config
from datetime import datetime
from flask import Flask, request, g, url_for, render_template
from flask.ext.mysql import MySQL

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL()
mysql.init_app(app)

@app.route("/")
def list_docs():
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
        row['filesize'] = pretty_filesize(row['filesize'])
        row['reldate'] = relative_date(row['found_date'])
 
    return render_template('list_docs.html', 
                           user=user,
                           docs=rows,
                           next_offset=offset+limit)

def pretty_filesize(size):
    size = int(size)/1000
    size = "{} KB".format(size)
    return size

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

@app.route("/all")
def list_locs():
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

@app.route("/sources")
def list_sources():
    cursor = mysql.connect().cursor(MySQLdb.cursors.DictCursor)
    query = 'SELECT * FROM sources WHERE parent_id IS NULL ORDER BY default_author'
    cursor.execute(query)
    rows = cursor.fetchall()
    return render_template('list_sources.html', srcs=rows)


if __name__ == "__main__":
    app.run()

