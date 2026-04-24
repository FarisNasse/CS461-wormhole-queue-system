# app/routes/auth.py
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

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

    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({"error": "This account has been deactivated"}), 401
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
        # ensure account still exists and is active
        user = User.query.get(session.get("user_id"))
        if user is None or not user.is_active:
            session.clear()
            return jsonify({"logged_in": False}), 200
        return jsonify(
            {"logged_in": True, "is_admin": session.get("is_admin", False)}
        ), 200

    return jsonify({"logged_in": False}), 200


# -------------------------------
# GET /reset_password_request (Render a simple reset request form)
# -------------------------------
@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if not current_app.config.get("PASSWORD_RESET_ENABLED", False):
        flash(
            "Password reset is not configured yet. Please contact an administrator.",
            "info",
        )
        return redirect(url_for("views.assistant_login"))

    form = ResetPasswordRequestForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Email-token delivery should be implemented before enabling this route.
            current_app.logger.info("Password reset requested for configured account")
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
    if not current_app.config.get("PASSWORD_RESET_ENABLED", False):
        flash(
            "Password reset is not configured yet. Please contact an administrator.",
            "info",
        )
        return redirect(url_for("views.assistant_login"))

    current_app.logger.info("Password reset page accessed")
    form = ResetPasswordForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Passwords do not match or are invalid.", "error")
            return render_template("reset_password.html", form=form)
        flash("Your password has been reset. You may now sign in.", "success")
        return redirect(url_for("views.assistant_login"))
    return render_template("reset_password.html", form=form)
