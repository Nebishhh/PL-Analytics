"""
01-value-predictor : cleaning script
====================================
Builds a one-row-per-player modelling table for predicting the current
Transfermarkt market value (EUR) of a Premier League player from their
career-to-date Premier League performance.

Design decisions (agreed in the Step 1 schema review):

  TARGET   players.market_value_in_eur -- the current snapshot value.
           We deliberately do NOT use player_valuations.csv (the point-in-time
           series). That would be the stronger dataset (656k rows, zero nulls)
           but it needs a time-windowed join and produces ~15 correlated rows
           per player. The snapshot keeps this a clean linear-regression problem.

  SCOPE    Premier League only, applied on BOTH sides:
             - the player's current club is in GB1, and
             - performance features aggregate only GB1 appearances.

  ACTIVE-PLAYER CRITERION
           last_season in {2024, 2025}.
           This is an explicit inclusion criterion, not a cleaning step.
           Rationale: players.market_value_in_eur is a *current* snapshot, so
           retired and inactive players lose it. Null-target rate across the
           full file runs 3-5% for 2012-2020 but climbs to 11.4% (2023),
           58.8% (2024) and 17.4% (2025). Training on non-null rows across all
           seasons would silently mean "players still active today" without
           ever saying so. Restricting to recent seasons makes it explicit.

           CAVEAT, worth knowing before trusting the coefficients: this limits
           the bias, it does not remove it. Within the GB1 scope the 2024
           cohort is 147 players of whom 36 (24.5%) have a null target and are
           dropped below. The survivors are still a selected subset -- the ones
           Transfermarkt continues to value. The 2025 cohort (826 players, 134
           null) is much closer to a full population. If the 2024 rows look
           influential in residual plots, try ACTIVE_SEASONS = (2025,) and
           compare.

  MINUTES THRESHOLD
           pl_minutes >= 900 (one full season's worth). Also an explicit
           inclusion criterion, not a cleaning step, and the single most
           consequential filter in this script.

           Two reasons, one arithmetic and one substantive.

           Arithmetic: the per-90 rates are computed as events * 90 / minutes,
           so at tiny minute counts they are not rates, they are noise with a
           huge denominator effect. One player had 38 PL minutes and 1 assist
           -> assists_per90 = 2.37, a z-score of 17.7 (Haaland's goals_per90
           is 0.91 for comparison). A linear model in log space multiplies
           that by a positive coefficient, extrapolates far outside the
           training range, and exp() turns the result into a EUR981bn
           prediction. Keeping the raw counting stats alongside the rates does
           not help, because the broken rate is still in the design matrix.

           Substantive, and the more important half: sub-500-minute players
           are academy and fringe signings whose market value is driven by
           potential and transfer hype, not by Premier League output. They are
           not noisy observations of a signal we can model -- they are
           unmodellable from career appearance data. No feature in this table
           can see them.

           Measured effect, 5-fold CV on log(value):
             no threshold  R^2 0.158 +/- 0.161   (folds ranged -0.43 to +0.44)
             >= 450 min    R^2 0.641 +/- 0.059
             >= 900 min    R^2 0.663 +/- 0.061   <- chosen
             >= 1800 min   R^2 0.725 +/- 0.034
           Shrinking the rates toward the league mean instead of thresholding
           only reached 0.27, and adds nothing once the threshold is applied.

           900 over 1800 is a deliberate trade: 1800 scores better but drops a
           further 75 players and starts selecting for "established starter",
           which narrows what the model can be asked about.

  LEAKAGE  highest_market_value_in_eur is dropped. It is a direct function of
           the target and is null in exactly the same 8,621 rows.

  AGE      Derived; there is no age column anywhere in the dataset. Computed
           as of AS_OF_DATE from date_of_birth. Rows with a missing or
           implausible age (<14 or >50) are dropped rather than repaired --
           they are scrape artifacts, not recoverable signal.

Reads : data/raw/players.csv, data/raw/appearances.csv
Writes: data/processed/pl_player_values.csv              (498 rows, modelling)
        data/processed/pl_player_values_prethreshold.csv (661 rows, app list)
"""

from pathlib import Path

import numpy as np
import pandas as pd

# --- configuration -----------------------------------------------------------

RAW = Path("data/raw")
OUT = Path("data/processed/pl_player_values.csv")

# Same columns, before the minutes threshold. Backs the Streamlit app's
# player list so that a below-threshold player can be shown the reason he is
# not predictable, rather than simply being absent from the dropdown.
OUT_PRETHRESHOLD = Path("data/processed/pl_player_values_prethreshold.csv")

COMPETITION = "GB1"          # Premier League
ACTIVE_SEASONS = (2024, 2025)
AGE_MIN, AGE_MAX = 14, 50

# Fixed rather than date.today() so the table is reproducible: re-running this
# script in six months should not silently shift every age by half a year.
AS_OF_DATE = pd.Timestamp("2026-08-29")

# Require that the player has actually played in the Premier League. Set to
# False to keep squad members with zero PL appearances (adds ~142 rows whose
# performance features are all exactly zero). Note that any MIN_PL_MINUTES > 0
# already implies this, so the flag only bites when the threshold is 0.
REQUIRE_PL_APPEARANCE = True

