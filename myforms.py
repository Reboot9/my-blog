from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from wtforms.validators import DataRequired
import email_validator


class ContactForm(FlaskForm):
    email = StringField(label='Email', validators=[
        validators.Length(min=6, message=u"email is too short"),
        validators.Email(), DataRequired()
    ])
    password = PasswordField(label="Password", validators=[
        validators.Length(min=4), DataRequired()
    ])
    submit = SubmitField(label="Log in")
