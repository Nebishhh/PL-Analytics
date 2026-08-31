# DESIGN.md — Step 2: Visual system (redesign)

Supersedes [archive/DESIGN-2026-08-30.md](archive/DESIGN-2026-08-30.md).

**One world, two densities.** The world is ink on paper. The landing page is set at
**broadsheet** density; the three tools and the methodology page are set at
**blueprint** density. This follows PRODUCT.md's own split — a recruiter skims
credibility, then uses a tool — rather than forcing one treatment across two
genuinely different jobs.

**Still no implementation code.** Typefaces were chosen in Step 4 and are recorded
in §3.

---

## 0. The governing idea

Every one of the three models produces a **measurement, its tolerance, and
sometimes no measurement at all**. Print has drawn exactly that for two hundred
years: a statistical abstract sets a figure, rules a column, and puts an em-dash
where the number does not exist. Nobody reads that dash as an error.

That is the whole system. **The page is a printed document; the marks are printed
instrument scales; absence is a typographic convention, not an alert.**

Three rules follow, and they are the ones the old system had right:

1. **Uncertainty is drawn, never boxed.** A visibly wide band is information; a
   yellow warning box is a scolding, and boxes accumulate into a wall.
2. **One sentence beside a mark, then a disclosure.** The paragraph goes behind the
   fold, never inline.
3. **Refusal is a reading.** An instrument that shows its operating limits is more
   trustworthy than one that always answers.

---

## 1. The chromatic question, resolved

Step 1 found that all five reference systems ration colour to a single chromatic
voice — Programa's phrasing: *"chromatic real estate is rationed, not
distributed."* The old system spent **seven hues**: three tool accents for
wayfinding plus four semantic states for meaning. That is more chromatic vocabulary
than Linear, Miranda, Programa, shadcn and LaunchDarkly spend **combined**.

The instruction was to argue the scale on its merits or restructure it. The
restructure is available, and it makes the encoding *more* correct rather than
merely cheaper.

### The scale was mis-encoded, independently of any rationing argument

Confidence here is **ordinal**: contested → borderline → clear is one dimension
with an order. The old scale encoded it as **three hues** — green, amber, red.
Hue is the correct channel for *categorical* data; ordered data belongs on a
**value/lightness ramp**. A traffic light is a categorical signal borrowed for an
ordinal quantity, and borrowing it costs three hues to say one thing.

### Red was actively wrong here

The old scale used `#E5484D` for "contested" and "outside band". Those are not
errors. A contested cluster assignment is the clustering **working correctly and
reporting weak structure**; an actual value outside the band is the ×1.75 band
doing exactly what it says on two players in five. Alarm-red states that the
product has failed at the precise moment it is being most honest — which inverts
the thing PRODUCT.md names as the positioning.

The old system already half-knew this. Its own V2 forbade red on a refusal state
for exactly this reason, then used red one step along the same scale.

### What replaces it

**Confidence is drawn in ink density, not hue.** On paper, weight has always
carried emphasis: a heavy rule means more, a light rule means less, a dash means
none. Four states, one ink, no hue:

| State | Encoding | Print analogue |
|---|---|---|
| **Strong** | Full-strength ink | A solid rule |
| **Qualified** | Mid ink | A lighter rule |
| **Weak** | Pale ink + the qualifier mark | A broken rule with a footnote |
| **Absent** | No fill; the trough's own rule, and an em-dash where the figure would be | The em-dash in a statistical abstract |

**One hue survives, and it never touches a mark's geometry.** A single vermilion
does two jobs that are the same job — telling the eye where to look: active
wayfinding (nav, focus) and the **qualifier mark** that annotates a weak reading.
It annotates; it never fills a band, a segment or a needle.

Net: **seven hues to one.** The rationing finding is satisfied, and the ordinal
data is now on the channel it belonged on.

### Where the scale genuinely could not shrink further

Only one surface shows three confidence states at once: project 03's zoned axis,
which prints CONTESTED / BORDERLINE / CLEAR bands simultaneously. There, ink
density is reinforced by **position**, because the axis is ordered left to right —
the two channels agree rather than competing. Everywhere else at most two states
are visible, so the ramp has ample room.

