from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

# --- WTForms Configuration ---
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


# 1. Login Form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


# 2. Request Password Reset Form (Stage 1) <-- THIS WAS MISSING
class ResetPasswordRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")


# 3. Reset Password Form (Stage 2)
class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Request Password Reset")


# --- Routes ---

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
@auth_bp.route("/index", endpoint="index")
def index():
    return render_template("index.html")


@auth_bp.route("/livequeue")
def student():
    return render_template("livequeue.html")


@auth_bp.route("/createticket")
def create_ticket_page():
    return render_template("createticket.html")


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
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/check-session", methods=["GET"])
def check_session():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "is_admin": current_user.is_admin}), 200
    return jsonify({"logged_in": False}), 200


# --- STAGE 1: Request the Reset (Enter Email) ---
@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # In a real app, send email here
            print(f"DEBUG: Reset requested for {user.email}")
        flash("Check your email for the instructions to reset your password")
        return redirect(url_for("auth.assistant_login"))

    return render_template(
        "reset_password_request.html", title="Reset Password", form=form
    )


# --- STAGE 2: Perform the Reset (Enter New Password) ---
@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    # NOTE: This line will cause the NEXT error because 'verify_reset_password_token'
    # is not yet defined in your User model. This is expected!
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("auth.index"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("auth.assistant_login"))

    return render_template("reset_password.html", title="Reset Password", form=form)
