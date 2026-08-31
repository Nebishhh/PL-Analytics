# getdesign.md — Step 1: Research / Taste (redesign)

Supersedes [archive/getdesign-2026-08-30.md](archive/getdesign-2026-08-30.md),
which is kept because two of its findings survive intact and are cited below.

**No code, no tokens, no chosen direction yet.** This records what was looked at,
what was measured, and which directions survive a test the previous round did not
apply.

---

## 0. Method, and what changed since the last round

Every screenshot here was taken with **Playwright at 1440×900, deviceScaleFactor 2**,
written to disk as a real file. The previous round's visual calls were made through
the in-app browser pane, which composites at roughly one third regardless of
viewport, clamps to a 448px floor, and cannot crop a region. That capped how
confidently type could be judged: the four-triad specimen had to be rebuilt twice
and was still unreadable, and the serif comparison only became legible when set at
76px. Playwright removes that constraint — the Refero gallery capture below is
2880×7850 and fully legible.

| Source | Access | What it gave |
|---|---|---|
| styles.refero.design | **Open.** No login wall, `/style/{uuid}` pages reachable | Extracted palettes and type scales for 5 systems |
| Awwwards | Open | Sites of the Day, browsed broadly rather than by category |
| Impeccable `craft-floor.md` | Local, installed Step 0 | A saturated-defaults list that indicts two things in the current build |
| Previous getdesign.md | Archived | Two findings carried forward; see §4 |

Refero's main site was login-gated in the previous round and was skipped rather
than guessed at. **The `styles.` subdomain is not gated** — that was verified, not
assumed.

---

## 1. The gating test: four uncertainty shapes

This is the change from the previous round, which ranked directions on how well
they carried uncertainty *in general* and let a striking direction through with a
noted risk. That is not strong enough. Every one of these three models outputs a
different shape of uncertainty, and a direction that cannot carry all four
honestly is **disqualified, not flagged**.

| | Shape | Where it comes from | What it must show |
|---|---|---|---|
| **a** | Range with a tolerance | 01 value | A point, a band around it whose width is a *typical miss* rather than a bound, on a log scale, plus where the actual value fell |
| **b** | Three-way probability distribution | 02 match | H·D·A in fixed order, never sorted, against a base rate that shows how small the model's edge is |
| **c** | Discrete tier + continuous margin | 03 style | A confidence tier, the continuous margin behind it, printed thresholds, and a *second independent* signal (negative silhouette) that a tier alone would hide |
| **d** | Refusal / no answer | 01 below its floor, 02 out of scope | That the instrument has a limit and this input is outside it — as a **state**, not an error, and not an alarm |

**(d) is the one that kills directions.** Most visual systems have a rich
vocabulary for success and a single vocabulary for failure — red, a warning
triangle, an alert box. This product refuses 163 of 661 players and has no forecast
for 1,649 of 4,616 matches. Refusal is roughly a quarter of everything the site
says. A system that can only express it as an error is unusable here.

---

## 2. Refero: five systems, real tokens

Palettes and scales read from the style pages directly, not from thumbnails.

**Linear** — *"midnight precision instrument."* Canvas `#08090a`, one acid-lime
`#e4f222` used sparingly as "a functional flashlight," hairline **0.5px** borders,
weights in a low **400–510** band rather than bold, tracking −0.022em, 6/12px radii.
Its stated principle: *darkness as a substrate rather than a theme.*

**Miranda** — *"old-world broadsheet on warm cream."* Parchment `#e2dedb`, ink
`#1d1d1b`, one ember orange `#c03f13` "like a hand-stamped seal." Display serifs at
enormous sizes with sub-1.0 line-heights. **Components flat and borderless; depth
comes from contrast, not shadow.**

**Programa** — *"Swiss design studio at high noon."* Near-white, four greys, one
highlighter yellow `#fbff2b`. Its line is the most useful sentence found in this
round: **"chromatic real estate is rationed, not distributed."**

