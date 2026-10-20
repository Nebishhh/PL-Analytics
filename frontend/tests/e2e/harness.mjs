/**
 * Shared pieces for the end-to-end suites.
 *
 * There is no live backend. Every /api request is intercepted and answered
 * from fixtures that backend/tests/export_ui_fixtures.py generates from the
 * committed artefacts, by calling the real route functions in-process. Paths
 * with no fixture are answered the way FastAPI answers them: 422 for an id
 * that is not an integer, 404 otherwise.
 *
 * WAITS
 *   Every wait is on a condition -- a request arriving, a response delivered,
 *   text appearing -- not on elapsed time. The one exception is settle(): a
 *   test that asserts something did NOT happen has no event to wait for, so
 *   after the last response is delivered it watches the page for a short,
 *   fixed window. That window is the only fixed delay in these suites.
 */

export const STALE = "STALE_RESPONSE_A";
export const FRESH = "FRESH_RESPONSE_B";
export const UNAVAILABLE = /backend unavailable/i;
const WAIT_MS = 10_000;
const SETTLE_MS = 250;

/** The three tools, keyed by route segment. */
export function tools(fx) {
  return {
    value: {
      a: fx.ids.value[0], b: fx.ids.value[1], unknown: "999999999",
      reading: (id) => `/api/value/players/${id}/estimate`,
      meta: "/api/value/meta",
      notFound: /no such player/i,
      picker: /pick a player to see an estimate/i,
    },
    match: {
      a: fx.ids.match[0], b: fx.ids.match[1], unknown: "999999999",
      reading: (id) => `/api/match/matches/${id}/held-out-forecast`,
      meta: "/api/match/meta",
      notFound: /no such match/i,
      picker: /pick a match to see the forecast/i,
    },
    style: {
      a: fx.ids.style[0], b: fx.ids.style[1], unknown: "no-such-player",
      reading: (id) => `/api/style/players/${encodeURIComponent(id)}/assignment`,
      meta: "/api/style/meta",
      notFound: /no such player/i,
      picker: /pick a player to see which cluster/i,
    },
  };
}

function deferred() {
  let resolve;
  const promise = new Promise((r) => { resolve = r; });
  return { promise, resolve };
}

/**
 * A page with /api intercepted.
 *   failPaths: paths answered with 500.
 *   holdPath:  a path whose response is withheld until held.release(mode) is
 *              called, mode "success" or "error". held.requested resolves when
 *              the page has sent that request.
 */
export async function openPage(browser, fx, { failPaths = [], holdPath = null } = {}) {
  const page = await browser.newPage();
  const calls = [];
  const requested = deferred();
  const release = deferred();

  await page.route("**/api/**", async (route) => {
    const u = new URL(route.request().url());
    const key = u.pathname + u.search;
    calls.push(key);

    if (key === holdPath) {
      requested.resolve();
      const mode = await release.promise;
      if (mode === "error") {
        return route.fulfill({ status: 500, contentType: "application/json",
                               body: '{"detail":"held request failed"}' });
      }
    } else if (failPaths.includes(key)) {
      return route.fulfill({ status: 500, contentType: "application/json",
                             body: '{"detail":"forced failure"}' });
    }

    if (key in fx.responses) {
      return route.fulfill({ status: 200, contentType: "application/json",
                             body: JSON.stringify(fx.responses[key]) });
    }
    const id = key.match(/\/(?:players|matches)\/([^/]+)\/(?:estimate|held-out-forecast)$/);
    if (id && !/^\d+$/.test(id[1])) {
      return route.fulfill({ status: 422, contentType: "application/json",
                             body: '{"detail":"int_parsing"}' });
    }
    return route.fulfill({ status: 404, contentType: "application/json",
                           body: '{"detail":"not found"}' });
  });

  return {
    page,
    calls,
    held: { requested: requested.promise, release: (mode) => release.resolve(mode) },
  };
}

/**
 * Client-side navigation, as the picker does it: the route changes and the
 * tool component stays mounted. A page.goto would remount it and hide exactly
 * the state bugs these suites exist to catch.
 */
export async function navigate(page, path) {
  await page.evaluate((p) => {
    history.pushState({}, "", p);
    window.dispatchEvent(new PopStateEvent("popstate", { state: history.state }));
  }, path);
  await page.waitForURL((u) => u.pathname === path, { timeout: WAIT_MS });
}

/** Resolves when a response for `path` has been delivered to the page. */
export function responseFor(page, path) {
  return page.waitForResponse((r) => new URL(r.url()).pathname === path,
                              { timeout: WAIT_MS });
}

/** Wait until text matching `pattern` is visible. */
export async function seen(page, pattern) {
  await page.getByText(pattern).first().waitFor({ state: "visible", timeout: WAIT_MS });
}

/** See WAITS above: two frames for React to commit, then a short watch. */
export async function settle(page) {
  await page.evaluate(() => new Promise((r) =>
    requestAnimationFrame(() => requestAnimationFrame(r))));
  await page.waitForTimeout(SETTLE_MS);
}

export async function present(page, pattern) {
  return (await page.getByText(pattern).count()) > 0;
}

/** Run one scenario, turning a timeout or assertion into a reported failure. */
export async function scenario(results, name, fn) {
  try {
    const detail = await fn();
    results.push({ name, pass: true, detail: detail ?? "" });
  } catch (e) {
    results.push({ name, pass: false, detail: String(e?.message ?? e).split("\n")[0] });
  }
}

export function expect(condition, message) {
  if (!condition) throw new Error(message);
}
