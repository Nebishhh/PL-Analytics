# getdesign.md — Step 1: Research / Taste

Research for a unified React + FastAPI frontend replacing the three Streamlit
apps. **No code or design files produced yet.** The three Streamlit apps remain
untouched and working.

---

## 0. Method, and what I could not get

Honesty about sourcing, because it changes how much weight each finding carries.

| Source | Access | What I got |
|---|---|---|
| **Awwwards** | Full | Browsed the Data Visualization category (1,280 sites) and Sports category. Extracted current listings, opened detail pages, read community scores. |
| **Fonts In Use** | Full | Sports topic (852 uses, 134 staff picks). Extracted real use names and, where the contributor wrote them up, actual typeface combinations. |
| **Refero** | ❌ **Blocked** | Requires an account — *"Other pages are hidden. Log In or Sign Up to See All."* I did not create one. No Refero findings below. |

Where a reference was **verified in this session** it is marked ✅. Where it comes
from domain knowledge rather than this session's browsing it is marked ○ — still
real and checkable, but I did not open it just now. Treat ✅ as evidence and ○ as
argument.

**One correction worth recording:** Fonts In Use shows a "most used typefaces"
sidebar on every topic page. It is tempting to read the Sports page's sidebar as
"the typefaces of sports design" — Helvetica 1513, Futura 1237, Univers 655. It
is not. I compared it against the News topic page and **the counts are byte-for-byte
identical**, so it is a site-wide popularity list, not topic-scoped. Nothing in
this document rests on it.

---

## 1. Awwwards: what reads as trustworthy vs gimmicky

The most useful thing I found was not a single site but a **natural experiment**.
Two World Cup 2026 data projects, both current Awwwards nominees, taking opposite
approaches — and the community scored them very differently.

### ✅ WC 2026 — Data Portraits *(nominee, Jul 2026)*

> "Every FIFA World Cup 2026 match rebuilt in 3D from real data — ~1,500 events a
> game become readable terrain. Real-time WebGL, data-driven crowd sound, live
> scorer cards. Coded solo."

Tags: Experimental, Sports, Animation, 3D, Data Visualization, Sound-Audio, WebGL,
Three.js, GLSL.

**Community scores: 6.30, 6.00, 7.00, 7.20, 7.90.**

### ✅ World Cup 2026, simplified. *(nominee, Jun 2026)*

> "Every team, stadium and match of the 2026 World Cup, built in a format that's
> easy to digest. 48 nations as homes, 16 stadiums, each side's travel and heat,
> and the road to the final."

Tags: Clean, Colorful, Minimal, Data Visualization, CSS, HTML5, Javascript.

**Community scores: 8.00, 7.70, 9.00, 8.00, 6.00.**

### What that contrast says

The same subject matter, the same year, the same jury pool. The one that describes
itself as *"easy to digest"* outscores the one that turns 1,500 events into 3D
terrain with generative crowd noise — by roughly a full point and a half at the
median.

I would not over-read five votes each. But the direction matches what the tag
vocabulary itself implies: the spectacle project is tagged **Experimental**, the
legible one is tagged **Clean / Minimal**. Awwwards rewards craft in both, and the
craft that reads as *trustworthy* is the craft of compression.

**The gimmick tell, generalised from the Data Visualization category listing:**
projects where the visual metaphor has to be *learned* before any data can be read
— terrain, particle fields, orbital diagrams, audio-reactive anything. The reader
spends their attention decoding the encoding. For a project whose entire claim is
"here is a number and here is how much to trust it", that is attention spent in
exactly the wrong place.

**The trust tell:** the number is legible in under a second, and the qualification
is adjacent to it rather than beneath it.

### Other ✅ listings worth knowing about

From the Data Visualization category, current: *Redesigning Trust: Level2*,
*Signal IQ (Setu by Pine Labs)*, *HydraDB*, *Cerebrium*, *Stone Center*,
*Everest · The Ascent*. From Sports: *The Performance Lab*, *sensiq.co*, *Radian*,
*Podium*, *Williams Grand Prix Tech*, *Cadillac Formula 1 Team*.

The F1 team sites are a useful negative reference: they are *brand* sites wearing
data as decoration — telemetry-styled ornament with no actual telemetry. That is
the failure mode our project must avoid in the other direction, since we have real
uncertainty to show and would be actively lying if we styled it as swagger.

---

## 2. Typography

### ✅ Verified from Fonts In Use

**Inside Youth Basketball 2025 report** (Luka Dončić Foundation), Mar 2026 —
designers Kurt Woerpel, Nejc Prah, Tracy Ma:

> "used **Focal** alongside **ABC Marist** and **VCR OSD Mono** for the report."

