# /app/routes/tickets.py
from flask import Blueprint, jsonify, request

from app import db
from app.models import Ticket
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
    location = data.get("table_number")

    # Validate required fields
    if not student_name or not physics_course or not location:
        return jsonify({"error": "Missing required fields"}), 400

    # Create the new ticket
    new_ticket = Ticket(
        student_name=student_name,
        table=location,
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
    data = request.get_json()
    
    # Get form data
    num_students_str = data.get("numStds", "")
    resolve_reason = data.get("resolveReason")

    # Validate required fields
    if not resolve_reason:
        return jsonify({"error": "Resolution reason is required"}), 400

    # Parse and validate number of students (optional, but must be positive if provided)
    num_students = None
    if num_students_str:
        try:
            num_students = int(num_students_str)
            if num_students < 1:
                return jsonify({"error": "Number of students must be at least 1"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Number of students must be a valid number"}), 400

    # Get ticket
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    # Update ticket
    ticket.status = "resolved"
    if num_students is not None:
        ticket.num_students = num_students
    ticket.resolve_reason = resolve_reason
    db.session.commit()
    
    # Broadcast update
    broadcast_ticket_update(ticket.id)

    return jsonify({"message": "Ticket resolved successfully"}), 200
