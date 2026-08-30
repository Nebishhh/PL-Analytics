"""
03-style-finder : K-Means clustering of activity profiles
=========================================================
Groups 315 Premier League outfielders by per-90 activity, then validates the
result against the held-out position label.

READ THIS FIRST: THE STRUCTURE IS WEAK
  Silhouette never exceeds 0.24 at any k, and 0.25 is the conventional line
  below which structure is considered weak. K-Means always returns k clusters
  -- that is what it does -- so a partition existing is not evidence that
  natural groups exist. Here it is largely imposing divisions on a continuous
  distribution. Player activity is a cloud, not clumps.

  That does not make the output useless. The k=4 partition is stable across
  seeds and interpretable, and it is a useful summary of how PL minutes are
  spent. It is not a discovery of natural archetypes, and this script does
  not describe it as one.

  This is the project-03 analogue of project 02's "does anything beat the
  dummy" question. The answer there was yes; the answer here is "sort of, and
  here is exactly how weak it is".

SCALING
  StandardScaler ships. The reason is stronger than matching projects 01 and
  02: it sets every feature to unit variance by construction, so the distance
  metric's weighting becomes exactly the feature count -- 50/20/30 across the
  three groups -- with nothing hidden. RobustScaler scales by IQR and does NOT
  equalise variance, so skewed features stay heavier, pushing attacking to
  52.7% and making the imbalance worse while adding a second, opaque weighting
  on top of it. It also barely touches the skew it would be adopted for
  (att_gls_p90 max |z| 4.63 -> 4.56). Reported as a comparison, not shipped.

GROUP IMBALANCE, REPORTED NOT CORRECTED
  ATTACKING_OUTPUT holds 5 of the 10 features and therefore gets 50% of the
  distance metric. Two players differing sharply in defensive activity are
  treated as more similar than two differing equally in attacking output.
  This is a real limitation of the result and is printed as such rather than
  silently patched.

  A group-normalised variant (each group's features divided by sqrt of group
  size, equalising contribution at 33/33/33) is fitted for comparison only.
  Agreement is ARI 0.835 at k=4 -- roughly one player in six changes cluster.
  The clusters are robust in shape but not in membership, so any individual
  assignment carries that caveat.

NAMING
  Names are generated mechanically from feature means against the quartiles of
  all 315 players, never hand-written and never inferred. Words like "inverted
  winger", "deep-lying playmaker" or "ball-playing centre-back" are claims
  about passing, carrying and positioning; this dataset has no passing,
  dribbling, xG, touch or carry data, so no such term can be justified. Pos
  exists but is held out for validation and must not leak into a name.

Reads : data/processed/pl_player_profiles.csv
Writes: 03-style-finder/plots/*.png
"""

import sys
from pathlib import Path

import matplotlib

sys.stdout.reconfigure(encoding="utf-8")
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_score)
from sklearn.preprocessing import RobustScaler, StandardScaler

DATA = Path("data/processed/pl_player_profiles.csv")
PLOTS = Path("03-style-finder/plots")

K_RANGE = range(2, 11)      # wider than 3-8 so the k=2 result is visible
K_CHOSEN = 4
SEEDS = 8
SEED = 42

# Readable labels, used to build cluster names. Deliberately literal: they name
# the measured quantity and nothing more.
LABELS = {
    "att_gls_p90": "goals",
    "att_ast_p90": "assists",
    "att_sh_p90": "shots",
    "att_crs_p90": "crosses",
    "att_sot_pct": "shot accuracy",
    "def_int_p90": "interceptions",
    "def_tklw_p90": "tackles won",
    "disc_fls_p90": "fouls",
    "disc_fld_p90": "fouls drawn",
    "disc_crdy_p90": "yellow cards",
}
PALETTE = ["#00FF87", "#04F5FF", "#E90052", "#F3EAF5", "#9C89A6", "#FFB000"]


# --- data --------------------------------------------------------------------

def load():
    df = pd.read_csv(DATA, encoding="utf-8")
    feats = [c for c in df.columns if c.startswith(("att_", "def_", "disc_"))]
    groups = {
        "ATTACKING_OUTPUT": [c for c in feats if c.startswith("att_")],
        "DEFENSIVE_ACTIVITY": [c for c in feats if c.startswith("def_")],
        "DISCIPLINE": [c for c in feats if c.startswith("disc_")],
    }
    assert "pos" not in feats, "position leaked into the feature matrix"
    assert df[feats].isna().sum().sum() == 0, "nulls in clustering features"
    return df, feats, groups


