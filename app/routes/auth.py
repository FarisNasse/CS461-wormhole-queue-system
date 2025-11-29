#auth.py
from flask import Blueprint, request, jsonify, session, render_template
from werkzeug.security import check_password_hash
from app.models import User
from app.models import Ticket
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/")
@auth_bp.route("/index", endpoint = "index")
def index():
    return render_template("index.html")

@auth_bp.route("/createticket", endpoint = "createticket")
def createticket():
    return render_template("createticket.html")

@auth_bp.route("/livequeue", endpoint = "livequeue")
def livequeue():
    return render_template("livequeue.html")

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        return jsonify({'message': 'Login successful', 'is_admin': user.is_admin}), 200
    return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'is_admin': session.get('is_admin', False)})
    return jsonify({'logged_in': False}), 200

@auth_bp.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json()

    student_name = data.get("student_name")
    physics_course = data.get("class_name")
    table = data.get("table_number")
    location = data.get("location")

    # Validate required fields
    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400

    # Create ticket
    new_ticket = Ticket(
        student_name = student_name,
        table = table,
        physics_course = physics_course,
        status = "live"
    )

    db.session.add(new_ticket)
    db.session.commit()

    return jsonify({
        "message": "Ticket created",
        "ticket_id": new_ticket.id
    }), 201