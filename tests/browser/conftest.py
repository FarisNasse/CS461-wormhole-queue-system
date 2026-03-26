# tests/browser/conftest.py
"""
Pytest fixtures for Playwright browser tests against a live Flask server.

Usage:
    pip install playwright pytest-playwright
    playwright install chromium
    pytest tests/browser/ -v
"""
from __future__ import annotations

import os
import sys
import threading
import time

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

# Allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import create_app, db  # noqa: E402
from app.models import User  # noqa: E402

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

TEST_PORT = int(os.getenv("BROWSER_TEST_PORT", "5555"))
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
ASSISTANT_USERNAME = os.getenv("LOCUST_ASSISTANT_USERNAME", "browser_test_assistant")
ASSISTANT_PASSWORD = os.getenv("LOCUST_ASSISTANT_PASSWORD", "browser_test_password")

# Core Web Vitals thresholds (milliseconds unless noted)
THRESHOLDS = {
    "lcp_ms": 2500,          # Largest Contentful Paint  ≤ 2.5 s  (Good)
    "fcp_ms": 1800,          # First Contentful Paint    ≤ 1.8 s  (Good)
    "ttfb_ms": 800,          # Time to First Byte        ≤ 800 ms (Good)
    "dom_content_loaded_ms": 1500,
    "load_event_ms": 3000,
    "cls": 0.1,              # Cumulative Layout Shift   ≤ 0.1   (Good)
}


# ──────────────────────────────────────────────────────────────────────────────
# Live Flask server
# ──────────────────────────────────────────────────────────────────────────────

def _run_server(flask_app, port: int) -> None:
    """Target for the server thread. Werkzeug dev server (single-threaded ok for tests)."""
    flask_app.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


@pytest.fixture(scope="session")
def live_app():
    """Create a Flask app in testing mode and seed a browser-test assistant account."""
    flask_app = create_app(testing=True)
    flask_app.config.update(
        {
            "WTF_CSRF_ENABLED": False,
            "SERVER_NAME": None,  # don't restrict to a hostname
        }
    )

    with flask_app.app_context():
        db.create_all()

        # Seed the assistant user so login tests work
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
def server(live_app):
    """Start the Flask dev server in a daemon thread for the whole test session."""
    thread = threading.Thread(
        target=_run_server, args=(live_app, TEST_PORT), daemon=True
    )
    thread.start()

    # Wait until the server is accepting connections
    import socket

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", TEST_PORT), timeout=0.5):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError(f"Test server did not start on port {TEST_PORT} in time")

    yield BASE_URL


# ──────────────────────────────────────────────────────────────────────────────
# Playwright browser / context / page fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_instance():
    """One Chromium browser for the whole session."""
    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                # Enables CDP Performance domain used in perf tests
                "--enable-precise-memory-info",
            ],
        )
        yield browser
        browser.close()


@pytest.fixture()
def context(browser_instance: Browser) -> BrowserContext:
    """Fresh browser context (= isolated session) for every test."""
    ctx = browser_instance.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
    )
    yield ctx
    ctx.close()


@pytest.fixture()
def page(context: BrowserContext, server) -> Page:  # noqa: F811
    """A blank page connected to the live server."""
    p = context.new_page()
    p.set_default_timeout(10_000)
    yield p
    p.close()


@pytest.fixture()
def authenticated_page(context: BrowserContext, server) -> Page:
    """A page that is already logged in as the test assistant."""
    p = context.new_page()
    p.set_default_timeout(10_000)

    p.goto(f"{server}/login")
    p.fill("input[name='username']", ASSISTANT_USERNAME)
    p.fill("input[name='password']", ASSISTANT_PASSWORD)
    p.click("button[type='submit']")
    p.wait_for_load_state("networkidle")

    yield p
    p.close()


# ──────────────────────────────────────────────────────────────────────────────
# Helper: collect Navigation Timing metrics via CDP
# ──────────────────────────────────────────────────────────────────────────────

def get_nav_timing(page: Page) -> dict:
    """
    Return a dict of timing values (all in ms) from the Navigation Timing API.
    Call this *after* page.goto() and page.wait_for_load_state('load').
    """
    raw = page.evaluate("""() => {
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
    }""")
    return raw


def get_cls(page: Page) -> float:
    """
    Approximate CLS using the Layout Instability API.
    Returns the cumulative layout shift score (0.0 if not supported).
    """
    return page.evaluate("""() => {
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
            // Give it 300 ms to collect buffered entries
            setTimeout(() => { observer.disconnect(); resolve(cls); }, 300);
        });
    }""")
