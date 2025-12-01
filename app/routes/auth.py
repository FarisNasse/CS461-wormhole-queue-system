# app/routes/auth.py
<<<<<<< Updated upstream
from flask import Blueprint, request, jsonify, session, render_template
from werkzeug.security import check_password_hash
from app.models import User
=======
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user  # [NEW]

>>>>>>> Stashed changes
from app import db
from app.auth_utils import login_required

# Update flask imports to include 'flash'
# Add this new import line
from app.forms import RegistrationForm, ResetPasswordForm, ResetPasswordRequestForm
from app.models import User


auth_bp = Blueprint("auth", __name__)

<<<<<<< Updated upstream
# -------------------------------
# GET / (Student Home Page)
# -------------------------------
=======
# --- Routes ---


>>>>>>> Stashed changes
@auth_bp.route("/")
@auth_bp.route("/index", endpoint = "index")
def index():
    # [FIX] Now renders your existing main home page
    return render_template("index.html")

<<<<<<< Updated upstream
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
=======

@auth_bp.route("/assistant-login")
def assistant_login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.user_profile"))  # Redirect if already logged in
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


@auth_bp.route("/api/login", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return jsonify({"message": "Already logged in"}), 200

>>>>>>> Stashed changes
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

<<<<<<< Updated upstream
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        return jsonify({
            'message': 'Login successful',
            'is_admin': user.is_admin
        }), 200
=======
    if user and user.check_password(password):
        # [NEW] This is the magic line. It creates the session for you.
        login_user(user)
        return jsonify({"message": "Login successful", "is_admin": user.is_admin}), 200
>>>>>>> Stashed changes

    return jsonify({"error": "Invalid credentials"}), 401

<<<<<<< Updated upstream
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
=======

@auth_bp.route("/api/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()  # [NEW] Clears session automatically
    if request.method == "GET":
        return redirect(url_for("auth.index"))
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/register", methods=["GET", "POST"])
@login_required  # Layer 1: Must be logged in
@admin_required  # Layer 2: Must be an Admin
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # 1. Create the new user object
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data,
        )
        # 2. Set the password (hashes it automatically via your model)
        user.set_password(form.password.data)

        # 3. Save to DB
        db.session.add(user)
        db.session.commit()

        flash(f"User {user.username} registered successfully!")
        return redirect(url_for("auth.user_list"))  # Redirect to the list of users

    # [FIX] Pass the 'form' object to the template
    return render_template("register.html", form=form)


@auth_bp.route("/users")
@login_required
@admin_required
def user_list():
    # Only admins can see the list of all users
    users = User.query.all()
    # Passing placeholder lists to match Jonathan's template expectations
    return render_template("user_list.html", new_users=users, old_users=[])


@auth_bp.route("/users/batch")
@login_required
@admin_required
def register_batch():
    return render_template("register_batch.html")


@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_password_token()
            # For prototype: Print to terminal instead of sending email
            url = url_for("auth.reset_password", token=token, _external=True)
            print(f"\n[DEBUG] Password Reset Link: {url}\n")

            flash("Check your email for the instructions to reset your password")
            return redirect(url_for("auth.assistant_login"))
        else:
            flash("Email not found")

    return render_template(
        "reset_password_request.html", title="Reset Password", form=form
    )


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("auth.index"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("auth.assistant_login"))

    return render_template("reset_password.html", form=form)
>>>>>>> Stashed changes
