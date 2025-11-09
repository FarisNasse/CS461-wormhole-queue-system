# app/__init__.py
from flask import Flask, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    
#     db.init_app(app)

#     @app.route("/")
#     def index():
#         return jsonify({"message": "Welcome to the Wormhole Queue System API!"}), 200

    # Register blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app

from app import routes, models


    
