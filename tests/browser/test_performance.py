"""
Core Web Vitals + Navigation Timing performance tests.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from playwright.sync_api import Page

from tests.browser.conftest import THRESHOLDS, get_cls, get_nav_timing

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def _navigate_and_collect(page: Page, url: str) -> dict:
    page.goto(url)
    page.wait_for_load_state("load")
    metrics = get_nav_timing(page)
    metrics["cls"] = get_cls(page)
    metrics["url"] = url
    return metrics


def _save_report(name: str, metrics: dict) -> None:
    path = REPORTS_DIR / f"{name}.json"
    path.write_text(json.dumps(metrics, indent=2))


def _assert_thresholds(metrics: dict, label: str) -> None:
    failures = []

    checks = [
        ("ttfb", "ttfb_ms", "Time to First Byte"),
        ("dom_content_loaded", "dom_content_loaded_ms", "DOMContentLoaded"),
        ("load_event", "load_event_ms", "Load Event"),
    ]
    for key, threshold_key, human in checks:
        value = metrics.get(key)
        limit = THRESHOLDS[threshold_key]
        if value is not None and value > limit:
            failures.append(f"  {human}: {value:.0f} ms  (limit {limit} ms)")

    fcp = metrics.get("fcp")
    if fcp is not None and fcp > THRESHOLDS["fcp_ms"]:
        failures.append(
            f"  First Contentful Paint: {fcp:.0f} ms  (limit {THRESHOLDS['fcp_ms']} ms)"
        )

    cls = metrics.get("cls", 0.0)
    if cls > THRESHOLDS["cls"]:
        failures.append(
            f"  Cumulative Layout Shift: {cls:.4f}  (limit {THRESHOLDS['cls']})"
        )

    if failures:
        detail = "\n".join(failures)
        pytest.fail(f"Performance regressions on {label}:\n{detail}")


class TestHomepagePerformance:
    def test_ttfb(self, page: Page, server: str):
        metrics = _navigate_and_collect(page, server + "/")
        _save_report("homepage", metrics)
        assert (
            metrics["ttfb"] <= THRESHOLDS["ttfb_ms"]
        ), f"TTFB {metrics['ttfb']:.0f} ms exceeds {THRESHOLDS['ttfb_ms']} ms"

    def test_dom_content_loaded(self, page: Page, server: str):
        metrics = _navigate_and_collect(page, server + "/")
        assert (
            metrics["dom_content_loaded"] <= THRESHOLDS["dom_content_loaded_ms"]
        ), f"DOMContentLoaded {metrics['dom_content_loaded']:.0f} ms"

    def test_cls(self, page: Page, server: str):
        _navigate_and_collect(page, server + "/")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        cls = get_cls(page)
        assert (
            cls <= THRESHOLDS["cls"]
        ), f"CLS {cls:.4f} on homepage exceeds threshold {THRESHOLDS['cls']}"

    def test_no_render_blocking_resources(self, page: Page, server: str):
        page.goto(server + "/")
        page.wait_for_load_state("load")

        blocking = page.evaluate(
            """() => {
            return performance.getEntriesByType('resource')
                .filter(r => ['script','link'].includes(r.initiatorType) && r.renderBlockingStatus === 'blocking')
                .map(r => ({ name: r.name, duration: Math.round(r.duration) }));
        }"""
        )

        if blocking:
            names = ", ".join(r["name"].split("/")[-1] for r in blocking)
            pytest.xfail(f"Render-blocking resources detected (advisory): {names}")


class TestLiveQueuePerformance:
    def test_initial_load_thresholds(self, page: Page, server: str):
        metrics = _navigate_and_collect(page, server + "/livequeue")
        _save_report("livequeue", metrics)
        _assert_thresholds(metrics, "/livequeue")

    def test_table_renders_within_timeout(self, page: Page, server: str):
        page.goto(server + "/livequeue")
        page.wait_for_load_state("load")
        page.wait_for_selector("#tickets", state="visible", timeout=3000)

    def test_no_console_errors_on_load(self, page: Page, server: str):
        errors: list[str] = []
        page.on(
            "console",
            lambda msg: errors.append(msg.text) if msg.type == "error" else None,
        )

        page.goto(server + "/livequeue")
        page.wait_for_load_state("load")
        page.wait_for_selector("#tickets", state="visible", timeout=3000)
        page.wait_for_timeout(1000)

        assert not errors, f"Console errors on /livequeue: {errors}"

    def test_polling_does_not_block_interaction(self, page: Page, server: str):
        page.goto(server + "/livequeue")
        page.wait_for_load_state("load")
        page.wait_for_selector("#tickets", state="visible", timeout=3000)
        page.wait_for_timeout(1500)

        start = page.evaluate("performance.now()")
        page.locator("a.nav-link", has_text="Home").click()
        page.wait_for_load_state("load")
        elapsed = page.evaluate("performance.now()") - start

        assert elapsed < 2000, f"Navigation after polling took {elapsed:.0f} ms"


class TestWikiPerformance:
    def test_load_thresholds(self, page: Page, server: str):
        metrics = _navigate_and_collect(page, server + "/wiki")
        _save_report("wiki", metrics)
        _assert_thresholds(metrics, "/wiki")

    def test_content_visible_fast(self, page: Page, server: str):
        page.goto(server + "/wiki")
        page.wait_for_load_state("load")
        page.wait_for_selector("main", state="visible", timeout=2000)


class TestCreateTicketPerformance:
    def test_load_thresholds(self, page: Page, server: str):
        metrics = _navigate_and_collect(page, server + "/createticket")
        _save_report("createticket", metrics)
        _assert_thresholds(metrics, "/createticket")

    def test_form_interactive_quickly(self, page: Page, server: str):
        page.goto(server + "/createticket")
        page.wait_for_load_state("load")
        page.wait_for_selector(
            "input[name='name'], select[name='phClass'], select[name='location']",
            state="visible",
            timeout=1500,
        )

    def test_submit_response_time(self, page: Page, server: str):
        import random
        import string

        suffix = "".join(random.choices(string.ascii_lowercase, k=6))
        page.goto(server + "/createticket")
        page.wait_for_load_state("load")

        page.fill("input[name='name']", f"perf_test_{suffix}")
        page.select_option("select[name='phClass']", index=1)
        page.select_option("select[name='location']", label="Teams")

        start = page.evaluate("performance.now()")
        with page.expect_navigation(wait_until="load"):
            page.locator("form").first.evaluate("(form) => form.requestSubmit()")
        elapsed = page.evaluate("performance.now()") - start

        assert elapsed < 3000, f"Ticket submission round-trip took {elapsed:.0f} ms"


class TestQueueDashboardPerformance:
    def test_load_thresholds(self, authenticated_page: Page, server: str):
        metrics = _navigate_and_collect(authenticated_page, server + "/queue")
        _save_report("queue_dashboard", metrics)
        _assert_thresholds(metrics, "/queue")

    def test_no_console_errors(self, authenticated_page: Page, server: str):
        errors: list[str] = []
        authenticated_page.on(
            "console",
            lambda msg: errors.append(msg.text) if msg.type == "error" else None,
        )

        authenticated_page.goto(server + "/queue")
        authenticated_page.wait_for_load_state("load")
        authenticated_page.wait_for_timeout(1000)

        assert not errors, f"Console errors on /queue: {errors}"


PUBLIC_ROUTES = ["/", "/livequeue", "/wiki", "/createticket"]


@pytest.mark.parametrize("route", PUBLIC_ROUTES)
def test_all_public_pages_within_load_threshold(page: Page, server: str, route: str):
    metrics = _navigate_and_collect(page, server + route)
    assert metrics["load_event"] <= THRESHOLDS["load_event_ms"], (
        f"{route}: load event at {metrics['load_event']:.0f} ms "
        f"(limit {THRESHOLDS['load_event_ms']} ms)"
    )