The one place ink density must **not** be used is project 02's distribution. Home,
Draw and Away are **categorical, not ordinal** — shading them by weight would
imply a ranking the model did not state, and V5's "never sorted" rule exists to
prevent exactly that misreading in the spatial channel. They are distinguished by
**fill texture** — solid, hatched, open — the standard monochrome convention for
categories in a printed chart.

### Why this project's requirement still differs from a dashboard's

A typical dashboard uses colour to make a state *findable in a grid of many*. This
site shows **one reading at a time**, at large size, with a sentence beside it. It
does not need colour to locate the state; it needs the state to be *legible and
unalarming* once found. That difference is why a single-ink ramp is sufficient
here and would not be on a monitoring wall.

---

## 2. Colour tokens

Warm paper, not clinical white: the broadsheet ground carries the landing page and
does not glare under the blueprint density.

### Ground and ink

```
--paper-000  #FFFDF9   lifted surface, card face
--paper-100  #F7F4EE   page ground
--paper-200  #EFEBE3   recessed / inset well
--rule-100   #E2DDD3   hairline, rail trough border
--rule-200   #CFC8BA   divider, inactive tick
--ink-300    #766F61   annotation, axis labels
--ink-500    #6B6455   secondary text
--ink-700    #3A352C   body text
--ink-900    #17150F   primary text, display, measured values
```

### The signal ramp — ordinal, one ink

The **only** fills permitted on a data mark. They encode confidence and nothing
else.

```
--signal-3   #17150F   strong      full ink
--signal-2   #6B6455   qualified   mid ink
--signal-1   #B0A899   weak        pale ink
--signal-0   none      absent      no fill; trough rule only
```

### The one hue

```
--accent     #A8341C   vermilion
```

Permitted uses, exhaustively: active navigation, focus ring, the qualifier mark on
a weak or footnoted reading, and the masthead rule. **Never** as the fill of a
band, a segment, a needle, or a zone.

### Dark mode

**Not in v1.** A printed-document world inverts badly — paper is the metaphor, and
"dark paper" is a contradiction the whole system would have to argue with. Recorded
as a deliberate omission, not an oversight.

---

## 3. Type scale

Three registers: **display serif** for voice, **grotesk** for interface, **mono**
for every figure.

### The faces, chosen in Step 4 by measurement

```
--font-display   Fraunces         variable, opsz 9–144, WONK 0
--font-ui        Archivo          400 / 600
--font-mono      IBM Plex Mono    400 / 600
```

All three are **OFL-1.1** and on `@fontsource`. That licence is not a preference:
the repository is public and its font files are redistributed to anyone who clones
it, so anything short of OFL would need a redistribution argument this project
should not have to make.

**Fraunces**, because §3 asks the serif to do two jobs — 92px display *and* the
18px finding — and its optical-size axis is the only mechanism that serves both
honestly. Verified the axis actually does something rather than trusting the
metadata: the `o` measures 175.7 units at `opsz 9` against 145.2 at `opsz 144`, a
21% widening as it moves to text sizes, with contrast flattening to match. Fixed
alternatives failed one end or the other. Instrument Serif has the highest
x-height of the serifs tested (x/cap 0.699) and safe 3.13 contrast, but is a
single-weight display design; Libre Caslon Display has the lowest x-height (0.623)
and 7.67 contrast with no optical compensation, so its hairlines are fragile at
18px.

**Archivo**, for the largest x-height of the grotesks measured (x/cap **0.768**,
against Geist 0.746 and Public Sans 0.712). That difference is spent entirely on
the blueprint density's 12px labels and 14px body, which is where a grotesk in
this system does its actual work. Inter was excluded deliberately: Impeccable's
craft floor names it among the saturated defaults of AI-generated design, and
nothing here needed it.

