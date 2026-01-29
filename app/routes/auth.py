# app/routes/auth.py
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from app.forms import ResetPasswordForm, ResetPasswordRequestForm
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


# -------------------------------
# GET /reset_password_request (Render a simple reset request form)
# -------------------------------
@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    form = ResetPasswordRequestForm()
    if request.method == "POST":
        if form.validate_on_submit():
            pass
        flash(
            "If an account with that email exists, check your inbox for reset instructions.",
            "info",
        )
        return redirect(url_for("views.assistant_login"))
    return render_template("reset_password_request.html", form=form)


# -------------------------------
# GET /reset_password/<token> (Render password reset form)
# -------------------------------
@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Passwords do not match or are invalid.", "error")
            return render_template("reset_password.html", form=form)
        flash("Your password has been reset. You may now sign in.", "success")
        return redirect(url_for("views.assistant_login"))
    return render_template("reset_password.html", form=form)
