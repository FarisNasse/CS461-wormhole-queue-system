# app/routes/queue_events.py
"""
SocketIO events for real-time queue updates.
Handles broadcasting ticket updates to connected clients.
"""

from flask_socketio import emit
from app import socketio, db
from app.models import Ticket


@socketio.on('connect', namespace='/queue')
def handle_queue_connect():
    """Handle client connection to queue namespace."""
    print('Client connected to /queue')


@socketio.on('disconnect', namespace='/queue')
def handle_queue_disconnect():
    """Handle client disconnect from queue namespace."""
    print('Client disconnected from /queue')


def broadcast_ticket_update(ticket_id):
    """
    Broadcast a ticket update to all connected clients on the queue namespace.
    Called when a new ticket is created or updated.
    """
    t = Ticket.query.get(ticket_id)
    if t:
        ticket_data = {
            'id': t.id,
            'student_name': t.student_name,
            'table': t.table,
            'physics_course': t.physics_course,
            'created_at': t.created_at.isoformat() if t.created_at else None,
            'status': t.status,
        }
        socketio.emit('new_ticket', ticket_data, namespace='/queue', broadcast=True)


def broadcast_queue_refresh():
    """
    Broadcast a refresh signal to all connected clients.
    Triggers the client to refetch the queue.
    """
    socketio.emit('queue_refresh', {}, namespace='/queue', broadcast=True)
