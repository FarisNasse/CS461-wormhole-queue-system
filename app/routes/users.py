import csv
from io import StringIO

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app import db
from app.auth_utils import admin_required
from app.forms import RegisterBatchForm, RegisterForm
from app.models import User

user_bp = Blueprint("users", __name__, url_prefix="/api")


# route to remove user
@admin_required
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
@admin_required
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
        suggestion = suggestion_by_field.get(
            field_name, "Review this field and try again."
        )
        for err in errors:
            flash(f"{label}: {err} Suggestion: {suggestion}", "error")

    if not form.errors:
        flash(
            "Error creating user. Suggestion: try again and verify all fields.", "error"
        )

    return render_template("register.html", form=form), 400


@admin_required
@user_bp.route("/users_add_batch", methods=["POST"])
def users_add_batch():
    form = RegisterBatchForm()

    if not form.validate_on_submit():
        for field_name, errors in form.errors.items():
            label = getattr(form, field_name).label.text
            for err in errors:
                flash(f"{label}: {err}", "error")
        return render_template("register_batch.html", form=form), 400

    uploaded_csv = form.user_csv.data
    content = uploaded_csv.read().decode("utf-8-sig")
    reader = csv.reader(StringIO(content))
    rows = list(reader)

    if not rows:
        flash(
            "The uploaded CSV is empty. Suggestion: add a header and at least one user row.",
            "error",
        )
        return render_template("register_batch.html", form=form), 400

    expected_header = ["first name", "last name", "onid"]
    found_header = [col.strip().lower() for col in rows[0][:3]]
    if found_header != expected_header:
        flash(
            "CSV header must be first name,last name,ONID. "
            "Suggestion: update the first row to match this exact order.",
            "error",
        )
        return render_template("register_batch.html", form=form), 400

    created_count = 0
    skipped_count = 0

    for row_number, row in enumerate(rows[1:], start=2):
        if not row or all(not col.strip() for col in row):
            continue

        if len(row) < 3:
            skipped_count += 1
            flash(
                f"Row {row_number} skipped: expected 3 columns "
                "(first name, last name, ONID).",
                "error",
            )
            continue

        first_name = row[0].strip()
        last_name = row[1].strip()
        onid = row[2].strip().lower()

        if not first_name or not last_name or not onid:
            skipped_count += 1
            flash(
                f"Row {row_number} skipped: first name, last name, and ONID are required.",
                "error",
            )
            continue

        username = onid
        email = f"{onid}@oregonstate.edu"

        if (
            User.query.filter_by(username=username).first()
            or User.query.filter_by(email=email).first()
        ):
            skipped_count += 1
            flash(
                f"Row {row_number} skipped: user {onid} already exists.",
                "error",
            )
            continue

        new_user = User(
            username=username,
            email=email,
            name=f"{first_name} {last_name}",
            is_admin=False,
            is_active=True,
        )
        new_user.set_password("wormhole")
        db.session.add(new_user)
        created_count += 1

    db.session.commit()

    flash(
        f"Batch registration complete: created {created_count} users, skipped {skipped_count} rows.",
        "success",
    )
    return redirect(url_for("views.user_list"))


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
