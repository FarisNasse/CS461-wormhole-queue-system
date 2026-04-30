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
    PASSWORD_RESET_ENABLED = _env_bool("PASSWORD_RESET_ENABLED", "0")

    # Keep all database URL selection in config.py. Production deployments should
    # provide DATABASE_URL; the local SQLite fallback is opt-in only.
    ALLOW_SQLITE_FALLBACK = _env_bool("ALLOW_SQLITE_FALLBACK", "0")
    SQLITE_FALLBACK_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        # SQLAlchemy 1.4+ requires "postgresql://" instead of "postgres://".
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or SQLITE_FALLBACK_DATABASE_URI


def validate_non_testing_config(app_config):
    """Fail fast on unsafe production-like configuration."""
    database_url = app_config.get("SQLALCHEMY_DATABASE_URI")
    if database_url == "sqlite:///:memory:":
        raise RuntimeError(
            "Refusing to start non-testing app with in-memory SQLite. "
            "Set DATABASE_URL, or explicitly set ALLOW_SQLITE_FALLBACK=1 for local development."
        )

    if not app_config.get("DATABASE_URL") and not app_config.get(
        "ALLOW_SQLITE_FALLBACK", False
    ):
        raise RuntimeError(
            "DATABASE_URL must be set for non-testing environments. "
            "Set ALLOW_SQLITE_FALLBACK=1 only for local development."
        )

    secret_key = app_config.get("SECRET_KEY")
    if not secret_key or secret_key == "dev-secret-key":
        raise RuntimeError(
            "SECRET_KEY must be set to a strong non-default value for non-testing "
            "environments. Generate a strong random value and store it as an "
            "environment variable."
        )
