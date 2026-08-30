"""
03-style-finder : cleaning script
=================================
Builds a one-row-per-player table of Premier League ACTIVITY PROFILES, for
K-Means clustering into archetypes.

WHY "ACTIVITY PROFILE" AND NOT "PLAYING STYLE"
  This is a correction to the goal, not a caveat on it, and it is carried in
  the naming so that a later script cannot quietly reintroduce the wrong
  claim.

  Playing style in football analytics is largely a passing and ball-carrying
  distinction: what separates a deep-lying playmaker from a ball-winner is
  mostly distribution and progression, not shot counts. None of that is
  measurable here. Searching every standard FBref family against this
  dataset's 102 columns:

    passing (Cmp, Att, PrgP, KP)      NONE
    dribbles / take-ons (Succ, Take)  NONE
    expected goals (xG, xA)           NONE
    touches / carries                 NONE
    full defence (Tkl, Blocks, Press) only TklW and Int
    shooting                          complete

  What can be measured is attacking output, defensive activity and
  discipline. So the clusters this feeds will be activity profiles. The
  output file, the feature-group constants and every emitted column name say
  so; there is no STYLE_FEATURES anywhere in this project.

NO TARGET, SO NO LEAKAGE -- BUT TWO OTHER TRAPS
  Unlike projects 01 and 02 there is nothing to leak. The failure modes move:

  1. SCALE. Fed unscaled, Min alone accounts for 99.79% of total variance
     across candidate features. K-Means is distance-based, so it would
     cluster on playing time and nothing else -- "starters vs squad players",
     with every actual signal as rounding error. Scaling is therefore not a
     nicety here. It is not done in this script (it belongs inside the
     clustering pipeline, as in projects 01 and 02), but the feature choices
     below are made with it in mind.

  2. LOW-MINUTES NOISE. No minutes floor is applied upstream. Min starts at
     1. Sh/90 reaches 30.00 for a player with one shot in three minutes --
     the project-01 per-90 explosion in new clothes, and worse here, because
     an outlier does not merely skew a coefficient, it pulls a centroid and
     can claim an entire cluster.

PER-90 ONLY, NO RAW COUNTS
  Settled by the data. Even after the 900-minute floor, Min spans 901 to
  3,420 -- a 3.7x range -- and raw counts inherit it: Int correlates 0.636
  with minutes, TklW 0.582, Fls 0.571. Raw interceptions measure availability
  as much as inclination. Every per-90 version sits at |r| < 0.07.

  Emitting both forms would repeat project 01's pl_matches / pl_minutes
  problem, except that in K-Means the consequence is not an unstable
  coefficient but a silently doubled weight in the distance metric.

Reads : data/raw/football-players-stats-2025-2026/players_data-2025_2026.csv
Writes: data/processed/pl_player_profiles.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw/football-players-stats-2025-2026/players_data-2025_2026.csv")
OUT = Path("data/processed/pl_player_profiles.csv")

# The country prefix is load-bearing. "Premier League" matches zero rows and
# fails silently; the assertion below is what turns that into an error.
COMPETITION = "eng Premier League"
MIN_MINUTES = 900

# --- feature groups ----------------------------------------------------------
# Named by what they actually measure. See the docstring: there is deliberately
# no STYLE_FEATURES constant in this project.

ATTACKING_OUTPUT = {
    "att_gls_p90": "Gls",     # goals
    "att_ast_p90": "Ast",     # assists
    "att_sh_p90": "Sh",       # shot volume
    "att_crs_p90": "Crs",     # crosses -- delivery
}
DEFENSIVE_ACTIVITY = {
    "def_int_p90": "Int",     # interceptions
    "def_tklw_p90": "TklW",   # tackles won
}
DISCIPLINE = {
    "disc_fls_p90": "Fls",    # fouls committed
    "disc_fld_p90": "Fld",    # fouls drawn
    "disc_crdy_p90": "CrdY",  # yellow cards
}

# Already a rate in the source, so it is not divided by 90s.
RATE_FEATURES = {"att_sot_pct": "SoT%"}

PER90 = {**ATTACKING_OUTPUT, **DEFENSIVE_ACTIVITY, **DISCIPLINE}
CLUSTER_FEATURES = list(PER90) + list(RATE_FEATURES)

GROUPS = {
    "ATTACKING_OUTPUT": list(ATTACKING_OUTPUT) + list(RATE_FEATURES),
    "DEFENSIVE_ACTIVITY": list(DEFENSIVE_ACTIVITY),
    "DISCIPLINE": list(DISCIPLINE),
}

# SoT/90 is deliberately absent. It is the redundant middle term of the
# shooting block -- volume x accuracy -- correlating 0.92 with Sh/90 and 0.87
# with Gls/90. In K-Means that is not a coefficient problem, it is implicit
# weighting: three near-identical shooting features means shooting votes three
# times in every distance calculation while defensive activity votes twice.
# Dropping it takes the worst pairwise correlation from 0.92 to 0.78.
#
# G/Sh and G/SoT are also absent: conversion rates, 20 of 315 null, and close
# to pure noise at single-season sample sizes.


def main() -> None:
    steps: list[tuple[str, int]] = []

    df = pd.read_csv(RAW, encoding="utf-8", low_memory=False)
    steps.append(("file loaded", len(df)))

    # --- league --------------------------------------------------------------
    pl = df[df["Comp"] == COMPETITION].copy()
    if pl.empty:
        raise SystemExit(
            f"No rows matched Comp == {COMPETITION!r}. The Comp column carries "
            f"a country prefix; found values: {sorted(df['Comp'].unique())}"
        )
    steps.append((f"Comp == {COMPETITION!r}", len(pl)))

    # --- goalkeepers ---------------------------------------------------------
    # Excluded, not clustered separately: their 11 keeper columns are null for
    # every outfielder and their outfield stats are near-zero, so including
    # them guarantees one trivial GK cluster that says nothing.
    by_pos = pl["Pos"].str.contains("GK")
    by_stats = pl["GA"].notna()
    assert (by_pos == by_stats).all(), (
        "Goalkeeper identification disagrees between Pos and the keeper stat "
        "columns; investigate before trusting the exclusion."
    )
    pl = pl[~by_pos]
    steps.append(("exclude goalkeepers", len(pl)))

    # --- minutes floor -------------------------------------------------------
    pl = pl[pl["Min"] >= MIN_MINUTES]
    steps.append((f"Min >= {MIN_MINUTES}", len(pl)))

    # --- derive per-90 rates -------------------------------------------------
    out = pd.DataFrame(index=pl.index)
    out["player"] = pl["Player"]
    out["squad"] = pl["Squad"]
    out["pos"] = pl["Pos"]           # validation only -- never a feature
    out["age"] = pl["Age"]
    out["minutes"] = pl["Min"]
    out["nineties"] = pl["90s"]

    for name, src in PER90.items():
        out[name] = pl[src] / pl["90s"]

    # SoT% is null exactly for players who never shot. Imputed to 0.0 rather
    # than left as NaN, which departs from project 01 on purpose: there the
    # residual nulls sat in UNUSED columns, whereas this is a clustering
    # feature and scikit-learn's KMeans rejects NaN outright.
    #
    # 0.0 is correct rather than merely convenient. A player who has put
    # nothing on target has an on-target rate of nothing -- the same statement
    # as a player who took ten shots and hit none -- and it is consistent with
    # their att_sh_p90 of 0. Dropping them would discard real regular
    # starters; median imputation would assert an accuracy never demonstrated.
    out["has_zero_shots"] = pl["Sh"].eq(0)
    out["att_sot_pct"] = pl["SoT%"].fillna(0.0)

    # Raw counts, for reporting and cluster naming. Not clustered on.
    for name, src in PER90.items():
        out[f"raw_{src.lower()}"] = pl[src]

    out = out.sort_values("minutes", ascending=False).reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, encoding="utf-8")

    # --- verification --------------------------------------------------------
    nulls = out[CLUSTER_FEATURES].isna().sum().sum()
    assert nulls == 0, f"{nulls} nulls remain in clustering features"

    # The check that the minutes confound is actually gone, not just intended.
    #
    # The bound is 0.25, not 0.10. Two features retain a mild residual after
    # the per-90 conversion -- def_int_p90 at +0.15 and disc_fls_p90 at -0.13 --
    # and that appears to be signal rather than arithmetic. Per-90 does its job
    # everywhere (Int falls 0.636 -> 0.152, TklW 0.582 -> -0.010, Fls 0.571 ->
    # -0.129); what is left is that players who accumulate minutes skew toward
    # defensive roles, so they intercept more per 90 as well as in total. That
    # is a real relationship between role and selection, not a denominator
    # artefact, and suppressing it would mean discarding a true signal.
    MAX_MINUTES_CORR = 0.25
    bad = {f: round(out[f].corr(out["minutes"]), 3) for f in PER90
           if abs(out[f].corr(out["minutes"])) >= MAX_MINUTES_CORR}
    assert not bad, (
        f"per-90 features still confounded with minutes beyond "
        f"{MAX_MINUTES_CORR}: {bad}"
    )

    # --- report --------------------------------------------------------------
    print("Filter funnel")
    for label, n in steps:
        print(f"  {label:<34} {n:>6,}")
    print(f"\nWrote {OUT}  ({len(out):,} rows x {len(out.columns)} cols)")
    print(f"  {len(CLUSTER_FEATURES)} clustering features, "
          f"{len(out.columns) - len(CLUSTER_FEATURES)} descriptive")
    print(f"  squads {out.squad.nunique()}, "
          f"{out.groupby('squad').size().min()}-{out.groupby('squad').size().max()}"
          f" players each")
    print(f"  minutes {out.minutes.min():,} to {out.minutes.max():,}")

    print("\nFeature groups")
    for g, cols in GROUPS.items():
        print(f"  {g:<20} {len(cols)}  {', '.join(cols)}")

    print("\nZero-shot players (att_sot_pct imputed to 0.0):"
          f" {int(out.has_zero_shots.sum())}")
    if out.has_zero_shots.any():
        print(out.loc[out.has_zero_shots,
                      ["player", "squad", "pos", "minutes"]]
              .to_string(index=False))

    print("\nMinutes confound, before and after the per-90 conversion:")
    print(f"  {'feature':<16}{'raw vs Min':>12}{'per-90 vs Min':>15}")
    for f, src in PER90.items():
        raw_r = pl[src].corr(pl["Min"])
        print(f"  {f:<16}{raw_r:>12.3f}{out[f].corr(out['minutes']):>15.3f}")
    # ASCII only: this script has no stdout reconfiguration and the Windows
    # console default mangles non-ASCII.
    print(f"  {'att_sot_pct':<16}{'n/a':>12}"
          f"{out['att_sot_pct'].corr(out['minutes']):>15.3f}"
          f"   (already a rate)")

    print("\nClustering-feature summary:")
    print(out[CLUSTER_FEATURES].describe().T[
        ["mean", "std", "min", "50%", "max"]].round(2).to_string())

    print("\nCorrelation pairs above 0.7 (implicit weighting in K-Means):")
    corr = out[CLUSTER_FEATURES].corr()
    flagged = [(i, j, corr.loc[i, j])
               for n, i in enumerate(corr.index)
               for j in corr.columns[n + 1:]
               if abs(corr.loc[i, j]) > 0.7]
    if flagged:
        for i, j, v in sorted(flagged, key=lambda t: -abs(t[2])):
            print(f"  {i:<16} {j:<16} r = {v:+.3f}")
    else:
        print("  none")
    print(f"  max |r| across all pairs: "
          f"{corr.where(~np.eye(len(corr), dtype=bool)).abs().max().max():.3f}")

    print("\nPosition breakdown (held out for validation, never a feature):")
    print(out.pos.value_counts().to_string())


if __name__ == "__main__":
    main()
