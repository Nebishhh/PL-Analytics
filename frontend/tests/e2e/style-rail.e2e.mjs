/**
 * The style rail draws its zones and its needle in ink.
 *
 * The API names zone states low / moderate / clear; the marks draw
 * strong / qualified / weak / absent. Passed through unmapped, every ink
 * lookup is undefined, so the zones and the needle render with no background
 * and the rail reads as empty. This checks the computed colour of each strip
 * inside the separation rail, for both exported players.
 */

import { expect, openPage, scenario, tools } from "./harness.mjs";

const RAIL = '[aria-label^="Separation"]';
const NO_INK = "rgba(0, 0, 0, 0)";

export async function run(browser, base, fx) {
  const results = [];
  const t = tools(fx).style;

  for (const slug of [t.a, t.b]) {
    await scenario(results, `style rail: zones and needle are inked (${slug})`, async () => {
      const { page } = await openPage(browser, fx);
      try {
        await page.goto(`${base}/style/${slug}`, { waitUntil: "domcontentloaded" });
        const rail = page.locator(RAIL).first();
        await rail.waitFor({ state: "visible", timeout: 10_000 });

        // Direct children of the trough: the zone strips, then the needle.
        const strips = await rail.evaluate((el) =>
          [...el.children].map((c) => ({
            width: c.getBoundingClientRect().width,
            ink: getComputedStyle(c).backgroundColor,
          })));
        const needle = strips.filter((s) => s.width <= 2);
        const zones = strips.filter((s) => s.width > 2);

        expect(needle.length === 1, `expected one needle, found ${needle.length}`);
        expect(zones.length >= 3, `expected three zones, found ${zones.length}`);
        const bare = strips.filter((s) => s.ink === NO_INK).length;
        expect(bare === 0, `${bare} of ${strips.length} strips have no ink`);
        return `needle ${needle[0].ink}; zones ${zones.map((z) => z.ink).join(", ")}`;
      } finally {
        await page.close();
      }
    });
  }
  return results;
}