**IBM Plex Mono**, which re-earned its place on a measurement rather than carrying
over, and for a different reason than it was originally chosen. Every figure on
this site is a measurement, so a mono's real job is making digits unmistakable.
Rendering each glyph and diffing the bitmaps:

| Mono | `0` vs `O` | `1` vs `l` | `l` vs `I` | x/cap |
|---|---|---|---|---|
| **IBM Plex Mono** | **77.1%** | **96.6%** | 42.7% | 0.743 |
| JetBrains Mono | 19.7% | 74.6% | **56.3%** | **0.753** |
| Geist Mono | 32.1% | 40.1% | 30.1% | 0.746 |
| Space Mono | 9.3% | 31.3% | 19.2% | 0.714 |

Plex Mono separates zero from capital O nearly **four times** better than
JetBrains and gives up only 1.3% of x-height for it. **Space Mono is
disqualified**: a 9.3% difference between `0` and `O` is no difference, which is
disqualifying on a surface where every number is a reading.

Set `font-optical-sizing: auto` on Fraunces and pin `WONK 0`; the axis is what
makes one face serve both densities.

### Broadsheet density — landing page

```
--b-display   clamp(40px, 5.4vw, 74px) / 0.95   display serif, the one big statement
--b-lead      clamp(19px, 2.0vw, 24px) / 1.5    the standfirst under it
--b-heading   32px / 1.15                        section heads
--b-body      17px / 1.65                        editorial body
--b-caption   13px / 1.45                        credits, footnotes
```

### Blueprint density — tools and methodology

```
--t-micro     12px / 1.3    axis ticks, scale endpoints          mono
--t-label     12px / 1.2    field labels, UPPERCASE, 0.06em      grotesk
--t-body      14px / 1.5    interface body                       grotesk
--t-finding   18px / 1.5    the one sentence beside a mark       serif
--t-figure    20px / 1.3    inline figures, table cells          mono
--t-value     32px / 1.05   the primary measured value           mono
--t-title     26px / 1.2    tool title                           grotesk
```

**Two weights only: 400 and 600.** An instrument needs contrast between label and
value, which the scale already provides. Carried from the old system because it was
right, and because Linear's own 400–510 band is the same finding.

**Every figure gets `font-variant-numeric: tabular-nums`.** Non-negotiable: digits
that align down a column are the difference between a comparison you can scan and
one you read twice.

---

## 4. Spacing and instrument metrics

4px base.

```
--s-1  4px     --s-5  24px
--s-2  8px     --s-6  32px
--s-3  12px    --s-7  48px
--s-4  16px    --s-8  72px    --s-9 120px  (broadsheet section gaps)
```

```
--rail-h        44px    ONE rail height across all tools
--rail-h-mini   10px    the ten per-rate rails only
--rule-w        1px     hairline; never 2px on a callout edge
--radius        2px     paper does not have rounded corners
```

`--radius: 2px` is a deliberate break from the old 8px cards. Printed rules meet at
corners; the softness of the old system was a SaaS habit, not a decision.

---

## 5. The four marks

Restyled, not re-specified. Each still shows what it showed, and each is tested in
§7.

### 5.1 Tolerance band — project 01
A log-scaled rule. The point estimate is a full-height tick in `--signal-3`; the
band is a `--signal-1` fill between its two ends; the actual value is a vermilion-free
open marker. Band ends are **capped with serifs**, the way an engineering dimension
line is, so the band reads as a stated tolerance rather than a gradient of
plausibility.

### 5.2 Proportional split — project 02
One 100% rule divided H · D · A, **fixed order, never sorted**. Categorical, so
**texture not weight**: Home solid, Draw hatched, Away open, each labelled. The
base rate is a printed tick with its own label above the rule — the number that
shows how small the model's edge actually is.

### 5.3 Zoned axis — project 03
A needle on a separation axis with the thresholds **printed on the axis**, read
from the artefact. Zones are ink-density bands, ordered left to right so density
and position agree. A negative silhouette is a **dagger (†)** against the reading
with its footnote below — print's own convention for "this entry carries an
exception", and structurally exactly what that second signal is.

