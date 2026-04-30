FLASK_APP=run.py

# ── Local development only ──────────────────────────────────────────────────
# These values are safe for localhost. Production overrides them via real
# environment variables (which python-dotenv will NOT override).
FORCE_HTTPS=0
ENABLE_HSTS=0
SESSION_COOKIE_SECURE=0
PREFERRED_URL_SCHEME=http
