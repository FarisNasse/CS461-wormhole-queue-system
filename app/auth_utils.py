"""
auth_utils.py
-----------------
Centralized authorization decorators for the Wormhole Queue System.

This module provides two reusable Flask decorators:
    - @login_required  → ensures that the user is authenticated
    - @admin_required  → ensures that the user is both authenticated and an admin

These decorators reduce repeated logic across route handlers, enforce
consistent error responses, and support security-related requirements:

    • REQ-021: Login/Logout (system must restrict privileged actions)
    • REQ-003: Add Wormhole Account (admin-only functionality)
    • REQ-005: Reset Ticket Counter (admin-only functionality)
    • REQ-010: Secure Transport Protocol (part of access control surface)
    • REQ-008: Intuitive Design (centralized, readable access control)

They should be applied to any route that requires authentication, such as:
    - Ticket CRUD for WAs/Admins
    - Admin utilities
    - User management and system configuration pages
"""

from functools import wraps

from flask import jsonify, session


def login_required(f):
    """
    Decorator: Ensure the user is authenticated before accessing the route.

    Behavior:
        - If 'user_id' does not exist in the session cookie, the user is not logged in.
        - Returns HTTP 401 Unauthorized with a JSON error message.
        - If authenticated, execution continues to the wrapped route handler.

    Returns:
        The decorated route function with authentication checks applied.

    Example:
        @app.route('/tickets')
        @login_required
        def view_tickets():
            ...

    Why important:
        All WA/Admin routes must restrict access to authenticated users to
        protect student ticket data (FERPA-related) and satisfy REQ-021.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401

        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    """
    Decorator: Ensure the user is both authenticated AND has administrator privileges.

    Behavior:
        - If 'user_id' not in session → user is not logged in → return HTTP 401.
        - If 'is_admin' flag in session is False → return HTTP 403 Forbidden.
        - If both conditions pass, route executes normally.

    Returns:
        The decorated route function with admin-level access control applied.

    Example:
        @app.route('/admin/reset-counter', methods=['POST'])
        @admin_required
        def reset_ticket_counter():
            ...

    Why important:
        Protects admin-only features such as:
            • Resetting ticket counters (REQ-005)
            • Creating WA accounts (REQ-003)
            • Viewing admin dashboards and logs (REQ-022/025)

        This prevents privilege escalation and ensures consistent security behavior
        across all admin features.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        # Step 1: Must be logged in
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401

        # Step 2: Must have admin privileges
        if not session.get("is_admin", False):
            return jsonify({"error": "Admin access required"}), 403

        return f(*args, **kwargs)

    return wrapper
