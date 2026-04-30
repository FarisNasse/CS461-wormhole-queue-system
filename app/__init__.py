# app/__init__.py
from types import SimpleNamespace

from flask import Flask, current_app, jsonify, redirect, request, session
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config, validate_non_testing_config

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()


def create_app(testing=False):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    app.config.from_object(Config)

    if testing:
        app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SESSION_COOKIE_SECURE=False,
            FORCE_HTTPS=False,
            ENABLE_HSTS=False,
            PREFERRED_URL_SCHEME="http",
        )

    if not testing:
        validate_non_testing_config(app.config)

    @app.before_request
    def enforce_https():
        if request.path == "/health":
            return None

        if (
            app.config.get("FORCE_HTTPS", False)
            and not request.is_secure
            and not app.debug
            and request.headers.get("X-Forwarded-Proto", "http").lower() != "https"
        ):
            return redirect(request.url.replace("http://", "https://", 1), code=308)

        return None

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )

        csp = app.config.get("CONTENT_SECURITY_POLICY")
        if csp:
            response.headers.setdefault("Content-Security-Policy", csp)

        if app.config.get("ENABLE_HSTS", False) and request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    from app.time_utils import format_pacific, serialize_datetime

    app.jinja_env.filters["datetime_pacific"] = format_pacific
    app.jinja_env.filters["iso_datetime_pacific"] = serialize_datetime

    from app import models  # noqa: F401
    from app.routes import queue_events  # noqa: F401
    from app.routes.auth import auth_bp
    from app.routes.error import error_bp
    from app.routes.tickets import tickets_bp
    from app.routes.users import user_bp
    from app.routes.views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(views_bp)

    @app.route("/health")
    def health_check():
        return jsonify({"message": "Wormhole Queue System API is running"}), 200

    @app.context_processor
    def inject_current_user():
        try:
            if "user_id" in session:
                from app.models import User

                user = db.session.get(User, session["user_id"])
                if user:
                    return {
                        "current_user": SimpleNamespace(
                            is_admin=bool(user.is_admin),
                            is_anonymous=False,
                            username=user.username,
                        ),
                        "password_reset_enabled": bool(
                            current_app.config.get("PASSWORD_RESET_ENABLED", False)
                        ),
                    }
        except Exception:
            pass

        return {
            "current_user": SimpleNamespace(
                is_admin=False,
                is_anonymous=True,
                username="",
            ),
            "password_reset_enabled": bool(
                current_app.config.get("PASSWORD_RESET_ENABLED", False)
            ),
        }

    with app.app_context():
        if testing or app.config.get("TESTING", False):
            db.create_all()

    return app
