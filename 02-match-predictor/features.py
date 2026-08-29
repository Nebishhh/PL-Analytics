"""
02-match-predictor : feature engineering
========================================
Builds a one-row-per-match table for Premier League Win/Draw/Loss
classification, from the home team's perspective.

THE GOVERNING RULE: every feature must be knowable days before kickoff.
The Step 1 leakage audit found that games.csv is actively booby-trapped, so
this script builds its features from raw results rather than trusting any
column that describes state.

  EXCLUDED, confirmed post-match:
    aggregate                  - literally "{home_goals}:{away_goals}", 100%
                                 of GB1 rows. The final score as a string.
    home/away_club_position    - the league position AFTER the match, result
                                 included. Verified over 10,640 club-match
                                 rows: the recorded value matches a table
                                 rebuilt INCLUDING the match 69.4% of the
                                 time, versus 40.5% EXCLUDING it. This is the
                                 subtle one -- position does vary within a
                                 season (6.74 distinct values per club-season)
                                 which makes it look like point-in-time data.
                                 It is point-in-time, just the wrong point.
    club_games.is_win          - cannot express a draw. All 2,538 drawn
                                 club-games carry is_win = 0, identical to
                                 losses.
    attendance, formations     - excluded by decision: the prediction boundary
                                 is "known days before kickoff", not "known at
                                 kickoff". Team sheets and turnstile counts
                                 fail that test even though neither is caused
                                 by the result.

  Everything below is derived from prior matches only. Rolling windows are
  shifted by one so the current match never enters its own features, and the
  league table is rebuilt by walking fixtures in date order.

SEASON BOUNDARY
  Rolling form is computed within a club-season; nothing carries across the
  summer, when squads change substantially. That leaves the opening matchdays
  with little or no history, so the first 5 matchdays of each club-season are
  dropped. A match survives only if BOTH clubs are at matchday 6 or later.

  Consequence worth knowing: the last-10 window is still partial for
  matchdays 6-10, holding 5 to 9 matches rather than 10. min_periods=1 means
  those are averaged over what exists rather than being null. The
  *_l10_matches columns record the true window size so this is auditable
  rather than hidden.

REST DAYS
  Computed from the club's full fixture list across ALL competitions, not
  just the Premier League. A club that played a midweek cup tie is genuinely
  less rested, and measuring rest from league matches alone would report a
  fortnight where there were three days.

PER-GAME RATES
  pre_points and pre_gd are accumulated season totals, which are confounded
  with how far into the season the match falls. pre_ppg and pre_gd_per_game
  divide by matches played; see add_per_game_rates for the numbers. Both the
  raw and per-game forms are written out.

Reads : data/raw/club_games.csv, data/raw/games.csv
Writes: data/processed/pl_matches_features.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed/pl_matches_features.csv")

COMPETITION = "GB1"
DROP_FIRST_MATCHDAYS = 5
SHORT, LONG = 5, 10        # rolling window lengths, in matches
VENUE_WINDOW = 5           # rolling window for the home/away split


# --- loading -----------------------------------------------------------------

def load_long_frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (GB1 club-match rows, all-competition club-match rows).

    club_games.csv is already one row per club per match, which is the shape
    rolling form wants. games.csv would need a union of its home and away
    column sets to get here.
    """
    cg = pd.read_csv(RAW / "club_games.csv", encoding="utf-8", low_memory=False)
    g = pd.read_csv(
        RAW / "games.csv", encoding="utf-8", low_memory=False,
        usecols=["game_id", "competition_id", "season", "date",
                 "home_club_id", "home_club_name", "away_club_name"],
    )
    g["date"] = pd.to_datetime(g["date"])

    every = cg.merge(g[["game_id", "competition_id", "season", "date"]],
                     on="game_id", how="inner")

    league = (
        cg.merge(g, on="game_id", how="inner")
          .query("competition_id == @COMPETITION")
          .copy()
    )
    # own_goals / opponent_goals, never is_win -- see the docstring.
    league["pts"] = np.select(
        [league.own_goals > league.opponent_goals,
         league.own_goals == league.opponent_goals],
        [3, 1], default=0,
    )
    league["gd"] = league.own_goals - league.opponent_goals
    league["is_home"] = league.hosting.eq("Home")
    league = league.sort_values(["date", "game_id"]).reset_index(drop=True)
    return league, every


# --- rolling form ------------------------------------------------------------

