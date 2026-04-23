# app/routes/views.py
import csv
import io
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

# Explicit imports for SQLAlchemy operators to ensure compatibility
from sqlalchemy import and_, func, or_, text

from app import db
from app.attendance_utils import (
    active_attendance_session_for_user,
    attendance_status_for_session,
    build_attendance_dashboard,
    record_attendance_activity,
    touch_attendance,
)
from app.auth_utils import admin_required, login_required
from app.forms import (
    AttendanceCheckInForm,
    AttendanceCheckOutForm,
    ChangePassForm,
    ClearQueueForm,
    DeleteArchiveForm,
    DeleteUserForm,
    EditUserForm,
    ExportArchiveForm,
    FlushQueueForm,
    LoginForm,
    RegisterBatchForm,
    RegisterForm,
    ResolveTicketForm,
    TicketForm,
)
from app.models import AttendanceActivity, Skipped, Ticket, User
from app.time_utils import (
    PACIFIC_TZ,
    format_pacific,
    pacific_day_bounds_to_utc,
    serialize_datetime,
)

views_bp = Blueprint("views", __name__)


# --- Helper Functions ---


def is_safe_url(target):
    """Ensures a URL is a safe local path to prevent open redirects."""
    # Ensure target is a non-empty string before using it with urljoin/urlparse
    if not target or not isinstance(target, str):
        return False
    stripped_target = target.strip()
    if not stripped_target:
        return False
    # Reject protocol-relative URLs (e.g., "//example.com/path") to prevent open redirects
    if stripped_target.startswith("//"):
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, stripped_target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def _ticket_to_ns(ticket: Ticket):
    if ticket is None:
        return None
    assistant_display_name = (
        ticket.wormhole_assistant.name
        if ticket.wormhole_assistant and ticket.wormhole_assistant.name
        else (
            ticket.wormhole_assistant.username
            if ticket.wormhole_assistant
            else "Unassigned"
        )
    )
    return SimpleNamespace(
        id=ticket.id,
        name=ticket.student_name,
        table=ticket.table,
        phClass=ticket.physics_course,
        time_create=ticket.created_at,
        time_close=ticket.closed_at,
        time_create_pacific=format_pacific(ticket.created_at, "%I:%M %p"),
        time_close_pacific=format_pacific(ticket.closed_at, "%I:%M %p"),
        num_students=ticket.number_of_students,
        closed_reason=ticket.closed_reason,
        closed_by=assistant_display_name,
        assigned_to=assistant_display_name,
    )


def _archive_dir() -> Path:
    archive_dir = Path(__file__).resolve().parents[1] / "data" / "archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def _list_archive_files() -> list[str]:
    archive_dir = _archive_dir()
    return sorted(
        [path.name for path in archive_dir.glob("*.csv") if path.is_file()],
        reverse=True,
    )


# --- Routes ---


@views_bp.route("/")
@views_bp.route("/index", endpoint="index")
def index():
    return render_template("index.html")


@views_bp.route("/livequeue")
def livequeue():
    # Fetch current open tickets for initial page load
    open_tickets = (
        Ticket.query.filter_by(status="live", wa_id=None)
        .order_by(Ticket.created_at)
        .all()
    )
    ol = [_ticket_to_ns(t) for t in open_tickets]
    return render_template("livequeue.html", ol=ol)


@views_bp.route("/wiki")
def wiki():
    return render_template("wiki.html")


