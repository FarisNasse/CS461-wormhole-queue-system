# app/models.py
from datetime import datetime
from app import db

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(80))
    table_number = db.Column(db.String(10))
    class_name = db.Column(db.String(50))
    status = db.Column(db.String(50), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    num_students = db.Column(db.Integer, nullable=True)
    current_ta = db.Column(db.String(80), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.student_name,
            "table_number": self.table_number,
            "class_name": self.class_name,
            "status": self.status,
            "created_at": self.created_at,
        }

from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
