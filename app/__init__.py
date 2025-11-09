# app/__init__.py
from flask import Flask, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) # set configuration settings from config.py
    
    db.init_app(app)
    migrate.init_app(app, db)

    from app import models # import models to register with SQLAlchemy

    # Register blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app
