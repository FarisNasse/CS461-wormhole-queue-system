# app/__init__.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

# --- REQUIRED IMPORTS (Fail Loudly) ---
# The auth and tickets blueprints are CRITICAL to the app's function.
# If they fail to import, the app should halt immediately.

try:
    from app.routes.auth import auth_bp
    from app.routes.tickets import tickets_bp
except Exception as e:
    # Use RuntimeError to stop the application startup process if a critical dependency fails.
    # This prevents the app from running in a broken state.
    raise RuntimeError(f"FATAL: Failed to import critical blueprints: {e}")


def create_app(testing=False):
    """
    Application factory for the Wormhole Queue System.
    # ... docstring content ...
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
    # These imports are guaranteed to succeed because they were verified 
    # outside this function (above) with the try/except block.
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)

    return app