# /app/routes/tickets.py
from flask import Blueprint, jsonify, redirect, request, render_template, flash, session, url_for
from app import db, socketio
from app.models import Ticket, User
from app.routes.queue_events import broadcast_ticket_update
from app.forms import ResolveTicketForm
from app.routes.views import currentticket

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

# API route to handle ticket resolution form submission
@tickets_bp.route('/resolveticket/<int:ticket_id>', methods=['POST'])
def resolve_ticket(ticket_id):
    user = User.query.get(session['user_id'])
    form = ResolveTicketForm()
    if form.validate_on_submit():
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            ticket.status = "resolved"
            ticket.num_students = form.numStds.data
            ticket.resolve_reason = form.resolveReason.data
            db.session.commit()
            broadcast_ticket_update(ticket.id)
            flash("Ticket resolved successfully", "success")
            return redirect(url_for('views.userpage', username = user.username))
        else:
            flash("Ticket not found", "error")
            return redirect(url_for('views.userpage', username = user.username))
    else:
        flash("There was a problem resolving the ticket.", "error")
        return redirect(url_for('views.currentticket', tktid=ticket_id))