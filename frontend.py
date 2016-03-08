# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from flask_cache import Cache
from flask_bootstrap import Bootstrap
import urllib2
import string
import pylast
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

@app.route('/api', methods=['GET', 'POST'])
def apisel():
    global api_s
    if request.form['apiselec'] == "getactive":
        try:
            api_s
        except:
            api_s = conf.default_search_api
        return api_s
    api_s = request.form['apiselec']
    return api_s

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
    search_provider = None
    try:
        search_provider = api_s
    except:
        print "default search provider not set"
    try:
        if search_provider == "lastfm":
            lastfm_search(message, srchquery)
        elif search_provider == "discogs":
            discogs_search(message, srchquery)
    except (IndexError, pylast.WSError):
        failedsearch = True
        return render_template("index.html", failedsearch=failedsearch)
    return render_template('search.html', srchquery=srchquery)

def discogs_search(message, srchquery):
    discg = discogs_client.Client('app/0.1', user_token='LfYzUfQpWhiJNnmtVQZJKuTVipDPebjIubijkzoT')
    db_search = discg.search(string.capwords(message), type='artist')[0].releases.page(1)
    srchquery.append(string.capwords(message) + " - Discography")
    for i in xrange(0, len(db_search)):
        srchquery.append(string.capwords(message) + " - " + db_search[i].title)

def lastfm_search(message, srchquery):
    API_KEY = "d5e9e669b3a12715c860607e3ddce016"
    API_SECRET = "44c1a2333db8fe1b083716a614fa569a"
    lfm = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
    artist = lfm.get_artist(message).get_top_albums(limit=10)
    for i in artist:
        srchquery.append(str(i[0]).decode('utf-8'))

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