@views_bp.route("/queue")
@login_required
def queue():
    # 1. Fetch the REAL user to ensure template links use the correct username
    sid = session.get("user_id")
    current_user_obj = db.session.get(User, sid) if sid else None

    if not current_user_obj:
        return redirect(url_for("views.assistant_login"))

    # Fetch current queue data
    open_tickets = (
        Ticket.query.filter_by(status="live", wa_id=None)
        .order_by(Ticket.created_at)
        .all()
    )

    # Filter by 'in_progress' to match Ticket.assign_to() logic
    current_tickets = (
        Ticket.query.filter_by(status="in_progress").order_by(Ticket.created_at).all()
    )

    # Include both "closed" and "resolved" in the historical list
    closed_tickets = (
        Ticket.query.filter(Ticket.status.in_(["closed", "resolved"]))
        .order_by(Ticket.created_at.desc())
        .all()
    )

    ol = [_ticket_to_ns(t) for t in open_tickets]
    cul = [_ticket_to_ns(t) for t in current_tickets]
    cll = [_ticket_to_ns(t) for t in closed_tickets]

    touch_attendance(current_user_obj.id)

    attendance_rows = []
    attendance_summary = None
    recent_attendance_activities = []
    if current_user_obj.is_admin:
        attendance_rows, attendance_summary = build_attendance_dashboard()
        recent_attendance_activities = (
            AttendanceActivity.query.order_by(AttendanceActivity.created_at.desc())
            .limit(10)
            .all()
        )

    # Use dedicated CSRF-protected forms for admin queue actions
    flush_form = FlushQueueForm()
    clear_form = ClearQueueForm()

    # Pass the real user object so permissions and usernames are correct in the template
    return render_template(
        "queue.html",
        ol=ol,
        cul=cul,
        cll=cll,
        user=current_user_obj,
        flush_form=flush_form,
        clear_form=clear_form,
        attendance_rows=attendance_rows,
        attendance_summary=attendance_summary,
        recent_attendance_activities=recent_attendance_activities,
    )


# -------------------------------
# POST /flush (Flush Queue)
# -------------------------------
@views_bp.route("/flush", methods=["POST"])
@admin_required
def flush():
    # Validate the form to enforce CSRF protection
    form = FlushQueueForm()
    if not form.validate_on_submit():
        flash("Invalid request or session expired.", "error")
        return redirect(url_for("views.queue"))

    # Use bulk UPDATE for performance
    now = datetime.now(timezone.utc)

    # Update all non-closed/resolved tickets
    count = Ticket.query.filter(~Ticket.status.in_(["closed", "resolved"])).update(
        {
            Ticket.status: "closed",
            Ticket.closed_reason: "Queue Flushed",
            Ticket.closed_at: now,
            Ticket.number_of_students: 0,
        },
        synchronize_session=False,
    )

    db.session.commit()

    flash(f"Queue flushed. {count} tickets closed.", "info")
    return redirect(url_for("views.queue"))


@views_bp.route("/clear_queue", methods=["POST"])
@admin_required
def clear_queue():
    """Permanently clear all queue ticket rows and reset ticket indexing."""
    form = ClearQueueForm()
    if not form.validate_on_submit():
        flash("Invalid request or session expired.", "error")
        return redirect(url_for("views.queue"))

    cleared_count = Ticket.query.count()
    bind = db.session.get_bind()
    dialect_name = bind.dialect.name if bind and bind.dialect else ""

    try:
        if dialect_name == "postgresql":
            db.session.execute(text("TRUNCATE TABLE tickets RESTART IDENTITY CASCADE"))
        elif dialect_name in {"mysql", "mariadb"}:
            db.session.execute(text("TRUNCATE TABLE tickets"))
        else:
            Ticket.query.delete(synchronize_session=False)
            if dialect_name == "sqlite":
                # Reset SQLite AUTOINCREMENT sequence (if sqlite_sequence exists).
                try:
                    db.session.execute(
                        text("DELETE FROM sqlite_sequence WHERE name = 'tickets'")
                    )
                except Exception:
                    pass

        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Unable to clear queue data.", "error")
        return redirect(url_for("views.queue"))

    flash(
        f"Queue data cleared permanently. {cleared_count} tickets removed.",
        "info",
    )
    return redirect(url_for("views.queue"))


@views_bp.route("/createticket", methods=["GET", "POST"])
def create_ticket_page():
    form = TicketForm()
    if form.validate_on_submit():
        t = Ticket(
            student_name=form.name.data,
            table=form.location.data,
            physics_course=form.phClass.data,
            number_of_students=1,
            status="live",
        )
        db.session.add(t)
        db.session.commit()

        # broadcast update to queue clients
        try:
            from app.routes.queue_events import broadcast_ticket_update

            broadcast_ticket_update(t.id)
        except Exception:
            pass

        flash("Ticket created — thank you!", "success")
        return redirect(url_for("views.livequeue"))

    return render_template("createticket.html", form=form)


