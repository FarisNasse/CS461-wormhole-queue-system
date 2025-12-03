# /app/routes/tickets.py
from flask import Blueprint, jsonify, render_template, request

from app import db
from app.models import Ticket

tickets_bp = Blueprint("tickets", __name__, url_prefix="/api")


# Route to render the create ticket page
@tickets_bp.route("/createticket", endpoint="createticket")
def createticket():
    return render_template("createticket.html")


# Route to render the live queue page
@tickets_bp.route("/livequeue", endpoint="livequeue")
def livequeue():
    return render_template("livequeue.html")


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
    location = data.get("location")

    # Validate required fields
    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400

    # Create the new ticket
    new_ticket = Ticket(
        student_name=student_name,
        table=table,
        physics_course=physics_course,
        status="Open",
    )

    # Add and commit the new ticket to the database
    db.session.add(new_ticket)
    db.session.commit()

    return jsonify(new_ticket.to_dict()), 201


# GET: API route to get all open tickets
@tickets_bp.route("/opentickets", methods=["GET"])
def get_open_tickets():
    tickets = Ticket.query.filter_by(status="Open").all()
    return jsonify([t.to_dict() for t in tickets])
