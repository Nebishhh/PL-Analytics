# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primary: hiring managers and recruiters**, evaluating the author as a candidate.
They arrive from a CV or GitHub link, are time-boxed, and are deciding whether the
engineering judgement here is real. What must be legible to them quickly: the
leakage audits, the out-of-fold serving constraint, the refusal states, and the
discipline visible in the repository's own history.

**Secondary: football data enthusiasts**, who came to use the tools on players and
fixtures they care about.

The ordering decides what leads, not who is served. Credibility leads; hands-on
tool use is immediately available after it and is never gated behind reading
anything first. Both audiences reach the tools.

## Product Purpose

Three machine-learning models over Premier League data, each exposed as a tool that
states what it can and cannot do:

| Tool | Technique | What it outputs |
|---|---|---|
| Value | Linear regression | A market-value range with a stated tolerance, or a refusal |
| Match | Classification (HistGradientBoosting, balanced) | A three-way Win/Draw/Loss distribution, or an out-of-scope state |
| Style | K-Means, k=4 | A cluster assignment with a confidence tier and a margin to the rival |

Success is a visitor correctly understanding how much to trust each reading —
including the cases where the honest answer is that there is no reading.

## Positioning

**The models state their own limits, and the interface is built so they cannot
stop doing so.**

The distinguishing claim is not accuracy; the accuracy is modest and openly
reported. It is that the honesty is structural rather than a matter of
discipline — enforced by the architecture and by executable checks, not by a
promise. A neighbouring project could copy the models in an afternoon and could
not truthfully copy this:

- Project 02 serves **stored out-of-fold predictions only**. Calling
  `predict_proba` on a match the model trained on would report ~0.98 accuracy
  against a real ~0.47. The serving path makes that misrepresentation
  impossible, and a test asserts it.
- Project 01 **refuses** below its calibrated range rather than extrapolating —
  163 of 661 players. An earlier version, unrefused, priced a 38-minute player in
  the hundreds of billions of euros.
- Project 03 reports that its clustering is **least trustworthy exactly where it
  is most interesting**: the best-separated clusters are the ones that merely
  restate position.
- Every quality figure is read from the trained artefact at request time, so the
  interface cannot drift from the models that produced it.

## Operating Context

Evaluated in a browser, most often desktop, in a single short session. A recruiter
may never scroll past the first screen; an enthusiast may sit with one tool for
some time. Nothing requires an account, and there is no persisted user state.

The site is a read-only surface over three already-trained artefacts. No model is
fitted at request time and no user input changes any stored data.

## Capabilities and Constraints

**Confirmed functionality**
- Three tool surfaces (Value, Match, Style) plus a methodology page, over a
  read-only FastAPI backend serving three `model.joblib` artefacts and their
  derived CSVs.
- Value: 661 players listed, 498 modelled, 163 refused below a 900-minute floor.
  Reports R² and a ×1.75 typical-error band whose coverage is stated out of fold.
- Match: 2,967 of 4,616 fixtures have a held-out forecast. The remainder render an
  explicit out-of-scope state rather than a fabricated even split.
- Style: 315 outfield players, k=4. Per-player confidence tier, margin to the
  nearest rival cluster, and a separate negative-silhouette signal.

**Hard constraints future work must preserve**
- Never compute a project-02 forecast at request time.
- Never hardcode a model quality figure anywhere in the interface.
- Cluster names come from the artefact, which generates them mechanically; no
  invented archetype language.
- Position was held out of the clustering and is shown for context only.
- Refusal and out-of-scope are first-class product states, not error states.
- Raw data and the three artefacts are read-only. The existing Streamlit apps and
  project code remain untouched as working references.

**Terminology**
"Out-of-fold", "calibrated range", "typical-error band", "margin", "silhouette",
"position-adjacent" all carry specific meanings defined by the models; they are not
interchangeable with looser synonyms.

## Brand Commitments

- Name: **PL-Analytics**. Author: Nebiyou Essayas Dessalegn.
- **Club crest artwork will be used** alongside generative per-player graphics on
  the public site. Recorded as a decision the user made explicitly and separately
  from the deployment question: the trademark consideration is accepted for a
  personal portfolio at this scale. This is a confirmed instruction, not an
  oversight to be revisited.
- **No real player photographs**, on licensing grounds.
- Voice: plain, specific, and unhedged about limitations. The caveats are the
  product and are never trimmed to reduce visual noise.

## Evidence on Hand

Real, in the repository, and usable without fabrication:
- Three trained artefacts carrying every quality figure the interface quotes.
- 13 committed plot PNGs (`01-value-predictor/plots/`, `02-`, `03-`), already
  served over a `/plots` route — the evidence the README's claims rest on.
- A README with the full methodology, including the three-model comparison tables
  and the reasoning for shipping the less accurate classifier.
- `AGENTS.md`, carrying the enforceable constraints, and 33 executable constraint
  checks that assert them.
- A commit history recording the failures that shaped the models: the €981bn
  prediction, the rank-deficient design matrix, the unstable sort that moved the
  headline R², the position-adjacency metric that was computed wrongly and caught
  before shipping.

**Absences that must not be filled with invention:** no testimonials, no users, no
customers, no benchmarks against other products, no traffic or uptime claims, no
live prediction capability, and no player photography.

## Product Principles

1. **Credibility leads, access is never gated.** The recruiter-first ordering
   governs sequence only; a visitor can reach any tool immediately.
2. **Every figure traces to an artefact.** If a number appears on screen, it was
   read from `model.joblib` at request time, not typed into a component.
3. **Refusal is a reading.** An instrument that shows its operating limits is more
   trustworthy than one that always answers, and refusal is styled as a state, not
   an error or a warning.
4. **The caveats are the product.** An interface optimised for cleanliness will be
   tempted to trim them; that trade is not available.
5. **Additive only.** The three Streamlit apps, the project code, and the artefacts
   are references that keep working. New surfaces are added beside them.

## Accessibility & Inclusion

No formal standard has been set as a product requirement. One product-specific
constraint is confirmed and load-bearing: **no caveat may live only in a tooltip or
hover state** — hover does not exist on touch and is invisible to a screen reader,
and anything essential must be visible or behind an explicit disclosure. Every mark
carries a text equivalent stating its reading.

**Open decision, and it stays open.** Whether a specific conformance target
(e.g. WCAG 2.1 AA) is adopted is undecided, and it remains undecided for the
duration of the current redesign. No step of that redesign may state or imply a
formal conformance level — not the build, and not the critique, audit or polish
passes that end it.

This is a rule about claims, not about effort. Accessibility work should happen;
asserting a standard has been met should not, because nothing here has tested
that. **An audit finding is not a conformance claim.** A tool reporting no
accessibility violations is evidence, not certification, and its output must not
be restated as "WCAG 2.1 AA compliant" or any equivalent. Only a real audit
against the standard can license that sentence, and none has been run.

Distinct from the above, and not weakened by it: the **no caveat may live only in
a tooltip or hover state** rule is a confirmed, tested commitment that binds every
step. It is a product constraint, not a conformance level, and satisfying it says
nothing about whether any standard is met.
