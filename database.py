# database.py
# Initializes and manages the Flask SQLAlchemy database.

from app import create_app, db
from app.models import User, Ticket  # Import your models so they get registered

def init_db():
    """Creates all database tables."""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ Database initialized successfully!")

        # Optional: create an initial admin user if not present
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", email="admin@example.com", is_admin=True)
            admin.set_password("password123")
            db.session.add(admin)
            db.session.commit()
            print("👤 Admin user created (username: admin, password: password123)")

if __name__ == "__main__":
    init_db()
