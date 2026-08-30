"""
03-style-finder : Streamlit app
===============================
Shows which activity cluster a Premier League player was assigned to, and how
much that assignment is worth.

Run with:
    streamlit run 03-style-finder/app.py

THE DESIGN PROBLEM THIS APP HAS
  Projects 01 and 02 shipped a prediction with an error bar. This one ships a
  label, and a label looks certain in a way a number does not. "Cluster 2" on
  a page reads as a fact. It frequently is not: silhouette at k=4 is 0.180,
  19 of 315 players sit closer to another cluster's members than their own,
  and 76 are within 0.5 of a rival centroid.

  So the confidence tier is computed FIRST and governs the wording, the
  colour, and the order of the sentence. For a contested player the rival
  cluster is named before the assigned one, because presenting the assigned
  cluster first would be asserting something the geometry does not support.

WHY TWO SIGNALS AND NOT ONE
  margin_to_next asks "is another centroid nearly as close?" -- geometry.
  Per-player silhouette asks "am I closer to another cluster's members than my
  own?" -- density. They are nearly independent: only 4 of the 19 players with
  negative silhouette also have a margin under 0.10. A margin-only rule would
  have shown the other 15 -- Rodri, Luke Shaw, Bernardo Silva among them -- as
  confidently assigned.

  Tiers:
    CONTESTED   silhouette < 0 OR margin < 0.10   25 players (7.9%)
    BORDERLINE  margin < 0.50 OR silhouette < 0.05  55 players (17.5%)
    PLACED      everything else                    235 players (74.6%)

THE TWO-TIER TRUST FINDING
  Stated statically at the top of the page, not per player, because it
  qualifies every answer the app can give: the clusters that separate best
  are the ones that merely restate position, and the clusters that carry
  information beyond the team sheet are the worst separated.

Reads: 03-style-finder/cluster_assignments.csv
       03-style-finder/model.joblib  (names, quality metadata)
"""

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ASSIGNMENTS = Path("03-style-finder/cluster_assignments.csv")
MODEL = Path("03-style-finder/model.joblib")

# Confidence thresholds. See the module docstring for why both are needed.
CONTESTED_MARGIN = 0.10
BORDERLINE_MARGIN = 0.50
BORDERLINE_SIL = 0.05

# Clusters that largely restate a position rather than revealing anything new:
# 0 holds 27 of the 28 pure forwards, 1 holds 73% of all defenders.
POSITION_ADJACENT = {0, 1}

ALL_POSITIONS = "All positions"
POSITION_GROUPS = ["DF", "MF", "FW"]

FEATURE_LABELS = {
    "att_gls_p90": "Goals", "att_ast_p90": "Assists", "att_sh_p90": "Shots",
    "att_crs_p90": "Crosses", "att_sot_pct": "Shot accuracy %",
    "def_int_p90": "Interceptions", "def_tklw_p90": "Tackles won",
    "disc_fls_p90": "Fouls", "disc_fld_p90": "Fouls drawn",
    "disc_crdy_p90": "Yellow cards",
}
GROUP_OF = {"att_": "Attacking output", "def_": "Defensive activity",
            "disc_": "Discipline"}

CSS = """
<style>
  .block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1100px; }
  [data-testid="stMetricLabel"] p {
      font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
      opacity: 0.65;
  }
  [data-testid="stMetricValue"] { font-size: 1.5rem; }
  .pill {
      display: inline-block; padding: 0.18rem 0.6rem; margin-right: 0.35rem;
      border-radius: 999px; font-size: 0.78rem; line-height: 1.5;
      background: rgba(0, 255, 135, 0.12); border: 1px solid rgba(0, 255, 135, 0.35);
  }
  .pill-muted {
      background: rgba(243, 234, 245, 0.07);
      border: 1px solid rgba(243, 234, 245, 0.18);
  }
  .distbar { display: flex; width: 100%; height: 30px; border-radius: 7px;
             overflow: hidden; margin: 0.5rem 0 0.3rem 0;
             border: 1px solid rgba(243,234,245,0.18); }
  .distbar div { display: flex; align-items: center; justify-content: center;
                 font-size: 0.74rem; font-weight: 600; color: #1B0620;
                 white-space: nowrap; overflow: hidden; }
  .seg-own { background: #00FF87; }
  .seg-rival { background: #9C89A6; }
  .tier { font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase;
          opacity: 0.75; }
</style>
"""


@st.cache_data
def load_assignments() -> pd.DataFrame:
    return pd.read_csv(ASSIGNMENTS, encoding="utf-8")


@st.cache_resource
def load_artefact() -> dict:
    return joblib.load(MODEL)


