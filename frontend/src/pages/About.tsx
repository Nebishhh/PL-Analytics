/**
 * The methodology page (DESIGN.md §9): the three headline results, what each
 * model cannot do, and the licence split.
 *
 * WHY ONE PAGE RATHER THAN THREE
 *   The licence split is shared material and would have to be triplicated, and
 *   the three limitations are most useful read together -- they are three
 *   different ways for a model to be confidently wrong. §9 also rules out
 *   cross-tool navigation in v1, so a reader who wants to compare has nowhere
 *   else to do it.
 *
 * WHY THE PLOTS ARE THE COMMITTED PNGs
 *   They are the evidence the README's claims rest on. Regenerating them in
 *   the browser, or restyling them to match this palette, would put the app's
 *   picture and the repository's picture quietly out of step (AGENTS.md §1.3).
 *   They arrive through the /plots proxy exactly as committed -- which is why
 *   they are light-background images sitting on a dark page, and why they are
 *   framed rather than blended into it.
 *
 * Every figure here is read from /api/meta, which reads the artefacts. Nothing
 * on this page is typed in (AGENTS.md §2.3).
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type AppMeta, type ToolSummary } from "../lib/api";
import { eur, num, pct } from "../lib/format";
import { ABOUT } from "../lib/copy";
import { Notice, Section, Sheet } from "../components/ui/Sheet";
import { Disclosure } from "../components/ui/Disclosure";

const TOOL_ROUTE: Record<string, string> = {
  value: "/value",
  match: "/match",
  style: "/style",
};

/**
 * Read a figure out of the untyped headline dict without asserting a shape.
 * Returns null rather than 0 when absent, so a missing figure renders as an
 * em dash instead of a confident wrong number.
 */
function n(h: Record<string, unknown>, key: string): number | null {
  const v = h[key];
  return typeof v === "number" ? v : null;
}

function str(h: Record<string, unknown>, key: string): string | null {
  const v = h[key];
  return typeof v === "string" ? v : null;
}

function Plot({ src }: { src: string }) {
  const file = src.split("/").pop() ?? "";
  const caption = ABOUT.plots[file];
  return (
    <figure className="m-0">
      <div
        className="overflow-hidden rounded"
        style={{ border: "var(--rule-w) solid var(--rule-200)", background: "var(--plot-ground)" }}
      >
        {/* Deliberately NOT loading="lazy". These mount inside a collapsed
            Radix disclosure, so they enter the DOM with no intrinsic height,
            never intersect the viewport, and never issue a request -- the
            images stayed blank at 0x0 while a fetch of the same URL returned
            43,061 bytes of image/png. The disclosure is the deferral: nothing
            here is fetched until a reader opens the section. */}
        <img
          src={src}
          alt={caption ?? file}
          className="block w-full"
          style={{ height: "auto" }}
        />
      </div>
      {caption && (
        <figcaption
          className="mt-2 text-ink-500"
          style={{ fontSize: "var(--t-body)" }}
        >
          {caption}
        </figcaption>
      )}
    </figure>
  );
}

function Headline({ tool }: { tool: ToolSummary }) {
  const h = (tool.headline ?? {}) as Record<string, unknown>;

  if (tool.id === "value") {
    const r2 = n(h, "cv_r2_mean");
    const sd = n(h, "cv_r2_std");
    const ef = n(h, "error_factor");
    const scheme = str(h, "cv_scheme") ?? "cross-validated";
    const bc = (h["band_coverage"] ?? {}) as Record<string, unknown>;
    const oof = n(bc, "out_of_fold");
    return (
      <>
        {r2 !== null && sd !== null && (
          <p className="text-ink-900"
            style={{ fontSize: "var(--t-body)" }}>
            {ABOUT.value.headline(num(r2, 3), num(sd, 3), scheme)}
          </p>
        )}
        {ef !== null && (
          <p className="mt-2 text-ink-700">
            {/* Both ends are computed from the served factor rather than typed
                in: 10M divided by it, and 10M multiplied by it. */}
            {ABOUT.value.band(
              num(ef, 2),
              eur(10_000_000 / ef),
              eur(10_000_000 * ef),
            )}
          </p>
        )}
        {oof !== null && (
          <p className="mt-2 text-ink-500">
            {ABOUT.value.coverage(pct(oof))}
          </p>
        )}
      </>
    );
  }

  if (tool.id === "match") {
    const acc = n(h, "accuracy");
    const sd = n(h, "accuracy_sd");
    const base = n(h, "baseline_accuracy");
    const f1 = n(h, "macro_f1");
    const scheme = str(h, "cv_scheme") ?? "";
    return (
      <>
        {acc !== null && sd !== null && base !== null && (
          <p className="text-ink-900"
            style={{ fontSize: "var(--t-body)" }}>
            {ABOUT.match.headline(
              num(acc, 3),
              num(sd, 3),
              num(base, 3),
              num(acc - base, 3),
            )}
          </p>
        )}
        {f1 !== null && (
          <p className="mt-2 text-ink-700">
            {ABOUT.match.f1(num(f1, 3), scheme)}
          </p>
        )}
        <p className="mt-2 text-ink-500" style={{ maxWidth: "68ch" }}>{ABOUT.match.theTrade}</p>
      </>
    );
  }

  const sil = n(h, "silhouette");
  const k = n(h, "k");
  const nPlayers = n(h, "n_players");
  return (
    <>
      {k !== null && nPlayers !== null && (
        <p className="text-ink-900"
            style={{ fontSize: "var(--t-body)" }}>{ABOUT.style.headline(k, nPlayers, 10)}</p>
      )}
      {sil !== null && (
        <p className="mt-2 text-ink-700">
          {ABOUT.style.silhouette(num(sil, 3))}
        </p>
      )}
    </>
  );
}

