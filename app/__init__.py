# app/__init__.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # [Restored Import]
from config import Config          # [Restored Import]

db = SQLAlchemy()
migrate = Migrate()                # [Restored Instance]

def create_app(testing=False):
    """
    Application factory for the Wormhole Queue System.

    Supports:
    - normal mode (sqlite file on disk)
    - testing mode (SQLite in-memory DB)

    This function is used by production, development, and pytest.
    """
    app = Flask(__name__)

    # ---------------------------------------------------
    # Configuration
    # ---------------------------------------------------
    # [Fix] Load the base Config class first (restores normal DB path)
    app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret"
    
    # [Fix] Removed the 'else' block with hardcoded relative paths. 
    # The app.config.from_object(Config) call above handles the 
    # production/dev configuration correctly now.

    # ---------------------------------------------------
    # Initialize Extensions
    # ---------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)  # [Fix] Initialize Flask-Migrate

    # [Fix] Import models to register them with SQLAlchemy
    # This must happen after db.init_app but before the app runs
    from app import models 

    # ---------------------------------------------------
    # Root test route (CI / smoke test)
    # ---------------------------------------------------
    # [Fix] Changed route to '/health' to avoid conflict with auth_bp
    @app.route("/health")
    def health_check():
        return jsonify({"message": "Wormhole Queue System API is running"}), 200

    # ---------------------------------------------------
    # Register Blueprints
    # ---------------------------------------------------
    from app.routes.auth import auth_bp

    try:
        from app.routes.tickets import tickets_bp
    except ModuleNotFoundError:
        tickets_bp = None

    # Register auth routes
    app.register_blueprint(auth_bp)

    # Register tickets routes ONLY if file exists
    if tickets_bp:
        app.register_blueprint(tickets_bp)

    return app