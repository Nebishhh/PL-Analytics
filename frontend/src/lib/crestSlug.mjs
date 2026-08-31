/**
 * Club display name -> crest filename.
 *
 * Plain ESM, deliberately, so that BOTH the React component and the Node
 * progress script import the same function. A crest report that computed slugs
 * with its own copy of this rule would drift from the app the first time either
 * changed, and would then confidently tell you a crest was present that the
 * page never asks for -- or missing when it is fine.
 *
 * This maps a display name to a filename. It is not the backend's player-slug
 * rule and does not need its transliteration table: these are 20 English club
 * names from one league, not player names with ø and æ in them.
 *
 * @param {string} club
 * @returns {string}
 */
export function crestSlug(club) {
  return club
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
