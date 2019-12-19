## Import all the things
# STD
import os
import secrets
# Third party
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
# Local
from flask_family_site.models import User, Post
from flask_family_site.forms import Registration_Form, Login_Form, Update_Account_Form
from flask_family_site import app, db, bcrypt


# Fake data for early testing
posts = [
        {
            'author': 'Rich Stadnick',
            'title': 'First Post',
            'content': 'First post content',
            'date_posted': 'April 20th, 2019'
            },
        {
            'author': 'Shawna Stadnick',
            'title': 'Second Post',
            'content': 'Second post content',
            'date_posted': 'April 25th, 2019'
            }
        ]

## app.route's
# Main or Home page(index)
@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)

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

