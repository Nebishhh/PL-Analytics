# API.md — contract for the unified frontend

Spec only. **No backend or frontend code yet.**

Governed by [AGENTS.md](AGENTS.md); marks described in [DESIGN.md](DESIGN.md).

---

## 0. Why markdown and not `openapi.yaml`

FastAPI generates OpenAPI from the Pydantic response models automatically and
serves it at `/openapi.json`. A hand-written `openapi.yaml` would immediately
become a **second source of truth that drifts** from the Pydantic models — the
exact failure mode AGENTS.md §2.3 exists to prevent, one level up.

So:

- **`API.md`** (this file) — the contract, the rationale, and the shapes. Written
  first, reviewed, and binding.
- **`/openapi.json`** — generated from the implementation. Machine-readable.
- If they disagree, the implementation is wrong, not this file.

---

## 1. Naming principle: the route says what actually happens

AGENTS.md §2.1 makes project 02 categorically different from 01 and 03. A uniform
`/predict` across all three would hide that behind identical-looking routes, and a
frontend developer wiring up a third endpoint that looks like the first two has no
reason to suspect it is not allowed to be computed on demand.

**So the difference is in the route name, the response field, and the HTTP verb.**

| Tool | Route noun | What it means | Verb |
|---|---|---|---|
| 01 value | **`/estimate`** | Computed now, by calling the model | `GET` (idempotent, but *derived*) |
| 02 match | **`/held-out-forecast`** | **Retrieved.** Made earlier by a model that had not seen this season | `GET` (a stored record) |
| 03 style | **`/assignment`** | Retrieved. A stored label plus its uncertainty | `GET` (a stored record) |

`held-out` is deliberate: it is standard ML vocabulary for "not trained on", and it
cannot be misread as a live prediction. Anyone who writes
`POST /api/match/predict` has departed from this contract visibly.

**Every response also carries a `source` discriminant**, so the distinction survives
into the payload and is visible in the network tab, not only in the URL:

```
"source": "model_inference"            # 01 — the model ran just now
"source": "precomputed_out_of_fold"    # 02 — read from oof_predictions.csv
"source": "precomputed_assignment"     # 03 — read from cluster_assignments.csv
```

---

## 2. Status discriminant: refusal is not an error

Every tool response carries `status`. **Refusal and out-of-scope return HTTP 200.**

| `status` | HTTP | Meaning |
|---|---|---|
| `ok` | 200 | A reading is available |
| `not_calibrated` | **200** | 01 only. The player exists; the model declines (sub-900 minutes) |
| `out_of_scope` | **200** | 02 only. The match exists; no held-out forecast exists for it |

A 4xx would be wrong for both. The entity *exists* and the API *knows about it* —
it is the model that has nothing honest to say. AGENTS.md §4 requires this be
presented as a state, not a failure, and a 404 would push every frontend into an
error path with error styling.

**Genuine errors keep genuine codes:** unknown `player_id` → `404`; malformed
parameter → `422`; artefact failed to load → `503`.

---

## 3. Where each quality figure lives

One rule, applied consistently:

> **A figure needed to draw a mark goes in the response. A figure describing
> overall model quality goes in `/meta`.**

Duplication between the two is acceptable — both read from the same artefact, so
there is no drift risk. What is forbidden is a figure typed into a frontend literal
(AGENTS.md §2.3).

| Figure | Where | Why |
|---|---|---|
| `error_factor` (×1.75) | **Both** | Response: needed to draw the band. Meta: describes the model |
| `min_pl_minutes` (900) | **Both** | Response: draws the calibration rail. Meta: states the criterion |
| Baseline home rate (0.446) | **Both** | Response: the base-rate tick on every forecast |
| Confidence thresholds (0.10 / 0.50) | **Response** (`axis.zones`) | The zones are drawn on the axis |
| CV R², macro F1, silhouette, ARI | **Meta only** | Never drawn on a per-entity mark |
| Per-class precision/recall | **Meta only** | Belongs to the methodology page |
| Cluster names, sizes, feature means | **Meta** + name echoed in response | Response needs the name to label; meta has the full set |

