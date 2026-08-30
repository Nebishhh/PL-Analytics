# AGENTS.md

Constraints for any agent or contributor writing code in this repository.

Read this **before** writing a component, an endpoint, or a query. Most rules here
exist because the alternative was tried, measured, and found to misrepresent a
model. Where a rule has a measured justification, the number is given — treat the
number as the reason, not decoration.

Companion documents: [getdesign.md](getdesign.md) (research), [DESIGN.md](DESIGN.md)
(visual system). This file is the enforceable subset.

---

## 0. Scope boundary — the frontend work is strictly additive

New work lives in **`backend/`** and **`frontend/`** only.

### Do not modify, for any reason

```
01-value-predictor/**      02-match-predictor/**      03-style-finder/**
data/processed/**          *.joblib                   *.csv artefacts
.streamlit/config.toml     README.md model claims
```

The three Streamlit apps are **working references and fallbacks** for the duration
of this build. They stay runnable on ports 8501/8502/8503.

**Specifically forbidden**, even when it looks like an improvement:

- Re-running `train_final.py` or `cluster.py` to "refresh" an artefact
- Re-training, re-tuning, or changing a hyperparameter
- Regenerating `plots/*.png`
- Editing a Streamlit app "for consistency with the new frontend"
- Reformatting a committed CSV
- Deleting a Streamlit app once its React equivalent works

If the port reveals a genuine bug in existing project code, **stop and report it**.
Do not fix it as part of frontend work — that couples two changes that need
separate review.

---

## 1. Binding technical decisions

Resolved in Step 3. Do not relitigate these in code.

### 1.1 Charts are hand-rolled SVG

No Recharts, Chart.js, D3-chart abstractions, Nivo, Victory, or Plotly.

**Why:** every chart library ships opinionated defaults — categorical palettes,
tooltips, legends, animated entrances — and this system forbids most of them
(§3). Fighting a library's conventions to preserve the semantic-colour-only rule
costs more than drawing four marks by hand. Hand-rolling also guarantees the four
uncertainty marks share **one** rail implementation, which is what makes three
tools read as one instrument.

D3 as a *scale/format utility* (`d3-scale`, `d3-format`) is permitted. D3 as a
*renderer* is not.

### 1.2 FastAPI wraps the existing artefacts, read-only

The backend loads the three committed `model.joblib` files and serves them. It does
not train, does not write to them, and does not maintain its own copy.

### 1.3 Methodology pages reuse the committed PNGs

`01-value-predictor/plots/*.png`, `02-match-predictor/plots/*.png`,
`03-style-finder/plots/*.png` are served as static assets.

**Why:** they are the evidence the README's claims rest on. Regenerating them in
the browser, or with different styling, creates drift between what the README says
and what the app shows. Serve the exact files.

---

## 2. Model and data integrity

This section is the reason the repository exists. Violating it produces an app that
lies.

### 2.1 ⛔ HARD REQUIREMENT — project 02 must never call `predict_proba` on a match

**The backend must serve precomputed out-of-fold predictions from
`02-match-predictor/oof_predictions.csv`, exactly as the Streamlit app does.**

**Why, with the measurement:** every match in the feature table is in the shipped
model's training set, where it scores **0.980**. The model's real accuracy is
**0.470**. An endpoint calling `predict_proba` would report the top pick as correct
**98%** of the time for a model that is right slightly less than half the time. That
is a factor-of-two misrepresentation, and no caption anywhere in the UI undoes it.

Concretely:

- ✅ Read `p_H`, `p_D`, `p_A` from `oof_predictions.csv`, keyed on `game_id`
- ✅ Serve `rival`-style metadata (`trained_on_seasons`) alongside, so the UI can
  state which seasons the forecasting model had seen
- ⛔ Do **not** load the match `model.joblib` and call `.predict_proba()` per request
- ⛔ Do **not** "optimise" by computing predictions on the fly
- ⛔ Do **not** extend coverage to seasons 2012–2016 by predicting them — they have
  no prior seasons to train on and therefore have no honest forecast. **2,967 of
  4,616 matches are available. The other 1,649 are not, by design.**

