# -*- coding: utf-8 -*-
import Queue
import os
import string
import threading
import time
import traceback
import urllib2
import uuid
from urllib import quote_plus
from collections import OrderedDict
from datetime import datetime

import discogs_client
import pylast
from flask import *
from flask_bootstrap import Bootstrap
from flask_cache import Cache
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask.ext.sse import sse, send_event
from lxml import etree
from flask_wtf.csrf import CsrfProtect
import conf
import torrentdler
import auto

# FLASK
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
basedir = os.path.abspath(os.path.dirname(__file__))
app.debug = True

# SSE channel
app.register_blueprint(sse, url_prefix='/updates')

# SESSION KEY
app.secret_key = 'something secure here if going prod'

# BOOTSTRAP
Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config['BOOTSTRAP_USE_MINIFIED'] = False

# FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

# SQLALCHEMY
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'history.db')
from models import User, Album, TrackedArtists, QueueAlbum, Search, Suggestion
from forms import Login, Registration

# MISC
discg = discogs_client.Client  # Discogs search API
q = Queue.Queue()  # FIFO with data for worker thread
dl_requests = 0  # DL requests made
starttime = datetime.now()  # UPTIME
API_KEY = "d5e9e669b3a12715c860607e3ddce016"  # LASTFM KEY
USER_TOKEN = 'LfYzUfQpWhiJNnmtVQZJKuTVipDPebjIubijkzoT'  # DISCOGS TOKEN

# CHECKS
a_running = 0
t_running = 0


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    suggestion_object = g.user.suggestions.all()
    return render_template("index.html", sug_o=suggestion_object)


@app.route('/api', methods=['POST'])
@login_required
def apisel():
    if request.form['setactive'] == "lastfm":
        g.user.searchapi = "lastfm"
        db.session.commit()
        return '', 204
    elif request.form['setactive'] == "discogs":
        g.user.searchapi = "discogs"
        db.session.commit()
        return '', 204
    return '', 400


@app.route('/refresh', methods=['GET'])
@login_required
def relsug():
    if current_user.searches_num >= 3:
        auto.generateSuggestions(current_user)
        suggestion_object = g.user.suggestions.all()
        return render_template("suggestion_template.html", sug_o=suggestion_object)
    else:
        return '', 405


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if conf.hidd_settings == "0" or current_user.admin is True:
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
                                   jpop_p=conf.jpopsuki_password,
                                   reg_enabled=conf.reg_enabled,
                                   settings_enabled=conf.hidd_settings)
        else:
            try:
                qbit_url = request.form['q_url']
                if not qbit_url.startswith('http://'):
                    qbit_url = "http://" + qbit_url
                conf.updateConf(request.form['tu_us'],
                                request.form['tu_pw'],
                                request.form['t_url'],
                                request.form['q_us'],
                                request.form['q_pw'],
                                qbit_url,
                                request.form['p_tc'],
                                request.form['ru_u'],
                                request.form['ru_p'],
                                request.form['j_u'],
                                request.form['ju_p'], )
            except:
                traceback.print_exc()
            reload(conf)
            flash("Configuration updated and reloaded", "success")
            return redirect(url_for("settings"))
    else:
        flash("Setting access is restricted", "warning")
        return redirect(url_for("index"))


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    message = request.form['search_term'].encode('utf-8')
    if len(str(message)) <= 0:
        print "empty search"
        flash("Empty search, enter an artist!", "warning")
        return redirect(url_for('index'))
    return redirect(url_for('search_results', message=message))


@app.route('/results/<message>')
@login_required
def search_results(message):
    srchquery = []
    covers = []
    search_provider = g.user.searchapi
    try:
        if search_provider == "lastfm":
            lastfm_search(message, srchquery, covers)
        elif search_provider == "discogs":
            discogs_search(message, srchquery)
    except (IndexError, pylast.WSError):
        flash("Couldn't find any albums", "warning")
        return redirect(url_for('index'))
    db.session.add(Search(search_term=message, user=g.user))
    g.user.searches_num += 1
    db.session.commit()
    return render_template("search.html", srchquery=srchquery)


def discogs_search(message, srchquery):
    discg = discogs_client.Client('app/0.1', user_token=USER_TOKEN)
    db_search = discg.search(string.capwords(message), type='artist')[0].releases.page(1)
    srchquery.append(string.capwords(message) + " - Discography")
    for i in xrange(0, len(db_search)):
        srchquery.append(string.capwords(message) + " - " + db_search[i].title)


def lastfm_search(message, srchquery, covers):
    lfm = pylast.LastFMNetwork(api_key=API_KEY)
    artist = lfm.get_artist(message).get_top_albums(limit=25)
    for i in artist:
        if not str(i[0]).decode('utf-8').split(" - ")[1] == "(null)":
            srchquery.append(str(i[0]).decode('utf-8'))


