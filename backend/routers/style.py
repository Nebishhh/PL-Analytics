"""Project 03 -- cluster assignment.

Serves stored assignments from cluster_assignments.csv. The KMeans model is
loaded for metadata; .predict() is not called for any of the 315 known
players, since their assignment and its uncertainty were computed at fit time
and stored.

Routing uses a slug rather than an id because the assignments table has no id
column, and three players appear twice after mid-season transfers, so a name
alone is genuinely ambiguous. Slugs come from the listing endpoint; clients
must not construct them.

Cluster names are read from the artefact, where they were generated
mechanically from feature quartiles. AGENTS.md section 2.4 forbids inventing
archetype language -- this dataset has no passing, dribbling, expected-goals,
touch or carry columns, so terms like "deep-lying playmaker" would be claims
it cannot support.
"""

from fastapi import APIRouter, HTTPException, Query, Request

from .. import artefacts as art
from ..config import PLOT_DIRS
from ..schemas import (Assignment, Axis, ClusterPositionShare, Rate,
                       StyleAssignmentResponse, StylePlayerListItem, ToolMeta,
                       Zone)

router = APIRouter(prefix="/style", tags=["style"])


def _a(request: Request):
    return request.app.state.artefacts


def _tier(margin: float, silhouette: float, t: dict) -> str:
    """CONTESTED / BORDERLINE / PLACED, from artefact thresholds.

    Two signals, not one. margin asks whether another centroid is nearly as
    close (geometry); silhouette asks whether the player sits closer to
    another cluster's members than his own (density). Only 4 of the 19
    negative-silhouette players also have a margin under 0.10, so a
    margin-only rule would show the other 15 as confidently assigned.
    """
    if silhouette < 0 or margin < t["contested_margin"]:
        return "CONTESTED"
    if margin < t["borderline_margin"] or silhouette < t["borderline_silhouette"]:
        return "BORDERLINE"
    return "PLACED"


@router.get("/meta", response_model=ToolMeta)
def meta(request: Request) -> ToolMeta:
    a = _a(request)
    names, sizes = a.style["cluster_names"], a.style["cluster_sizes"]
    adjacent = a.style["position_adjacent"]
    return ToolMeta(
        tool="style",
        model=f"KMeans k={a.style['k']} (StandardScaler)",
        quality={**art.style_quality(a.style),
                 "n_players": a.style["n_players"]},
        clusters=[
            {"id": int(c), "name": names[c], "size": int(sizes[c]),
             "position_adjacent": bool(adjacent[c])}
            for c in sorted(names)
        ],
        thresholds=dict(a.style["thresholds"]),
        criteria={"groups": {g: list(cols)
                             for g, cols in a.style["groups"].items()},
                  "feature_labels": dict(a.style["feature_labels"])},
        plots=[f"/plots/03/{p.name}" for p in sorted(PLOT_DIRS["03"].glob("*.png"))],
    )


@router.get("/players", response_model=list[StylePlayerListItem])
def players(request: Request,
            position: str | None = Query(None)) -> list[StylePlayerListItem]:
    """Filters on ANY listed position, not the first.

    84 of the 315 players carry two (MF,FW and the like). First-token matching
    would hide 30 forwards from a client filtering on FW, which is how the
    Streamlit app behaves and must be reproduced exactly (AGENTS.md 5).
    """
    a = _a(request)
    df = a.style_assignments
    if position:
        df = df[df["pos"].str.contains(position, regex=False)]
    return [
        StylePlayerListItem(slug=r.slug, name=r.player, club=r.squad,
                            pos=r.pos, minutes=int(r.minutes))
        for _, r in df.sort_values("player").iterrows()
    ]


@router.get("/players/{slug}/assignment",
            response_model=StyleAssignmentResponse)
def assignment(request: Request, slug: str) -> StyleAssignmentResponse:
    a = _a(request)
    idx = a.style_by_slug.get(slug)
    if idx is None:
        raise HTTPException(404, f"No player with slug {slug!r}")
    r = a.style_assignments.iloc[idx]

    thresholds = a.style["thresholds"]
    tier = _tier(float(r.margin_to_next), float(r.silhouette), thresholds)

    feats = list(a.style["feature_names"])
    labels = dict(a.style["feature_labels"])
    group_of = {c: g for g, cols in a.style["groups"].items() for c in cols}
    rates = [
        Rate(key=f, label=labels[f], group=group_of[f],
             value=round(float(r[f]), 4),
             percentile=int(round((a.style_assignments[f] < r[f]).mean() * 100)))
        for f in feats
    ]

    members = a.style_assignments[a.style_assignments.cluster == r.cluster]
    dominant = members["pos"].str.split(",").str[0].value_counts()

    margins = a.style_assignments["margin_to_next"]
    zones = [
        Zone(name="CONTESTED", **{"from": 0.0},
             to=float(thresholds["contested_margin"]), state="low"),
        Zone(name="BORDERLINE", **{"from": float(thresholds["contested_margin"])},
             to=float(thresholds["borderline_margin"]), state="moderate"),
        Zone(name="CLEAR", **{"from": float(thresholds["borderline_margin"])},
             to=float(margins.max()), state="clear"),
    ]

    return StyleAssignmentResponse(
        status="ok",
        player={"slug": r.slug, "name": r.player, "club": r.squad,
                "pos": r.pos, "age": float(r.age), "minutes": int(r.minutes)},
        rates=rates,
        assignment=Assignment(
            cluster=int(r.cluster), cluster_name=r.cluster_name, tier=tier,
            distance_to_centroid=float(r.distance_to_centroid),
            distance_to_rival=float(r.distance_to_rival),
            margin_to_next=float(r.margin_to_next),
            silhouette=float(r.silhouette),
            negative_silhouette=bool(r.silhouette < 0),
            rival_cluster=int(r.rival_cluster),
            rival_cluster_name=r.rival_cluster_name,
            position_adjacent=bool(a.style["position_adjacent"][int(r.cluster)]),
            cluster_position_share=ClusterPositionShare(
                dominant=dominant.index[0],
                share=round(float(dominant.iloc[0] / len(members)), 4),
                n=int(len(members)),
            ),
        ),
        axis=Axis(min=0.0, max=float(margins.max()),
                  value=float(r.margin_to_next), zones=zones),
    )