This is the single most relevant artefact I found: a *sports data report*, not a
sports brand. Its type system is three-part —

- **Focal** — a contemporary grotesk, does the UI and figure work
- **ABC Marist** — a serif, carries the prose and gives the document an editorial
  voice rather than a dashboard voice
- **VCR OSD Mono** — a mono, for the data itself

That grotesk + serif + mono triad is exactly the structure a project like ours
wants, and it is worth noting that a *foundation's youth basketball report* reached
for a serif. Data-serious does not have to mean voice-less.

The Sports topic (852 uses) is otherwise dominated by identity work — clubs, kits,
races, campaigns. ✅ *ballesterer* #206, an Austrian football magazine running a
critical 100-page World Cup issue, is the closest thing to a sports-*journalism*
register in the set. ✅ *Terzo Uomo* is literally a typographic analysis of football
shirt numbering. Neither is a dashboard, and that gap is itself the finding: **there
is very little prior art for "football analytics as a serious document."** Most
football typography is either kit-and-crest heraldry or broadcast-graphic bombast.

### ○ The three registers, named

- **"Fantasy football app"** — Poppins, Montserrat, Nunito, heavy rounded geometrics,
  gradient-filled numerals, badge shapes. Reads as gambling-adjacent. Actively
  wrong for us: it signals confidence we do not have.
