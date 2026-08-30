"""Project 01 -- market value estimate.

This tool DOES call the model per request, unlike project 02. The difference
is not arbitrary: project 01's in-sample R^2 (0.761) is close to its
cross-validated one (0.727), so live prediction does not misrepresent it.
Project 02's equivalent gap is 0.980 against 0.470, which is why AGENTS.md
section 2.1 forbids it there. See AGENTS.md section 2.2.
"""

from fastapi import APIRouter, HTTPException, Query, Request

from .. import artefacts as art
from ..config import PLOT_DIRS
from ..schemas import (Caveat, ToolMeta, ValueActual, ValueCalibration,
                       ValueEstimate, ValueEstimateResponse, ValuePlayer,
                       ValuePlayerListItem)

router = APIRouter(prefix="/value", tags=["value"])


def _players(request: Request):
    return request.app.state.artefacts


@router.get("/meta", response_model=ToolMeta)
def meta(request: Request) -> ToolMeta:
    a = _players(request)
    return ToolMeta(
        tool="value",
        model="LinearRegression (log target, age squared)",
        quality={**art.value_quality(a.value),
                 "n_training_rows": a.value["n_training_rows"]},
        criteria={"min_pl_minutes": a.value["min_pl_minutes"],
                  "competition": "GB1",
                  "players_listed": int(len(a.value_players)),
                  "players_modelled": int(a.value["n_training_rows"])},
        plots=[f"/plots/01/{p.name}"
               for p in sorted(PLOT_DIRS["01"].glob("*.png"))],
    )


@router.get("/players", response_model=list[ValuePlayerListItem])
def players(request: Request,
            club: str | None = Query(None),
            position: str | None = Query(None)) -> list[ValuePlayerListItem]:
    """The 661-row list, filtered as the Streamlit app filters it.

    Sub-threshold players are included on purpose. They are in the dropdown so
    the refusal can be shown; removing them would hide the limitation rather
    than communicate it.
    """
    a = _players(request)
    df = a.value_players
    if club:
        df = df[df["current_club_name"] == club]
    if position:
        df = df[df["position"] == position]
    minimum = a.value["min_pl_minutes"]
    return [
        ValuePlayerListItem(
            player_id=int(r.player_id), name=r["name"],
            club=r.current_club_name, position=r.position,
            pl_minutes=int(r.pl_minutes),
            eligible=bool(r.pl_minutes >= minimum),
        )
        for _, r in df.sort_values("name").iterrows()
    ]


@router.get("/players/{player_id}/estimate",
            response_model=ValueEstimateResponse)
def estimate(request: Request, player_id: int) -> ValueEstimateResponse:
    a = _players(request)
    rows = a.value_players[a.value_players["player_id"] == player_id]
    if rows.empty:
        raise HTTPException(404, f"No player with id {player_id}")
    r = rows.iloc[0]

    player = ValuePlayer(
        player_id=int(r.player_id), name=r["name"],
        club=r.current_club_name, position=r.position,
        sub_position=None if r.isna().get("sub_position", True) else r.sub_position,
        age=round(float(r.age), 2),
        pl_minutes=int(r.pl_minutes), pl_matches=int(r.pl_matches),
    )
    actual = ValueActual(market_value_eur=float(r.market_value_in_eur))

    minimum = float(a.value["min_pl_minutes"])
    if r.pl_minutes < minimum:
        # HTTP 200 with a status discriminant, not 4xx. The player exists and
        # the API knows about him; the model declines. A 404 would push the
        # client into an error path with error styling (API.md section 2).
        # The model is not called at all here.
        domain = a.value_modelling["pl_minutes"]
        return ValueEstimateResponse(
            status="not_calibrated",
            reason="below_minimum_minutes",
            player=player,
            estimate=None,
            actual=actual,
            calibration=ValueCalibration(
                field="pl_minutes", value=float(r.pl_minutes),
                minimum=minimum,
                domain_min=float(domain.min()), domain_max=float(domain.max()),
            ),
        )

    point = art.value_estimate_eur(a, r)
    factor = float(a.value["error_factor"])
    low, high = point / factor, point * factor
    actual.inside_band = bool(low <= actual.market_value_eur <= high)

    thresholds = a.value["caveat_thresholds"]
    caveats: list[Caveat] = []
    if r.age >= thresholds["veteran_age"]:
        caveats.append(Caveat(key="veteran", detail=f"{r.age:.1f}"))
    if (r.position in thresholds["blind_spot_positions"]
            and point < actual.market_value_eur / factor):
        caveats.append(Caveat(key="blind_spot", detail=r.position))

    return ValueEstimateResponse(
        status="ok",
        player=player,
        inputs={
            "pl_goals": float(r.pl_goals), "pl_assists": float(r.pl_assists),
            "pl_yellow_cards": float(r.pl_yellow_cards),
            "pl_red_cards": float(r.pl_red_cards),
            "goals_per90": round(float(r.goals_per90), 4),
            "assists_per90": round(float(r.assists_per90), 4),
        },
        estimate=ValueEstimate(point_eur=round(point, 2),
                               low_eur=round(low, 2), high_eur=round(high, 2),
                               error_factor=factor),
        actual=actual,
        caveats=caveats,
    )
