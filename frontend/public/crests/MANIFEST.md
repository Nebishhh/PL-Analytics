# Crest artwork — evaluated, and not adopted

**Decision: the typographic monogram is the final design for club identity, not
a placeholder.** No crest artwork ships, and none is pending.

Recorded here rather than left in a conversation, per AGENTS.md §7.3: a
rejected alternative with its reasoning is a decision, and without it a rumour.
The next person to look at `Crest.tsx` will find code that loads an SVG and
will reasonably assume someone forgot to add the files. They did not.

## What was evaluated

Using crests was a settled product decision — PRODUCT.md recorded the trademark
consideration as accepted for a personal portfolio at this scale. That decision
was never the blocker. **Sourcing was.** Every route failed on licensing,
consistency or accuracy:

| Route | Why it failed |
|---|---|
| **Wikimedia Commons** | Does not hold current club crests. Direct file lookups for Chelsea, Manchester United, Liverpool and Tottenham return nothing on Commons and `Fair use` on en.wikipedia. |
| **English Wikipedia** | The files exist but are non-free. "Fair use" is not a licence — it is a US-law defence tied to Wikipedia's own encyclopedic use, argued per article, and it does not transfer to a third party. Copying them here and writing "Fair use" in a Licence column would record a licence that does not exist. |
| **Historical PD crests** | Genuinely free — the Arsenal 1888 and 2001–2002 marks are public domain — but only for some clubs, from the wrong era, and mismatched in style. Even the PD ones carry a `Restrictions: insignia` tag. A set assembled this way fails the consistency requirement by construction. |
| **Official club media kits** | Real terms exist per club, but 31 separate permissions at 31 different weights is disproportionate to a portfolio site, and would still not guarantee one visual treatment. |
| **Commission or buy a set** | The only route with unambiguous licensing, and not worth the cost here. |

## Why the monogram is a good answer rather than a consolation

It is **consistent by construction** — all 31 clubs get the same treatment,
which no assembled set of downloaded badges would have achieved.

It is **honest about what it is.** Initials set in the display face inside a
ruled square do not claim to be a badge. A traced approximation would have.

It **fits the world.** This is an ink-on-paper system where a full-colour badge
would be the only chromatic object on the page — exactly what V1 exists to
prevent. Every crest would have needed flattening to a single ink anyway, at
which point much of a badge's recognisability is gone.

It resolves through `canonicalClub()`, so a club shows the same initials in
every tool regardless of which dataset named it.

## If this is ever revisited

The loading path in `Crest.tsx` still works and is left in place as an escape
hatch, not as an unfinished task. Drop conforming SVGs into this directory named
by `crestSlug()` and they will be used with no code change.

`npm run crests` still validates any file it finds — viewBox present, single
ink, no embedded raster — and reports clubs on the monogram as the intended
state rather than as missing work. `npm run flatten-crest` still reduces a
downloaded badge to one ink.

Requirements a file would have to meet, unchanged:

- SVG with a `viewBox`, no fixed pixel width or height.
- Single colour, ideally `currentColor`.
- No `<image>` and no base64 payload.
- One consistent treatment across the whole set, or it is worse than no set.

**Every file added must record its source and licence below.** A crest with no
provenance is a trademark question nobody can answer later.

| File | Source | Licence | Notes |
|---|---|---|---|
| *(none — monogram is the design)* | | | |
