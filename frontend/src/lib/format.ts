/** Display formatting. No thresholds or model figures live here -- those come
 *  from the artefacts via the API (AGENTS.md §2.3). */

/** Euros at a readable magnitude. Values span EUR100k to EUR200m, so a single
 *  format string cannot serve the whole range. */
export function eur(value: number): string {
  if (value >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  return `€${Math.round(value / 1_000).toLocaleString()}K`;
}

export function pct(fraction: number, digits = 0): string {
  return `${(fraction * 100).toFixed(digits)}%`;
}

/** 1st, 2nd, 3rd... 11th/12th/13th are the exceptions. */
export function ordinal(n: number): string {
  const r100 = n % 100;
  if (r100 >= 11 && r100 <= 13) return `${n}th`;
  const suffix = { 1: "st", 2: "nd", 3: "rd" }[n % 10] ?? "th";
  return `${n}${suffix}`;
}

export function num(value: number, digits = 2): string {
  return value.toFixed(digits);
}

/** Position on a log10 rail, 0..1.
 *
 *  The value rail is logarithmic and that is not a style choice: on a linear
 *  axis a EUR33.8M estimate and a EUR100M actual sit almost on top of each
 *  other, and everything below EUR20M compresses into nothing. DESIGN.md V6
 *  forbids a linear scale here, and the API sends `scale: "log10"` so a client
 *  rendering it linearly is contradicting a field it was handed. */
export function logPosition(value: number, min: number, max: number): number {
  const lo = Math.log10(Math.max(min, 1));
  const hi = Math.log10(Math.max(max, 10));
  const v = Math.log10(Math.max(value, 1));
  return Math.min(1, Math.max(0, (v - lo) / (hi - lo)));
}
