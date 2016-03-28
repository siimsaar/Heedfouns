# Classes for SQL tables and Forms for adding entries to SQL

from app import db
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Regexp, equal_to
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


def init_db():
    db.create_all()


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
    password = db.Column(db.String(256), unique=False)

    def __init__(self, name, password):
        self.name = name
        self.set_password(password)

    def __repr__(self):
        return '<User %r>' % self.name

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Login(Form):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class Registration(Form):
    name = StringField('Username', validators=[DataRequired(), Length(1, 24),
                                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, "Invalid chars")])
    password = PasswordField('Password', validators=[DataRequired(), equal_to('password2', "Passwords dont match!"),
                                                     Length(4, 24, "Password too short ( 4 chars min ) ")])
    password2 = PasswordField('Confirm pw', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('Username already exists')
