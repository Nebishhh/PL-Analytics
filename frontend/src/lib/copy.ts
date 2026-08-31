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

/** Keyed by `caveats[].key`. Only the ones that need no figure live here. */
export const VALUE_CAVEATS: Record<string, string> = {
  blind_spot:
    "The model has no club-quality or reputation signal, so it prices defenders and goalkeepers almost entirely on goals and assists, and under-values them as a result.",
};

/**
 * Resolve a caveat to a sentence, using the threshold the API now serves.
 *
 * The veteran caveat used to be a fixed string reading "past 40" while it
 * actually fires at `caveat_thresholds.veteran_age`, which is 38 — so a
 * 38-year-old was told about a problem beginning two years after the one that
 * had just been applied to him. It also asserted a "€300–500K" floor that no
 * artefact backs. Both numbers are gone: the trigger age comes from the model
 * and the unsourced one is not replaced with another guess.
 */
export function valueCaveat(c: {
  key: string;
  detail?: string | null;
  threshold?: number | null;
}): string {
  if (c.key === "veteran") {
    return typeof c.threshold === "number"
      ? `Past ${c.threshold}, the fitted age² curve keeps falling while real market values flatten out, so the oldest players are systematically under-estimated.`
      : // No threshold served: describe the shape without inventing an age.
        "At the top of the age range the fitted age² curve keeps falling while real market values flatten out, so the oldest players are systematically under-estimated.";
  }
  return VALUE_CAVEATS[c.key] ?? "";
}

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

/* -- /about ---------------------------------------------------------------- */

/**
 * The methodology page's prose.
 *
 * The headline sentences deliberately reuse the README's wording. The README
 * is where these claims were first made and argued; restating them differently
 * in the app would create two versions of the same finding, and the weaker one
 * would be whichever a reader saw second. Figures are still passed in from the
 * artefacts -- the sentences are shared, the numbers are not duplicated.
 *
 * Plot captions say what each image is EVIDENCE FOR, not what it depicts. A
 * caption reading "residuals by predicted value" tells a reader nothing they
 * could not see; the point of showing the committed PNGs at all is that they
 * are what the claims rest on (AGENTS.md §1.3).
 */
export const ABOUT = {
  intro:
    "Three models on Premier League data, each built to a different technique, and each shown here with what it cannot do alongside what it can. The figures below are read from the trained artefacts rather than written into this page, so they cannot drift from the models that produced them.",

  value: {
    headline: (r2: string, sd: string, scheme: string) =>
      `R² = ${r2} ± ${sd} (${scheme} cross-validation, log space).`,
    band: (factor: string, low: string, high: string) =>
      `Typical error ×${factor} — a €10M player is predicted somewhere between ${low} and ${high}.`,
    coverage: (pct: string) =>
      `The band holds the actual value for ${pct} of players, measured out of fold. Roughly two in five fall outside it.`,
  },

  match: {
    headline: (acc: string, sd: string, base: string, delta: string) =>
      `Accuracy ${acc} ± ${sd} against a ${base} always-predict-home-win baseline (+${delta}).`,
    f1: (f1: string, scheme: string) =>
      `Macro F1 ${f1}. ${scheme[0]?.toUpperCase()}${scheme.slice(1)}.`,
    theTrade:
      "Logistic regression is more accurate and is not what ships. It earns its higher accuracy substantially by declining to predict draws, and a model that has quietly reduced a three-outcome forecast to two is a worse product than a slightly less accurate one that attempts all three.",
  },

  style: {
    headline: (k: number, n: number, features: number) =>
      `k = ${k}, StandardScaler, ${n} players, ${features} per-90 features.`,
    silhouette: (s: string) =>
      `Overall silhouette ${s} — below 0.25, the conventional threshold for meaningful structure.`,
  },

  /** Keyed by the PNG filename the API serves, so a renamed plot loses its
   *  caption loudly rather than silently mislabelling a different image. */
  plots: {
    "07_residuals.png":
      "Where the error band comes from. The spread of residuals is what the band is sized to cover, which is why it is a typical miss rather than a bound.",
    "04_age_curve.png":
      "The fitted age² term. It keeps falling at the right-hand end while real market values floor out, which is why the oldest players carry a caveat.",
    "06_cv_results.png":
      "Fold-to-fold R². The headline figure is the mean of these, and their spread is how much precision to read into it.",
    "05_position_boxplot.png":
      "Value by position. Defenders and goalkeepers sit low and tight, which is the shape the model over-fits to when it has no reputation signal.",
    "01_target_distribution.png":
      "Why the target is logged. Raw market value is heavily right-skewed; the log is close to symmetric.",
    "02_correlation_heatmap.png":
      "Collinearity among the per-90 rates. This is what ruled out the two diff_gd columns, which were exactly diff_gf minus diff_ga.",
    "03_feature_scatters.png":
      "Each feature against the log target, before any fitting.",

    "01_confusion_matrices.png":
      "Draw-blindness, made visible. The draw row is where every model in this project loses — including the one that ships.",
    "02_accuracy_by_season.png":
      "Accuracy per held-out season against the always-home baseline. The gap between the two lines is the entire value the model adds.",

    "01_k_selection.png":
      "Silhouette against k. No value from 2 to 10 reaches 0.25, which is the finding, not a step on the way to one.",
    "04_pca_scatter.png":
      "The clusters in two principal components. They overlap, because they are regions of a continuous distribution rather than natural kinds.",
    "03_cluster_profiles.png":
      "The feature means each mechanically generated cluster name is derived from. No name here was written by hand.",
    "02_group_variance.png":
      "How much each feature group contributes to the fit. The shares are uneven, and equalising them reassigns a noticeable minority of players — which is what the group-normalised ARI figure above measures.",
  } as Record<string, string>,

  licenceIntro:
    "Three different things, under three different terms. The code licence makes no claim over either dataset.",
};

/* -- shared ---------------------------------------------------------------- */

export const COMMON = {
  positionHeldOut:
    "Position is shown for context only. It was held out of the clustering entirely — the whole point was to see whether grouping players by what they do would recover something the team sheet does not already say.",
};
