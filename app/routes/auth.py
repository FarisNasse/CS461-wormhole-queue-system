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

# -------------------------------
# Import required modules
# -------------------------------

from flask import Blueprint, request, jsonify, session
# Blueprint allows us to organize routes into logical groups (auth routes are kept separate)
# request gives access to incoming request data (JSON, form data, etc.)
# jsonify makes it easy to return JSON responses
# session stores temporary user information on the server (e.g., user_id)

from werkzeug.security import check_password_hash
# check_password_hash securely compares a plain password to a stored hashed password.

from app.models import User
# Imports the User model class so we can look up users in the database.

from app import db
# Imports the database instance to interact with the SQLAlchemy database.

# -------------------------------
# Create a Blueprint for auth routes
# -------------------------------
# Blueprints make it easier to organize and register groups of related routes
# in a larger Flask application. This one will be registered in app/__init__.py.
auth_bp = Blueprint('auth', __name__)

# -------------------------------
# POST /api/login
# -------------------------------
# This route logs a user in.
# It expects a JSON body containing a username and password.
# If the credentials are valid, it stores the user’s ID and admin flag in the session.
# Otherwise, it returns a 401 Unauthorized response.

@auth_bp.route('/api/login', methods=['POST'])
def login():
    # Extract the JSON data from the request body.
    data = request.get_json()

    # Get the username and password provided by the user.
    username = data.get('username')
    password = data.get('password')

    # Query the database for a user with this username.
    user = User.query.filter_by(username=username).first()

    # If the user exists AND the password matches the stored hash:
    if user and check_password_hash(user.password_hash, password):
        # Store the user’s ID and admin status in the session.
        # The session is stored securely on the server (not client-side).
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin

        # Return a success message and whether the user is an admin.
        return jsonify({
            'message': 'Login successful',
            'is_admin': user.is_admin
        }), 200

    # If authentication fails, return an error message with a 401 status.
    return jsonify({'error': 'Invalid credentials'}), 401


# -------------------------------
# POST /api/logout
# -------------------------------
# This route logs the user out by clearing all session data.
# It doesn’t require any input — it just resets the session.

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    # Clear all stored session variables (log the user out).
    session.clear()

    # Return confirmation message.
    return jsonify({'message': 'Logged out successfully'}), 200


# -------------------------------
# GET /api/check-session
# -------------------------------
# This route checks whether a user is currently logged in.
# It looks for 'user_id' in the session object.
# Useful for frontend components that need to know whether a user is authenticated.

@auth_bp.route('/api/check-session', methods=['GET'])
def check_session():
    # If there’s a user_id in the session, the user is logged in.
    if 'user_id' in session:
        # Return logged_in=True and whether they are an admin.
        return jsonify({
            'logged_in': True,
            'is_admin': session.get('is_admin', False)
        }), 200

    # If no user_id is found, return logged_in=False.
    return jsonify({'logged_in': False}), 200
