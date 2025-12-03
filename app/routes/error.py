# app/routes/error.py
from flask import Blueprint, render_template

from app import db

error_bp = Blueprint("error", __name__)


@error_bp.app_errorhandler(404)  # <-- Changed from errorhandler to app_errorhandler
def not_found_error(error):
    return render_template("404.html"), 404


@error_bp.app_errorhandler(500)  # <-- Changed here too
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), 500
