# app/__init__.py
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()

# --- REQUIRED IMPORTS ---
# We import these at the top level. If they fail (e.g., syntax error or missing file),
# the application will crash immediately with a helpful traceback.
from app.routes.auth import auth_bp
from app.routes.views import views_bp
from app.routes.tickets import tickets_bp
from app.routes import queue_events  # Import SocketIO events

def create_app(testing=False):
    """
    Creates and configures the Flask application instance.
    
    Args:
        testing (bool): If True, configures the app for testing with an
            in-memory SQLite database.
            
    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)

    # ---------------------------------------------------
    # Configuration
    # ---------------------------------------------------
    app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret"

    # ---------------------------------------------------
    # Initialize Extensions
    # ---------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    # Import models to register them with SQLAlchemy (needed for db setup)
    from app import models 

    # ---------------------------------------------------
    # Health Check Route
    # ---------------------------------------------------
    @app.route("/health")
    def health_check():
        return jsonify({"message": "Wormhole Queue System API is running"}), 200

    # ---------------------------------------------------
    # Register Blueprints
    # ---------------------------------------------------
    # The imports happened at the top of the file, so we just register them here.
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(tickets_bp)

    # ---------------------------------------------------
    # Template context processors
    # ---------------------------------------------------
    from types import SimpleNamespace

    @app.context_processor
    def inject_current_user():
        from flask import session
        try:
            if 'user_id' in session:
                from app.models import User
                u = User.query.get(session['user_id'])
                if u:
                    return {
                        'current_user': SimpleNamespace(
                            is_admin=bool(u.is_admin),
                            is_anonymous=False,
                            username=u.username,
                        )
                    }
        except Exception:
            # keep silent on DB errors; fall back to anonymous
            pass

        return {'current_user': SimpleNamespace(is_admin=False, is_anonymous=True, username='')}

    return app
