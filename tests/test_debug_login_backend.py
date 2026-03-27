from app import create_app, db
from app.models import User


def test_debug_backend_login():
    app = create_app(testing=True, database_uri="sqlite:///debug-login.sqlite")

    with app.app_context():
        db.drop_all()
        db.create_all()

        user = User(
            username="browser_test_assistant",
            email="browser_test_assistant@wormhole.test",
            name="Browser Test Assistant",
            is_admin=False,
            is_active=True,
        )
        user.set_password("browser_test_password")
        db.session.add(user)
        db.session.commit()

        saved = (
            db.session.query(User).filter_by(username="browser_test_assistant").first()
        )
        print("\n=== USER IN DB ===")
        print(saved.username, saved.email, saved.is_admin, saved.is_active)
        print("PASSWORD OK:", saved.check_password("browser_test_password"))

    client = app.test_client()

    get_resp = client.get("/assistant-login")
    print("\n=== GET /assistant-login ===")
    print(get_resp.status_code)

    post_resp = client.post(
        "/assistant-login",
        data={
            "username": "browser_test_assistant",
            "password": "browser_test_password",
        },
        follow_redirects=False,
    )

    print("\n=== POST /assistant-login ===")
    print("STATUS:", post_resp.status_code)
    print("LOCATION:", post_resp.headers.get("Location"))
    print("BODY:", post_resp.get_data(as_text=True)[:500])

    assert True
