# app/routes/auth.py
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    session,
)
from werkzeug.security import check_password_hash

from app.models import User

auth_bp = Blueprint("auth", __name__)


# -------------------------------
# POST /api/login (The Logic)
# -------------------------------
@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session["user_id"] = user.id
        session["is_admin"] = user.is_admin
        return jsonify({"message": "Login successful", "is_admin": user.is_admin}), 200

    return jsonify({"error": "Invalid credentials"}), 401


# -------------------------------
# POST /api/logout
# -------------------------------
@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


# -------------------------------
# GET /api/check-session
# -------------------------------
@auth_bp.route("/api/check-session", methods=["GET"])
def check_session():
    if "user_id" in session:
        return jsonify(
            {"logged_in": True, "is_admin": session.get("is_admin", False)}
        ), 200

    return jsonify({"logged_in": False}), 200


# POST /api/changepass (Change user password)
# -------------------------------
@auth_bp.route("/api/changepass", methods=["POST"])
def change_password():
    from app import db

    data = request.get_json()
    username = data.get("username")
    old_password = data.get("old_password")
    new_password = data.get("password")
    password_confirm = data.get("password2")

    # Validate required fields
    if not username or not old_password or not new_password or not password_confirm:
        return jsonify({"error": "Missing required fields"}), 400

    # Check password confirmation
    if new_password != password_confirm:
        return jsonify({"error": "New passwords do not match"}), 400

    # Get the user to change password for
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get current session user
    session_user_id = session.get("user_id")
    current_user = User.query.get(session_user_id) if session_user_id else None

    if not current_user:
        return jsonify({"error": "Not authorized"}), 401

    # Allow admins to change without old password, but require old password for non-admins changing own password
    if current_user.id != user.id and not current_user.is_admin:
        return jsonify({"error": "Not authorized to change this user's password"}), 403

    # If changing own password, verify old password
    if current_user.id == user.id and not user.check_password(old_password):
        return jsonify({"error": "Old password is incorrect"}), 401

    # Set new password
    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200


# GET /reset_password_request (Render a simple reset request form)
# -------------------------------
@auth_bp.route("/reset_password_request", methods=["GET"])
def reset_password_request():
    # Render reset password request form (submission handled via /api/reset_password_request)
    return render_template("reset_password_request.html")


# POST /api/reset_password_request (Handle password reset request)
# -------------------------------
@auth_bp.route("/api/reset_password_request", methods=["POST"])
def api_reset_password_request():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    # Log the request (in real implementation, would send email with reset link)
    if user:
        current_app.logger.info(f"Password reset requested for: {email}")

    # Always return same message for security (don't reveal if email exists)
    return jsonify(
        {
            "message": "If an account with that email exists, check your inbox for reset instructions."
        }
    ), 200


# GET /reset_password/<token> (Render password reset form)
# -------------------------------
@auth_bp.route("/reset_password/<token>", methods=["GET"])
def reset_password(token):
    # Log the token access
    current_app.logger.info(f"Password reset page accessed with token: {token}")
    # Render reset password form (submission handled via /api/reset_password/<token>)
    return render_template("reset_password.html", token=token)


# POST /api/reset_password/<token> (Handle password reset)
# -------------------------------
@auth_bp.route("/api/reset_password/<token>", methods=["POST"])
def api_reset_password(token):
    data = request.get_json()
    password = data.get("password")
    password2 = data.get("password2")

    if not password or not password2:
        return jsonify({"error": "Both password fields are required"}), 400

    if password != password2:
        return jsonify({"error": "Passwords do not match"}), 400

    # In a real implementation, validate the token and find the user
    # For now, just accept the reset (token validation would be implemented with a proper token system)
    current_app.logger.info(f"Password reset for token: {token}")

    return jsonify(
        {"message": "Your password has been reset. You may now sign in."}
    ), 200
