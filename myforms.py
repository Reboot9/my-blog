from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
import email_validator


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    name = StringField("Username", validators=[DataRequired()])
    email = StringField(label='Email', validators=[
        validators.Length(min=6, message=u"Email is too short"),
        validators.Email(), DataRequired()
    ])
    password = PasswordField(label="Password", validators=[
        validators.Length(min=4, message=u"Password has to be at least 4 characters long"), DataRequired()
    ])
    submit = SubmitField(label="Sign in")


class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[
        validators.Length(min=6, message=u"Email is too short"),
        validators.Email(), DataRequired()
    ])
    password = PasswordField(label="Password", validators=[
        validators.Length(min=4, message=u"Password has to be at least 4 characters long"), DataRequired()
    ])
    submit = SubmitField(label="Log in")
