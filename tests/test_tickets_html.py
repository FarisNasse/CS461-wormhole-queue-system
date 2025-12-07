from app.models import Ticket


def test_html_ticket_creation_success(test_client, test_app):
    """
    Integration Test: Submit the HTML form and verify redirect + DB creation.
    """
    # 1. Simulate Form Data (matching Flask-WTF expectations)
    form_data = {"name": "Jane Doe", "phClass": "PH 212", "table": "Table 5"}

    # 2. POST request (follow_redirects=True to check the final page load if needed)
    response = test_client.post("/createticket", data=form_data, follow_redirects=False)

    # 3. Assert Redirect (302 Found) to livequeue
    assert response.status_code == 302
    assert "/livequeue" in response.headers["Location"]

    # 4. Verify DB side effect
    with test_app.app_context():
        ticket = Ticket.query.filter_by(student_name="Jane Doe").first()
        assert ticket is not None
        assert ticket.table == "Table 5"
        assert ticket.status == "Open"


def test_html_ticket_creation_missing_data(test_client):
    """
    Validation Test: Ensure submitting an empty form re-renders the page with errors.
    """
    # Missing 'table' and 'phClass'
    form_data = {"name": "Incomplete User"}

    response = test_client.post("/createticket", data=form_data)

    # Should NOT redirect (200 OK means it re-rendered the template)
    assert response.status_code == 200
    # Check for Flask-WTF error message in the HTML (implicitly)
    # Note: You can check for specific error strings if your template renders them.
    # For now, just ensuring it didn't redirect is a good baseline.