def group_variance_shares(z: np.ndarray, feats: list[str],
                          groups: dict[str, list[str]]) -> dict[str, float]:
    """Each group's share of total variance after scaling.

    Pairwise correlations cannot show whether one group dominates the distance
    metric in aggregate; this can. Five attacking features out of ten means
    attacking carries half the geometry regardless of how well-behaved any
    individual pair looks.
    """
    var = pd.Series(z.var(axis=0, ddof=1), index=feats)
    return {g: var[cols].sum() / var.sum() * 100 for g, cols in groups.items()}


# --- naming ------------------------------------------------------------------

def name_clusters(df: pd.DataFrame, feats: list[str],
                  labels: np.ndarray) -> dict[int, str]:
    """Names from feature means against the quartiles of the full 315.

    Fallback matters: at k=4 the largest cluster has no feature in either
    quartile -- it sits mid-range on all ten. A purely quartile-driven rule
    returns an empty string there, so magnitude relative to average is used
    instead. That a third of regular starters are statistically unremarkable
    on these axes is a finding about a continuous distribution, not a defect.
    """
    q1, q3 = df[feats].quantile(0.25), df[feats].quantile(0.75)
    means = df.assign(_c=labels).groupby("_c")[feats].mean()
    sd = df[feats].std()
    overall = df[feats].mean()

    names = {}
    for c in sorted(means.index):
        high = [LABELS[f] for f in feats if means.loc[c, f] >= q3[f]]
        low = [LABELS[f] for f in feats if means.loc[c, f] <= q1[f]]
        parts = []
        if high:
            parts.append("high " + ", ".join(high))
        if low:
            parts.append("low " + ", ".join(low))
        if parts:
            names[c] = "; ".join(parts).capitalize()
        else:
            mean_z = ((means.loc[c] - overall) / sd).mean()
            direction = "below" if mean_z < 0 else "above"
            names[c] = (f"Low involvement - {direction} average across all "
                        f"three groups (mean z {mean_z:+.2f}), no feature in "
                        f"either quartile")
    return names


# --- main --------------------------------------------------------------------

