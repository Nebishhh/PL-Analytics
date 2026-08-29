"""
02-match-predictor : model comparison
=====================================
Win/Draw/Loss classification for Premier League matches, from the home team's
perspective. Compares a logistic regression baseline against a gradient
boosted tree ensemble, under two chronological cross-validation schemes.

THE NUMBER THAT MATTERS: always predicting a home win scores 45.2% on this
data. That, not 33%, is the bar. A DummyClassifier is scored under the exact
same folds as everything else so the baseline is measured rather than quoted.

FEATURE SET
  Paired statistics enter as differences, not as levels. diff_pts_l5 is
  exactly home_pts_l5 - away_pts_l5, so including all three would make the
  design matrix rank-deficient: regularised logistic regression still fits,
  but the coefficients are split arbitrarily among the dependent triple and
  cannot be read. The rank is asserted before fitting.

  Venue statistics are the exception and stay as levels. The home side's home
  form and the away side's away form are different quantities; differencing
  them would destroy the asymmetry that carries home advantage, which is the
  entire reason the split was computed.

  Club identity is excluded. One-hot over 40+ clubs is ~80 sparse columns on
  4,616 rows, and identity is already expressed through form and league
  position. Newly promoted clubs would carry almost no training support.

  season is one-hot, not ordinal. Home-win rate runs 39% (2020, empty
  stadiums) to 50% (2016); as an integer a linear model reads that as a
  trend, which is wrong. The cost is no extrapolation to unseen seasons,
  which is acceptable for a retrospective study.

MISSING DATA
  h2h_home_pts_per_match is null for 401 matches -- first-ever meetings,
  where h2h_matches == 0. Handled per model rather than globally, because the
  two families genuinely differ: median imputation inside the logistic
  pipeline (refitted per fold), native NaN passthrough for the tree. Filling
  with 0.0 would assert "these clubs have met and the home side took
  nothing", which is false. Dropping is also wrong -- 8.7% of rows, and
  non-random, since it selects promoted clubs.

CROSS-VALIDATION
  Chronological only; random k-fold would train on 2025 and test on 2013.
  Two schemes are reported side by side so it is visible whether any
  conclusion is an artefact of where the fold boundaries fall.

NO TUNING
  This pass compares model families at their defaults. If no model beats the
  dummy on macro F1, that is the finding and it gets reported as such.
  Tuning is a separate deliberate step, not something to slip in here to
  chase a better number.

Reads : data/processed/pl_matches_features.csv
Writes: 02-match-predictor/plots/*.png
"""

import sys
from pathlib import Path

import matplotlib

sys.stdout.reconfigure(encoding="utf-8")
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             log_loss, precision_recall_fscore_support)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path("data/processed/pl_matches_features.csv")
PLOTS = Path("02-match-predictor/plots")

CLASSES = ["H", "D", "A"]
SEED = 42

# diff_gd_l5 and diff_gd_l10 are deliberately absent. gd = gf - ga by
# construction, so diff_gd is exactly diff_gf - diff_ga and including all
# three leaves the matrix rank-deficient -- the assert_full_rank check below
# caught this at rank 32 of 34. Keeping gf and ga separately loses nothing:
# goal difference is recoverable as their difference, and the split carries
# strictly more information, distinguishing attacking from defensive form.
DIFF_FEATURES = [
    "diff_pts_l5", "diff_gf_l5", "diff_ga_l5",
    "diff_pts_l10", "diff_gf_l10", "diff_ga_l10",
    "diff_pre_position", "diff_pre_ppg", "diff_pre_gd_per_game",
    "diff_rest_days",
]
VENUE_FEATURES = [
    "home_venue_pts_l5", "home_venue_gf_l5", "home_venue_ga_l5",
    "away_venue_pts_l5", "away_venue_gf_l5", "away_venue_ga_l5",
]
CONTEXT_FEATURES = ["h2h_matches", "h2h_home_pts_per_match", "home_matchday"]


# --- data --------------------------------------------------------------------

