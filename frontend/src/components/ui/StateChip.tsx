/**
 * A state marker. Two to four words, never a sentence.
 *
 * DESIGN.md §5: the chip is the one glanceable thing. The sentence beside it
 * carries the single most important qualification; everything else goes behind
 * a disclosure. A chip containing a clause has taken the sentence's job.
 */

import type { MarkState } from "../marks/Rail";
import { stateColor } from "../marks/Rail";

export function StateChip({
  state,
  children,
}: {
  state: MarkState;
  children: React.ReactNode;
}) {
  const c = stateColor(state);
  return (
    <span
      className="inline-block rounded-full font-mono"
      style={{
        color: c,
        border: `1px solid ${c}`,
        background: `color-mix(in srgb, ${c} 14%, transparent)`,
        fontSize: "var(--t-label)",
        padding: "3px 10px",
        letterSpacing: "0.04em",
      }}
    >
      {children}
    </span>
  );
}
