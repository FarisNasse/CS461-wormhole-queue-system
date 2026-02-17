# app/__init__.py
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from config import Config

# Extensions are initialized at the top level
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()


def create_app(testing=False):
    """
    Create and configure the Flask application instance.

    Parameters
    ----------
    testing : bool, optional
        If True, configure the application for testing. This enables
        Flask's testing mode, uses an in-memory SQLite database, disables
        CSRF protection, and sets a deterministic secret key.

    Returns
    -------
    Flask
        The configured Flask application instance.
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

    # ---------------------------------------------------
    # Internal Imports & Registration
    # ---------------------------------------------------
    # Moving these inside create_app prevents circular imports and E402 errors.
    # The '# noqa: F401' tells Ruff that although the import isn't used directly
    # in this file, it is intentional (for registering models and events).
    from app import models  # noqa: F401
    from app.routes import queue_events  # noqa: F401
    from app.routes.auth import auth_bp
    from app.routes.error import error_bp
    from app.routes.tickets import tickets_bp
    from app.routes.views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(error_bp)

    # ---------------------------------------------------
    # Health Check Route
    # ---------------------------------------------------
    @app.route("/health")
    def health_check():
        return jsonify({"message": "Wormhole Queue System API is running"}), 200

    # ---------------------------------------------------
    # Template context processors
    # ---------------------------------------------------
    from types import SimpleNamespace

    @app.context_processor
    def inject_current_user():
        from flask import session

        try:
            if "user_id" in session:
                from app.models import User

                u = db.session.get(User, session["user_id"])
                if u:
                    return {
                        "current_user": SimpleNamespace(
                            is_admin=bool(u.is_admin),
                            is_anonymous=False,
                            username=u.username,
                        )
                    }
        except Exception:
            # keep silent on DB errors; fall back to anonymous
            pass

        return {
            "current_user": SimpleNamespace(
                is_admin=False, is_anonymous=True, username=""
            )
        }

    from app.routes.users import user_bp

    app.register_blueprint(user_bp)

    return app