### 5.4 Out of calibrated range — refusal
The trough is drawn empty: its rule, its endpoints, its calibrated span marked, and
the input's position outside it. Where the figure would be, **an em-dash**. No red,
no triangle, no box. A vermilion qualifier mark and one sentence say why.

---

## 6. Reference screens

### 6.1 Landing — broadsheet density

```
┌──────────────────────────────────────────────────────────────┐
│ PL·ANALYTICS                          value  match  style  about│
├══════════════════════════════════════════════════════════════┤  ← masthead rule, vermilion
│                                                              │
│   Three models that                                          │
│   tell you when                                              │  --b-display
│   they don't know.                                           │
│                                                              │
│   Market value, match outcome and playing-style clusters       │  --b-lead
│   for the Premier League — each shown with what it cannot do.  │
│                                                              │
│   ───────────────────────────────────────────────────────    │
│                                                              │
│   R² 0.727 ± 0.054      0.470 vs 0.446      silhouette 0.180  │  mono, from the artefacts
│   value predictor        match predictor     style finder      │
│                                                              │
│   [ open the value tool → ]   [ match → ]   [ style → ]       │  reachable immediately
│                                                              │
│   ───────────────────────────────────────────────────────    │
│                                                              │
│   163 of 661 players get no estimate.                        │  the refusal, stated as a
│   1,649 of 4,616 matches get no forecast.                    │  headline, not a caveat
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

The credibility material leads and the tools are reachable in the first viewport —
PRODUCT.md's ordering rule, which governs sequence and never gates access. **No
kicker above the heading** (Impeccable's one outright ban). Figures come from the
artefacts, never typed.

### 6.2 Value tool, normal reading — blueprint density

```
  Market value estimate
  ─────────────────────────────────────────────────────────────

  CLUB            POSITION         PLAYER
  [All clubs  ▾]  [All positions ▾] [Bukayo Saka          ▾]

  ═════════════════════════════════════════════════════════════

  Bukayo Saka
  Arsenal FC · Attack · 23.8 yrs · 17,487 PL min

  ESTIMATE
  €70.7M – €216.4M                                    --t-value, mono

        €10M        €50M        €100M       €500M
  ├──────┬───────────╆━━━━━━━━━━━━━━━━━━━╅──────┬─────────┤   ← band, serif-capped
                     ▲ €123.6M          ○ actual €110.0M

  A ×1.75 band around €123.6M, which is the typical size of a
  miss rather than a bound.                              --t-finding, serif

  › What the band means, and what it does not
```

### 6.3 Style tool, contested — the hardest case

```
  Lewis Hall
  Newcastle United · DF · 20 yrs · 2,181 PL min

  ASSIGNED CLUSTER
  High tackles won, fouls, yellow cards          †

  0.00        0.10                0.50                    2.74
  ├───────────┬───────────────────┬───────────────────────┤
  │▓▓▓▓▓▓▓▓▓▓▓│░░░░░░░░░░░░░░░░░░░│                       │
  │ CONTESTED │ BORDERLINE        │ CLEAR                 │
   ▲ 0.042

  Nearly as close to "Low involvement" — and sits among that
  cluster's members rather than its own.

  † Per-player silhouette is negative. That is a different problem
    from a narrow margin: 19 of 315 players are in this position.

  › What margin and silhouette each measure
```

The dagger carries the second signal without a second hue and without a second box.

### 6.4 Refusal

```
  Alex Murphy
  Newcastle United · Defender · 22.2 yrs · 18 PL min

  ESTIMATE
  —                                        em-dash, --t-value, --ink-300

  CALIBRATED RANGE
  900                                                    32,861
  ├──────────────────────────────────────────────────────┤
  ╳ 18
  this player

  Under 900 minutes the per-90 inputs stop measuring anything —
  one shot in three minutes reads as 30 shots per 90.

  › Why the model refuses rather than extrapolating
