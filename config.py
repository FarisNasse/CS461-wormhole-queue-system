import os

basedir = os.path.abspath(os.path.dirname(__file__))


def _env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "on"}


def _env_list(name):
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

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _env_flag("SESSION_COOKIE_SECURE", default=is_production)

    PREFERRED_URL_SCHEME = "https"
    ENABLE_HTTPS_REDIRECT = _env_flag("ENABLE_HTTPS_REDIRECT", default=is_production)
    ENABLE_HSTS = _env_flag("ENABLE_HSTS", default=is_production)

    SOCKETIO_CORS_ALLOWED_ORIGINS = _env_list("SOCKETIO_CORS_ALLOWED_ORIGINS")

    WORMHOLE_SCHEDULE_PUBHTML_URL = os.environ.get(
        "WORMHOLE_SCHEDULE_PUBHTML_URL"
    ) or (
        "https://docs.google.com/spreadsheets/d/e/"
        "2PACX-1vRcotW2LQyMMUHgBjvig-ZcHnybkT4_0XfiHDp-IVeqkX7VGh4vtrXBuHmDfTAVHdmHM2jcHInYuwOn/"
        "pubhtml?widget=true&headers=false"
    )

    WORMHOLE_SCHEDULE_CACHE_SECONDS = int(
        os.environ.get("WORMHOLE_SCHEDULE_CACHE_SECONDS", "300")
    )
