# app/__init__.py
from flask import Flask, jsonify
from config import Config

# IMPORT FROM THE NEW EXTENSIONS MODULE
from app.extensions import db, migrate, login_manager, mail, limiter, socketio

def create_app(testing=False):
    """
    Application Factory: Creates and configures the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret"

    # ---------------------------------------------------
    # Initialize Extensions
    # ---------------------------------------------------
    # This binds the extensions to this specific app instance
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Configure Login Manager
    login_manager.login_view = "auth.assistant_login"
    login_manager.login_message_category = "info"

    # ---------------------------------------------------
    # Import Models
    # ---------------------------------------------------
    # We import models here so SQLAlchemy knows about them before we run migrations
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
    # Imports are inside the function to prevent premature loading
    from app.routes.auth import auth_bp
    from app.routes.error import error_bp
    from app.routes.tickets import tickets_api_bp, tickets_html_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_html_bp)
    app.register_blueprint(tickets_api_bp)
    app.register_blueprint(error_bp)

    return app