/**
 * Not-found and error states follow the route, and do not outlive it.
 *
 *  - valid -> unknown id -> valid: "No such ..." appears, then clears.
 *  - unknown id on load -> "Start from the picker": the picker returns.
 *  - a non-numeric id: "No such ..." with no reading request sent.
 *  - a failed meta load is still reported after navigating, because clearing
 *    the per-reading error must not hide a load error.
 */

import { expect, FRESH, navigate, openPage, present, responseFor, scenario,
         seen, settle, tools, UNAVAILABLE } from "./harness.mjs";

export async function run(browser, base, fx) {
  const results = [];
  const all = tools(fx);

  for (const [tool, t] of Object.entries(all)) {
    await scenario(results, `${tool}: valid -> unknown id -> valid`, async () => {
      const { page } = await openPage(browser, fx);
      try {
        await page.goto(`${base}/${tool}/${t.a}`, { waitUntil: "domcontentloaded" });
        await seen(page, /STALE_RESPONSE_A/);
        await navigate(page, `/${tool}/${t.unknown}`);
        await seen(page, t.notFound);
        expect(!(await present(page, UNAVAILABLE)), "unknown id reported as backend unavailable");
        await navigate(page, `/${tool}/${t.b}`);
        await seen(page, FRESH);
        const notFound = await present(page, t.notFound);
        const unavailable = await present(page, UNAVAILABLE);
        expect(!notFound && !unavailable, `after recovery: notFound=${notFound} unavailable=${unavailable}`);
        return "not-found shown, then cleared";
      } finally {
        await page.close();
      }
    });
  }

  for (const [tool, t] of Object.entries(all)) {
    await scenario(results, `${tool}: unknown id on load -> picker link`, async () => {
      const { page } = await openPage(browser, fx);
      try {
        await page.goto(`${base}/${tool}/${t.unknown}`, { waitUntil: "domcontentloaded" });
        await seen(page, t.notFound);
        await page.getByRole("link", { name: /start from the picker/i }).first().click();
        await page.waitForURL((u) => u.pathname === `/${tool}`);
        await seen(page, t.picker);
        const notFound = await present(page, t.notFound);
        const unavailable = await present(page, UNAVAILABLE);
        expect(!notFound && !unavailable, `after link: notFound=${notFound} unavailable=${unavailable}`);
        return "picker restored";
      } finally {
        await page.close();
      }
    });
  }

  for (const tool of ["value", "match"]) {
    const t = all[tool];
    await scenario(results, `${tool}: /${tool}/abc`, async () => {
      const { page, calls } = await openPage(browser, fx);
      try {
        const metaLoaded = responseFor(page, t.meta);
        await page.goto(`${base}/${tool}/abc`, { waitUntil: "domcontentloaded" });
        await metaLoaded;             // mount effects, including the reading one, have run
        await seen(page, t.notFound);
        await settle(page);
        const reading = calls.filter((c) => /\/(estimate|held-out-forecast)$/.test(c));
        expect(reading.length === 0, `reading requests sent: ${JSON.stringify(reading)}`);
        expect(!(await present(page, UNAVAILABLE)), "reported as backend unavailable");
        return "not found, no reading request";
      } finally {
        await page.close();
      }
    });
  }

  for (const [tool, t] of Object.entries(all)) {
    await scenario(results, `${tool}: failed meta load survives navigation`, async () => {
      const { page } = await openPage(browser, fx, { failPaths: [t.meta] });
      try {
        await page.goto(`${base}/${tool}/${t.a}`, { waitUntil: "domcontentloaded" });
        await seen(page, UNAVAILABLE);
        const bDelivered = responseFor(page, t.reading(t.b));
        await navigate(page, `/${tool}/${t.b}`);
        await bDelivered;
        await settle(page);
        expect(await present(page, UNAVAILABLE), "load error cleared after reading B");
        await navigate(page, `/${tool}`);
        await settle(page);
        expect(await present(page, UNAVAILABLE), "load error cleared on the picker");
        return "load error kept across navigation";
      } finally {
        await page.close();
      }
    });
  }

  return results;
}
