import json
import logging
from datetime import datetime

from flask import (
    jsonify, Blueprint
)
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('model', __name__)
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


@bp.errorhandler(SQLAlchemyError)
def handle_database_error(e):
    # Log error
    logger.error(f'Database error: {str(e)}')
    # user-friendly response
    return jsonify({'error': 'A database error occurred'}), 500


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    google_calendar_token = db.Column(db.String(200))  # store google calendar API token
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    conversations = db.relationship('Conversation', backref='user', lazy=True)

    # def set_google_calendar_token(self, token):
    #     self.google_calendar_token = token
    #     db.session.commit()
    #     print(f"User ID: {self.id}, Google Calendar Token: {token}")

    # Existing code
    def set_google_calendar_token(self, token):
        self.google_calendar_token = token
        db.session.commit()
        print(f"User ID: {self.id}, Google Calendar Token: {token}")

    # def get_google_calendar_token(self):
    #     return json.loads(self.google_calendar_token) if self.google_calendar_token else None

    # Updated code
    def get_google_calendar_token(self):
        return json.loads(self.google_calendar_token) if self.google_calendar_token else None


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))
    event_id = db.Column(db.String(255), unique=True)
    date = db.Column(db.DateTime(timezone=True))
    time = db.Column(db.String(10))
    title = db.Column(db.String(100))
    location = db.Column(db.String(100))
    description = db.Column(db.Text())

    def __init__(self, user_id, date, event_id, time, title, location, description):
        self.user_id = user_id
        self.event_id = event_id
        self.date = date
        self.time = time
        self.title = title
        self.location = location
        self.description = description


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_input = db.Column(db.String(1000))
    bot_response = db.Column(db.String(1000))

    def __repr__(self):
        return f"<Conversation {self.id}>"
