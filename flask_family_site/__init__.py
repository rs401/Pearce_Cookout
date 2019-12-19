## Import all the things
# 3rd Party
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
# Local
from flask_family_site.my_config import my_secret

## Config
app = Flask(__name__)
app.config['SECRET_KEY'] = my_secret
# SQLite because this app will never go over 100k hits/day
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from flask_family_site import routes
