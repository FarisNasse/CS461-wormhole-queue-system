# app/routes/error.py
from flask import Blueprint, current_app, jsonify, render_template, request, url_for

from app import db

error_bp = Blueprint("error", __name__)


def _debug_enabled():
    return bool(current_app.debug or current_app.config.get("DEBUG", False))


def _prefers_json_response():
    if request.path.startswith("/api/"):
        return True

    accept = request.accept_mimetypes
    return (
        accept.best == "application/json"
        and accept["application/json"] >= accept["text/html"]
    )


def _json_error(message, status_code):
    return jsonify({"error": message}), status_code


@error_bp.app_errorhandler(401)
def unauthorized_error(error):
    message = "Authentication required"

    if _prefers_json_response():
        return _json_error(message, 401)

    return (
        render_template(
            "401.html",
            error_code=401,
            message="Please sign in to continue.",
            home_url=url_for("views.index"),
            login_url=url_for("views.assistant_login"),
            debug=_debug_enabled(),
        ),
        401,
    )


@error_bp.app_errorhandler(403)
def forbidden_error(error):
    message = "Permission denied"

    if _prefers_json_response():
        return _json_error(message, 403)

    return (
        render_template(
            "403.html",
            error_code=403,
            message="You do not have permission to access this page.",
            home_url=url_for("views.index"),
            debug=_debug_enabled(),
        ),
        403,
    )


@error_bp.app_errorhandler(404)
def not_found_error(error):
    debug = _debug_enabled()

    if _prefers_json_response():
        return _json_error("Not found", 404)

    return (
        render_template(
            "404.html",
            error_code=404,
            message="Page not found",
            home_url=url_for("views.index"),
            debug=debug,
        ),
        404,
    )


@error_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    debug = _debug_enabled()

    if _prefers_json_response():
        return _json_error("Unexpected server error", 500)

    tb = None
    if debug:
        import traceback

        tb = traceback.format_exc()

    return (
        render_template(
            "500.html",
            error_code=500,
            message="Internal server error",
            home_url=url_for("views.index"),
            debug=debug,
            traceback=tb,
        ),
        500,
    )
