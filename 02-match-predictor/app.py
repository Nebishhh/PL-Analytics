"""
02-match-predictor : Streamlit app
==================================
Win/Draw/Loss probabilities for historical Premier League matches.

Run with:
    streamlit run 02-match-predictor/app.py

Design constraints, each one a limitation made visible rather than hidden:

  1. Only real historical matches are selectable. There is no "team A vs
     team B today" mode. Every feature the model needs -- rolling form,
     pre-match league position, rest days, head-to-head -- is derived from
     what had actually been played before that specific kickoff. A
     hypothetical fixture has no such history, and inventing one would mean
     inventing the inputs.

  2. All three probabilities are always shown, never just the predicted
     class. A 41/26/33 split is the honest output; collapsing it to "Home
     win" would present a coin-flip as a verdict.

  3. The fixture dropdown never shows the score. Putting "Arsenal 2:2
     Tottenham" in the selector would hand over the answer before the model
     has spoken, which defeats the comparison the page exists to make.

  4. Every forecast shown is OUT OF SAMPLE, read from oof_predictions.csv
     rather than computed live from model.joblib. Each match there was
     predicted by a model trained only on the seasons before it.

     This matters more than it sounds. Every match in the feature table is in
     the shipped model's training set, where it scores 0.980. An app calling
     predict_proba directly would report the top pick as correct 98% of the
     time, for a model whose real accuracy is 0.470 -- a factor-of-two
     misrepresentation that no caption can undo. The cost is the first five
     seasons, which have no prior seasons to train on: the app covers 2017
     onward, 2,967 of the 4,616 matches.

FEATURE CONSTRUCTION
  build_xy is imported from model.py rather than reimplemented. The design
  matrix has 32 columns including 13 season dummies, and scikit-learn matches
  on position rather than name -- a divergence between training and serving
  would mispredict silently, with no error. There is one definition of it.

Reads: data/processed/pl_matches_features.csv
       02-match-predictor/model.joblib        (metadata and CV figures)
       02-match-predictor/oof_predictions.csv (the forecasts actually shown)
"""

import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from model import build_xy  # noqa: E402

MODEL = Path("02-match-predictor/model.joblib")
OOF = Path("02-match-predictor/oof_predictions.csv")

ALL_CLUBS = "All clubs"
OUTCOME_LABELS = {"H": "Home win", "D": "Draw", "A": "Away win"}

