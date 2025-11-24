# app/__init__.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(testing=False):
    app = Flask(__name__)
<<<<<<< Updated upstream
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SECRET_KEY'] = 'dev-secret-key'
    db.init_app(app)

    @app.route("/")
    def index():
        return jsonify({"message": "Welcome to the Wormhole Queue System API!"}), 200

    # Register blueprints
=======

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False

    # normal config
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
    app.config.setdefault("SECRET_KEY", "dev")

    # init extensions
    db.init_app(app)

    # register blueprints (important!)
>>>>>>> Stashed changes
    from app.routes.auth import auth_bp
    from app.routes.tickets import tickets_bp  # adjust to your structure

    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)

    return app
<<<<<<< Updated upstream
    
=======

>>>>>>> Stashed changes
