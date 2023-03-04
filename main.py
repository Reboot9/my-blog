from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import requests
import myforms

app = Flask(__name__)
app.secret_key = "fdffdjj45tktykh"
Bootstrap(app)

url = "https://gist.githubusercontent.com/gellowg/389b1e4d6ff8effac71badff67e4d388/raw/fc31e41f8e1a6b713eafb9859f3f7e335939d518/data.json"
posts = requests.get(url).json()


@app.route("/")
def homepage():
    return render_template("index.html", all_posts=posts)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = None
    for blog_post in posts:
        if blog_post["id"] == post_id:
            requested_post = blog_post
            break
    return render_template("post.html", post=requested_post)


@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form
        print(data["name"])
        print(data["email"])
        print(data["message"])
        return render_template("contact.html", msg_sent=True)
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
    # print(posts[0].keys())
    app.run(debug=True)
