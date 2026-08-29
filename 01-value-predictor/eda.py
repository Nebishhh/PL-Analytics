"""
01-value-predictor : exploratory data analysis
==============================================
Reads the cleaned table and writes diagnostic plots plus a printed summary.
Nothing here modifies the data -- this is look-only.

The three questions this is meant to answer before any modelling:

  1. Does log(market_value) actually behave better than the raw target?
     (Raw is median EUR12m / mean EUR19.2m / max EUR200m -- badly right-skewed.)

  2. How collinear are the features? We are deliberately feeding in raw
     counting stats AND per-90 rates together, and goals_per90 is by
     construction pl_goals * 90 / pl_minutes -- a deterministic function of two
     other columns in the matrix. Plain OLS has no defence against that, which
     is the whole reason Ridge and Lasso are on the menu.

  3. Is age non-linear? Market value peaks in the mid-20s and falls away on
     both sides, which a single linear age term cannot represent.

Reads : data/processed/pl_player_values.csv
Writes: 01-value-predictor/plots/*.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display in this environment
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA = Path("data/processed/pl_player_values.csv")
PLOTS = Path("01-value-predictor/plots")

NUMERIC = [
    "age",
    "pl_matches", "pl_minutes", "pl_goals", "pl_assists",
    "pl_yellow_cards", "pl_red_cards",
    "goals_per90", "assists_per90",
]


def variance_inflation(x: pd.DataFrame) -> pd.Series:
    """VIF per column, computed directly so we don't need statsmodels.

    VIF_j = 1 / (1 - R^2_j), where R^2_j is from regressing column j on all
    the others. Above ~10 is the usual 'this coefficient is not identified'
    warning line.
    """
    z = (x - x.mean()) / x.std(ddof=0)
    z = z.to_numpy()
    out = {}
    for j, col in enumerate(x.columns):
        others = np.delete(z, j, axis=1)
        a = np.column_stack([np.ones(len(others)), others])
        coef, *_ = np.linalg.lstsq(a, z[:, j], rcond=None)
        resid = z[:, j] - a @ coef
        ss_res = float((resid ** 2).sum())
        ss_tot = float(((z[:, j] - z[:, j].mean()) ** 2).sum())
        r2 = 1.0 - ss_res / ss_tot
        out[col] = np.inf if r2 >= 1.0 else 1.0 / (1.0 - r2)
    return pd.Series(out).sort_values(ascending=False)


def main() -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA, encoding="utf-8")
    df["log_value"] = np.log(df["market_value_in_eur"])

    print(f"Loaded {len(df):,} rows x {len(df.columns)} cols from {DATA}\n")

    # --- 1. target distribution, raw vs log ---------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].hist(df["market_value_in_eur"] / 1e6, bins=50, color="#c8102e")
    axes[0].set_xlabel("market value (EUR m)")
    axes[0].set_ylabel("players")
    axes[0].set_title("Raw target: severely right-skewed")
    axes[1].hist(df["log_value"], bins=50, color="#3d195b")
    axes[1].set_xlabel("log(market value in EUR)")
    axes[1].set_title("Log target: roughly symmetric")
    fig.suptitle("Why we model the log", fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS / "01_target_distribution.png", dpi=130)
    plt.close(fig)

    raw, log = df["market_value_in_eur"], df["log_value"]
    print("Target skewness")
    print(f"  raw  skew {raw.skew():6.2f}   kurtosis {raw.kurtosis():7.2f}")
    print(f"  log  skew {log.skew():6.2f}   kurtosis {log.kurtosis():7.2f}\n")

    # --- 2. correlation heatmap ---------------------------------------------
    corr = df[NUMERIC + ["log_value"]].corr()
    fig, ax = plt.subplots(figsize=(8.5, 7))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(corr)))
    ax.set_yticklabels(corr.columns, fontsize=8)
    for i in range(len(corr)):
        for j in range(len(corr)):
            v = corr.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(v) > 0.55 else "black")
    ax.set_title("Feature correlations (note pl_matches / pl_minutes)",
                 fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(PLOTS / "02_correlation_heatmap.png", dpi=130)
    plt.close(fig)

    print("Correlation with log_value (descending):")
    print(corr["log_value"].drop("log_value").sort_values(ascending=False)
          .round(3).to_string(), "\n")

    print("Worst collinear pairs (|r| > 0.7, features only):")
    c = corr.drop(index="log_value", columns="log_value").abs()
    seen = set()
    for i in c.index:
        for j in c.columns:
            if i != j and (j, i) not in seen and c.loc[i, j] > 0.7:
                seen.add((i, j))
                print(f"  {i:<16} {j:<16} r = {corr.loc[i, j]:.3f}")
    print()

    # --- 3. VIF --------------------------------------------------------------
    vif = variance_inflation(df[NUMERIC])
    print("Variance inflation factor (>10 = coefficient not identified):")
    print(vif.round(2).to_string(), "\n")

    # --- 4. feature vs target scatters --------------------------------------
    show = ["age", "pl_minutes", "pl_matches", "pl_goals",
            "goals_per90", "assists_per90"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5))
    for ax, col in zip(axes.ravel(), show):
        ax.scatter(df[col], df["log_value"], s=9, alpha=0.35, color="#3d195b")
        ax.set_xlabel(col)
        ax.set_ylabel("log(value)")
        r = df[col].corr(df["log_value"])
        ax.set_title(f"{col}  (r = {r:.2f})", fontsize=10)
    fig.suptitle("Features vs log target", fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS / "03_feature_scatters.png", dpi=130)
    plt.close(fig)

    # --- 5. age curve --------------------------------------------------------
    # Binned means, to show the shape a linear age term would have to miss.
    bins = pd.cut(df["age"], bins=range(16, 44, 2))
    prof = df.groupby(bins, observed=True)["log_value"].agg(["mean", "size"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    centres = [iv.mid for iv in prof.index]
    ax.plot(centres, np.exp(prof["mean"]) / 1e6, "o-", color="#c8102e")
    ax.set_xlabel("age")
    ax.set_ylabel("geometric mean value (EUR m)")
    ax.set_title("Value peaks in the mid-20s -- age is not linear",
                 fontweight="bold")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTS / "04_age_curve.png", dpi=130)
    plt.close(fig)

    print("Age profile (geometric mean value by 2-year band):")
    prof["EUR_m"] = (np.exp(prof["mean"]) / 1e6).round(2)
    print(prof[["size", "EUR_m"]].to_string(), "\n")

    # --- 6. position ---------------------------------------------------------
    order = ["Goalkeeper", "Defender", "Midfield", "Attack"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    # matplotlib >= 3.11 renamed boxplot's `labels` argument to `tick_labels`.
    ax.boxplot([df.loc[df.position == p, "log_value"] for p in order],
               tick_labels=order)
    ax.set_ylabel("log(value)")
    ax.set_title("Value by position", fontweight="bold")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(PLOTS / "05_position_boxplot.png", dpi=130)
    plt.close(fig)

    print("By position (median EUR):")
    pos = df.groupby("position")["market_value_in_eur"].agg(["size", "median"])
    pos["median"] = pos["median"].map(lambda v: f"{v:,.0f}")
    print(pos.to_string(), "\n")

    # --- 7. the low-minutes tail --------------------------------------------
    thin = df[df.pl_minutes < 500]
    print(f"Low-minutes tail: {len(thin)} players under 500 PL minutes "
          f"({len(thin) / len(df) * 100:.1f}%)")
    print(f"  their goals_per90 spread: "
          f"min {thin.goals_per90.min():.2f}  max {thin.goals_per90.max():.2f}")
    print(f"  everyone else:            "
          f"min {df[df.pl_minutes >= 500].goals_per90.min():.2f}  "
          f"max {df[df.pl_minutes >= 500].goals_per90.max():.2f}")

    print(f"\nWrote {len(list(PLOTS.glob('*.png')))} plots to {PLOTS}/")


if __name__ == "__main__":
    main()
