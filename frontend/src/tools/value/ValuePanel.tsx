/**
 * Project 01's reading, in both states.
 *
 * The refusal path is not an afterthought here: `ValueEstimate` is a
 * discriminated union, so TypeScript will not let this component reach
 * `estimate.point_eur` without first narrowing on `status`. Forgetting to
 * handle refusal is a compile error rather than a blank panel.
 *
 * Layout follows DESIGN.md §5's finding pattern, in order:
 *   mark -> state chip -> one sentence -> disclosure
 */

import type { ValueEstimate } from "../../lib/api";
import { eur, num, pct } from "../../lib/format";
import { BandRail } from "../../components/marks/BandRail";
import { CalibrationRail } from "../../components/marks/CalibrationRail";
import { Disclosure } from "../../components/ui/Disclosure";
import { MetricRow } from "../../components/ui/MetricRow";
import { Panel } from "../../components/ui/Panel";
import { StateChip } from "../../components/ui/StateChip";

/** `inputs` is an open record in the OpenAPI schema, so indexing it yields
 *  `number | undefined` under noUncheckedIndexedAccess. Rather than assert the
 *  key away, render an em dash: a field the backend stopped sending should
 *  show as absent, not as a confident zero. */
function input(inputs: Record<string, number>, key: string): string {
  const v = inputs[key];
  return v === undefined ? "—" : String(v);
}

function inputRate(inputs: Record<string, number>, key: string): string {
  const v = inputs[key];
  return v === undefined ? "—" : num(v);
}

const CAVEAT_TEXT: Record<string, string> = {
  blind_spot:
    "The model has no club-quality or reputation signal, so it prices defenders and goalkeepers almost entirely on goals and assists, and under-values them as a result.",
  veteran:
    "The fitted age² curve keeps falling past 40 while real values floor out around €300–500K, so the oldest players are systematically under-estimated.",
};

export function ValuePanel({
  data,
  bandCoverage,
}: {
  data: ValueEstimate;
  bandCoverage: number | null;
}) {
  const p = data.player;

  const header = (
    <div className="mb-6">
      <h2 className="text-ink-100" style={{ fontSize: "var(--t-value)" }}>
        {p.name}
      </h2>
      <div className="font-mono text-ink-300" style={{ fontSize: "var(--t-micro)" }}>
        {p.club} · {p.position}
        {p.sub_position ? ` (${p.sub_position})` : ""} · {num(p.age, 1)} yrs ·{" "}
        {p.pl_minutes.toLocaleString()} PL min
      </div>
    </div>
  );

  // --- refusal --------------------------------------------------------------
  // Reached only when status narrows to "not_calibrated". Grey throughout, and
  // the actual value is still shown: the app knows it, and withholding it
  // would be its own kind of dishonesty.
  if (data.status === "not_calibrated") {
    const c = data.calibration;
    return (
      <Panel>
        {header}
        <div className="mb-5">
          <div className="label mb-2">Estimate</div>
          <div className="font-mono text-ink-400" style={{ fontSize: "var(--t-figure)" }}>
            — not calibrated for this player
          </div>
        </div>

        <CalibrationRail
          actual={data.actual.market_value_eur}
          field={c.field}
          value={c.value}
          minimum={c.minimum}
          domainMin={c.domain_min}
          domainMax={c.domain_max}
        />

        <div className="mt-5 space-y-3">
          <StateChip state="null">Below calibrated range</StateChip>
          <p className="font-prose text-ink-200">
            Under {c.minimum.toLocaleString()} minutes the per-90 inputs stop
            measuring anything — one shot in three minutes reads as 30 shots per 90.
          </p>
          <Disclosure label="Why the model refuses rather than extrapolating">
            <p>
              Below roughly one season of football the per-90 rates are not rates,
              they are noise with a very small denominator. An earlier version of
              this model, given a player with 38 minutes and one assist, produced a
              prediction in the hundreds of billions of euros.
            </p>
            <p className="mt-3">
              The deeper reason is that players with limited minutes are priced on
              potential and transfer hype, which nothing in this feature set can
              observe. Refusing is the honest answer, not a gap to be filled.
            </p>
          </Disclosure>
        </div>
      </Panel>
    );
  }

  // --- reading --------------------------------------------------------------
  const e = data.estimate;
  const inside = data.actual.inside_band === true;

  return (
    <Panel>
      {header}

      <div className="mb-4">
        <div className="label mb-1">Estimate</div>
        <div className="font-mono text-ink-100" style={{ fontSize: "var(--t-value)" }}>
          {eur(e.low_eur)} – {eur(e.high_eur)}
        </div>
      </div>

      <BandRail
        point={e.point_eur}
        low={e.low_eur}
        high={e.high_eur}
        actual={data.actual.market_value_eur}
        insideBand={inside}
      />

      <div className="mt-5 space-y-3">
        <StateChip state={inside ? "clear" : "low"}>
          {inside ? "Actual inside band" : "Actual outside band"}
        </StateChip>

        {/* One sentence. It does not restate what the mark already shows -- the
            band's geometry says whether the actual fell inside it -- so this
            says why, or what it means. */}
        <p className="font-prose text-ink-200">
          {data.caveats.length > 0
            ? CAVEAT_TEXT[data.caveats[0]!.key]
            : `A ×${e.error_factor} band around ${eur(e.point_eur)}, which is the typical size of a miss rather than a bound.`}
        </p>

        <Disclosure label="What the band means, and what it does not">
          <p>
            The ×{e.error_factor} range is a <em>typical-error</em> band, not a
            confidence interval.
            {bandCoverage !== null && (
              <>
                {" "}
                The actual value lands inside it for {pct(bandCoverage)} of
                players, measured out of fold — so roughly two in five fall
                outside.
              </>
            )}
          </p>
          <p className="mt-3">
            The model predicts log value, so the figure shown is a conditional
            median rather than a mean. These estimates should not be summed to
            value a squad without a smearing correction.
          </p>
          {data.caveats.length > 1 &&
            data.caveats.slice(1).map((c) => (
              <p className="mt-3" key={c.key}>
                {CAVEAT_TEXT[c.key]}
              </p>
            ))}
        </Disclosure>
      </div>

      <div className="mt-6 border-t pt-5" style={{ borderColor: "var(--ink-700)" }}>
        <div className="label mb-3">Inputs the model used</div>
        <MetricRow
          items={[
            { label: "PL matches", value: p.pl_matches.toLocaleString() },
            { label: "PL minutes", value: p.pl_minutes.toLocaleString() },
            { label: "Goals", value: input(data.inputs, "pl_goals") },
            { label: "Assists", value: input(data.inputs, "pl_assists") },
          ]}
        />
        <div className="mt-4">
          <MetricRow
            items={[
              { label: "Goals / 90", value: inputRate(data.inputs, "goals_per90") },
              { label: "Assists / 90", value: inputRate(data.inputs, "assists_per90") },
              { label: "Yellow cards", value: input(data.inputs, "pl_yellow_cards") },
              { label: "Red cards", value: input(data.inputs, "pl_red_cards") },
            ]}
          />
        </div>
      </div>
    </Panel>
  );
}
