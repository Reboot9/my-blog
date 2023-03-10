import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from functools import wraps
import myforms
import bleach  # To clean user input when create post

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
ckeditor = CKEditor(app)
Bootstrap(app)

# Connect to DB
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'posts.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app, size=50, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = relationship("User", back_populates="posts")  # db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship("Comments", back_populates="parent_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100), unique=True)

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")


class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


def strip_invalid_html(content):
    """Strips invalid tags/attributes"""
    allowed_tags = frozenset(('a', 'abbr', 'acronym', 'address', 'b', 'br', 'div', 'dl', 'dt',
                              'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                              'li', 'ol', 'p', 'pre', 'q', 's', 'small', 'strike',
                              'span', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                              'thead', 'tr', 'tt', 'u', 'ul'))

    allowed_attrs = {
        'a': frozenset(('href', 'target', 'title')),
        'img': frozenset(('src', 'alt', 'width', 'height')),
    }

    cleaned = bleach.clean(content,
                           tags=allowed_tags,
                           attributes=allowed_attrs,
                           strip=True)

    return cleaned


def admin_only(func):
    """My superuser decorator to make sure user with id=1 is admin"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return func(*args, **kwargs)

    return wrapper


@login_manager.user_loader
def load_user(user_id: int):
    return db.session.get(User, user_id)


@app.route("/")
def homepage():
    # Get last 5 posts
    posts = db.session.query(BlogPost).order_by(BlogPost.id.desc()).limit(5)
    posts = posts[::-1]
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
@admin_only
def create_post():
    form = myforms.CreatePostForm()
    if form.validate_on_submit():
        all_post_data = {item: strip_invalid_html(value.data) for item, value in form._fields.items() if
                         item not in ['submit', 'csrf_token']}
        current_date = datetime.now().strftime("%B %d, %Y")
        # cleaned_post_body = strip_invalid_html(form.body.data)

        new_post = BlogPost(date=current_date, **all_post_data)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('homepage'))
    return render_template("make_post.html", form=form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = myforms.CommentForm()

    if comment_form.validate_on_submit():
        new_comment = Comments(
            text=strip_invalid_html(comment_form.comment_text.data),
            comment_author=current_user,
            parent_post=requested_post
        )

        db.session.add(new_comment)
        db.session.commit()
        comment_form.comment_text.data = ""  # Clear comment text field after saving it in new_comment variable

        return redirect(url_for('show_post', post_id=post_id))

    return render_template("post.html", post=requested_post, form=comment_form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    edit_form = myforms.CreatePostForm(
        title=requested_post.title,
        subtitle=requested_post.subtitle,
        img_url=requested_post.img_url,
        author=requested_post.author,
        body=requested_post.body
    )
    if edit_form.validate_on_submit():
        # Changing requested_post info to what user wrote in edit_form
        [setattr(requested_post, field.name, strip_invalid_html(field.data)) for field in edit_form if
         field.name not in ['submit', 'csrf_token']]

        db.session.commit()
        return redirect(url_for('show_post', post_id=requested_post.id))

    return render_template("make_post.html", form=edit_form, is_edit=True)


@app.route("/delete-post/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()

    return redirect(url_for('homepage'))


@app.route('/contact', methods=["GET", "POST"])
def contact():
    # if request.method == "POST":
    #     data = request.form
    #     print(data["name"])
    #     print(data["email"])
    #     print(data["message"])
    #     return render_template("contact.html", msg_sent=True)
    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = myforms.RegisterForm()
    if register_form.validate_on_submit():
        # User already exists
        if User.query.filter_by(email=request.form.get('email')).first():
            flash("This email is already in use, try to log in")
            return redirect(url_for("login"))

        hashed_password = generate_password_hash(
            register_form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(
            email=register_form.email.data,
            password=hashed_password,
            name=register_form.name.data
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("homepage"))
    return render_template("register.html", form=register_form, logged_in=current_user.is_authenticated)


@app.route("/login", methods=['GET', 'POST'])
def login():
    login_form = myforms.LoginForm()
    if login_form.validate_on_submit():
        password = login_form.password.data
        user = User.query.filter_by(email=login_form.email.data).first()

        if not user:
            flash("There's no account with this email registered")
        elif not check_password_hash(user.password, password):
            flash("Wrong password, try again")
        else:
            login_user(user)
            return redirect(url_for("homepage"))

    return render_template("login.html", form=login_form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("homepage"))


if __name__ == '__main__':
    app.run(debug=True)
