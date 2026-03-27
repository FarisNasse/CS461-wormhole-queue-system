"""
Pytest fixtures for Playwright browser tests against a live Flask server.

Usage:
    pip install playwright pytest-playwright
    playwright install chromium
    pytest tests/browser/ -v
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
)

import pytest  # noqa: E402

pytest.importorskip(
    "playwright.sync_api",
    reason="Playwright is not installed; browser tests are optional.",
)

from playwright.sync_api import (  # noqa: E402
    Browser,
    BrowserContext,
    Page,
    sync_playwright,
)

from app import create_app, db  # noqa: E402
from app.models import User  # noqa: E402

ASSISTANT_USERNAME = os.getenv("LOCUST_ASSISTANT_USERNAME", "browser_test_assistant")
ASSISTANT_PASSWORD = os.getenv("LOCUST_ASSISTANT_PASSWORD", "browser_test_password")

THRESHOLDS = {
    "lcp_ms": 2500,
    "fcp_ms": 1800,
    "ttfb_ms": 800,
    "dom_content_loaded_ms": 1500,
    "load_event_ms": 3000,
    "cls": 0.1,
}


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(s.getsockname()[1])


def _run_server(flask_app, port: int) -> None:
    flask_app.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


@pytest.fixture(scope="session")
def browser_test_port() -> int:
    return _find_free_port()


@pytest.fixture(scope="session")
def base_url(browser_test_port: int) -> str:
    return f"http://127.0.0.1:{browser_test_port}"


@pytest.fixture(scope="session")
def browser_database_uri(tmp_path_factory) -> str:
    """
    Use a file-backed SQLite DB so the Flask server thread and the test
    thread see the same seeded users and tickets.
    """
    db_dir = tmp_path_factory.mktemp("browser-db")
    db_path = Path(db_dir) / "browser-tests.sqlite"
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def live_app(browser_database_uri):
    flask_app = create_app(testing=True, database_uri=browser_database_uri)
    flask_app.config.update(
        {
            "WTF_CSRF_ENABLED": False,
            "SERVER_NAME": None,
        }
    )

    with flask_app.app_context():
        db.create_all()

        if not db.session.query(User).filter_by(username=ASSISTANT_USERNAME).first():
            user = User(
                username=ASSISTANT_USERNAME,
                email=f"{ASSISTANT_USERNAME}@wormhole.test",
                name="Browser Test Assistant",
                is_admin=False,
                is_active=True,
            )
            user.set_password(ASSISTANT_PASSWORD)
            db.session.add(user)
            db.session.commit()

        yield flask_app

        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session")
def server(live_app, browser_test_port, base_url):
    thread = threading.Thread(
        target=_run_server,
        args=(live_app, browser_test_port),
        daemon=True,
    )
    thread.start()

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.create_connection(
                ("127.0.0.1", browser_test_port), timeout=0.5
            ):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError(
            f"Test server did not start on port {browser_test_port} in time"
        )

    yield base_url


@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--enable-precise-memory-info",
            ],
        )
        yield browser
        browser.close()


@pytest.fixture()
def context(browser_instance: Browser) -> BrowserContext:
    ctx = browser_instance.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
    )
    yield ctx
    ctx.close()


@pytest.fixture()
def page(context: BrowserContext, server) -> Page:
    p = context.new_page()
    p.set_default_timeout(10_000)
    yield p
    p.close()


@pytest.fixture()
def authenticated_page(context: BrowserContext, server) -> Page:
    p = context.new_page()
    p.set_default_timeout(10_000)

    p.goto(f"{server}/assistant-login")
    p.fill("input[name='username']", ASSISTANT_USERNAME)
    p.fill("input[name='password']", ASSISTANT_PASSWORD)

    with p.expect_navigation(wait_until="load"):
        p.locator("form").first.evaluate("(form) => form.requestSubmit()")

    yield p
    p.close()


def get_nav_timing(page: Page) -> dict:
    raw = page.evaluate(
        """() => {
        const t = performance.getEntriesByType('navigation')[0];
        return {
            ttfb:               t.responseStart   - t.requestStart,
            fcp:                (() => {
                const e = performance.getEntriesByName('first-contentful-paint')[0];
                return e ? e.startTime : null;
            })(),
            dom_content_loaded: t.domContentLoadedEventEnd - t.startTime,
            load_event:         t.loadEventEnd            - t.startTime,
            dom_interactive:    t.domInteractive           - t.startTime,
            transfer_size:      t.transferSize,
            encoded_body_size:  t.encodedBodySize,
        };
    }"""
    )
    return raw


def get_cls(page: Page) -> float:
    return page.evaluate(
        """() => {
        return new Promise((resolve) => {
            let cls = 0;
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) cls += entry.value;
                }
            });
            try {
                observer.observe({ type: 'layout-shift', buffered: true });
            } catch (_) {}
            setTimeout(() => { observer.disconnect(); resolve(cls); }, 300);
        });
    }"""
    )
