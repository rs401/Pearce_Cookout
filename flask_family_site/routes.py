## Import all the things
# STD
import os
import shutil
import secrets
# Third party
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
# Local
from flask_family_site.models import User, Post
from flask_family_site.forms import (Registration_Form, Login_Form, \
        Update_Account_Form, Post_Form, Request_Reset_Form, \
        Reset_Password_Form)
from flask_family_site import app, db, bcrypt, mail

## app.route's
# Main or Home page(index)
@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, \
            per_page=5)
    pic_path = os.path.join(app.root_path, 'static/post_pics/')
    return render_template('home.html', posts=posts, os=os, pic_path=pic_path)

# About page
@app.route("/about")
def about():
    return render_template('about.html', title='About')

# Login page
@app.route("/login", methods=['GET','POST'])
def login():
    # Check if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # From our forms.py local import
    form = Login_Form()
    # If POST request
    if form.validate_on_submit():
        # Check against db
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, \
                form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else \
                    redirect(url_for('home'))
        else:
            flash('Unsuccessful Login! Please check your email and password',\
                'danger')
    # Return for GET request
    return render_template('login.html', title='Login', form=form)

# Register page
@app.route("/register", methods=['GET','POST'])
def register():
    # Check if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # From our forms.py local import
    form = Registration_Form()
    # If POST request
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)\
                .decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, \
                password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created. You can now Log In', 'success')
        return redirect(url_for('login'))
    # Return for GET request
    return render_template('register.html', title='Register', form=form)


# Logout function and route with redirect to home
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# Function to handle saving profile pic
def save_profile_pic(form_pic):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_pic.filename)
    profile_pic = random_hex + f_ext
    pic_path = os.path.join(app.root_path, 'static/profile_pics', profile_pic)

    output_size = (125,125)
    i = Image.open(form_pic)
    i.thumbnail(output_size)
    i.save(pic_path)

    return profile_pic

# Account update function and route
@app.route("/account", methods=['GET','POST'])
@login_required
def account():
    form = Update_Account_Form()
    if form.validate_on_submit():
        if form.pic.data:
            pic_file = save_profile_pic(form.pic.data)
            current_user.profile_image = pic_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated.', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + \
            current_user.profile_image)
    return render_template('account.html', title='My Account', \
            image_file=image_file, form=form)

# Save Post pics
def save_post_pics(pic,dir):
    post_pics_dir = dir
    pics_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(pic.filename)
    the_pic = pics_hex + f_ext
    pic_path = os.path.join(app.root_path, 'static/post_pics', post_pics_dir, \
            the_pic)

    base_width = 600
    i = Image.open(pic)
    wpercent = (base_width/float(i.size[0]))
    hsize = int((float(i.size[1])*float(wpercent)))
    i_resized = i.resize((base_width,hsize), Image.ANTIALIAS)
    i_resized.save(pic_path)
    return the_pic

# Save Post dir
def save_post_dir():
    dir_hex = secrets.token_hex(8)
    return dir_hex

# Create Post function and route
@app.route("/post/new", methods=['GET','POST'])
@login_required
def new_post():
    form = Post_Form()
    if form.validate_on_submit():
        post_pics_dir = save_post_dir()
        post = Post(title=form.title.data,content=form.content.data, \
                images=post_pics_dir, author=current_user)
        db.session.add(post)
        db.session.commit()
        new_dir = os.path.join(app.root_path, 'static/post_pics', \
                post_pics_dir)
        os.makedirs(new_dir)
        post_files = []
        for file in form.images.data:
            post_files = save_post_pics(file, post_pics_dir)
            print(post_files)
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, \
            legend='New Post', update=False)

# View Post function and route
@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    pic_path = os.path.join(app.root_path, 'static/post_pics/')
    return render_template('post.html', title=post.title, post=post, os=os, \
            pic_path=pic_path)

# Update Post function and route
@app.route("/post/<int:post_id>/update", methods=['GET','POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = Post_Form()

    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', title='Update Post', form=form,\
            legend='Update Post', update=True)

# Delete pics helper
def delete_pics(post_dir):
    pic_path = os.path.join(app.root_path, 'static/post_pics/')
    path = pic_path + post_dir
    shutil.rmtree(path)

# Delete Post function and route
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    post_dir = post.images
    delete_pics(post_dir)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


# User's Posts function and route
@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
            .order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    pic_path = os.path.join(app.root_path, 'static/post_pics/')
    return render_template('user_posts.html', user=user, posts=posts, os=os, \
            pic_path=pic_path)

# Reset email helper
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request.', sender='noreply@demo.com', \
            recipients=[user.email])
    msg.body = f'''
To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not send this request, simply ignore this email and no \
changes will be made.
'''
    mail.send(msg)

# Request Reset Password function and route
@app.route("/reset_password", methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = Request_Reset_Form()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your \
                password','info')
        return redirect(url_for('login'))
    return render_template('request_reset.html', title='Reset Password', \
            form=form)


# Reset Password function and route
@app.route("/reset_password/<token>", methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('reset_request'))
    form = Reset_Password_Form()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)\
                .decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated. You can now Log In', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', \
            form=form)









