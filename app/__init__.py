# app/__init__.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SECRET_KEY'] = 'dev-secret-key'
    db.init_app(app)

    @app.route("/")
    def index():
        return jsonify({"message": "Welcome to the Wormhole Queue System API!"}), 200

    # Register blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app
    