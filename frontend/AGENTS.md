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

