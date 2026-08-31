# DESIGN.md — Step 2: Visual system

**Direction D (instrument panel)** as the primary visual system, borrowing
**Direction B's prose-adjacency discipline** for how findings sit next to marks.

Three tools under one shell. No comparison view in v1. Faithful port of the three
existing Streamlit apps' functionality — no new scope.

**Still no implementation code.** This is the system and three reference screens.

---

## 0. The governing idea

Every one of the three projects outputs a **measurement with a stated tolerance**.
That is the whole system:

| Tool | What it outputs | Instrument reading |
|---|---|---|
| 01 value | Point estimate + ×1.75 band | Needle inside a tolerance band on a log scale |
| 01 value (refusal) | *No answer* below 900 min | Input outside the instrument's calibrated range |
| 02 match | 3-way probability distribution | Proportional split of a fixed 100% rail |
| 03 style | Cluster + margin to rival | Needle on a separation axis with threshold zones printed on it |

**The rule that makes this coherent: uncertainty is drawn on a rail, never written
in a box.** A yellow warning box is a scolding. A visibly wide band is information.
Same honesty, no wagging finger — and it does not accumulate into a wall.

**The second rule, from Direction B:** every mark is followed by *one sentence*, not
a paragraph. The paragraph goes behind a disclosure. This is the pattern the
project-03 restructure arrived at empirically last session, generalised to all three
tools.

**The third rule, and the one that keeps the system from lying:** an instrument that
shows its own operating limits is more trustworthy than one that always answers.
Refusal is a first-class reading, styled as a *state*, not an error.

---

## 1. Colour tokens

Dark ground. Not the Streamlit apps' saturated PL purple — that reads as brand.
Instrument panels want a neutral ground so the marks carry all the colour.

### Ground and ink

```
--ink-900   #0A0D13   page ground
--ink-850   #0F131B   raised panel
--ink-800   #151A24   card / rail trough
--ink-700   #1E2431   hairline, rail border
--ink-600   #2A3140   divider, inactive tick
--ink-400   #5B6478   disabled / annotation
--ink-300   #8892A6   secondary text, axis labels
--ink-200   #B8C0D0   body text
--ink-100   #E8ECF4   primary text, measured values
```

### Semantic scale — meaning, never decoration

These three are the **only** colours permitted on a data mark. They encode
confidence and nothing else.

```
--state-clear     #3DDC97   well separated / inside band / high margin
--state-moderate  #E8B84B   borderline
--state-low       #E5484D   contested / outside band
--state-null      #5B6478   REFUSAL — deliberately neutral grey
```

**`--state-null` must never be red.** Refusal is the instrument working correctly.
Colouring it as an error teaches the reader that "no answer" is a failure, when in
this project it is the single most honest thing the system does.

### Tool accents — wayfinding only

Three tools under one shell need distinguishing, but hue must not compete with the
semantic scale.

```
--tool-01  #D9A441   value predictor    (gold — money)
--tool-02  #4CC2E0   match predictor    (cyan)
--tool-03  #A98BD9   style finder       (violet)
```

**Constraint: tool accents appear only in the shell** — active nav item, the 2px
rule under the tool header, the tool's index card. **Never on a data mark.** Hue
carries navigation; the semantic scale carries meaning. If a chart ever renders in
gold, the system has been violated.

### Band and rail fills

```
--band-fill      currentColor @ 18%    the tolerance band itself
--band-edge      currentColor @ 45%    band boundary
--rail-trough    --ink-800             unfilled rail
--hatch          repeating 45° 2px --ink-600 on --ink-850   out-of-range
```

---

## 2. Typography

**IBM Plex**, all three cuts. One superfamily, free, and designed for a technology
company's data contexts — it reads as measurement without tipping into
terminal-cosplay.

```
--font-ui     "IBM Plex Sans"    UI, labels, navigation
--font-mono   "IBM Plex Mono"    every figure, axis tick, table cell
--font-prose  "IBM Plex Serif"   findings prose only
```

