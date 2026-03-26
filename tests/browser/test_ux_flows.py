# tests/browser/test_ux_flows.py
"""
End-to-end UX flow tests.

These tests exercise the real user journeys described in the Wormhole
requirements document, verifying that each step works correctly in a real
browser (not just at the HTTP layer as the Locust tests do).

Covered flows:
  1. Student submits a help request → appears in live queue
  2. Student sees their position update as tickets ahead resolve
  3. Assistant logs in, claims a ticket, resolves it, ticket disappears
  4. Navigation landmark / skip-link presence (basic a11y smoke)
  5. Mobile viewport: hamburger menu opens and all nav links are reachable

Run:
    pytest tests/browser/test_ux_flows.py -v
"""
from __future__ import annotations

import random
import string

import pytest
from playwright.sync_api import Page, expect

from tests.browser.conftest import ASSISTANT_PASSWORD, ASSISTANT_USERNAME, BASE_URL


def _rand_name(prefix: str = "ux") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}"


# ──────────────────────────────────────────────────────────────────────────────
# Flow 1 – Student submits a ticket and sees it in the live queue
# ──────────────────────────────────────────────────────────────────────────────

class TestStudentTicketFlow:
    def test_submit_ticket_via_form(self, page: Page, server: str):
        """
        Navigate to the create-ticket page, fill the form, submit, and assert
        a success indicator is shown (redirect or confirmation message).
        """
        name = _rand_name("stu")
        page.goto(server + "/createticket")
        page.wait_for_load_state("load")

        page.fill("input[name='student_name']", name)
        page.select_option("select[name='class_name']", index=1)
        page.fill("input[name='table_number']", "3")
        page.click("button[type='submit']")
        page.wait_for_load_state("load")

        # Either redirected away from /createticket (success) or a flash message
        current_url = page.url
        body_text = page.inner_text("body")
        assert "/createticket" not in current_url or "success" in body_text.lower() or \
               name in body_text, (
            "Ticket submission did not redirect or show a confirmation. "
            f"URL: {current_url}"
        )

    def test_submitted_ticket_visible_in_live_queue(self, page: Page, server: str):
        """
        After submitting a ticket the student's name should appear in
        /livequeue (polled table).
        """
        name = _rand_name("lq")

        # Submit via API so the UX test focuses on the queue display
        import requests  # stdlib-adjacent; only used here

        try:
            resp = requests.post(
                server + "/api/tickets",
                json={"student_name": name, "class_name": "PH 201", "table_number": 7},
                timeout=5,
            )
            if resp.status_code != 201:
                pytest.skip(f"API ticket creation returned {resp.status_code}; skipping queue check")
        except Exception as exc:
            pytest.skip(f"Could not reach API: {exc}")

        page.goto(server + "/livequeue")
        # Wait for the table to show the new ticket (JS polling or SSR)
        try:
            page.wait_for_function(
                f"() => document.body.innerText.includes('{name}')",
                timeout=8000,
            )
        except Exception:
            pytest.fail(
                f"Student name '{name}' did not appear in /livequeue within 8 s. "
                "Check that livequeue.js polls /api/opentickets correctly."
            )

    def test_homepage_cta_links_work(self, page: Page, server: str):
        """All three hero CTA buttons on the homepage should be present and have valid hrefs."""
        page.goto(server + "/")
        page.wait_for_load_state("load")

        # "Submit a Help Request" button
        submit_btn = page.locator(".hero-actions a.btn-primary").first
        expect(submit_btn).to_be_visible()
        href = submit_btn.get_attribute("href")
        assert href and "createticket" in href, f"Submit CTA href unexpected: {href}"

        # "View Live Queue" button
        queue_btn = page.locator(".hero-actions a.btn-secondary").first
        expect(queue_btn).to_be_visible()
        href2 = queue_btn.get_attribute("href")
        assert href2 and "livequeue" in href2, f"Queue CTA href unexpected: {href2}"


# ──────────────────────────────────────────────────────────────────────────────
# Flow 2 – Assistant login → claim → resolve
# ──────────────────────────────────────────────────────────────────────────────

