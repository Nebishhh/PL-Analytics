/**
 * Structure for a printed page.
 *
 * REPLACES `Panel`, WHICH WAS THE PAGE STRUCTURE AND SHOULD NOT HAVE BEEN.
 * One container served controls, results, errors and licensing alike, and
 * nested inside itself on /about. V13 forbids both. The craft floor's phrasing
 * is that cards are the lazy container -- reaching for one is what an agent
 * does instead of deciding what a region actually is.
 *
 * A printed page separates regions with RULES AND SPACE, not with a stack of
 * floating rectangles. So there are three primitives here and they are not
 * interchangeable:
 *
 *   Section   a region of the page. A rule above it, space around it, no box.
 *             This is the default and should be what almost everything uses.
 *   Sheet     the one genuinely lifted surface, for a RESULT. Sparing by
 *             design: if two Sheets are visible at once, one of them is a
 *             Section that has not admitted it.
 *   Well      a recessed area for the controls a reader operates, so the
 *             instrument and its knobs are not the same object.
 */

import type { ReactNode } from "react";

export function Section({
  title,
  children,
  ruled = true,
}: {
  title?: string;
  children: ReactNode;
  /** A rule above the section. Off for the first section on a page, where a
   *  rule would fence the heading off from its own content. */
  ruled?: boolean;
}) {
  return (
    <section
      style={{
        borderTop: ruled ? "var(--rule-w) solid var(--rule-200)" : undefined,
        paddingTop: ruled ? "var(--s-5)" : undefined,
      }}
    >
      {title && <div className="label mb-3">{title}</div>}
      {children}
    </section>
  );
}

export function Sheet({
  children,
  animate = false,
}: {
  children: ReactNode;
  animate?: boolean;
}) {
  return (
    <section
      className={animate ? "panel-in" : undefined}
      style={{
        background: "var(--paper-000)",
        border: "var(--rule-w) solid var(--rule-100)",
        // The one place a rule is heavier than a hairline: the top edge of a
        // reading, the way a broadsheet rules off a table from the column
        // above it. It is ink, not the accent -- V12 keeps coloured edges off
        // callouts, and this is not a callout.
        borderTop: "2px solid var(--ink-900)",
        borderRadius: "var(--radius)",
        padding: "var(--s-5)",
      }}
    >
      {children}
    </section>
  );
}

export function Well({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        background: "var(--paper-200)",
        border: "var(--rule-w) solid var(--rule-100)",
        borderRadius: "var(--radius)",
        padding: "var(--s-4)",
      }}
    >
      {children}
    </div>
  );
}

/**
 * A failure the reader can act on. Not a Sheet, because it is not a reading,
 * and not a coloured callout, because V12 bans the border-left pattern that
 * every framework reaches for.
 */
export function Notice({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div
      style={{
        border: "var(--rule-w) solid var(--rule-200)",
        borderRadius: "var(--radius)",
        padding: "var(--s-4)",
        background: "var(--paper-000)",
      }}
    >
      <div className="label mb-2">{title}</div>
      {children}
    </div>
  );
}
