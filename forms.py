from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Regexp, equal_to
from flask_wtf import Form
from models import User

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