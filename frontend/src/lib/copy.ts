/**
 * Every piece of prose that qualifies a reading, for all three tools, in one
 * place.
 *
 * WHY THIS MODULE EXISTS
 *   The API sends keys, not sentences -- `caveats[].key`, `tier`,
 *   `reason_key`, `status` -- and the copy lives here so it can be reviewed as
 *   copy rather than buried in JSX. AGENTS.md §4 is explicit that caveats are
 *   the product and must never be trimmed to reduce visual noise, which is
 *   easier to hold to when the wording is visible in one file.
 *
 *   The keys are namespaced by tool but the module is shared deliberately. The
 *   model figures nearly drifted across four files before §2.3 pushed them
 *   into the artefacts; wording will drift the same way if each tool grows its
 *   own map. A reader moving between tools should meet one voice.
 *
 * WHAT DOES NOT BELONG HERE
 *   Numbers. Every figure -- thresholds, coverage, baselines, silhouette --
 *   comes from the artefacts via the API (AGENTS.md §2.3). Where a sentence
 *   needs one, it takes it as an argument rather than embedding a literal.
 */

/* -- 01 value -------------------------------------------------------------- */

/** Keyed by `caveats[].key` from the API. */
export const VALUE_CAVEATS: Record<string, string> = {
  blind_spot:
    "The model has no club-quality or reputation signal, so it prices defenders and goalkeepers almost entirely on goals and assists, and under-values them as a result.",
  veteran:
    "The fitted age² curve keeps falling past 40 while real values floor out around €300–500K, so the oldest players are systematically under-estimated.",
};

export const VALUE = {
  /** Shown when no caveat applies. Takes the figures rather than embedding them. */
  defaultFinding: (factor: number, point: string) =>
    `A ×${factor} band around ${point}, which is the typical size of a miss rather than a bound.`,

  refusalChip: "Below calibrated range",

  refusalFinding: (minimum: number) =>
    `Under ${minimum.toLocaleString()} minutes the per-90 inputs stop measuring anything — one shot in three minutes reads as 30 shots per 90.`,

  refusalDetail: [
    "Below roughly one season of football the per-90 rates are not rates, they are noise with a very small denominator. An earlier version of this model, given a player with 38 minutes and one assist, produced a prediction in the hundreds of billions of euros.",
    "The deeper reason is that players with limited minutes are priced on potential and transfer hype, which nothing in this feature set can observe. Refusing is the honest answer, not a gap to be filled.",
  ],

  bandDetail:
    "The model predicts log value, so the figure shown is a conditional median rather than a mean. These estimates should not be summed to value a squad without a smearing correction.",

  bandCoverage: (pct: string) =>
    `The actual value lands inside it for ${pct} of players, measured out of fold — so roughly two in five fall outside.`,
};

/* -- 02 match -------------------------------------------------------------- */

export const MATCH = {
  /** The finding beside every forecast. Draw-blindness is the standing caveat,
   *  so it is stated on each reading rather than only in the methodology. */
  drawBlindSpot: (recallPct: string) =>
    `Draws are the model's blind spot: it finds only ${recallPct} of the ones that happen, so a low draw probability is weak evidence that a draw will not occur.`,

  /** Never claims skill from a single case (DESIGN.md V9). */
  correct:
    "The model's most likely outcome was the one that happened — though one correct forecast is not evidence of skill.",
  incorrect: (predicted: string, actual: string) =>
    `The model's top pick was ${predicted.toLowerCase()}; the match ended in a ${actual.toLowerCase()}.`,

  baselineExplainer: (baselinePct: string, accuracyPct: string) =>
    `The tick marks ${baselinePct}, the accuracy of always predicting a home win. The model reaches ${accuracyPct} overall, so the gap between the two is the entire value it adds.`,

  outOfScopeChip: "No held-out forecast",

  /** Keyed by `coverage.reason_key`. */
  outOfScopeReasons: {
    no_prior_seasons_to_train_on:
      "This match is from a season the model could not be tested on. Every forecast here comes from a model trained only on earlier seasons, and the first five have no earlier seasons to learn from.",
  } as Record<string, string>,

  outOfScopeDetail: (available: number, total: number) =>
    `${available.toLocaleString()} of ${total.toLocaleString()} matches have a held-out forecast. The rest are not shown with a guess, because a fabricated even split would look like a prediction while carrying no information.`,

  heldOutExplainer: (seasons: string) =>
    `This forecast came from a model trained on ${seasons} only, which had never seen this season. Predicting a match the model was trained on would report it as far more accurate than it is.`,
};

