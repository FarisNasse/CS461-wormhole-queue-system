# app/__init__.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(testing=False):
    """
    Application factory for the Wormhole Queue System.

    Supports:
    - normal mode (sqlite file)
    - testing mode (SQLite in-memory DB)

    This function is used by production, development, and pytest.
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
        # Normal (Development/Production)
        # -----------------------------
        app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
        app.config.setdefault("SECRET_KEY", "dev-secret-key")

    # -----------------------------
    # Initialize database
    # -----------------------------
    db.init_app(app)

    # -----------------------------
    # Simple root route (for testing)
    # -----------------------------
    @app.route("/")
    def index():
        return jsonify({"message": "Welcome to the Wormhole Queue System API!"}), 200

    # -----------------------------
    # Register Blueprints
    # -----------------------------
    from app.routes.auth import auth_bp

    # Some teams put tickets in app/routes/tickets.py — adjust this if needed:
    try:
        from app.routes.tickets import tickets_bp
    except ModuleNotFoundError:
        tickets_bp = None

    # Optional error blueprint
    try:
        from app.routes.error import error_bp
        app.register_blueprint(error_bp)
    except ModuleNotFoundError:
        pass

    app.register_blueprint(auth_bp)

    if tickets_bp:
        app.register_blueprint(tickets_bp)

    return app
