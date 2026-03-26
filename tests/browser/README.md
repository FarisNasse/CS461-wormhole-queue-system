# Browser Performance & UX Tests

This folder contains two complementary test layers that sit on top of the
existing Locust server-load tests:

| Layer | Tool | What it measures |
|---|---|---|
| **Server load** | Locust (`tests/load/`) | Request throughput, response-time percentiles, failure rate under concurrent users |
| **Browser perf** | Playwright (`test_performance.py`) | Core Web Vitals (FCP, LCP, CLS, TTFB) inside a real Chromium browser |
| **UX flows** | Playwright (`test_ux_flows.py`) | Student ticket submission, assistant claim/resolve cycle, mobile nav |
| **Accessibility** | axe-core + Playwright (`test_accessibility.py`) | WCAG 2.1 AA violations, semantic HTML structure |
| **Lighthouse audit** | Lighthouse + Node.js (`lighthouse_audit.js`) | Full Lighthouse scores (Performance, Accessibility, Best Practices, SEO) |

---

## Quick start

### 1 — Python dependencies

```bash
pip install playwright pytest-playwright axe-playwright-python requests
playwright install chromium
```

### 2 — Node.js dependencies (Lighthouse only)

```bash
npm install --save-dev lighthouse chrome-launcher
```

### 3 — Start the Flask app in a separate terminal

```bash
# Seed the browser-test assistant account first
python tests/seed_loadtest.py

# Start the server
flask run --port 5555
# or
python run.py
```

### 4 — Run the Playwright tests

```bash
# From the project root
pytest tests/browser/ -v

# Skip the slow polling test in dev
pytest tests/browser/ -v -m "not slow"

# Just performance tests
pytest tests/browser/test_performance.py -v

# Just accessibility
pytest tests/browser/test_accessibility.py -v

# Custom server port (default: 5555)
BROWSER_TEST_PORT=5000 pytest tests/browser/ -v
```

### 5 — Run the Lighthouse audit

```bash
# Requires the Flask server to be running
node tests/browser/lighthouse_audit.js

# Against a different host
node tests/browser/lighthouse_audit.js http://localhost:5000

# Against staging
BASE_URL=https://staging.example.com node tests/browser/lighthouse_audit.js
```

Reports are written to `tests/browser/reports/`:
- `lh_<page>.html`  — full interactive Lighthouse report
- `lh_<page>.json`  — machine-readable Lighthouse data
- `lh_summary.md`   — Markdown table for PR descriptions / wiki
- `lh_summary.json` — machine-readable summary
- `<page>.json`      — Playwright Navigation Timing snapshot
- `a11y_<page>.json` — axe-core violations per page

---

## Score thresholds

Thresholds are defined in two places:

### Playwright (Core Web Vitals)

`tests/browser/conftest.py` → `THRESHOLDS` dict:

```python
THRESHOLDS = {
    "lcp_ms":               2500,   # Largest Contentful Paint  ≤ 2.5 s
    "fcp_ms":               1800,   # First Contentful Paint    ≤ 1.8 s
    "ttfb_ms":               800,   # Time to First Byte        ≤ 800 ms
    "dom_content_loaded_ms": 1500,
    "load_event_ms":         3000,
    "cls":                   0.1,   # Cumulative Layout Shift
}
```

### Lighthouse

`tests/browser/lighthouse_audit.js` → `PAGES` array, per-page `thresholds` object:

```js
{ performance: 70, accessibility: 85, "best-practices": 80, seo: 70 }
```

Adjust these to match your team's SLAs.

---

## CI integration (GitHub Actions example)

```yaml
# .github/workflows/browser-tests.yml
name: Browser Tests

on: [push, pull_request]

jobs:
  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - uses: actions/setup-node@v4
        with: { node-version: "20" }

      - name: Install Python deps
        run: |
          pip install -r requirements.txt
          pip install playwright pytest-playwright axe-playwright-python requests
          playwright install --with-deps chromium

      - name: Install Node deps
        run: npm install --save-dev lighthouse chrome-launcher

      - name: Seed DB and start Flask
        run: |
          python tests/seed_loadtest.py &
          FLASK_APP=run.py flask run --port 5555 &
          sleep 3
        env:
          LOCUST_ASSISTANT_USERNAME: ci_test_assistant
          LOCUST_ASSISTANT_PASSWORD: ci_test_password

      - name: Run Playwright tests
        run: pytest tests/browser/ -v --tb=short
        env:
          BROWSER_TEST_PORT: 5555

      - name: Run Lighthouse audit
        run: node tests/browser/lighthouse_audit.js http://127.0.0.1:5555

      - name: Upload reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: browser-test-reports
          path: tests/browser/reports/
```

---

## What the tests cover

### `test_performance.py`

- **Homepage** — TTFB, DOMContentLoaded, CLS (including after scroll)
- **Live Queue** — initial load thresholds, table renders before polling fires, no console errors, interaction responsiveness after polling
- **Wiki** — load thresholds, `<main>` visible quickly
- **Create Ticket** — form interactive within 1.5 s, submit round-trip < 3 s
- **Queue Dashboard** — authenticated load thresholds, no console errors
- **All public pages** — parametrised smoke check: load event < 3 s

### `test_ux_flows.py`

- **Student flow** — form submission, ticket appears in live queue
- **Homepage CTAs** — Submit Request and View Live Queue buttons link correctly
- **Assistant flow** — login renders form, invalid credentials show error, valid login redirects, queue dashboard accessible, full claim→resolve→verify cycle
- **Navigation** — all primary nav links land on the right page, brand lockup returns home, active state applied correctly
- **Mobile (390 px)** — viewport meta prevents zoom, user-menu toggle opens panel, no horizontal overflow

### `test_accessibility.py`

- **WCAG 2.1 AA** — axe-core automated scan on all public pages; critical/serious violations fail CI
- **Single `<h1>`** per page
- **All `<img>` have `alt`** attributes
- **Form inputs have `<label>`** elements (or aria-label)
- **`<main>` landmark** present on every page
- **`<nav>` has `aria-label`**
- **`aria-live` region** on Live Queue for screen-reader announcements
- **Flash messages** inside `aria-live="polite"` container
