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
    limit = app.config['DOCS_PER_PAGE']
    max_spam = app.config['MAX_SPAM']
    min_confidence = app.config['MIN_CONFIDENCE']
    offset = int(request.args.get('start') or 0);
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
            AND spamminess <= %s
            AND meta_confidence >= %s
            AND L.status = 1
         GROUP BY D.document_id
         ORDER BY D.found_date DESC
         LIMIT %s
         OFFSET %s
    '''
    cursor.execute(query, (max_spam, min_confidence, limit, offset))
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

if __name__ == "__main__":
    app.run()

