# /app/routes/tickets.py
from flask import Blueprint, flash, jsonify, redirect, request, session, url_for, current_app

from app import db
from app.forms import ResolveTicketForm
from app.models import Ticket, User
from app.routes.queue_events import broadcast_ticket_update
import os
import csv
from datetime import datetime, timezone

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


# GET: API route to get all open tickets
@tickets_bp.route("/opentickets", methods=["GET"])
def get_open_tickets():
    tickets = Ticket.query.filter_by(status="live").all()
    return jsonify([t.to_dict() for t in tickets])


# API route to handle ticket resolution form submission
@tickets_bp.route("/resolveticket/<int:ticket_id>", methods=["POST"])
def resolve_ticket(ticket_id):
    user = User.query.get(session["user_id"])
    form = ResolveTicketForm()
    if form.validate_on_submit():
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            ticket.status = "resolved"
            ticket.number_of_students = form.numStds.data
            ticket.resolve_reason = form.resolveReason.data
            # mark closed time for archive purposes
            ticket.closed_at = datetime.now(timezone.utc)
            db.session.commit()
            # append to closed tickets CSV
            try:
                data_dir = os.path.join(current_app.root_path, "data")
                os.makedirs(data_dir, exist_ok=True)
                csv_path = os.path.join(data_dir, "closed_tickets.csv")
                write_header = not os.path.exists(csv_path)
                with open(csv_path, "a", newline='', encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    if write_header:
                        writer.writerow([
                            "ticket_id",
                            "name",
                            "table",
                            "class",
                            "status",
                            "created_at",
                            "updated_at",
                            "num_students",
                            "ticket_type",
                        ])
                    writer.writerow([
                        ticket.id,
                        ticket.student_name,
                        ticket.table,
                        ticket.physics_course,
                        ticket.status,
                        ticket.created_at.isoformat() if ticket.created_at else "",
                        ticket.closed_at.isoformat() if ticket.closed_at else "",
                        ticket.number_of_students if ticket.number_of_students is not None else "",
                        ticket.resolve_reason or ticket.closed_reason or "",
                    ])
            except Exception:
                # Do not block resolution on CSV errors
                pass
            broadcast_ticket_update(ticket.id)
            flash("Ticket resolved successfully", "success")
            return redirect(url_for("views.userpage", username=user.username))
        else:
            flash("Ticket not found", "error")
            return redirect(url_for("views.userpage", username=user.username))
    else:
        flash("There was a problem resolving the ticket.", "error")
        return redirect(url_for("views.currentticket", tktid=ticket_id))
