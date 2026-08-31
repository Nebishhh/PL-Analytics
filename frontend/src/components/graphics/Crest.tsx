/**
 * A club crest.
 *
 * THE MONOGRAM IS THE DESIGN, NOT A PLACEHOLDER. No crest artwork ships and
 * none is pending. Initials set in the display face inside a ruled square is
 * what a printed almanac does when it cannot print a badge, and it is honest in
 * a way a traced approximation is not: it shows the club, at the right size, in
 * the right voice, without claiming to be a logo it is not.
 *
 * Using crests was a settled decision; sourcing failed. Current crests are not
 * on Wikimedia Commons, English Wikipedia's copies are non-free, and historical
 * public-domain marks cover only some clubs in mismatched styles. The full
 * evaluation is in `public/crests/MANIFEST.md`, recorded there so this file
 * does not read as work someone forgot to finish.
 *
 * The loading path below is an escape hatch, not a TODO. If a licensable,
 * consistent set ever appears, drop single-colour SVGs into
 * `frontend/public/crests/` named by `crestSlug()` and they are used with no
 * code change.
 */

import { useState } from "react";
import { canonicalClub, crestSlug } from "../../lib/crestSlug.mjs";

export { crestSlug };

function monogram(club: string): string {
  const skip = new Set(["fc", "afc", "united", "city", "and", "hove", "the"]);
  const words = canonicalClub(club)
    .split(/\s+/)
    // A token that is nothing but punctuation is not a word. Without this the
    // ampersand in "Brighton & Hove Albion" survived as its own token and the
    // monogram read "B&".
    .map((w) => ({ raw: w, letters: w.replace(/[^a-z]/gi, "") }))
    .filter((w) => w.letters.length > 0 && !skip.has(w.letters.toLowerCase()))
    .map((w) => w.letters);
  const source = words.length ? words : canonicalClub(club).split(/\s+/);
  return source
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

export function Crest({ club, size = 22 }: { club: string; size?: number }) {
  const [failed, setFailed] = useState(false);
  const src = `/crests/${crestSlug(club)}.svg`;

  if (!failed) {
    return (
      <img
        src={src}
        alt=""
        width={size}
        height={size}
        onError={() => setFailed(true)}
        style={{ display: "block", objectFit: "contain" }}
      />
    );
  }

  return (
    <span
      aria-hidden
      className="font-display inline-flex items-center justify-center"
      title={canonicalClub(club)}
      style={{
        width: size,
        height: size,
        border: "var(--rule-w) solid var(--rule-200)",
        borderRadius: "var(--radius)",
        color: "var(--ink-500)",
        fontSize: Math.round(size * 0.44),
        lineHeight: 1,
        letterSpacing: "0.02em",
      }}
    >
      {monogram(club)}
    </span>
  );
}
