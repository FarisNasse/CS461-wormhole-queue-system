# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

# Define extensions here, but do NOT bind them to the app yet.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO()