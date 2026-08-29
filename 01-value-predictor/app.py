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
                   layout="centered")

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

# --- 1. player selection -----------------------------------------------------

names = sorted(players["name"].tolist())
choice = st.selectbox(
    "Player",
    options=names,
    index=None,
    placeholder="Search for a player…",
)

if choice is None:
    st.info(
        f"Pick a player to see an estimate. "
        f"{len(players)} Premier League players are available — "
        f"everyone with at least one appearance who was active in 2024 or 2025."
    )
    st.stop()

row = players.loc[players["name"] == choice].iloc[0]

# --- 2. player card ----------------------------------------------------------

st.subheader(row["name"])
st.caption(f"{row['current_club_name']} · {row['position']}"
           + (f" ({row['sub_position']})"
              if pd.notna(row["sub_position"]) else ""))

top = st.columns(4)
top[0].metric("Age", f"{row['age']:.1f}")
top[1].metric("PL matches", f"{int(row['pl_matches']):,}")
top[2].metric("PL minutes", f"{int(row['pl_minutes']):,}")
top[3].metric("Goals + assists",
              f"{int(row['pl_goals'] + row['pl_assists']):,}")

bottom = st.columns(4)
bottom[0].metric("Goals", f"{int(row['pl_goals']):,}")
bottom[1].metric("Assists", f"{int(row['pl_assists']):,}")
bottom[2].metric("Goals per 90", f"{row['goals_per90']:.2f}")
bottom[3].metric("Assists per 90", f"{row['assists_per90']:.2f}")

st.divider()

# --- 3. prediction -----------------------------------------------------------

actual = row["market_value_in_eur"]

if row["pl_minutes"] < min_minutes:
    # Refusal, not a fallback estimate. See constraint 2 in the module
    # docstring: showing a number here would be the failure mode the
    # 900-minute threshold exists to prevent.
    st.subheader("No estimate for this player")
    st.warning(
        f"**{row['name']}** has **{int(row['pl_minutes']):,} Premier League "
        f"minutes**, below the **{min_minutes:,}-minute** threshold this model "
        f"requires.\n\n"
        f"Below roughly one season of football, per-90 rates stop measuring "
        f"anything — a player with 38 minutes and one assist scores 2.37 "
        f"assists per 90, seventeen standard deviations above the mean, and "
        f"the model extrapolates that into nonsense. Earlier versions of this "
        f"model produced predictions in the hundreds of billions of euros for "
        f"exactly these players.\n\n"
        f"The deeper problem is that players with limited minutes are valued "
        f"on potential and transfer hype, which nothing in this feature set "
        f"can observe. The honest answer is that this model cannot price him."
    )
    st.metric("Transfermarkt market value", format_eur(actual))
    st.caption("Shown for reference only — the model made no prediction.")
    st.stop()

features = build_features(row, artefact["feature_names"])

# The model predicts log(value); exponentiate back to euros. Note this is the
# conditional median rather than the mean -- fine for "what is he worth",
# but these figures should not be summed to value a whole squad.
predicted = float(np.exp(model.predict(features)[0]))

low, high = predicted / error_factor, predicted * error_factor

st.subheader("Model estimate")
cols = st.columns(2)
cols[0].metric(f"Estimated range (×{error_factor})",
               f"{format_eur(low)} – {format_eur(high)}")
cols[1].metric("Transfermarkt market value", format_eur(actual))

within = low <= actual <= high
st.caption(
    ("✓ The actual value falls inside the model's range."
     if within else
     "✗ The actual value falls outside the model's range — "
     "this is one the model gets wrong.")
    + f"  Point estimate {format_eur(predicted)}, shown as a range because "
      f"the cross-validated typical error is a factor of {error_factor}."
)

# --- 4. caveats --------------------------------------------------------------
# One line each, only when they apply. See the README's "Known limitations".

caveats = []

if row["age"] >= VETERAN_AGE:
    caveats.append(
        f"**Ageing veteran.** At {row['age']:.1f}, this player sits where the "
        f"model is known to be unreliable: the fitted age² curve keeps falling "
        f"past 40 while real values floor out around €300–500K. Expect a "
        f"substantial under-estimate."
    )

if row["position"] in BLIND_SPOT_POSITIONS and predicted < actual / error_factor:
    caveats.append(
        f"**Known blind spot.** The model has no club-quality or reputation "
        f"signal, so it prices {row['position'].lower()}s almost entirely on "
        f"goals and assists. Elite defenders and goalkeepers are systematically "
        f"under-valued as a result — the model is under-predicting this player "
        f"by more than its own typical error."
    )

if caveats:
    st.divider()
    st.subheader("Caveats")
    for c in caveats:
        st.warning(c)