@views_bp.route("/debug/tickets")
def debug_tickets():
    """List all tickets for debugging."""
    from flask import jsonify

    all_tickets = Ticket.query.all()
    return jsonify(
        {
            "total": len(all_tickets),
            "tickets": [
                {
                    "id": t.id,
                    "name": t.student_name,
                    "class": t.physics_course,
                    "table": t.table,
                    "status": t.status,
                    "created_at": serialize_datetime(t.created_at),
                    "created_at_local": format_pacific(
                        t.created_at, "%Y-%m-%d %H:%M:%S %Z"
                    ),
                }
                for t in all_tickets
            ],
        }
    )


@views_bp.route("/assistant-login", methods=["GET", "POST"])
def assistant_login():
    # support form-based login (POST) as well as rendering the login page (GET)
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash("This account has been deactivated.", "error")
                return render_template("login.html", form=form)
            session["user_id"] = user.id
            session["is_admin"] = user.is_admin
            if user.is_admin:
                return redirect(url_for("views.hardware_list"))
            return redirect(url_for("views.hardware_list"))

        flash("Invalid username or password.", "error")
        return render_template("login.html", form=form)

    return render_template("login.html", form=form)


@views_bp.route("/dashboard")
@login_required
def dashboard():
    return "<h1>Welcome! You are logged in to the Wormhole System.</h1>", 200


@views_bp.route("/hardware_list")
@login_required
def hardware_list():
    # Placeholder for hardware list - will be populated with actual data
    boxes = []
    sid = session.get("user_id")
    current_user_obj = db.session.get(User, sid) if sid else None
    active_session = (
        active_attendance_session_for_user(current_user_obj.id)
        if current_user_obj
        else None
    )
    attendance_status = (
        attendance_status_for_session(active_session) if active_session else None
    )
    check_in_form = AttendanceCheckInForm()
    check_out_form = AttendanceCheckOutForm()
    touch_attendance(current_user_obj.id) if current_user_obj else None
    return render_template(
        "hardware_list.html",
        boxes=boxes,
        attendance_session=active_session,
        attendance_status=attendance_status,
        check_in_form=check_in_form,
        check_out_form=check_out_form,
    )


@views_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("views.index"))


# -------------------------------
# POST /archive/export (Archive Export)
# -------------------------------
@views_bp.route("/archive/export", methods=["POST"])
@admin_required
def export_archive():
    form = ExportArchiveForm()
    if not form.validate_on_submit():
        flash("Invalid date format or missing fields.", "error")
        return redirect(url_for("views.archive"))

    # Interpret the selected dates in Pacific Time, then convert to UTC for querying.
    start_date, _ = pacific_day_bounds_to_utc(form.start_date.data)
    _, end_date = pacific_day_bounds_to_utc(form.end_date.data)

    # Logical Validation
    if start_date > end_date:
        flash("Start date cannot be after end date.", "error")
        return redirect(url_for("views.archive"))

    # Prevent exporting archives for future dates
    now_pacific = datetime.now(PACIFIC_TZ)
    now_pacific = now_pacific.replace(hour=23, minute=59, second=59, microsecond=999999)
    if (
        form.start_date.data > now_pacific.date()
        or form.end_date.data > now_pacific.date()
    ):
        flash("Dates cannot be in the future.", "error")
        return redirect(url_for("views.archive"))

    # Query the database using closed_at OR fallback to created_at for resolved tickets
    # Using explicit or_ / and_ for compatibility
    tickets_query = Ticket.query.filter(
        or_(
            and_(
                Ticket.status.in_(["closed", "resolved"]),
                Ticket.closed_at.between(start_date, end_date),
            ),
            and_(
                Ticket.status == "resolved",
                Ticket.closed_at.is_(None),
                Ticket.created_at.between(start_date, end_date),
            ),
        )
    ).order_by(func.coalesce(Ticket.closed_at, Ticket.created_at).desc())

    # Optimization: Use limit(1) instead of count() to check for existence
    if tickets_query.limit(1).first() is None:
        flash("No closed or resolved tickets found for this period.", "info")
        return redirect(url_for("views.archive"))

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Injection Sanitization Helper
    def sanitize(value):
        if value and isinstance(value, str):
            normalized = value.lstrip()
            if normalized.startswith(("=", "+", "-", "@")):
                # Prepend quote to the ORIGINAL value so leading whitespace is preserved
                return f"'{value}"
        return value

    writer.writerow(
        [
            "Ticket ID",
            "Student Name",
            "Table",
            "Course",
            "Status",
            "Created At",
            "Closed At",
            "Students Helped",
            "Assistant ID",
            "Assistant Name",
            "Ticket Type",
        ]
    )

    for t in tickets_query.yield_per(1000):
        writer.writerow(
            [
                t.id,
                sanitize(t.student_name),
                sanitize(t.table),
                sanitize(t.physics_course),
                t.closed_reason,
                t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                t.closed_at.strftime("%Y-%m-%d %H:%M:%S") if t.closed_at else "N/A",
                t.number_of_students,
                t.wa_id or "Unassigned",
                t.wormhole_assistant.name
                if t.wormhole_assistant and t.wormhole_assistant.name
                else ("N/A"),
                "Zoom"
                if t.table == "Zoom"
                else "Teams"
                if t.table == "Teams"
                else "Box",
            ]
        )

    csv_content = output.getvalue()

    safe_start = start_date.date().isoformat()
    safe_end = end_date.date().isoformat()
    filename = f"wormhole_archive_{safe_start}_to_{safe_end}.csv"

    archive_path = _archive_dir() / filename
    try:
        with archive_path.open("w", encoding="utf-8", newline="") as archive_file:
            archive_file.write(csv_content)
    except OSError:
        flash("Failed to save archive file on server.", "error")
        return redirect(url_for("views.archive"))

    flash(f"Archive created: {filename}", "success")
    return redirect(url_for("views.archive"))


