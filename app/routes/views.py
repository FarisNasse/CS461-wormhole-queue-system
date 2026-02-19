# app/routes/views.py
from types import SimpleNamespace

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)

from app import db
from app.auth_utils import admin_required, login_required
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
@views_bp.route("/createticket", methods=["GET"])
def create_ticket_page():
    # Render the create ticket form (submission handled via /api/tickets)
    return render_template("createticket.html")


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
@views_bp.route("/assistant-login", methods=["GET"])
def assistant_login():
    # Render login page (form submission now handled via /api/login)
    return render_template("login.html")


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


@views_bp.route("/register", methods=["GET"])
@admin_required
def register():
    # Render registration form (submission handled via /api/users_add_json)
    return render_template("register.html")


@views_bp.route("/register_batch", methods=["GET"])
@admin_required
def register_batch():
    # Render batch registration form (submission handled via /api/register_batch)
    return render_template("register_batch.html")


@views_bp.route("/delete/<username>", methods=["GET"])
@admin_required
def delete_user(username):
    u = User.query.filter_by(username=username).first()
    if not u:
        abort(404)
    user_ns = SimpleNamespace(username=u.username)
    # Render delete confirmation form (submission handled via /api/users_remove)
    return render_template("delete_user.html", user=user_ns)


@views_bp.route("/changepass", methods=["GET"])
@login_required
def changepass():
    # Render password change form (submission handled via /api/changepass)
    return render_template("changepass.html")


@views_bp.route("/currentticket/<int:tktid>")
@login_required
def currentticket(tktid):
    t = Ticket.query.get(tktid)
    if not t:
        abort(404)
    ticket_ns = _ticket_to_ns(t)
    # Pass ticket ID for JavaScript to use in API calls
    return render_template("currentticket.html", ticket=ticket_ns)


@views_bp.route("/pastticket/<username>/<int:tktid>")
@login_required
def pastticket(username, tktid):
    t = Ticket.query.get(tktid)
    if not t:
        abort(404)
    ticket_ns = _ticket_to_ns(t)
    # Pass ticket ID for JavaScript to use in API calls
    return render_template("pastticket.html", ticket=ticket_ns)
