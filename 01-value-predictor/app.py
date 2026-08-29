"""
01-value-predictor : Streamlit app
==================================
Interactive market-value estimates for Premier League players.

Run with:
    streamlit run 01-value-predictor/app.py

Three deliberate constraints, each of which is a limitation made visible
rather than papered over:

  1. The player list is a closed set, read from the pre-threshold table.
     There is no free-text stat entry. The model was fitted on 498 real
     players and has no business extrapolating to invented ones -- a form
     that accepts "42 goals in 300 minutes" would return a confident number
     for a player who cannot exist.

  2. Players below 900 Premier League minutes get an explanation instead of
     a prediction. They are in the dropdown precisely so the refusal can be
     shown; dropping them from the list would hide the limitation rather
     than communicate it. 163 of the 661 players are in this category.

  3. Estimates are shown as a multiplicative range, never a single figure.
     Cross-validated typical error is a factor of 1.75, so a point estimate
     of EUR10m means "somewhere between EUR5.7m and EUR17.5m". Displaying
     one number would imply a precision the model does not have.

Layout note: club and position filters narrow the list before the name
search, which matters at 661 options -- "every centre-back at Arsenal" is a
question the plain name box cannot answer. Both default to "All", so the
unfiltered list is still one click away.

Reads: data/processed/pl_player_values_prethreshold.csv
       01-value-predictor/model.joblib
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

DATA = Path("data/processed/pl_player_values_prethreshold.csv")
MODEL = Path("01-value-predictor/model.joblib")

VETERAN_AGE = 38
BLIND_SPOT_POSITIONS = {"Goalkeeper", "Defender"}

ALL_CLUBS = "All clubs"
ALL_POSITIONS = "All positions"

# Modest CSS only: tighten Streamlit's generous default top padding, make the
# metric labels read as labels rather than body text, and give the club /
# position line a pill treatment. Everything else is stock Streamlit.
CSS = """
<style>
  .block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1100px; }
  [data-testid="stMetricLabel"] p {
      font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
      opacity: 0.65;
  }
  [data-testid="stMetricValue"] { font-size: 1.55rem; }
  .pill {
      display: inline-block; padding: 0.18rem 0.6rem; margin-right: 0.35rem;
      border-radius: 999px; font-size: 0.78rem; line-height: 1.5;
      background: rgba(0, 255, 135, 0.12); border: 1px solid rgba(0, 255, 135, 0.35);
  }
  .pill-muted {
      background: rgba(243, 234, 245, 0.07);
      border: 1px solid rgba(243, 234, 245, 0.18);
  }
  .panel {
      border: 1px solid rgba(243, 234, 245, 0.14); border-radius: 10px;
      padding: 1rem 1.15rem; background: rgba(46, 10, 53, 0.55);
  }
