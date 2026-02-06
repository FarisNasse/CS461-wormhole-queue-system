# /app/routes/tickets.py
from flask import abort, Blueprint, flash, jsonify, redirect, request, render_template, session, url_for

from app import db, socketIO
from app.forms import ResolveTicketForm
from app.models import Ticket, User
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
    table = data.get("table_number")

    # Validate required fields
    if not student_name or not physics_course or table is None:
        return jsonify({"error": "Missing required fields"}), 400

    # Create the new ticket
    new_ticket = Ticket(
        student_name=student_name,
        table=table,
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
    tickets = Ticket.query.filter(Ticket.status.in_(["live", 'in_progress'])).all()
    return jsonify([t.to_dict() for t in tickets])


# API route to handle ticket resolution form submission
@tickets_bp.route("/resolveticket/<int:ticket_id>", methods=["POST"])
def resolve_ticket(ticket_id):
    user = User.query.get(session["user_id"])
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
            return redirect(url_for("views.userpage", username=user.username))
        else:
            flash("Ticket not found", "error")
            return redirect(url_for("views.userpage", username=user.username))
    else:
        flash("There was a problem resolving the ticket.", "error")
        return redirect(url_for('views.currentticket', tktid=ticket_id))
    
# API route to handle return to queue form submission
@tickets_bp.route('/returntoqueue/<int:ticket_id>', methods=['POST'])
def return_to_queue(ticket_id):
    user = User.query.get(session['user_id'])
    ticket = Ticket.query.get(ticket_id)
    if ticket:
        ticket.return_to_queue()
        broadcast_ticket_update(ticket.id)
        flash("Ticket returned to queue successfully", "success")
        return redirect(url_for('views.userpage', username = user.username))
    else:
        flash("Ticket not found", "error")
        return redirect(url_for('views.currentticket', tktid=ticket_id))
    
@tickets_bp.route('/getnextticket/<username>')
def getnextticket(username):
    # Assign the next available live ticket to the given user and redirect
    u = User.query.filter_by(username=username).first()
    if not u:
        abort(404)

    # find the oldest live unassigned ticket
    t = Ticket.query.filter_by(status='live', wa_id=None).order_by(Ticket.created_at).first()
    if not t:
        # no tickets available; redirect back to user page
        flash('No available tickets to claim.', 'info')
        return redirect(url_for('views.userpage', username=username))

    t.assign_to(u)
    broadcast_ticket_update(t.id)
    return redirect(url_for('views.currentticket', tktid=t.id))