def ordinal(n: int) -> str:
    """1st, 2nd, 3rd, 4th... 11th/12th/13th are the exceptions."""
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def confidence_tier(row) -> str:
    """CONTESTED / BORDERLINE / PLACED. Computed before anything is rendered,
    because it governs wording and sentence order, not just a colour."""
    if row.silhouette < 0 or row.margin_to_next < CONTESTED_MARGIN:
        return "CONTESTED"
    if row.margin_to_next < BORDERLINE_MARGIN or row.silhouette < BORDERLINE_SIL:
        return "BORDERLINE"
    return "PLACED"


# --- page --------------------------------------------------------------------

st.set_page_config(page_title="PL Style Finder", page_icon="⚽", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

st.title("Premier League activity profiles")
st.caption(
    "K-Means clustering of 315 Premier League outfielders on 10 per-90 rates. "
    "Activity profiles, not playing styles — this data has no passing, "
    "carrying or expected-goals columns."
)

for path in (ASSIGNMENTS, MODEL):
    if not path.exists():
        st.error(f"Required file not found at `{path}`. "
                 "Run `python 03-style-finder/train_final.py` first.")
        st.stop()

df = load_assignments()
artefact = load_artefact()
feats = artefact["feature_names"]
sil_overall = artefact["quality"]["silhouette"]

# --- the static two-tier trust warning ---------------------------------------
# Not per player: it qualifies every answer this app can give.
st.warning(
    f"**This clustering is most confident exactly where it is least "
    f"informative.** The two best-separated clusters are the ones that largely "
    f"restate position — one holds 27 of the 28 pure forwards, another 73% of "
    f"all defenders. The two clusters that split defenders and midfielders by "
    f"*what they do* rather than where they line up are the worst separated "
    f"(silhouette 0.101 and 0.136), and one of them contains 15 of the 19 "
    f"players who sit closer to another cluster's members than their own.\n\n"
    f"Overall silhouette is **{sil_overall:.3f}**, and no k from 2 to 10 "
    f"reaches 0.25 — the conventional threshold for meaningful structure. "
    f"These are regions of a continuous distribution, not natural kinds."
)

# --- 1. player selection -----------------------------------------------------

filter_cols = st.columns([1, 3])

# Matches ANY listed position, not just the first. 84 of the 315 players carry
# two (MF,FW and the like), so first-token matching would hide 30 forwards from
# anyone filtering on FW.
position = filter_cols[0].selectbox(
    "Position", options=[ALL_POSITIONS] + POSITION_GROUPS
)

shortlist = df
if position != ALL_POSITIONS:
    shortlist = shortlist[shortlist.pos.str.contains(position)]

choice = filter_cols[1].selectbox(
    "Player",
    options=sorted(shortlist.player.tolist()),
    index=None,
    placeholder=f"Search {len(shortlist)} player"
                f"{'s' if len(shortlist) != 1 else ''} by name…",
)

if choice is None:
    scope = (f"All {len(df)} Premier League outfielders with at least 900 "
             f"minutes in 2025–26 are here"
             if position == ALL_POSITIONS else
             f"**{len(shortlist)}** of {len(df)} players list {position}")
    st.info(
        f"Pick a player to see which activity cluster they were assigned to, "
        f"and how solid that assignment is. {scope} — goalkeepers are "
        f"excluded, since their statistical profile shares almost nothing "
        f"with outfield players."
    )
    st.stop()

row = df[df.player == choice].iloc[0]
tier = confidence_tier(row)

# --- 2. player card ----------------------------------------------------------

st.divider()
head = st.columns([3, 2])
head[0].subheader(row.player)
head[1].markdown(
    f'<div style="text-align:right;padding-top:0.7rem">'
    f'<span class="pill">{row.squad}</span>'
    f'<span class="pill pill-muted">{row.pos}</span>'
    f'<span class="pill pill-muted">{row.age:.0f} yrs</span>'
    f'<span class="pill pill-muted">{int(row.minutes):,} min</span>'
    f"</div>",
    unsafe_allow_html=True,
)
st.caption(
    "Position is shown for context only. It was held out of the clustering "
    "entirely — the whole point was to see whether grouping players by what "
    "they do would recover something the team sheet does not already say."
)

st.markdown("**The ten per-90 rates that produced this assignment**")
for prefix, group_name in GROUP_OF.items():
    cols = [f for f in feats if f.startswith(prefix)]
    st.markdown(f'<span class="pill pill-muted">{group_name}</span>',
                unsafe_allow_html=True)
    metric_cols = st.columns(len(cols))
    for col, f in zip(metric_cols, cols):
        pct = round((df[f] < row[f]).mean() * 100)
        col.metric(FEATURE_LABELS[f], f"{row[f]:.2f}",
                   delta=f"{ordinal(pct)} pct", delta_color="off")

# --- 3. cluster result -------------------------------------------------------

st.divider()
st.subheader("Cluster assignment")

own, rival = row.cluster_name, row.rival_cluster_name

if tier == "CONTESTED":
    st.markdown('<span class="tier">⚠ Contested assignment</span>',
                unsafe_allow_html=True)
    # Rival named FIRST. Leading with the assigned cluster would assert
    # something the geometry does not support.
    st.error(
        f"**Close call — this assignment is not solid.** {row.player} sits "
        f"almost as close to *{rival}* as to the cluster actually assigned, "
        f"*{own}*. The gap is **{row.margin_to_next:.3f}**, against a median "
        f"of {df.margin_to_next.median():.2f} across all {len(df)} players."
    )
elif tier == "BORDERLINE":
    st.markdown('<span class="tier">◐ Borderline assignment</span>',
                unsafe_allow_html=True)
    st.warning(
        f"**{own}** — but not decisively. The nearest alternative is "
        f"*{rival}*, only **{row.margin_to_next:.3f}** further away."
    )
else:
    st.markdown('<span class="tier">✓ Reasonably placed</span>',
                unsafe_allow_html=True)
    st.success(
        f"**{own}** — a reasonably clear placement. The nearest alternative, "
        f"*{rival}*, is **{row.margin_to_next:.2f}** further away, against a "
        f"median of {df.margin_to_next.median():.2f}."
    )

# Negative silhouette gets its own callout: a distinct failure mode from a
# narrow margin, and one a margin-only rule would miss entirely.
if row.silhouette < 0:
    st.error(
        f"**This player sits closer to another cluster's members than to his "
        f"own.** Per-player silhouette is **{row.silhouette:+.3f}** — negative. "
        f"That is a different problem from a narrow margin: the assigned "
        f"centroid may be nearest, but the players actually around him mostly "
        f"belong to a different group. His assigned cluster should not be read "
        f"as descriptive of him at all. 19 of {len(df)} players are in this "
        f"position."
    )

# Distance bar: two near-equal segments make a close call visible without
# anyone having to interpret 0.042.
total = row.distance_to_centroid + row.distance_to_rival
st.markdown(
    f'<div class="distbar">'
    f'<div class="seg-own" style="width:{row.distance_to_centroid / total * 100:.1f}%">'
    f'assigned {row.distance_to_centroid:.2f}</div>'
    f'<div class="seg-rival" style="width:{row.distance_to_rival / total * 100:.1f}%">'
    f'rival {row.distance_to_rival:.2f}</div>'
    f"</div>",
    unsafe_allow_html=True,
)
st.caption("Distance to the assigned centroid versus the next-nearest. "
           "Near-equal segments mean the label could easily have gone the "
           "other way.")

m = st.columns(3)
m[0].metric("Margin to next cluster", f"{row.margin_to_next:.3f}")
m[1].metric("Per-player silhouette", f"{row.silhouette:+.3f}")
m[2].metric("Cluster size", f"{int((df.cluster == row.cluster).sum())} players")

# --- position adjacency ------------------------------------------------------

members = df[df.cluster == row.cluster]
broad = members.pos.str.split(",").str[0].value_counts()
dom, dom_n = broad.index[0], broad.iloc[0]
share = dom_n / len(members) * 100

if row.cluster in POSITION_ADJACENT:
    st.info(
        f"**This cluster mostly restates position.** {share:.0f}% of its "
        f"{len(members)} members are listed {dom} first. It is one of the two "
        f"clusters that track the team sheet closely — which is also why it "
        f"separates comparatively well. Being placed here says little beyond "
        f"what the position column already told you."
    )
else:
    st.info(
        f"**This cluster does not simply restate position.** Its members are "
        f"{share:.0f}% {dom}-first, but it mixes positions substantially — "
        f"grouping players by what they do rather than where they line up. "
        f"That is the part of this clustering that adds something beyond the "
        f"team sheet, and it is also the least well separated, so treat the "
        f"grouping as suggestive rather than settled."
    )

with st.expander("How this cluster was named"):
    st.markdown(
        f"Names are generated mechanically by comparing each cluster's feature "
        f"means against the quartiles of all {len(df)} players — never written "
        f"by hand. Terms like *inverted winger* or *deep-lying playmaker* are "
        f"claims about passing, carrying and positioning, and this dataset has "
        f"none of those columns, so no such name could be justified.\n\n"
        f"The largest cluster has no feature in either quartile, so it is named "
        f"for that: low involvement across all three groups.\n\n"
        f"**All four clusters:**"
    )
    summary = pd.DataFrame([
        {"Cluster": c, "Players": int((df.cluster == c).sum()), "Name": n}
        for c, n in sorted(artefact["cluster_names"].items())
    ])
    st.dataframe(summary, hide_index=True, use_container_width=True)