**shadcn/ui** — *"clinical blueprint on frosted paper."* Achromatic; a single red
`#e7000b` **reserved for destructive states and nothing else**. Reads as developer
infrastructure rather than consumer product.

**LaunchDarkly** — *"neon control room."* Charcoal, a violet→blue gradient as the
brand's "electronic pulse," **elevation communicated through glow rather than
shadow**, 30–60px pill radii.

### The pattern across all five

Every one rations colour to a single chromatic voice against a neutral field. None
of them distributes hue. That converges with what this project already needs for a
different reason — a mark's colour must mean confidence and nothing else — and it
sharpens the requirement: **the semantic scale is the exception that must be
argued for, not the default.** Three semantic colours plus a null is already more
chromatic vocabulary than any of these five systems spends in total.

---

## 3. Awwwards, browsed broadly

Sites of the Day, across categories rather than filtered to data or sport. The
winners are overwhelmingly **spectacle**: cinematic video heroes (Hobro Digital),
retro-maximalist collage (index), dark 3D product worlds (Sharplink), photographic
narrative (Merci Michel), oversized pixel display type.

Two exceptions are relevant here:

- **++hellohello, "AI in Design Report 2026"** — an editorial report: modular grid,
  mixed image blocks, monospace annotation, a dotted halftone frame. This is what a
  *document* looks like when it is designed rather than templated.
- **Sharplink** — topographic contour lines as the ground. Contours encode a
  continuous field, which is structurally the same problem as showing a margin or a
  distribution.

The previous round's measured finding survives and is worth restating, because it
is the only quantitative evidence in either round about this exact trade: on the
same jury, the WebGL spectacle World Cup piece scored **6.30 / 6.00 / 7.00 / 7.20 /
7.90** while the clean, minimal one scored **8.00 / 7.70 / 9.00 / 8.00 / 6.00** —
losing only on creativity. Spectacle did not win here even on a subject built for
it.

---

## 4. Carried forward from the archived round

Two findings still hold and are not re-derived:

1. **The grotesk + serif + mono triad is the right structure** — evidenced by the
   *Inside Youth Basketball 2025* report's Focal / ABC Marist / VCR OSD Mono. Which
   specific faces fill it is reopened entirely in Step 4; nothing carries over.
2. **Mono is load-bearing, not decorative.** Tabular figures that align down a
   column are the difference between a comparison you can scan and one you read
   twice. Impeccable's craft floor independently warns against *"monospace as a
   costume for 'technical' rather than for code, data, or measurement"* — here it
   is measurement, so it is earned rather than borrowed.

---

## 5. What the craft floor says about the current build

Impeccable's saturated-defaults list names two things this build currently does.
Recorded now so the redesign does not carry them forward:

- **"A colored `border-left` or `border-right` above 1px on cards, list items,
  callouts, or alerts."** The `/about` page's "What it cannot do" block is a
  `2px solid var(--state-low)` left border. It is the exact pattern.
- **"Same-size cards of icon plus heading plus text as the page structure. Cards
  are the lazy container; nested cards are always wrong."** The current system has
  one container, `Panel`, used for controls, results, errors and licensing alike,
  and `/about` nests content inside it.

Two others it warns about are *earned* here rather than borrowed, and the new
direction should keep them: mono for real measurement, and rails that are content
rather than sparklines standing in for content.

One is a hard ban worth adopting verbatim: **no kicker or eyebrow above a
heading.**

---

## 6. Directions, each tested against all four shapes

A direction passes only if it carries **a, b, c and d** honestly.

### Direction 1 — Midnight precision instrument
*Linear-adjacent. Near-black substrate, hairline borders, rationed accent.*

| a | b | c | d |
|---|---|---|---|
| ✅ band on a dark rail | ✅ split rail | ✅ zoned axis | ✅ neutral grey null |

**Passes — and is disqualified for a different reason.** This is what the site
already is. As the outcome of a redesign it would mean the redesign did not happen.
It stays here as the control: any direction that wins must beat it on something
other than novelty.

