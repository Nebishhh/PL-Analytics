/**
 * The shared rail. Every uncertainty mark in this app is drawn on this one
 * primitive, at one height (V8).
 *
 * That is the whole reason three tools read as one instrument rather than
 * three dashboards sharing a nav bar: a tolerance band, a probability split
 * and a separation axis are different statistics, but rendering them at
 * different heights makes a reader parse them as different kinds of object.
 *
 * COLOUR IS NOT AN ARGUMENT HERE. Marks accept a semantic `state` and resolve
 * it internally. There is no `color` prop and no `className` that reaches a
 * fill, so the accent has no route into a data mark even as an inline style --
 * V1 enforced by the component's shape rather than by review.
 *
 * The four states are ORDINAL and are drawn in ink density, not hue. See
 * AGENTS.md §3.2 before reaching for colour here: confidence is one dimension
 * with an order, hue is the channel for categorical data, and the previous
 * system spent three hues saying one thing while putting alarm-red on the
 * readings where the model is being most honest.
 */

import type { ReactNode } from "react";

export type MarkState = "strong" | "qualified" | "weak" | "absent";

const SIGNAL: Record<MarkState, string> = {
  strong: "var(--signal-3)",
  qualified: "var(--signal-2)",
  weak: "var(--signal-1)",
  // Absence has no ink. It is drawn as an empty trough and set as an em-dash
  // where the figure would be -- the convention a statistical abstract uses,
  // which no reader mistakes for an error.
  absent: "transparent",
};

export function signalInk(state: MarkState): string {
  return SIGNAL[state];
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
        <div className="relative mb-1 h-4 w-full">
          {ticks.map((t) => (
            <span
              key={`${t.at}-${t.label}`}
              className="font-mono absolute -translate-x-1/2 text-ink-300"
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
          borderRadius: "var(--radius)",
          background: "var(--paper-200)",
          border: "var(--rule-w) solid var(--rule-200)",
        }}
      >
        {children}
      </div>

      {zones && zones.length > 0 && (
        // A legend, not labels floating over the bands. Positioning each label
        // at its zone's start collided as soon as a zone was narrower than its
        // own name -- the contested band is 3.6% of this axis -- and a printed
        // chart has always solved that with a key underneath.
        <div
          className="font-mono mt-1 flex flex-wrap gap-x-4 gap-y-1 text-ink-500"
          style={{ fontSize: "var(--t-micro)" }}
        >
          {zones.map((z) => (
            <span key={z.label} className="inline-flex items-center gap-1.5">
              <span
                aria-hidden
                style={{
                  width: "10px",
                  height: "10px",
                  background: signalInk(z.state),
                  opacity: 0.32,
                  border: "var(--rule-w) solid var(--rule-200)",
                }}
              />
              {z.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * A stated tolerance, drawn the way an engineering dimension line states one:
 * a filled span with a serif cap at each end.
 *
 * The caps matter. Without them a band fades into its trough and reads as a
 * gradient of plausibility, which is the opposite of what a ×1.75 typical-error
 * band means -- it has two definite ends and the model is not more confident in
 * the middle of it.
 */
export function Band({
  from,
  to,
  state,
}: {
  from: number;
  to: number;
  state: MarkState;
}) {
  const ink = signalInk(state);
  return (
    <>
      <div
        className="absolute inset-y-0"
        style={{
          left: `${from * 100}%`,
          width: `${Math.max(0, to - from) * 100}%`,
          background: ink,
          opacity: 0.16,
        }}
      />
      {[from, to].map((at, i) => (
        <div
          key={i}
          className="absolute inset-y-0"
          style={{
            left: `${at * 100}%`,
            width: "var(--rule-w)",
            marginLeft: "calc(var(--rule-w) / -2)",
            background: ink,
          }}
        />
      ))}
    </>
  );
}

/**
 * The measured value. Does not bounce or overshoot: an instrument that
 * oscillates looks uncertain about its own reading, and the uncertainty here
 * belongs to the band, not the needle.
 */
export function Needle({ at, state }: { at: number; state: MarkState }) {
  return (
    <div
      className="absolute inset-y-0"
      style={{
        left: `${at * 100}%`,
        width: "2px",
        marginLeft: "-1px",
        background: signalInk(state),
      }}
    />
  );
}

/**
 * The observed value, drawn open rather than filled so prediction and reality
 * are never confused for one another. An outline against a printed ground is
 * how a chart distinguishes a plotted observation from a fitted line.
 */
export function Observed({ at }: { at: number }) {
  return (
    <div
      className="absolute top-1/2"
      style={{
        left: `${at * 100}%`,
        width: "9px",
        height: "9px",
        transform: "translate(-50%, -50%)",
        borderRadius: "50%",
        border: "1.5px solid var(--ink-900)",
        background: "var(--paper-100)",
      }}
    />
  );
}

/**
 * Fill textures for CATEGORICAL segments -- project 02's Home / Draw / Away.
 *
 * These must never take the signal ramp. H, D and A are categories, not an
 * ordered scale, and shading them by weight would imply a ranking the model
 * never stated (V5, AGENTS.md §3.3). Solid, hatched and open is the monochrome
 * convention a printed chart uses for exactly this.
 */
export type Texture = "solid" | "hatched" | "open";

export function textureStyle(texture: Texture): React.CSSProperties {
  switch (texture) {
    case "solid":
      return { background: "var(--ink-700)", opacity: 0.85 };
    case "hatched":
      return {
        backgroundImage:
          "repeating-linear-gradient(45deg, var(--ink-700) 0 1px, transparent 1px 5px)",
      };
    case "open":
      return { background: "transparent" };
  }
}

/** The input's position when it falls outside the calibrated span. */
export function OutOfRange({ at }: { at: number }) {
  return (
    <div
      className="font-mono absolute top-1/2 text-ink-500"
      style={{
        left: `${at * 100}%`,
        transform: "translate(-50%, -50%)",
        fontSize: "var(--t-body)",
      }}
      aria-hidden
    >
      ×
    </div>
  );
}
