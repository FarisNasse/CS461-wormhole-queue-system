# app/routes/error.py
from flask import Blueprint, request, jsonify, session, render_template, current_app, url_for
from werkzeug.security import check_password_hash
from app.models import User
from app import db

error_bp = Blueprint('error', __name__)

@error_bp.errorhandler(404)
def not_found_error(error):
    debug = bool(current_app.debug or current_app.config.get('DEBUG', False))
    return (
        render_template(
            '404.html',
            error_code=404,
            message=str(error),
            home_url=url_for('index'),
            debug=debug,
        ),
        404,
    )

@error_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    debug = bool(current_app.debug or current_app.config.get('DEBUG', False))
    tb = None
    if debug:
        import traceback
        tb = traceback.format_exc()

    return (
        render_template(
            '500.html',
            error_code=500,
            message=str(error),
            home_url=url_for('index'),
            debug=debug,
            traceback=tb,
        ),
        500,
    )