This mirrors the one genuinely comparable artefact found in research — the *Inside
Youth Basketball 2025* report's **Focal / ABC Marist / VCR OSD Mono** triad. Grotesk
for interface, serif for argument, mono for data.

**The mono is load-bearing, not stylistic.** Every figure in this app gets
`font-variant-numeric: tabular-nums`. Digits that align down a column are the
difference between a scannable comparison and one you have to read twice.

**The serif is also load-bearing.** It is reserved *exclusively* for the
one-sentence finding beside each mark, and for expander prose. That gives the
project's actual claims — "learned home advantage, learned nothing about draws" — a
different voice from the chrome around them. A reader can tell at a glance which
text is an assertion about the model and which is a label.

### Scale

Tight at the bottom for density, wide jumps at the top for the measured value.

```
--t-micro    11px / 1.3    axis ticks, scale endpoints          mono
--t-label    12px / 1.2    metric labels, UPPERCASE, 0.06em     ui
--t-body     14px / 1.5    interface body                       ui
--t-prose    16px / 1.6    findings sentence, expander prose    serif
--t-figure   20px / 1.3    inline figures, table values         mono
--t-value    30px / 1.1    the primary measured value           mono
--t-display  38px / 1.15   tool title                           ui, 600
```

Only two weights: **400** and **600**. Instrument panels do not need a weight ramp;
they need contrast between label and value, which the scale already provides.

---

## 3. Spacing and the instrument metrics

4px base grid.

```
--s-1  4px    --s-2  8px    --s-3  12px   --s-4  16px
--s-5  24px   --s-6  32px   --s-7  48px   --s-8  64px
```

Instrument-specific tokens — these are what make rails consistent across three
tools that are otherwise showing different things:

```
--rail-h        44px    height of a scale rail
--rail-radius   6px
--rail-inset    12px    left/right padding inside a rail's container
--tick-w        2px     a needle or reference tick
--tick-over     8px     how far a needle overshoots the rail vertically
--zone-label-h  18px    the strip under a rail carrying zone names
--mark-dot      10px    the "actual value" dot
```

**One rail height everywhere.** A value band, a probability split and a separation
axis are different statistics, but if they render at different heights the reader
reads them as different *kinds* of object. Same rail, same height, same radius —
that is what makes three tools feel like one instrument.

---

## 4. The four uncertainty marks

### 4.1 Band on a scale — project 01

Log-scale rail (values span €100K–€200M; linear would compress everything below
€20M into nothing). Tolerance band drawn as a filled region. Needle at the point
estimate. **Actual value as a visually distinct mark** — a dot, not a needle, so
prediction and reality are never confused.

Inside/outside is geometric. The reader sees it before reading a word.

### 4.2 Proportional split — project 02

A fixed 100% rail divided into three segments. Because the three probabilities sum
to 1, the rail is *full* by definition — which correctly communicates "this is a
distribution", not "this is a score out of 100".

**With a base-rate tick.** A small inverted tick at 44.6% marks the always-guess-home
baseline. This is the single most honest mark in the system: it lets a reader see
whether the model is actually saying anything beyond the base rate, on every
individual forecast. No text can do that as efficiently.

### 4.3 Needle on a zoned axis — project 03

Separation axis 0 → 2.74 (observed max margin). **The confidence thresholds are
printed on the axis itself** as zones: `0–0.10 CONTESTED`, `0.10–0.50 BORDERLINE`,
`0.50+ CLEAR`. The needle lands in a zone.

This is the purest instrument idiom in the system — a gauge with a red zone. Lewis
Hall's 0.042 sits visibly inside the red band; no sentence needed to establish that
the reading is marginal.

Negative silhouette is a **separate secondary mark**, because it is a different
failure mode from a narrow margin and only 4 of 19 players trip both.

### 4.4 Out of calibrated range — refusal, project 01