@app.route('/auto', methods=['GET', 'POST', 'DELETE'])
@login_required
def automation():
    if request.method == "GET":
        from auto import l_a_check
        from auto import l_t_check
        a_enabled = conf.automation_status
        a_interval = conf.automation_interval
        s_al = QueueAlbum.query.all()
        scheduled_albums = OrderedDict()
        for i in reversed(xrange(len(s_al))):
            if s_al[i].status == "0":
                scheduled_albums[s_al[i].album_name] = s_al[i].date
        t_ar = TrackedArtists.query.all()
        tracked_artists = []
        for i in reversed(xrange(len(t_ar))):
            tracked_artists.append(t_ar[i].artist_name)
        print a_enabled
        return render_template("auto.html", scheduled_albums=scheduled_albums,
                               tracked_artists=tracked_artists, l_a_check=l_a_check, l_t_check=l_t_check,
                               a_enabled=a_enabled, a_interval=a_interval)
    if request.method == 'POST':
        artist_n = request.form['art_name']
        if (len(artist_n)) == 0:
            return "", 400
        db.session.add(TrackedArtists(artist_name=artist_n))
        db.session.commit()
        return "", 204
    if request.method == 'DELETE':
        deleted_artist = request.form['tbdeleted']
        query_a = TrackedArtists.query.filter_by(artist_name=deleted_artist)
        query_a.delete()
        for i in QueueAlbum.query.all():
            if unicode(i.album_name).split(" - ")[0].lower() == unicode(deleted_artist).lower():
                QueueAlbum.query.filter_by(album_name=i.album_name).delete()
        db.session.commit()
        return "", 204


@app.route('/auto/conf', methods=['POST', 'PUT'])
@login_required
def automation_conf():
    if request.method == 'POST':
        try:
            enable_b = request.form['enable_b']
        except:
            enable_b = conf.automation_status
        try:
            interval = request.form['interval']
        except:
            interval = conf.automation_interval
        conf.updateAutomation(enable_b, interval)
        reload(conf)
        auto.reschedule()
        return "", 204
    if request.method == 'PUT':
        try:
            auto.l_a_check = request.form['a_date']
        except:
            pass
        try:
            auto.l_t_check = request.form['t_date']
        except:
            pass
        return "", 204


@app.route('/auto/run', methods=['POST'])
@login_required
def run_automation():
    global a_running, t_running
    if request.form['run_type'] == "album_check":
        if a_running == 1:
            return "", 204
        a_running = 1
        auto.look_for_artist(forced=True)
        a_running = 0
    else:
        if t_running == 1:
            return "", 204
        auto.look_for_torrents(forced=True)
        t_running = 0
    return "", 204


def pushtoListener(data):
    print "ran_shedl"
    send_event("scheduled", json.dumps(data), channel='sched')


def pushtoListenerHiVal(cur_u, id):
    hival_u = User.query.filter_by(name=cur_u).first()
    hival_u.historynum += 1
    db.session.commit()
    send_event("historynum", json.dumps({"user": cur_u, "number": hival_u.historynum}), channel='historynum=' + id)


def pushtoListenerHistory(data):
    print "ran_history"
    send_event("history", json.dumps(data), channel='history')


@app.route('/dl', methods=['GET', 'POST'])
@login_required
def download(name=None):
    try:
        result = request.form['alname']
        sse_id = request.form['id_sse']
        global dl_requests
    except:
        try:
            result = name
        except:
            print "download undefined or identifier missing"
            traceback.print_exc()
    if dl_requests > 0:
        dl_requests += 1
        data = [result, g.user.name, sse_id]
        q.put(data)
    else:
        dl_requests += 1
        data = [result, g.user.name, sse_id]
        q.put(data)
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
        data = q.get()
        result = data[0]
        user = data[1]
        id = data[2]
        print "USER: %s | ALBUM ADDED: %s" % (user, result)
        try:
            dlalbum.getCookies()
            dlalbum.getAlbums(result, client=conf.torrent_client)
            rq_album = Album(result, "Added")
            try:
                succeess_album = QueueAlbum.query.filter_by(album_name=result).first()
                print succeess_album.status
                succeess_album.status = "1"
            except:
                print "unable to remove scheduler album from queue"
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
                    with app.app_context():
                        pushtoListenerHiVal(user, id)
                else:
                    db.session.add(rq_album)
                    db.session.commit()
                    data = ({"name": result, "status": rq_album.status})
                    with app.app_context():
                        pushtoListenerHistory(data)
                        pushtoListenerHiVal(user, id)
                q.task_done()
                global dl_requests
                dl_requests -= 1
            except:
                traceback.print_exc()
                db.session.rollback()
                pass


