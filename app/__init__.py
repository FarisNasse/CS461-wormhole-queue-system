# app/__init__.py
import mimetypes
import os
from types import SimpleNamespace

from flask import Flask, jsonify, redirect, request, send_from_directory
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config

# Ignore broken Windows/system MIME mappings
mimetypes.init([])
mimetypes.add_type("application/javascript", ".js", strict=True)
mimetypes.add_type("application/javascript", ".mjs", strict=True)
mimetypes.add_type("text/css", ".css", strict=True)

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()


def _request_is_secure():
    """Return True for direct HTTPS or proxied HTTPS requests."""
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
    if forwarded_proto:
        first_hop = forwarded_proto.split(",", maxsplit=1)[0].strip().lower()
        if first_hop == "https":
            return True
    return request.is_secure


def _build_csp_header():
    """Return a CSP that disallows inline scripts but preserves current styling."""
    policy = {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self'",
        "img-src": "'self' data:",
        "font-src": "'self' data:",
        "connect-src": "'self' ws: wss:",
        "frame-src": "'self' https://docs.google.com",
        "object-src": "'none'",
        "base-uri": "'self'",
        "form-action": "'self'",
        "frame-ancestors": "'self'",
    }
    return "; ".join(f"{directive} {value}" for directive, value in policy.items())


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
    app = Flask(__name__, static_folder=None)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    @app.route("/static/<path:filename>", endpoint="static")
    def static_files(filename):
        static_dir = os.path.join(app.root_path, "static")

        if filename.endswith((".js", ".mjs")):
            return send_from_directory(
                static_dir,
                filename,
                mimetype="application/javascript",
            )

        if filename.endswith(".css"):
            return send_from_directory(
                static_dir,
                filename,
                mimetype="text/css",
            )

        return send_from_directory(static_dir, filename)

    # ---------------------------------------------------
    # Configuration
    # ---------------------------------------------------
    app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret"
        app.config["SESSION_COOKIE_SECURE"] = False
        app.config["ENABLE_HTTPS_REDIRECT"] = False
        app.config["ENABLE_HSTS"] = False

    # ---------------------------------------------------
    # Initialize Extensions
    # ---------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get("SOCKETIO_CORS_ALLOWED_ORIGINS"),
    )

    # ---------------------------------------------------
    # Security / HTTPS enforcement
    # ---------------------------------------------------
    @app.before_request
    def enforce_https():
        if not app.config.get("ENABLE_HTTPS_REDIRECT"):
            return None

        if _request_is_secure():
            return None

        secure_url = request.url.replace("http://", "https://", 1)
        status_code = 301 if request.method in {"GET", "HEAD", "OPTIONS"} else 308
        return redirect(secure_url, code=status_code)

    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault("Content-Security-Policy", _build_csp_header())

        if app.config.get("ENABLE_HSTS") and _request_is_secure():
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response

    # ---------------------------------------------------
    # Internal Imports & Registration
    # ---------------------------------------------------
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
            pass

        return {
            "current_user": SimpleNamespace(
                is_admin=False,
                is_anonymous=True,
                username="",
            )
        }

    from app.routes.users import user_bp

    app.register_blueprint(user_bp)

    return app
