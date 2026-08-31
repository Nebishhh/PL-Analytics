/**
 * Club identity: one canonical name per real club, and its crest filename.
 *
 * Plain ESM, deliberately, so that the React component and the Node coverage
 * script import the SAME functions. Anything that resolves a club to a file or
 * to a set of initials goes through here — a second copy of these rules would
 * drift, and the first symptom would be a report confidently claiming a crest
 * exists that the page never asks for.
 *
 * WHY THERE IS AN ALIAS MAP AT ALL
 *   The two datasets name the same clubs differently. Project 01 carries
 *   Transfermarkt naming ("Arsenal FC"); project 03 carries FBref naming
 *   ("Arsenal"). Only 8 of the names match exactly, and 12 clubs appear under
 *   two spellings. Left unresolved that costs twice: 43 crest files for ~31
 *   clubs, and — the moment the Crest component is rendered anywhere, which the
 *   same change did — the same club showing different monogram initials in the
 *   Value tool than in the Style tool, because each would derive them from
 *   whichever name it was handed.
 *
 * WHY TRANSFERMARKT IS CANONICAL
 *   Not a coin flip: it is the superset. Project 01 spans the full history and
 *   names 31 clubs; project 03 is one season and names 20. Every FBref name
 *   resolves onto a Transfermarkt name, while 11 Transfermarkt clubs have no
 *   FBref counterpart at all. Mapping the smaller set into the larger leaves no
 *   name without a home; the reverse would strand eleven.
 *
 * This is a display-name rule. It is not the backend's player-slug rule and
 * needs none of its transliteration: these are English club names from one
 * league, not player names carrying ø and æ.
 */

/**
 * FBref spelling -> Transfermarkt spelling.
 *
 * Exhaustive against the current datasets: all 12 names that differ are here,
 * and `npm run crests` fails loudly if a new one appears, rather than silently
 * splitting a club into two rows again.
 */
export const CLUB_ALIASES = {
  Arsenal: "Arsenal FC",
  Bournemouth: "AFC Bournemouth",
  Brentford: "Brentford FC",
  Brighton: "Brighton & Hove Albion",
  Burnley: "Burnley FC",
  Chelsea: "Chelsea FC",
  Everton: "Everton FC",
  Fulham: "Fulham FC",
  Liverpool: "Liverpool FC",
  "Manchester Utd": "Manchester United",
  Sunderland: "Sunderland AFC",
  Wolves: "Wolverhampton Wanderers",
};

/**
 * The one name a club is known by, whichever dataset supplied it.
 *
 * Everything user-facing that identifies a club should pass through this, so a
 * club looks like one club across all three tools.
 *
 * @param {string} club
 * @returns {string}
 */
export function canonicalClub(club) {
  return CLUB_ALIASES[club] ?? club;
}

/**
 * Canonical club name -> crest filename stem.
 *
 * @param {string} club
 * @returns {string}
 */
export function crestSlug(club) {
  return canonicalClub(club)
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