# Minimum Premier League minutes to be modelled at all. See the MINUTES
# THRESHOLD note in the module docstring -- this is the filter that takes CV
# R^2 from 0.16 to 0.66 and cuts fold-to-fold variance by a factor of five.
# Set to 0 to disable and reproduce the original unfiltered table.
MIN_PL_MINUTES = 900


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Final column set, shared by both output tables so they cannot drift.

    highest_market_value_in_eur is intentionally absent (leakage).
    """
    return df[[
        "player_id", "name", "age", "position", "sub_position", "foot",
        "height_in_cm", "country_of_citizenship", "current_club_id",
        "current_club_name", "last_season", "contract_expiration_date",
        "pl_matches", "pl_goals", "pl_assists", "pl_minutes",
        "pl_yellow_cards", "pl_red_cards", "goals_per90", "assists_per90",
        "market_value_in_eur",
    ]].sort_values(
        # player_id as a tiebreak, with a stable sort: market values are highly
        # tied (dozens of players at exactly EUR50m), and an unstable sort makes
        # row order depend on how many rows were passed in. Without this, the
        # 498-row table reorders itself whenever the 661-row table is written
        # first, producing a 500-line diff that contains no actual change.
        ["market_value_in_eur", "player_id"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)


def main() -> None:
    steps: list[tuple[str, int]] = []

    # --- load ----------------------------------------------------------------
    # encoding is explicit: names carry accents (Sergio, Muller) and the
    # Windows console default mangles them.
    players = pd.read_csv(RAW / "players.csv", encoding="utf-8", low_memory=False)
    steps.append(("players.csv loaded", len(players)))

    appearances = pd.read_csv(
        RAW / "appearances.csv",
        encoding="utf-8",
        low_memory=False,
        usecols=[
            "player_id", "competition_id", "goals", "assists",
            "minutes_played", "yellow_cards", "red_cards",
        ],
    )

    # --- filter players ------------------------------------------------------
    players = players[players["last_season"].isin(ACTIVE_SEASONS)]
    steps.append((f"last_season in {ACTIVE_SEASONS}", len(players)))

    players = players[players["current_club_domestic_competition_id"] == COMPETITION]
    steps.append((f"current club in {COMPETITION}", len(players)))

    # Target must be present. This is the survivorship drop described above.
    players = players[players["market_value_in_eur"].notna()]
    steps.append(("non-null market_value_in_eur", len(players)))

    # --- derive age ----------------------------------------------------------
    dob = pd.to_datetime(players["date_of_birth"], errors="coerce")
    players = players.assign(age=(AS_OF_DATE - dob).dt.days / 365.25)

    players = players[players["age"].notna()]
    steps.append(("parseable date_of_birth", len(players)))

    players = players[players["age"].between(AGE_MIN, AGE_MAX)]
    steps.append((f"plausible age ({AGE_MIN}-{AGE_MAX})", len(players)))

    # --- aggregate Premier League career-to-date performance -----------------
    # No look-ahead concern here: the target is "value now" and the features are
    # "everything up to now", so the whole GB1 career is in-window.
    pl = appearances[appearances["competition_id"] == COMPETITION]
    perf = (
        pl.groupby("player_id")
        .agg(
            pl_matches=("player_id", "size"),
            pl_goals=("goals", "sum"),
            pl_assists=("assists", "sum"),
            pl_minutes=("minutes_played", "sum"),
            pl_yellow_cards=("yellow_cards", "sum"),
            pl_red_cards=("red_cards", "sum"),
        )
        .reset_index()
    )

    how = "inner" if REQUIRE_PL_APPEARANCE else "left"
    df = players.merge(perf, on="player_id", how=how)
    steps.append((
        "joined PL appearances" + ("" if REQUIRE_PL_APPEARANCE else " (left)"),
        len(df),
    ))

    count_cols = ["pl_matches", "pl_goals", "pl_assists",
                  "pl_minutes", "pl_yellow_cards", "pl_red_cards"]
    df[count_cols] = df[count_cols].fillna(0).astype(int)

    # Per-90 rates. Guarded: 3 appearance rows dataset-wide have 0 minutes, so
    # a player could in principle total 0 and divide by zero. Computed before
    # the minutes threshold so the pre-threshold table carries them too -- the
    # app displays them, it just does not feed them to the model.
    minutes = df["pl_minutes"].to_numpy(dtype=float)
    for src, dest in [("pl_goals", "goals_per90"), ("pl_assists", "assists_per90")]:
        df[dest] = np.where(minutes > 0, df[src].to_numpy() * 90.0 / minutes, 0.0)

    df = select_columns(df)

    # --- write the pre-threshold table ---------------------------------------
    # Every PL player with at least one appearance, including those below the
    # minutes threshold. The Streamlit app uses this for its player list, so
    # that a player who does not qualify can be shown an explanation instead
    # of silently not existing. Nothing is trained on this file.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PRETHRESHOLD, index=False, encoding="utf-8")
    below = int((df["pl_minutes"] < MIN_PL_MINUTES).sum())

    # --- apply the threshold and write the modelling table -------------------
    # Applied after the join, since pl_minutes only exists once aggregated.
    df = df[df["pl_minutes"] >= MIN_PL_MINUTES].reset_index(drop=True)
    steps.append((f"pl_minutes >= {MIN_PL_MINUTES}", len(df)))

    df.to_csv(OUT, index=False, encoding="utf-8")

    # --- report --------------------------------------------------------------
    print("Filter funnel")
    for label, n in steps:
        print(f"  {label:<34} {n:>7,}")
    print(f"\nWrote {OUT_PRETHRESHOLD}  "
          f"({len(df) + below:,} rows -- app player list, {below} below threshold)")
    print(f"Wrote {OUT}  ({len(df):,} rows x {len(df.columns)} cols)")
    print(
        f"Target: market_value_in_eur  "
        f"min {df.market_value_in_eur.min():,.0f}  "
        f"median {df.market_value_in_eur.median():,.0f}  "
        f"max {df.market_value_in_eur.max():,.0f}"
    )
    print("\nRemaining nulls:")
    nulls = df.isna().sum()
    print(nulls[nulls > 0].to_string() if nulls.any() else "  none")


if __name__ == "__main__":
    main()
