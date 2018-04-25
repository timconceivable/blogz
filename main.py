from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:bloggy@localhost:8889/build-a-blog'
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



@app.before_request
def require_login():
    allowed_routes = ['login','register']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        if username == "" or email == "" or password == "":
            flash('Please fill in all fields', 'error')
            return render_template('register.html', 
                username=username, email=email)
        
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
    
    return render_template('register.html', pagetitle="register")


@app.route('/login', methods=['POST', 'GET'])
def login():
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

    return render_template('login.html', pagetitle="login")


@app.route('/logout')
def logout():
    del session['email']
    flash('You are now logged out', 'confirm')
    return redirect('/')


# MAIN BLOG PAGE
@app.route('/', methods=['POST', 'GET'])
def index():
    owner = User.query.filter_by(email=session['email']).first()
    posts = Post.query.filter_by(published=True,owner=owner).order_by(desc(Post.date)).all()
    blogname = str(owner.username)+"'s blog"
    return render_template('blog.html', pagetitle=blogname,
        owner=owner, posts=posts)


@app.route('/drafts', methods=['POST', 'GET'])
def drafts():
    owner = User.query.filter_by(email=session['email']).first()
    posts = Post.query.filter_by(published=False,owner=owner).all()
    return render_template('drafts.html', pagetitle="saved drafts", 
        owner=owner, posts=posts)


# INDIVIDUAL POST PAGE
@app.route('/blog', methods=['POST', 'GET'])
def blogpost():
    owner = User.query.filter_by(email=session['email']).first()
    post_id = request.args.get('id')
    post = Post.query.get(post_id)
    return render_template('blogpost.html', pagetitle=post.title, 
        owner=owner, post=post)


@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    owner = User.query.filter_by(email=session['email']).first()
    return render_template('newpost.html', pagetitle="new post", owner=owner)


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
        return render_template("blogpost.html", 
            pagetitle=title, owner=owner, post=post)
    else:
        flash('Please fill in all fields', 'error')
        return render_template('/newpost.html', 
            pagetitle=title, body=body, owner=owner)


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
        return render_template("blogpost.html", 
            pagetitle=title, owner=owner, post=post)
    else:
        flash('Please fill in all fields', 'error')
        return render_template('/newpost.html', 
            pagetitle=title, body=body, owner=owner)


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