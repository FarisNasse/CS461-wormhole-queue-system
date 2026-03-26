#!/usr/bin/env node
/**
 * tests/browser/lighthouse_audit.js
 *
 * Runs programmatic Lighthouse audits against a live Wormhole server and
 * writes per-page JSON + HTML reports to tests/browser/reports/.
 *
 * Usage:
 *   node tests/browser/lighthouse_audit.js [base_url]
 *
 * Examples:
 *   node tests/browser/lighthouse_audit.js                         # default http://127.0.0.1:5000
 *   node tests/browser/lighthouse_audit.js http://localhost:5555   # custom port
 *   BASE_URL=http://staging.example.com node tests/browser/lighthouse_audit.js
 *
 * Install once:
 *   npm install --save-dev lighthouse chrome-launcher
 *
 * The script exits with code 1 if any page violates the defined score thresholds.
 */

const fs   = require("fs");
const path = require("path");

let lighthouse, chromeLauncher;
try {
  lighthouse     = require("lighthouse");
  chromeLauncher = require("chrome-launcher");
} catch (_) {
  console.error(
    "❌  Missing dependencies. Run:\n    npm install --save-dev lighthouse chrome-launcher"
  );
  process.exit(1);
}

// ──────────────────────────────────────────────────────────────────────────────
// Configuration
// ──────────────────────────────────────────────────────────────────────────────

const BASE_URL = process.argv[2] || process.env.BASE_URL || "http://127.0.0.1:5000";

const REPORTS_DIR = path.join(__dirname, "reports");
fs.mkdirSync(REPORTS_DIR, { recursive: true });

/**
 * Pages to audit.
 *  - route      : URL path
 *  - name       : used for report filenames and log output
 *  - thresholds : Lighthouse score thresholds (0–100).  A page fails if any
 *                 category score falls below its threshold.
 *                 Set a threshold to 0 to skip that category for this page.
 */
const PAGES = [
  {
    route: "/",
    name:  "homepage",
    thresholds: { performance: 70, accessibility: 85, "best-practices": 80, seo: 70 },
  },
  {
    route: "/livequeue",
    name:  "livequeue",
    thresholds: { performance: 65, accessibility: 85, "best-practices": 80, seo: 60 },
  },
  {
    route: "/wiki",
    name:  "wiki",
    thresholds: { performance: 70, accessibility: 85, "best-practices": 80, seo: 70 },
  },
  {
    route: "/createticket",
    name:  "createticket",
    thresholds: { performance: 70, accessibility: 85, "best-practices": 80, seo: 60 },
  },
  {
    route: "/login",
    name:  "login",
    thresholds: { performance: 75, accessibility: 90, "best-practices": 80, seo: 60 },
  },
];

/** Lighthouse configuration shared across all pages. */
const LH_CONFIG = {
  extends: "lighthouse:default",
  settings: {
    // Simulate a mid-range mobile device on a typical campus network
    formFactor:      "mobile",
    throttlingMethod: "simulate",
    throttling: {
      rttMs:                   40,
      throughputKbps:          10240,  // 10 Mbps – typical campus Wi-Fi
      cpuSlowdownMultiplier:   2,
    },
    // Only run the audits for our four categories
    onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
    // Skip audits that require HTTPS in development
    skipAudits:      ["uses-http2", "redirects-http", "is-on-https"],
  },
};

// ──────────────────────────────────────────────────────────────────────────────
// Audit runner
// ──────────────────────────────────────────────────────────────────────────────

