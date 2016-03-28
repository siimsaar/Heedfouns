# -*- coding: utf-8 -*-
from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_cache import Cache
from flask_bootstrap import Bootstrap
from collections import OrderedDict
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import urllib2
from models import *
import string
import time
import threading
import Queue
import pylast
from datetime import datetime
import os
import traceback
from lxml import etree
import discogs_client
import torrentdler
import conf

##FLASK
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
basedir = os.path.abspath(os.path.dirname(__file__))
app.secret_key = 'whateva'

##BOOTSTRAP
Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config['BOOTSTRAP_USE_MINIFIED'] = False

##FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

## SQLALCHEMY
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'history.db')

discg = discogs_client.Client
q = Queue.Queue()
starttime = datetime.now()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
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


@app.route('/lists/p4k')
@login_required
# @cache.cached(timeout=3600)
def p4k_listing():
    ureq = urllib2.Request(r'http://pitchfork.com/reviews/albums', headers={'User-Agent': "asdf"})
    site = urllib2.urlopen(ureq)
    parser = etree.HTMLParser()
    tree = etree.parse(site, parser)
    p4k_reviews = []
    rv_links = []
    covers = []
    genre = []
    for i in xrange(1, 25):
        try:
            h1 = tree.xpath('//*[@id="reviews"]/div[2]/div/div[1]/div[1]/div/div/div[%d]/a/div[2]/ul/li' % (i))[0].text
            h2 = tree.xpath('//*[@id="reviews"]/div[2]/div/div[1]/div[1]/div/div/div[%d]/a/div[2]/h2' % (i))[0].text
            cover = \
                tree.xpath('//*[@id="reviews"]/div[2]/div/div[1]/div[1]/div/div/div[%d]/a/div[1]/div/img//@src' % (i))[
                    0]
            reviewlink = tree.xpath('//*[@id="reviews"]/div[2]/div/div[1]/div/div/div/div[%d]/a//@href' % (i))[0]
            try:
                genres = tree.xpath('//*[@id="reviews"]/div[2]/div/div[1]/div[1]/div/div/div[%d]/div/ul[1]/li/a' % i)[
                    0].text
            except:
                genres = "N/A"
            appendable = '%s - %s' % (h1, h2)
            p4k_reviews.append(appendable)
            genre.append(genres)
            rv_links.append("http://pitchfork.com" + reviewlink)
            covers.append(str(cover))
        except (TypeError):
            pass
    return render_template("p4k.html", p4k_reviews=p4k_reviews, covers=covers, genre=genre, rv_links=rv_links)


@app.route('/lists')
@login_required
def list_landing():
    return render_template("list.html")


@app.route('/lists/mnet/<page>')
@login_required
def list_mnet(page):
    ureq = urllib2.Request(r'http://mwave.interest.me/kpop/new-album.m?page.nowPage=' + page,
                           headers={'User-Agent': "asdf"})
    site = urllib2.urlopen(ureq)
    parser = etree.HTMLParser()
    tree = etree.parse(site, parser)
    mnet_lists = []
    covers = []
    genre = []
    for i in xrange(1, 21):
        try:
            h1 = tree.xpath('//*[@id="content"]/div[1]/ul/li[%d]/dl/dd[1]/a' % (i))[0].text
            h2 = tree.xpath('//*[@id="content"]/div[1]/ul/li[%d]/dl/dd[2]/a' % (i))[0].text
            cover = \
                tree.xpath('//*[@id="content"]/div[1]/ul/li[%d]/dl/dt/a/img//@src' % (i))[
                    0]
            # moreinflink = tree.xpath('//*[@id="reviews"]/div[2]/div/div[1]/div/div/div/div[%d]/a//@href' % (i))[0]
            try:
                genres = tree.xpath('//*[@id="content"]/div[1]/ul/li[%d]/dl/dd[4]//text()[2]' % i)[
                    0]
            except:
                genres = "N/A"
            if h2 is " ":
                continue
            else:
                appendable = '%s - %s' % (h2, h1)
                mnet_lists.append(appendable)
                genre.append(genres)
                covers.append(str(cover))
        except (TypeError):
            pass
    return render_template("mnet.html", mnet_lists=mnet_lists, covers=covers, genre=genre, page=int(page))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        return render_template("settings.html", torrent_client=conf.torrent_client,
                               fallback=conf.use_fallback,
                               default_api=conf.default_search_api,
                               transmission_u=conf.transmission_user,
                               transmission_p=conf.transmission_password,
                               qbitorrent_u=conf.qbittorrent_user,
                               qbitorrent_p=conf.qbittorrent_password,
                               tranmission_url=conf.transmission_url,
                               qbitorrent_url=conf.qbittorrent_url,
                               rutracker_u=conf.rutracker_user,
                               rutracker_p=conf.rutracker_password,
                               jpop_u=conf.jpopsuki_user,
                               jpop_p=conf.jpopsuki_password)
    else:
        try:
            conf.updateConf(request.form['tu_us'],
                            request.form['tu_pw'],
                            request.form['t_url'],
                            request.form['q_us'],
                            request.form['q_pw'],
                            request.form['q_url'],
                            request.form['p_tc'],
                            request.form['ru_u'],
                            request.form['ru_p'],
                            request.form['j_u'],
                            request.form['ju_p'], )
        except:
            traceback.print_exc()
        reload(conf)
        flash("Configuration updated and reloaded")
        return redirect(url_for("settings"))


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    message = request.form['search_term']
    return redirect(url_for('search_results', message=message))


