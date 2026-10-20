/**
 * End-to-end runner:  npm run test:e2e
 *
 * Prerequisites, both generated rather than committed:
 *   1. fixtures:  python -m backend.tests.export_ui_fixtures frontend/tests/e2e/.fixtures/fixtures.json
 *                 (from the repository root)
 *   2. a build:   npm run build
 *
 * Serves the build with Vite's preview server on localhost, runs both suites
 * in headless Chromium, and exits non-zero if any scenario fails.
 *
 *   --fixtures <file>  default tests/e2e/.fixtures/fixtures.json
 *   --dist <dir>       default dist; lets a different build be checked
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { preview } from "vite";
import { run as staleResponse } from "./stale-response.e2e.mjs";
import { run as routeErrors } from "./route-errors.e2e.mjs";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
};
const fixturesPath = resolve(frontend, arg("--fixtures", "tests/e2e/.fixtures/fixtures.json"));
const dist = resolve(frontend, arg("--dist", "dist"));

if (!existsSync(fixturesPath)) {
  console.error(`No fixtures at ${fixturesPath}.\nFrom the repository root run:\n` +
                "  python -m backend.tests.export_ui_fixtures frontend/tests/e2e/.fixtures/fixtures.json");
  process.exit(2);
}
if (!existsSync(resolve(dist, "index.html"))) {
  console.error(`No build at ${dist}. Run: npm run build`);
  process.exit(2);
}

const fx = JSON.parse(readFileSync(fixturesPath, "utf8"));
const server = await preview({
  root: frontend,
  logLevel: "warn",
  build: { outDir: dist },
  preview: { port: 4173, strictPort: false },
});
const base = server.resolvedUrls.local[0].replace(/\/$/, "");
const browser = await chromium.launch();

let results = [];
try {
  results = [
    ...(await staleResponse(browser, base, fx)),
    ...(await routeErrors(browser, base, fx)),
  ];
} finally {
  await browser.close();
  await server.close();
}

for (const r of results) {
  console.log(`${r.pass ? "PASS" : "FAIL"}  ${r.name}${r.detail ? `  (${r.detail})` : ""}`);
}
const passed = results.filter((r) => r.pass).length;
console.log(`${passed}/${results.length} passed`);
process.exit(passed === results.length ? 0 : 1);
