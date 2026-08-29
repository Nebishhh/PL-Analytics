"""
01-value-predictor : baseline models with cross-validated scoring
=================================================================
Compares plain OLS against Ridge and Lasso on the same 5-fold splits.

Decisions worth knowing:

  TARGET     log(market_value_in_eur). All fitting happens in log space; all
             error reporting is converted back to EUR so the numbers are
             readable. R^2 stays in log space because that is what the models
             actually optimise -- an R^2 quoted in EUR would be a different
             quantity and would flatter or punish models arbitrarily depending
             on how the top of the range happens to fall.

  BACK-TRANSFORM
             exp(mean prediction in log space) is the conditional *median*,
             not the mean -- Jensen's inequality. So the EUR errors below are
             honest median-style errors, and the models will systematically
             under-predict the arithmetic mean. That is fine for "what is this
             player worth", which is a median question, but do not sum these
             predictions to value a squad without a smearing correction.

  FEATURES   Raw counting stats AND per-90 rates together, on purpose: the
             rates alone are unstable for low-minutes players, and the counts
             alone cannot distinguish an efficient rotation player from a
             starter with the same total. The cost is severe collinearity
             (goals_per90 is literally pl_goals * 90 / pl_minutes), which is
             exactly what Ridge is designed to absorb -- see eda.py.

             age^2 is included because the age-value relationship is an
             inverted U, not a line. The ablation at the top of the output
             reports CV R^2 with and without it on identical splits.

             Deliberately excluded from v1, by decision: foot, height_in_cm,
             contract_expiration_date.

  SCALING    StandardScaler lives inside the Pipeline, so it is refitted on
             each training fold. Scaling before splitting would leak test-fold
             distribution into training.

  ALPHA      Chosen by RidgeCV / LassoCV *within* each training fold, never on
             the full dataset. Picking one alpha globally and then scoring it
             with CV would reuse the test folds and optimistically bias the
             result.

Reads : data/processed/pl_player_values.csv
Writes: 01-value-predictor/plots/06_cv_results.png
        01-value-predictor/plots/07_residuals.png
"""

import sys
from pathlib import Path

import matplotlib

# Player names carry accents; the Windows console default mangles them.
sys.stdout.reconfigure(encoding="utf-8")

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LassoCV, LinearRegression, RidgeCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path("data/processed/pl_player_values.csv")
PLOTS = Path("01-value-predictor/plots")

NUMERIC = [
    "age",
    "pl_matches", "pl_minutes", "pl_goals", "pl_assists",
    "pl_yellow_cards", "pl_red_cards",
    "goals_per90", "assists_per90",
]

N_SPLITS = 5
SEED = 42


def build_xy(df: pd.DataFrame, age_squared: bool = True
             ) -> tuple[pd.DataFrame, np.ndarray]:
    """Design matrix and log target.

    age_squared adds an age^2 term. The EDA age curve (plot 04) is an
    inverted U -- geometric mean value climbs from EUR4.6m at 18-20 to
    EUR18.3m at 26-28, then falls to EUR0.35m by 38-40. A single linear age
    term has to draw a straight line through that, so it cannot represent
    "young and unproven" and "old and declining" as both being cheap.
    """
    # drop_first avoids the dummy trap, which would leave OLS singular.
    dummies = pd.get_dummies(df["position"], prefix="pos", drop_first=True)
    parts = [df[NUMERIC]]
    if age_squared:
        parts.append(df[["age"]].pow(2).rename(columns={"age": "age_sq"}))
    parts.append(dummies)
    x = pd.concat(parts, axis=1).astype(float)
    y = np.log(df["market_value_in_eur"].to_numpy())
    return x, y


