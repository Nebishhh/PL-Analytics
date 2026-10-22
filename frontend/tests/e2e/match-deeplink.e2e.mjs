/**
 * A deep link to a match outside the default season shows that season.
 *
 * The season dropdown defaults to the latest season. A link to an earlier
 * match used to load the right forecast while the dropdown still showed the
 * latest season, so the Match picker could not find the linked match and
 * showed its placeholder instead of the fixture.
 *
 * Run twice: once with responses in their natural order, and once with the
 * season list held until the forecast has landed, so the default season
 * arrives last and must not overwrite the linked one.
 */

import { expect, openPage, responseFor, scenario, settle, tools } from "./harness.mjs";

export async function run(browser, base, fx) {
  const results = [];
  const t = tools(fx).match;
  const { game_id: id, season } = fx.ids.match_early;
  const forecast = fx.responses[t.reading(id)];
  const { home_club: home, away_club: away } = forecast.match;

  for (const holdSeasons of [false, true]) {
    const order = holdSeasons ? "season list arrives last" : "natural order";
    await scenario(results, `match deep link: season ${season} selected (${order})`, async () => {
      const { page, held } = await openPage(browser, fx,
        holdSeasons ? { holdPath: "/api/match/seasons" } : {});
      try {
        const landed = responseFor(page, t.reading(id));
        await page.goto(`${base}/match/${id}`, { waitUntil: "domcontentloaded" });
        await landed;
        if (holdSeasons) {
          await held.requested;
          const seasonsLanded = responseFor(page, "/api/match/seasons");
          held.release("success");
          await seasonsLanded;
        }
        await page.getByText(`${home}`).first().waitFor({ state: "visible", timeout: 10_000 });
        await settle(page);

        const seasonShown = (await page.locator("div.label", { hasText: /^Season$/ })
          .locator("xpath=following-sibling::*[1]").innerText()).trim();
        const matchShown = (await page.locator("div.label", { hasText: /^Match$/ })
          .locator("xpath=following-sibling::*[1]").innerText()).trim();

        expect(seasonShown === String(season),
               `season dropdown shows "${seasonShown}", expected "${season}"`);
        expect(matchShown.includes(home) && matchShown.includes(away),
               `match picker shows "${matchShown}", expected ${home} vs ${away}`);
        return `season "${seasonShown}"; match "${matchShown}"`;
      } finally {
        await page.close();
      }
    });
  }
  return results;
}
