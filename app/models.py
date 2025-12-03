from time import time
import jwt  # Needs 'pip install pyjwt'
from flask import current_app
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ---------------------------------------------------------
    # FAANG-Standard Stateless Token Logic
    # ---------------------------------------------------------

    def get_reset_password_token(self, expires_in=600):
        """
        Generates a signed JWT that encodes the user's ID.
        expires_in: Default is 600 seconds (10 minutes).
        """
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        """
        Decodes the token.
        - If valid and unexpired: Returns the User object.
        - If invalid or expired: Returns None.
        """
        try:
            id = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )["reset_password"]
        except Exception:
            return None
            
        return User.query.get(id)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(64))
    table = db.Column(db.Integer)
    physics_course = db.Column(db.String(64))
    status = db.Column(db.String(20), default="Open")

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.student_name,
            "table_number": self.table,
            "class_name": self.physics_course,
            "status": self.status,
        }


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))