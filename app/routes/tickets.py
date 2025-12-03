# /app/routes/tickets.py
from flask import Blueprint, jsonify, render_template, request

from app import db
from app.forms import CreateTicketForm
from app.models import Ticket

# Blueprint 1: Frontend (HTML Pages) - No Prefix
tickets_html_bp = Blueprint("tickets_html", __name__)


@tickets_html_bp.route("/createticket")
def createticket():
    form = CreateTicketForm()  # Instantiate the form
    return render_template("createticket.html", form=form)


@tickets_html_bp.route("/livequeue")
def livequeue():
    return render_template("livequeue.html")


# Blueprint 2: Backend (JSON API) - Prefix: /api
tickets_api_bp = Blueprint("tickets_api", __name__, url_prefix="/api")


@tickets_api_bp.route("/tickets", methods=["GET"])
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([t.to_dict() for t in tickets])


@tickets_api_bp.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json()
    # Note: 'location' is accepted but not stored (future feature)
    student_name = data.get("student_name")
    physics_course = data.get("class_name")
    table = data.get("table_number")

    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400

    new_ticket = Ticket(
        student_name=student_name,
        table=table,
        physics_course=physics_course,
        status="Open",
    )

    db.session.add(new_ticket)
    db.session.commit()
    return jsonify(new_ticket.to_dict()), 201


@tickets_api_bp.route("/opentickets", methods=["GET"])
def get_open_tickets():
    tickets = Ticket.query.filter_by(status="Open").all()
    return jsonify([t.to_dict() for t in tickets])
