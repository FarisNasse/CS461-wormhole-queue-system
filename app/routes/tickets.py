# app/routes/tickets.py
from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models import Ticket

tickets_bp = Blueprint('tickets', __name__)

# -------------------------------
# HTML Page Routes
# -------------------------------

@tickets_bp.route('/live-queue')
def live_queue():
    return render_template('livequeue.html')

@tickets_bp.route('/create-ticket')
def create_ticket_page():
    return render_template('createticket.html')

@tickets_bp.route('/archive')
def archive():
    return render_template('archive.html')

@tickets_bp.route('/manage-queue')
def manage_queue():
    return render_template('queue.html')


# -------------------------------
# API Routes
# -------------------------------

@tickets_bp.route('/api/tickets', methods=['GET'])
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([t.to_dict() for t in tickets]), 200


@tickets_bp.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json() or {}

    required = ["student_name", "table", "physics_course"]
    if not all(k in data and data[k] for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    ticket = Ticket(
        student_name=data["student_name"],
        table=data["table"],
        physics_course=data["physics_course"]
    )

    db.session.add(ticket)
    db.session.commit()

    return jsonify(ticket.to_dict()), 201
