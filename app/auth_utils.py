"""
auth_utils.py
-----------------
Centralized authorization decorators for the Wormhole Queue System.

This module provides two reusable Flask decorators:
    - @login_required  → ensures that the user is authenticated
    - @admin_required  → ensures that the user is both authenticated and an admin

The decorators return JSON errors for API/AJAX-style requests and use Flask's
HTTP error handlers for normal browser page requests. That keeps API responses
machine-readable while allowing HTML routes to render friendly 401/403 pages.
"""

from functools import wraps

from flask import abort, jsonify, request, session

from app.models import User


def _prefers_json_error() -> bool:
    """Return True when an auth failure should be JSON instead of an HTML page."""
    if request.path.startswith("/api/"):
        return True

    accept = request.accept_mimetypes
    if not accept or not accept.best or accept.best == "*/*":
        # Flask's test client and some non-browser clients often send no
        # specific Accept preference (including */*). Preserve the previous
        # JSON behavior for those callers.
        return True

    return (
        accept.best == "application/json"
        and accept["application/json"] >= accept["text/html"]
    )


def _auth_error(message: str, status_code: int):
    if _prefers_json_error():
        return jsonify({"error": message}), status_code

    abort(status_code)


def login_required(f):
    """Ensure the user is authenticated before accessing the route."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return _auth_error("Authentication required", 401)

        user = User.query.get(session.get("user_id"))
        if user is None or not user.is_active:
            session.clear()
            return _auth_error("Authentication required", 401)

        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    """Ensure the user is authenticated and has administrator privileges."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return _auth_error("Authentication required", 401)

        user = User.query.get(session.get("user_id"))
        if user is None or not user.is_active:
            session.clear()
            return _auth_error("Authentication required", 401)

        if not session.get("is_admin", False):
            return _auth_error("Admin access required", 403)

        return f(*args, **kwargs)

    return wrapper
