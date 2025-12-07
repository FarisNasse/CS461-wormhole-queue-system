# tests/test_tickets_api.py
from app import db
from app.models import Ticket


def test_create_ticket_success(test_client, test_app):
    """
    Happy Path: Ensure a valid POST request creates a ticket in the DB.
    """
    payload = {
        "student_name": "Isaac Newton",
        "class_name": "PH 211",
        "table_number": 42,  # Sending int is fine, but DB stores as String
        "location": "Library",
    }

    response = test_client.post("/api/tickets", json=payload)

    # 1. Check API Response
    assert response.status_code == 201
    data = response.get_json()
    assert data["student_name"] == "Isaac Newton"
    assert data["status"] == "Open"

    # 2. Check Database Integrity
    with test_app.app_context():
        ticket = Ticket.query.filter_by(student_name="Isaac Newton").first()
        assert ticket is not None
        # FIXED: Compare against string because DB column is String(50)
        assert ticket.table == "42"


def test_create_ticket_validation_error(test_client):
    """
    Negative Test: Ensure API rejects incomplete data with 400 Bad Request.
    """
    # Missing 'table_number'
    payload = {"student_name": "Bad Data User", "class_name": "PH 211"}

    response = test_client.post("/api/tickets", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_get_tickets_returns_list(test_client, test_app):
    """
    Integration: Ensure GET /api/tickets returns the list of created tickets.
    """
    # Setup: Create a ticket manually in the DB
    with test_app.app_context():
        t1 = Ticket(
            student_name="Alice", physics_course="PH 211", table="1", status="Open"
        )
        t2 = Ticket(
            student_name="Bob", physics_course="PH 212", table="2", status="Closed"
        )
        db.session.add_all([t1, t2])
        db.session.commit()

    # Action: Fetch from API
    response = test_client.get("/api/tickets")

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["student_name"] == "Alice"


def test_get_open_tickets_filter(test_client, test_app):
    """
    Logic Test: Ensure /api/opentickets ONLY returns 'Open' tickets.
    """
    with test_app.app_context():
        t1 = Ticket(
            student_name="Open User", physics_course="PH 211", table="1", status="Open"
        )
        t2 = Ticket(
            student_name="Closed User",
            physics_course="PH 212",
            table="2",
            status="Closed",
        )
        db.session.add_all([t1, t2])
        db.session.commit()

    response = test_client.get("/api/opentickets")
    data = response.get_json()

    assert len(data) == 1
    assert data[0]["student_name"] == "Open User"


def test_create_ticket_missing_table(test_client):
    """
    Negative Test: API should reject requests missing the 'table_number' field.
    """
    payload = {
        "student_name": "No Table User",
        "class_name": "PH 211",
        # 'table_number' is missing
    }

    response = test_client.post("/api/tickets", json=payload)

    # Expecting 400 Bad Request
    assert response.status_code == 400
    assert "error" in response.get_json()
