#auth.py
from flask import Blueprint, request, jsonify, session, render_template
from werkzeug.security import check_password_hash
from app.models import User
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
