# /app/routes/tickets.py
from flask import Blueprint, jsonify, request
from app import db
from app.models import Ticket

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api')

# GET: list all tickets
@tickets_bp.route('/tickets', methods=['GET'])
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([t.to_dict() for t in tickets])

# POST: create a new ticket
@tickets_bp.route('/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json()
    if not data or not all(k in data for k in ['student_name', 'table_number', 'class_name']):
        return jsonify({'error': 'Missing required fields'}), 400

    new_ticket = Ticket(
        student_name=data['student_name'],
        table_number=data['table_number'],
        class_name=data['class_name'],
        status="Open"
    )
    db.session.add(new_ticket)
    db.session.commit()
    return jsonify(new_ticket.to_dict()), 201




