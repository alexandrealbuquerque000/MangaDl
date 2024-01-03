from . import db
from flask_login import UserMixin

favorites = db.Table  ('favorites', 
                            db.Column('User_id', db.Integer, db.ForeignKey('users.id')), 
                            db.Column('Title_id', db.Integer, db.ForeignKey('titles.id'))
                        )

checkpoints = db.Table  ('checkpoints', 
                            db.Column('User_id', db.Integer, db.ForeignKey('users.id')), 
                            db.Column('Content_id', db.Integer, db.ForeignKey('contents.id'))
                        )

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String, unique=True)
    Password = db.Column(db.String)

class Servers(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String)
    Config = db.Column(db.JSON, nullable=True)

class Titles(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String)
    Description = db.Column(db.String)
    URL = db.Column(db.String)
    user_favorites = db.relationship('Users', secondary=favorites, backref=db.backref('Favorites', lazy='dynamic'))
    Ower_id = db.Column(db.Integer, db.ForeignKey('servers.id'))
    Ower = db.relationship('Servers', backref=db.backref('Backref', lazy='dynamic', order_by='Titles.Name'))

class Contents(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String)
    URL = db.Column(db.String)
    user_checkpoints = db.relationship('Users', secondary=checkpoints, backref=db.backref('Checkpoints', lazy='dynamic'))
    Ower_id = db.Column(db.Integer, db.ForeignKey('titles.id'))
    Ower = db.relationship('Titles', backref=db.backref('Backref', lazy='dynamic'))

class Subcontents(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String)
    URL = db.Column(db.String)
    Ower_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    Ower = db.relationship('Contents', backref=db.backref('Backref', lazy='dynamic'))