# Same visual language as project 01's app: tightened padding, uppercase
# metric labels, pill treatment. Added here: a three-segment probability bar,
# because a row of numbers reads as three separate facts while a single
# divided bar reads as one distribution that sums to 100%.
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
  .probbar { display: flex; width: 100%; height: 34px; border-radius: 7px;
             overflow: hidden; margin: 0.4rem 0 0.2rem 0;
             border: 1px solid rgba(243,234,245,0.18); }
  .probbar div { display: flex; align-items: center; justify-content: center;
                 font-size: 0.78rem; font-weight: 600; color: #1B0620; }
  .seg-h { background: #00FF87; }
  .seg-d { background: #9C89A6; }
  .seg-a { background: #04F5FF; }
</style>
"""


# --- loading -----------------------------------------------------------------

@st.cache_data
def load_matches():
    """The match table joined to its out-of-fold forecasts.

    An inner join, deliberately: matches with no out-of-fold prediction are
    the 2012-2016 seasons, and they are dropped rather than shown with an
    in-sample number. If a fixture is selectable here, its forecast is honest.
    """
    _, _, df = build_xy()
    oof = pd.read_csv(OOF, encoding="utf-8")
    return df.merge(oof[["game_id", "p_H", "p_D", "p_A",
                         "trained_on_seasons"]], on="game_id", how="inner")


@st.cache_resource
def load_model() -> dict:
    return joblib.load(MODEL)


def fixture_label(row, club: str | None) -> str:
    """Date and teams. Deliberately no score -- see constraint 3."""
    base = (f"{row.date:%Y-%m-%d} · {row.home_club_name} vs "
            f"{row.away_club_name}")
    if club and club != ALL_CLUBS:
        base += " (H)" if row.home_club_name == club else " (A)"
    return base


# --- page --------------------------------------------------------------------

st.set_page_config(page_title="PL Match Predictor", page_icon="⚽",
                   layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

st.title("Premier League match predictor")
st.caption(
    "Win/Draw/Loss probabilities from pre-match form only — nothing the model "
    "sees was knowable after kickoff. Gradient boosting, cross-validated "
    "accuracy 0.470 ± 0.031 against a 0.446 always-home-win baseline."
)

for path in (MODEL, OOF):
    if not path.exists():
        st.error(
            f"Required file not found at `{path}`. "
            "Run `python 02-match-predictor/train_final.py` first."
        )
        st.stop()

df = load_matches()
artefact = load_model()
cv = artefact["cv"]

# --- 1. season -> club (optional) -> match -----------------------------------

cols = st.columns([1, 1.3, 3])

season = cols[0].selectbox("Season", options=sorted(df.season.unique(),
                                                    reverse=True))
in_season = df[df.season == season]

clubs = sorted(set(in_season.home_club_name) | set(in_season.away_club_name))
club = cols[1].selectbox("Club", options=[ALL_CLUBS] + clubs)

shortlist = in_season
if club != ALL_CLUBS:
    shortlist = shortlist[(shortlist.home_club_name == club)
                          | (shortlist.away_club_name == club)]
shortlist = shortlist.sort_values("date")

labels = {fixture_label(r, club): r.Index for r in shortlist.itertuples()}
choice = cols[2].selectbox(
    "Match",
    options=list(labels),
    index=None,
    placeholder=f"Search {len(labels)} match"
                f"{'es' if len(labels) != 1 else ''}…",
)

if choice is None:
    st.info(
        f"Pick a match to see the model's forecast. "
        f"**{len(labels)}** matches available"
        + (f" for {club} in {season}." if club != ALL_CLUBS
           else f" in the {season} season.")
        + f"  Only real historical fixtures are selectable — the model needs "
          f"the form and league position that actually existed before kickoff, "
          f"which a hypothetical matchup does not have."
    )
    st.stop()

idx = labels[choice]
row = df.loc[idx]

# --- 2. match card -----------------------------------------------------------

st.divider()
head = st.columns([3, 2])
head[0].subheader(f"{row.home_club_name}  v  {row.away_club_name}")
head[1].markdown(
    f'<div style="text-align:right;padding-top:0.8rem">'
    f'<span class="pill">{row.date:%d %b %Y}</span>'
    f'<span class="pill pill-muted">Season {row.season}</span>'
    f'<span class="pill pill-muted">Matchday {int(row.home_matchday)}</span>'
    f"</div>",
    unsafe_allow_html=True,
)

st.caption("Form as it stood before this kickoff — the model sees nothing else.")

home_col, away_col = st.columns(2, gap="large")
for side, col, name in [("home", home_col, row.home_club_name),
                        ("away", away_col, row.away_club_name)]:
    with col:
        st.markdown(f'<span class="pill pill-muted">{name}</span>',
                    unsafe_allow_html=True)
        st.write("")
        a = st.columns(3)
        a[0].metric("Points/game", f"{row[f'{side}_pre_ppg']:.2f}")
        a[1].metric("Position", f"{int(row[f'{side}_pre_position'])}")
        a[2].metric("Rest days",
                    f"{row[f'{side}_rest_days']:.0f}"
                    if pd.notna(row[f"{side}_rest_days"]) else "—")
        b = st.columns(3)
        b[0].metric("Form, last 5", f"{row[f'{side}_pts_l5']:.2f}")
        b[1].metric("Form, last 10", f"{row[f'{side}_pts_l10']:.2f}")
        b[2].metric("Goals for / against, last 5",
                    f"{row[f'{side}_gf_l5']:.1f} / {row[f'{side}_ga_l5']:.1f}")

if row.h2h_matches and row.h2h_matches > 0:
    st.caption(
        f"**Head to head:** {int(row.h2h_matches)} prior meeting"
        f"{'s' if row.h2h_matches != 1 else ''} in this dataset, "
        f"{row.home_club_name} averaging "
        f"{row.h2h_home_pts_per_match:.2f} points per meeting."
    )
else:
    st.caption("**Head to head:** no prior meetings in this dataset.")

# --- 3. prediction -----------------------------------------------------------

st.divider()
# Read, do not compute. See constraint 4 in the module docstring.
p = {c: float(row[f"p_{c}"]) for c in ("H", "D", "A")}

st.subheader("Model forecast")

pcols = st.columns(3)
pcols[0].metric(f"Home win — {row.home_club_name}", f"{p['H'] * 100:.0f}%")
pcols[1].metric("Draw", f"{p['D'] * 100:.0f}%")
pcols[2].metric(f"Away win — {row.away_club_name}", f"{p['A'] * 100:.0f}%")

st.markdown(
    f'<div class="probbar">'
    f'<div class="seg-h" style="width:{p["H"] * 100:.2f}%">'
    f'{"H " + format(p["H"] * 100, ".0f") + "%" if p["H"] > 0.11 else ""}</div>'
    f'<div class="seg-d" style="width:{p["D"] * 100:.2f}%">'
    f'{"D " + format(p["D"] * 100, ".0f") + "%" if p["D"] > 0.11 else ""}</div>'
    f'<div class="seg-a" style="width:{p["A"] * 100:.2f}%">'
    f'{"A " + format(p["A"] * 100, ".0f") + "%" if p["A"] > 0.11 else ""}</div>'
    f"</div>",
    unsafe_allow_html=True,
)

# The draw caveat, in the same register as project 01's x1.75 line.
draw_recall = cv["per_class"]["D"][1]
st.caption(
    f"These are probabilities, not a verdict. The model catches only about "
    f"1 in 4 draws that actually happen (recall {draw_recall:.2f}), so a low "
    f"draw probability is not evidence that a draw is unlikely — it mostly "
    f"reflects that the model cannot see draws coming."
)

# --- what actually happened --------------------------------------------------

st.write("")
actual = row.target
top = max(p, key=p.get)

res = st.columns(3)
res[0].metric("Actual result", OUTCOME_LABELS[actual])
res[1].metric("Model's top pick", OUTCOME_LABELS[top],
              delta=f"{p[top] * 100:.0f}% confidence", delta_color="off")
res[2].metric("Probability given to the actual result",
              f"{p[actual] * 100:.0f}%")

if top == actual:
    st.success(
        f"The model's most likely outcome was correct — though at "
        f"{p[top] * 100:.0f}% it was far from certain."
    )
else:
    st.error(
        f"The model's top pick was {OUTCOME_LABELS[top].lower()}, and the "
        f"match ended in a {OUTCOME_LABELS[actual].lower()}. It gave the "
        f"actual result {p[actual] * 100:.0f}%."
    )

st.caption(
    f"This forecast is genuinely out of sample: it comes from a model trained "
    f"on seasons {row.trained_on_seasons} only, which had never seen the "
    f"{row.season} season when it made this prediction. Across all "
    f"{len(df):,} matches shown in this app the top pick is correct "
    f"{cv['accuracy'] * 100:.0f}% of the time, against "
    f"{cv['baseline_accuracy'] * 100:.0f}% for always guessing a home win. "
    f"Seasons before 2017 are not selectable because there is not enough "
    f"prior history to forecast them honestly."
)
