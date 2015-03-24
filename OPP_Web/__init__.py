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
        row['short_url'] = shorten_url(row['url'])
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

def shorten_url(url):
    url = re.sub(r'^https?://', '', url);
    if len(url) > 70:
        url = url[:33] + '...' + url[-34:]
    return url

def relative_date(time):
    now = datetime.now()
    diff = now - time
    second_diff = diff.seconds
    day_diff = diff.days
    
    if second_diff < 120:
        return "1&nbsp;minute ago"
    if second_diff < 3600:
        return str(second_diff / 60) + "&nbsp;minutes ago"
    if second_diff < 7200:
        return "1&nbsp;hour ago"
    if second_diff < 86400:
        return str(second_diff / 3600) + "&nbsp;hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + "&nbsp;days ago"
    if day_diff < 31:
        return str(day_diff / 7) + "&nbsp;weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + "&nbsp;months ago"
    return str(day_diff / 365) + "&nbsp;years ago"

if __name__ == "__main__":
    app.run()

