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
import { VALUE, VALUE_CAVEATS } from "../../lib/copy";
import { BandRail } from "../../components/marks/BandRail";
import { CalibrationRail } from "../../components/marks/CalibrationRail";
import { Disclosure } from "../../components/ui/Disclosure";
import { MetricRow } from "../../components/ui/MetricRow";
import { Sheet } from "../../components/ui/Sheet";
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
      <h2 className="text-ink-900" style={{ fontSize: "var(--t-value)" }}>
        {p.name}
      </h2>
      <div className="font-mono text-ink-500" style={{ fontSize: "var(--t-micro)" }}>
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
      <Sheet animate>
        {header}
        <div className="mb-5">
          <div className="label mb-2">Estimate</div>
          <div className="font-mono text-ink-300" style={{ fontSize: "var(--t-figure)" }}>
            —
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
          <StateChip state="absent">{VALUE.refusalChip}</StateChip>
          <p className="finding">
            {VALUE.refusalFinding(c.minimum)}
          </p>
          <Disclosure label="Why the model refuses rather than extrapolating">
            {VALUE.refusalDetail.map((para, i) => (
              <p key={para.slice(0, 24)} className={i > 0 ? "mt-3" : undefined}>
                {para}
              </p>
            ))}
          </Disclosure>
        </div>
      </Sheet>
    );
  }

  // --- reading --------------------------------------------------------------
  const e = data.estimate;
  const inside = data.actual.inside_band === true;

  return (
    <Sheet animate>
      {header}

      <div className="mb-4">
        <div className="label mb-1">Estimate</div>
        <div className="font-mono text-ink-900" style={{ fontSize: "var(--t-value)" }}>
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
        <StateChip state={inside ? "strong" : "weak"}>
          {inside ? "Actual inside band" : "Actual outside band"}
        </StateChip>

        {/* One sentence. It does not restate what the mark already shows -- the
            band's geometry says whether the actual fell inside it -- so this
            says why, or what it means. */}
        <p className="finding">
          {data.caveats.length > 0
            ? VALUE_CAVEATS[data.caveats[0]!.key]
            : VALUE.defaultFinding(e.error_factor, eur(e.point_eur))}
        </p>

        <Disclosure label="What the band means, and what it does not">
          <p>
            The ×{e.error_factor} range is a <em>typical-error</em> band, not a
            confidence interval.
            {bandCoverage !== null && (
              <> {VALUE.bandCoverage(pct(bandCoverage))}</>
            )}
          </p>
          <p className="mt-3">{VALUE.bandDetail}</p>
          {data.caveats.length > 1 &&
            data.caveats.slice(1).map((c) => (
              <p className="mt-3" key={c.key}>
                {VALUE_CAVEATS[c.key]}
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
    </Sheet>
  );
}
