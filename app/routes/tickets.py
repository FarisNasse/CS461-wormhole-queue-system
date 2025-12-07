# /app/routes/tickets.py
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.forms import CreateTicketForm
from app.models import Ticket

# Blueprint 1: Frontend (HTML Pages) - No Prefix
tickets_html_bp = Blueprint("tickets_html", __name__)


@tickets_html_bp.route("/createticket", methods=["GET", "POST"])
def createticket():
    form = CreateTicketForm()
    if form.validate_on_submit():
        try:
            ticket = Ticket(
                student_name=form.name.data,
                physics_course=form.phClass.data,
                table=form.table.data,
                status="Open"
            )
            db.session.add(ticket)
            db.session.commit()
            flash("Help request submitted successfully!")
            return redirect(url_for("tickets_html.livequeue"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("An error occurred while saving your request. Please try again.")
            
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
    student_name = data.get("student_name")
    physics_course = data.get("class_name")
    table = data.get("table_number")

    # VALIDATION FIX: Check for missing fields AND excessive length
    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400
    
    if len(student_name) > 100 or len(physics_course) > 50 or len(str(table)) > 50:
        return jsonify({"error": "Input exceeds maximum character length"}), 400

    try:
        new_ticket = Ticket(
            student_name=student_name,
            table=str(table),
            physics_course=physics_course,
            status="Open",
        )
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify(new_ticket.to_dict()), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@tickets_api_bp.route("/opentickets", methods=["GET"])
def get_open_tickets():
    tickets = Ticket.query.filter_by(status="Open").all()
    return jsonify([t.to_dict() for t in tickets])
