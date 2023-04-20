from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tokens = db.Column(db.Integer, default=200, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VisualNovel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    private = db.Column(db.Boolean, default=False)
    dialogues = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String, nullable=True)
    ip_address = db.Column(db.String, nullable=True)
    location = db.Column(db.String, nullable=True)