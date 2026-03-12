import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"

    # In production (Elastic Beanstalk), DATABASE_URL must be set as an
    # environment variable pointing to an RDS instance.
    # The SQLite fallback is kept only for local development.
    _db_url = os.environ.get("DATABASE_URL")
    if _db_url and _db_url.startswith("postgres://"):
        # SQLAlchemy 1.4+ requires "postgresql://" instead of "postgres://"
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url or "sqlite:///" + os.path.join(basedir, "app.db")