# -------------------------------
# Auxiliary page routes for testing templates
# -------------------------------
@views_bp.route("/archive")
@admin_required
def archive():
    # Instantiate form for the template to render CSRF token and fields
    form = ExportArchiveForm()
    delete_form = DeleteArchiveForm()
    archive_files = _list_archive_files()
    tkt_list = []
    assoc_list = []
    return render_template(
        "archive.html",
        tkt_list=tkt_list,
        assoc_list=assoc_list,
        archive_files=archive_files,
        delete_form=delete_form,
        form=form,
    )


@views_bp.route("/archive/delete", methods=["POST"])
@admin_required
def delete_archives():
    form = DeleteArchiveForm()
    if not form.validate_on_submit():
        flash("Invalid request or session expired.", "error")
        return redirect(url_for("views.archive"))

    selected_files = request.form.getlist("filenames")
    if not selected_files:
        flash("No archive files selected.", "info")
        return redirect(url_for("views.archive"))

    archive_dir = _archive_dir()
    deleted_count = 0

    for raw_name in selected_files:
        safe_name = Path(raw_name).name
        if safe_name != raw_name or not safe_name.lower().endswith(".csv"):
            continue

        archive_path = archive_dir / safe_name
        try:
            if archive_path.is_file():
                archive_path.unlink()
                deleted_count += 1
        except OSError:
            continue

    if deleted_count > 0:
        flash(f"Deleted {deleted_count} archive file(s).", "success")
    else:
        flash("No archive files were deleted.", "info")

    return redirect(url_for("views.archive"))


@views_bp.route("/archive/download/<path:filename>")
@admin_required
def download_archive(filename):
    safe_filename = Path(filename).name
    if safe_filename != filename or not safe_filename.lower().endswith(".csv"):
        abort(404)

    archive_dir = _archive_dir()
    file_path = archive_dir / safe_filename
    if not file_path.is_file():
        abort(404)

    return send_from_directory(str(archive_dir), safe_filename, as_attachment=True)


@views_bp.route("/user/<username>")
@login_required
def userpage(username):
    u = User.query.filter_by(username=username).first()
    if not u:
        abort(404)
    # Get user's current ticket (if any)
    current_ticket = Ticket.query.filter_by(wa_id=u.id, status="in_progress").first()
    # All Skipped?
    # Get IDs of tickets already skipped by the current user
    skipped_subquery = (
        db.session.query(Skipped.tkt_id)
        .filter(Skipped.wa_id == session["user_id"])
        .subquery()
        .select()
    )

    # Get all live tickets which the current user has not skipped
    ticket_count = (
        Ticket.query.filter_by(status="live")
        .filter(Ticket.id.notin_(skipped_subquery))
        .count()
    )
    skipped_all = ticket_count == 0
    # create minimal surface for template
    active_session = active_attendance_session_for_user(u.id)
    attendance_status = (
        attendance_status_for_session(active_session) if active_session else None
    )
    if session.get("user_id") == u.id:
        touch_attendance(u.id)

    user_ns = SimpleNamespace(
        id=u.id,
        username=u.username,
        email=u.email,
        name=u.name,
        is_admin=u.is_admin,
        tkt=current_ticket,
        all_tkt_assoc_sorted=lambda: [],
    )
    logged_in_user = db.session.get(User, session.get("user_id"))
    current_user = SimpleNamespace(
        username=logged_in_user.username if logged_in_user else "",
        is_admin=bool(logged_in_user.is_admin) if logged_in_user else False,
        is_anonymous=logged_in_user is None,
    )
    return render_template(
        "userpage.html",
        user=user_ns,
        current_user=current_user,
        skipped_all=skipped_all,
        attendance_session=active_session,
        attendance_status=attendance_status,
        check_in_form=AttendanceCheckInForm(),
        check_out_form=AttendanceCheckOutForm(),
    )


