from flask import Flask, render_template, request
from flask_cache import Cache
from flask_bootstrap import Bootstrap
import urllib2
import string
from lxml import etree
import discogs_client
import backend
import conf
import random

app = Flask(__name__)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
Bootstrap(app)
backend = backend

discg = discogs_client.Client

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")

@app.route('/lists')
@cache.cached(timeout=3600)
def lists():
    site = urllib2.urlopen(r'http://pitchfork.com/reviews/albums/1/')
    parser = etree.HTMLParser()
    tree = etree.parse(site, parser)
    p4k_reviews = []
    for i in xrange(1, 6):
        for j in xrange(1,5):
                try:
                    h1 = tree.xpath('//*[@id="main"]/ul/li[%d]/ul/li[%d]/a/div[2]/h1' % (i, j))[0].text
                    h2 = tree.xpath('//*[@id="main"]/ul/li[%d]/ul/li[%d]/a/div[2]/h2' % (i, j))[0].text
                    appendable = '%s - %s' % (h1, h2)
                    p4k_reviews.append(appendable)
                except (TypeError):
                    pass
    return render_template("lists.html", p4k_reviews=p4k_reviews)

@app.route('/settings')
def settings():
    return render_template("settings.html")

@app.route('/search', methods=['GET', 'POST'])
def search():
    message = request.form['action']
    srchquery = []
    discg = discogs_client.Client('app/0.1', user_token='LfYzUfQpWhiJNnmtVQZJKuTVipDPebjIubijkzoT')
    try:
        db_search = discg.search(string.capwords(message), type='artist')[0].releases.page(1)
        srchquery.append(string.capwords(message) + " - Discography")
        for i in xrange(0, len(db_search)):
            srchquery.append(string.capwords(message) + " - " + db_search[i].title)
    except IndexError:
        failedsearch = True
        return render_template("index.html", failedsearch=failedsearch)
    return render_template('search.html', srchquery=srchquery)

@app.route('/dl', methods=['GET', 'POST'])
def download():
    result = request.form['alname']
    dlalbum = backend.ruTracker(
        conf.rutracker_user,
        conf.rutracker_password,
        transmission_user=conf.transmission_user,
        transmission_password=conf.transmission_password,
        qbittorrent_user=conf.qbittorrent_user,
        qbittorrent_password=conf.qbittorrent_password,
        transmission_url=conf.transmission_url,
        qbittorrent_url=conf.qbittorrent_url)
    dlalbum.getCookies()
    dlalbum.getAlbums(result, client=conf.torrent_client)

@app.route('/status')
def queue():
    return render_template("status.html")

if __name__ == '__main__':
    app.run()