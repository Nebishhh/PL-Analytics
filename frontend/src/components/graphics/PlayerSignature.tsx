/**
 * A player's ten per-90 rates, drawn as a closed hairline figure.
 *
 * THIS IS BUILT FROM REAL DATA AND IS NOT DECORATION. Every vertex is that
 * player's percentile on one of the ten rates project 03 clusters on, in the
 * order the API serves them. Two players with the same shape have the same
 * profile; a spike is a real outlier. Nothing is smoothed, jittered or
 * stylised for looks.
 *
 * It is deliberately NOT one of the four marks. It carries no uncertainty and
 * makes no claim about confidence -- it is a portrait, and the reading beside
 * it is what states how much to trust the assignment. That distinction is why
 * it sits in graphics/ rather than marks/, and why it must never be used where
 * a reading is expected.
 *
 * Drawn in ink at hairline weight, like a figure in a printed paper: no fill
 * gradient, no glow, no hue (V14, V1).
 */

export interface Rate {
  key: string;
  label: string;
  percentile: number;
}

export function PlayerSignature({
  rates,
  size = 132,
  label,
}: {
  rates: Rate[];
  size?: number;
  /** Screen-reader description. Required: the figure is data, so it needs a
   *  text equivalent like every other data drawing here. */
  label: string;
}) {
  if (rates.length < 3) return null;

  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 12;

  const point = (i: number, frac: number) => {
    // Start at twelve o'clock and run clockwise, so the order a reader meets
    // the axes matches the order the rates are listed beside it.
    const a = (i / rates.length) * Math.PI * 2 - Math.PI / 2;
    const rad = r * Math.max(0.04, frac);
    return [cx + Math.cos(a) * rad, cy + Math.sin(a) * rad] as const;
  };

  const outline = rates
    .map((rate, i) => point(i, rate.percentile / 100))
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-label={label}
    >
      {/* Reference rings at the quartiles, so the outline is read against a
          scale rather than admired as a shape. */}
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <circle
          key={f}
          cx={cx}
          cy={cy}
          r={r * f}
          fill="none"
          stroke="var(--rule-200)"
          strokeWidth="0.5"
        />
      ))}
      {rates.map((rate, i) => {
        const [x, y] = point(i, 1);
        return (
          <line
            key={rate.key}
            x1={cx}
            y1={cy}
            x2={x}
            y2={y}
            stroke="var(--rule-100)"
            strokeWidth="0.5"
          />
        );
      })}
      <path
        d={`${outline} Z`}
        fill="var(--ink-900)"
        fillOpacity="0.08"
        stroke="var(--ink-900)"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {rates.map((rate, i) => {
        const [x, y] = point(i, rate.percentile / 100);
        return (
          <circle key={rate.key} cx={x} cy={y} r="1.6" fill="var(--ink-900)" />
        );
      })}
    </svg>
  );
}
