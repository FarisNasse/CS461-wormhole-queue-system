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
from flask import send_from_directory, current_app
import os

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


# -------------------------------
# Auxiliary page routes for testing templates
# -------------------------------
@views_bp.route("/archive")
@admin_required
def archive():
    # show single closed tickets CSV if present
    data_dir = os.path.join(current_app.root_path, "data")
    csv_path = os.path.join(data_dir, "closed_tickets.csv")
    csv_exists = os.path.exists(csv_path)
    return render_template("archive.html", csv_exists=csv_exists)


@views_bp.route('/archive/download')
@admin_required
def download_closed_tickets():
    data_dir = os.path.join(current_app.root_path, "data")
    if not os.path.exists(os.path.join(data_dir, "closed_tickets.csv")):
        flash("No closed tickets file found.", "error")
        return redirect(url_for("views.archive"))
    return send_from_directory(data_dir, "closed_tickets.csv", as_attachment=True)


@views_bp.route('/archive/delete', methods=['POST'])
@admin_required
def delete_closed_tickets():
    data_dir = os.path.join(current_app.root_path, "data")
    csv_file = os.path.join(data_dir, "closed_tickets.csv")
    if os.path.exists(csv_file):
        try:
            os.remove(csv_file)
            flash("Closed tickets file deleted.", "success")
        except Exception:
            flash("Failed to delete file.", "error")
    else:
        flash("No closed tickets file found.", "error")
    return redirect(url_for("views.archive"))


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
