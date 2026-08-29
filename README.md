# PL-Analytics

Three progressively harder machine learning projects built on Transfermarkt
football data, working up from regression to classification to unsupervised
clustering.

| # | Project | Technique | Status |
|---|---------|-----------|--------|
| 01 | **value-predictor** | Linear regression | Complete — Streamlit app for interactive predictions coming next |
| 02 | **match-predictor** | Classification | Planned |
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

The derived table `data/processed/pl_player_values.csv` **is** committed (92KB),
so you can run the EDA, the models and the app without downloading anything.
You only need `data/raw/` if you want to re-run `clean.py` or change a filter.

---

## 01-value-predictor

Predicts a Premier League player's current market value in EUR from their
career-to-date Premier League appearance record.

```bash
python 01-value-predictor/clean.py   # data/raw -> data/processed (498 rows)
python 01-value-predictor/eda.py     # diagnostic plots + collinearity report
python 01-value-predictor/model.py   # 5-fold CV: Linear vs Ridge vs Lasso
```

### Result

**R² = 0.729 ± 0.045** (5-fold cross-validation, log space)
**Typical error ×1.75** — a €10M player is predicted somewhere between €5.7M
and €17.5M.

Cross-validation rather than a single holdout: at n=498 one split tells you
very little. Fold-to-fold R² still ranges 0.664 to 0.781 even after the fixes
below, and an unlucky split would have made this look far worse or far better
than it is.

| Model | R² (log) | Median abs. error |
|-------|----------|-------------------|
| Linear | 0.729 ± 0.045 | €5.85M |
| Ridge | 0.730 ± 0.043 | €5.94M |
| Lasso | 0.731 ± 0.040 | €5.82M |

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
**+0.058 R²** (0.671 → 0.729), consistent across all three models.

**Dropped as leakage:** `highest_market_value_in_eur` is a direct function of
the target.

**Parked for v1:** `foot`, `height_in_cm`, `contract_expiration_date`.

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

## Setup

```bash
pip install pandas numpy scikit-learn matplotlib
```

Built against pandas 2.3.3, numpy 2.4.0, scikit-learn 1.9.0, matplotlib 3.11.1
on Python 3.12.

---

## Repository layout

```
01-value-predictor/
    clean.py      raw CSVs -> modelling table
    eda.py        distributions, correlations, VIF, age curve
    model.py      cross-validated model comparison
    plots/        generated figures
data/
    raw/          Kaggle download (gitignored - see above)
    processed/    pl_player_values.csv (committed)
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