@views_bp.route("/getnewticket/<username>")
@login_required
def getnewticket(username):
    # Assign the next available live ticket to the given user and redirect
    u = User.query.filter_by(username=username).first()
    if not u:
        abort(404)

    # Get IDs of tickets already skipped by the current user
    skipped_subquery = (
        db.session.query(Skipped.tkt_id)
        .filter(Skipped.wa_id == session["user_id"])
        .subquery()
        .select()
    )

    # Get the live ticket which the current user has not skipped that is first in line
    t = (
        Ticket.query.filter_by(status="live")
        .filter(Ticket.id.notin_(skipped_subquery))
        .first()
    )

    if not t:
        # no tickets available; redirect back to user page
        flash("No available tickets to claim.", "info")
        return redirect(url_for("views.userpage", username=username))

    t.assign_to(u)
    record_attendance_activity(
        u.id,
        "ticket_claimed",
        f"Claimed ticket #{t.id} for {t.student_name}.",
        ticket_id=t.id,
    )

    try:
        from app.routes.queue_events import broadcast_ticket_update

        broadcast_ticket_update(t.id)
    except Exception:
        pass

    return redirect(url_for("views.currentticket", tktid=t.id))


@views_bp.route("/user_list")
@admin_required
def user_list():
    current_users = User.query.filter_by(is_active=True).all()
    old_users = User.query.filter_by(is_active=False).all()

    def last_name(user):
        if not user.name:
            return ""
        return user.name.split()[-1].lower()

    new_users = sorted(current_users, key=last_name)
    old_users = sorted(old_users, key=last_name)

    return render_template("user_list.html", new_users=new_users, old_users=old_users)


@views_bp.route("/register", methods=["GET"])
@admin_required
def register():
    form = RegisterForm()
    return render_template("register.html", form=form)


@views_bp.route("/register_batch", methods=["GET"])
@admin_required
def register_batch():
    form = RegisterBatchForm()
    return render_template("register_batch.html", form=form)


@views_bp.route("/delete/<username>", methods=["GET", "POST"])
@admin_required
def delete_user(username):
    u = User.query.filter_by(username=username).first()
    if not u:
        abort(404)
    # Parse first and last name from the name field
    name_parts = u.name.split() if u.name else ["", ""]
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    delete_form = DeleteUserForm()
    edit_form = EditUserForm()
    # Handle POST requests
    if request.method == "POST":
        # Check which form was submitted
        if delete_form.submit.data and delete_form.validate():
            if delete_form.confirm.data == "DELETE":
                username_to_delete = u.username
                db.session.delete(u)
                db.session.commit()
                flash(
                    f"User {username_to_delete} has been deleted permanently.",
                    "success",
                )
                return redirect(url_for("views.user_list"))
            else:
                flash('Please type "DELETE" to confirm user deletion.', "error")
        elif edit_form.submit.data and edit_form.validate():
            # Update user fields based on form data
            if edit_form.first_name.data or edit_form.last_name.data:
                new_first = edit_form.first_name.data or first_name
                new_last = edit_form.last_name.data or last_name
                u.name = f"{new_first} {new_last}".strip()
            if edit_form.onid.data:
                # ONID is the username, which is unique and shouldn't be changed easily
                # For now, we'll skip this or validate it
                if edit_form.onid.data != u.username:
                    existing_user = User.query.filter_by(
                        username=edit_form.onid.data
                    ).first()
                    if existing_user:
                        flash("This ONID is already in use.", "error")
                        return render_template(
                            "delete_user.html",
                            user=SimpleNamespace(username=u.username),
                            delete_form=delete_form,
                            edit_form=edit_form,
                        )
                    u.username = edit_form.onid.data
            if edit_form.email.data:
                if edit_form.email.data != u.email:
                    existing_user = User.query.filter_by(
                        email=edit_form.email.data
                    ).first()
                    if existing_user:
                        flash("This email is already in use.", "error")
                        return render_template(
                            "delete_user.html",
                            user=SimpleNamespace(username=u.username),
                            delete_form=delete_form,
                            edit_form=edit_form,
                        )
                    u.email = edit_form.email.data
            if edit_form.is_admin.data:
                u.is_admin = edit_form.is_admin.data == "true"
            if edit_form.is_active.data:
                u.is_active = edit_form.is_active.data == "true"
            db.session.commit()
            flash("User information has been updated successfully.", "success")
            # Refresh the page with updated data
            return redirect(url_for("views.delete_user", username=u.username))
    user_ns = SimpleNamespace(username=u.username)
    return render_template(
        "delete_user.html",
        user=user_ns,
        delete_form=delete_form,
        edit_form=edit_form,
        user_data=SimpleNamespace(
            first_name=first_name,
            last_name=last_name,
            onid=u.username,
            email=u.email,
            is_admin=u.is_admin,
            is_active=u.is_active,
        ),
    )