@app.route('/status', methods=['GET', 'DELETE', 'PUT'])
@login_required
def queue():
    if request.method == "GET":
        wholedb = Album.query.all()
        album_history = OrderedDict()
        for i in reversed(xrange(len(wholedb))):
            album_history[wholedb[i].album_name] = wholedb[i].status
        g.user.historynum = 0
        db.session.commit()
        return render_template("status.html", album_history=album_history)
    if request.method == "DELETE":
        tobedeleted = request.form['alname']
        query_a = Album.query.filter_by(album_name=tobedeleted)
        query_a.delete()
        db.session.commit()
        return '', 204
    if request.method == "PUT":
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
    global API_KEY
    tag_l = []
    trak_l = []
    similar_l = []
    release = "N/A"
    album_url = ("http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=%s&artist=%s&album=%s&format=json" % (
        API_KEY, quote_plus(artist.encode('utf-8')), quote_plus(album.encode('utf-8'))))
    artist_url = ("http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=%s&api_key=%s&format=json" % (
        quote_plus(artist.encode('utf-8')), API_KEY))
    album = urllib2.urlopen(album_url)
    data = json.load(album)
    cover = data['album']['image'][3]['#text']
    for track in data['album']['tracks']['track']:
        trak_l.append("%s - %s" % (artist, track['name']))
    for tag in data['album']['tags']['tag']:
        if str(tag['name']).isdigit():
            release = tag['name']
    artist = urllib2.urlopen(artist_url)
    data_a = json.load(artist)
    for tag in data_a['artist']['tags']['tag']:
        tag_l.append(tag['name'])
    for similar in data_a['artist']['similar']['artist']:
        similar_l.append(similar['name'])
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
                response = make_response(redirect(url_for("index")))
                response.set_cookie('sse_channel_id', str(uuid.uuid4()))
                return response
        flash("Invalid username or password", "warning")
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/reg', methods=['GET', 'POST'])
def regacc():
    if conf.reg_enabled == "0":
        flash("Registration is closed", "warning")
        return redirect(url_for("login"))
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = Registration()
    if form.validate_on_submit():
        user = User(name=form.name.data, password=form.password.data,
                    admin=False, historynum=0, searchapi="lastfm", search_num=0)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash("Successfully registered, start searching for albums!", 'success')
        return redirect(url_for("index"))
    return render_template("reg.html", form=form)


@app.route('/lists/p4k')
@login_required
@cache.cached(timeout=86400)
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
        try:  # ugly
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


@app.route('/admin/<command>')
@login_required
def admin(command):
    if current_user.admin is True:
        if command == "shutdown":
            print "shutting down"
            os.system("killall -9 gunicorn")
            return '', 201
        if command == "sugg":
            auto.generateSuggestions()
            return '', 201
        if command == "reg":
            if conf.reg_enabled == "0":
                print "enabling registration"
                conf.updateRegistration("1")
                reload(conf)
                return '', 201
            else:
                print "disabling registration"
                conf.updateRegistration("0")
                reload(conf)
                return '', 201
        if command == "shid":
            if conf.hidd_settings == "0":
                print "enabling pub settings"
                conf.updateSettings("1")
                reload(conf)
                return '', 201
            else:
                print "disabling pub settings"
                conf.updateSettings("0")
                reload(conf)
                return '', 201
    else:
        return '', 401


@app.route('/lists/mnet/<page>')
@login_required
@cache.cached(timeout=86400)
def list_mnet(page):
    ureq = urllib2.Request(r'http://mwave.interest.me/kpop/new-album.m?page.nowPage=' + page,
                           headers={'User-Agent': "asdf"})
    site = urllib2.urlopen(ureq)
    parser = etree.HTMLParser()
    tree = etree.parse(site, parser)
    mnet_lists = []
    more_info = []
    covers = []
    genre = []
    for i in xrange(1, 21):
        try:  # ugly
            h1 = tree.xpath('//*[@id="content"]/div[1]/ul/li[%d]/dl/dd[1]/a' % (i))[0].text
            h2 = tree.xpath('//*[@id="content"]/div[1]/ul/li[%d]/dl/dd[2]/a' % (i))[0].text
            cover = \
                tree.xpath('//*[@id="content"]/div[1]/ul/li[%d]/dl/dt/a/img//@src' % (i))[
                    0]
            moreinflink = tree.xpath('//*[@id="content"]/div[1]/ul/li[%d]/dl/dd[1]/a//@href' % (i))[0]
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
                more_info.append('http://mwave.interest.me' + moreinflink)
                genre.append(genres)
                covers.append(str(cover))
        except (TypeError):
            pass
    return render_template("mnet.html", mnet_lists=mnet_lists, covers=covers, genre=genre, page=int(page),
                           more_info=more_info)


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


if not os.path.exists('history.db'):
    db.create_all()