def build_xy() -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    df = pd.read_csv(DATA, encoding="utf-8", parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    seasons = pd.get_dummies(df["season"], prefix="season", drop_first=True)
    x = pd.concat(
        [df[DIFF_FEATURES + VENUE_FEATURES + CONTEXT_FEATURES], seasons],
        axis=1,
    ).astype(float)
    y = df["target"].to_numpy()
    return x, y, df


def assert_full_rank(x: pd.DataFrame) -> None:
    """Fail loudly if any column is a linear combination of the others.

    This is the check that would have caught the levels-plus-diffs mistake.
    NaNs are median-filled first purely so the rank is computable.
    """
    m = x.fillna(x.median()).to_numpy()
    m = m - m.mean(axis=0)
    rank = np.linalg.matrix_rank(m)
    if rank != m.shape[1]:
        raise SystemExit(
            f"Design matrix is rank-deficient: rank {rank} < {m.shape[1]} "
            f"columns. Some feature is a linear combination of others."
        )
    print(f"  design matrix full rank: {rank} = {m.shape[1]} columns ✓")


def variance_inflation(x: pd.DataFrame) -> pd.Series:
    """VIF per column. Above ~10 means the coefficient is not identified."""
    z = x.fillna(x.median())
    z = (z - z.mean()) / z.std(ddof=0).replace(0, np.nan)
    z = z.dropna(axis=1).to_numpy()
    cols = x.fillna(x.median()).std(ddof=0)
    cols = cols[cols > 0].index
    out = {}
    for j, col in enumerate(cols):
        others = np.delete(z, j, axis=1)
        a = np.column_stack([np.ones(len(others)), others])
        coef, *_ = np.linalg.lstsq(a, z[:, j], rcond=None)
        resid = z[:, j] - a @ coef
        ss_res, ss_tot = float((resid ** 2).sum()), float((z[:, j] ** 2).sum())
        r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
        out[col] = np.inf if r2 >= 1 else 1 / (1 - r2)
    return pd.Series(out).sort_values(ascending=False)


# --- models ------------------------------------------------------------------

def make_models() -> dict[str, object]:
    """Five entries so the baseline and the class-weight trade are measured
    under identical folds rather than argued about."""
    return {
        "Dummy (home)": DummyClassifier(strategy="most_frequent"),
        "LogReg": Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=SEED)),
        ]),
        "LogReg-bal": Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=SEED,
                                       class_weight="balanced")),
        ]),
        # No imputation: HistGradientBoosting handles NaN natively and learns
        # its own default direction for missing values.
        "HGB": HistGradientBoostingClassifier(random_state=SEED),
        "HGB-bal": HistGradientBoostingClassifier(random_state=SEED,
                                                  class_weight="balanced"),
    }


# --- splitting ---------------------------------------------------------------

def season_splits(df: pd.DataFrame, min_train_seasons: int = 5):
    """Expanding window on whole seasons: train on all prior, test on one.

    Boundaries land where a real season ends, so each fold answers "how would
    this have done that year".
    """
    seasons = sorted(df.season.unique())
    for test_season in seasons[min_train_seasons:]:
        tr = np.flatnonzero((df.season < test_season).to_numpy())
        te = np.flatnonzero((df.season == test_season).to_numpy())
        yield tr, te, str(test_season)


def timeseries_splits(df: pd.DataFrame, n_splits: int = 5):
    for i, (tr, te) in enumerate(TimeSeriesSplit(n_splits=n_splits)
                                 .split(df), 1):
        yield tr, te, f"fold{i}"


# --- evaluation --------------------------------------------------------------

def evaluate(x, y, df, splitter, scheme_name: str) -> tuple[dict, dict]:
    print(f"\n{'=' * 78}\n{scheme_name}\n{'=' * 78}")
    models = make_models()
    summary, confusions = {}, {}
    fold_rows = []

    for name, model in models.items():
        accs, f1s, lls, folds = [], [], [], []
        cm_total = np.zeros((3, 3), dtype=int)

        for tr, te, label in splitter(df):
            # Guard the entire premise of the exercise.
            assert df.date.iloc[tr].max() <= df.date.iloc[te].min(), \
                f"{scheme_name}/{label}: train dates overlap test dates"

            model.fit(x.iloc[tr], y[tr])
            pred = model.predict(x.iloc[te])

            acc = accuracy_score(y[te], pred)
            f1 = f1_score(y[te], pred, average="macro", zero_division=0)
            accs.append(acc)
            f1s.append(f1)
            cm_total += confusion_matrix(y[te], pred, labels=CLASSES)

            try:
                proba = model.predict_proba(x.iloc[te])
                lls.append(log_loss(y[te], proba,
                                    labels=list(model.classes_)))
            except (AttributeError, ValueError):
                lls.append(np.nan)

            vc = pd.Series(y[te]).value_counts(normalize=True)
            folds.append(label)
            fold_rows.append({
                "model": name, "fold": label, "n_test": len(te),
                "acc": acc, "macro_f1": f1,
                "H%": vc.get("H", 0) * 100, "D%": vc.get("D", 0) * 100,
                "A%": vc.get("A", 0) * 100,
            })

        summary[name] = {
            "acc": np.mean(accs), "acc_sd": np.std(accs),
            "f1": np.mean(f1s), "f1_sd": np.std(f1s),
            "ll": np.nanmean(lls), "per_fold_acc": accs, "folds": folds,
        }
        confusions[name] = cm_total

    base = summary["Dummy (home)"]["acc"]

    print(f"\n{'model':<14} {'accuracy':>16} {'vs base':>9} "
          f"{'macro F1':>16} {'log loss':>9}")
    print("-" * 70)
    for name, s in summary.items():
        delta = "" if name.startswith("Dummy") else f"{s['acc'] - base:+.3f}"
        ll = "n/a" if np.isnan(s["ll"]) else f"{s['ll']:.3f}"
        print(f"{name:<14} {s['acc']:.3f} +/- {s['acc_sd']:.3f}   {delta:>9} "
              f"  {s['f1']:.3f} +/- {s['f1_sd']:.3f}  {ll:>9}")

    print("\nPer-class precision / recall / F1 (summed over folds):")
    for name, cm in confusions.items():
        tp = np.diag(cm)
        prec = np.divide(tp, cm.sum(0), out=np.zeros(3), where=cm.sum(0) > 0)
        rec = np.divide(tp, cm.sum(1), out=np.zeros(3), where=cm.sum(1) > 0)
        f1c = np.divide(2 * prec * rec, prec + rec, out=np.zeros(3),
                        where=(prec + rec) > 0)
        line = "  ".join(f"{c}: {prec[i]:.2f}/{rec[i]:.2f}/{f1c[i]:.2f}"
                         for i, c in enumerate(CLASSES))
        print(f"  {name:<14} {line}")
        pred_counts = cm.sum(0)
        print(f"  {'':<14} predicted H/D/A: "
              f"{pred_counts[0]:,} / {pred_counts[1]:,} / {pred_counts[2]:,}")

    return summary, confusions, pd.DataFrame(fold_rows)


