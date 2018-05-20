from application import db
from datetime import datetime

class Parameters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    param_id = db.Column(db.String(32), unique=True, nullable=False)
    param_value = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<Parameters "+self.param_id+" => "+self.param_value+">"
    
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True)
    currency = db.Column(db.Integer, nullable=False, default=0)
    viewer_since = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    hours_watched= db.Column(db.Integer, nullable=False, default=0)
    songs_requested= db.Column(db.Integer, nullable=False, default=0)
    def __init__(self, notes):
        self.notes = notes

    def __repr__(self):
        return '<Users %r>' % self.username

class Commands(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command=db.Column(db.String(16), nullable=False, unique=True)
    description=db.Column(db.Text, nullable=False)
    function=db.Column(db.PickleType, nullable=False)
    isShoutout=db.Column(db.Boolean, nullable=False, default=False)
    shoutoutId=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return '<Commands %r>' % self.command
    
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youtube_id= db.Column(db.String(16), nullable=False)
    title= db.Column(db.Text, nullable=False)
    file_location= db.Column(db.Text, nullable=False)
    user_added= db.Column(db.String(32), nullable=False)
    date_added= db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    num_plays = db.Column(db.Integer, nullable=False, default=0)
    
    def __repr__(self):
        return '<Playlist %r>' % self.youtube_id

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youtube_id= db.Column(db.String(16), nullable=False)
    title= db.Column(db.Text, nullable=False)
    file_location= db.Column(db.Text, nullable=False)
    user_added= db.Column(db.String(32), nullable=False)
    date_added= db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<Request %r>' % self.youtube_id
