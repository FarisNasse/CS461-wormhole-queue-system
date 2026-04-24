# /app/routes/tickets.py
from datetime import datetime, timezone

from flask import Blueprint, abort, flash, jsonify, redirect, request, session, url_for

from app import db
from app.auth_utils import admin_required, login_required
from app.forms import ResolveTicketForm
from app.models import Skipped, Ticket, User
from app.routes.queue_events import broadcast_ticket_update

tickets_bp = Blueprint("tickets", __name__, url_prefix="/api")


# GET: API route to get all tickets
@tickets_bp.route("/tickets", methods=["GET"])
@admin_required
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([t.to_dict() for t in tickets])


# POST: API route to create a new ticket
@tickets_bp.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json()
    student_name = data.get("student_name")
    physics_course = data.get("class_name")
    table = data.get("table_number")

    # Validate required fields
    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400

    # Create the new ticket
    new_ticket = Ticket(
        student_name=student_name,
        table=table,
        physics_course=physics_course,
        status="live",
    )

    # Add and commit the new ticket to the database
    db.session.add(new_ticket)
    db.session.commit()

    # Broadcast the new ticket to all connected queue clients
    broadcast_ticket_update(new_ticket.id)

    return jsonify(new_ticket.to_dict()), 201


# GET: API route to get all open tickets that the current user has not skipped
@tickets_bp.route("/unskippedtickets", methods=["GET"])
@login_required
def get_unskipped_tickets():
    # skipped_subquery = get all tickets skipped by current user
    # get all live tickets not
    user_id = session["user_id"]
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Get IDs of tickets already skipped by the current user
    skipped_subquery = (
        db.session.query(Skipped.tkt_id)
        .filter(Skipped.wa_id == user_id)
        .subquery()
        .select()
    )

    # Get all live tickets which the current user has not skipped
    tickets = (
        Ticket.query.filter_by(status="live")
        .filter(Ticket.id.notin_(skipped_subquery))
        .all()
    )

    return jsonify([t.to_dict() for t in tickets])


# GET: API route to get all open tickets
@tickets_bp.route("/opentickets", methods=["GET"])
@login_required
def get_open_tickets():
    # Get all live tickets
    tickets = Ticket.query.filter_by(status="live").all()

    return jsonify([t.to_dict() for t in tickets])


@tickets_bp.route("/livequeuetickets", methods=["GET"])
def get_livequeue_tickets():
    """Return every active ticket shown on the public live queue."""
    tickets = (
        Ticket.query.filter(Ticket.status.in_(["live", "in_progress"]))
        .order_by(Ticket.created_at)
        .all()
    )

    return jsonify([t.to_dict() for t in tickets])


# API route to handle ticket resolution form submission
@tickets_bp.route("/resolveticket/<int:ticket_id>", methods=["POST"])
@login_required
def resolve_ticket(ticket_id):
    user = db.session.get(User, session["user_id"])
    ticket = db.session.get(Ticket, ticket_id)

    if not user:
        abort(401)
    if not ticket:
        abort(404)
    if ticket.wa_id != user.id and not user.is_admin:
        abort(403)

    form = ResolveTicketForm()
    form.resolveReason.choices = [
        *form.resolveReason.choices,
        ("return_to_queue", "Return To Queue"),
    ]
    if not form.validate_on_submit():
        flash("Invalid request or session expired.", "error")
        return redirect(url_for("views.currentticket", tktid=ticket_id))

    resolved_as = form.resolveReason.data
    number_students = form.numStds.data if form.numStds.data is not None else 1

    if resolved_as == "return_to_queue":
        ticket.status = "live"
        ticket.wa_id = None
        ticket.wormhole_assistant = None
        db.session.add(Skipped(wa_id=user.id, tkt_id=ticket_id))
        db.session.commit()
        broadcast_ticket_update(ticket.id)
        flash("Ticket returned to the queue for another assistant.", "info")
        return redirect(url_for("views.userpage", username=user.username))

    if resolved_as in {"duplicate", "no_show"}:
        number_students = 0

    ticket.status = "closed"
    ticket.closed_reason = resolved_as
    ticket.closed_at = datetime.now(timezone.utc)
    ticket.number_of_students = number_students
    db.session.commit()
    broadcast_ticket_update(ticket.id)

    if resolved_as == "helped":
        flash(
            f"Ticket marked as helped and resolved successfully ({number_students} students)",
            "success",
        )
    else:
        flash(
            f"Ticket marked as {resolved_as.replace('_', ' ')} and resolved successfully",
            "success",
        )

    return redirect(url_for("views.userpage", username=user.username))
