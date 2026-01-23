from flask import Flask, jsonify, session
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config

# 1. Initialize Extensions Globally (Unbound)
# We define them here so other files (models.py) can import 'db'
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
mail = Mail()

def create_app(testing=False):
    """
    Application Factory: Creates and configures the Flask app.
    """
    app = Flask(__name__)

    # 2. Configuration
    app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret"

    # 3. Bind Extensions to the App
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # 4. Register Blueprints (The "Routes")
    # We import them INSIDE the function to avoid "Circular Import" errors
    from app.routes.auth import auth_bp
    from app.routes.views import views_bp
    from app.routes.tickets import tickets_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(tickets_bp)

    # 5. Import Non-Blueprint Logic
    # These files need to be imported so their code "runs" and registers with the app
    with app.app_context():
        # Import error handlers (404, 500 pages)
        from app.routes import error
        
        # Import SocketIO events so the server listens for them
        from app.routes import queue_events 

        # Import models so Alembic/SQLAlchemy 'knows' about them for migrations
        from app import models

    # 6. Global Routes (Health Check)
    @app.route("/health")
    def health_check():
        return jsonify({"message": "Wormhole Queue System API is running"}), 200

    # 7. Context Processor (Injects variables into ALL templates)
    # This makes 'current_user' available in every HTML file automatically
    from types import SimpleNamespace
    
    @app.context_processor
    def inject_current_user():
        try:
            if 'user_id' in session:
                # Use db.session.get for modern SQLAlchemy compatibility
                u = db.session.get(models.User, session['user_id'])
                if u:
                    return {
                        'current_user': SimpleNamespace(
                            is_admin=bool(u.is_admin),
                            is_anonymous=False,
                            username=u.username,
                            email=u.email
                        )
                    }
        except Exception:
            pass
        return {'current_user': SimpleNamespace(is_admin=False, is_anonymous=True, username='')}

    # 8. Shell Context (Optional but amazing for debugging)
    # Allows you to type 'flask shell' and have 'db' and 'User' ready to use
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'User': models.User, 'mail': mail}

    return app