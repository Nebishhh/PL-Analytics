/**
 * Project 02's mark: a fixed 100% rail split three ways, with a base-rate tick.
 *
 * The rail is FULL by definition, because the three probabilities sum to 1.
 * That is deliberate and load-bearing: a partially-filled bar would read as a
 * score out of 100, while a fully-divided one reads as a distribution, which
 * is what it is.
 *
 * THE BASE-RATE TICK IS THE MOST IMPORTANT MARK IN THIS TOOL.
 *   Project 02's headline finding is that the model beats always-guessing-home
 *   by 2.4 points. Putting that baseline on every individual forecast makes it
 *   structural rather than a README footnote -- a reader can see, per match,
 *   whether the model has an opinion or is restating the prior.
 *
 * Segment order is FIXED H, D, A and comes from the API's `order` field rather
 * than being sorted by value (DESIGN.md V5). A rail whose segments reorder
 * cannot be compared across matches.
 */

import { Rail, textureStyle, type Texture } from "./Rail";
import { pct } from "../../lib/format";

/**
 * TEXTURE, NOT THE SIGNAL RAMP -- this is the one place ink density must not
 * be used (AGENTS.md §3.3).
 *
 * Home, Draw and Away are CATEGORICAL. Shading them by weight would imply a
 * ranking the model never stated, which is the same misreading V5 prevents in
 * the spatial channel by fixing the order. A segment reading from `--signal-*`
 * is a violation even when its order is correct.
 *
 * Solid / hatched / open is the monochrome convention a printed chart uses for
 * categories, and every segment is labelled regardless.
 */
const SEGMENT_TEXTURE: Record<string, Texture> = {
  H: "solid",
  D: "hatched",
  A: "open",
};

interface Props {
  probabilities: Record<string, number>;
  /** Served, not inferred. See V5 above. */
  order: string[];
  labels: Record<string, string>;
  actual: string;
  baseline: number;
  baselineLabel: string;
}

export function DistributionRail({
  probabilities,
  order,
  labels,
  actual,
  baseline,
  baselineLabel,
}: Props) {
  let offset = 0;
  const segments = order.map((k) => {
    const p = probabilities[k] ?? 0;
    const seg = { key: k, from: offset, width: p, p };
    offset += p;
    return seg;
  });

  return (
    <div>
      <Rail
        ticks={[
          { at: 0, label: "0%" },
          { at: 0.5, label: "50%" },
          { at: 1, label: "100%" },
        ]}
        ariaLabel={
          order
            .map((k) => `${labels[k] ?? k} ${pct(probabilities[k] ?? 0)}`)
            .join(", ") +
          `. Actual outcome ${labels[actual] ?? actual}. ` +
          `Baseline ${pct(baseline)}.`
        }
      >
        {segments.map((s) => {
          const texture = SEGMENT_TEXTURE[s.key] ?? "open";
          const wide = s.width > 0.11;
          return (
            <div
              key={s.key}
              className="absolute inset-y-0 flex items-center justify-center font-mono"
              style={{
                left: `${s.from * 100}%`,
                width: `${s.width * 100}%`,
                ...textureStyle(texture),
                color: "var(--ink-900)",
                fontSize: "var(--t-micro)",
                fontWeight: 600,
                borderRight: "var(--rule-w) solid var(--ink-700)",
              }}
            >
              {wide ? `${s.key} ${pct(s.p)}` : ""}
            </div>
          );
        })}

        {/* The baseline. Drawn over the segments so it reads as a reference
            against them rather than as another quantity beside them. */}
        <div
          className="absolute inset-y-0"
          style={{
            left: `${baseline * 100}%`,
            width: "2px",
            marginLeft: "-1px",
            background: "var(--ink-900)",
          }}
        />
      </Rail>

      <div className="mt-2 flex items-start justify-between">
        <span
          className="font-mono text-ink-300"
          style={{ fontSize: "var(--t-micro)" }}
        >
          ▲ {pct(baseline)} — {baselineLabel}
        </span>
        <span
          className="font-mono text-ink-300"
          style={{ fontSize: "var(--t-micro)" }}
        >
          actual: {labels[actual] ?? actual}
        </span>
      </div>
    </div>
  );
}
