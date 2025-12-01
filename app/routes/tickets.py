# app/routes/tickets.py
from flask import Blueprint, jsonify, render_template, request

from app import db
from app.models import Ticket


tickets_bp = Blueprint("tickets", __name__)

# Route to render the create ticket page
@tickets_bp.route("/createticket", endpoint="createticket")
def createticket():
    return render_template("createticket.html")


@tickets_bp.route("/live-queue")
def live_queue():
    return render_template("livequeue.html")


@tickets_bp.route("/create-ticket")
def create_ticket_page():
    return render_template("createticket.html")


@tickets_bp.route("/archive")
def archive():
    return render_template("archive.html")


@tickets_bp.route("/manage-queue")
def manage_queue():
    return render_template("queue.html")


# -------------------------------
# API Routes
# -------------------------------


@tickets_bp.route("/api/tickets", methods=["GET"])
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([t.to_dict() for t in tickets])


@tickets_bp.route("/api/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json()
    student_name = data.get("student_name")
    physics_course = data.get("class_name")
    table = data.get("table_number")
    location = data.get("location")

    # Validate required fields
    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400

    ticket = Ticket(
        student_name=data["student_name"],
        table=data["table"],
        physics_course=data["physics_course"],
    )

    # Add and commit the new ticket to the database
    db.session.add(new_ticket)
    db.session.commit()

    return jsonify(new_ticket.to_dict()), 201
