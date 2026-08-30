# PL-Analytics

Three progressively harder machine learning projects built on Transfermarkt
football data, working up from regression to classification to unsupervised
clustering.

| # | Project | Technique | Status |
|---|---------|-----------|--------|
| 01 | **value-predictor** | Linear regression | Complete, with a Streamlit app for interactive predictions |
| 02 | **match-predictor** | Classification | Complete, with a Streamlit app for match forecasts |
| 03 | **style-finder** | K-Means clustering | Complete |

---

## Data

Source: [davidcariboo/player-scores](https://www.kaggle.com/datasets/davidcariboo/player-scores)
on Kaggle — a Transfermarkt scrape, CC0-1.0 licensed. 12 CSVs, 219MB
compressed, covering 50,149 players and 1.89M individual match appearances
across 31 domestic leagues from 2012 onward.

`03-style-finder` uses a **second dataset**:
[hubertsidorowicz/football-players-stats-2025-2026](https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2025-2026)
— per-90 and season-total stats for the top five European leagues, 2,839 players,
**MIT licensed** (not CC0 — see [Licensing](#licensing)). It goes in a subdirectory
to avoid filename collisions with the player-scores CSVs:

```bash
python -m kaggle datasets download -d hubertsidorowicz/football-players-stats-2025-2026 -p data/raw/football-players-stats-2025-2026 --unzip
```

`data/raw/` is gitignored, so you need to fetch both yourself.

### Reproducing `data/raw/`

Get a Kaggle API token from your
[account settings](https://www.kaggle.com/settings) (Create New Token), which
downloads `kaggle.json`. Put it where the CLI expects it:

```bash
mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json && chmod 600 ~/.kaggle/kaggle.json
```

Then:

```bash
pip install kaggle
python -m kaggle datasets download -d davidcariboo/player-scores -p data/raw --unzip
```

`python -m kaggle` rather than the bare `kaggle` command, because pip's
user-level script directory is often not on PATH.

Derived tables **are** committed, so you can run the EDA, the models and the app
without downloading anything:

- `pl_player_values.csv` — 498 rows, project 01's modelling table (≥900 PL minutes)
- `pl_player_values_prethreshold.csv` — 661 rows, backs the app's player list
  so that below-threshold players can be shown *why* they get no prediction
  rather than silently not existing
- `pl_matches_features.csv` — 4,616 rows, project 02's match table
- `pl_player_profiles.csv` — 315 rows, project 03's activity-profile table

You only need `data/raw/` if you want to re-run `clean.py` or change a filter.

---

## 01-value-predictor

Predicts a Premier League player's current market value in EUR from their
career-to-date Premier League appearance record.

```bash
python 01-value-predictor/clean.py   # data/raw -> data/processed (498 rows)
python 01-value-predictor/eda.py     # diagnostic plots + collinearity report
python 01-value-predictor/model.py   # 5-fold CV: Linear vs Ridge vs Lasso
python 01-value-predictor/train_final.py   # fit the shipping model -> model.joblib
streamlit run 01-value-predictor/app.py    # interactive app
```

### Result

**R² = 0.727 ± 0.054** (5-fold cross-validation, log space)
**Typical error ×1.75** — a €10M player is predicted somewhere between €5.7M
and €17.5M.

Cross-validation rather than a single holdout: at n=498 one split tells you
very little. Fold-to-fold R² still ranges 0.646 to 0.811 even after the fixes
below, and an unlucky split would have made this look far worse or far better
than it is. Reordering the rows — same data, different fold assignment — moves
the headline figure by ±0.002, which is a fair measure of how much precision
to read into it.

| Model | R² (log) | Median abs. error |
|-------|----------|-------------------|
| Linear | 0.727 ± 0.054 | €6.06M |
| Ridge | 0.726 ± 0.058 | €6.14M |
| Lasso | 0.727 ± 0.056 | €6.15M |

The three are indistinguishable — the spread is far inside the fold noise.
Ridge selects α ≈ 0.17 and Lasso zeroes out no features, meaning both are
declining to regularise. **Plain `LinearRegression` is what ships.**

### Modelling decisions

Each of these is an explicit choice, documented in the module docstrings.

**Scope: Premier League only (`GB1`).** Applied on both sides — the player's
current club must be in the Premier League, and only PL appearances count
toward the performance features. The dataset covers 31 leagues; market values
are not comparable across them without a league-strength feature.

**Active-player criterion: `last_season` in {2024, 2025}.** The target is a
*current* snapshot value, so retired and inactive players simply lose it.
Null-target rate runs 3–5% for players last seen in 2012–2020 but climbs to
58.8% for 2024. Training on non-null rows across all seasons would silently
mean "players still active today" without ever saying so. This makes the
population explicit rather than letting missingness define it.

**Minimum 900 Premier League minutes.** The most consequential filter, for two
reasons.

*Arithmetic:* per-90 rates are `events × 90 / minutes`, which at low minutes
are not rates but noise. One player had 38 PL minutes and 1 assist —
`assists_per90` = 2.37, a z-score of 17.7, where Haaland's `goals_per90` is
0.91. A linear model in log space extrapolated that into a **€981 billion**
prediction.

*Substantive, and more important:* sub-500-minute players are academy and
fringe signings priced on potential and transfer hype. No appearance-derived
feature can see that. They are not noisy measurements of a signal — they are
unmodellable from this data.

| Threshold | n | R² |
|-----------|---|-----|
| none | 661 | 0.158 ± 0.161 |
| ≥ 450 min | 535 | 0.641 ± 0.059 |
| **≥ 900 min** | **498** | **0.663 ± 0.061** |
| ≥ 1800 min | 423 | 0.725 ± 0.034 |

900 over 1800 is a deliberate trade: 1800 scores better but drops another 75
players and starts selecting for "established starter", narrowing what the
model can be asked about. Shrinking the rates toward the league mean instead
of thresholding only reached 0.27.

**Log target.** Raw market value has skew 2.29 and kurtosis 8.80; log has skew
−0.77. Predictions are exponentiated back to EUR for reporting. Note that
`exp(mean prediction in log space)` is the conditional *median*, not the mean,
so these predictions should not be summed to value a squad without a smearing
correction.

**age² feature.** Value follows an inverted U — geometric mean rises from €4.6M
at 18–20 to €18.3M at 26–28, then falls to €0.35M by 38–40. A single linear age
term has to draw a straight line through that curve. Adding age² is worth
**+0.076 R²** (0.651 → 0.727), consistent across all three models.

**Dropped as leakage:** `highest_market_value_in_eur` is a direct function of
the target.

**Parked for v1:** `foot`, `height_in_cm`, `contract_expiration_date`.

### The app

```bash
streamlit run 01-value-predictor/app.py
```

Pick a player, get an estimate. Optional club and position dropdowns narrow
the list before the name search — useful at 661 options, where "every
centre-back at Arsenal" is not a question a plain name box can answer. Both
default to "All".

Three deliberate constraints, each one a limitation made visible rather than
hidden:

**The player list is closed.** 661 real players, no free-text stat entry. A form
accepting "42 goals in 300 minutes" would return a confident number for a
player who cannot exist.

**Below 900 minutes, the app refuses.** 163 of the 661 players get an
explanation instead of a number. They are in the dropdown *precisely* so the
refusal is visible — removing them would hide the limitation instead of
communicating it.

**Estimates are always a range, never a point.** A point estimate of €10M is
shown as €5.7M–€17.5M. The app also says whether the real value fell inside
that range, and flags the two known failure modes (ageing veterans, and
under-predicted defenders and goalkeepers) when they apply.

One caveat on the range itself: ×1.75 is a *typical-error* band, not a
confidence interval. The actual value falls inside it for 59% of players.

### Known limitations

**No club-quality or reputation signal.** This is the ceiling. The feature set
knows how many minutes a player has played and how many goals they scored, and
nothing about who they play for or how good they are. Consequences:

- **Elite defenders, holding midfielders and goalkeepers are systematically
  under-predicted**, because their value has almost nothing to do with goals
  and assists. Martín Zubimendi (€75M) predicts at €13M; Gianluigi Donnarumma
  (€45M) at €9.4M; Lisandro Martínez (€40M) at €9.8M.
- **Ageing veterans are under-predicted.** The fitted age² curve keeps falling
  past 40 while real values floor out around €300–500K. James Milner (40.6,
  €500K) predicts at €29K.
- **Goalkeepers clear the minutes threshold on far fewer appearances** than
  outfielders, since they play 90 minutes whenever they play at all.

R² ≈ 0.73 is roughly the ceiling here. Getting past it needs club strength or
share-of-available-minutes, not more model tuning.

**Survivorship bias is limited, not eliminated.** The 2024/2025 filter removes
the retiree problem, but 170 of 973 Premier League players still have a null
target and are dropped. Those are mostly youth and fringe players Transfermarkt
has not priced, and their absence is not random.

**Market value is an estimate, not a transfer fee.** Transfermarkt values are
community-driven appraisals. This model predicts *those appraisals*, which are
themselves influenced by reputation and hype.

---

## 02-match-predictor

Predicts Premier League Win/Draw/Loss from the home team's perspective, using
only information knowable days before kickoff.

```bash
python 02-match-predictor/features.py      # raw CSVs -> 4,616-match table
python 02-match-predictor/model.py         # 5 models x 2 CV schemes
python 02-match-predictor/train_final.py   # fit shipping model -> model.joblib
streamlit run 02-match-predictor/app.py    # interactive app
```

### Result

**Accuracy 0.470 ± 0.031** against a **0.446 always-predict-home-win baseline**
(+0.024). **Macro F1 0.429.** Season-based expanding-window CV, 9 folds.

| Model | Accuracy | vs baseline | Macro F1 | Draw recall |
|-------|----------|-------------|----------|-------------|
| Dummy (always home) | 0.446 ± 0.032 | — | 0.205 | 0.00 |
| Logistic regression | **0.512** ± 0.036 | +0.066 | 0.416 | 0.11 |
| LogReg, balanced | 0.422 ± 0.043 | −0.024 | 0.417 | 0.59 |
| HistGradientBoosting | 0.476 ± 0.026 | +0.030 | 0.413 | 0.19 |
| **HGB, balanced** *(shipped)* | 0.470 ± 0.031 | +0.024 | **0.429** | 0.26 |

**Logistic regression is more accurate and is not what ships.** It earns its
51.2% substantially by declining to predict draws — 317 draw predictions across
2,967 test matches when 697 draws occurred. For a Win/Draw/Loss forecast, a model
that has quietly reduced the problem to two classes is a worse product than a
slightly less accurate one that attempts all three. HGB-balanced has the best
macro F1, the metric that refuses to let draw-blindness hide, and still beats the
baseline. A deliberate trade of 4.2 accuracy points.

Results were checked under a second scheme (`TimeSeriesSplit(n_splits=5)`), which
agrees on ordering and magnitude to within ~0.01. No conclusion here depends on
where the fold boundaries fall.

### Leakage: the thing this project is really about

`games.csv` is booby-trapped, and the traps are not obvious.

**`aggregate` is the final score as a string.** It equals `"{home_goals}:{away_goals}"`
in 5,320 of 5,320 Premier League rows.

**`home_club_position` is the league position *after* the match.** This one is
subtle enough to be worth the detail. Position varies within a club-season — 6.74
distinct values on average, only 1 of 280 club-seasons constant — which makes it
look like legitimate point-in-time data. It is point-in-time; it is just the wrong
point. Rebuilding the table at every date across 10,640 club-match rows and
comparing:

| Reconstruction | Agreement with the recorded column |
|---|---|
| Rank **including** the match | **69.4%** |
| Rank **excluding** the match | 40.5% |

A model given that column is being told, in part, whether the home team just won.
League position is instead rebuilt from prior results only.

**`club_games.is_win` cannot express a draw** — all 2,538 drawn club-games carry
`is_win = 0`, identical to losses.

**`attendance` and formation columns are excluded by choice.** Neither is caused by
the result, but the prediction boundary here is "known days before kickoff", not
"known at kickoff", and team sheets fail that test.

### Features

All derived from prior matches only; rolling windows are shifted by one so no match
enters its own features. Rolling points, goals for/against over the last 5 and 10
matches; separate home and away form; rebuilt pre-match league position; rest days
computed across **all** competitions (a midweek cup tie is real fatigue); head-to-head
history; season one-hot.

Season form enters as **points per game**, not accumulated points. Raw totals
correlate 0.761 with matchday — thirty points is top-four in October and mid-table in
March. Per-game rates drop that to 0.022.

The first 5 matchdays of each club-season are dropped rather than carrying form across
the summer, costing 704 of 5,320 matches (13.2%).

### The app

```bash
streamlit run 02-match-predictor/app.py
```

Pick a season, optionally a club, then a fixture. Same visual language as
project 01.

**Every forecast shown is out of sample.** The app reads `oof_predictions.csv`,
where each match was predicted by a model trained only on the seasons before it
— not `model.joblib` live. This is not a detail: every match in the feature table
is in the shipped model's training set, where it scores 0.980, so an app calling
`predict_proba` directly would show the top pick as correct **98%** of the time
for a model whose real accuracy is **47%**. No caption undoes a factor-of-two
misrepresentation. The cost is seasons 2012–2016, which have no prior seasons to
train on and are therefore not selectable; the app covers 2,967 of the 4,616
matches.

**All three probabilities are always shown**, as a divided bar, never collapsed
to a single predicted class. A 41/26/33 split is a coin-flip, not a verdict.
The fixture dropdown deliberately omits the score, so the model speaks before
the answer is visible.

### Known limitations

**The model has learned home advantage and relative form, and has learned nothing
about draws.** Draw precision sits at 0.26 in every configuration tested. The balanced
variants change only how *often* draws are guessed, not how well: LogReg-balanced lifts
draw recall from 0.11 to 0.59 and falls *below* the dummy on accuracy, predicting 1,600
draws where 697 occurred. Draws have no distinctive feature signature — they happen
between evenly matched teams, which is a region of feature space rather than a
direction in it. Worth noting what it *does* get right: across the 2,967 matches
in the app it predicts 682 draws against 686 that actually occurred. It has the
right *number* of draws and the wrong *ones*.

**The ceiling is low and this is near it.** Max eta-squared across every engineered
feature is 0.132; nothing separates these classes strongly. Match outcomes are
substantially irreducible without market odds or squad-strength signals. +2.4 points
over baseline is a real but modest gain and is reported as such.

**Multicollinearity is severe but harmless here.** Seven features exceed VIF 10, topping
out at 31.7. Coefficients are not individually interpretable. An `l10`-only variant was
tested and scored *worse* (0.507 vs 0.512), so the full feature set stands.

**HGB fits the training set almost exactly at library defaults** — in-sample accuracy
0.980 against cross-validated 0.470. This is expected behaviour for gradient boosting
with an unconstrained depth, not a defect, and it does not affect any number reported
here: every figure quoted is cross-validated, and the shipped artefact stores those
rather than anything measured in-sample. What the gap does indicate is *where* tuning
would pay off — regularisation (`max_depth`, `min_samples_leaf`, `l2_regularization`)
rather than more capacity. That is scheduled as the first item under
[Future work](#future-work-deliberately-deferred) below, not an outstanding problem
with this result.

**Home advantage is non-stationary.** It ranges 39% (2020, empty stadiums) to 50%
(2016). Season dummies absorb the level shift. Notably, 2020 is where the models beat
the dummy by the *widest* margin (+0.076) — the dummy collapses when home advantage
evaporates while the models hold near 46%.

### Future work, deliberately deferred

- **HGB hyperparameter tuning** — the train/test gap noted above points at
  regularisation specifically. Must be nested inside the training fold, or the CV
  estimate stops meaning anything.
- **Draws as a distinct problem** — an ordinal or two-stage "decisive vs draw, then
  which side" formulation may suit them better than flat 3-class.

Neither was attempted in this pass. Chasing a better number with ad hoc tuning after
seeing the results is how CV estimates become fiction.

---

## 03-style-finder

Groups Premier League outfielders into activity archetypes with K-Means, then
checks the result against the position label it was never shown.

```bash
python 03-style-finder/clean.py         # raw CSV -> 315-player table
python 03-style-finder/cluster.py       # scaling, k selection, stability, naming
python 03-style-finder/train_final.py   # fit and persist -> model.joblib + assignments
```

### Result

**k = 4**, StandardScaler, 315 players, 10 per-90 features.

| # | n | Mechanically generated name | Silhouette |
|---|---|---|---|
| 0 | 51 (16%) | High goals, shots, shot accuracy; low interceptions, tackles won | **0.250** |
| 1 | 114 (36%) | Low involvement — below average across all three groups (mean z −0.35), no feature in either quartile | 0.233 |
| 2 | 86 (27%) | High tackles won, fouls, yellow cards | **0.101** |
| 3 | 64 (20%) | High assists, crosses, fouls drawn | **0.136** |

Most central player in each: Ollie Watkins, Diogo Dalot, Marc Cucurella,
Marcus Tavernier.

### The clustering is least trustworthy exactly where it is most interesting

This is the finding, and it comes from cross-referencing the silhouette column
above against the position validation.

**Cluster 0 largely rediscovers a position.** It holds 27 of the 28 pure forwards
(96%). Cluster 1 captures 73% of all defenders. Those two are close to the team
sheet — and they are the two best-separated clusters, at 0.250 and 0.233.

**Clusters 2 and 3 are the ones that add something.** Both are midfield-plurality
but capture only 38% and 34% of midfielders respectively, and cluster 2 holds 25
defenders alongside 41 midfielders. They split defenders and midfielders by *what
they do* — high tackling and fouling versus high crossing and assisting — rather
than where they line up. That is the only part of this result that goes beyond
`Pos`.

**And they are the weakest-separated clusters, at 0.101 and 0.136.** Cluster 2
alone contains 15 of the 19 players whose silhouette is negative.

So the parts of the partition that merely restate the team sheet are solid, and
the parts that carry genuine information are the shakiest. That is not a bug to
fix; it is what the data supports, and it is the single most important thing to
know before using these labels for anything.

### Silhouette never exceeds 0.24 — this project's "nothing beats the dummy"

Project 02 asked whether any model beat a 45.2% always-home-win baseline. The
answer was yes, modestly. **The equivalent question here gets a much weaker
answer.**

| k | Inertia drop | Silhouette |
|---|---|---|
| 2 | — | **0.237** |
| 3 | 11.8% | 0.171 |
| **4** | 11.1% | **0.180** |
| 5 | 6.3% | 0.164 |
| 8 | 4.1% | 0.155 |

**No k from 2 to 10 reaches 0.25**, the conventional threshold for meaningful
structure. K-Means always returns k clusters — that is what the algorithm does, and
a partition existing is not evidence that natural groups exist. Here it is largely
**imposing divisions on a continuous cloud**, which the PCA scatter shows directly:
one blob, not four islands.

The output is still a useful summary of how Premier League minutes get spent. It is
not a discovery of natural archetypes, and nothing in this repo describes it as one.

### Clustering decisions

**k = 4, chosen against two metrics that disagree.** Elbow points at 4 — inertia
drops 11.8% and 11.1%, then halves to 6.3%. Silhouette peaks at **k = 2**.

k=2 is **rejected despite scoring best**, because it is near-trivial: it puts 28 of
28 pure forwards on one side and 96 of 96 pure defenders on the other. It wins by
rediscovering the team sheet. Choosing it would mean optimising a metric into a
non-finding.

**Stability breaks the tie.** Mean adjusted Rand index across 8 seeds:

| k | Mean ARI | Min ARI |
|---|---|---|
| 4 | **0.966** | 0.925 |
| 5 | 0.792 | **0.565** |

At k=5 clusters genuinely dissolve and re-form depending on initialisation. k=4 is
the largest k that holds together.

**StandardScaler over RobustScaler**, for a stronger reason than matching projects
01 and 02. StandardScaler sets unit variance by construction, so the distance
metric's weighting *is* the feature count — nothing hidden:

| Scaler | Attacking | Defensive | Discipline | Heaviest feature |
|---|---|---|---|---|
| **StandardScaler** | 50.00% | 20.00% | 30.00% | all exactly 10.00% |
| RobustScaler | 52.74% | 18.38% | 28.88% | `att_gls_p90` 14.74% |

RobustScaler makes the group imbalance *worse* and layers a second, opaque weighting
on top of it — while barely touching the skew it would be adopted for
(`att_gls_p90` max |z| 4.63 → 4.56). The skew is moderate (1.60 and 1.78), nothing
like project 01's z = 17.7 that would justify a robust scaler.

**Group imbalance: reported, not corrected.** `ATTACKING_OUTPUT` holds 5 of the 10
features and therefore carries **50% of the distance metric**. Two players differing
sharply in defensive activity are treated as more similar than two differing equally
in attacking output.

A group-normalised variant (each group divided by √group size, equalising
contribution at 33/33/33) agrees at **ARI 0.835** — meaning **roughly one player in
six lands in a different cluster** when the weighting changes. The clusters are
robust in shape but not in membership. The standard-weighted fit still ships,
because equalising groups is itself an arbitrary choice rather than a neutral
correction.

**Per-90 rates only, no raw counts.** Even after the 900-minute floor, minutes span
901 to 3,420, and raw counts inherit it — `Int` correlates 0.636 with minutes,
`TklW` 0.582. Per-90 removes nearly all of it (`Int` → 0.152, `TklW` → −0.010).
Including both forms would repeat project 01's `pl_matches`/`pl_minutes` problem,
except that in K-Means the consequence is a silently doubled weight rather than an
unstable coefficient.

Filter chain: 2,839 → **551** (Premier League) → **511** (goalkeepers excluded, their
stat profile is disjoint) → **315** (≥900 minutes, same threshold and same reason as
project 01).

### Activity profiles, not playing styles

The goal was corrected, and the correction is carried in the naming rather than a
footnote. **This dataset cannot measure playing style.** Searching every standard
FBref family against its 102 columns:

| Expected | Present |
|---|---|
| Passing (`Cmp`, `PrgP`, `KP`) | **none** |
| Dribbles / take-ons | **none** |
| Expected goals (`xG`, `xA`) | **none** |
| Touches / carries | **none** |
| Full defence (`Tkl`, `Blocks`, `Press`) | only `TklW`, `Int` |
| Shooting | complete |

What separates a deep-lying playmaker from a ball-winner is mostly distribution and
progression — none of which is here. What *can* be measured is attacking output,
defensive activity and discipline.

So the output file is `pl_player_profiles.csv`, the feature groups are
`ATTACKING_OUTPUT` / `DEFENSIVE_ACTIVITY` / `DISCIPLINE`, columns carry `att_` /
`def_` / `disc_` prefixes, and there is no `STYLE_FEATURES` constant anywhere. A
later script cannot call these "styles" without renaming things first.

**Cluster names are generated mechanically** from feature means against the
quartiles of all 315 players — never hand-written. "Inverted winger", "deep-lying
playmaker" and "ball-playing centre-back" are all claims about passing, carrying or
positioning, and none can be justified from these ten columns. `Pos` exists but is
held out for validation and never enters a name.

The largest cluster has no feature in either quartile, so a magnitude fallback names
it for what it is. That a third of regular Premier League starters are statistically
unremarkable on these axes is a real finding about a continuous distribution, not a
naming failure.

### Known limitations

**Individual assignments are often marginal.** Stored per player in
`cluster_assignments.csv`:

- **19 of 315 (6%)** have a *negative* silhouette — they sit closer to another
  cluster's members than to their own
- **76 (24%)** are within 0.5 of a rival centroid
- Lewis Hall's margin is **0.04**, which makes his label essentially a coin flip

`distance_to_centroid`, `margin_to_next` and per-player `silhouette` are all in the
output precisely so a consumer can surface that uncertainty rather than presenting
every label as equally solid.

**Cluster numbering is arbitrary.** K-Means integer labels can permute across refits
even for an identical partition, so the generated *names* are the durable
identifier, not the numbers.

**One season, one league.** 315 players from 2025–26 Premier League only. No
cross-season stability check is possible from this dataset, so whether these
groupings persist year to year is unknown.

**The feature groups are unbalanced 5 / 2 / 3**, which is upstream of every result
above — see the group-imbalance note.

---

## Ideas parked for later

Nothing in this section is started. Each item is recorded because it was
considered and deliberately deferred, not because it is in progress.

### Live prediction — not started

Both apps currently predict against the static Kaggle-derived dataset. That is a
deliberate property rather than a limitation: because every fixture already has
a known outcome, each prediction can be shown next to what actually happened,
which is what makes the apps honest about how often the models are wrong.

A live version would instead forecast genuinely upcoming fixtures — matches that
have not been played. What it would take:

- **A live data source** for recent results and upcoming fixtures.
  [football-data.org](https://www.football-data.org/) has a usable free tier, as
  does [API-Football](https://www.api-football.com/) at roughly 100 requests per
  day. Both are comfortably enough for a weekly refresh ahead of a matchday.
  Neither supports real-time in-play updates at zero cost, and that is fine —
  the model's features are all pre-match anyway.
- **A recurring pipeline rather than a one-time script.** Every feature would
  need recomputing before each matchday: rolling form over the last 5 and 10,
  rest days, head-to-head, and the rebuilt league position. This is the same
  logic as [features.py](02-match-predictor/features.py), run repeatedly against
  live data instead of once against a static dump.
- **A club-identity mapping layer.** The live source's team names and IDs will
  not match Transfermarkt's, so a crosswalk is needed. Expect this to be the
  fiddliest part — promoted clubs, renames, and inconsistent suffixes
  ("Wolverhampton Wanderers" vs "Wolves") are where it breaks.
- **Scheduling**, if it should run without being triggered by hand. GitHub
  Actions' free tier is sufficient for a weekly cron.

**The model itself needs no changes.** `model.joblib` and the feature definitions
stay exactly as they are — this is a data-engineering addition, not a modelling
one. Only the input pipeline changes: same 32 features, same trained model,
different source of rows.

One consequence worth stating up front: a live version loses the
prediction-versus-reality comparison that both apps are currently built around,
at least until each fixture is played. Any live UI would need to decide what to
show in the gap between forecast and result.

### Already recorded per project

- **HGB hyperparameter tuning** — see
  [02's future work](#future-work-deliberately-deferred). The train/test gap
  points at regularisation specifically.
- **Draw-specific modelling** — an ordinal or two-stage formulation, same section.
- **A Streamlit app for 03-style-finder** — the only one of the three without one.
  It would have to surface `margin_to_next` and per-player silhouette rather than
  presenting a confident archetype label, since 24% of players sit within 0.5 of a
  rival centroid. Those columns exist in `cluster_assignments.csv` precisely so that
  is possible.
- **Cross-season cluster stability for 03** — whether these groupings persist year
  to year is untestable from a single-season dataset. Would need a second season of
  the same stats.

---

## Setup

```bash
pip install pandas numpy scikit-learn matplotlib streamlit joblib
```

Built against pandas 2.3.3, numpy 2.4.0, scikit-learn 1.9.0, matplotlib 3.11.1
on Python 3.12.

---

## Repository layout

```
01-value-predictor/
    clean.py         raw CSVs -> modelling tables
    eda.py           distributions, correlations, VIF, age curve
    model.py         cross-validated model comparison
    train_final.py   fits the shipping model, writes model.joblib
    app.py           Streamlit app
    model.joblib     fitted LinearRegression + metadata
    plots/           generated figures
02-match-predictor/
    features.py           raw CSVs -> 4,616-match table, leak-free by construction
    model.py              5 models x 2 chronological CV schemes
    train_final.py        fits the shipping model, writes model.joblib + OOF
    app.py                Streamlit app
    model.joblib          fitted HistGradientBoosting + metadata
    oof_predictions.csv   out-of-sample forecasts, seasons 2017-2025
    plots/                confusion matrices, accuracy by season
03-style-finder/
    clean.py                  raw CSV -> 315-player activity-profile table
    cluster.py                scaling, k selection, stability, naming, validation
    train_final.py            fits and persists the clustering
    model.joblib              fitted Pipeline + quality metadata
    cluster_assignments.csv   per-player cluster, name and uncertainty
    plots/                    k selection, group variance, profiles, PCA
data/
    raw/          Kaggle download (gitignored - see above)
    processed/    both derived tables (committed)
```

---

## Licensing

Three different things, under three different terms.

- **Code** in this repository is MIT licensed — see [LICENSE](LICENSE).
- **Player-scores data** (projects 01 and 02) comes from the Kaggle
  [player-scores](https://www.kaggle.com/datasets/davidcariboo/player-scores)
  dataset under **CC0-1.0**, a public domain dedication. That covers the committed
  `pl_player_values.csv`, `pl_player_values_prethreshold.csv` and
  `pl_matches_features.csv`.
- **Player-stats data** (project 03) comes from the Kaggle
  [football-players-stats-2025-2026](https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2025-2026)
  dataset under the **MIT licence**, which is a different grant from CC0 and carries
  its own attribution condition. That covers `pl_player_profiles.csv` and
  `cluster_assignments.csv`.

The code licence being MIT and the project-03 data licence being MIT is a
coincidence, not a shared grant — they are separate and cover different things.

The code licence makes no claim over either dataset. Both remain subject to their
own terms and to the original sources' — Transfermarkt for player-scores, FBref for
the stats dataset.
