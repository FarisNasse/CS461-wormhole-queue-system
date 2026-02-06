from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app import db, limiter
from app.forms import LoginForm, ResetPasswordForm, ResetPasswordRequestForm
from app.models import User
from app.email_utils import send_password_reset_email  # Your new AWS/Hybrid utility

auth_bp = Blueprint("auth", __name__)

# --- HTML Routes ---

@auth_bp.route("/")
@auth_bp.route("/index", endpoint="index")
def index():
    return render_template("index.html")

# NOTE: /livequeue and /createticket have been removed from here 
# because they are now handled in app/routes/tickets.py

@auth_bp.route("/assistant-login", methods=["GET", "POST"])
def assistant_login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("auth.assistant_login"))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("auth.dashboard"))

    return render_template("login.html", title="Sign In", form=form)


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return "<h1>Welcome! You are logged in to the Wormhole System.</h1>", 200


# --- API Routes ---

@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        return jsonify({"message": "Login successful", "is_admin": user.is_admin}), 200

    return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/check-session", methods=["GET"])
def check_session():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "is_admin": current_user.is_admin}), 200
    return jsonify({"logged_in": False}), 200


# --- Password Reset Flow ---

@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Calls your AWS/Hybrid Email Utility
            send_password_reset_email(user)
        
        flash("Check your email for the instructions to reset your password")
        return redirect(url_for("auth.assistant_login"))

    return render_template(
        "reset_password_request.html", title="Reset Password", form=form
    )


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    user = User.verify_reset_password_token(token)
    if not user:
        flash("The reset link is invalid or has expired.")
        return redirect(url_for("auth.index"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("auth.assistant_login"))

    return render_template("reset_password.html", title="Reset Password", form=form)