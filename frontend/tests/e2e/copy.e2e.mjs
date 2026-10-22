/**
 * Project 03's output is never described as playing styles (AGENTS.md §4).
 *
 * Checked on rendered text, not source, so a comment that names the rule
 * cannot trip it (AGENTS.md §7.1). The style tool's own disclaimer, "not
 * playing styles", is the one permitted use and is removed before matching.
 */

import { expect, openPage, present, scenario, seen, UNAVAILABLE } from "./harness.mjs";

const FORBIDDEN = /playing[\s-]+styles?/i;
const PERMITTED = /not playing styles/gi;

const PAGES = [
  ["/", /market value/i],
  ["/style", /pick a player to see which cluster/i],
  ["/about", /how these models work/i],
];

export async function run(browser, base, fx) {
  const results = [];
  for (const [path, ready] of PAGES) {
    await scenario(results, `copy: no "playing styles" on ${path}`, async () => {
      const { page } = await openPage(browser, fx);
      try {
        await page.goto(`${base}${path}`, { waitUntil: "networkidle" });
        await seen(page, ready);
        // An error notice would pass the text check vacuously.
        expect(!(await present(page, UNAVAILABLE)), "page shows the backend-unavailable notice");
        const text = (await page.locator("body").innerText()).replace(PERMITTED, "");
        const hit = text.match(FORBIDDEN);
        expect(!hit, `found "${hit?.[0]}" in: …${hit ? text.slice(Math.max(0, hit.index - 40), hit.index + 40).replace(/\s+/g, " ") : ""}…`);
        return "";
      } finally {
        await page.close();
      }
    });
  }
  return results;
}
