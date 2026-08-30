/**
 * The shared rail. Every uncertainty mark in this app is drawn on this one
 * primitive, at one height, with one radius.
 *
 * That is the whole reason three tools read as one instrument rather than
 * three dashboards sharing a nav bar: a tolerance band, a probability split
 * and a separation axis are different statistics, but rendering them at
 * different heights makes a reader parse them as different kinds of object
 * (DESIGN.md §3).
 *
 * COLOUR IS NOT AN ARGUMENT HERE. Marks accept a semantic `state` and resolve
 * it internally. There is no `color` prop and no `className` that reaches the
 * SVG fill, so a tool accent has no route into a data mark even as an inline
 * style -- DESIGN.md V1 enforced by the component's shape rather than by
 * review.
 */

import type { ReactNode } from "react";

export type MarkState = "clear" | "moderate" | "low" | "null";

const STATE_VAR: Record<MarkState, string> = {
  clear: "var(--state-clear)",
  moderate: "var(--state-moderate)",
  low: "var(--state-low)",
  // Grey, never red. Refusal is the instrument working correctly, and an
  // error colour would teach the reader that "no answer" is a failure.
  null: "var(--state-null)",
};

export function stateColor(state: MarkState): string {
  return STATE_VAR[state];
}

export interface RailProps {
  /** Tick labels along the axis, positioned 0..1 left to right. */
  ticks?: { at: number; label: string }[];
  /** Drawn inside the trough, in rail-local coordinates (0..1 horizontally). */
  children?: ReactNode;
  /** Zone strip beneath the rail, e.g. project 03's threshold bands. */
  zones?: { from: number; to: number; label: string; state: MarkState }[];
  ariaLabel: string;
}

export function Rail({ ticks, children, zones, ariaLabel }: RailProps) {
  return (
    <div className="w-full">
      {ticks && ticks.length > 0 && (
        <div className="relative h-4 w-full">
          {ticks.map((t) => (
            <span
              key={`${t.at}-${t.label}`}
              className="absolute font-mono text-ink-300 -translate-x-1/2"
              style={{ left: `${t.at * 100}%`, fontSize: "var(--t-micro)" }}
            >
              {t.label}
            </span>
          ))}
        </div>
      )}

      <div
        role="img"
        aria-label={ariaLabel}
        className="relative w-full overflow-hidden"
        style={{
          height: "var(--rail-h)",
          borderRadius: "var(--rail-radius)",
          background: "var(--ink-800)",
          border: "1px solid var(--ink-700)",
        }}
      >
        {children}
      </div>

      {zones && zones.length > 0 && (
        <div
          className="relative w-full"
          style={{ height: "var(--zone-label-h)" }}
        >
          {zones.map((z) => (
            <span
              key={z.label}
              className="absolute font-mono whitespace-nowrap"
              style={{
                left: `${z.from * 100}%`,
                fontSize: "var(--t-micro)",
                color: stateColor(z.state),
                paddingLeft: "2px",
              }}
            >
              {z.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/** A filled region of the trough, 0..1. */
export function Band({
  from,
  to,
  state,
}: {
  from: number;
  to: number;
  state: MarkState;
}) {
  const c = stateColor(state);
  return (
    <div
      className="absolute inset-y-0"
      style={{
        left: `${from * 100}%`,
        width: `${Math.max(0, to - from) * 100}%`,
        background: c,
        opacity: 0.18,
        borderLeft: `1px solid ${c}`,
        borderRight: `1px solid ${c}`,
      }}
    />
  );
}

/** The measured value. Does not bounce or overshoot: an instrument that
 *  oscillates looks uncertain about its own reading, and the uncertainty here
 *  belongs to the band, not the needle (DESIGN.md §10). */
export function Needle({ at, state }: { at: number; state: MarkState }) {
  return (
    <div
      className="absolute inset-y-0"
      style={{
        left: `${at * 100}%`,
        width: "var(--tick-w)",
        marginLeft: "calc(var(--tick-w) / -2)",
        background: stateColor(state),
      }}
    />
  );
}

/** A second, visually distinct mark. Used for the actual observed value, so
 *  prediction and reality are never confused for one another. */
export function Dot({ at, state }: { at: number; state: MarkState }) {
  return (
    <div
      className="absolute top-1/2 rounded-full"
      style={{
        left: `${at * 100}%`,
        width: "var(--mark-dot)",
        height: "var(--mark-dot)",
        transform: "translate(-50%, -50%)",
        background: stateColor(state),
        boxShadow: "0 0 0 2px var(--ink-900)",
      }}
    />
  );
}

/** Out of calibrated range: hatched, empty, grey. There is no reading. */
export function Hatch() {
  return (
    <div
      className="absolute inset-0"
      style={{
        backgroundImage:
          "repeating-linear-gradient(45deg, var(--ink-600) 0 1px, transparent 1px 6px)",
        opacity: 0.7,
      }}
    />
  );
}
