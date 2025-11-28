# app/auth_decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(func):
    """
    Security Decorator:
    1. Checks if the user is logged in (via is_authenticated).
    2. Checks if the user has admin privileges (via is_admin).
    3. If either fails, returns a 403 Forbidden error.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        # Ensure user is logged in first
        if not current_user.is_authenticated:
            # You could redirect to login here, but 403/401 is strictly more correct for "Unauthorized"
            return abort(401) 

        # Ensure user is an admin
        if not current_user.is_admin:
            return abort(403) # Forbidden
            
        return func(*args, **kwargs)
    return decorated_view