### ⚠ Two artefact quirks the backend must absorb

**a) Project 01's metadata is shaped differently.** It stores flat `cv_r2_mean` /
`cv_r2_std` keys, while 02 uses a nested `cv` dict and 03 a nested `quality` dict.
The backend **normalises these into one response shape**. It must **not** rewrite
the artefact to match (AGENTS.md §0).

**b) The baseline must be read, not computed.** Computing the home-win rate over
all 4,616 matches gives **0.4521**. The artefact's `cv.baseline_accuracy` is
**0.446**. Serve the artefact value; do not recompute.

The reason is not that 0.446 is the "official" number — it is that **0.446 is the
only one of the two that is comparable to 0.470**.

The headline accuracy of 0.470 is a mean across 9 season-based folds, each measured
on one held-out season. `cv.baseline_accuracy` of 0.446 is a `DummyClassifier`
scored **under those same 9 folds, on those same test seasons**. The two numbers
are measurements of the same quantity on the same data under the same protocol, so
subtracting them is meaningful: the model beats always-guessing-home by 2.4 points.

0.4521 is a different quantity — the raw home-win rate across all 4,616 matches,
including the 1,649 from 2012–2016 that no fold ever tested on. Comparing 0.470
against it would be comparing a cross-validated score to a whole-population rate,
which is not a like-for-like difference and would silently misstate the model's
margin. The gap between the two baselines (0.6 points) is a quarter of the
model's entire claimed edge, so the distinction is not academic.

---

## 4. Endpoints

```
GET  /api/health

GET  /api/meta                                          aggregate, for /about

GET  /api/value/meta
GET  /api/value/players                                 ?club=&position=
GET  /api/value/players/{player_id}/estimate

GET  /api/match/meta
GET  /api/match/seasons
GET  /api/match/matches                                 ?season=&club=
GET  /api/match/matches/{game_id}/held-out-forecast

GET  /api/style/meta
GET  /api/style/players                                 ?position=
GET  /api/style/players/{player_id}/assignment
```

Listing endpoints exist to drive the ported dropdowns and must reproduce their
filter semantics exactly (AGENTS.md §5) — including that `/api/style/players`
matches **any** listed position, so `MF,FW` appears under both `MF` and `FW`.

---

## 5. Project 01 — value estimate

### `GET /api/value/players/{player_id}/estimate` — `status: ok`

Real values, William Saliba:

```json
{
  "status": "ok",
  "source": "model_inference",
  "player": {
    "player_id": 495666,
    "name": "William Saliba",
    "club": "Arsenal FC",
    "position": "Defender",
    "sub_position": "Centre-Back",
    "age": 25.43,
    "pl_minutes": 11492,
    "pl_matches": 131
  },
  "inputs": {
    "pl_goals": 7, "pl_assists": 2,
    "pl_yellow_cards": 12, "pl_red_cards": 1,
    "goals_per90": 0.0548, "assists_per90": 0.0157
  },
  "estimate": {
    "point_eur": 33800000,
    "low_eur": 19314286,
    "high_eur": 59150000,
    "error_factor": 1.75,
    "scale": "log10"
  },
  "actual": {
    "market_value_eur": 100000000,
    "inside_band": false
  },
  "caveats": [
    { "key": "blind_spot", "position_group": "Defender" }
  ]
}
```

- `low_eur` / `high_eur` are `point / factor` and `point * factor`. Sent computed
  so the frontend never re-derives the band.
- `"scale": "log10"` is a **contract-level enforcement of DESIGN.md V6**. A client
  that renders this linearly is contradicting a field it was handed.
- `inside_band` is computed server-side — the band's colour is the verdict
  (DESIGN.md §6), so the verdict must not depend on client float arithmetic.
- `caveats` is a **list of keys, not prose**. Copy lives in the frontend so it can
  be reviewed as copy. Keys: `blind_spot`, `veteran`.

### `status: not_calibrated` — Jamie Gittens, 490 minutes