# --- main --------------------------------------------------------------------

def main() -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    x, y, df = build_xy()

    print(f"{len(df):,} matches, {x.shape[1]} features "
          f"({len(DIFF_FEATURES)} diffs + {len(VENUE_FEATURES)} venue + "
          f"{len(CONTEXT_FEATURES)} context + "
          f"{x.shape[1] - len(DIFF_FEATURES) - len(VENUE_FEATURES) - len(CONTEXT_FEATURES)} "
          f"season dummies)")
    print(f"seasons {df.season.min()}-{df.season.max()}, "
          f"{df.date.min().date()} to {df.date.max().date()}")

    vc = pd.Series(y).value_counts()
    print("\nClass balance: " + "  ".join(
        f"{k} {vc[k]:,} ({vc[k] / len(y) * 100:.1f}%)" for k in CLASSES))
    print(f"Always-home-win baseline: {vc.max() / len(y) * 100:.1f}%")

    print("\nPre-flight checks:")
    assert_full_rank(x)
    vif = variance_inflation(x[DIFF_FEATURES + VENUE_FEATURES
                              + ["h2h_matches", "home_matchday"]])
    over = vif[vif > 10]
    print(f"  VIF > 10: {len(over)} feature(s)"
          + (f" -- {', '.join(over.index)}" if len(over) else ""))
    print("  top 5 VIF: " + ", ".join(f"{k} {v:.1f}"
                                      for k, v in vif.head(5).items()))

    results = {}
    for scheme, splitter in [
        ("SCHEME A - season-based expanding window (9 folds)", season_splits),
        ("SCHEME B - TimeSeriesSplit(n_splits=5)", timeseries_splits),
    ]:
        results[scheme] = evaluate(x, y, df, splitter, scheme)

    # --- per-fold detail for the headline scheme ----------------------------
    scheme_a = list(results)[0]
    folds = results[scheme_a][2]
    print(f"\n{'=' * 78}\nPer-fold detail, Scheme A\n{'=' * 78}")
    piv = folds.pivot(index="fold", columns="model", values="acc")
    bal = folds.drop_duplicates("fold").set_index("fold")[["n_test", "H%",
                                                           "D%", "A%"]]
    print(bal.join(piv).round(3).to_string())

    # --- plots ---------------------------------------------------------------
    summary_a, conf_a, _ = results[scheme_a]

    fig, axes = plt.subplots(1, 5, figsize=(20, 4))
    for ax, (name, cm) in zip(axes, conf_a.items()):
        ax.imshow(cm, cmap="Purples")
        ax.set_xticks(range(3), CLASSES)
        ax.set_yticks(range(3), CLASSES)
        ax.set_xlabel("predicted")
        ax.set_ylabel("actual")
        ax.set_title(name, fontsize=10)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center",
                        fontsize=8,
                        color="white" if cm[i, j] > cm.max() * 0.6 else "black")
    fig.suptitle("Confusion matrices, Scheme A (summed over folds)",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS / "01_confusion_matrices.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for name, s in summary_a.items():
        ax.plot(s["folds"], s["per_fold_acc"], "o-", label=name)
    ax.set_xlabel("test season")
    ax.set_ylabel("accuracy")
    ax.set_title("Accuracy by test season (Scheme A)", fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "02_accuracy_by_season.png", dpi=130)
    plt.close(fig)

    print(f"\nWrote plots to {PLOTS}/")


if __name__ == "__main__":
    main()
