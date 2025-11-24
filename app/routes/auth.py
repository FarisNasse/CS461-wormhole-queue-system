# ===============================
# auth.py — Authentication Routes
# ===============================
# This file defines the authentication-related API routes for the
# Wormhole Queue System backend. It handles:
#   • User login (verifies username/password)
#   • User logout (clears the session)
#   • Session checking (to verify if a user is currently logged in)
#
# It uses Flask’s session mechanism to temporarily store user data between
# requests, and Werkzeug’s password hashing utilities to securely verify passwords.

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
    return render_template("index.html")

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
        return jsonify({
            'message': 'Login successful',
            'is_admin': user.is_admin
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401


# -------------------------------
# POST /api/logout
# -------------------------------
# Clears the session (logs user out).
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200


# -------------------------------
# GET /api/check-session
# -------------------------------
# Returns user’s session state.
@auth_bp.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'is_admin': session.get('is_admin', False)
        }), 200

    return jsonify({'logged_in': False}), 200
