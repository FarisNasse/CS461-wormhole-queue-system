# app/routes/views.py
import csv
import io
from datetime import datetime, time
from types import SimpleNamespace

from flask import (
    Blueprint,
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import db
from app.auth_utils import admin_required, login_required
from app.forms import (
    ChangePassForm,
    DeleteUserForm,
    LoginForm,
    RegisterBatchForm,
    RegisterForm,
    ResolveTicketForm,
    TicketForm,
)
from app.models import Ticket, User

views_bp = Blueprint("views", __name__)


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
    closed_tickets = (
        Ticket.query.filter_by(status="closed").order_by(Ticket.created_at.desc()).all()
    )

    ol = [_ticket_to_ns(t) for t in open_tickets]
    cul = [_ticket_to_ns(t) for t in current_tickets]
    cll = [_ticket_to_ns(t) for t in closed_tickets]

    return render_template(
        "queue.html", ol=ol, cul=cul, cll=cll, user=SimpleNamespace(username="admin")
    )


# -------------------------------
# GET /flush (Flush Queue)
# -------------------------------
@views_bp.route("/flush")
@login_required
def flush():
    # Placeholder for flushing/clearing the queue
    flash("Queue flushed", "info")
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
# GET /assistant-login (Assistant Login Page)
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


@views_bp.route("/archive/export", methods=["POST"])
@admin_required
def export_archive():
    # 1. Get dates from the form
    start_str = request.form.get("start_date")
    end_str = request.form.get("end_date")

    # 2. Validate input
    if not start_str or not end_str:
        flash("Please select both a start and end date.", "error")
        return redirect(url_for("views.archive"))

    # 3. Convert strings to datetime objects (handling full day ranges)
    # We set start time to 00:00:00 and end time to 23:59:59
    start_date = datetime.strptime(start_str, "%Y-%m-%d")
    end_date = datetime.combine(datetime.strptime(end_str, "%Y-%m-%d"), time.max)

    # 4. Query the database
    # We filter for tickets that are 'closed' AND created within the range
    tickets = (
        Ticket.query.filter(
            Ticket.status == "closed", Ticket.created_at.between(start_date, end_date)
        )
        .order_by(Ticket.created_at.desc())
        .all()
    )

    if not tickets:
        flash("No closed tickets found for this period.", "info")
        return redirect(url_for("views.archive"))

    # 5. Generate CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)

    # Write Header
    cw.writerow(
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

    # Write Rows
    for t in tickets:
        cw.writerow(
            [
                t.id,
                t.student_name,
                t.physics_course,
                t.table,
                t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                t.closed_at.strftime("%Y-%m-%d %H:%M:%S") if t.closed_at else "N/A",
                t.closed_reason or "N/A",
                t.wa_id or "Unassigned",
            ]
        )

    # 6. Create the response object
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = (
        f"attachment; filename=wormhole_archive_{start_str}_to_{end_str}.csv"
    )
    output.headers["Content-type"] = "text/csv"

    return output


# -------------------------------
# Auxiliary page routes for testing templates
# -------------------------------
@views_bp.route("/archive")
@admin_required
def archive():
    # keep lists empty to avoid url_for('protected') being invoked
    tkt_list = []
    assoc_list = []
    return render_template("archive.html", tkt_list=tkt_list, assoc_list=assoc_list)


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
    t = Ticket.query.get(tktid)
    if not t:
        abort(404)
    form = ResolveTicketForm()
    ticket_ns = _ticket_to_ns(t)
    return render_template("currentticket.html", ticket=ticket_ns, form=form)


@views_bp.route("/pastticket/<username>/<int:tktid>")
@login_required
def pastticket(username, tktid):
    t = Ticket.query.get(tktid)
    if not t:
        abort(404)
    form = ResolveTicketForm()
    ticket_ns = _ticket_to_ns(t)
    return render_template("pastticket.html", ticket=ticket_ns, form=form)