/* -- 03 style -------------------------------------------------------------- */

/**
 * NOTE ON THE MINUTES FLOOR, so it is not silently re-hardcoded.
 *
 * The 315 players here all cleared a 900-minute filter, but that figure is
 * deliberately absent from this tool's copy, because the frontend has no
 * honest source for it. It lives in `03-style-finder/clean.py` as
 * `MIN_MINUTES` and is not carried into the artefact.
 *
 * That absence is correct rather than an oversight. In project 01 the
 * equivalent constant (`MIN_PL_MINUTES`) is a refusal boundary the serving
 * code enforces on every request, so the artefact must carry it. Here it is a
 * historical data filter with no runtime role -- the model never refuses, and
 * all 315 players have an assignment. Recording it under model.joblib would
 * imply an enforcement that does not exist.
 *
 * If the number is ever wanted on screen, read it from clean.py via importlib
 * (it imports only pathlib/numpy/pandas, so unlike app.py it is importable)
 * and expose it through /api/style/meta. Do not type it into a component.
 */
export const STYLE = {
  /** Keyed by `assignment.tier`. Two to four words -- these are chip labels,
   *  not sentences (DESIGN.md §5). */
  tierChip: {
    CONTESTED: "Contested",
    BORDERLINE: "Borderline",
    PLACED: "Reasonably placed",
  } as Record<string, string>,

  negativeSilhouetteChip: "Sits with another cluster",

  /** For a contested assignment the rival is named FIRST, because leading with
   *  the assignment asserts what the geometry does not support. */
  contestedWithNegative: (rival: string) =>
    `Nearly as close to “${rival}” — and sits among that cluster's members rather than its own.`,
  contested: (rival: string, margin: string) =>
    `Nearly as close to “${rival}”: only ${margin} further away.`,
  borderline: (rival: string, margin: string) =>
    `“${rival}” is only ${margin} further away — not a decisive placement.`,
  placed: (rival: string, margin: string) =>
    `“${rival}” is ${margin} further away — a clear placement.`,

  negativeSilhouetteDetail: (silhouette: string, n: number, total: number) =>
    `Per-player silhouette is ${silhouette}, which is negative. That is a different problem from a narrow margin: the assigned centroid may be nearest, but the players actually around this one mostly belong to a different group, so the assigned cluster should not be read as descriptive at all. ${n} of ${total} players are in this position.`,

  twoSignals:
    "Margin asks whether another centroid is nearly as close — geometry. Silhouette asks whether the player sits closer to another cluster's members than his own — density. They are near-independent, so a margin-only rule would show players with a comfortable margin and a negative silhouette as confidently assigned.",

  positionAdjacent: (share: string, dominant: string) =>
    `This cluster mostly restates position: ${share} of its members are listed ${dominant} first. It is one of the two clusters that track the team sheet closely, which is also why it separates comparatively well — being placed here says little beyond what the position column already told you.`,

  positionMixed: (share: string, dominant: string) =>
    `This cluster does not simply restate position. Its members are ${share} ${dominant}-first but it mixes positions substantially, grouping players by what they do rather than where they line up. That is the part of this clustering that adds something beyond the team sheet, and it is also the least well separated, so treat the grouping as suggestive rather than settled.`,

  namingDetail:
    "Names are generated mechanically by comparing each cluster's feature means against the quartiles of all players — never written by hand. Terms like “inverted winger” or “deep-lying playmaker” are claims about passing, carrying and positioning, and this dataset has none of those columns.",

  weakStructure: (silhouette: string) =>
    `Overall silhouette is ${silhouette}, and no k from 2 to 10 reaches 0.25 — the conventional threshold for meaningful structure. These are regions of a continuous distribution, not natural kinds.`,
};

/* -- shared ---------------------------------------------------------------- */

export const COMMON = {
  positionHeldOut:
    "Position is shown for context only. It was held out of the clustering entirely — the whole point was to see whether grouping players by what they do would recover something the team sheet does not already say.",
};
