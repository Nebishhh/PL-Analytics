/**
 * A response for a selection the user has already left must not land.
 *
 * For each tool: open reading A and hold its response; navigate to reading B
 * and wait until B is on screen; only then release A -- once as a success and
 * once as a 500 -- and confirm the page still shows B with no error. Holding
 * A until B has rendered guarantees A arrives last, without timing guesses.
 */

import { expect, FRESH, navigate, openPage, present, responseFor, scenario,
         seen, settle, STALE, tools, UNAVAILABLE } from "./harness.mjs";

export async function run(browser, base, fx) {
  const results = [];
  for (const [tool, t] of Object.entries(tools(fx))) {
    for (const mode of ["success", "error"]) {
      await scenario(results, `stale ${tool}: late ${mode} for A after switching to B`, async () => {
        const { page, held } = await openPage(browser, fx, { holdPath: t.reading(t.a) });
        try {
          await page.goto(`${base}/${tool}/${t.a}`, { waitUntil: "domcontentloaded" });
          await held.requested;
          await navigate(page, `/${tool}/${t.b}`);
          await seen(page, FRESH);

          const delivered = responseFor(page, t.reading(t.a));
          held.release(mode);
          await delivered;
          await settle(page);

          const fresh = await present(page, FRESH);
          const stale = await present(page, STALE);
          const unavailable = await present(page, UNAVAILABLE);
          expect(fresh && !stale && !unavailable,
                 `fresh=${fresh} stale=${stale} unavailable=${unavailable}`);
          return `fresh=${fresh} stale=${stale} unavailable=${unavailable}`;
        } finally {
          await page.close();
        }
      });
    }
  }
  return results;
}