- **"Corporate dashboard"** — Inter, Roboto, Open Sans, system stacks. Trustworthy
  but voiceless. Our project has opinions ("the clustering is least trustworthy
  where it is most interesting") and a voiceless typeface cannot carry them.
- **"Serious analytics"** — a neutral grotesk for UI, a real mono for figures, and
  optionally a serif for argument. Examples ○: FiveThirtyEight (Decima Mono +
  Atlas Grotesk), The Pudding, Bloomberg Graphics, The Athletic's data pieces,
  Observable, FBref/StatsBomb output.

**The mono is not decoration.** Tabular figures that align across rows are the
difference between a comparison table you can scan and one you have to read.
Every one of our three projects is fundamentally a table of numbers with
qualifications attached.

---

## 3. Five directions

### Direction A — Data terminal

Dark ground, mono-forward, dense, high information-per-pixel. Numbers are the
interface. Minimal chrome, no illustration, generous use of tabular figures and
small-caps labels.

- ○ Bloomberg Terminal aesthetic, ○ Observable notebooks, ○ Vercel/Linear dark
  surfaces, ✅ *HydraDB* and *Cerebrium* from the Awwwards data-viz listing.
- **Fit:** Strong. Our current Streamlit apps are already dark-purple, so this is
  continuous with what exists. Density suits three projects under one roof.
- **Risk:** Mono-everything becomes unreadable in prose, and this project has a
  *lot* of prose — the caveats are the product. Terminal aesthetics also carry a
  "quant who is very sure of himself" connotation that is the opposite of our
  actual message.

### Direction B — Editorial sports journalism

Serif headlines, generous measure, charts embedded in argument rather than gridded
into a dashboard. The page reads as a piece *about* the model, not a control panel
*for* it.

- ✅ *ballesterer* magazine, ✅ *Inside Youth Basketball 2025* report; ○ The Pudding,
  ○ FiveThirtyEight long-form, ○ The Athletic tactical analysis.
- **Fit:** Very strong on substance. Every one of our three projects has a written
  finding at its centre — "learned home advantage, learned nothing about draws";
  "least trustworthy where most interesting". Those are *sentences*, and editorial
  design is built to carry sentences next to figures.
- **Risk:** Weak on interaction. An editorial layout wants to be read top to bottom;
  our apps are lookup tools where the user picks a player and gets an answer. Pure
  editorial would fight that.

### Direction C — Clean SaaS dashboard

Light ground, card grid, Inter, restrained accent colour, generous whitespace,
conventional chart library styling.

- ✅ *Signal IQ (Setu by Pine Labs)*, ✅ *PartnerProp*; ○ Stripe Dashboard,
  ○ Linear, ○ Posthog.
- **Fit:** Fastest to build, most familiar to users, best component ecosystem.
- **Risk:** **This is the direction most likely to make us dishonest.** SaaS
  dashboard conventions are built to project competence — every metric in a card,
  every card equally weighted, every number equally confident. A ×1.75 error range
  and a 47%-accurate classifier rendered in that visual language will read as more
  authoritative than they are. The form actively fights the content.

### Direction D — Instrument panel / measurement device

Explicitly borrows from scientific instruments and measurement: ranges drawn as
ranges, error bars as first-class marks, tick scales, calibration language. The
visual metaphor is a *gauge with tolerances*, not a scoreboard.

- ○ Our World in Data, ○ FiveThirtyEight's election forecast "snake" and cone-of-
  uncertainty charts, ○ NASA/JPL mission dashboards, ○ scientific poster
  conventions; ✅ *Stone Center* (economics data) from the Awwwards listing.
- **Fit:** This is the only direction where **uncertainty is the native visual
  vocabulary rather than an addition to it.** Our three outputs are: a range
  (project 01), a probability distribution (02), and a confidence tier with a
  distance margin (03). All three are measurement statements.
- **Risk:** Can tip cold and academic. Needs deliberate warmth — colour, a serif,
  real player names and photos — or it feels like a lab report about football.

### Direction E — Broadcast graphics / matchday

Bold condensed type, team colours, high contrast, the visual language of Sky Sports
and TNT match graphics.

- ○ Sky Sports / Premier League broadcast packages, ○ FIFA/UEFA match graphics;
  ✅ the F1 team sites (*Williams Grand Prix Tech*, *Cadillac F1*).
- **Fit:** Immediately legible as football. Familiar to any visitor.
- **Risk:** **Worst fit of the five.** Broadcast graphics exist to project certainty
  and drama — they are advocacy, not analysis. There is no broadcast convention for
  "we are 47% accurate and cannot predict draws". Adopting this language would
  require either hiding our caveats or having them constantly clash with the styling.

---

## 4. Which directions carry uncertainty without becoming a wall of warnings

This is the real design problem, and it is worth stating precisely why it is harder
here than in any of the three Streamlit apps individually.

**Each Streamlit app had one caveat shape.** Project 01: a multiplicative range.
Project 02: a probability distribution plus a draw-blindness note. Project 03: a
three-tier confidence badge plus a negative-silhouette flag. Individually, each got
its own bespoke treatment.

**A unified frontend has to hold all three at once, in one visual language**, and
they are genuinely different kinds of doubt:

| Project | Uncertainty shape | Native mark |
|---|---|---|
| 01 value | Multiplicative range (×1.75) + refusal below 900 min | Interval / error bar |
| 02 match | 3-way probability distribution, ~47% top-1 accuracy | Stacked bar / simplex |
| 03 style | Discrete confidence tier + continuous margin | Badge + distance comparison |

Plus a **fourth** state the others do not have: **refusal**. Project 01 declines to
predict under 900 minutes. That is not low confidence, it is *no answer*, and it
needs a visual treatment distinct from "wide range".

### Ranking the directions on this specific problem

**D (Instrument panel) — strongest.** Ranges, tolerances and tiers are the same
grammar. A ×1.75 band, a probability distribution and a centroid margin can all be
drawn as *positions on a scale with a marked region*, which unifies three different
statistical objects under one mark. Refusal becomes "outside measurable range" —
a legible instrument state, not an error message.

**B (Editorial) — strong, differently.** Editorial design's answer to uncertainty is
*prose adjacency*: the qualification sits in the sentence next to the number, not in
a callout below it. Our project-03 restructure already discovered this — the
badge-plus-one-sentence pattern outperformed the paragraph. Editorial scales that
instinct across all three projects. Weaker on the *comparative* case (two players
side by side).

**A (Data terminal) — workable but cold.** Terminals show precision well and doubt
badly. Everything renders as equally hard numbers; there is no established terminal
convention for "this figure is soft". Would need invented vocabulary.

**C (SaaS dashboard) — actively hostile.** Card grids imply every metric is equally
solid. Warnings become yellow boxes, and yellow boxes accumulate into exactly the
wall the brief warns about. To show our caveats honestly we would be fighting the
idiom on every screen.

**E (Broadcast) — incompatible.** No convention for doubt at all.

### The pattern that avoids the wall of warnings, whichever direction wins

From what the project-03 restructure demonstrated empirically last session:

1. **One glanceable state marker** (badge/colour/bar position) — not a sentence.
2. **One short sentence** carrying the single most important qualification.
3. **Everything else behind a disclosure** the reader opens if they care.
4. **The uncertainty is drawn, not written**, wherever a mark can carry it — a
   range as a range, a probability as a proportion, a margin as a gap.

Rule 4 is what keeps it off the warning-wall. A yellow box is a warning. A bar with
a visibly wide band is *information* — same honesty, no scolding.

---

## 5. What I am not doing yet

Not recommending one. You pick, then we move to DESIGN.md.

Two things I would want settled at that point, because they constrain the visual
system more than the aesthetic does:

- **Is the unified app three tools under one shell, or one narrative with three
  chapters?** Direction B only works for the second reading; D works for both.
- **Does it need a comparison view** (two players, two matches side by side)? None
  of the Streamlit apps have one. If yes, that pushes toward D or C, because
  editorial layouts handle side-by-side comparison poorly.
