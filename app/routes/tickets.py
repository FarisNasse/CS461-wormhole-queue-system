# /app/routes/tickets.py
from flask import Blueprint, jsonify, request
from app import db
from app.models import Ticket

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api')

# Routing for creating help request
@tickets_bp.route("/createticket", endpoint = "createticket")
def createticket():
    return render_template("createticket.html")

#Routing for live queue
@tickets_bp.route("/livequeue", endpoint = "livequeue")
def livequeue():
    return render_template("livequeue.html")

# GET: list all tickets
@tickets_bp.route('/tickets', methods=['GET'])
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([t.to_dict() for t in tickets])

# POST: create a new ticket
@tickets_bp.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json()

    student_name = data.get("student_name")
    physics_course = data.get("class_name")
    table = data.get("table_number")
    location = data.get("location")

    # Validate required fields
    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400

    # Create ticket
    new_ticket = Ticket(
        student_name = student_name,
        table = table,
        physics_course = physics_course,
        status = "Open"
    )

    db.session.add(new_ticket)
    db.session.commit()

    return jsonify(new_ticket.to_dict()), 201
