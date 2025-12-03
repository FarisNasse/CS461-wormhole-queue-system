from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# --- REQUIRED IMPORTS ---
from app.routes.auth import auth_bp
from app.routes.tickets import tickets_bp
from app.routes.error import error_bp


def create_app(testing=False):
    """
    Creates and configures the Flask application instance.
    """
    app = Flask(__name__)

    # ---------------------------------------------------
    # Configuration
    # ---------------------------------------------------
    app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "test-secret"

    # ---------------------------------------------------
    # Initialize Extensions
    # ---------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize LoginManager
    login_manager.init_app(app)
    login_manager.login_view = "auth.assistant_login"
    login_manager.login_message_category = "info"

    # Import models to register them with SQLAlchemy
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
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(error_bp)

    return app
