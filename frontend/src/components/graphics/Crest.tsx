/**
 * A club crest.
 *
 * PRODUCT.md records crests as an accepted decision. The artwork itself is not
 * in this repository and never has been -- no crest, logo or badge file is
 * tracked. So this renders real artwork when a file is present at
 * `/crests/<slug>.svg` and falls back to a typographic monogram otherwise.
 *
 * The fallback is not a placeholder to be replaced in a hurry. Initials set in
 * the display face inside a ruled square is what a printed almanac does when it
 * cannot print a badge, and it is honest in a way a grey box is not: it shows
 * the club, at the right size, in the right voice, without pretending to be a
 * logo it does not have.
 *
 * To supply real artwork: drop single-colour SVGs into `frontend/public/crests/`
 * named by the slug this component receives. Nothing else needs to change.
 */

import { useState } from "react";

/** "Arsenal FC" -> "arsenal-fc". Kept local and simple: this maps a display
 *  name to a filename, not a player to a database row, so it does not need the
 *  backend's transliteration rules. */
export function crestSlug(club: string): string {
  return club
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function monogram(club: string): string {
  const skip = new Set(["fc", "afc", "united", "city", "and", "hove", "the"]);
  const words = club
    .split(/\s+/)
    .filter((w) => !skip.has(w.toLowerCase().replace(/[^a-z]/gi, "")));
  const source = words.length ? words : club.split(/\s+/);
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
      title={club}
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
