# /app/routes/tickets.py
from flask import Blueprint, flash, jsonify, redirect, request, session, url_for

from app import db
from app.models import Skipped, Ticket, User
from app.routes.queue_events import broadcast_ticket_update

tickets_bp = Blueprint("tickets", __name__, url_prefix="/api")


# GET: API route to get all tickets
@tickets_bp.route("/tickets", methods=["GET"])
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
def resolve_ticket(ticket_id):
    user = User.query.get(session["user_id"])
    resolved_as = request.form.get("resolve")

    if resolved_as not in ["duplicate", "helped", "no_show", "return_to_queue"]:
        flash("Invalid resolution option selected.", "error")
        return redirect(url_for("views.currentticket", tktid=ticket_id))
    elif resolved_as == "duplicate":
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            ticket.status = "resolved"
            ticket.resolve_reason = "duplicate"
            db.session.commit()
            broadcast_ticket_update(ticket.id)
            flash("Ticket marked as duplicate and resolved successfully", "success")
            return redirect(url_for("views.userpage", username=user.username))
        else:
            flash("Ticket not found", "error")
            return redirect(url_for("views.userpage", username=user.username))
    elif resolved_as == "helped":
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            ticket.status = "resolved"
            ticket.resolve_reason = "helped"
            db.session.commit()
            broadcast_ticket_update(ticket.id)
            flash("Ticket marked as helped and resolved successfully", "success")
            return redirect(url_for("views.userpage", username=user.username))
        else:
            flash("Ticket not found", "error")
            return redirect(url_for("views.userpage", username=user.username))
    elif resolved_as == "no_show":
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            ticket.status = "resolved"
            ticket.resolve_reason = "no_show"
            db.session.commit()
            broadcast_ticket_update(ticket.id)
            flash("Ticket marked as no show and resolved successfully", "success")
            return redirect(url_for("views.userpage", username=user.username))
        else:
            flash("Ticket not found", "error")
            return redirect(url_for("views.userpage", username=user.username))
    elif resolved_as == "return_to_queue":
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            ticket.status = "live"
            ticket.wa_id = None
            ticket.wormhole_assistant = None
            db.session.commit()
            broadcast_ticket_update(ticket.id)

            skipped = Skipped(wa_id=user.id, tkt_id=ticket_id)
            db.session.add(skipped)
            db.session.commit()

            flash("Ticket skipped and will be handled by another wormhole assistant")
            return redirect(url_for("views.userpage", username=user.username))
        else:
            flash("Ticket not found", "error")
            return redirect(url_for("views.userpage", username=user.username))
