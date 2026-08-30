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
  .distbar { display: flex; width: 100%; height: 46px; border-radius: 9px;
             overflow: hidden; margin: 0.8rem 0 0.4rem 0;
             border: 1px solid rgba(243,234,245,0.22); }
  .distbar div { display: flex; align-items: center; justify-content: center;
                 font-size: 0.85rem; font-weight: 700; color: #1B0620;
                 white-space: nowrap; overflow: hidden; }
  .seg-own { background: #00FF87; }
  .seg-rival { background: #9C89A6; }
  .clustername { font-size: 1.35rem; font-weight: 700; line-height: 1.35;
                 margin: 0.2rem 0 0.6rem 0; }
  .badge { display: inline-block; padding: 0.22rem 0.7rem; margin-right: 0.4rem;
           border-radius: 999px; font-size: 0.82rem; font-weight: 600; }
  .badge-red   { background: rgba(233,0,82,0.18);   border: 1px solid #E90052;
                 color: #FF9CBD; }
  .badge-amber { background: rgba(255,176,0,0.16);  border: 1px solid #FFB000;
                 color: #FFCC66; }
  .badge-green { background: rgba(0,255,135,0.14);  border: 1px solid #00FF87;
                 color: #7CFFC0; }
  .badge-plain { background: rgba(243,234,245,0.07);
                 border: 1px solid rgba(243,234,245,0.20); font-weight: 500; }
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
# Not per player: it qualifies every answer this app can give. Compressed to a
# single line so a casual visitor gets the gist without reading a paragraph;
# every word of the original reasoning is preserved in the expander below.
st.warning("**This clustering is most confident where it is least informative.**")

with st.expander("Why does this matter?"):
    st.markdown(
        f"""
**The two best-separated clusters barely tell you anything new.** One holds 27
of the 28 pure forwards; another holds 73% of all defenders. They separate
cleanly *because* they track the team sheet — being placed in them says little
beyond what the position column already said.

**The two clusters that do add something are the worst separated.** They split
defenders and midfielders by *what they do* rather than where they line up —
high tackling and fouling versus high crossing and assisting. Their silhouettes
are **0.101** and **0.136**, and one of them contains 15 of the 19 players who
sit closer to another cluster's members than to their own.

So the parts of this result you can trust are the parts that restate position,
and the parts that carry real information are the shakiest. That is not a bug
to be fixed — it is what the data supports.

**Overall silhouette is {sil_overall:.3f}**, and no k from 2 to 10 reaches 0.25,
the conventional threshold for meaningful structure. K-Means always returns k
clusters; a partition existing is not evidence that natural groups exist. These
are regions of a continuous distribution, not natural kinds.
"""
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
# Restructured for scannability: name, badge, bar and one sentence are visible
# by default; every word of the fuller reasoning lives in the expander below.
# Nothing was removed, only relocated.

st.divider()
st.subheader("Cluster assignment")

own, rival = row.cluster_name, row.rival_cluster_name
members = df[df.cluster == row.cluster]
broad = members.pos.str.split(",").str[0].value_counts()
dom, dom_n = broad.index[0], broad.iloc[0]
share = dom_n / len(members) * 100
position_adjacent = row.cluster in POSITION_ADJACENT

st.markdown(f'<div class="clustername">{own}</div>', unsafe_allow_html=True)

TIER_BADGE = {
    "CONTESTED": ("Contested", "badge-red"),
    "BORDERLINE": ("Borderline", "badge-amber"),
    "PLACED": ("Reasonably placed", "badge-green"),
}
badge_text, badge_class = TIER_BADGE[tier]
badges = f'<span class="badge {badge_class}">{badge_text}</span>'
# Negative silhouette earns its own badge rather than hiding in the expander:
# it is a distinct failure mode and a reader skimming must not miss it.
if row.silhouette < 0:
    badges += ('<span class="badge badge-red">Sits with another cluster</span>')
# Position adjacency, shrunk from a paragraph to a tag beside the name.
badges += (f'<span class="badge badge-plain">'
           f'{"Mostly restates position" if position_adjacent else "Mixes positions"}'
           f"</span>")
st.markdown(badges, unsafe_allow_html=True)

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

# One sentence. For a contested player the rival is named first, because
# leading with the assignment would assert what the geometry does not support.
if tier == "CONTESTED" and row.silhouette < 0:
    headline = (f"Nearly as close to **{rival}** — and sits among that "
                f"cluster's members rather than his own.")
elif tier == "CONTESTED":
    headline = (f"Nearly as close to **{rival}**: only "
                f"**{row.margin_to_next:.3f}** further away.")
elif tier == "BORDERLINE":
    headline = (f"**{rival}** is only **{row.margin_to_next:.2f}** further "
                f"away — not a decisive placement.")
else:
    headline = (f"**{rival}** is **{row.margin_to_next:.2f}** further away — "
                f"a clear placement.")
st.markdown(headline)

with st.expander("More detail"):
    m = st.columns(3)
    m[0].metric("Margin to next cluster", f"{row.margin_to_next:.3f}")
    m[1].metric("Per-player silhouette", f"{row.silhouette:+.3f}")
    m[2].metric("Cluster size", f"{len(members)} players")

    st.markdown(
        f"The bar above compares the distance from {row.player} to his assigned "
        f"centroid ({row.distance_to_centroid:.2f}) against the next-nearest "
        f"({row.distance_to_rival:.2f}). Near-equal segments mean the label "
        f"could easily have gone the other way."
    )

    if tier == "CONTESTED":
        st.error(
            f"**Why contested.** {row.player} sits almost as close to *{rival}* "
            f"as to the cluster actually assigned, *{own}*. The gap is "
            f"**{row.margin_to_next:.3f}**, against a median of "
            f"**{df.margin_to_next.median():.2f}** across all {len(df)} players. "
            f"A player is flagged contested when the margin falls below "
            f"{CONTESTED_MARGIN} or the silhouette goes negative — "
            f"{int(((df.silhouette < 0) | (df.margin_to_next < CONTESTED_MARGIN)).sum())} "
            f"of {len(df)} players qualify."
        )
    elif tier == "BORDERLINE":
        st.warning(
            f"**Why borderline.** The nearest alternative, *{rival}*, is only "
            f"**{row.margin_to_next:.3f}** further away, against a median of "
            f"**{df.margin_to_next.median():.2f}**. Borderline covers a margin "
            f"under {BORDERLINE_MARGIN} or a silhouette under {BORDERLINE_SIL} — "
            f"neither clearly placed nor genuinely contested."
        )
    else:
        st.success(
            f"**Why reasonably placed.** The nearest alternative, *{rival}*, is "
            f"**{row.margin_to_next:.2f}** further away, against a median of "
            f"**{df.margin_to_next.median():.2f}** across all {len(df)} players, "
            f"and the silhouette is positive at **{row.silhouette:+.3f}**."
        )

    if row.silhouette < 0:
        st.error(
            f"**This player sits closer to another cluster's members than to his "
            f"own.** Per-player silhouette is **{row.silhouette:+.3f}** — "
            f"negative. That is a different problem from a narrow margin: the "
            f"assigned centroid may be nearest, but the players actually around "
            f"him mostly belong to a different group. His assigned cluster "
            f"should not be read as descriptive of him at all. "
            f"{int((df.silhouette < 0).sum())} of {len(df)} players are in this "
            f"position."
        )

    st.markdown(
        "**What these two numbers mean.** *Margin* asks whether another "
        "centroid is nearly as close — pure geometry. *Silhouette* asks whether "
        "the player sits closer to another cluster's members than his own — "
        "density. They are near-independent: only 4 of the 19 negative-"
        "silhouette players also have a margin under 0.10, so a margin-only "
        "rule would show the other 15 as confidently assigned."
    )

    if position_adjacent:
        st.info(
            f"**This cluster mostly restates position.** {share:.0f}% of its "
            f"{len(members)} members are listed {dom} first. It is one of the "
            f"two clusters that track the team sheet closely — which is also "
            f"why it separates comparatively well. Being placed here says "
            f"little beyond what the position column already told you."
        )
    else:
        st.info(
            f"**This cluster does not simply restate position.** Its members "
            f"are {share:.0f}% {dom}-first, but it mixes positions "
            f"substantially — grouping players by what they do rather than "
            f"where they line up. That is the part of this clustering that adds "
            f"something beyond the team sheet, and it is also the least well "
            f"separated, so treat the grouping as suggestive rather than settled."
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
