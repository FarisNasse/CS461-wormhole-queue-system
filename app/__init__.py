# app/__init__.py
from flask import Flask, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.assistant_login' # Where to send users who aren't logged in

def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret"

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from app import models

    # User Loader for Flask-Login
    @login.user_loader
    def load_user(id):
        return db.session.get(models.User, int(id))

    # ---------------------------------------------------
    # COMPATIBILITY LAYER (The Professional Fix)
    # ---------------------------------------------------
    
    # 1. Context Shim: Allows templates to use 'user' instead of 'current_user'
    @app.context_processor
    def inject_user_context():
        u = current_user if current_user.is_authenticated else None
        return dict(current_user=current_user, user=u)
    # 2. Route Shims: Aliases for old route names found in templates
    # These prevent BuildErrors without editing every HTML file.
    @app.route('/shim/login')
    def login_alias():
        return redirect(url_for('auth.assistant_login'))

    @app.route('/shim/index')
    def index_alias():
        return redirect(url_for('auth.index'))

    @app.route('/shim/createhelprequest')
    def create_ticket_alias():
        return redirect(url_for('tickets.create_ticket_page'))

    @app.route('/shim/livequeue')
    def live_queue_alias():
        return redirect(url_for('tickets.live_queue'))

    @app.route('/shim/userpage/<username>')
    def userpage_alias(username):
        return redirect(url_for('auth.user_profile'))

    # [Shim] Fixes 'auth.reset_password_request' error in login.html
    @app.route('/shim/reset-password')
    def reset_password_shim():
        # We don't have a reset page yet, so just redirect to login
        return redirect(url_for('auth.assistant_login'))

    # [Shim] Fixes 'auth.change_password' error in userpage.html
    @app.route('/shim/change-password')
    def change_password_shim():
        # We don't have a change password page yet, so redirect to profile
        return redirect(url_for('auth.user_profile'))

    # Add these specific endpoint overrides so url_for works
    # This is the "Magic" that stops the BuildErrors
    with app.app_context():
        app.add_url_rule(
            "/shim/reset-password",
            endpoint="auth.reset_password_request",
            view_func=reset_password_shim,
        )
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
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    # ---------------------------------------------------
    # Health Check
    # ---------------------------------------------------
    @app.route("/health")
    def health_check():
        return jsonify({"message": "Wormhole Queue System API is running"}), 200

    # ---------------------------------------------------
    # Register Blueprints
    # ---------------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.tickets import tickets_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)

    return app