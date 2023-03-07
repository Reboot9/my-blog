from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
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


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")
