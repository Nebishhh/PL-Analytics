/**
 * Project 03's mark: a needle on a separation axis with the confidence
 * thresholds printed on the axis itself.
 *
 * This is the purest instrument idiom in the system -- a gauge with a red
 * zone. A reader who never reads a word can see that a needle at 0.042 sits
 * inside the contested band at the far left.
 *
 * THE ZONES ARE DATA, NOT CONSTANTS.
 *   `zones` comes from the API, which reads the thresholds from the artefact
 *   (they were moved there under AGENTS.md §0.1 precisely so a second consumer
 *   would not re-declare them). A frontend containing the literals 0.10 or
 *   0.50 has violated §2.3, so this component contains neither -- it renders
 *   whatever boundaries it is handed, and `state` on each zone maps straight
 *   onto the semantic scale so the client picks no colours either.
 */

import { Needle, Rail, signalInk, type MarkState } from "./Rail";
import { num } from "../../lib/format";

export interface AxisZone {
  name: string;
  /** The generated type names this `from`; kept verbatim. */
  from: number;
  to: number;
  state: MarkState;
}

interface Props {
  min: number;
  max: number;
  value: number;
  zones: AxisZone[];
  /** Which zone the needle actually falls in, for the aria description. */
  tier: string;
}

export function ZonedAxis({ min, max, value, zones, tier }: Props) {
  const span = max - min || 1;
  const pos = (v: number) => Math.min(1, Math.max(0, (v - min) / span));

  return (
    <div>
      <Rail
        ticks={[
          { at: 0, label: num(min, 2) },
          ...zones
            .slice(1)
            .map((z) => ({ at: pos(z.from), label: num(z.from, 2) })),
          { at: 0.98, label: num(max, 2) },
        ]}
        zones={zones.map((z) => ({
          from: pos(z.from),
          to: pos(z.to),
          label: z.name,
          state: z.state,
        }))}
        ariaLabel={`Separation ${num(value, 3)} of ${num(max, 2)}, in the ${tier.toLowerCase()} zone.`}
      >
        {zones.map((z) => (
          <div
            key={z.name}
            className="absolute inset-y-0"
            style={{
              left: `${pos(z.from) * 100}%`,
              width: `${(pos(z.to) - pos(z.from)) * 100}%`,
              background: signalInk(z.state),
              // Zones are context, not the reading. Kept faint so the needle
              // is what the eye lands on. Density and position agree here --
              // the axis is ordered left to right -- so the two channels
              // reinforce rather than compete (DESIGN.md §1).
              opacity: 0.30,
              borderRight: "var(--rule-w) solid var(--rule-200)",
            }}
          />
        ))}
        <Needle
          at={pos(value)}
          state={zones.find((z) => value >= z.from && value <= z.to)?.state ?? "absent"}
        />
      </Rail>

      <div
        className="mt-1 font-mono text-ink-500"
        style={{ fontSize: "var(--t-micro)" }}
      >
        separation {num(value, 3)}
      </div>
    </div>
  );
}
