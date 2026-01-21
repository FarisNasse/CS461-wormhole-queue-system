# /app/routes/tickets.py
from flask import Blueprint, jsonify, request, session
from app import db
from app.models import Ticket
from app.routes.queue_events import broadcast_ticket_update

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api')

# GET: API route to get all tickets
@tickets_bp.route('/tickets', methods=['GET'])
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([t.to_dict() for t in tickets])

# POST: API route to create a new ticket
@tickets_bp.route('/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json()
    student_name = data.get("student_name")
    physics_course = data.get("class_name")
    table = data.get("table_number")
    location = data.get("location")

    # Validate required fields
    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400

    # Create the new ticket
    new_ticket = Ticket(
        student_name = student_name,
        table = table,
        physics_course = physics_course,
        status = "live"
    )

    # Add and commit the new ticket to the database
    db.session.add(new_ticket)
    db.session.commit()

    # Broadcast the new ticket to all connected queue clients
    broadcast_ticket_update(new_ticket.id)

    return jsonify(new_ticket.to_dict()), 201

# GET: API route to get all open tickets
@tickets_bp.route('/opentickets', methods=['GET'])
def get_open_tickets():
    tickets = Ticket.query.filter_by(status="live").all()
    return jsonify([t.to_dict() for t in tickets])

# GET: API route to get next open ticket in line
@tickets_bp.route('/nextticket', methods=['GET'])
def get_next_ticket():
    ticket = Ticket.query.filter_by(status="live").order_by(Ticket.created_at).first()
    if ticket:
        current_user = session.get('user_id')
        ticket.assign_to(current_user)
        return jsonify(ticket.to_dict()), 200
    else:
        return jsonify({"message": "No open tickets"}), 404