### Direction 2 — Editorial broadsheet
*Miranda / ++hellohello adjacent. Warm ground, ink, one stamped accent, large
display serif, flat and borderless, newspaper grid.*

| a | b | c | d |
|---|---|---|---|
| ✅ error bars are native to print charts | ✅ stacked column, fixed order | ✅ printed axis with labelled thresholds | ✅ **strongest of any direction** |

**Passes, strongly.** Shape (d) is where it wins: newspapers and statistical
abstracts have a centuries-old convention for *no data* — an em-dash in the cell, a
footnote, a break in the rule. It is neutral, unalarming, and instantly legible as
"nothing here," which is exactly what a refusal is. No other direction has an
inherited vocabulary for absence.

Risk to carry into Step 2: a warm parchment ground plus large serif can tip into
pastiche, and the tool pages are Operate/Read surfaces where that would cost
scanability.

### Direction 3 — Clinical blueprint / technical drawing
*shadcn + Programa adjacent. Near-white, hairline 1px, Swiss grid, rationed signal.*

| a | b | c | d |
|---|---|---|---|
| ✅ dimension line with tolerance is literally this drawing convention | ✅ proportional bar | ✅ a gauge face with printed zones | ✅ "outside calibrated range" is a drafting convention |

**Passes.** Shape (a) is unusually well served: engineering drawings annotate a
dimension *with its tolerance* as a matter of course, which is precisely what the
×1.75 band is. Light ground is also a genuine departure from the incumbent.

Risk: a near-white field gives the semantic scale less room to separate than a dark
one does, and three states plus a null must stay distinguishable.

### Direction 4 — Neon control room
*LaunchDarkly adjacent. Charcoal, gradient brand voice, glow elevation.*

| a | b | c | d |
|---|---|---|---|
| ⚠️ | ✅ | ✅ | ❌ |

**Disqualified**, on (d) primarily. A neon cockpit's vocabulary for "no reading" is
an alarm, and refusal here is correct behaviour rather than a fault — styling it as
an alert misrepresents the product's best feature. Two structural conflicts
compound it: a gradient on a mark encodes a value that does not exist, and glow as
the elevation system puts a broadcast-graphic sheen on instruments that must read
as measurement.

### Direction 5 — Spectacle / expressive
*The Awwwards SOTD majority. Video heroes, 3D, maximalist collage.*

| a | b | c | d |
|---|---|---|---|
| ⚠️ | ⚠️ | ❌ | ❌ |

**Disqualified.** It has no vocabulary for (d) that is not an error screen, and (c)
requires showing two independent weak signals at once, which a spectacle system
resolves by picking the more dramatic one. The jury scores in §3 also say it would
not even win on its own terms.

---

## 7. Where this leaves Step 2

Two directions survive on merit — **Editorial broadsheet (2)** and **Clinical
blueprint (3)** — with **Midnight instrument (1)** as the incumbent control.

They are not equally suited to every surface, and the modes recorded in PRODUCT.md
already split the site: the landing page is **Persuade**, the three tools and the
methodology page are **Operate/Read**. Direction 2's strength is voice and its
inherited vocabulary for absence; Direction 3's strength is precision and
scanability. Whether the answer is one direction throughout, or a single world with
different density on Persuade versus Operate surfaces, is Step 2's decision and is
deliberately left open here.

**Not decided in this step**, and not to be inferred from it: palette values, type
scale, spacing, specific typefaces (Step 4 reopens these with no carry-over from
Newsreader or IBM Plex), component inventory, or page composition.

---

## 8. Evidence on disk

Captures from this round, at true resolution:

- `refero-gallery.png` — 2880×7850, the full gallery
- `awwwards-sotd.png` — 2880×2800, Sites of the Day

Both were taken with `frontend/scripts/shoot.mjs`, which is committed so any figure
here can be re-captured rather than taken on trust.
