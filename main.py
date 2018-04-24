from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:bloggy@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'cornflakes'


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    published = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, published, owner):
        self.title = title
        self.body = body
        self.published = published
        self.owner = owner


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blog = db.relationship('Blog', backref='owner')

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
    
    return render_template('register.html')


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

    return render_template('login.html')


@app.route('/logout')
def logout():
    del session['email']
    flash('You are now logged out', 'confirm')
    return redirect('/')


@app.route('/', methods=['POST', 'GET'])
def index():
    owner = User.query.filter_by(email=session['email']).first()
    blogs = Blog.query.filter_by(published=True,owner=owner).all()
    return render_template('blog.html', owner=owner, blogs=blogs)


@app.route('/drafts', methods=['POST', 'GET'])
def drafts():
    owner = User.query.filter_by(email=session['email']).first()
    blogs = Blog.query.filter_by(published=False,owner=owner).all()
    return render_template('drafts.html', blogs=blogs)


# TODO make an html template to display individual posts
# TODO make a route for this so that route('/blog?id=#')
@app.route('/blog')
def blogpost():
    id = request.args.get('blog-id')
    return redirect('/blog')

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    return render_template('newpost.html')


@app.route('/publish', methods=['POST'])
def publish():
    owner = User.query.filter_by(email=session['email']).first()
    title = request.form['post-title']
    body = request.form['post-body']
    if title != "" and body != "":
        published = True
        blog = Blog(title, body, published, owner)
        db.session.add(blog)
        db.session.commit()
        flash('Post published', 'confirm')
        return redirect('/blog')
    else:
        flash('Please fill in all fields', 'error')
        return render_template('/newpost.html', 
            title=title, body=body, owner=owner)


@app.route('/draft', methods=['POST'])
def draft():
    owner = User.query.filter_by(email=session['email']).first()
    title = request.form['post-title']
    body = request.form['post-body']
    published = False
    blog = Blog(title, body, published, owner)
    db.session.add(blog)
    db.session.commit()
    flash('Draft Saved', 'confirm')
    return redirect('/')


@app.route('/publishdraft', methods=['POST'])
def publishdraft():
    blog_id = int(request.form['blog-id'])
    blog = Blog.query.get(blog_id)
    blog.published = True
    db.session.add(blog)
    db.session.commit()
    flash('Draft published!', 'confirm')
    return redirect('/drafts')


@app.route('/deletepost', methods=['POST'])
def delete_post():
    blog_id = int(request.form['blog-id'])
    blog = Blog.query.get(blog_id)
    db.session.delete(blog)
    db.session.commit()
    flash('Post deleted!', 'confirm')
    return redirect('/')


@app.route('/deletedraft', methods=['POST'])
def delete_draft():
    blog_id = int(request.form['blog-id'])
    blog = Blog.query.get(blog_id)
    db.session.delete(blog)
    db.session.commit()
    flash('Draft deleted!', 'confirm')
    return redirect('/drafts')


if __name__ == '__main__':
    app.run()