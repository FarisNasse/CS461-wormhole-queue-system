# app/__init__.py
<<<<<<< Updated upstream
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
=======
from flask import Flask, jsonify, redirect, render_template, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

>>>>>>> Stashed changes
from config import Config


db = SQLAlchemy()
migrate = Migrate()
<<<<<<< Updated upstream

# --- REQUIRED IMPORTS ---
# We import these at the top level. If they fail (e.g., syntax error or missing file),
# the application will crash immediately with a helpful traceback.
from app.routes.auth import auth_bp
from app.routes.tickets import tickets_bp
=======
login = LoginManager()
login.login_view = "auth.assistant_login"  # Where to send users who aren't logged in

>>>>>>> Stashed changes

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

    # Import models to register them with SQLAlchemy (needed for db setup)
    from app import models 

    # ---------------------------------------------------
<<<<<<< Updated upstream
    # Health Check Route
=======
    # COMPATIBILITY LAYER (The Professional Fix)
    # ---------------------------------------------------

    # 1. Context Shim: Allows templates to use 'user' instead of 'current_user'
    @app.context_processor
    def inject_user_context():
        u = current_user if current_user.is_authenticated else None
        return dict(current_user=current_user, user=u)

    # 2. Route Shims: Aliases for old route names found in templates
    # These prevent BuildErrors without editing every HTML file.
    @app.route("/shim/login")
    def login_alias():
        return redirect(url_for("auth.assistant_login"))

    @app.route("/shim/index")
    def index_alias():
        return redirect(url_for("auth.index"))

    @app.route("/shim/createhelprequest")
    def create_ticket_alias():
        return redirect(url_for("tickets.create_ticket_page"))

    @app.route("/shim/livequeue")
    def live_queue_alias():
        return redirect(url_for("tickets.live_queue"))

    @app.route("/shim/userpage/<username>")
    def userpage_alias(username):
        return redirect(url_for("auth.user_profile"))

    # [Shim] Fixes 'auth.change_password' error in userpage.html
    @app.route("/shim/change-password")
    def change_password_shim():
        # We don't have a change password page yet, so redirect to profile
        return redirect(url_for("auth.user_profile"))

    # Add these specific endpoint overrides so url_for works
    # This is the "Magic" that stops the BuildErrors
    with app.app_context():
        app.add_url_rule(
            "/shim/change-password",
            endpoint="auth.change_password",
            view_func=change_password_shim,
        )

    app.route("/userpage")

    def userpage():
        if current_user.is_authenticated:
            return redirect(url_for("auth.user_profile"))
        return redirect(url_for("auth.assistant_login"))

    # ---------------------------------------------------
    # Error Handlers
    # ---------------------------------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    # ---------------------------------------------------
    # Health Check
>>>>>>> Stashed changes
    # ---------------------------------------------------
    @app.route("/health")
    def health_check():
        return jsonify({"message": "Wormhole Queue System API is running"}), 200

    # ---------------------------------------------------
    # Register Blueprints
    # ---------------------------------------------------
<<<<<<< Updated upstream
    # The imports happened at the top of the file, so we just register them here.
=======
    from app.routes.auth import auth_bp
    from app.routes.tickets import tickets_bp

>>>>>>> Stashed changes
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)

    return app
