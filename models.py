import app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = app.db

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    album_name = db.Column(db.TEXT, unique=True)
    status = db.Column(db.TEXT, unique=False)

    def __init__(self, album_name, status):
        self.album_name = album_name
        self.status = status

    def __repr__(self):
        return '<Album %r>' % self.album_name


class TrackedArtists(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.TEXT, unique=True)

    def __init__(self, artist_name):
        self.artist_name = artist_name

    def __repr__(self):
        return '<TrackedA %r>' % self.artist_name


class QueueAlbum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    album_name = db.Column(db.TEXT, unique=True)
    date = db.Column(db.TEXT, unique=False)
    status = db.Column(db.TEXT, unique=False)

    def __init__(self, album_name, date, status):
        self.album_name = album_name
        self.date = date
        self.status = status

    def __repr__(self):
        return '<PlannedA %r>' % self.album_name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True)
    password = db.Column(db.String(256), unique=False)
    admin = db.Column(db.Boolean, unique=False)
    historynum = db.Column(db.Integer)
    searchapi = db.Column(db.Enum('lastfm', 'discogs'), unique=False)

    def __init__(self, name, password, admin, historynum, searchapi):
        self.name = name
        self.set_password(password)
        self.admin = admin
        self.historynum = historynum
        self.searchapi = searchapi

    def __repr__(self):
        return '<User %r>' % self.name

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)