The one that most systems get wrong.

- Value rail renders **hatched and empty** — no band, no needle. There is no reading.
- A **second rail appears below it**: the input domain, 900 → 32,861 minutes, with
  the player's position marked *outside* the left edge.
- Colour is `--state-null` grey, never red.
- The label reads **"not calibrated for this player"**, not "error" or "unavailable".

The instrument shows its own operating limits and where this input fell relative to
them. That is a stronger honesty signal than any warning copy, and it turns
project 01's refusal from an apology into a demonstration of competence.

---

## 5. The finding pattern (Direction B, generalised)

Every mark is followed by exactly this, in this order:

```
[ MARK ]                          drawn, carries the uncertainty
[ state chip ]                    2–4 words, semantic colour, never a sentence
[ one sentence ]                  serif, the single most important qualification
[ ▸ disclosure ]                  everything else, collapsed
```

Rules:

1. **The chip is never a sentence.** "Contested", "Outside band", "Not calibrated".
2. **The sentence names the alternative first when confidence is low.** From
   project 03: when contested, the rival is named before the assignment, because
   leading with the assignment asserts what the geometry does not support.
3. **Nothing that is drawn is also written.** If the band shows the actual value
   falling outside it, the sentence does not say "the actual value fell outside the
   band" — it says *why*, or *what to do about it*.
4. **At most one disclosure per mark.** Two collapsed panels stacked is a wall of
   warnings wearing a disguise.

---

## 6. Reference screen 1 — Value predictor, normal reading

