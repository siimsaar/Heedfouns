# -*- coding: utf-8 -*-
from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_cache import Cache
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_bootstrap import Bootstrap
from collections import OrderedDict
from flask_login import LoginManager, login_user, login_required, UserMixin
import urllib2
import string
import pylast
import os
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

##FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

## SQLALCHEMY
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'history.db')

discg = discogs_client.Client


@app.route('/', methods=['GET', 'POST'])
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
@cache.cached(timeout=3600)
def lists():
    site = urllib2.urlopen(r'http://pitchfork.com/reviews/albums/1/')
    parser = etree.HTMLParser()
    tree = etree.parse(site, parser)
    p4k_reviews = []
    for i in xrange(1, 6):
        for j in xrange(1, 5):
            try:
                h1 = tree.xpath('//*[@id="main"]/ul/li[%d]/ul/li[%d]/a/div[2]/h1' % (i, j))[0].text
                h2 = tree.xpath('//*[@id="main"]/ul/li[%d]/ul/li[%d]/a/div[2]/h2' % (i, j))[0].text
                appendable = '%s - %s' % (h1, h2)
                p4k_reviews.append(appendable)
            except (TypeError):
                pass
    return render_template("lists.html", p4k_reviews=p4k_reviews)


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
    dlalbum = torrentdler.TorrentDl(
        conf.rutracker_user,
        conf.rutracker_password,
        transmission_user=conf.transmission_user,
        transmission_password=conf.transmission_password,
        qbittorrent_user=conf.qbittorrent_user,
        qbittorrent_password=conf.qbittorrent_password,
        transmission_url=conf.transmission_url,
        qbittorrent_url=conf.qbittorrent_url)
    try:
        dlalbum.getCookies()
        dlalbum.getAlbums(result, client=conf.torrent_client)
        rq_album = Album(result, "Added")
    except ValueError:
        print "• Fix your configuration"
        rq_album = Album(result, "Fail: Configuration error")
    except ReferenceError:
        rq_album = Album(result, "Fail: Unable to find album")
    except IOError:
        rq_album = Album(result, "Fail: Unable to add to torrent client")
    finally:
        db.session.add(rq_album)
        db.session.commit()
    return '', 204


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    print url_for('index')
    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if user is not None:
            login_user(user, remember=True)
            return redirect(url_for("index"))
    return render_template("login.html", form=form)


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


if __name__ == '__main__':
    app.run(debug=True)
