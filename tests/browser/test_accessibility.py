# tests/browser/test_accessibility.py
"""
Accessibility tests powered by axe-core (via axe-playwright).

These tests inject the axe-core engine into each page and run automated
WCAG 2.1 AA checks.  They complement the performance tests and are
particularly valuable for a physics tutoring centre that may serve
students with visual or motor impairments.

Install:
    pip install axe-playwright
    playwright install chromium

Run:
    pytest tests/browser/test_accessibility.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from playwright.sync_api import Page

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# axe-playwright is optional – skip the whole module gracefully if absent
axe_playwright = pytest.importorskip(
    "axe_playwright_python",
    reason="axe-playwright not installed; run: pip install axe-playwright-python",
)

from axe_playwright_python.sync_playwright import Axe  # noqa: E402

AXE = Axe()

# Violation impact levels that should fail CI
FAIL_ON_IMPACT = {"critical", "serious"}

# Pages to audit  (route → human-readable name)
PUBLIC_PAGES = {
    "/": "Homepage",
    "/livequeue": "Live Queue",
    "/wiki": "Wiki",
    "/createticket": "Create Ticket",
    "/login": "Login",
}


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _run_axe(page: Page, url: str, report_name: str) -> list[dict]:
    """
    Navigate to *url*, inject axe-core, run the audit, save a JSON report,
    and return only the violations.
    """
    page.goto(url)
    page.wait_for_load_state("networkidle")

    results = AXE.run(page)
    report_path = REPORTS_DIR / f"a11y_{report_name}.json"
    report_path.write_text(
        json.dumps(
            {
                "url": url,
                "violations": results.violations,
                "passes": len(results.passes) if hasattr(results, "passes") else "n/a",
            },
            indent=2,
        )
    )
    return results.violations


def _format_violations(violations: list[dict]) -> str:
    lines = []
    for v in violations:
        lines.append(f"  [{v.get('impact','?').upper()}] {v.get('id')} — {v.get('description')}")
        for node in v.get("nodes", [])[:2]:
            lines.append(f"      selector: {node.get('target')}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Parametrised accessibility audit for all public pages
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("route,name", PUBLIC_PAGES.items())
def test_no_critical_or_serious_violations(page: Page, server: str, route: str, name: str):
    """
    WCAG 2.1 AA: no critical or serious axe-core violations allowed.
    Minor/moderate violations are reported as warnings only.
    """
    violations = _run_axe(page, server + route, name.lower().replace(" ", "_"))

    blocking = [v for v in violations if v.get("impact") in FAIL_ON_IMPACT]
    advisory = [v for v in violations if v.get("impact") not in FAIL_ON_IMPACT]

    if advisory:
        # Print as informational, not a failure
        print(
            f"\n[a11y advisory on {name}]\n"
            + _format_violations(advisory)
        )

    if blocking:
        detail = _format_violations(blocking)
        pytest.fail(
            f"Accessibility violations (critical/serious) on {name} ({route}):\n{detail}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Targeted structural checks (don't require axe)
# ──────────────────────────────────────────────────────────────────────────────

class TestSemanticStructure:
    """
    Manual checks for semantic HTML patterns that axe-core does not always
    catch automatically.
    """

    def test_single_h1_per_page(self, page: Page, server: str):
        for route in PUBLIC_PAGES:
            page.goto(server + route)
            page.wait_for_load_state("load")
            h1_count = page.locator("h1").count()
            assert h1_count == 1, (
                f"{route}: expected exactly 1 <h1>, found {h1_count}"
            )

    def test_all_images_have_alt_text(self, page: Page, server: str):
        for route in PUBLIC_PAGES:
            page.goto(server + route)
            page.wait_for_load_state("load")
            imgs_without_alt = page.evaluate("""() =>
                [...document.querySelectorAll('img')]
                    .filter(img => !img.hasAttribute('alt'))
                    .map(img => img.src)
            """)
            assert not imgs_without_alt, (
                f"{route}: images missing alt attribute: {imgs_without_alt}"
            )

    def test_form_inputs_have_labels(self, page: Page, server: str):
        page.goto(server + "/createticket")
        page.wait_for_load_state("load")
        unlabelled = page.evaluate("""() => {
            const inputs = [...document.querySelectorAll('input, select, textarea')]
                .filter(el => el.type !== 'hidden' && el.type !== 'submit');
            return inputs
                .filter(el => {
                    const hasLabel = document.querySelector(`label[for='${el.id}']`);
                    const hasAria  = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
                    return !hasLabel && !hasAria;
                })
                .map(el => el.outerHTML.slice(0, 80));
        }""")
        assert not unlabelled, (
            f"Form inputs on /createticket without labels: {unlabelled}"
        )

    def test_main_landmark_present(self, page: Page, server: str):
        for route in PUBLIC_PAGES:
            page.goto(server + route)
            count = page.locator("main, [role='main']").count()
            assert count >= 1, f"{route}: no <main> landmark found"

    def test_nav_has_aria_label(self, page: Page, server: str):
        page.goto(server + "/")
        page.wait_for_load_state("load")
        nav = page.locator("nav[aria-label]")
        assert nav.count() >= 1, (
            "Primary <nav> should have an aria-label for screen-reader users"
        )

    def test_live_queue_has_aria_live_region(self, page: Page, server: str):
        """
        The live queue updates dynamically; the container should declare
        aria-live='polite' so screen readers announce changes.
        """
        page.goto(server + "/livequeue")
        page.wait_for_load_state("load")
        live_regions = page.locator("[aria-live]").count()
        assert live_regions >= 1, (
            "/livequeue has no aria-live region — screen readers won't announce queue updates"
        )

    def test_flash_messages_use_role_status(self, page: Page, server: str):
        """
        Flash messages on /createticket should have role=status or be inside
        an aria-live region so assistive tech announces them.
        """
        page.goto(server + "/createticket")
        page.wait_for_load_state("load")
        # The flash container uses aria-live='polite' in base.html
        polite = page.locator("[aria-live='polite']").count()
        assert polite >= 1, (
            "Flash message container should have aria-live='polite'"
        )