```json
{
  "status": "not_calibrated",
  "source": "model_inference",
  "reason": "below_minimum_minutes",
  "player": {
    "player_id": 806055,
    "name": "Jamie Gittens",
    "club": "Chelsea FC",
    "position": "Attack",
    "age": 22.09,
    "pl_minutes": 490,
    "pl_matches": 16
  },
  "estimate": null,
  "calibration": {
    "field": "pl_minutes",
    "value": 490,
    "minimum": 900,
    "domain_min": 900,
    "domain_max": 32861
  },
  "actual": { "market_value_eur": 30000000 }
}
```

- `estimate` is **explicitly `null`**, never `0`, never omitted, never a wide band.
- The `calibration` block exists to draw DESIGN.md §6b's **second rail**:
  `domain_min`/`domain_max` give the rail its extent, `value` places the marker
  outside it.
- `actual` is still returned. The app knows the value; withholding it would be its
  own dishonesty.

### `GET /api/value/meta`

```json
{
  "tool": "value",
  "model": "LinearRegression (log target, age²)",
  "n_training_rows": 498,
  "quality": {
    "cv_r2_mean": 0.727, "cv_r2_std": 0.054,
    "cv_scheme": "5-fold",
    "error_factor": 1.75,
    "band_coverage": {
      "in_sample": 0.5884, "out_of_fold": 0.5763, "n": 498,
      "method": "actual within [prediction / 1.75, prediction * 1.75]",
      "cv_scheme": "5-fold, seed 42", "quote_this": "out_of_fold"
    }
  },
  "criteria": {
    "min_pl_minutes": 900,
    "competition": "GB1",
    "active_seasons": [2024, 2025]
  },
  "plots": ["/static/plots/01/04_age_curve.png", "..."]
}
```

`band_coverage` is the caveat that the ×1.75 band is a typical-error range, not a
confidence interval — it says how often the actual value really lands inside it.

**It is read from the artefact**, which stores the full block:

```json
"band_coverage": {
  "in_sample":   0.5884,
  "out_of_fold": 0.5763,
  "n": 498,
  "method": "actual within [prediction / 1.75, prediction * 1.75]",
  "cv_scheme": "5-fold, seed 42",
  "quote_this": "out_of_fold"
}
```

`/api/value/meta` serves this block verbatim. **The UI quotes `out_of_fold`
(58%)**, and the artefact says so itself via `quote_this` rather than leaving the
choice to whoever renders it.

Both figures are stored because they are different claims. `in_sample` (0.5884, the
59% in the current Streamlit caption) is measured with the shipped model predicting
the rows it was fitted on. `out_of_fold` (0.5763) predicts each player from a model
trained without them, under the same 5-fold scheme that produced the headline R².
A coverage rate shown to a reader as "the value lands in here N% of the time" is a
claim about unseen players, and only the out-of-fold figure supports it.

The gap is 1.2 points and 12 players — far smaller than project 02's 0.980 against
0.470 — but it is the same class of distinction, and this project resolves it the
same way every time.

---

## 6. Project 02 — held-out forecast

### `GET /api/match/matches/{game_id}/held-out-forecast` — `status: ok`

Real values, Arsenal v Tottenham, 2025-11-23:

```json
{
  "status": "ok",
  "source": "precomputed_out_of_fold",
  "computed_at_request_time": false,
  "match": {
    "game_id": 4625884,
    "date": "2025-11-23",
    "season": 2025,
    "matchday": 12,
    "home_club": "Arsenal FC",
    "away_club": "Tottenham Hotspur"
  },
  "forecast": {
    "probabilities": { "H": 0.658, "D": 0.1769, "A": 0.1651 },
    "order": ["H", "D", "A"],
    "labels": { "H": "Home win", "D": "Draw", "A": "Away win" },
    "top_pick": "H",
    "trained_on_seasons": "2012-2024"
  },
  "baseline": {
    "always_home_accuracy": 0.446,
    "label": "always predict home win"
  },
  "actual": {
    "outcome": "H",
    "top_pick_correct": true
  },
  "form": {
    "home": { "pre_ppg": 2.36, "pre_position": 1, "pts_l5": 2.60, "pts_l10": 2.30, "rest_days": 15 },
    "away": { "pre_ppg": 1.64, "pre_position": 8, "pts_l5": 1.40, "pts_l10": 1.50, "rest_days": 15 }
  }
}
```

