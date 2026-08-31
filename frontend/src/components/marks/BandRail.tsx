/**
 * Project 01's mark: a tolerance band on a log scale, with the actual value
 * drawn as a distinct dot.
 *
 * Whether the actual lands inside the band is GEOMETRIC -- the reader sees it
 * before reading a word. The band's own colour is the verdict, which is why
 * `insideBand` is computed server-side rather than from client float
 * arithmetic (API.md §5).
 */

import { Band, Observed, Needle, Rail } from "./Rail";
import { eur, logPosition } from "../../lib/format";

interface Props {
  point: number;
  low: number;
  high: number;
  actual: number;
  insideBand: boolean;
}

export function BandRail({ point, low, high, actual, insideBand }: Props) {
  // Rail extent is derived from the data on screen, padded a decade either
  // side so the marks are never flush against the edge.
  const min = Math.min(low, actual) / 3;
  const max = Math.max(high, actual) * 3;
  const pos = (v: number) => logPosition(v, min, max);

  // The verdict. Inside is not "good" and outside is not "an error" -- both
  // are honest readings -- but outside is the one that qualifies the number,
  // so it carries the attention-getting state.
  const state = insideBand ? "strong" : "weak";

  const decades: { at: number; label: string }[] = [];
  for (let e = Math.ceil(Math.log10(min)); e <= Math.floor(Math.log10(max)); e++) {
    const v = 10 ** e;
    if (v >= 100_000) decades.push({ at: pos(v), label: eur(v) });
  }

  return (
    <div>
      <Rail
        ticks={decades}
        ariaLabel={
          `Estimated ${eur(point)}, band ${eur(low)} to ${eur(high)}. ` +
          `Actual ${eur(actual)}, ${insideBand ? "inside" : "outside"} the band.`
        }
      >
        <Band from={pos(low)} to={pos(high)} state={state} />
        <Needle at={pos(point)} state={state} />
        <Observed at={pos(actual)} />
      </Rail>

      <div className="mt-2 flex justify-between font-mono text-ink-300"
           style={{ fontSize: "var(--t-micro)" }}>
        <span>estimate {eur(point)}</span>
        <span>actual {eur(actual)}</span>
      </div>
    </div>
  );
}