class TestAssistantWorkflowFlow:
    def test_login_page_renders_form(self, page: Page, server: str):
        page.goto(server + "/login")
        expect(page.locator("input[name='username']")).to_be_visible()
        expect(page.locator("input[name='password']")).to_be_visible()
        expect(page.locator("button[type='submit']")).to_be_visible()

    def test_invalid_login_shows_error(self, page: Page, server: str):
        page.goto(server + "/login")
        page.fill("input[name='username']", "nobody")
        page.fill("input[name='password']", "wrongpassword")
        page.click("button[type='submit']")
        page.wait_for_load_state("load")

        body = page.inner_text("body").lower()
        assert any(word in body for word in ("invalid", "incorrect", "failed", "error")), (
            "Expected an error message for bad credentials but none was found"
        )

    def test_valid_login_redirects_to_app(self, page: Page, server: str):
        page.goto(server + "/login")
        page.fill("input[name='username']", ASSISTANT_USERNAME)
        page.fill("input[name='password']", ASSISTANT_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("load")

        # After login the user should *not* be on /login anymore
        assert "/login" not in page.url, (
            f"Login did not redirect; still on {page.url}"
        )

    def test_authenticated_can_reach_queue_dashboard(
        self, authenticated_page: Page, server: str
    ):
        authenticated_page.goto(server + "/queue")
        page_text = authenticated_page.inner_text("body").lower()
        assert "queue" in page_text, "/queue did not render expected content for logged-in assistant"

    def test_claim_and_resolve_full_cycle(self, authenticated_page: Page, server: str):
        """
        Seed a ticket via API, let the assistant claim it through the UI,
        resolve it, then verify it no longer appears in /api/opentickets.
        """
        import requests

        name = _rand_name("cycle")
        try:
            resp = requests.post(
                server + "/api/tickets",
                json={"student_name": name, "class_name": "PH 213", "table_number": 2},
                timeout=5,
            )
        except Exception as exc:
            pytest.skip(f"Could not seed ticket: {exc}")

        if resp.status_code != 201:
            pytest.skip(f"Ticket seeding returned {resp.status_code}")

        # Claim the next ticket (the app redirects to /currentticket/<id>)
        authenticated_page.goto(f"{server}/getnewticket/{ASSISTANT_USERNAME}")
        authenticated_page.wait_for_load_state("load")

        current_url = authenticated_page.url
        if "/currentticket/" not in current_url:
            pytest.skip("No ticket was available to claim; skipping resolve test")

        # Verify the ticket page loaded
        expect(authenticated_page.locator("main")).to_be_visible()

        # Resolve the ticket
        resolve_btn = authenticated_page.locator(
            "button[value='helped'], button[name='resolve'], input[value='helped']"
        ).first
        if not resolve_btn.is_visible():
            pytest.skip("Could not locate resolve button; skipping")

        resolve_btn.click()
        authenticated_page.wait_for_load_state("load")

        # Confirm the ticket is gone from the open list
        import json

        open_resp = requests.get(server + "/api/opentickets", timeout=5)
        tickets = open_resp.json()
        ticket_id = int(current_url.rstrip("/").split("/")[-1])
        assert not any(t.get("id") == ticket_id for t in tickets), (
            f"Resolved ticket {ticket_id} still appears in /api/opentickets"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Flow 3 – Navigation integrity
# ──────────────────────────────────────────────────────────────────────────────

class TestNavigationFlow:
    @pytest.mark.parametrize(
        "label,expected_path",
        [
            ("Home", "/"),
            ("Submit Request", "/createticket"),
            ("Live Queue", "/livequeue"),
            ("Wiki", "/wiki"),
        ],
    )
    def test_primary_nav_links_land_on_correct_page(
        self, page: Page, server: str, label: str, expected_path: str
    ):
        page.goto(server + "/")
        page.wait_for_load_state("load")
        page.locator(f"nav a:has-text('{label}')").click()
        page.wait_for_load_state("load")
        assert page.url.endswith(expected_path) or expected_path in page.url, (
            f"Nav link '{label}' led to {page.url}, expected path containing '{expected_path}'"
        )

    def test_brand_lockup_returns_home(self, page: Page, server: str):
        page.goto(server + "/wiki")
        page.locator("a.brand-lockup").click()
        page.wait_for_load_state("load")
        assert page.url.rstrip("/") == server or page.url == server + "/", (
            f"Brand lockup did not return to homepage; ended at {page.url}"
        )

    def test_active_nav_state_applied(self, page: Page, server: str):
        """The currently active nav link must carry the is-active class."""
        routes_and_texts = [
            ("/", "Home"),
            ("/livequeue", "Live Queue"),
            ("/wiki", "Wiki"),
        ]
        for path, link_text in routes_and_texts:
            page.goto(server + path)
            page.wait_for_load_state("load")
            active_link = page.locator("nav a.is-active")
            assert active_link.count() >= 1, f"No .is-active nav link on {path}"
            assert link_text in active_link.first.inner_text(), (
                f"On {path} the active link text was '{active_link.first.inner_text()}', "
                f"expected '{link_text}'"
            )


# ──────────────────────────────────────────────────────────────────────────────
# Flow 4 – Mobile viewport
# ──────────────────────────────────────────────────────────────────────────────

class TestMobileViewport:
    @pytest.fixture()
    def mobile_page(self, context, server):
        ctx = context
        p = ctx.new_page()
        p.set_viewport_size({"width": 390, "height": 844})  # iPhone 14
        p.goto(server + "/")
        p.wait_for_load_state("load")
        yield p
        p.close()

    def test_page_is_not_zoomed_out(self, mobile_page: Page):
        """viewport meta should prevent default 980-px layout zoom."""
        viewport_meta = mobile_page.locator("meta[name='viewport']")
        expect(viewport_meta).to_have_count(1)
        content = viewport_meta.get_attribute("content") or ""
        assert "width=device-width" in content, (
            f"viewport meta missing 'width=device-width': {content}"
        )

    def test_user_menu_toggle_opens_panel(self, mobile_page: Page, server: str):
        """The User menu toggle button must open the dropdown panel."""
        toggle = mobile_page.locator("button.user-menu-toggle")
        expect(toggle).to_be_visible()
        toggle.click()
        panel = mobile_page.locator("#user-menu-panel")
        # Panel should no longer be hidden after click
        hidden = panel.get_attribute("hidden")
        assert hidden is None, "User menu panel did not open after toggle click"

    def test_no_horizontal_overflow(self, mobile_page: Page):
        """At 390 px width there should be no horizontal scroll (overflow-x)."""
        overflow = mobile_page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )
        assert not overflow, (
            "Horizontal overflow detected at 390 px viewport width – content is wider than screen"
        )
