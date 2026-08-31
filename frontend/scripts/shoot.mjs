/**
 * True-resolution screenshot + text capture, for design research and visual
 * verification.
 *
 * Exists because the in-app browser pane composites at roughly one third
 * regardless of the viewport requested, clamps to a 448px floor, and cannot
 * crop regions. Every visual call in this redesign is a call about type and
 * spacing at real sizes, so the evidence has to come from a real headless
 * Chromium writing a real file.
 *
 *   node scripts/shoot.mjs <url> <out.png> [--w 1440] [--h 900] [--dsf 2]
 *                          [--full] [--wait 1500] [--text out.txt]
 *
 * Defaults to 1440x900 at deviceScaleFactor 2 -> a 2880x1800 file.
 */

import { chromium } from "playwright";
import { writeFileSync } from "node:fs";

const args = process.argv.slice(2);
const [url, out] = args;
if (!url || !out) {
  console.error("usage: shoot.mjs <url> <out.png> [--w N] [--h N] [--dsf N] [--full] [--wait ms] [--text file]");
  process.exit(2);
}
const flag = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i === -1 ? fallback : args[i + 1];
};
const has = (name) => args.includes(`--${name}`);

const width = Number(flag("w", 1440));
const height = Number(flag("h", 900));
const dsf = Number(flag("dsf", 2));
const wait = Number(flag("wait", 1800));
const textOut = flag("text", null);

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width, height },
  deviceScaleFactor: dsf,
});

try {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
  // networkidle is unreliable on marketing sites that poll; a fixed settle
  // plus a fonts.ready await is more predictable than waiting for silence.
  await page.waitForTimeout(wait);
  await page.evaluate(() => document.fonts?.ready).catch(() => {});

  await page.screenshot({ path: out, fullPage: has("full") });

  const info = await page.evaluate(() => ({
    title: document.title,
    url: location.href,
    text: document.body.innerText.slice(0, 6000),
  }));
  if (textOut) writeFileSync(textOut, `${info.title}\n${info.url}\n\n${info.text}`, "utf8");

  console.log(JSON.stringify({ ok: true, title: info.title, url: info.url, out, width, height, dsf }));
} catch (e) {
  console.log(JSON.stringify({ ok: false, error: e.message.split("\n")[0], url }));
  process.exitCode = 1;
} finally {
  await browser.close();
}
