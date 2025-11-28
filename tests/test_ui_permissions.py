import json
from app.models import Ticket, db

def test_create_ticket(test_client, test_app):
    payload = {
        "student_name": "Faris",
        "table": "A1",
        "physics_course": "PH211"
    }

    resp = test_client.post(
        "/api/tickets",
        json=payload
    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["student_name"] == "Faris"
    assert data["table"] == "A1"


def test_get_tickets(test_client, test_app):
    with test_app.app_context():
        t = Ticket(student_name="A", table="Z2", physics_course="PH212")
        db.session.add(t)
        db.session.commit()

    resp = test_client.get("/api/tickets")
    assert resp.status_code == 200

    data = resp.get_json()
    assert any(ticket["student_name"] == "A" for ticket in data)
