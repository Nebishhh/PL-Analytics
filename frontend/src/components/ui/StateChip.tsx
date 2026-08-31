/**
 * A state marker. Two to four words, never a sentence.
 *
 * The chip is the one glanceable thing. The sentence beside it carries the
 * single most important qualification; everything else goes behind a
 * disclosure. A chip containing a clause has taken the sentence's job.
 *
 * It is set in ink density like every other confidence signal, not in a hue.
 * The WORD is what carries the state here -- "Contested" says more, and says
 * it to a screen reader too, than any colour could. Density reinforces the
 * word; it does not replace it.
 */

import type { MarkState } from "../marks/Rail";
import { signalInk } from "../marks/Rail";

/** Absence gets the trough's rule rather than an ink fill, so a refusal chip
 *  reads as an empty field rather than as a filled state. */
const BORDER: Record<MarkState, string> = {
  strong: "var(--signal-3)",
  qualified: "var(--signal-2)",
  weak: "var(--signal-1)",
  absent: "var(--rule-200)",
};

export function StateChip({
  state,
  children,
}: {
  state: MarkState;
  children: React.ReactNode;
}) {
  // The word is always set in readable ink. Density lives on the border.
  // Colouring the LABEL by confidence put "Contested" at 2.15:1 against the
  // sheet -- the least readable word on the page was the one warning you not
  // to trust the reading, which is the exact inversion this system exists to
  // avoid.
  const ink = "var(--ink-900)";
  return (
    <span
      className="font-mono inline-block"
      style={{
        color: ink,
        border: `var(--rule-w) solid ${BORDER[state]}`,
        borderRadius: "var(--radius)",
        background: "var(--paper-000)",
        fontSize: "var(--t-label)",
        padding: "3px 9px",
        letterSpacing: "0.04em",
      }}
    >
      {state !== "absent" && (
        <span
          aria-hidden
          className="mr-1.5 inline-block align-middle"
          style={{
            width: "7px",
            height: "7px",
            background: signalInk(state),
            border: "var(--rule-w) solid var(--rule-200)",
          }}
        />
      )}
      {children}
    </span>
  );
}
