"""Aggregate metadata, for the shell's /about route.

Carries the honesty material the README holds, so the app states its own
limits rather than relying on a reader finding the repository.
"""

from fastapi import APIRouter, Request

from .. import artefacts as art

router = APIRouter(tags=["meta"])


@router.get("/health")
def health(request: Request) -> dict:
    a = getattr(request.app.state, "artefacts", None)
    if a is None:
        return {"status": "loading"}
    return {
        "status": "ok",
        "artefacts": {
            "value": a.value["trained_date"],
            "match": a.match["trained_date"],
            "style": a.style["trained_date"],
        },
        "rows": {
            "value_players": int(len(a.value_players)),
            "match_features": int(len(a.match_features)),
            "match_forecasts": int(len(a.match_oof)),
            "style_players": int(len(a.style_assignments)),
        },
    }


@router.get("/meta")
def meta(request: Request) -> dict:
    a = request.app.state.artefacts
    return {
        "tools": [
            {
                "id": "value", "name": "Value predictor",
                "technique": "Linear regression",
                "headline": art.value_quality(a.value),
                "limitation": (
                    "No club-quality or reputation signal, so elite defenders, "
                    "holding midfielders and goalkeepers are systematically "
                    "under-predicted."
                ),
            },
            {
                "id": "match", "name": "Match predictor",
                "technique": "Classification",
                "headline": art.match_quality(a.match),
                "limitation": (
                    "The model has learned home advantage and relative form, "
                    "and has learned nothing about draws."
                ),
            },
            {
                "id": "style", "name": "Style finder",
                "technique": "K-Means clustering",
                "headline": art.style_quality(a.style),
                "limitation": (
                    "The clustering is least trustworthy exactly where it is "
                    "most interesting: the best-separated clusters are the "
                    "ones that merely restate position."
                ),
            },
        ],
        "licensing": {
            "code": "MIT",
            "player_scores_data": "CC0-1.0 (Kaggle, davidcariboo/player-scores)",
            "player_stats_data": "MIT (Kaggle, hubertsidorowicz/"
                                 "football-players-stats-2025-2026)",
            "note": "The code licence being MIT and the project-03 data "
                    "licence being MIT is a coincidence, not a shared grant.",
        },
    }
