from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:bloggy@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'cornflakes'


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    published = db.Column(db.Boolean)
    date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, published, date, owner):
        self.title = title
        self.body = body
        self.published = published
        self.date = date
        self.owner = owner

    def __repr__(self):
        return '<Post %r>' % self.title


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    post = db.relationship('Post', backref='owner')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password


users = User.query.all()

@app.before_request
def require_login():
    allowed_routes = ['login','signup','index','userblog','blogpost','static']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')



@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        if username == "" or email == "" or password == "":
            flash('Please fill in all fields', 'error')
            return render_template('signup.html', 
                username=username, email=email, owner="")
        
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(username, email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            flash('Logged In Successfully', 'confirm')
            return redirect('/')
        else:
            flash('User already exists', 'error')
    
    users = User.query.all()
    return render_template('signup.html', pagetitle="signup", 
        users=users, owner="")


@app.route('/login', methods=['POST', 'GET'])
def login():
    users = User.query.all()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            flash('Logged In Successfully', 'confirm')
            return redirect('/')
        else:
            flash('Password incorrect or user does not exist', 'error')

    return render_template('login.html', pagetitle="login", 
        users=users, owner="")


@app.route('/logout')
def logout():
    del session['email']
    flash('You are now logged out', 'confirm')
    users = User.query.all()
    return redirect('/')


# OPTIONAL STUFF:
# TODO flash messages as popup that can be cleared manually
# TODO 'EDIT POST' option
# TODO add pagination! (max 7 posts)
# TODO hashing passwords
# TODO cookies


# MAIN PAGE -- DISPLAYS POSTS FROM ALL USERS
@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    if 'email' in session:
        owner = User.query.filter_by(email=session['email']).first()
    else:
        owner = ""
    posts = Post.query.filter_by(published=True).order_by(desc(Post.date)).all()
    return render_template('index.html', pagetitle="Blogz",
        users=users, owner=owner, posts=posts)


# INDIVIDUAL USER PAGE -- DISPLAYS POSTS FROM INDIVIDUAL USER
@app.route('/user', methods=['POST', 'GET'])
def userblog():
    if 'email' in session:
        owner = User.query.filter_by(email=session['email']).first()
    else:
        owner = ""
    user_id = request.args.get('id')
    user = User.query.get(user_id)
    posts = Post.query.filter_by(published=True,owner=user).order_by(desc(Post.date)).all()
    blogname = str(user)+"'s blog"
    return render_template('blog.html', pagetitle=blogname, 
        user=user, users=users, owner=owner, posts=posts)


@app.route('/drafts', methods=['POST', 'GET'])
def drafts():
    owner = User.query.filter_by(email=session['email']).first()
    posts = Post.query.filter_by(published=False,owner=owner).all()
    return render_template('drafts.html', pagetitle="saved drafts", 
        users=users, owner=owner, posts=posts)


# RENDERS INDIVIDUAL POST
@app.route('/post', methods=['POST', 'GET'])
def blogpost():
    if 'email' in session:
        owner = User.query.filter_by(email=session['email']).first()
    else:
        owner = ""
    post_id = request.args.get('id')
    post = Post.query.get(post_id)
    return render_template('post.html', pagetitle=post.title, 
        users=users, owner=owner, post=post)


@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    owner = User.query.filter_by(email=session['email']).first()
    return render_template('newpost.html', pagetitle="new post", 
        users=users, owner=owner)


# PUBLISHES A NEW POST
@app.route('/publish', methods=['POST'])
def publish():
    owner = User.query.filter_by(email=session['email']).first()
    title = request.form['post-title']
    body = request.form['post-body']
    if title != "" and body != "":
        published = True
        date = datetime.utcnow()
        post = Post(title, body, published, date, owner)
        db.session.add(post)
        db.session.commit()
        flash('Post published', 'confirm')
        return render_template("post.html", 
            pagetitle=title, users=users, owner=owner, post=post)
    else:
        flash('Please fill in all fields', 'error')
        return render_template('/newpost.html', 
            pagetitle=title, users=users, body=body, owner=owner)


@app.route('/draft', methods=['POST'])
def draft():
    owner = User.query.filter_by(email=session['email']).first()
    title = request.form['post-title']
    body = request.form['post-body']
    if title != "" and body != "":
        published = False
        date = None
        post = Post(title, body, published, date, owner)
        db.session.add(post)
        db.session.commit()
        flash('Draft Saved', 'confirm')
        return render_template("post.html", pagetitle=title, 
            users=users, owner=owner, post=post)
    else:
        flash('Please fill in all fields', 'error')
        return render_template('/newpost.html', 
            pagetitle=title, users=users, body=body, owner=owner)


@app.route('/publishdraft', methods=['POST'])
def publishdraft():
    post_id = int(request.form['id'])
    post = Post.query.get(post_id)
    post.published = True
    post.date = datetime.utcnow()
    db.session.add(post)
    db.session.commit()
    flash('Draft published!', 'confirm')
    return redirect('/drafts')


@app.route('/deletepost', methods=['POST'])
def delete_post():
    post_id = int(request.form['id'])
    post = Post.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted!', 'confirm')
    return redirect('/')


@app.route('/deletedraft', methods=['POST'])
def delete_draft():
    post_id = int(request.form['id'])
    post = Post.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Draft deleted!', 'confirm')
    return redirect('/drafts')


if __name__ == '__main__':
    app.run()