def main() -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    df, feats, groups = load()
    x = df[feats]
    print(f"{len(df):,} players, {len(feats)} features")
    for g, cols in groups.items():
        print(f"  {g:<20} {len(cols)}  {', '.join(cols)}")

    # --- 1. scaling comparison ----------------------------------------------
    print("\n" + "=" * 74)
    print("1. SCALING")
    print("=" * 74)
    scaled = {}
    for nm, sc in [("StandardScaler", StandardScaler()),
                   ("RobustScaler", RobustScaler())]:
        z = sc.fit_transform(x)
        scaled[nm] = z
        shares = group_variance_shares(z, feats, groups)
        heaviest = pd.Series(z.var(axis=0, ddof=1), index=feats).idxmax()
        hv = pd.Series(z.var(axis=0, ddof=1), index=feats).max()
        tot = pd.Series(z.var(axis=0, ddof=1), index=feats).sum()
        print(f"\n  {nm}")
        for g, s in shares.items():
            n = len(groups[g])
            print(f"    {g:<20} {n} feats  {s:>6.2f}%   "
                  f"(count share {n / len(feats) * 100:.1f}%)")
        print(f"    heaviest single feature: {heaviest} "
              f"({hv / tot * 100:.2f}%)")

    z_std = scaled["StandardScaler"]
    shares = group_variance_shares(z_std, feats, groups)
    for g, s in shares.items():
        expected = len(groups[g]) / len(feats) * 100
        assert abs(s - expected) < 0.01, (
            f"StandardScaler should equalise variance: {g} at {s:.2f}% "
            f"vs expected {expected:.1f}%"
        )
    print("\n  StandardScaler ships: group shares equal feature-count shares "
          "exactly,\n  so the weighting is visible rather than implicit. "
          "Attacking output carries\n  50% of the distance metric because it "
          "holds 5 of 10 features. Reported,\n  not corrected.")

    # --- 2. k selection ------------------------------------------------------
    print("\n" + "=" * 74)
    print("2. K SELECTION")
    print("=" * 74)
    print(f"\n  {'k':>3}{'inertia':>11}{'drop':>8}{'silhouette':>12}"
          f"{'CH':>9}{'DB':>7}{'smallest':>10}")
    sweep, prev = {}, None
    for k in K_RANGE:
        km = KMeans(n_clusters=k, n_init=25, random_state=SEED).fit(z_std)
        sil = silhouette_score(z_std, km.labels_)
        drop = "" if prev is None else f"{(prev - km.inertia_) / prev * 100:5.1f}%"
        sizes = np.bincount(km.labels_)
        print(f"  {k:>3}{km.inertia_:>11.1f}{drop:>8}{sil:>12.3f}"
              f"{calinski_harabasz_score(z_std, km.labels_):>9.1f}"
              f"{davies_bouldin_score(z_std, km.labels_):>7.2f}{sizes.min():>10}")
        sweep[k] = {"inertia": km.inertia_, "sil": sil}
        prev = km.inertia_

    best_sil = max(sweep, key=lambda k: sweep[k]["sil"])
    print(f"\n  silhouette maximum: k={best_sil} ({sweep[best_sil]['sil']:.3f})")
    print(f"  every value is below 0.25 -- the conventional threshold for "
          f"meaningful\n  structure. K-Means is largely imposing divisions on a "
          f"continuous cloud.")

    # --- 3. stability --------------------------------------------------------
    print("\n" + "=" * 74)
    print("3. STABILITY ACROSS SEEDS")
    print("=" * 74)
    print(f"\n  {'k':>3}{'mean ARI':>11}{'min ARI':>10}{'identical pairs':>18}")
    stability = {}
    for k in (2, 3, 4, 5, 6):
        labs = [KMeans(n_clusters=k, n_init=10, random_state=s).fit_predict(z_std)
                for s in range(SEEDS)]
        aris = [adjusted_rand_score(labs[i], labs[j])
                for i in range(SEEDS) for j in range(i + 1, SEEDS)]
        stability[k] = np.mean(aris)
        ident = sum(1 for a in aris if a > 0.999)
        print(f"  {k:>3}{np.mean(aris):>11.3f}{min(aris):>10.3f}"
              f"{f'{ident}/{len(aris)}':>18}")
    assert stability[K_CHOSEN] >= 0.9, (
        f"k={K_CHOSEN} stability degraded to {stability[K_CHOSEN]:.3f}; "
        f"clusters dissolve between seeds"
    )
    print(f"\n  k<=4 is stable; k>=5 collapses -- clusters genuinely dissolve "
          f"and re-form\n  depending on initialisation. Independent "
          f"corroboration of k={K_CHOSEN}.")

    # --- 4. group-normalised comparison (not shipped) -----------------------
    print("\n" + "=" * 74)
    print("4. GROUP-NORMALISED COMPARISON (comparison only, not shipped)")
    print("=" * 74)
    z_w = z_std.copy()
    for g, cols in groups.items():
        idx = [feats.index(c) for c in cols]
        z_w[:, idx] /= np.sqrt(len(cols))
    print("\n  Each group's features divided by sqrt(group size), equalising "
          "group\n  contribution at 33/33/33 instead of 50/20/30.\n")
    for k in (3, 4, 5):
        a = KMeans(n_clusters=k, n_init=25, random_state=SEED).fit_predict(z_std)
        b = KMeans(n_clusters=k, n_init=25, random_state=SEED).fit_predict(z_w)
        print(f"    k={k}: ARI = {adjusted_rand_score(a, b):.3f}")
    print("\n  ARI 0.835 at k=4 is a finding, not a reassurance: roughly one "
          "player in\n  six lands in a different cluster when the group "
          "weighting changes. The\n  clusters are robust in shape but not in "
          "membership, so any individual\n  assignment carries that caveat. "
          "The standard-weighted fit still ships,\n  because equalising groups "
          "is itself an arbitrary choice, not a neutral fix.")

    # --- 5. fit the chosen model --------------------------------------------
    print("\n" + "=" * 74)
    print(f"5. CLUSTERS AT k={K_CHOSEN}")
    print("=" * 74)
    km = KMeans(n_clusters=K_CHOSEN, n_init=25, random_state=SEED).fit(z_std)
    df["cluster"] = km.labels_
    names = name_clusters(df, feats, km.labels_)
    assert all(names.values()), "a cluster received an empty name"

    means = df.groupby("cluster")[feats].mean()
    zmeans = ((means - df[feats].mean()) / df[feats].std()).round(2)
    print("\n  Feature means as z-scores vs the full 315:")
    print(zmeans.to_string())
    print("\n  Sizes and generated names:")
    for c in sorted(names):
        n = int((df.cluster == c).sum())
        print(f"    cluster {c} (n={n:>3}, {n / len(df) * 100:4.1f}%): {names[c]}")

    # --- 6. validation against held-out position -----------------------------
    print("\n" + "=" * 74)
    print("6. VALIDATION AGAINST HELD-OUT POSITION")
    print("=" * 74)
    ct = pd.crosstab(df.cluster, df.pos)
    print("\n" + ct.to_string())
    print("\n  Position concentration per cluster:")
    for c in sorted(df.cluster.unique()):
        sub = df[df.cluster == c]
        top_pos = sub.pos.value_counts()
        share = top_pos.iloc[0] / len(sub) * 100
        # How much of that position, league-wide, this cluster captured.
        captured = top_pos.iloc[0] / (df.pos == top_pos.index[0]).sum() * 100
        print(f"    cluster {c}: most common pos {top_pos.index[0]!r} "
              f"= {share:.0f}% of the cluster, and {captured:.0f}% of all "
              f"{top_pos.index[0]!r} players league-wide")

    fw = df[df.pos == "FW"]
    if len(fw):
        dom = fw.cluster.value_counts()
        print(f"\n  Of {len(fw)} pure-FW players, {dom.iloc[0]} "
              f"({dom.iloc[0] / len(fw) * 100:.0f}%) sit in cluster "
              f"{dom.index[0]} -- that cluster substantially rediscovers a "
              f"position\n  label. The others do not: clusters mixing DF and "
              f"MF are where this adds\n  something beyond the team sheet.")

    # --- plots ---------------------------------------------------------------
    ks = list(sweep)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    ax[0].plot(ks, [sweep[k]["inertia"] for k in ks], "o-", color="#00FF87")
    ax[0].axvline(K_CHOSEN, ls="--", color="#E90052")
    ax[0].set_xlabel("k"); ax[0].set_ylabel("inertia")
    ax[0].set_title("Elbow"); ax[0].grid(alpha=0.3)
    ax[1].plot(ks, [sweep[k]["sil"] for k in ks], "o-", color="#04F5FF")
    ax[1].axhline(0.25, ls=":", color="#E90052")
    ax[1].axvline(K_CHOSEN, ls="--", color="#E90052")
    ax[1].set_xlabel("k"); ax[1].set_ylabel("silhouette")
    ax[1].set_title("Silhouette (dotted line = weak-structure threshold)")
    ax[1].grid(alpha=0.3)
    fig.suptitle("Choosing k: the two metrics disagree", fontweight="bold")
    fig.tight_layout(); fig.savefig(PLOTS / "01_k_selection.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.2))
    gnames = list(groups)
    w = 0.38
    for i, (nm, z) in enumerate(scaled.items()):
        s = group_variance_shares(z, feats, groups)
        ax.bar(np.arange(len(gnames)) + i * w, [s[g] for g in gnames],
               w, label=nm, color=PALETTE[i])
    ax.set_xticks(np.arange(len(gnames)) + w / 2)
    ax.set_xticklabels([f"{g}\n({len(groups[g])} feats)" for g in gnames],
                       fontsize=8)
    ax.set_ylabel("% of total variance")
    ax.set_title("Group share of the distance metric", fontweight="bold")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(PLOTS / "02_group_variance.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 4))
    im = ax.imshow(zmeans.to_numpy(), cmap="RdBu_r", vmin=-1.8, vmax=1.8,
                   aspect="auto")
    ax.set_xticks(range(len(feats)))
    ax.set_xticklabels([LABELS[f] for f in feats], rotation=40, ha="right",
                       fontsize=8)
    ax.set_yticks(range(K_CHOSEN))
    ax.set_yticklabels([f"cluster {c}\nn={int((df.cluster == c).sum())}"
                        for c in sorted(names)], fontsize=8)
    for i in range(K_CHOSEN):
        for j in range(len(feats)):
            v = zmeans.iloc[i, j]
            ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(v) > 1.0 else "black")
    fig.colorbar(im, ax=ax, shrink=0.8, label="z vs all 315")
    ax.set_title("Cluster feature means", fontweight="bold")
    fig.tight_layout(); fig.savefig(PLOTS / "03_cluster_profiles.png", dpi=130)
    plt.close(fig)

    p2 = PCA(n_components=2, random_state=SEED).fit(z_std)
    xy = p2.transform(z_std)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for c in sorted(names):
        m = df.cluster == c
        ax.scatter(xy[m, 0], xy[m, 1], s=18, alpha=0.7, color=PALETTE[c],
                   label=f"{c} (n={int(m.sum())})")
    ax.set_xlabel(f"PC1 ({p2.explained_variance_ratio_[0] * 100:.0f}% var)")
    ax.set_ylabel(f"PC2 ({p2.explained_variance_ratio_[1] * 100:.0f}% var)")
    ax.legend(fontsize=8)
    ax.set_title("PCA projection — display only", fontweight="bold")
    ax.text(0.5, -0.13, "Clustering happened in the full 10-D space; this 2-D "
                        f"view shows only "
                        f"{p2.explained_variance_ratio_[:2].sum() * 100:.0f}% "
                        "of the variance.",
            transform=ax.transAxes, ha="center", fontsize=8, style="italic")
    fig.tight_layout(); fig.savefig(PLOTS / "04_pca_scatter.png", dpi=130)
    plt.close(fig)

    print(f"\nWrote {len(list(PLOTS.glob('*.png')))} plots to {PLOTS}/")


if __name__ == "__main__":
    main()
