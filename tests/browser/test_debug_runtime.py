from __future__ import annotations

import inspect
from pathlib import Path

from app import create_app, db
from app.models import User
from tests.browser.conftest import ASSISTANT_PASSWORD, ASSISTANT_USERNAME


def test_debug_runtime_paths_and_db(live_app):
    print("\n=== IMPORT PATHS ===")
    print("create_app module file:", inspect.getfile(create_app))

    print("\n=== FLASK APP PATHS ===")
    print("root_path:", live_app.root_path)
    print("template_folder:", live_app.template_folder)

    template_folder = live_app.template_folder or "templates"
    base_path = Path(live_app.root_path) / template_folder / "base.html"

    print("\n=== BASE TEMPLATE FILE ===")
    print("base_path:", base_path)
    print("exists:", base_path.exists())

    if base_path.exists():
        text = base_path.read_text(encoding="utf-8")
        print("contains <h1 class='site-title'>:", '<h1 class="site-title">' in text)
        print("contains <p class='site-title'>:", '<p class="site-title">' in text)
        print("--- first 500 chars of base.html ---")
        print(text[:500])

    print("\n=== DB CONFIG ===")
    print("SQLALCHEMY_DATABASE_URI:", live_app.config.get("SQLALCHEMY_DATABASE_URI"))

    with live_app.app_context():
        users = db.session.query(User).all()
        print("\n=== USERS IN LIVE_APP DB ===")
        print([(u.username, u.email, u.is_active, u.is_admin) for u in users])

        user = db.session.query(User).filter_by(username=ASSISTANT_USERNAME).first()
        print("\n=== SEEDED BROWSER USER ===")
        print("username searched:", ASSISTANT_USERNAME)
        print("found:", bool(user))
        if user:
            print("email:", user.email)
            print("is_active:", user.is_active)
            print("is_admin:", user.is_admin)
            print("password ok:", user.check_password(ASSISTANT_PASSWORD))

    assert True