import os

basedir = os.path.abspath(os.path.dirname(__file__))


def _env_bool(name, default="0"):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"

    # Reverse-proxy HTTPS defaults for production deployments.
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", "1")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")
    FORCE_HTTPS = _env_bool("FORCE_HTTPS", "1")
    ENABLE_HSTS = _env_bool("ENABLE_HSTS", "1")

    # Set the database to the correct sqlite path
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
