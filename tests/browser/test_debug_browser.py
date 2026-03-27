from __future__ import annotations

from playwright.sync_api import Page

from tests.browser.conftest import ASSISTANT_PASSWORD, ASSISTANT_USERNAME


def test_debug_homepage_h1s(page: Page, server: str):
    page.goto(server + "/")
    page.wait_for_load_state("load")

    h1_data = page.evaluate(
        """
    () => Array.from(document.querySelectorAll("h1")).map((el, i) => ({
        index: i,
        text: (el.textContent || "").trim(),
        html: el.outerHTML
    }))
    """
    )

    print("\n=== H1 DEBUG ===")
    print(h1_data)
    assert True


def test_debug_login_submission(page: Page, server: str):
    responses = []

    def record_response(resp):
        if (
            "assistant-login" in resp.url
            or "queue" in resp.url
            or "hardware_list" in resp.url
        ):
            responses.append(
                {
                    "url": resp.url,
                    "status": resp.status,
                    "headers": dict(resp.headers),
                }
            )

    page.on("response", record_response)

    page.goto(server + "/assistant-login")
    page.wait_for_load_state("load")

    print("\n=== LOGIN PAGE URL BEFORE SUBMIT ===")
    print(page.url)

    print("\n=== LOGIN FORM HTML ===")
    print(page.locator("form").first.evaluate("(el) => el.outerHTML"))

    page.fill("input[name='username']", ASSISTANT_USERNAME)
    page.fill("input[name='password']", ASSISTANT_PASSWORD)

    with page.expect_navigation(wait_until="load"):
        page.locator("form").first.evaluate("(form) => form.requestSubmit()")

    print("\n=== LOGIN PAGE URL AFTER SUBMIT ===")
    print(page.url)

    print("\n=== LOGIN PAGE BODY AFTER SUBMIT ===")
    print(page.inner_text("body"))

    print("\n=== LOGIN COOKIES AFTER SUBMIT ===")
    print(page.context.cookies())

    print("\n=== LOGIN RESPONSES ===")
    print(responses)

    assert True


def test_debug_queue_requests(authenticated_page: Page, server: str):
    responses = []

    def record_response(resp):
        if "queue" in resp.url or "api" in resp.url or "socket.io" in resp.url:
            try:
                body_preview = resp.text()[:300]
            except Exception:
                body_preview = "<unavailable>"
            responses.append(
                {
                    "url": resp.url,
                    "status": resp.status,
                    "body_preview": body_preview,
                }
            )

    authenticated_page.on("response", record_response)

    authenticated_page.goto(server + "/queue")
    authenticated_page.wait_for_load_state("load")
    authenticated_page.wait_for_timeout(1500)

    print("\n=== QUEUE PAGE URL ===")
    print(authenticated_page.url)

    print("\n=== QUEUE PAGE BODY ===")
    print(authenticated_page.inner_text("body"))

    print("\n=== QUEUE COOKIES ===")
    print(authenticated_page.context.cookies())

    print("\n=== QUEUE RESPONSES ===")
    for item in responses:
        print(item)

    assert True


def test_debug_assistant_login_page_structure(page: Page, server: str):
    page.goto(server + "/assistant-login")
    page.wait_for_load_state("load")

    data = page.evaluate(
        """
    () => ({
        title: document.title,
        forms: Array.from(document.querySelectorAll("form")).map(f => f.outerHTML),
        inputs: Array.from(document.querySelectorAll("input")).map(i => ({
            name: i.name,
            type: i.type,
            value: i.value
        })),
        buttons: Array.from(document.querySelectorAll("button")).map(b => ({
            type: b.type,
            text: (b.textContent || "").trim()
        })),
        bodyText: document.body.innerText
    })
    """
    )

    print("\n=== ASSISTANT LOGIN STRUCTURE ===")
    print(data)
    assert True
