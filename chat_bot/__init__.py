# chat_bot/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from chat_bot.config import Config
from chat_bot.celery_worker.celery_worker_app import make_celery
from chat_bot.logging_configurations import configure_logging

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        SQLALCHEMY_DATABASE_URI='sqlite:///appointments.db'
    )

    instance_config_path = os.path.join(app.instance_path, 'config.py')
    app.config.from_pyfile(instance_config_path, silent=True)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config.from_object(Config)
    configure_logging(app, config=Config)


    from flask_session import Session
    Session(app)



    # Initialize the SQLAlchemy and Flask-Bcrypt extensions
    from .models import db, bcrypt, migrate, login_manager
    from . import models
    app.register_blueprint(models.bp)
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'


    # Initialize Celery
    celery = make_celery(app)
    celery.set_default()

    # Initialize auth route
    from . import auth
    app.register_blueprint(auth.bp)

    # Initialize auth2callback route
    from . import calendar_api
    app.register_blueprint(calendar_api.calendar_bp)

    # Initialize main_page route
    from . import main_page
    app.register_blueprint(main_page.bp, url_prefix='/')
    app.add_url_rule('/', endpoint='index')

    # Initialize user_input module route
    from .user_input import bp as user_input
    app.register_blueprint(user_input)

    from .appointment import bp as appointment_bp
    appointment_bp.celery = celery
    app.register_blueprint(appointment_bp)

    from .mail_sending import mail
    mail.init_app(app)

    from .session_tracker import bp as session_tracker
    app.register_blueprint(session_tracker)

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
