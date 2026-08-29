# PL-Analytics

Three progressively harder machine learning projects built on Transfermarkt
football data, working up from regression to classification to unsupervised
clustering.

| # | Project | Technique | Status |
|---|---------|-----------|--------|
| 01 | **value-predictor** | Linear regression | Complete, with a Streamlit app for interactive predictions |
| 02 | **match-predictor** | Classification | Complete |
| 03 | **style-finder** | K-Means clustering | Planned |

---

## Data

Source: [davidcariboo/player-scores](https://www.kaggle.com/datasets/davidcariboo/player-scores)
on Kaggle — a Transfermarkt scrape, CC0-1.0 licensed. 12 CSVs, 219MB
compressed, covering 50,149 players and 1.89M individual match appearances
across 31 domestic leagues from 2012 onward.

`data/raw/` is gitignored, so you need to fetch it yourself.

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

### Known limitations

**The model has learned home advantage and relative form, and has learned nothing
about draws.** Draw precision sits at 0.26 in every configuration tested. The balanced
variants change only how *often* draws are guessed, not how well: LogReg-balanced lifts
draw recall from 0.11 to 0.59 and falls *below* the dummy on accuracy, predicting 1,600
draws where 697 occurred. Draws have no distinctive feature signature — they happen
between evenly matched teams, which is a region of feature space rather than a
direction in it.

**The ceiling is low and this is near it.** Max eta-squared across every engineered
feature is 0.132; nothing separates these classes strongly. Match outcomes are
substantially irreducible without market odds or squad-strength signals. +2.4 points
over baseline is a real but modest gain and is reported as such.

**Multicollinearity is severe but harmless here.** Seven features exceed VIF 10, topping
out at 31.7. Coefficients are not individually interpretable. An `l10`-only variant was
tested and scored *worse* (0.507 vs 0.512), so the full feature set stands.

**HGB overfits badly at library defaults** — in-sample accuracy 0.980 against
cross-validated 0.470. The CV figure is unaffected and is the honest one, but the gap
says the defaults are memorising 4,616 rows.

**Home advantage is non-stationary.** It ranges 39% (2020, empty stadiums) to 50%
(2016). Season dummies absorb the level shift. Notably, 2020 is where the models beat
the dummy by the *widest* margin (+0.076) — the dummy collapses when home advantage
evaporates while the models hold near 46%.

### Future work, deliberately deferred

- **HGB hyperparameter tuning** — see the overfitting gap above. Must be nested inside
  the training fold.
- **Draws as a distinct problem** — an ordinal or two-stage "decisive vs draw, then
  which side" formulation may suit them better than flat 3-class.

Neither was attempted in this pass. Chasing a better number with ad hoc tuning after
seeing the results is how CV estimates become fiction.

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
    features.py      raw CSVs -> 4,616-match table, leak-free by construction
    model.py         5 models x 2 chronological CV schemes
    train_final.py   fits the shipping model, writes model.joblib
    model.joblib     fitted HistGradientBoosting + metadata
    plots/           confusion matrices, accuracy by season
data/
    raw/          Kaggle download (gitignored - see above)
    processed/    both derived tables (committed)
```

---

## Licensing

Two different things, under two different terms:

- **Code** in this repository is MIT licensed — see [LICENSE](LICENSE).
- **Data** comes from the Kaggle
  [player-scores](https://www.kaggle.com/datasets/davidcariboo/player-scores)
  dataset, released under CC0-1.0 (public domain dedication). That covers the
  committed `data/processed/pl_player_values.csv`, which is derived from it.

The MIT license applies to the analysis code only and makes no claim over the
underlying data, which remains subject to its own terms and to Transfermarkt's
as the original source.