A match with no row in `oof_predictions.csv` is **out of scope**, not an error.
Return a state that says so.

The match `model.joblib` may still be loaded — for its metadata (§2.3). Loading it
is fine. Calling it on a match is not.

### 2.2 Projects 01 and 03 may call the model

Different situation, and the difference is worth understanding rather than
pattern-matching.

- **Project 01** predicts a *continuous value* whose in-sample R² (0.761) is close
  to its cross-validated R² (0.727). Live prediction does not misrepresent it.
- **Project 03** assigns a cluster; the app shows *stored* assignments and
  uncertainty from `cluster_assignments.csv`. Prefer the stored table. Calling
  `.predict()` is acceptable only for a profile not in the 315.

### 2.3 Never hardcode a quality figure

Every accuracy, R², silhouette, threshold and baseline **must be read from the
artefact metadata at runtime**, not typed into a component.

| Figure | Source |
|---|---|
| 01 R², error factor ×1.75, 900-min floor | `01-value-predictor/model.joblib` → `cv`, `error_factor`, `min_pl_minutes` |
| 02 accuracy, baseline, macro F1, per-class P/R/F1 | `02-match-predictor/model.joblib` → `cv` |
| 03 silhouette, ARI, group variance shares, cluster names | `03-style-finder/model.joblib` → `quality`, `cluster_names` |
| 03 confidence thresholds (0.10 / 0.50 / 0.05) | Import from the app's constants, or re-declare **once** in backend config |

**Why:** the numbers have already moved once. Reordering rows in project 01 shifted
its headline R² from 0.729 to 0.727, and every hardcoded copy had to be chased down
across four files. A figure typed into JSX is a figure that will be wrong.

### 2.4 Never invent cluster names

Project 03's cluster names are **generated mechanically** from feature quartiles and
stored in the artefact. Read them.

⛔ Do not write "Inverted winger", "Deep-lying playmaker", "Ball-winner",
"Target man", or any archetype term. This dataset has **no passing, dribbling,
expected-goals, touch or carry columns**. Every one of those names is a claim the
data cannot support.

### 2.5 Position is display-only in project 03

`Pos` was held out of the clustering deliberately, so that cross-tabulating clusters
against it is a real validation. Show it, label it as held out, and never feed it
into anything.

### 2.6 Raw data stays out

`data/raw/**` is gitignored and must remain so. The backend reads only from
`data/processed/**` and the project folders' committed artefacts. No endpoint
re-derives features from raw CSVs.

---

## 3. Visual system rules

Formalised from DESIGN.md §11. Each is checkable.

| # | Rule | Check |
|---|---|---|
| V1 | **No data mark in a tool accent colour.** Hue is navigation only. | `--tool-01/02/03` must not appear in any `<svg>` subtree |
| V2 | **No red on a refusal state.** Refusal uses `--state-null` grey. | Refusal components must not reference `--state-low` |
| V3 | **No warning box where a mark would do.** | If it can be drawn on a rail, it must not be a callout |
| V4 | **One sentence beside a mark, then a disclosure.** No paragraphs inline. | Finding text ≤ ~2 lines; rest behind `<Disclosure>` |
| V5 | **Probability segments are fixed H·D·A.** Never sorted by value. | Segment order is a constant, not derived |
| V6 | **Market value uses a log scale.** | Linear scale on the value rail is a bug |
| V7 | **All figures use tabular numerals.** | `font-variant-numeric: tabular-nums` on every number |
| V8 | **One rail height across all tools** (`--rail-h`). | Rails must not set their own height |
| V9 | **No claim of skill from a single case.** | Copy must not imply one correct forecast is evidence |
| V10 | **Only two font weights**, 400 and 600. | No 300/500/700/800 |

### 3.1 Additional prohibitions

- No gradients on data marks. A gradient encodes a value that does not exist.
- No glow, neon, or drop-shadow on a rail. This is not a broadcast graphic.
- No counters animating up to their value. The number is a measurement, not a reveal.
- No scroll-triggered animation, parallax, or 3D.
- No tooltips as the *only* home for a caveat. Anything essential must be visible
  or behind an explicit disclosure, never behind hover — hover does not exist on
  touch and is invisible to a scanner.
