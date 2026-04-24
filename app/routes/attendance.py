"""Routes for Wormhole assistant attendance tracking."""

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
from flask_wtf.csrf import validate_csrf
from sqlalchemy.orm import joinedload

from app import db
from app.attendance_utils import (
    DAY_NAMES,
    active_attendance_session_for_user,
    attendance_status_for_session,
    build_attendance_dashboard,
    current_shift_for_user,
    format_datetime_for_display,
    format_shift_time_range,
    record_attendance_activity,
    touch_attendance,
    utc_now,
)
from app.auth_utils import admin_required, login_required
from app.forms import (
    AttendanceCheckInForm,
    AttendanceCheckOutForm,
    AttendanceShiftDeleteForm,
    AttendanceShiftForm,
)
from app.models import AttendanceActivity, AttendanceSession, AttendanceShift, User

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


def _current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def _populate_shift_form_choices(form: AttendanceShiftForm) -> None:
    users = (
        User.query.filter_by(is_active=True)
        .order_by(User.name.is_(None), User.name, User.username)
        .all()
    )
    form.user_id.choices = [
        (user.id, user.name or user.username) for user in users if not user.is_admin
    ]


def _redirect_back(default_endpoint: str = "views.hardware_list"):
    target = request.form.get("next") or request.referrer
    if target and target.startswith("/") and not target.startswith("//"):
        return redirect(target)
    if target and target.startswith(request.host_url):
        return redirect(target)
    return redirect(url_for(default_endpoint))


def _validate_csrf_from_request() -> bool:
    """Validate CSRF for AJAX endpoints that cannot use hidden FlaskForm fields."""
    if not current_app.config.get("WTF_CSRF_ENABLED", True):
        return True

    token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
    if not token:
        return False

    try:
        validate_csrf(token)
    except Exception:
        return False
    return True


@attendance_bp.route("/", methods=["GET"])
@admin_required
def dashboard():
    shift_form = AttendanceShiftForm()
    delete_shift_form = AttendanceShiftDeleteForm()
    _populate_shift_form_choices(shift_form)

    rows, summary = build_attendance_dashboard()
    shifts = (
        AttendanceShift.query.filter_by(is_active=True)
        .options(joinedload(AttendanceShift.user))
        .join(User)
        .order_by(AttendanceShift.day_of_week, AttendanceShift.start_time, User.name)
        .all()
    )
    recent_activities = (
        AttendanceActivity.query.options(joinedload(AttendanceActivity.user))
        .order_by(AttendanceActivity.created_at.desc())
        .limit(30)
        .all()
    )

    return render_template(
        "attendance.html",
        rows=rows,
        summary=summary,
        shifts=shifts,
        recent_activities=recent_activities,
        shift_form=shift_form,
        delete_shift_form=delete_shift_form,
        day_names=DAY_NAMES,
        format_shift_time_range=format_shift_time_range,
    )


@attendance_bp.route("/check-in", methods=["POST"])
@login_required
def check_in():
    form = AttendanceCheckInForm()
    if not form.validate_on_submit():
        flash("Invalid attendance request or session expired.", "error")
        return _redirect_back()

    user = _current_user()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    existing = active_attendance_session_for_user(user.id)
    if existing:
        flash("You are already checked in to the Wormhole.", "info")
        return _redirect_back()

    now = utc_now()
    shift = current_shift_for_user(user.id, now)
    attendance_session = AttendanceSession(
        user_id=user.id,
        shift_id=shift.id if shift else None,
        checked_in_at=now,
        last_seen_at=now,
        status="active",
        check_in_source="manual",
        notes=None if shift else "Checked in outside a scheduled shift.",
    )
    db.session.add(attendance_session)
    db.session.flush()

    shift_text = (
        format_shift_time_range(shift) if shift else "no matching scheduled shift"
    )
    record_attendance_activity(
        user.id,
        "check_in",
        f"Checked in for {shift_text}.",
        commit=False,
    )
    db.session.commit()

    flash("You are now checked in to the Wormhole.", "success")
    return _redirect_back()


@attendance_bp.route("/check-out", methods=["POST"])
@login_required
def check_out():
    form = AttendanceCheckOutForm()
    if not form.validate_on_submit():
        flash("Invalid attendance request or session expired.", "error")
        return _redirect_back()

    user = _current_user()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    attendance_session = active_attendance_session_for_user(user.id)
    if not attendance_session:
        flash("You are not currently checked in.", "info")
        return _redirect_back()

    record_attendance_activity(
        user.id,
        "check_out",
        "Checked out of the Wormhole.",
        commit=False,
    )

    now = utc_now()
    attendance_session.checked_out_at = now
    attendance_session.last_seen_at = now
    attendance_session.status = "checked_out"
    db.session.commit()

    flash("You have checked out of the Wormhole.", "success")
    return _redirect_back()


@attendance_bp.route("/heartbeat", methods=["POST"])
@login_required
def heartbeat():
    if not _validate_csrf_from_request():
        return jsonify({"error": "Invalid or missing CSRF token"}), 400

    user = _current_user()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    attendance_session = touch_attendance(user.id)
    if not attendance_session:
        return jsonify({"ok": True, "checked_in": False}), 200

    return (
        jsonify(
            {
                "ok": True,
                "checked_in": True,
                "status": attendance_status_for_session(attendance_session),
                "last_seen_at": format_datetime_for_display(
                    attendance_session.last_seen_at,
                    "%Y-%m-%d %H:%M:%S %Z",
                ),
            }
        ),
        200,
    )


@attendance_bp.route("/shifts/add", methods=["POST"])
@admin_required
def add_shift():
    form = AttendanceShiftForm()
    _populate_shift_form_choices(form)

    if not form.validate_on_submit():
        flash("Could not add shift. Please check all required fields.", "error")
        return redirect(url_for("attendance.dashboard"))

    if form.end_time.data <= form.start_time.data:
        flash("Shift end time must be after the start time.", "error")
        return redirect(url_for("attendance.dashboard"))

    user = db.session.get(User, form.user_id.data)
    if not user or not user.is_active:
        flash("Selected assistant could not be found.", "error")
        return redirect(url_for("attendance.dashboard"))
    if user.is_admin:
        flash("Admin users cannot be assigned attendance shifts.", "error")
        return redirect(url_for("attendance.dashboard"))

    shift = AttendanceShift(
        user_id=user.id,
        day_of_week=form.day_of_week.data,
        start_time=form.start_time.data,
        end_time=form.end_time.data,
        location=(form.location.data or "Wormhole").strip() or "Wormhole",
        is_active=True,
    )
    db.session.add(shift)
    db.session.commit()

    flash("Attendance shift added.", "success")
    return redirect(url_for("attendance.dashboard"))


@attendance_bp.route("/shifts/<int:shift_id>/delete", methods=["POST"])
@admin_required
def delete_shift(shift_id):
    form = AttendanceShiftDeleteForm()
    if not form.validate_on_submit():
        flash("Invalid attendance request or session expired.", "error")
        return redirect(url_for("attendance.dashboard"))

    shift = db.session.get(AttendanceShift, shift_id)
    if not shift:
        flash("Shift not found.", "error")
        return redirect(url_for("attendance.dashboard"))

    shift.is_active = False
    db.session.commit()

    flash("Attendance shift removed.", "success")
    return redirect(url_for("attendance.dashboard"))