</style>
"""


# --- data loading ------------------------------------------------------------

@st.cache_data
def load_players() -> pd.DataFrame:
    return pd.read_csv(DATA, encoding="utf-8")


@st.cache_resource
def load_model() -> dict:
    return joblib.load(MODEL)


# --- helpers -----------------------------------------------------------------

def format_eur(value: float) -> str:
    """Euros at a readable magnitude. Market values span EUR100k to EUR200m,
    so a single format string cannot serve the whole range."""
    if value >= 1_000_000:
        return f"€{value / 1_000_000:,.1f}M"
    return f"€{value / 1_000:,.0f}K"


def build_features(row: pd.Series, feature_names: list[str]) -> pd.DataFrame:
    """One player -> one row of the design matrix.

    Built as a dict and then reindexed onto the training column order stored
    in the artefact. Constructing the columns in a hand-written order would
    silently mispredict if train_final.py ever changed that order, because
    scikit-learn matches on position, not name.
    """
    values = {
        "age": row["age"],
        "pl_matches": row["pl_matches"],
        "pl_minutes": row["pl_minutes"],
        "pl_goals": row["pl_goals"],
        "pl_assists": row["pl_assists"],
        "pl_yellow_cards": row["pl_yellow_cards"],
        "pl_red_cards": row["pl_red_cards"],
        "goals_per90": row["goals_per90"],
        "assists_per90": row["assists_per90"],
        "age_sq": row["age"] ** 2,
        f"pos_{row['position']}": 1.0,
    }
    # Missing dummies default to 0 -- that is how the dropped reference
    # category (Attack) is represented.
    return pd.DataFrame([values]).reindex(columns=feature_names, fill_value=0.0)


# --- page --------------------------------------------------------------------

st.set_page_config(page_title="PL Value Predictor", page_icon="⚽",
                   layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

st.title("Premier League value predictor")
st.caption(
    "Estimates a player's Transfermarkt market value from his career-to-date "
    "Premier League record. Linear regression on log value, "
    "cross-validated R² 0.727 ± 0.054."
)

if not MODEL.exists():
    st.error(
        f"Model artefact not found at `{MODEL}`. "
        "Run `python 01-value-predictor/train_final.py` first."
    )
    st.stop()

players = load_players()
artefact = load_model()
model = artefact["model"]
error_factor = artefact["error_factor"]
min_minutes = artefact["min_pl_minutes"]

# --- 1. filters and player selection -----------------------------------------

filter_cols = st.columns([1, 1, 2])

club = filter_cols[0].selectbox(
    "Club",
    options=[ALL_CLUBS] + sorted(players["current_club_name"].unique()),
)
position = filter_cols[1].selectbox(
    "Position",
    options=[ALL_POSITIONS] + sorted(players["position"].unique()),
)

shortlist = players
if club != ALL_CLUBS:
    shortlist = shortlist[shortlist["current_club_name"] == club]
if position != ALL_POSITIONS:
    shortlist = shortlist[shortlist["position"] == position]

if shortlist.empty:
    # Reachable: a small squad may have no player in a given position.
    st.warning(
        f"No {position.lower()} in the list for {club}. "
        f"Widen one of the filters above."
    )
    st.stop()

choice = filter_cols[2].selectbox(
    "Player",
    options=sorted(shortlist["name"].tolist()),
    index=None,
    placeholder=f"Search {len(shortlist)} player"
                f"{'s' if len(shortlist) != 1 else ''} by name…",
)

if choice is None:
    st.info(
        f"Pick a player to see an estimate. "
        f"**{len(shortlist)}** of {len(players)} Premier League players match "
        f"the current filters — everyone with at least one appearance who was "
        f"active in 2024 or 2025. Start typing in the name box to search."
    )
    st.stop()

row = shortlist.loc[shortlist["name"] == choice].iloc[0]
actual = row["market_value_in_eur"]
below_threshold = row["pl_minutes"] < min_minutes

st.divider()

# --- 2. player card (left) and prediction (right) ----------------------------
# Side by side rather than stacked, so the stats that drive the estimate stay
# on screen next to the estimate itself.

left, right = st.columns([1.15, 1], gap="large")

with left:
    st.subheader(row["name"])
    sub = f'<span class="pill">{row["position"]}</span>'
    if pd.notna(row["sub_position"]):
        sub += f'<span class="pill pill-muted">{row["sub_position"]}</span>'
    sub += f'<span class="pill pill-muted">{row["current_club_name"]}</span>'
    st.markdown(sub, unsafe_allow_html=True)
    st.write("")

    r1 = st.columns(3)
    r1[0].metric("Age", f"{row['age']:.1f}")
    r1[1].metric("PL matches", f"{int(row['pl_matches']):,}")
    r1[2].metric("PL minutes", f"{int(row['pl_minutes']):,}")

    r2 = st.columns(3)
    r2[0].metric("Goals", f"{int(row['pl_goals']):,}")
    r2[1].metric("Assists", f"{int(row['pl_assists']):,}")
    r2[2].metric("Goals + assists",
                 f"{int(row['pl_goals'] + row['pl_assists']):,}")

    r3 = st.columns(3)
    r3[0].metric("Goals per 90", f"{row['goals_per90']:.2f}")
    r3[1].metric("Assists per 90", f"{row['assists_per90']:.2f}")
    r3[2].metric("Cards (Y/R)",
                 f"{int(row['pl_yellow_cards'])}/{int(row['pl_red_cards'])}")

with right:
    if below_threshold:
        # Refusal, not a fallback estimate. See constraint 2 in the module
        # docstring: showing a number here would be the failure mode the
        # 900-minute threshold exists to prevent.
        st.subheader("No estimate for this player")
        st.warning(
            f"**{row['name']}** has **{int(row['pl_minutes']):,} Premier League "
            f"minutes**, below the **{min_minutes:,}-minute** threshold this "
            f"model requires.\n\n"
            f"Below roughly one season of football, per-90 rates stop measuring "
            f"anything — a player with 38 minutes and one assist scores 2.37 "
            f"assists per 90, seventeen standard deviations above the mean, and "
            f"the model extrapolates that into nonsense. Earlier versions of "
            f"this model produced predictions in the hundreds of billions of "
            f"euros for exactly these players.\n\n"
            f"The deeper problem is that players with limited minutes are "
            f"valued on potential and transfer hype, which nothing in this "
            f"feature set can observe. The honest answer is that this model "
            f"cannot price him."
        )
        st.metric("Transfermarkt market value", format_eur(actual))
        st.caption("Shown for reference only — the model made no prediction.")
    else:
        features = build_features(row, artefact["feature_names"])

        # The model predicts log(value); exponentiate back to euros. Note this
        # is the conditional median rather than the mean -- fine for "what is
        # he worth", but these figures should not be summed to value a squad.
        predicted = float(np.exp(model.predict(features)[0]))
        low, high = predicted / error_factor, predicted * error_factor
        within = low <= actual <= high

        st.subheader("Model estimate")
        st.metric(f"Estimated range (×{error_factor})",
                  f"{format_eur(low)} – {format_eur(high)}")

        # Stated up front, because a range invites being read as a confidence
        # interval. It is not one -- it is the typical size of a miss, and
        # roughly four players in ten fall outside it.
        st.caption(
            "This is a typical-error range, not a guaranteed bound — the "
            "actual value falls inside it for about 6 in 10 players "
            "(59% of the 498 the model was fitted on)."
        )

        st.write("")
        actual_cols = st.columns(2)
        actual_cols[0].metric("Transfermarkt value", format_eur(actual))
        actual_cols[1].metric("Point estimate", format_eur(predicted),
                              delta=f"{predicted / actual - 1:+.0%} vs actual",
                              delta_color="off")

        if within:
            st.success("The actual value falls inside the model's range.")
        else:
            st.error("The actual value falls outside the model's range — "
                     "this is one the model gets wrong.")

# --- 3. caveats --------------------------------------------------------------
# One line each, only when they apply. See the README's "Known limitations".
# Full width beneath both columns: these qualify the whole reading, not just
# the number in the right-hand panel.

if not below_threshold:
    caveats = []

    if row["age"] >= VETERAN_AGE:
        caveats.append(
            f"**Ageing veteran.** At {row['age']:.1f}, this player sits where "
            f"the model is known to be unreliable: the fitted age² curve keeps "
            f"falling past 40 while real values floor out around €300–500K. "
            f"Expect a substantial under-estimate."
        )

    if (row["position"] in BLIND_SPOT_POSITIONS
            and predicted < actual / error_factor):
        caveats.append(
            f"**Known blind spot.** The model has no club-quality or "
            f"reputation signal, so it prices {row['position'].lower()}s almost "
            f"entirely on goals and assists. Elite defenders and goalkeepers "
            f"are systematically under-valued as a result — the model is "
            f"under-predicting this player by more than its own typical error."
        )

    if caveats:
        st.divider()
        st.subheader("Caveats")
        for c in caveats:
            st.warning(c)
