import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
import myforms
import bleach  # To clean user input when create post

app = Flask(__name__)
app.config["SECRET_KEY"] = "fdffdjj45tktykh"
ckeditor = CKEditor(app)
Bootstrap(app)

# Connect to DB
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'posts.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


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


@app.route("/")
def homepage():
    # Get last 5 posts
    posts = db.session.query(BlogPost).order_by(BlogPost.id.desc()).limit(5)
    posts = posts[::-1]
    return render_template("index.html", all_posts=posts)


@app.route("/new-post", methods=["GET", "POST"])
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


@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)

    return render_template("post.html", post=requested_post)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
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
    return render_template("contact.html", msg_sent=False)


@app.route("/login", methods=['GET', 'POST'])
def login():
    login_form = myforms.ContactForm()
    if request.method == "POST" and login_form.validate_on_submit():
        if login_form.email.data == "admin@email.com" and login_form.password.data == "12345678":
            return render_template("success_login.html")
        print(login_form.email.data)
        return render_template('denied_login.html')
    return render_template('login.html', form=login_form)


if __name__ == '__main__':
    app.run(debug=True)
