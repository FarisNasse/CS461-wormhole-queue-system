# app/routes/auth.py
from flask import Blueprint, request, jsonify, session, render_template
from werkzeug.security import check_password_hash
from app.models import User
from app import db
from app.auth_utils import login_required

auth_bp = Blueprint('auth', __name__)

# -------------------------------
# GET / (Student Home Page)
# -------------------------------
@auth_bp.route("/")
@auth_bp.route("/index", endpoint = "index")
def index():
    # [FIX] Now renders your existing main home page
    return render_template("index.html")

# -------------------------------
# GET / (Live Queue)
# -------------------------------
@auth_bp.route("/livequeue")
def student():
    return render_template("livequeue.html")

# -------------------------------
# GET / (Help Request Creation)
# -------------------------------
@auth_bp.route("/createticket")
def create_ticket_page():
    return render_template("createticket.html")

# -------------------------------
# GET /assistant-login (Assistant Login Page)
# -------------------------------
@auth_bp.route("/assistant-login")
def assistant_login():
    # [FIX] Renders the login form specifically at this URL
    return render_template("login.html")

# -------------------------------
# GET /dashboard (Protected Area)
# -------------------------------
@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return "<h1>Welcome! You are logged in to the Wormhole System.</h1>", 200

# -------------------------------
# POST /api/login (The Logic)
# -------------------------------
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        return jsonify({
            'message': 'Login successful',
            'is_admin': user.is_admin
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401

# -------------------------------
# POST /api/logout
# -------------------------------
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# -------------------------------
# GET /api/check-session
# -------------------------------
@auth_bp.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'is_admin': session.get('is_admin', False)
        }), 200

    return jsonify({'logged_in': False}), 200