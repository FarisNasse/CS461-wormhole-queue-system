# app/routes/auth.py
from flask import Blueprint, request, jsonify, session, render_template
from werkzeug.security import check_password_hash
from app.models import User
from app import db

# -------------------------------
# Create a Blueprint for auth routes
# -------------------------------
auth_bp = Blueprint('auth', __name__)

# -------------------------------
# GET /
# -------------------------------
# This provides the public landing page.
@auth_bp.route("/")
@auth_bp.route("/index")
def index():
    # [Nitpick Fix] Added explicit status code 200 for consistency
    return render_template("index.html"), 200

# -------------------------------
# POST /api/login
# -------------------------------
# Verifies username/password and sets session variables.
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        # [Check] Explicit 200 OK
        return jsonify({
            'message': 'Login successful',
            'is_admin': user.is_admin
        }), 200

    # [Check] Explicit 401 Unauthorized
    return jsonify({'error': 'Invalid credentials'}), 401


# -------------------------------
# POST /api/logout
# -------------------------------
# Clears the session (logs user out).
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    # [Check] Explicit 200 OK
    return jsonify({'message': 'Logged out successfully'}), 200


# -------------------------------
# GET /api/check-session
# -------------------------------
# Returns user’s session state.
@auth_bp.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        # [Check] Explicit 200 OK
        return jsonify({
            'logged_in': True,
            'is_admin': session.get('is_admin', False)
        }), 200

    # [Check] Explicit 200 OK
    return jsonify({'logged_in': False}), 200