@views_bp.route("/changepass", methods=["GET", "POST"])
@login_required
def changepass():
    form = ChangePassForm()
    if form.validate_on_submit():
        username = form.username.data
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("User not found.", "error")
            return render_template("changepass.html", form=form)

        # get current session user
        sid = session.get("user_id")
        cur = User.query.get(sid) if sid else None
        if not cur:
            flash("Not authorized.", "error")
            return render_template("changepass.html", form=form)

        # allow admins to change without old password
        if cur.id != user.id and not cur.is_admin:
            flash("Not authorized to change this user's password.", "error")
            return render_template("changepass.html", form=form)

        # if changing own password, verify old password
        if cur.id == user.id and not user.check_password(form.old_password.data):
            flash("Old password is incorrect.", "error")
            return render_template("changepass.html", form=form)

        # set new password
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("views.userpage", username=user.username))

    return render_template("changepass.html", form=form)


@views_bp.route("/currentticket/<int:tktid>")
@login_required
def currentticket(tktid):
    # Use session.get for SQLAlchemy 2.0 compliance
    t = db.session.get(Ticket, tktid)
    if not t:
        abort(404)
    form = ResolveTicketForm()
    ticket_ns = _ticket_to_ns(t)
    return render_template("currentticket.html", ticket=ticket_ns, form=form)


# -------------------------------
# POST /pastticket (Past Ticket Resolution)
# -------------------------------
@views_bp.route("/pastticket/<username>/<int:tktid>", methods=["GET", "POST"])
@login_required
def pastticket(username, tktid):
    # Validate authorization first: Ensure path username matches logged-in user or admin
    sid = session.get("user_id")
    current_user_obj = db.session.get(User, sid) if sid else None

    if not current_user_obj or (
        current_user_obj.username != username and not current_user_obj.is_admin
    ):
        abort(403)

    # Use session.get for SQLAlchemy 2.0 compliance
    t = db.session.get(Ticket, tktid)
    if not t:
        abort(404)
    form = ResolveTicketForm()

    if form.validate_on_submit():
        # Delegate closing logic to the model method
        # Standardize num_stds retrieval logic
        num_stds = form.numStds.data if form.numStds.data is not None else 1

        # Persist the user performing the close so history can show who resolved it.
        t.wa_id = current_user_obj.id

        t.close_ticket(closed_reason=form.resolveReason.data, num_students=num_stds)
        record_attendance_activity(
            current_user_obj.id,
            "ticket_resolved",
            f"Resolved ticket #{t.id} as {form.resolveReason.data}.",
            ticket_id=t.id,
        )

        flash("Ticket resolved successfully.", "success")

        # Open Redirect Protection
        next_page = request.args.get("next")
        if is_safe_url(next_page):
            return redirect(next_page)

        return redirect(url_for("views.queue"))

    ticket_ns = _ticket_to_ns(t)
    return render_template("pastticket.html", ticket=ticket_ns, form=form)