```

---

## 7. The four-shapes test, re-run against this direction

| Shape | Carried by | Verdict |
|---|---|---|
| **a** Range with a tolerance | §5.1 — serif-capped band on a log rule, point tick, open actual marker | ✅ The engineering dimension line is the native form for a stated tolerance |
| **b** Three-way distribution | §5.2 — fixed H·D·A, texture not weight, printed base-rate tick | ✅ Categorical data kept off the ordinal channel; order fixed structurally |
| **c** Tier + continuous margin | §5.3 — ink-density zones with printed thresholds, needle, dagger for the second signal | ✅ Density and position agree; the independent signal gets a footnote rather than a competing colour |
| **d** Refusal | §5.4 — empty trough, calibrated span, em-dash | ✅ The strongest shape in this direction, and the reason it was chosen |

**Two densities, one test.** The landing page states shapes (a)–(d) as figures in
prose rather than as live marks, so the broadsheet density carries them as
*claims*; the tools carry them as *instruments*. Neither density weakens a shape.

---

## 8. What this system forbids

Carried forward where the old list was right, revised where Step 1 showed it wrong.

1. **No hue on a data mark.** Confidence is ink density; the vermilion annotates
   and never fills. *(Replaces the old "no tool accent on a mark" — there are no
   tool accents now.)*
2. **No red for a weak reading.** Weak is the instrument working; red says broken.
3. **No warning box where a mark would do.**
4. **One sentence beside a mark, then a disclosure.** No paragraphs inline.
5. **Probability segments are fixed H·D·A**, never sorted, and never shaded by
   magnitude.
6. **Market value on a log scale.** Linear makes the band meaningless.
7. **No number without tabular figures.**
8. **One rail height** (`--rail-h`) across all tools.
9. **No invented archetype language** in project 03. Names come from the artefact.
10. **No claim of skill from a single case.**
11. **Only two font weights**, 400 and 600.
12. **No kicker or eyebrow above a heading.** *(New — Impeccable's one outright
    ban, adopted verbatim.)*
13. **No coloured border-left above 1px** on a callout, card or list item. *(New —
    the `/about` limitation block is exactly this and does not survive.)*
14. **`Panel` is not the page structure.** One container serving controls, results,
    errors and licensing alike is the lazy container; nested panels are always
    wrong. *(New.)*
15. **No gradient, glow, or drop-shadow on a mark.** Depth comes from contrast, as
    Miranda's system puts it, not from shadow.
16. **No dark mode in v1**, deliberately.

---

## 9. Base UI

Chosen in Step 5. Every verdict was re-derived against the ink-on-paper system
rather than carried over — and one had to be, because **the prior Sonner and Vaul
rejections were not recorded anywhere**: not in a document, not in a commit
message. An unrecorded decision is one that has to be made again, so both were
re-argued from scratch. They are recorded here so this does not repeat.

### Kept

**Radix Collapsible** — the disclosure is load-bearing. V4 sends every paragraph
behind it, so it is the mechanism the caveat rules depend on. It also publishes
the measured content height, which is what lets the expand animate without a
guessed `max-height` that clips long caveats.

**Radix Popover** — dismissal, focus return and outside-click for the player
search. Rebuilding this by hand is how keyboard traps get shipped.

**cmdk** — the 661-player and 330-match searches. Nothing about a change of visual
world changes the need to search a long list.

### Changed: Radix Select is adopted, having been installed and never used

`@radix-ui/react-select` has been a dependency since the scaffold and is imported
**nowhere**; four native `<select>` elements are used instead. Shipping an unused
dependency is its own small failure, so this needed resolving either way.

It is adopted rather than removed. A native `<select>` renders its open list as OS
chrome, which cannot be typeset — and in a world this committed to a printed
document, an operating-system dropdown is exactly the undrawn seam the craft floor
warns about. The closed state can be styled; the open state is where the illusion
breaks.

With one consequence: **Club (30+ options) becomes a Combobox**, joining Player and
Match. Select then handles only genuinely short lists — Position (4), Season (9) —
which is the rule the old `SimpleSelect` comment already stated and did not follow.
Search for long lists, select for short ones.

### Kept with an adaptation: Lucide

Only two icons are in use — `ChevronsUpDown` and `ChevronRight` — and both are
genuine affordances rather than decoration. Lucide stays, because the craft floor
is right that icons should come from a real library at one consistent stroke, not
from Unicode.

**Set `strokeWidth` to 1.** Lucide's 2px round-capped default is a modern-UI
signature that fights a hairline paper world; 1px matches `--rule-w` so an icon
reads as drawn with the same pen as the rules around it.

`lucide-react` is four majors behind (0.469 → 1.37) and should be upgraded in
Step 6, not silently left.

**Typographic marks are not icons.** The dagger (†) on a footnoted reading, the
em-dash on a refusal, and the `›` on a disclosure are *typesetting*, set in the
text face, and they are the correct form precisely because print already has these
conventions. The craft floor's ban is on a Unicode glyph *standing in for* an icon
system — a `▶` doing a chevron's job. That is a different thing and remains
banned.

### Rejected: Sonner

The verdict is unchanged and the reasoning is now stronger, not merely inherited.

A toast is a **time-limited** message. This system's entire argument is that
uncertainty is stated in place and stays there: confidence is ink density on the
mark, refusal is an em-dash where the figure would be. §3.4 already forbids a
caveat living only in a tooltip because hover is invisible to touch and to a
screen reader; a toast is worse, because it is invisible to *everyone* a few
seconds later.

The new direction adds a second, independent reason: **paper has no notifications.**
A transient overlay is a category error in a printed-document world, not merely an
accessibility problem.

There is also nothing for it to announce. There is no save, no submit, no
mutation — the entire site is read-only over three artefacts.

*The one thing that would reopen this:* if Step 8's URL-state work introduces a
copy-link affordance, that action needs feedback and a toast is the conventional
answer. Reopen it then, on that specific need, and not before.

### Deferred, not rejected: Vaul

This verdict **changes** from the old one. Vaul is a bottom-sheet primitive, and
the case for it is a real problem this build already has rather than a stylistic
preference: a `cmdk` list of 661 players inside a popover, at 375px, is the exact
thing Step 7's mobile QA is meant to test. A bottom sheet is the standard answer
because it gets full height and protected focus.

It is not adopted now, because adopting a dependency for a problem that has not
been demonstrated is speculative, and the craft floor's warning against "a modal
for a task that needs neither interruption nor protected focus" cuts both ways —
a 661-item search on a phone may well *earn* protected focus.

**The trigger is named so this is decidable rather than re-argued:** if Step 7's
mobile pass shows the player or match picker unusable at 375px — list clipped,
keyboard covering results, or scroll trapped — Vaul is adopted for the picker on
small viewports only, and the desktop popover is untouched. If the picker holds
up, Vaul stays out and this note records why it was considered.

---

## 9b. Amended in Step 7, by measurement

Three token values changed during the critique/audit pass. Recorded here so the
scale in §2 and §3 stays the authority rather than drifting from the code.

- **`--ink-300` #948C7C → #766F61.** Measured 3.04:1 against the page ground
  while carrying real annotation text. Now 4.54:1 on paper-100 and 4.90:1 on a
  sheet.
- **`--t-micro` 11px → 12px.** The detector read it as body text, and on a
  light ground 11px was genuinely tight. It no longer differs from `--t-label`
  in size, which is fine: those two are separated by case and tracking, not by
  scale step.
- **`--b-display` max 92px → 74px.** At 92px the landing headline occupied 29%
  of the viewport and pushed the three tool links below the fold, which turned
  PRODUCT.md's ordering rule into the gate it explicitly is not.

---

## 10. Open for Step 6 and later

- **Crest treatment.** PRODUCT.md confirms crests are in. How they sit in an
  ink-on-paper world — single-ink, duotone, or full colour as the one licensed
  exception — is a Step 6 decision.
- **Generative per-player graphics.** Built from real per-90 data. Form is Step 6.
- **Whether the landing page needs its own route** (`/` currently redirects to
  `/value`). Step 8 owns routing.