- **`computed_at_request_time: false` is a literal in the response**, restating
  AGENTS.md §2.1 where a developer will actually see it. If this field is ever
  `true`, the constraint has been violated.
- **`order` is served, not inferred.** DESIGN.md V5 forbids sorting segments by
  value; sending the order makes that a contract term rather than a convention.
- **`baseline` appears on every single forecast** — this is the base-rate tick, the
  most important mark in the tool (DESIGN.md §7). Value comes from
  `cv.baseline_accuracy`; see §3(b).
- `trained_on_seasons` lets the UI state which seasons the forecasting model had
  seen, which is what makes "held-out" verifiable rather than asserted.

### `status: out_of_scope` — a 2013 match

```json
{
  "status": "out_of_scope",
  "source": "precomputed_out_of_fold",
  "reason": "no_held_out_forecast",
  "match": {
    "game_id": 2445301,
    "date": "2013-11-02",
    "season": 2013,
    "home_club": "Arsenal FC",
    "away_club": "Liverpool FC"
  },
  "forecast": null,
  "coverage": {
    "seasons_available": [2017, 2025],
    "matches_available": 2967,
    "matches_total": 4616,
    "reason_key": "no_prior_seasons_to_train_on"
  },
  "actual": { "outcome": "H" }
}
```

- `forecast: null`, never a uniform 1/3 distribution. A fabricated flat prior is
  worse than no answer.
- **The listing endpoint should not surface these matches by default**, matching
  the Streamlit app, which inner-joins to the OOF table. The endpoint still handles
  a direct `game_id` because a bookmarked URL must not 500.

### `GET /api/match/meta`

```json
{
  "tool": "match",
  "model": "HistGradientBoostingClassifier (class_weight=balanced)",
  "n_training_rows": 4616,
  "quality": {
    "cv_scheme": "season-based expanding window, 9 folds",
    "accuracy": 0.47, "accuracy_sd": 0.031,
    "macro_f1": 0.429, "macro_f1_sd": 0.028,
    "baseline_accuracy": 0.446,
    "log_loss": 1.158,
    "per_class": {
      "H": { "precision": 0.56, "recall": 0.63, "f1": 0.59 },
      "D": { "precision": 0.26, "recall": 0.26, "f1": 0.26 },
      "A": { "precision": 0.49, "recall": 0.40, "f1": 0.44 }
    }
  },
  "coverage": {
    "forecasts_available": 2967,
    "matches_total": 4616,
    "seasons_available": [2017, 2025],
    "source": "oof_predictions.csv"
  }
}
```

`per_class.D.recall = 0.26` is the draw-blindness figure. It is served so the UI's
draw caveat quotes the artefact rather than a hardcoded "1 in 4".

---

## 7. Project 03 — cluster assignment

### `GET /api/style/players/{player_id}/assignment` — `status: ok`

Real values, Lewis Hall:

```json
{
  "status": "ok",
  "source": "precomputed_assignment",
  "player": {
    "name": "Lewis Hall",
    "club": "Newcastle United",
    "pos": "DF",
    "age": 20,
    "minutes": 2181
  },
  "rates": [
    { "key": "def_tklw_p90", "label": "tackles won", "group": "DEFENSIVE_ACTIVITY",
      "value": 1.28, "percentile": 74 }
  ],
  "assignment": {
    "cluster": 2,
    "cluster_name": "High tackles won, fouls, yellow cards",
    "tier": "CONTESTED",
    "distance_to_centroid": 2.6102,
    "distance_to_rival": 2.6525,
    "margin_to_next": 0.0423,
    "silhouette": -0.0511,
    "negative_silhouette": true,
    "rival_cluster": 1,
    "rival_cluster_name": "Low involvement - below average across all three groups (mean z -0.35), no feature in either quartile",
    "position_adjacent": false,
    "cluster_position_share": { "dominant": "MF", "share": 0.56, "n": 86 }
  },
  "axis": {
    "min": 0.0,
    "max": 2.7423,
    "value": 0.0423,
    "zones": [
      { "name": "CONTESTED",  "from": 0.0,  "to": 0.10,   "state": "low" },
      { "name": "BORDERLINE", "from": 0.10, "to": 0.50,   "state": "moderate" },
      { "name": "CLEAR",      "from": 0.50, "to": 2.7423, "state": "clear" }
    ]
  }
}
```

