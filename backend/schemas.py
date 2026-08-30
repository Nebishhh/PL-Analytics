"""Pydantic response models. These generate /openapi.json.

API.md is the binding contract; this file is its implementation. If the two
disagree, this file is wrong.

Two conventions carried from API.md and worth not losing:

  `status`  discriminates ok / not_calibrated / out_of_scope, and all three
            are returned with HTTP 200. Refusal is a state, not a failure.

  `source`  says whether the number was computed just now or retrieved. It
            makes project 02's constraint visible in the payload, not only in
            the route name.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Source = Literal["model_inference", "precomputed_out_of_fold",
                 "precomputed_assignment"]


# --- shared -------------------------------------------------------------------

class BandCoverage(BaseModel):
    in_sample: float
    out_of_fold: float
    n: int
    method: str
    cv_scheme: str
    quote_this: str = Field(
        description="Which of the two figures a UI should display."
    )


# --- 01 value -----------------------------------------------------------------

class ValuePlayer(BaseModel):
    player_id: int
    name: str
    club: str
    position: str
    sub_position: str | None = None
    age: float
    pl_minutes: int
    pl_matches: int


class ValuePlayerListItem(BaseModel):
    player_id: int
    name: str
    club: str
    position: str
    pl_minutes: int
    eligible: bool = Field(
        description="False below min_pl_minutes. Such players stay in the "
                    "list on purpose: removing them would hide the refusal "
                    "rather than communicate it."
    )


class ValueEstimate(BaseModel):
    point_eur: float
    low_eur: float
    high_eur: float
    error_factor: float
    scale: Literal["log10"] = Field(
        default="log10",
        description="The band is only meaningful on a log axis; values span "
                    "EUR100k to EUR200m. A client rendering this linearly "
                    "contradicts a field it was handed.",
    )


class ValueActual(BaseModel):
    market_value_eur: float
    inside_band: bool | None = Field(
        default=None,
        description="Computed server-side; the band's colour is the verdict, "
                    "so it must not depend on client float arithmetic.",
    )


class ValueCalibration(BaseModel):
    field_name: str = Field(alias="field")
    value: float
    minimum: float
    domain_min: float
    domain_max: float

    model_config = {"populate_by_name": True}


class Caveat(BaseModel):
    key: Literal["blind_spot", "veteran"]
    detail: str | None = None


class ValueEstimateResponse(BaseModel):
    status: Literal["ok", "not_calibrated"]
    source: Source = "model_inference"
    reason: str | None = None
    player: ValuePlayer
    inputs: dict[str, float] | None = None
    estimate: ValueEstimate | None = None
    actual: ValueActual
    calibration: ValueCalibration | None = None
    caveats: list[Caveat] = []


# --- 02 match -----------------------------------------------------------------

class MatchSummary(BaseModel):
    game_id: int
    date: str
    season: int
    matchday: int | None = None
    home_club: str
    away_club: str


class Forecast(BaseModel):
    probabilities: dict[str, float]
    order: list[str] = Field(
        description="Fixed H, D, A. Served rather than inferred so that "
                    "DESIGN.md's no-sorted-segments rule is a contract term."
    )
    labels: dict[str, str]
    top_pick: str
    trained_on_seasons: str


class Baseline(BaseModel):
    always_home_accuracy: float
    label: str = "always predict home win"


class MatchActual(BaseModel):
    outcome: str
    top_pick_correct: bool | None = None


class Coverage(BaseModel):
    seasons_available: list[int]
    matches_available: int
    matches_total: int
    reason_key: str


class SideForm(BaseModel):
    pre_ppg: float | None = None
    pre_position: float | None = None
    pts_l5: float | None = None
    pts_l10: float | None = None
    rest_days: float | None = None


class HeldOutForecastResponse(BaseModel):
    status: Literal["ok", "out_of_scope"]
    source: Source = "precomputed_out_of_fold"
    computed_at_request_time: Literal[False] = Field(
        default=False,
        description="Always false. AGENTS.md section 2.1 forbids calling the "
                    "model per request; this restates it where a developer "
                    "will see it. If it is ever true, the constraint broke.",
    )
    reason: str | None = None
    match: MatchSummary
    forecast: Forecast | None = None
    baseline: Baseline | None = None
    actual: MatchActual
    coverage: Coverage | None = None
    form: dict[str, SideForm] | None = None


# --- 03 style -----------------------------------------------------------------

class StylePlayerListItem(BaseModel):
    slug: str
    name: str
    club: str
    pos: str
    minutes: int


class Rate(BaseModel):
    key: str
    label: str
    group: str
    value: float
    percentile: int


class Zone(BaseModel):
    name: str
    from_: float = Field(alias="from")
    to: float
    state: Literal["low", "moderate", "clear"]

    model_config = {"populate_by_name": True}


class Axis(BaseModel):
    min: float
    max: float
    value: float
    zones: list[Zone]


class ClusterPositionShare(BaseModel):
    dominant: str
    share: float
    n: int


class Assignment(BaseModel):
    cluster: int
    cluster_name: str
    tier: Literal["CONTESTED", "BORDERLINE", "PLACED"]
    distance_to_centroid: float
    distance_to_rival: float
    margin_to_next: float
    silhouette: float
    negative_silhouette: bool
    rival_cluster: int
    rival_cluster_name: str
    position_adjacent: bool
    cluster_position_share: ClusterPositionShare


class StyleAssignmentResponse(BaseModel):
    status: Literal["ok"]
    source: Source = "precomputed_assignment"
    player: dict
    rates: list[Rate]
    assignment: Assignment
    axis: Axis


# --- meta ---------------------------------------------------------------------

class ToolMeta(BaseModel):
    tool: str
    model: str
    quality: dict
    criteria: dict = {}
    coverage: dict = {}
    clusters: list[dict] = []
    thresholds: dict = {}
    plots: list[str] = []