async function auditPage(chrome, page) {
  const url    = BASE_URL + page.route;
  const flags  = { port: chrome.port, output: ["json", "html"], logLevel: "error" };

  console.log(`\n  Auditing  ${url} …`);

  let runnerResult;
  try {
    runnerResult = await lighthouse(url, flags, LH_CONFIG);
  } catch (err) {
    console.error(`  ❌  Lighthouse threw for ${url}: ${err.message}`);
    return { page, scores: {}, passed: false, error: err.message };
  }

  const { lhr, report } = runnerResult;

  // Write reports
  const jsonPath = path.join(REPORTS_DIR, `lh_${page.name}.json`);
  const htmlPath = path.join(REPORTS_DIR, `lh_${page.name}.html`);
  fs.writeFileSync(jsonPath, report[0]);   // [0] = JSON
  fs.writeFileSync(htmlPath, report[1]);   // [1] = HTML

  // Extract category scores
  const scores = {};
  for (const [id, cat] of Object.entries(lhr.categories)) {
    scores[id] = Math.round((cat.score ?? 0) * 100);
  }

  // Check thresholds
  const failures = [];
  for (const [cat, minScore] of Object.entries(page.thresholds)) {
    if (minScore === 0) continue;
    const actual = scores[cat] ?? 0;
    if (actual < minScore) {
      failures.push(`${cat}: ${actual} (need ≥ ${minScore})`);
    }
  }

  const passed = failures.length === 0;
  const icon   = passed ? "✅" : "❌";
  const scoreStr = Object.entries(scores)
    .map(([k, v]) => `${k.slice(0,4)}=${v}`)
    .join("  ");

  console.log(`  ${icon}  ${page.name}  [${scoreStr}]`);
  if (!passed) {
    failures.forEach(f => console.log(`       ↳ FAIL  ${f}`));
  }
  console.log(`       Reports: ${htmlPath}`);

  // Surface key performance metrics
  const fcp  = lhr.audits?.["first-contentful-paint"]?.displayValue   ?? "–";
  const lcp  = lhr.audits?.["largest-contentful-paint"]?.displayValue ?? "–";
  const tbt  = lhr.audits?.["total-blocking-time"]?.displayValue      ?? "–";
  const cls  = lhr.audits?.["cumulative-layout-shift"]?.displayValue  ?? "–";
  const ttfb = lhr.audits?.["server-response-time"]?.displayValue     ?? "–";
  console.log(`       FCP=${fcp}  LCP=${lcp}  TBT=${tbt}  CLS=${cls}  TTFB=${ttfb}`);

  return { page, scores, passed, failures };
}

// ──────────────────────────────────────────────────────────────────────────────
// Summary report
// ──────────────────────────────────────────────────────────────────────────────

function writeSummary(results) {
  const summary = {
    generatedAt: new Date().toISOString(),
    baseUrl:     BASE_URL,
    pages:       results.map(r => ({
      name:   r.page.name,
      route:  r.page.route,
      scores: r.scores,
      passed: r.passed,
      failures: r.failures ?? [],
      error:  r.error ?? null,
    })),
  };
  const summaryPath = path.join(REPORTS_DIR, "lh_summary.json");
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));

  // Also write a simple Markdown table for PR / wiki embedding
  const rows = results.map(r => {
    const icon  = r.passed ? "✅" : "❌";
    const perf  = r.scores["performance"]     ?? "–";
    const a11y  = r.scores["accessibility"]   ?? "–";
    const bp    = r.scores["best-practices"]  ?? "–";
    const seo   = r.scores["seo"]             ?? "–";
    return `| ${icon} | \`${r.page.route}\` | ${perf} | ${a11y} | ${bp} | ${seo} |`;
  });

  const md = [
    `# Lighthouse Summary — ${new Date().toLocaleDateString()}`,
    "",
    `Base URL: \`${BASE_URL}\``,
    "",
    "| | Page | Perf | A11y | Best Practices | SEO |",
    "|---|---|---|---|---|---|",
    ...rows,
    "",
    `_Generated by \`tests/browser/lighthouse_audit.js\`_`,
  ].join("\n");

  fs.writeFileSync(path.join(REPORTS_DIR, "lh_summary.md"), md);
  console.log(`\n  Summary written to ${summaryPath}`);
}

// ──────────────────────────────────────────────────────────────────────────────
// Main
// ──────────────────────────────────────────────────────────────────────────────

(async () => {
  console.log(`\n🔭  Wormhole Lighthouse Audit`);
  console.log(`    Base URL : ${BASE_URL}`);
  console.log(`    Pages    : ${PAGES.map(p => p.route).join("  ")}`);
  console.log("─".repeat(60));

  // Launch one Chrome instance; re-use it across all pages for speed
  const chrome = await chromeLauncher.launch({
    chromeFlags: [
      "--headless=new",
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
    ],
  });

  const results = [];
  try {
    for (const page of PAGES) {
      results.push(await auditPage(chrome, page));
    }
  } finally {
    await chrome.kill();
  }

  writeSummary(results);

  const failCount = results.filter(r => !r.passed).length;
  console.log("\n" + "─".repeat(60));
  if (failCount === 0) {
    console.log(`✅  All ${results.length} pages passed their Lighthouse thresholds.\n`);
    process.exit(0);
  } else {
    console.log(`❌  ${failCount}/${results.length} page(s) failed their Lighthouse thresholds.\n`);
    process.exit(1);
  }
})();