```
┌──────────────────────────────────────────────────────────────────────┐
│  PL·ANALYTICS        ▸ VALUE      MATCH      STYLE                    │
│  ══════════════                                                       │ ← gold rule
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  MARKET VALUE ESTIMATE                            01 · REGRESSION     │
│                                                                       │
│  William Saliba                                                       │
│  Arsenal FC · Defender (Centre-Back) · 25.4 yrs · 11,492 PL min      │
│                                                                       │
│  ┌─ ESTIMATE ──────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  €33.8M                                                          │  │
│  │                                                                  │  │
│  │   €1M          €10M            €100M                             │  │
│  │   ├─────────────┼───────────────┼──────────────────────────┤     │  │
│  │   ░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░●░░░░░░░░░░░░░░░░     │  │
│  │                 └── ×1.75 band ──┘        ▲                      │  │
│  │                        ▲                  actual €100M           │  │
│  │                     estimate                                     │  │
│  │                                                                  │  │
│  │  ▪ OUTSIDE BAND                                                  │  │
│  │  Elite defenders are a known blind spot — the model prices       │  │
│  │  them almost entirely on goals and assists.                      │  │
│  │                                                                  │  │
│  │  ▸ Why the band is ×1.75 and what it does not mean               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ INPUTS ────────────────────────────────────────────────────────┐  │
│  │  PL MATCHES   PL MINUTES   GOALS   ASSISTS   G/90    A/90       │  │
│  │  131          11,492       7       2         0.05    0.02       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

Notes:

- The band is `--state-low` here because the actual fell outside it; it would be
  `--state-clear` when inside. **The band's own colour is the verdict** — that is
  the drawn-not-written rule doing its job.
- Log scale is non-negotiable. Saliba's €33.8M estimate and €100M actual are one
  band-width apart on a log rail and nearly touching on a linear one.
- The disclosure holds the 59%-coverage caveat, the median-vs-mean note, and the
  smearing warning — all currently in project 01's prose.

### 6b — the refusal state

```
│  ┌─ ESTIMATE ──────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  — not calibrated for this player                                │  │
│  │                                                                  │  │
│  │   €1M          €10M            €100M                             │  │
│  │   ├─────────────┼───────────────┼──────────────────────────┤     │  │
│  │   ▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨●▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨     │  │
│  │                    (no reading)     ▲                            │  │
│  │                                  actual €30M                     │  │
│  │                                                                  │  │
│  │   CALIBRATED RANGE                                               │  │
│  │        900 min ├────────────────────────────────┤ 32,861         │  │
│  │   490 ◄┤▒▒▒▒▒▒▒│                                                 │  │
│  │        ▲                                                         │  │
│  │   this player                                                    │  │
│  │                                                                  │  │
│  │  ▪ BELOW CALIBRATED RANGE                                        │  │
│  │  Under 900 minutes the per-90 inputs stop measuring anything —   │  │
│  │  one shot in three minutes reads as 30 shots per 90.             │  │
│  │                                                                  │  │
│  │  ▸ Why the model refuses rather than extrapolating               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
```

The second rail is the whole idea. All grey, no red. The actual value is still
shown — the app knows it, and hiding it would be its own kind of dishonesty.

---

## 7. Reference screen 2 — Match forecast, distribution + base rate

```
│  MATCH FORECAST                              02 · CLASSIFICATION     │
│                                                                       │
│  Arsenal FC   v   Tottenham Hotspur                                   │
│  23 Nov 2025 · Matchday 12 · forecast by a model trained on 2012–2024 │
│                                                                       │
│  ┌─ FORECAST ──────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │   0%                      50%                            100%    │  │
│  │   ├───────────────────────┼─────────────────────────────────┤    │  │
│  │   ███████████████████████████████▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░    │  │
│  │              HOME 66%            DRAW 18%      AWAY 17%          │  │
│  │                        ╹                                         │  │
│  │                   base rate 45%                                  │  │
│  │                                                                  │  │
│  │  ▪ CORRECT · HOME WIN                                            │  │
│  │  At 66% against a 45% base rate, the model is saying something   │  │
│  │  here — but it finds only one draw in four.                      │  │
│  │                                                                  │  │
│  │  ▸ Accuracy, the baseline, and why draws are the blind spot      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ PRE-MATCH FORM ────────────────────────────────────────────────┐  │
│  │                    ARSENAL          TOTTENHAM                    │  │
│  │  Points/game       2.36             1.64                         │  │
│  │  Position          1                8                            │  │
│  │  Form, last 5      2.60             1.40                         │  │
│  │  Rest days         15               15                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
```

Notes:

- **The base-rate tick is the most important mark in this tool.** Project 02's
  headline finding is that the model beats always-guess-home by only 2.4 points.
  Putting the baseline on every single forecast makes that structural rather than a
  README footnote — the reader can see, per match, whether the model has an opinion
  or is just restating the prior.
- Segment order is fixed **H · D · A** always, never sorted by probability. A rail
  whose segments reorder cannot be compared across matches.
- The state chip reports *outcome correctness*, but the sentence never claims skill
  from one match. One correct forecast at 66% is not evidence.
- The form table is `--font-mono`, tabular, right-aligned — the two columns must be
  diffable by eye since there is no comparison view in v1.

---

## 8. Reference screen 3 — Style finder, zoned axis

```
│  ACTIVITY PROFILE                                03 · CLUSTERING      │
│                                                                       │
│  Lewis Hall                                                           │
│  Newcastle United · DF · 20 yrs · 2,181 PL min                        │
│                                                                       │
│  ┌─ ASSIGNMENT ────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  High tackles won, fouls, yellow cards                           │  │
│  │  ▪ CONTESTED   ▪ SITS WITH ANOTHER CLUSTER   ▫ MIXES POSITIONS   │  │
│  │                                                                  │  │
│  │   SEPARATION FROM NEXT CLUSTER                                   │  │
│  │   0     0.10          0.50                              2.74     │  │
│  │   ├──────┼─────────────┼──────────────────────────────────┤      │  │
│  │   ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░      │  │
│  │   ▲ CONTESTED   BORDERLINE        CLEAR                          │  │
│  │   0.042                                                          │  │
│  │                                                                  │  │
│  │  Nearly as close to "Low involvement" as to the cluster it was   │  │
│  │  assigned — and sits among that cluster's members, not its own.  │  │
│  │                                                                  │  │
│  │  ▸ What margin and silhouette each measure                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ THE TEN RATES THAT PRODUCED IT ────────────────────────────────┐  │
│  │  ATTACKING          DEFENSIVE           DISCIPLINE               │  │
│  │  Goals      0.04    Interceptions 1.20  Fouls        0.70        │  │
│  │  ├─▪──────────┤     ├────────▪──┤       ├──▪────────┤            │  │
│  │  33rd               81st                21st                     │  │
│  │  ...                                                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
```

Notes:

- **Threshold zones printed on the axis** is the move. A reader who never reads a
  word can see the needle is in the red band at the far left.
- Zone boundaries at 0.10 and 0.50 are the actual constants from the app, so the
  drawing and the logic cannot drift.
- The three-badge row is carried over from the project-03 restructure verbatim,
  including that negative silhouette earns its own chip.
- The per-90 table reuses the **same rail** at miniature scale — each rate shown as
  a percentile position rather than a bare number. Same grammar, third context.

---

## 9. Shell

Three tools under one shell, not a narrative.

```
PL·ANALYTICS     ▸ VALUE    MATCH    STYLE                    [about]
════════════
```

- Persistent top bar. Active tool marked by its accent rule.
- Each tool owns its route and its own search/filter controls — ported faithfully
  from the corresponding Streamlit app, including project 01's Club/Position
  filters, project 02's Season/Club chain, project 03's Position filter.
- **An `about` route holds the shared honesty material**: the three headline
  results, what each model cannot do, and the licence split (code MIT, player-scores
  CC0, player-stats MIT). This is where the README's substance lives in the app.
- No cross-tool navigation beyond the top bar in v1. No comparison view.

---

## 10. Motion

Minimal, and only where it aids reading.

- Rails animate their fill **once on data change**, 240ms, ease-out. A band that
  grows to its width reads as a measurement being taken.
- Needles do **not** bounce or overshoot. An instrument that oscillates looks
  uncertain about its own reading, which is precisely the wrong signal — our
  uncertainty is in the *band*, not the needle.
- No scroll-triggered animation, no parallax, no counters ticking up to their value.
  Research finding: the WebGL/spectacle World Cup project scored ~1.5 points below
  the "easy to digest" one on the same jury.
- `prefers-reduced-motion` removes all of it; nothing above carries meaning.

---

## 11. What this system forbids

Recorded so the constraints survive into implementation.

1. **No data mark in a tool accent colour.** Hue is navigation only.
2. **No red on a refusal state.** Refusal is correct behaviour.
3. **No warning box where a mark would do.** If it can be drawn on a rail, it is
   not allowed to be a yellow callout.
4. **No paragraph beside a mark.** One sentence, then a disclosure.
5. **No sorted probability segments.** H·D·A order is fixed.
6. **No linear scale for market value.** Log, or the band is meaningless.
7. **No number without tabular figures.**
8. **No invented archetype language in project 03.** Cluster names come from the
   artefact, which generates them mechanically.
9. **No claim of skill from a single case.** One correct forecast is not evidence,
   and the copy must not imply it is.

---

## 12. Open questions for Step 3

- **Chart rendering:** hand-rolled SVG or a library? The rails are simple enough
  (a trough, a band, ticks) that a library may cost more than it saves, and
  hand-rolled guarantees the four marks share one implementation.
- **Where does the model run?** FastAPI loading the three existing `model.joblib`
  files read-only, or precomputed JSON? Project 02 already ships out-of-fold
  predictions as a CSV precisely because live prediction would misrepresent it —
  that constraint must survive the port.
- **Does `about` need the plots?** The existing `plots/*.png` are committed and
  carry real evidence (k-selection, confusion matrices, the age curve). Reusing them
  is cheap; regenerating them in-browser is not.
