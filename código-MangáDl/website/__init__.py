from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .Functions import verifpath, Get_ExactTable
import os

db = SQLAlchemy()
DB_DIR = 'database.db'


#Apenas enquanto teste!
DB_DIR = os.path.join(os.path.expanduser("~/Desktop"), DB_DIR)
#

def create_app():

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'SECRET_KEY'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(DB_DIR)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import Users

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(Id):
        
        return Get_ExactTable(Users, {'id': Id}).first()

    return app


def create_database(app):
    if not verifpath(DB_DIR, 0): 
        db.create_all(app=app)
