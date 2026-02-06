import os
from dotenv import load_dotenv
from datetime import UTC, datetime

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")

    # --- AWS & Email Configuration ---
    # Default to False so it works locally without AWS keys
    ENABLE_AWS_SES = os.environ.get("ENABLE_AWS_SES", "False").lower() in ["true", "1"]
    
    # Defaults for the server
    AWS_REGION = os.environ.get("AWS_REGION") or "us-west-2"
    SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL")
    
    # MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 8025)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')