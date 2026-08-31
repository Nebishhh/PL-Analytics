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

### 0.1 Permitted exception: extending an artefact's metadata

There is one category of change to protected project code that is allowed.

**When a figure the application genuinely needs is missing from an artefact, the
artefact gets extended — the gap is not worked around in application code.**

A backend constant, a frontend literal, or a value recomputed at request time is a
second source of truth, and it will drift. §2.3 exists because that has already
happened once in this repository.

#### Conditions — all four must hold

1. **A new key is added.** No existing key is modified or removed.
2. **No retraining.** No coefficient, intercept, scaler statistic, cluster centroid
   or prediction changes.
3. **Proof is shown in the commit message.** Capture the artefact's state before
   the edit, compare after, and state the result explicitly — coefficients,
   intercept, scaler, keys added / changed / removed, and at least one prediction
   verified unchanged.
4. **Explicit confirmation before the file is opened.** Flag it as an exception,
   say what will be added and why application code cannot carry it, and wait. The
   `band_coverage` change followed exactly this sequence: the figure was computed
   read-only first, so the decision to proceed was made with the number already in
   hand.

#### What this is not

This does **not** license re-running `train_final.py` or `cluster.py` to "refresh"
an artefact, re-tune a hyperparameter, or improve a score. Those remain forbidden
by §0 without exception. The distinction is that an extension **adds a fact that
was already true but unrecorded**; a refresh **changes what the artefact asserts**.

If a proposed change would move any number that is already stored, it is not an
extension.

#### Precedents

Three, all following this pattern:

| Change | Missing figure | Why application code could not carry it |
|---|---|---|
| **02** `oof_predictions.csv` | Held-out forecasts | Computing them per request is forbidden outright (§2.1) |
| **03** `rival_cluster`, `rival_cluster_name`, `distance_to_rival` | Which cluster an assignment was close *to* | A consumer could see an assignment was close but not to what — the more useful half |
| **01** `band_coverage` | How often the ×1.75 band actually contains the value | Recomputing invites approximation; the in-sample/out-of-fold choice must travel with the data, not be made by whoever renders it |

Each was requested, confirmed, and verified before the file was touched. Follow the
same sequence.

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

## 3. Presentation rules

Formalised from DESIGN.md §8, for the **ink-on-paper** system: one world at two
densities, broadsheet for the landing page and blueprint for the tools. Each rule
below is checkable, and the check is the point — a rule nobody can test is a
preference.

**This section was rewritten for the redesign. §2 above was not**, and is
byte-identical to what it was before: model and data integrity is not a
presentation concern and was explicitly out of the redesign's scope.

### 3.1 The rules

| # | Rule | Check |
|---|---|---|
| V1 | **No hue on a data mark.** Confidence is ink density (`--signal-0..3`). The one accent annotates and never fills. | `--accent` must not appear in `components/marks/` |
| V2 | **No red for a weak reading.** Weak is the instrument working correctly; red says broken. | No red value anywhere in the signal ramp |
| V3 | **No warning box where a mark would do.** | If it can be drawn on a rule, it must not be a callout |
| V4 | **One sentence beside a mark, then a disclosure.** No paragraphs inline. | Finding text ≤ ~2 lines; the rest behind `<Disclosure>` |
| V5 | **Probability segments are fixed H·D·A** — never sorted, and **never shaded by magnitude**. | Segment order is a constant, not derived; segments must not read `--signal-*` |
| V6 | **Market value uses a log scale.** | A linear scale on the value rule is a bug |
| V7 | **All figures use tabular numerals.** | `font-variant-numeric: tabular-nums` on every number |
| V8 | **One rail height across all tools** (`--rail-h`). | Marks must not set their own height |
| V9 | **No claim of skill from a single case.** | Copy must not imply one correct forecast is evidence |
| V10 | **Only two font weights**, 400 and 600. | No 300/500/700/800 |
| V11 | **No kicker or eyebrow above a heading.** | No label element immediately preceding an `<h1>`/`<h2>` |
| V12 | **No coloured border-left or border-right above 1px** on a card, list item, callout or alert. | `border-left`/`border-right` > 1px with a non-rule colour |
| V13 | **One container is not the page structure.** No single `Panel` serving controls, results, errors and content alike; **nested panels are always wrong**. | A panel component rendered inside another panel |
| V14 | **No gradient, glow, neon or drop-shadow on a mark.** Depth comes from contrast, not shadow. | `gradient`/`box-shadow`/`filter` inside `components/marks/` |
| V15 | **No dark mode in v1.** Paper is the metaphor; "dark paper" is a contradiction. | No `prefers-color-scheme: dark` block, no `[data-theme]` |
| V16 | **Radius is 2px.** Printed rules meet at corners. | No `border-radius` above `--radius` outside the accent stamp |

`§2.4` (never invent cluster names) and `§2.5` (position is display-only) are model
integrity rules and live in §2. They are not restated here, because a duplicated
rule drifts from its original.

### 3.2 Why the confidence ramp is not a colour scale

The previous system spent seven hues: three tool accents plus a four-state
green/amber/red scale. The redesign spends one.

This is not austerity. Confidence here is **ordinal** — contested → borderline →
clear is one dimension with an order — and hue is the channel for *categorical*
data. Ordered data belongs on a lightness ramp. Encoding an ordinal quantity as
three hues cost three channels to say one thing, and it put alarm-red on the
states where the model is being most honest: a contested assignment is the
clustering correctly reporting weak structure, and an actual outside the band is
the ×1.75 band behaving exactly as documented on two players in five.

