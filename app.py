# -*- coding: utf-8 -*-
from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_cache import Cache
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Regexp, equal_to
from flask_bootstrap import Bootstrap
from collections import OrderedDict
from flask_login import LoginManager, login_user, login_required, UserMixin, current_user, logout_user
import urllib2
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
import random

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


@app.route('/lists')
@login_required
# @cache.cached(timeout=3600)
def lists():
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
            tree.xpath('//*[@id="reviews"]/div[2]/div/div[1]/div[1]/div/div/div[%d]/a/div[1]/div/img//@src' % (i))[0]
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
    return render_template("lists.html", p4k_reviews=p4k_reviews, covers=covers, genre=genre, rv_links=rv_links)


@app.route('/settings')
@login_required
def settings():
    return render_template("settings.html")


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    message = request.form['action']
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
        failedsearch = True
        return render_template("index.html", failedsearch=failedsearch)
    return render_template('search.html', srchquery=srchquery)


def discogs_search(message, srchquery):
    discg = discogs_client.Client('app/0.1', user_token='LfYzUfQpWhiJNnmtVQZJKuTVipDPebjIubijkzoT')
    db_search = discg.search(string.capwords(message), type='artist')[0].releases.page(1)
    srchquery.append(string.capwords(message) + " - Discography")
    for i in xrange(0, len(db_search)):
        srchquery.append(string.capwords(message) + " - " + db_search[i].title)


def lastfm_search(message, srchquery, covers):
    API_KEY = "d5e9e669b3a12715c860607e3ddce016"
    API_SECRET = "44c1a2333db8fe1b083716a614fa569a"
    lfm = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
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
    changetxt = Album.query.filter_by(album_name=edits['oldn']).first()
    Album.query.get(changetxt.id).album_name = edits['newn']
    db.session.commit()
    return '', 204

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if user is not None:
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


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    album_name = db.Column(db.TEXT, unique=True)
    status = db.Column(db.TEXT, unique=False)

    def __init__(self, album_name, status):
        self.album_name = album_name
        self.status = status

    def __repr__(self):
        return '<Album %r>' % self.album_name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True)
    password = db.Column(db.String(24), unique=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.name


class Login(Form):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class Registration(Form):
    name = StringField('Username', validators=[DataRequired(), Length(1, 24),
                                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, "Invalid chars")])
    password = PasswordField('Password', validators=[DataRequired(), equal_to('password2', "Passwords dont match!"),
                                                     Length(4, 24, "Password too short")])
    password2 = PasswordField('Confirm pw', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('Username already exists')

@app.before_request
def get_current_user():
    g.user = current_user

@app.before_request
def get_uptime():
    g.time = str(datetime.now() - starttime)[:7]

if __name__ == '__main__':
    if not os.path.exists('history.db'):
        db.create_all()
    app.run(debug=True)