def cross_validate(x: pd.DataFrame, y: np.ndarray
                   ) -> tuple[dict[str, dict], dict[str, np.ndarray]]:
    """Run the same KFold splits across every model. Returns metrics and
    out-of-fold predictions (in log space)."""
    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    results: dict[str, dict] = {}
    oof: dict[str, np.ndarray] = {}

    for name, model in make_models().items():
        r2s, maes_eur, medaes_eur, maes_log, alphas_used = [], [], [], [], []
        preds = np.zeros_like(y)

        for train_idx, test_idx in kf.split(x):
            model.fit(x.iloc[train_idx], y[train_idx])
            pred_log = model.predict(x.iloc[test_idx])
            preds[test_idx] = pred_log

            true_eur = np.exp(y[test_idx])
            pred_eur = np.exp(pred_log)

            r2s.append(r2_score(y[test_idx], pred_log))
            maes_log.append(mean_absolute_error(y[test_idx], pred_log))
            maes_eur.append(mean_absolute_error(true_eur, pred_eur))
            medaes_eur.append(float(np.median(np.abs(true_eur - pred_eur))))

            reg = model.named_steps["reg"]
            if hasattr(reg, "alpha_"):
                alphas_used.append(float(reg.alpha_))

        results[name] = {
            "r2": r2s, "mae_eur": maes_eur, "medae_eur": medaes_eur,
            "mae_log": maes_log, "alphas": alphas_used,
        }
        oof[name] = preds

    return results, oof


def make_models() -> dict[str, Pipeline]:
    alphas = np.logspace(-3, 3, 60)
    return {
        "Linear": Pipeline([
            ("scale", StandardScaler()),
            ("reg", LinearRegression()),
        ]),
        "Ridge": Pipeline([
            ("scale", StandardScaler()),
            ("reg", RidgeCV(alphas=alphas)),
        ]),
        "Lasso": Pipeline([
            ("scale", StandardScaler()),
            ("reg", LassoCV(alphas=alphas, max_iter=50_000, random_state=SEED)),
        ]),
    }


