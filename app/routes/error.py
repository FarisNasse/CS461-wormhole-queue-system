# app/routes/error.py
from flask import Blueprint, render_template

from app import db

error_bp = Blueprint("error", __name__)


@error_bp.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@error_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), 500
