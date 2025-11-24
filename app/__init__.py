# app/__init__.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(testing=False):
    """
    Application factory for the Wormhole Queue System.

    Supports:
    - normal mode (sqlite file)
    - testing mode (SQLite in-memory)
    """

    app = Flask(__name__)

    # -----------------------------
    # Testing Configuration
    # -----------------------------
    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret"
    else:
        # -----------------------------
        # Normal Development/Production Config
        # -----------------------------
        app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
        app.config.setdefault("SECRET_KEY", "dev-secret-key")

    # -----------------------------
    # Initialize Extensions
    # -----------------------------
    db.init_app(app)

    # -----------------------------
    # Root test route
    # -----------------------------
    @app.route("/")
    def index():
        return jsonify({"message": "Welcome to the Wormhole Queue System API!"}), 200

    # -----------------------------
    # Register Blueprints
    # -----------------------------
    from app.routes.auth import auth_bp

    # Optional: tickets blueprint if it exists
    try:
        from app.routes.tickets import tickets_bp
    except ModuleNotFoundError:
        tickets_bp = None

    app.register_blueprint(auth_bp)

    if tickets_bp:
        app.register_blueprint(tickets_bp)

    return app
