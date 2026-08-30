"""Project 02 -- held-out match forecast.

⛔ THIS MODULE MUST NEVER CALL predict_proba. AGENTS.md section 2.1.

Every match in the feature table is in the shipped model's training set, where
it scores 0.980. The model's real accuracy is 0.470. An endpoint that computed
forecasts per request would report the top pick correct 98% of the time for a
model right slightly less than half the time -- a factor-of-two
misrepresentation that no caption in the UI undoes.

So forecasts are READ from oof_predictions.csv, where each match was predicted
by a model trained only on the seasons before it. The match model.joblib is
loaded for its metadata and is never invoked.

The 1,649 matches from 2012-2016 have no held-out forecast because they have
no prior seasons to train on. They are out of scope by design, not missing
data, and are returned as such rather than filled with a flat prior.
"""

from fastapi import APIRouter, HTTPException, Query, Request

from .. import artefacts as art
from ..config import PLOT_DIRS
from ..schemas import (Baseline, Coverage, Forecast, HeldOutForecastResponse,
                       MatchActual, MatchSummary, SideForm, ToolMeta)

router = APIRouter(prefix="/match", tags=["match"])


def _a(request: Request):
    return request.app.state.artefacts


def _summary(r) -> MatchSummary:
    return MatchSummary(
        game_id=int(r.game_id), date=str(r.date)[:10], season=int(r.season),
        matchday=int(r.home_matchday) if "home_matchday" in r else None,
        home_club=r.home_club_name, away_club=r.away_club_name,
    )


@router.get("/meta", response_model=ToolMeta)
def meta(request: Request) -> ToolMeta:
    a = _a(request)
    return ToolMeta(
        tool="match",
        model="HistGradientBoostingClassifier (class_weight=balanced)",
        quality={**art.match_quality(a.match),
                 "n_training_rows": a.match["n_training_rows"]},
        coverage={
            "forecasts_available": int(len(a.match_oof)),
            "matches_total": int(len(a.match_features)),
            "seasons_available": [int(a.match_oof.season.min()),
                                  int(a.match_oof.season.max())],
            "source": "oof_predictions.csv",
            "note": "Seasons before the first available one have no prior "
                    "seasons to train on, so no honest forecast exists.",
        },
        plots=[f"/plots/02/{p.name}" for p in sorted(PLOT_DIRS["02"].glob("*.png"))],
    )


@router.get("/seasons", response_model=list[int])
def seasons(request: Request) -> list[int]:
    """Only seasons with held-out forecasts, matching the Streamlit app,
    which inner-joins its match table to the OOF table."""
    a = _a(request)
    return sorted(int(s) for s in a.match_oof.season.unique())


@router.get("/matches")
def matches(request: Request,
            season: int | None = Query(None),
            club: str | None = Query(None)) -> list[dict]:
    """Fixture list for the Season -> Club -> Match chain.

    Restricted to matches that have a forecast. A bookmarked game_id outside
    that set still resolves (see below); it is simply not offered here.
    """
    a = _a(request)
    df = a.match_features[a.match_features.game_id.isin(a.match_oof_index)]
    if season is not None:
        df = df[df.season == season]
    if club:
        df = df[(df.home_club_name == club) | (df.away_club_name == club)]
    df = df.sort_values("date")
    return [
        {"game_id": int(r.game_id), "date": str(r.date)[:10],
         "season": int(r.season),
         "home_club": r.home_club_name, "away_club": r.away_club_name,
         # Deliberately no score. Putting the result in the selector would
         # answer the question before the model has spoken.
         "venue": ("H" if club and r.home_club_name == club
                   else "A" if club else None)}
        for _, r in df.iterrows()
    ]


@router.get("/clubs", response_model=list[str])
def clubs(request: Request, season: int | None = Query(None)) -> list[str]:
    a = _a(request)
    df = a.match_features[a.match_features.game_id.isin(a.match_oof_index)]
    if season is not None:
        df = df[df.season == season]
    return sorted(set(df.home_club_name) | set(df.away_club_name))


@router.get("/matches/{game_id}/held-out-forecast",
            response_model=HeldOutForecastResponse)
def held_out_forecast(request: Request, game_id: int) -> HeldOutForecastResponse:
    a = _a(request)
    rows = a.match_features[a.match_features.game_id == game_id]
    if rows.empty:
        raise HTTPException(404, f"No match with game_id {game_id}")
    r = rows.iloc[0]
    actual_outcome = str(r.target)

    stored = a.match_oof_index.get(int(game_id))
    if stored is None:
        # Out of scope, not an error, and not a fabricated flat prior. 200.
        return HeldOutForecastResponse(
            status="out_of_scope",
            reason="no_held_out_forecast",
            match=_summary(r),
            forecast=None,
            actual=MatchActual(outcome=actual_outcome),
            coverage=Coverage(
                seasons_available=[int(a.match_oof.season.min()),
                                   int(a.match_oof.season.max())],
                matches_available=int(len(a.match_oof)),
                matches_total=int(len(a.match_features)),
                reason_key="no_prior_seasons_to_train_on",
            ),
        )

    # Read, do not compute.
    order = list(a.match["target_order"])              # fixed H, D, A
    probs = {k: round(float(stored[f"p_{k}"]), 4) for k in order}
    top = max(probs, key=probs.get)

    return HeldOutForecastResponse(
        status="ok",
        match=_summary(r),
        forecast=Forecast(
            probabilities=probs,
            order=order,
            labels=dict(a.match["class_labels"]),
            top_pick=top,
            trained_on_seasons=str(stored["trained_on_seasons"]),
        ),
        baseline=Baseline(
            # From the artefact, never recomputed. Recomputing the home-win
            # rate over all 4,616 matches gives 0.4521, but the comparable
            # figure is the dummy scored under the same 9 folds that produced
            # the 0.470 headline. See API.md section 3(b).
            always_home_accuracy=float(a.match["cv"]["baseline_accuracy"]),
        ),
        actual=MatchActual(outcome=actual_outcome,
                           top_pick_correct=bool(top == actual_outcome)),
        form={
            "home": SideForm(
                pre_ppg=float(r.home_pre_ppg),
                pre_position=float(r.home_pre_position),
                pts_l5=float(r.home_pts_l5), pts_l10=float(r.home_pts_l10),
                rest_days=None if r.isna().get("home_rest_days", True)
                else float(r.home_rest_days)),
            "away": SideForm(
                pre_ppg=float(r.away_pre_ppg),
                pre_position=float(r.away_pre_position),
                pts_l5=float(r.away_pts_l5), pts_l10=float(r.away_pts_l10),
                rest_days=None if r.isna().get("away_rest_days", True)
                else float(r.away_rest_days)),
        },
    )