def main() -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA, encoding="utf-8")

    print(f"{len(df):,} players, {N_SPLITS}-fold CV, seed {SEED}")
    print(f"PL minutes: min {df.pl_minutes.min():,}  "
          f"median {df.pl_minutes.median():,.0f}  max {df.pl_minutes.max():,}\n")

    # --- age^2 ablation: identical splits, one feature different -------------
    print("age^2 ablation (CV R^2 in log space)")
    print(f"  {'model':<8} {'without age^2':>20} {'with age^2':>20} {'delta':>9}")
    print("  " + "-" * 60)
    ablation = {}
    for flag in (False, True):
        xa, ya = build_xy(df, age_squared=flag)
        ablation[flag], _ = cross_validate(xa, ya)
    for name in ablation[True]:
        a, b = ablation[False][name]["r2"], ablation[True][name]["r2"]
        print(f"  {name:<8} "
              f"{np.mean(a):>11.3f} +/- {np.std(a):<5.3f} "
              f"{np.mean(b):>11.3f} +/- {np.std(b):<5.3f} "
              f"{np.mean(b) - np.mean(a):>+9.3f}")
    print()

    # Everything below uses the age^2 design matrix.
    x, y = build_xy(df, age_squared=True)
    print(f"Final design matrix: {x.shape[1]} features "
          f"({len(NUMERIC)} numeric + age_sq + "
          f"{x.shape[1] - len(NUMERIC) - 1} position dummies)\n")
    results, oof = cross_validate(x, y)

    # --- report --------------------------------------------------------------
    print(f"{'model':<8} {'R2 (log)':>16} {'MAE (EUR)':>20} "
          f"{'MedAE (EUR)':>20} {'MAE (log)':>14}")
    print("-" * 82)
    for name, r in results.items():
        print(f"{name:<8} "
              f"{np.mean(r['r2']):>7.3f} +/- {np.std(r['r2']):<5.3f} "
              f"{np.mean(r['mae_eur']):>12,.0f} +/- {np.std(r['mae_eur']):<6,.0f} "
              f"{np.mean(r['medae_eur']):>12,.0f} +/- {np.std(r['medae_eur']):<6,.0f} "
              f"{np.mean(r['mae_log']):>6.3f} +/- {np.std(r['mae_log']):<5.3f}")

    print("\nPer-fold R^2:")
    for name, r in results.items():
        print(f"  {name:<8} " + "  ".join(f"{v:6.3f}" for v in r["r2"]))

    print("\nAlpha chosen per fold:")
    for name, r in results.items():
        if r["alphas"]:
            print(f"  {name:<8} " + "  ".join(f"{a:.4g}" for a in r["alphas"]))

    # A typical-error readout that is actually interpretable: MAE in log space
    # is roughly a multiplicative factor on the prediction.
    print("\nTypical multiplicative error (exp of mean log MAE):")
    for name, r in results.items():
        f = np.exp(np.mean(r["mae_log"]))
        print(f"  {name:<8} x{f:.2f}  "
              f"(a EUR10m player predicted between EUR{10 / f:.1f}m and EUR{10 * f:.1f}m)")

    # --- coefficients on a full-data refit -----------------------------------
    print("\nCoefficients (standardised, full-data refit -- direction only):")
    coef_table = {}
    for name, model in make_models().items():
        model.fit(x, y)
        coef_table[name] = pd.Series(model.named_steps["reg"].coef_, index=x.columns)
    coefs = pd.DataFrame(coef_table).round(3)
    coefs["|Ridge|"] = coefs["Ridge"].abs()
    print(coefs.sort_values("|Ridge|", ascending=False)
          .drop(columns="|Ridge|").to_string())

    dropped = coefs.index[coefs["Lasso"].abs() < 1e-8].tolist()
    print(f"\nLasso zeroed out {len(dropped)} feature(s): {dropped or 'none'}")

    # --- plots ---------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    names = list(results)
    xpos = np.arange(len(names))
    axes[0].bar(xpos, [np.mean(results[n]["r2"]) for n in names],
                yerr=[np.std(results[n]["r2"]) for n in names],
                capsize=5, color=["#3d195b", "#c8102e", "#00a398"])
    axes[0].set_xticks(xpos)
    axes[0].set_xticklabels(names)
    axes[0].set_ylabel("R^2 (log space)")
    axes[0].set_title("CV R^2, mean +/- 1 sd")
    axes[0].grid(alpha=0.3, axis="y")

    axes[1].bar(xpos, [np.mean(results[n]["medae_eur"]) / 1e6 for n in names],
                yerr=[np.std(results[n]["medae_eur"]) / 1e6 for n in names],
                capsize=5, color=["#3d195b", "#c8102e", "#00a398"])
    axes[1].set_xticks(xpos)
    axes[1].set_xticklabels(names)
    axes[1].set_ylabel("median abs error (EUR m)")
    axes[1].set_title("CV median absolute error, mean +/- 1 sd")
    axes[1].grid(alpha=0.3, axis="y")
    fig.suptitle(f"{N_SPLITS}-fold cross-validation", fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS / "06_cv_results.png", dpi=130)
    plt.close(fig)

    # Out-of-fold predicted vs actual, in EUR, log-log axes.
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, name in zip(axes, names):
        true_eur, pred_eur = np.exp(y) / 1e6, np.exp(oof[name]) / 1e6
        ax.scatter(true_eur, pred_eur, s=10, alpha=0.35, color="#3d195b")
        lim = [0.05, 250]
        ax.plot(lim, lim, "--", color="#c8102e", lw=1)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_xlabel("actual (EUR m)")
        ax.set_ylabel("predicted (EUR m)")
        ax.set_title(f"{name}  (out-of-fold)")
        ax.grid(alpha=0.3, which="both")
    fig.suptitle("Predicted vs actual, out-of-fold, EUR",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS / "07_residuals.png", dpi=130)
    plt.close(fig)

    # --- worst misses, for a sanity read ------------------------------------
    best = max(results, key=lambda n: np.mean(results[n]["r2"]))
    df_out = df.assign(
        pred_eur=np.exp(oof[best]),
        ratio=np.exp(oof[best]) / df["market_value_in_eur"],
    )
    print(f"\nBiggest over-predictions ({best}, out-of-fold):")
    cols = ["name", "age", "position", "pl_matches", "market_value_in_eur",
            "pred_eur", "ratio"]
    print(df_out.nlargest(5, "ratio")[cols].to_string(index=False,
          float_format=lambda v: f"{v:,.2f}"))
    print(f"\nBiggest under-predictions ({best}, out-of-fold):")
    print(df_out.nsmallest(5, "ratio")[cols].to_string(index=False,
          float_format=lambda v: f"{v:,.2f}"))


if __name__ == "__main__":
    main()
