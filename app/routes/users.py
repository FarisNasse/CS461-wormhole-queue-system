from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app import db
from app.forms import RegisterForm
from app.models import User

user_bp = Blueprint("users", __name__, url_prefix="/api")


# route to remove user
@user_bp.route("/users_remove", methods=["POST"])
def users_remove():
    data = request.get_json()

    # filler field for now, to be updated later
    if not data or not all(k in data for k in ["username"]):
        return jsonify({"error": "Missing required fields"}), 400

    user = User.query.filter_by(username=data["username"]).first()

    if not user:
        return jsonify({"error": "User not found"}), 400

    db.session.delete(user)
    db.session.commit()

    if user.is_admin:
        return jsonify({"success": "admin removed"}), 200

    return jsonify({"success": "user removed"}), 200


# route to add user
@user_bp.route("/users_add", methods=["POST"])
def users_add():
    form = RegisterForm()
    if form.validate_on_submit():
        onid = form.onid.data.strip().lower()
        first_name = form.first_name.data
        last_name = form.last_name.data
        full_name = f"{first_name} {last_name}"
        email = f"{onid}@oregonstate.edu"
        username = onid

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash(
                "A user with this ONID already exists. Suggestion: "
                "verify the ONID spelling or use a different ONID.",
                "error",
            )
            return render_template("register.html", form=form), 400
        if User.query.filter_by(email=email).first():
            flash(
                "A user with this email already exists. Suggestion: "
                "check whether this user was already registered.",
                "error",
            )
            return render_template("register.html", form=form), 400

        u = User(
            username=username,
            email=email,
            name=full_name,
            is_admin=form.is_admin.data,
            is_active=True,
        )

        u.set_password("wormhole")

        db.session.add(u)
        db.session.commit()

        flash("User created successfully!", "success")
        return redirect(url_for("views.user_list"))

    suggestion_by_field = {
        "first_name": "Enter the student's first name.",
        "last_name": "Enter the student's last name.",
        "onid": "Enter the ONID username only (for example: smithj).",
    }
    for field_name, errors in form.errors.items():
        label = getattr(form, field_name).label.text
        suggestion = suggestion_by_field.get(field_name, "Review this field and try again.")
        for err in errors:
            flash(f"{label}: {err} Suggestion: {suggestion}", "error")

    if not form.errors:
        flash("Error creating user. Suggestion: try again and verify all fields.", "error")

    return render_template("register.html", form=form), 400


# New JSON API for testing
@user_bp.route("/users_add_json", methods=["POST"])
def api_users_add():
    data = request.get_json()

    if not data or not all(k in data for k in ["username", "email", "password"]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user already exists
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    u = User(
        username=data["username"],
        email=data["email"],
        is_admin=data.get("is_admin", False),
    )
    u.set_password(data["password"])

    db.session.add(u)
    db.session.commit()

    return jsonify({"success": "User created", "username": u.username}), 201
