import os

basedir = os.path.abspath(os.path.dirname(__file__))


def _env_flag(name, default=False):
    """Convert common truthy environment variable strings to booleans."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "on"}


def _env_list(name):
    """Parse a comma-separated environment variable into a list."""
    value = os.environ.get(name)
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


environment = os.environ.get("FLASK_ENV", os.environ.get("APP_ENV", "development"))
is_production = environment.strip().lower() == "production"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session-cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _env_flag("SESSION_COOKIE_SECURE", default=is_production)

    # URL / transport security
    PREFERRED_URL_SCHEME = "https"
    ENABLE_HTTPS_REDIRECT = _env_flag(
        "ENABLE_HTTPS_REDIRECT", default=is_production
    )
    ENABLE_HSTS = _env_flag("ENABLE_HSTS", default=is_production)

    # Socket.IO same-origin by default; can be relaxed explicitly with env var.
    SOCKETIO_CORS_ALLOWED_ORIGINS = _env_list("SOCKETIO_CORS_ALLOWED_ORIGINS")