@app.route('/results/<message>')
@login_required
def search_results(message):
    srchquery = []
    covers = []
    search_provider = None
    try:
        search_provider = api_s
    except:
        print "default search provider not set"
    try:
        if search_provider == "lastfm":
            lastfm_search(message, srchquery, covers)
        elif search_provider == "discogs":
            discogs_search(message, srchquery)
    except (IndexError, pylast.WSError):
        flash("Couldn't find any albums", 'error')
        return render_template("index.html")
    return render_template("search.html", srchquery=srchquery)


def discogs_search(message, srchquery):
    discg = discogs_client.Client('app/0.1', user_token='LfYzUfQpWhiJNnmtVQZJKuTVipDPebjIubijkzoT')
    db_search = discg.search(string.capwords(message), type='artist')[0].releases.page(1)
    srchquery.append(string.capwords(message) + " - Discography")
    for i in xrange(0, len(db_search)):
        srchquery.append(string.capwords(message) + " - " + db_search[i].title)


def lastfm_search(message, srchquery, covers):
    API_KEY = "d5e9e669b3a12715c860607e3ddce016"
    lfm = pylast.LastFMNetwork(api_key=API_KEY)
    artist = lfm.get_artist(message).get_top_albums(limit=25)
    for i in artist:
        srchquery.append(str(i[0]).decode('utf-8'))


@app.route('/dl', methods=['GET', 'POST'])
@login_required
def download():
    result = request.form['alname']
    time.sleep(1)
    if q.unfinished_tasks > 0:
        q.put(result)
    else:
        q.put(result)
        dlThread = threading.Thread(target=initDl, args=(q,)).start()
    return '', 204


def initDl(q):
    while True:
        dlalbum = torrentdler.TorrentDl(
            conf.rutracker_user,
            conf.rutracker_password,
            transmission_user=conf.transmission_user,
            transmission_password=conf.transmission_password,
            qbittorrent_user=conf.qbittorrent_user,
            qbittorrent_password=conf.qbittorrent_password,
            transmission_url=conf.transmission_url,
            qbittorrent_url=conf.qbittorrent_url,
            jpopsuki_user=conf.jpopsuki_user,
            jpopsuki_password=conf.jpopsuki_password)
        result = q.get()
        print result
        try:
            dlalbum.getCookies()
            dlalbum.getAlbums(result, client=conf.torrent_client)
            rq_album = Album(result, "Added")
        except ValueError:
            rq_album = Album(result, "Fail: Configuration error")
        except ReferenceError:
            rq_album = Album(result, "Fail: Unable to find album")
        except IOError:
            rq_album = Album(result, "Fail: Unable to add to torrent client")
        finally:
            try:
                exitingobj = db.session.query(Album.id).filter(Album.album_name == rq_album.album_name).first()
                if exitingobj:
                    print "Updating status"
                    Album.query.get(exitingobj.id).status = rq_album.status
                    db.session.commit()
                else:
                    db.session.add(rq_album)
                    db.session.commit()
                q.task_done()
            except:
                traceback.print_exc()
                db.session.rollback()
                pass


@app.route('/status')
@login_required
def queue():
    wholedb = Album.query.all()
    album_history = OrderedDict()
    for i in reversed(xrange(len(wholedb))):
        album_history[wholedb[i].album_name] = wholedb[i].status
    return render_template("status.html", album_history=album_history)


@app.route('/del', methods=['POST'])
@login_required
def delete():
    tobedeleted = request.form['alname']
    row = Album.query.filter_by(album_name=tobedeleted).delete()
    db.session.commit()
    return '', 204


@app.route('/rename', methods=['POST'])
@login_required
def rename():
    edits = request.json
    if not "-" in edits['newn'] or edits['newn'] is "":
        return '', 500
    changetxt = Album.query.filter_by(album_name=edits['oldn']).first()
    Album.query.get(changetxt.id).album_name = edits['newn']
    db.session.commit()
    return '', 204


@app.route('/more_info/<artist>/<album>', methods=['GET', 'POST'])
@login_required
def m_info(artist, album):
    API_KEY = "d5e9e669b3a12715c860607e3ddce016"
    lfm = pylast.LastFMNetwork(api_key=API_KEY)
    g_artist = lfm.get_artist(artist)
    g_album = lfm.get_album(artist, album)
    tags = g_album.get_top_tags(limit=6)
    cover = str(g_album.get_cover_image())
    similar = g_artist.get_similar(limit=6)
    tracks = g_album.get_tracks()
    tag_l = []
    trak_l = []
    similar_l = []
    release = "N/A"
    for i in xrange(0, 5):
        try:
            if not str(tags[i][0]).isdigit():
                tag_l.append(str(tags[i][0]))
            else:
                release = str(tags[i][0])
            similar_l.append(str(similar[i][0]))
        except:
            continue
    for j in tracks:
        trak_l.append(str(j))
    return jsonify(tags=tag_l, similar_artists=similar_l, track_list=trak_l, cover=cover, release=release)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if user is not None:
            if User.check_password(user, form.password.data):
                login_user(user, remember=True)
                return redirect(url_for("index"))
        flash("Invalid username or password", 'error')
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/reg', methods=['GET', 'POST'])
def regacc():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = Registration()
    if form.validate_on_submit():
        user = User(name=form.name.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registered")
        return redirect(url_for("login"))
    return render_template("reg.html", form=form)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("login"))


@app.before_request
def get_current_user():
    g.user = current_user


@app.before_request
def get_uptime():
    g.time = str(datetime.now() - starttime)[:7]


if __name__ == '__main__':
    if not os.path.exists('history.db'):
        init_db()
    app.run(debug=True)
