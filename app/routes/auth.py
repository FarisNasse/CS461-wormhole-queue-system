# app/routes/auth.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required # [NEW]
from app.models import User
from app import db
from app.auth_decorators import admin_required

auth_bp = Blueprint('auth', __name__)

# --- Routes ---

@auth_bp.route("/")
@auth_bp.route("/index")
def index():
    return render_template("index.html")

@auth_bp.route("/assistant-login")
def assistant_login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.user_profile')) # Redirect if already logged in
    return render_template("login.html")

@auth_bp.route("/dashboard")
@auth_bp.route("/profile")
@login_required  # [NEW] Using Flask-Login's decorator
def user_profile():
    # Flask-Login provides 'current_user' automatically.
    # The template userpage.html uses 'user' for the profile owner and 'current_user' for the viewer.
    # In the dashboard, they are the same person.
    return render_template("userpage.html", user=current_user)

# --- API Logic ---

@auth_bp.route('/api/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'message': 'Already logged in'}), 200

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        # [NEW] This is the magic line. It creates the session for you.
        login_user(user) 
        return jsonify({
            'message': 'Login successful',
            'is_admin': user.is_admin
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/api/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user() # [NEW] Clears session automatically
    if request.method == 'GET':
        return redirect(url_for('auth.index'))
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route("/register", methods=['GET', 'POST'])
@login_required  # Layer 1: Must be logged in
@admin_required  # Layer 2: Must be an Admin
def register():
    # Only admins can see the registration form
    if request.method == 'POST':
        # ... logic to create user ...
        pass
    return render_template("register.html")

@auth_bp.route('/users')
@login_required
@admin_required
def user_list():
    # Only admins can see the list of all users
    users = User.query.all()
    # Passing placeholder lists to match Jonathan's template expectations
    return render_template('user_list.html', new_users=users, old_users=[])

@auth_bp.route('/users/batch')
@login_required
@admin_required
def register_batch():
    return render_template('register_batch.html')

# ... (Keep reset_password_request placeholder if you want, or remove) ...