- **`axis.zones` is the whole point.** The thresholds are drawn on the rail
  (DESIGN.md §8), so they are served as data. A frontend containing the literals
  `0.10` or `0.50` has violated AGENTS.md §2.3.
- `state` values map directly onto the semantic colour tokens, so the client picks
  no colours itself.
- `negative_silhouette` is a **separate boolean**, not folded into `tier`, because
  it is a distinct failure mode — only 4 of the 19 negative-silhouette players also
  have a margin under 0.10.
- `cluster_name` and `rival_cluster_name` come from the artefact. AGENTS.md §2.4
  forbids the frontend inventing archetype language.
- `rates[].percentile` is computed server-side over all 315, feeding the miniature
  rails in DESIGN.md §8.

### `GET /api/style/meta`

```json
{
  "tool": "style",
  "model": "KMeans k=4 (StandardScaler)",
  "n_players": 315,
  "quality": {
    "silhouette": 0.1799,
    "silhouette_note": "Below 0.25, the conventional threshold...",
    "stability_ari_mean": 0.966,
    "stability_ari_min": 0.925,
    "groupnorm_ari": 0.835,
    "group_variance_shares": {
      "ATTACKING_OUTPUT": 50.0, "DEFENSIVE_ACTIVITY": 20.0, "DISCIPLINE": 30.0
    }
  },
  "clusters": [
    { "id": 0, "name": "High goals, shots, shot accuracy; low interceptions, tackles won",
      "size": 51, "position_adjacent": true },
    { "id": 1, "name": "Low involvement - ...", "size": 114, "position_adjacent": true },
    { "id": 2, "name": "High tackles won, fouls, yellow cards", "size": 86, "position_adjacent": false },
    { "id": 3, "name": "High assists, crosses, fouls drawn", "size": 64, "position_adjacent": false }
  ],
  "thresholds": { "contested_margin": 0.10, "borderline_margin": 0.50, "borderline_silhouette": 0.05 }
}
```

`position_adjacent` is served per cluster so the "mostly restates position" tag is
data-driven rather than a hardcoded `{0, 1}` set in the client.

---

## 8. Shape → mark mapping

Every field exists because a mark needs it. This table is the check that the
contract actually serves DESIGN.md.

| Mark (DESIGN.md) | Fields |
|---|---|
| §6 value band | `estimate.{point,low,high}_eur`, `estimate.scale`, `actual.market_value_eur`, `actual.inside_band` |
| §6b calibration rail | `calibration.{value,minimum,domain_min,domain_max}` |
| §7 probability split | `forecast.probabilities`, `forecast.order` |
| §7 base-rate tick | `baseline.always_home_accuracy` |
| §8 zoned axis | `axis.{min,max,value,zones}` |
| §8 secondary flag | `assignment.negative_silhouette` |
| §8 per-90 mini-rails | `rates[].{value,percentile,group}` |
| State chips | `status`, `assignment.tier`, `caveats[].key` |

---

## 9. Not in v1

- `POST` anything. The API is read-only.
- Arbitrary-input prediction (`?goals=12&minutes=900`). The models have no business
  extrapolating to invented players; all three Streamlit apps enforce a closed set
  and the API must too.
- Comparison endpoints (AGENTS.md §5).
- Any endpoint for seasons 2012–2016 forecasts (AGENTS.md §2.1).
- Pagination. Largest list is 661 rows; send it.
- Auth, rate limiting, caching headers beyond `Cache-Control` on `/meta`.