export function About() {
  const [meta, setMeta] = useState<AppMeta | null>(null);
  const [plots, setPlots] = useState<Record<string, string[]>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setError(String(e)));
    // The plot lists live on the per-tool metas rather than the aggregate,
    // because each is derived from that project's own plots directory.
    Promise.all([api.value.meta(), api.match.meta(), api.style.meta()])
      .then(([v, m, s]) =>
        setPlots({ value: v.plots, match: m.plots, style: s.plots }),
      )
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <Notice title="Backend unavailable">
        <p className="text-ink-700">
          {error}. The API should be running on 127.0.0.1:8000.
        </p>
      </Notice>
    );
  }

  if (!meta) {
    return (
      <Sheet>
        <p className="text-ink-500">Loading…</p>
      </Sheet>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-ink-900" style={{ fontSize: "var(--b-heading)" }}>
          How these models work, and where they fail
        </h1>
        <p className="mt-3 text-ink-500" style={{ maxWidth: "62ch" }}>
          {ABOUT.intro}
        </p>
      </div>

      {meta.tools.map((tool) => (
        <Section key={tool.id}>
          <div
            className="mb-4 flex flex-wrap items-baseline justify-between gap-3 pb-3"
            style={{ borderBottom: "2px solid var(--ink-900)" }}
          >
            <div>
              <h2 className="text-ink-900" style={{ fontSize: "var(--t-value)" }}>
                {tool.name}
              </h2>
              <div
                className="font-mono text-ink-300"
                style={{ fontSize: "var(--t-micro)" }}
              >
                {tool.technique}
              </div>
            </div>
            <Link
              to={TOOL_ROUTE[tool.id] ?? "/"}
              className="font-mono rounded px-3 py-1.5 text-ink-700"
              style={{
                fontSize: "var(--t-micro)",
                border: "var(--rule-w) solid var(--rule-200)",
              }}
            >
              open the tool →
            </Link>
          </div>

          {/* One measure for the whole reading, rather than a max-width on
              each paragraph. The detector measured 150-character lines here:
              this page's prose was running the full 1100px column. */}
          <div style={{ maxWidth: "68ch" }}>
            <Headline tool={tool} />
          </div>

          {/* The limitation is not tucked inside a disclosure. It is the half
              of the headline a reader is most likely to skip and least able
              to afford skipping (AGENTS.md §4). */}
          <div
            className="mt-5"
              style={{ borderTop: "var(--rule-w) solid var(--rule-200)", paddingTop: "var(--s-3)" }}
          >
            <div className="label mb-1">What it cannot do</div>
            <p className="text-ink-700" style={{ maxWidth: "68ch" }}>{tool.limitation}</p>
          </div>

          {(plots[tool.id] ?? []).length > 0 && (
            <div className="mt-6">
              <Disclosure
                label={`The evidence (${(plots[tool.id] ?? []).length} plots)`}
              >
                <div className="grid gap-6 md:grid-cols-2">
                  {(plots[tool.id] ?? []).map((p) => (
                    <Plot key={p} src={p} />
                  ))}
                </div>
              </Disclosure>
            </div>
          )}
        </Section>
      ))}

      <Section title="Licensing">
        <p className="text-ink-700" style={{ maxWidth: "68ch" }}>{ABOUT.licenceIntro}</p>
        <dl className="mt-4 grid gap-3">
          {[
            ["Code", meta.licensing.code],
            ["Player-scores data (01, 02)", meta.licensing.player_scores_data],
            ["Player-stats data (03)", meta.licensing.player_stats_data],
          ].map(([k, v]) => (
            <div
              key={k}
              className="grid gap-1 md:grid-cols-[minmax(0,18rem)_1fr]"
            >
              <dt className="label">{k}</dt>
              <dd
                className="font-mono m-0 text-ink-700"
                style={{ fontSize: "var(--t-body)" }}
              >
                {v}
              </dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-ink-500" style={{ maxWidth: "68ch" }}>{meta.licensing.note}</p>
      </Section>
    </div>
  );
}
