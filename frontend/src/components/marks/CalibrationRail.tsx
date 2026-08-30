/**
 * Project 01's refusal state, and the mark most systems get wrong.
 *
 * Two rails. The value rail renders hatched and empty -- there is no reading,
 * so nothing is drawn in it. Beneath it, a second rail shows the instrument's
 * CALIBRATED INPUT DOMAIN with this player marked outside it.
 *
 * That second rail is the whole idea: an instrument that shows its own
 * operating limits and where this input fell relative to them is making a
 * stronger honesty claim than any warning copy could. It turns a refusal from
 * an apology into a demonstration of competence (DESIGN.md §6b).
 *
 * Everything here is --state-null grey. Never red.
 */

import { Dot, Hatch, Rail, stateColor } from "./Rail";
import { eur, logPosition } from "../../lib/format";

interface Props {
  actual: number;
  field: string;
  value: number;
  minimum: number;
  domainMin: number;
  domainMax: number;
}

export function CalibrationRail({
  actual,
  field,
  value,
  minimum,
  domainMin,
  domainMax,
}: Props) {
  const vMin = actual / 10;
  const vMax = actual * 10;

  // The input rail spans from below this player's value to the domain max, so
  // the marker sits visibly outside the calibrated region rather than clamped
  // to the edge, which would understate how far outside it is.
  const inLo = Math.min(value, domainMin) * 0.8;
  const inHi = domainMax;
  const inPos = (v: number) => (v - inLo) / (inHi - inLo);

  return (
    <div className="space-y-5">
      <div>
        <Rail ariaLabel="No estimate: this player is outside the model's calibrated range.">
          <Hatch />
          <Dot at={logPosition(actual, vMin, vMax)} state="null" />
        </Rail>
        <div className="mt-2 flex justify-between font-mono text-ink-400"
             style={{ fontSize: "var(--t-micro)" }}>
          <span>no reading</span>
          <span>actual {eur(actual)}</span>
        </div>
      </div>

      <div>
        <div className="label mb-1">Calibrated range</div>
        <Rail
          ticks={[
            { at: inPos(domainMin), label: `${minimum.toLocaleString()}` },
            { at: 0.97, label: domainMax.toLocaleString() },
          ]}
          ariaLabel={
            `Calibrated for ${minimum} to ${domainMax} ${field}. ` +
            `This player has ${value}.`
          }
        >
          {/* The calibrated region, drawn so "outside" is a position rather
              than an assertion. */}
          <div
            className="absolute inset-y-0"
            style={{
              left: `${inPos(domainMin) * 100}%`,
              right: 0,
              background: "var(--ink-700)",
            }}
          />
          <div
            className="absolute inset-y-0"
            style={{
              left: `${inPos(value) * 100}%`,
              width: "var(--tick-w)",
              background: stateColor("null"),
            }}
          />
        </Rail>
        <div className="mt-2 font-mono text-ink-400"
             style={{ fontSize: "var(--t-micro)" }}>
          this player: {value.toLocaleString()} {field.replace(/_/g, " ")}
        </div>
      </div>
    </div>
  );
}