def add_rolling(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling form over the previous N matches, within a club-season.

    .shift(1) before .rolling() is what keeps the current match out of its own
    features. Without it every row would carry its own result and the whole
    exercise would be pointless.
    """
    df = df.sort_values(["club_id", "season", "date"]).copy()
    grp = df.groupby(["club_id", "season"], sort=False)

    df["matchday"] = grp.cumcount() + 1

    for win, tag in [(SHORT, f"l{SHORT}"), (LONG, f"l{LONG}")]:
        for src, name in [("pts", "pts"), ("own_goals", "gf"),
                          ("opponent_goals", "ga")]:
            df[f"{name}_{tag}"] = grp[src].transform(
                lambda s, w=win: s.shift(1).rolling(w, min_periods=1).mean()
            )
        df[f"gd_{tag}"] = df[f"gf_{tag}"] - df[f"ga_{tag}"]
        # True window size, so partial windows are visible rather than implied.
        df[f"{tag}_matches"] = grp["pts"].transform(
            lambda s, w=win: s.shift(1).rolling(w, min_periods=1).count()
        )

    # Home/away split: a club's form at this venue specifically, which is a
    # different quantity from its overall form and the reason home advantage
    # is worth modelling per club rather than as one global constant.
    vgrp = df.groupby(["club_id", "season", "is_home"], sort=False)
    for src, name in [("pts", "pts"), ("own_goals", "gf"),
                      ("opponent_goals", "ga")]:
        df[f"venue_{name}_l{VENUE_WINDOW}"] = vgrp[src].transform(
            lambda s: s.shift(1).rolling(VENUE_WINDOW, min_periods=1).mean()
        )
    df["venue_matches"] = vgrp["pts"].transform(
        lambda s: s.shift(1).rolling(VENUE_WINDOW, min_periods=1).count()
    )
    return df


# --- pre-match league table and head-to-head ---------------------------------

def add_table_and_h2h(league: pd.DataFrame) -> pd.DataFrame:
    """Rebuild the league position each club held BEFORE kickoff, plus the
    head-to-head record between the two clubs before this meeting.

    Written as an explicit chronological walk rather than a vectorised
    groupby. The whole point is that state is read before the result is
    applied, and a loop makes that ordering checkable by eye. It is also
    cheap: ~5,300 matches.

    Matches on the same date all read the table as it stood at the start of
    that day, which is what a supporter reading a Saturday morning paper
    would see.
    """
    league = league.sort_values(["date", "game_id"]).reset_index(drop=True)
    out_pos, out_pts, out_gd = {}, {}, {}
    h2h_n, h2h_pts = {}, {}

    for season, block in league.groupby("season", sort=True):
        table = {c: {"pts": 0, "gf": 0, "ga": 0}
                 for c in block.club_id.unique()}

        for date, day in block.groupby("date", sort=True):
            # --- read state as it stands at the start of this day ---------
            ranked = sorted(
                table.items(),
                key=lambda kv: (-kv[1]["pts"],
                                -(kv[1]["gf"] - kv[1]["ga"]),
                                -kv[1]["gf"]),
            )
            rank = {club: i + 1 for i, (club, _) in enumerate(ranked)}

            for row in day.itertuples():
                out_pos[row.Index] = rank[row.club_id]
                out_pts[row.Index] = table[row.club_id]["pts"]
                out_gd[row.Index] = (table[row.club_id]["gf"]
                                     - table[row.club_id]["ga"])

                key = frozenset((row.club_id, row.opponent_id))
                prior = h2h_pts.get(key, {}).get(row.club_id, 0)
                n = h2h_n.get(key, 0)
                league.loc[row.Index, "h2h_matches"] = n
                league.loc[row.Index, "h2h_pts_per_match"] = (
                    prior / n if n else np.nan
                )

            # --- only now apply this day's results ------------------------
            for row in day.itertuples():
                t = table[row.club_id]
                t["pts"] += row.pts
                t["gf"] += row.own_goals
                t["ga"] += row.opponent_goals

                key = frozenset((row.club_id, row.opponent_id))
                # Each match appears twice (once per club), so count halves.
                h2h_n[key] = h2h_n.get(key, 0) + 0.5
                h2h_pts.setdefault(key, {})
                h2h_pts[key][row.club_id] = (
                    h2h_pts[key].get(row.club_id, 0) + row.pts
                )

    league["pre_position"] = pd.Series(out_pos)
    league["pre_points"] = pd.Series(out_pts)
    league["pre_gd"] = pd.Series(out_gd)
    return league


# --- rest days ---------------------------------------------------------------

def add_per_game_rates(league: pd.DataFrame) -> pd.DataFrame:
    """Per-game versions of the accumulated season totals.

    Raw accumulated points measure how far into the season we are as much as
    how good the team is: corr(pre_points, matchday) = 0.761, with the mean
    running from 9.4 points at matchdays 6-10 to 45.5 at matchdays 30-38.
    Thirty points is top-four form in October and mid-table in March, and a
    linear model reading the raw column cannot tell those apart.

    Dividing by matches played drops that correlation to 0.022.

    Differencing the raw totals does not fix this on its own, because the two
    clubs have not always played the same number of matches -- home_matchday
    differs from away_matchday in 19.5% of matches (games in hand).

    The raw totals are kept in the output as well: tree models can recover the
    same information by splitting on matchday, and they remain useful for
    reporting a real league table.
    """
    played = league["matchday"] - 1
    # matchday 1 has no prior matches; those rows are dropped later by the
    # season-boundary filter, but guard rather than emit inf.
    league["pre_ppg"] = np.where(played > 0, league["pre_points"] / played,
                                 np.nan)
    league["pre_gd_per_game"] = np.where(played > 0, league["pre_gd"] / played,
                                         np.nan)
    return league


def add_rest_days(league: pd.DataFrame, every: pd.DataFrame) -> pd.DataFrame:
    """Days since the club's previous fixture in ANY competition."""
    e = every[["club_id", "game_id", "date"]].drop_duplicates()
    e = e.sort_values(["club_id", "date"])
    e["prev_date"] = e.groupby("club_id")["date"].shift(1)
    e["rest_days"] = (e["date"] - e["prev_date"]).dt.days
    return league.merge(e[["club_id", "game_id", "rest_days"]],
                        on=["club_id", "game_id"], how="left")


# --- assembly ----------------------------------------------------------------

FEATURES = (
    [f"{n}_l{w}" for w in (SHORT, LONG) for n in ("pts", "gf", "ga", "gd")]
    + [f"l{w}_matches" for w in (SHORT, LONG)]
    + [f"venue_{n}_l{VENUE_WINDOW}" for n in ("pts", "gf", "ga")]
    + ["venue_matches", "pre_position", "pre_points", "pre_gd",
       "pre_ppg", "pre_gd_per_game",
       "rest_days", "h2h_matches", "h2h_pts_per_match", "matchday"]
)


def main() -> None:
    league, every = load_long_frame()
    print(f"GB1 club-match rows loaded: {len(league):,} "
          f"(= 2 x {len(league) // 2:,} matches)")

    league = add_rolling(league)
    league = add_table_and_h2h(league)
    league = add_per_game_rates(league)
    league = add_rest_days(league, every)

    home = league[league.is_home].set_index("game_id")
    away = league[~league.is_home].set_index("game_id")

    df = pd.DataFrame(index=home.index)
    df["date"] = home["date"]
    df["season"] = home["season"]
    df["home_club_id"] = home["club_id"]
    df["away_club_id"] = away["club_id"]
    df["home_club_name"] = home["home_club_name"]
    df["away_club_name"] = home["away_club_name"]

    for f in FEATURES:
        df[f"home_{f}"] = home[f]
        df[f"away_{f}"] = away[f]

    # Differences: for most linear and tree models the gap between the two
    # sides carries the signal more directly than the two levels do.
    for f in ["pts_l5", "gf_l5", "ga_l5", "gd_l5",
              "pts_l10", "gf_l10", "ga_l10", "gd_l10",
              "pre_position", "pre_points", "pre_gd",
              "pre_ppg", "pre_gd_per_game", "rest_days"]:
        df[f"diff_{f}"] = df[f"home_{f}"] - df[f"away_{f}"]

    # h2h_pts_per_match is recorded per club, so the home side's figure is the
    # informative one; the away side's is its complement.
    df["h2h_matches"] = home["h2h_matches"]
    df["h2h_home_pts_per_match"] = home["h2h_pts_per_match"]
    df = df.drop(columns=["home_h2h_matches", "away_h2h_matches",
                          "home_h2h_pts_per_match", "away_h2h_pts_per_match"])

    df["target"] = np.select(
        [home.own_goals > home.opponent_goals,
         home.own_goals == home.opponent_goals],
        ["H", "D"], default="A",
    )

    before = len(df)
    keep = (df.home_matchday > DROP_FIRST_MATCHDAYS) & \
           (df.away_matchday > DROP_FIRST_MATCHDAYS)
    df = df[keep].sort_values("date").reset_index()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8")

    # --- report --------------------------------------------------------------
    print(f"\nSeason-boundary filter (drop first {DROP_FIRST_MATCHDAYS} "
          f"matchdays per club-season)")
    print(f"  matches before : {before:,}")
    print(f"  matches after  : {len(df):,}")
    print(f"  cost           : {before - len(df):,} rows "
          f"({(before - len(df)) / before * 100:.1f}%)")

    print(f"\nWrote {OUT}  ({len(df):,} rows x {len(df.columns)} cols)")

    print("\nClass balance:")
    vc = df.target.value_counts()
    for k in ("H", "D", "A"):
        print(f"  {k}  {vc[k]:>5,}  {vc[k] / len(df) * 100:5.1f}%")
    print(f"  majority-class baseline: {vc.max() / len(df) * 100:.1f}%")

    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]
    print("\nNull counts:")
    print(nulls.to_string() if len(nulls) else "  none")

    print("\nPartial rolling windows (expected on matchdays 6-10):")
    for c in ["home_l10_matches", "away_l10_matches",
              "home_venue_matches", "away_venue_matches"]:
        print(f"  {c:<22} min {df[c].min():.0f}  "
              f"median {df[c].median():.0f}  max {df[c].max():.0f}")


if __name__ == "__main__":
    main()