**An agent tempted to reintroduce colour "for scannability" should read that
paragraph again.** A dashboard uses hue to make one state findable in a grid of
many. This site shows one reading at a time, at size, with a sentence beside it.
It never had the problem hue solves.

### 3.3 The one place the ramp must not go

Project 02's Home / Draw / Away are **categorical, not ordinal**. Shading them by
weight implies a ranking the model never stated, which is the same misreading V5
prevents in the spatial channel. They are distinguished by **fill texture** —
solid, hatched, open — each labelled.

A segment that reads from `--signal-*` is a V5 violation even when the order is
correct.

### 3.4 Additional prohibitions

- No counters animating up to their value. The number is a measurement, not a
  reveal.
- No scroll-triggered animation, parallax, or 3D.
- **No motion on a mark's geometry.** A band that grows or a needle that travels
  reads as an instrument still making up its mind. Chrome may move; marks do not.
- No tooltips as the *only* home for a caveat. Anything essential must be visible
  or behind an explicit disclosure, never behind hover — hover does not exist on
  touch and is invisible to a screen reader. This one is a confirmed product
  commitment in PRODUCT.md, not a preference.
- No real player photographs (licensing). Club crests are permitted and are a
  recorded product decision; generative per-player graphics are built from real
  per-90 data.
- **No formal accessibility conformance claim** — not in copy, not in a commit
  message, not in a report. PRODUCT.md holds that target open for the whole
  redesign. An audit finding is evidence, not certification.
- Everything in §3.4 must honour `prefers-reduced-motion`.

### 3.5 Density is a decision, not a default

Two densities exist and they are not interchangeable. Broadsheet is for the
landing page only; blueprint is for the three tools and the methodology page.
Applying broadsheet's display sizes and air to a tool page costs the scanability
those pages exist for, and applying blueprint's density to the landing page throws
away the voice that page needs. Neither is "the safe one".

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
4. **Is this a refusal / no-data state?** → An **em-dash** where the figure would
   be, an empty trough showing the calibrated span, and the input's position
   outside it. No red, no triangle, no box (§3 V2, §4).
5. **Am I about to add a colour?** → Almost certainly no. Confidence is ink
   density (`--signal-0..3`); the single accent annotates and never fills a mark
   (§3 V1, and read §3.2 before arguing).
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
grep -rn --include="*.py" -E "\.predict_proba\s*\(" backend/ | grep -v "/tests/" && echo "VIOLATION of 2.1" || echo "OOF constraint intact"
```

Three details in that command are load-bearing, and the first version of it
had none of them — it reported a violation against a compliant backend.

- **`\.predict_proba\s*\(` rather than the bare word.** The bare word matches
  §2.1's own prohibition text. `match.py` opens with a docstring saying it must
  never call `predict_proba`, and that sentence tripped the check.
- **`--include="*.py"`.** Otherwise `__pycache__/*.pyc` matches, because
  compiled bytecode carries the docstring.
- **`grep -v "/tests/"`.** The constraint test names the thing it forbids.

A check that fires on its own rationale is worse than no check: the cheapest
way to make it pass is to delete the explanation. `backend/tests/`
`test_constraints.py` makes the same check properly, stripping docstrings and
comments with `ast` before searching, and should be preferred over the grep
where it can be run.

### 7.1 Every grep-based check must strip prose before matching

**A check that searches source for a forbidden token will otherwise fire on the
comment explaining the prohibition.** Strip comments and docstrings first — with
`ast` for Python, a comment-stripping pass for TS/JS — or scope the pattern
tightly enough that prose cannot match it.

This has now happened three separate times in this repository:

| Check | Fired on |
|---|---|
| §7's own `predict_proba` grep | `match.py`'s docstring stating it must never call `predict_proba` |
| `backend/tests/test_constraints.py` | Comments in `match.py`, `artefacts.py`, `value.py` — every hit prose |
| Frontend figure-drift grep (`0\.10\|0\.50\|900\|1\.75`) | `ZonedAxis.tsx`'s docstring stating the component must not contain those literals |

Each reported a violation against compliant code. The failure mode is worse than
a false positive, because the quickest way to make the check pass is to delete
the sentence that says why the rule exists — from the file a developer reads
before touching that code. A rule enforced by a check that punishes its own
documentation will end up undocumented.

### 7.2 Windows: two traps that cost real time

- **`pkill` silently does nothing.** Killing the backend to reload a changed
  schema appeared to succeed while the stale process kept serving the old
  `/openapi.json`. Use `netstat -ano | grep ':8000\s'` to find the PID, then
  `taskkill //PID <pid> //F` (double slashes under Git Bash).
- **A schema change needs a genuine restart.** FastAPI builds `/openapi.json`
  once at startup, so an edit to `schemas.py` stays invisible until the process
  actually dies. Confirm the reload landed —
  `curl -s localhost:8000/openapi.json | grep <NewModel>` — rather than assuming
  it did.

Related, in `frontend/vite.config.ts`: Vite binds `localhost`, which Node 17+
resolves to `::1`, so the dev server listens on IPv6 only. Browsers are
unaffected; `curl http://127.0.0.1:5173` fails while `curl http://localhost:5173`
succeeds.

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
