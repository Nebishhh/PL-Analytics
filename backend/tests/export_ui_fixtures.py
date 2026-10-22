"""Export API responses for the frontend end-to-end tests.

Run from the repository root:
    python -m backend.tests.export_ui_fixtures frontend/tests/e2e/.fixtures/fixtures.json

The browser tests intercept every /api call and answer it from this file, so
they need no live backend. Each response is produced by calling the real route
function in-process -- the same stand-in request test_constraints.py uses --
so the shapes are exactly what the API serves.

The output is generated from the committed artefacts on every run and is never
committed (frontend/.gitignore). A committed copy would be a second source of
truth for figures that must come from the artefacts (AGENTS.md section 2.3).

Two readings per tool are exported, and one display field in each is replaced
with a marker -- STALE_RESPONSE_A for the first, FRESH_RESPONSE_B for the
second -- so a test can tell from page text alone which response the page is
showing. Nothing else is altered. Read-only: this writes only the output file.

One more match is exported unmarked, from the earliest season with forecasts,
so a deep link to a match outside the default (latest) season can be tested
against its real club names.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import artefacts as art  # noqa: E402
from backend.routers import match, meta, style, value  # noqa: E402


def _dump(model) -> dict:
    # by_alias, as FastAPI serialises: Zone.from_ and ValueCalibration.field.
    return model.model_dump(mode="json", by_alias=True)


def _mark(payload: dict, path: tuple[str, ...], marker: str) -> dict:
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = marker
    return payload


def build() -> dict:
    a = art.load()
    req = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(artefacts=a)))

    # Query defaults are FastAPI Query objects when a route is called directly,
    # so every optional filter is passed explicitly.
    vplayers = value.players(req, club=None, position=None)
    eligible = [p for p in vplayers if p.eligible]
    va, vb = eligible[0], eligible[1]

    seasons = match.seasons(req)
    season = seasons[-1]
    fixtures = match.matches(req, season=season, club=None)
    ga, gb = fixtures[0], fixtures[1]

    early = seasons[0]
    early_fixtures = match.matches(req, season=early, club=None)
    ge = early_fixtures[0]

    splayers = style.players(req, position=None)
    sa, sb = splayers[0], splayers[1]

    def estimate(pid, marker):
        return _mark(_dump(value.estimate(req, pid)), ("player", "name"), marker)

    def forecast(gid, marker):
        return _mark(_dump(match.held_out_forecast(req, gid)),
                     ("match", "home_club"), marker)

    def assignment(slug, marker):
        return _mark(_dump(style.assignment(req, slug)), ("player", "name"), marker)

    return {
        "ids": {"value": [va.player_id, vb.player_id],
                "match": [ga.game_id, gb.game_id],
                "match_early": {"game_id": ge.game_id, "season": early},
                "style": [sa.slug, sb.slug],
                "season": season},
        "responses": {
            "/api/meta": _dump(meta.meta(req)),
            "/api/value/players": [_dump(p) for p in vplayers],
            "/api/value/meta": _dump(value.meta(req)),
            f"/api/value/players/{va.player_id}/estimate": estimate(va.player_id, "STALE_RESPONSE_A"),
            f"/api/value/players/{vb.player_id}/estimate": estimate(vb.player_id, "FRESH_RESPONSE_B"),
            "/api/match/seasons": seasons,
            "/api/match/meta": _dump(match.meta(req)),
            f"/api/match/clubs?season={season}": match.clubs(req, season=season),
            f"/api/match/matches?season={season}": [_dump(m) for m in fixtures],
            f"/api/match/matches/{ga.game_id}/held-out-forecast": forecast(ga.game_id, "STALE_RESPONSE_A"),
            f"/api/match/matches/{gb.game_id}/held-out-forecast": forecast(gb.game_id, "FRESH_RESPONSE_B"),
            f"/api/match/clubs?season={early}": match.clubs(req, season=early),
            f"/api/match/matches?season={early}": [_dump(m) for m in early_fixtures],
            f"/api/match/matches/{ge.game_id}/held-out-forecast":
                _dump(match.held_out_forecast(req, ge.game_id)),
            "/api/style/meta": _dump(style.meta(req)),
            "/api/style/players": [_dump(p) for p in splayers],
            f"/api/style/players/{sa.slug}/assignment": assignment(sa.slug, "STALE_RESPONSE_A"),
            f"/api/style/players/{sb.slug}/assignment": assignment(sb.slug, "FRESH_RESPONSE_B"),
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    fixtures = build()
    out.write_text(json.dumps(fixtures), encoding="utf-8")
    print(f"wrote {len(fixtures['responses'])} responses to {out}; ids {fixtures['ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
