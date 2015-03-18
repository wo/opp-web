import re
import MySQLdb.cursors
import config

from flask import Flask, request, g, url_for, render_template
from flaskext.mysql import MySQL

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL()
mysql.init_app(app)

@app.route("/")
def list_docs():
    cursor = mysql.connect().cursor(MySQLdb.cursors.DictCursor)
    limit = 20
    offset = request.args.get('offset') or 0
    max_spam = app.config['MAX_SPAM']
    min_confidence = app.config['MIN_CONFIDENCE']
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
    cursor.execute(query, (max_spam, min_confidence, limit, int(offset)))
    rows = cursor.fetchall()
    for row in rows: 
        row['title'] = 'asdf'
        row['src'] = row['srcs']
        row['url'] = row['locs']
        row['short_url'] = 'k'+shorten_url(row['url'])

    return render_template('list_docs.html', docs=rows)

def shorten_url(url):
    url = re.sub(r'^https?://', '', url);
    if len(url) > 60:
        url = url[:28] + '...' + url[-28:]
    return url

if __name__ == "__main__":
    app.run()

