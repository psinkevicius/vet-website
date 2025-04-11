from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
import os
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

db = SQLAlchemy()
mail = Mail()
oauth = OAuth()
DB_NAME = "database.db"

LOG_FILE = 'logs/activity.log'


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    migrate = Migrate(app, db)

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    mail.init_app(app)

    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_handler = ConcurrentRotatingFileHandler(LOG_FILE, maxBytes=10240, backupCount=3, encoding='utf-8')
    log_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)
    app.logger.addHandler(log_handler)
    app.logger.setLevel(logging.INFO)

    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=os.getenv('OAUTH_CLIENT_ID'),
        client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'token_endpoint_auth_method': 'client_secret_post',
        },
        userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo'
    )

    from .notes import notes
    from .auth import auth
    from .chatbot import chatbot
    from .admin import admin
    from .animals import animals
    from .appointment import appointment

    app.register_blueprint(notes, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(chatbot, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')
    app.register_blueprint(animals, url_prefix='/')
    app.register_blueprint(appointment, url_prefix='/')

    from .models import User, Note
    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    import atexit

    @atexit.register
    def cleanup_logging():
        logging.shutdown()

    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')