- Everything in §3.1 must honour `prefers-reduced-motion`.

---

## 4. Copy rules

The caveats **are** the product. An agent optimising for a clean interface will be
tempted to trim them. Do not.

- **Never delete a caveat to reduce visual noise.** Move it behind a disclosure.
  §3 V3/V4 give you somewhere to put it.
- **Name the alternative first when confidence is low.** From project 03: for a
  contested assignment, the rival cluster is named *before* the assigned one,
  because leading with the assignment asserts what the geometry does not support.
- **Do not restate what a mark already shows.** If the band visibly excludes the
  actual value, the sentence explains *why*, not *that*.
- **Refusal copy says "not calibrated", never "error", "unavailable", or "N/A".**
- **Never describe project 03's output as "playing styles"** — the term is
  "activity profiles". The naming is load-bearing and is enforced in the existing
  code by the absence of any `STYLE_FEATURES` constant.
- Prefer the existing apps' wording where it exists. It was reviewed line by line.

---

## 5. Scope discipline

v1 is a **faithful port**. Three tools under one shell.

⛔ Not in v1, do not add opportunistically:

- Comparison view (two players or two matches side by side)
- Live/upcoming fixture prediction — see README *Ideas parked for later*; it needs
  a data pipeline that does not exist
- Any new model, feature, or metric
- Auth, accounts, persistence, or analytics
- Cross-tool navigation beyond the top bar

Each tool ports its existing controls exactly: project 01's Club + Position filters,
project 02's Season → Club → Match chain, project 03's Position filter. Same
defaults ("All …"), same behaviour — including that project 03's position filter
matches **any** listed position, so `MF,FW` appears under both.

---

## 6. Pre-flight checklist

Before writing any component, answer these:

1. **Does this render a number?** → Read it from artefact metadata (§2.3), not a
   literal. Tabular numerals (V7).
2. **Does this express uncertainty?** → It must be a **drawn mark on a rail**
   (§3 V3), not a coloured box.
3. **Is this a project-02 forecast?** → It comes from `oof_predictions.csv`
   (§2.1). If you typed `predict_proba`, stop.
4. **Is this a refusal / no-data state?** → Grey, "not calibrated", second rail
   showing the calibrated range (V2, §4).
5. **Am I about to add a colour?** → Semantic scale for meaning, tool accent for
   navigation, nothing else (V1).
6. **Am I about to write more than one sentence next to a mark?** → Disclosure (V4).
7. **Am I about to touch a file outside `backend/` or `frontend/`?** → Stop (§0).
8. **Am I about to name a cluster?** → Read it from the artefact (§2.4).

---

## 7. Verification

Run before considering any milestone done.

```bash
python -c "import joblib; [print(p, sorted(joblib.load(p).keys())) for p in ['01-value-predictor/model.joblib','02-match-predictor/model.joblib','03-style-finder/model.joblib']]"
```

```bash
git status --porcelain | grep -vE '^\?\? (backend|frontend)/|^ M (backend|frontend)/' || echo "additive only - ok"
```

```bash
grep -rn "predict_proba" backend/ | grep -i match && echo "VIOLATION of 2.1" || echo "OOF constraint intact"
```

Manual checks that no grep will catch:

- The three Streamlit apps still run on 8501/8502/8503 and produce identical output
  to before the frontend work started.
- A project-02 forecast in the React app matches the Streamlit app's numbers **for
  the same `game_id`**, to the displayed precision.
- A 2013 match is unavailable in both, with the same explanation.
- Project 01 refuses for a sub-900-minute player, in grey, without the word "error".
- Every headline figure shown in the UI matches the README.

---

## 8. When a rule blocks something genuinely better

These rules encode measured findings, not taste — but they are not sacred.

If a rule prevents a real improvement: **stop, state which rule, state the evidence
that it is wrong here, and ask.** Do not route around it silently, and do not weaken
it in passing.

The one exception, which is not negotiable and should not be raised: **§2.1**. The
out-of-fold constraint is the difference between an honest app and one claiming 98%
accuracy for a 47% model.
