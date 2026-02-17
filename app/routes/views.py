# app/routes/views.py
import csv
import io
from datetime import datetime, time, timezone
from types import SimpleNamespace
from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)

from app import db
from app.auth_utils import admin_required, login_required
from app.forms import (
    ChangePassForm,
    DeleteUserForm,
    ExportArchiveForm,
    LoginForm,
    RegisterBatchForm,
    RegisterForm,
    ResolveTicketForm,
    TicketForm,
)
from app.models import Ticket, User

views_bp = Blueprint("views", __name__)


# --- Helper Functions ---


def is_safe_url(target):
    """Ensures a URL is a safe local path to prevent open redirects."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def _ticket_to_ns(ticket: Ticket):
    if ticket is None:
        return None
    return SimpleNamespace(
        id=ticket.id,
        name=ticket.student_name,
        table=ticket.table,
        phClass=ticket.physics_course,
        time_create=ticket.created_at,
        num_students=ticket.number_of_students,
    )


# --- Routes ---


# -------------------------------
# GET / (Student Home Page)
# -------------------------------
@views_bp.route("/")
@views_bp.route("/index", endpoint="index")
def index():
    return render_template("index.html")


# -------------------------------
# GET /livequeue (Live Queue)
# -------------------------------
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


# -------------------------------
# GET /wiki (Wiki Page)
# -------------------------------
@views_bp.route("/wiki")
def wiki():
    return render_template("wiki.html")


# -------------------------------
# GET /queue (New Queue Page)
# -------------------------------
@views_bp.route("/queue")
@login_required
def queue():
    # Fetch current queue data
    open_tickets = (
        Ticket.query.filter_by(status="live", wa_id=None)
        .order_by(Ticket.created_at)
        .all()
    )
    current_tickets = (
        Ticket.query.filter_by(status="current").order_by(Ticket.created_at).all()
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

    # Provide a form for CSRF protection on the flush action
    form = ResolveTicketForm()

    return render_template(
        "queue.html",
        ol=ol,
        cul=cul,
        cll=cll,
        user=SimpleNamespace(username="admin"),
        form=form,
    )


# -------------------------------
# POST /flush (Flush Queue)
# -------------------------------
@views_bp.route("/flush", methods=["POST"])
@admin_required
@login_required
def flush():
    # Close all tickets that are not already in a terminal state (closed/resolved)
    # This includes 'live', 'current', 'in_progress', etc.
    active_tickets = Ticket.query.filter(
        ~Ticket.status.in_(["closed", "resolved"])
    ).all()

    count = 0
    now = datetime.now(timezone.utc)
    for t in active_tickets:
        t.status = "closed"
        t.closed_reason = "Queue Flushed"
        t.closed_at = now
        count += 1

    # Commit all changes in a single transaction
    db.session.commit()

    flash(f"Queue flushed. {count} tickets closed.", "info")
    return redirect(url_for("views.queue"))


# -------------------------------
# GET /anonymize (Anonymize Closed Tickets)
# -------------------------------
@views_bp.route("/anonymize")
@login_required
def anonymize():
    # Placeholder for anonymizing closed tickets
    flash("Closed tickets anonymized", "info")
    return redirect(url_for("views.queue"))


# -------------------------------
# GET/POST /createticket (Help Request Creation)
# -------------------------------
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


# Debug endpoint to list all tickets
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
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in all_tickets
            ],
        }
    )


# -------------------------------
# GET/POST /assistant-login (Assistant Login Page)
# -------------------------------
@views_bp.route("/assistant-login", methods=["GET", "POST"])
def assistant_login():
    # support form-based login (POST) as well as rendering the login page (GET)
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["is_admin"] = user.is_admin
            if user.is_admin:
                return redirect(url_for("views.hardware_list"))
            return redirect(url_for("views.hardware_list"))

        flash("Invalid username or password.", "error")
        return render_template("login.html", form=form)

    return render_template("login.html", form=form)


# -------------------------------
# GET /dashboard (Protected Area)
# -------------------------------
@views_bp.route("/dashboard")
@login_required
def dashboard():
    return "<h1>Welcome! You are logged in to the Wormhole System.</h1>", 200


# -------------------------------
# GET /hardware_list (Hardware List)
# -------------------------------
@views_bp.route("/hardware_list")
@login_required
def hardware_list():
    # Placeholder for hardware list - will be populated with actual data
    boxes = []
    return render_template("hardware_list.html", boxes=boxes)


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

    # 3. Parse dates (combine with time.min/max for full day coverage)
    # Ensure they are timezone aware (UTC) to match database storage
    start_date = datetime.combine(form.start_date.data, time.min).replace(
        tzinfo=timezone.utc
    )
    end_date = datetime.combine(form.end_date.data, time.max).replace(
        tzinfo=timezone.utc
    )

    # 4. Logical Validation
    if start_date > end_date:
        flash("Start date cannot be after end date.", "error")
        return redirect(url_for("views.archive"))

    # 5. Query the database using closed_at
    # Filter for all terminal statuses ("closed", "resolved")
    tickets_query = Ticket.query.filter(
        Ticket.status.in_(["closed", "resolved"]),
        Ticket.closed_at.between(start_date, end_date),
    ).order_by(Ticket.closed_at.desc())

    # Check for empty results without loading objects
    if tickets_query.first() is None:
        flash("No closed or resolved tickets found for this period.", "info")
        return redirect(url_for("views.archive"))

    # 6. Streaming CSV Generation
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)

        # CSV Injection Sanitization Helper
        def sanitize(value):
            if value and isinstance(value, str):
                normalized = value.lstrip()
                if normalized.startswith(("=", "+", "-", "@")):
                    return f"'{value}"
            return value

        # Write Header
        writer.writerow(
            [
                "Ticket ID",
                "Student Name",
                "Course",
                "Table",
                "Created At",
                "Closed At",
                "Resolution",
                "Assistant ID",
            ]
        )
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)

        # Write Rows in batches to avoid memory overload
        for t in tickets_query.yield_per(1000):
            writer.writerow(
                [
                    t.id,
                    sanitize(t.student_name),
                    t.physics_course,
                    t.table,
                    t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    t.closed_at.strftime("%Y-%m-%d %H:%M:%S") if t.closed_at else "N/A",
                    sanitize(t.closed_reason) or "N/A",
                    t.wa_id or "Unassigned",
                ]
            )
            yield output.getvalue()
            output.truncate(0)
            output.seek(0)

    # 7. Create the streaming response object
    filename = f"wormhole_archive_{start_date.date()}_to_{end_date.date()}.csv"
    return Response(
        stream_with_context(generate()),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# -------------------------------
# Auxiliary page routes for testing templates
# -------------------------------
@views_bp.route("/archive")
@admin_required
def archive():
    # Instantiate form for the template to render CSRF token and fields
    form = ExportArchiveForm()
    tkt_list = []
    assoc_list = []
    return render_template(
        "archive.html", tkt_list=tkt_list, assoc_list=assoc_list, form=form
    )


@views_bp.route("/user/<username>")
def userpage(username):
    u = User.query.filter_by(username=username).first()
    if not u:
        abort(404)
    # create minimal surface for template
    user_ns = SimpleNamespace(
        username=u.username,
        email=u.email,
        is_admin=u.is_admin,
        tkt=None,
        all_tkt_assoc_sorted=lambda: [],
    )
    current_user = user_ns
    return render_template("userpage.html", user=user_ns, current_user=current_user)


@views_bp.route("/getnewticket/<username>")
@login_required
def getnewticket(username):
    # Assign the next available live ticket to the given user and redirect
    u = User.query.filter_by(username=username).first()
    if not u:
        abort(404)

    # find the oldest live unassigned ticket
    t = (
        Ticket.query.filter_by(status="live", wa_id=None)
        .order_by(Ticket.created_at)
        .first()
    )
    if not t:
        # no tickets available; redirect back to user page
        flash("No available tickets to claim.", "info")
        return redirect(url_for("views.userpage", username=username))

    t.assign_to(u)
    return redirect(url_for("views.currentticket", tktid=t.id))


@views_bp.route("/user_list")
@admin_required
def user_list():
    users = User.query.all()
    new_users = [SimpleNamespace(username=u.username) for u in users]
    old_users = []
    return render_template("user_list.html", new_users=new_users, old_users=old_users)


@views_bp.route("/users_add", methods=["GET"])
@admin_required
def users_add():
    form = RegisterForm()
    return render_template("users_add.html", form=form)


@views_bp.route("/register_batch", methods=["GET", "POST"])
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
    form = DeleteUserForm()
    user_ns = SimpleNamespace(username=u.username)
    return render_template("delete_user.html", user=user_ns, form=form)


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
    # Use session.get for SQLAlchemy 2.0 compliance
    t = db.session.get(Ticket, tktid)
    if not t:
        abort(404)
    form = ResolveTicketForm()

    if form.validate_on_submit():
        # Delegate closing logic to the model method
        # Standardize num_stds retrieval logic
        num_stds = form.numStds.data if form.numStds.data else 1

        t.close_ticket(closed_reason=form.resolveReason.data, num_students=num_stds)

        flash("Ticket resolved successfully.", "success")

        # Open Redirect Protection
        next_page = request.args.get("next")
        if is_safe_url(next_page):
            return redirect(next_page)

        return redirect(url_for("views.queue"))

    ticket_ns = _ticket_to_ns(t)
    return render_template("pastticket.html", ticket=ticket_ns, form=form)
