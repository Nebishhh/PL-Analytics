# Crest artwork — provenance

31 canonical clubs. Filenames come from `crestSlug()` in
`src/lib/crestSlug.mjs`; do not rename them by hand — run `npm run crests` and
use the names it prints.

**Every file must record where it came from.** A crest with no provenance is a
trademark question nobody can answer later.

## Requirements

Checked by `npm run crests`, which reports any file that fails:

- **SVG with a `viewBox`**, and no fixed pixel width/height — the component
  sizes it.
- **Single colour.** Prefer `currentColor` so the mark inherits the ink around
  it; one flat fill is acceptable. Not the club's official colours: this is an
  ink-on-paper system, and a full-colour badge would be the only chromatic
  object on the page, which is what V1 exists to prevent.
- **No embedded raster.** No `<image>`, no base64 payload. A traced PNG inside
  an SVG wrapper is still a PNG.
- **Consistent weight across all 31.** One treatment from one source family —
  not a mix of outline and solid, or heavy and hairline.

## Sourcing

These are club trademarks. PRODUCT.md records the decision to use them as
accepted and settled; that decision does not extend to the *files*, so each row
below needs a real answer under Source.

Routes that give a consistent set rather than 31 mismatched ones:

- **Wikimedia Commons** — most clubs have an SVG badge with a stated licence.
  Licences vary per file, so record each one separately.
- **Trace one source family yourself** — official badges through a vector tracer
  at a fixed threshold and stroke weight. Slowest, most consistent result.
- **Commission or buy a set** — the only route with unambiguous licensing.

## Making a downloaded badge single-colour

`npm run flatten-crest -- <in.svg> <out.svg>` strips the colours and sets
`currentColor`, which is the tedious half of preparing a badge. It does not do
the half that needs drawing judgement — it will not simplify a complex crest,
redraw it at a consistent weight, or make two differently-traced sources match.

It preserves `fill="none"`, because that is structural: a hollow ring is drawn
entirely by its stroke, and filling it turns a badge into a blob. For the same
reason it keeps the stroke on unfilled elements and drops it elsewhere. It
reports, rather than guesses at, gradients, patterns, filters, embedded raster,
live `<text>`, opacity, and strokes declared in a `<style>` block.

Run `npm run crests` afterwards — flattening does not guarantee the result
passes.

Avoid mixing sources. Two crests traced at different weights are more visibly
wrong here than a monogram is, because they sit at 18px beside the same club
name on the same rule.

## Files

| File | Source | Licence | Notes |
|---|---|---|---|
| `afc-bournemouth.svg` | | | |
| `arsenal-fc.svg` | | | |
| `aston-villa.svg` | | | |
| `brentford-fc.svg` | | | |
| `brighton-and-hove-albion.svg` | | | |
| `burnley-fc.svg` | | | |
| `chelsea-fc.svg` | | | |
| `crystal-palace.svg` | | | |
| `everton-fc.svg` | | | |
| `fulham-fc.svg` | | | |
| `hull-city.svg` | | | |
| `ipswich-town.svg` | | | |
| `leeds-united.svg` | | | |
| `leicester-city.svg` | | | |
| `liverpool-fc.svg` | | | |
| `luton-town.svg` | | | |
| `manchester-city.svg` | | | |
| `manchester-united.svg` | | | |
| `newcastle-united.svg` | | | |
| `norwich-city.svg` | | | |
| `nottingham-forest.svg` | | | |
| `queens-park-rangers.svg` | | | |
| `sheffield-united.svg` | | | |
| `southampton-fc.svg` | | | |
| `sunderland-afc.svg` | | | |
| `swansea-city.svg` | | | |
| `tottenham-hotspur.svg` | | | |
| `watford-fc.svg` | | | |
| `west-bromwich-albion.svg` | | | |
| `west-ham-united.svg` | | | |
| `wolverhampton-wanderers.svg` | | | |
