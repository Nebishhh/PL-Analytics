/**
 * Project 02's reading, in both states.
 *
 * `HeldOutForecast` is a discriminated union, so reaching `forecast.probabilities`
 * without narrowing on `status` is a compile error. The out-of-scope branch
 * cannot be skipped.
 */

import type { HeldOutForecast, ToolMeta } from "../../lib/api";
import { pct } from "../../lib/format";
import { MATCH } from "../../lib/copy";
import { DistributionRail } from "../../components/marks/DistributionRail";
import { Disclosure } from "../../components/ui/Disclosure";
import { MetricRow } from "../../components/ui/MetricRow";
import { Panel } from "../../components/ui/Panel";
import { StateChip } from "../../components/ui/StateChip";

function quality(meta: ToolMeta | null) {
  const q = (meta?.quality ?? {}) as Record<string, unknown>;
  const perClass = q.per_class as
    | Record<string, { precision: number; recall: number; f1: number }>
    | undefined;
  return {
    accuracy: typeof q.accuracy === "number" ? q.accuracy : null,
    drawRecall: perClass?.D?.recall ?? null,
  };
}

export function MatchPanel({
  data,
  meta,
}: {
  data: HeldOutForecast;
  meta: ToolMeta | null;
}) {
  const m = data.match;
  const q = quality(meta);

  const header = (
    <div className="mb-6">
      <h2 className="text-ink-100" style={{ fontSize: "var(--t-value)" }}>
        {m.home_club} <span className="text-ink-400">v</span> {m.away_club}
      </h2>
      <div
        className="font-mono text-ink-300"
        style={{ fontSize: "var(--t-micro)" }}
      >
        {m.date} · season {m.season}
        {m.matchday ? ` · matchday ${m.matchday}` : ""}
      </div>
    </div>
  );

  // --- out of scope ---------------------------------------------------------
  // Reached only when status narrows. No forecast is invented: a uniform 1/3
  // split would look like a prediction while carrying no information.
  if (data.status === "out_of_scope") {
    const c = data.coverage;
    return (
      <Panel>
        {header}
        <div className="mb-5">
          <div className="label mb-2">Forecast</div>
          <div
            className="font-mono text-ink-400"
            style={{ fontSize: "var(--t-figure)" }}
          >
            — no held-out forecast for this match
          </div>
        </div>

        <div className="space-y-3">
          <StateChip state="null">{MATCH.outOfScopeChip}</StateChip>
          <p className="font-prose text-ink-200">
            {MATCH.outOfScopeReasons[c.reason_key] ??
              "No held-out forecast exists for this match."}
          </p>
          <Disclosure label="Which matches have a forecast, and why the rest do not">
            <p>
              {MATCH.outOfScopeDetail(c.matches_available, c.matches_total)}
            </p>
            <p className="mt-3">
              Seasons {c.seasons_available[0]}–{c.seasons_available[1]} are
              covered.
            </p>
          </Disclosure>
        </div>

        <div
          className="mt-6 border-t pt-5"
          style={{ borderColor: "var(--ink-700)" }}
        >
          <MetricRow
            items={[
              {
                label: "Actual result",
                value: data.actual.outcome,
                sub: "shown for reference only",
              },
            ]}
          />
        </div>
      </Panel>
    );
  }

  // --- reading --------------------------------------------------------------
  const f = data.forecast;
  const correct = data.actual.top_pick_correct === true;
  const labels = f.labels;

  return (
    <Panel>
      {header}

      <div className="mb-4">
        <div className="label mb-1">Forecast</div>
        <div
          className="font-mono text-ink-100"
          style={{ fontSize: "var(--t-value)" }}
        >
          {f.order
            .map((k) => `${k} ${pct(f.probabilities[k] ?? 0)}`)
            .join("  ·  ")}
        </div>
      </div>

      <DistributionRail
        probabilities={f.probabilities}
        order={f.order}
        labels={labels}
        actual={data.actual.outcome}
        baseline={data.baseline.always_home_accuracy}
        baselineLabel={data.baseline.label}
      />

      <div className="mt-5 space-y-3">
        <StateChip state={correct ? "clear" : "low"}>
          {correct ? "Top pick correct" : "Top pick wrong"}
        </StateChip>

        {/* The finding is the standing caveat, not a verdict on this match.
            One correct forecast is not evidence of skill (DESIGN.md V9). */}
        <p className="font-prose text-ink-200">
          {q.drawRecall !== null
            ? MATCH.drawBlindSpot(pct(q.drawRecall))
            : correct
              ? MATCH.correct
              : MATCH.incorrect(
                  labels[f.top_pick] ?? f.top_pick,
                  labels[data.actual.outcome] ?? data.actual.outcome,
                )}
        </p>

        <Disclosure label="What this forecast is, and what the tick means">
          <p>{MATCH.heldOutExplainer(f.trained_on_seasons)}</p>
          {q.accuracy !== null && (
            <p className="mt-3">
              {MATCH.baselineExplainer(
                pct(data.baseline.always_home_accuracy),
                pct(q.accuracy),
              )}
            </p>
          )}
          <p className="mt-3">
            {correct ? MATCH.correct : MATCH.incorrect(
              labels[f.top_pick] ?? f.top_pick,
              labels[data.actual.outcome] ?? data.actual.outcome,
            )}
          </p>
        </Disclosure>
      </div>

      {data.form && (
        <div
          className="mt-6 border-t pt-5"
          style={{ borderColor: "var(--ink-700)" }}
        >
          <div className="label mb-3">Form before kickoff</div>
          <div className="grid gap-6 md:grid-cols-2">
            {(["home", "away"] as const).map((side) => {
              const s = data.form?.[side];
              return (
                <div key={side}>
                  <div className="label mb-2">
                    {side === "home" ? m.home_club : m.away_club}
                  </div>
                  <MetricRow
                    items={[
                      {
                        label: "Points / game",
                        value: s?.pre_ppg?.toFixed(2) ?? "—",
                      },
                      {
                        label: "Position",
                        value: s?.pre_position?.toFixed(0) ?? "—",
                      },
                      {
                        label: "Rest days",
                        value: s?.rest_days?.toFixed(0) ?? "—",
                      },
                    ]}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Panel>
  );
}
