/**
 * Flatten a downloaded SVG badge to a single ink.
 *
 *   node scripts/flatten-crest.mjs in.svg                 # preview to stdout
 *   node scripts/flatten-crest.mjs in.svg out.svg         # write a new file
 *   node scripts/flatten-crest.mjs in.svg --write         # rewrite in place
 *   node scripts/flatten-crest.mjs public/crests/*.svg --write
 *
 * This does the tedious half of preparing a crest — making it one colour —
 * which is reliable text transformation. It does NOT do the half that needs
 * drawing judgement: it will not simplify a complex badge, redraw it at a
 * consistent weight, or make two differently-traced sources match. Those stay
 * manual, and `npm run crests` still has to pass afterwards.
 *
 * WHAT IT PRESERVES, AND WHY
 *   `fill="none"` is structural, not colour. It means "do not fill this shape",
 *   and a ring drawn as an outline depends on it. Replacing it with an ink
 *   would fill the hole and turn a badge into a blob, so it is left alone —
 *   this is the single most important rule here.
 *
 * WHAT IT FLAGS RATHER THAN GUESSES
 *   Gradients, patterns, filters, masks and embedded raster cannot be reduced
 *   to one ink by substitution. They are reported so a human decides, because
 *   silently pointing a gradient fill at currentColor produces a shape that
 *   looks right in the preview and wrong at 18px.
 */

import { readFileSync, writeFileSync } from "node:fs";

const INK = "currentColor";

const argv = process.argv.slice(2);
const write = argv.includes("--write");
const keepStroke = argv.includes("--keep-stroke");
const inputs = argv.filter((a) => !a.startsWith("--"));

if (inputs.length === 0) {
  console.error(
    "usage: flatten-crest.mjs <in.svg> [out.svg] [--write] [--keep-stroke]",
  );
  process.exit(2);
}

/** @param {string} svg */
function flatten(svg) {
  const notes = [];
  let out = svg;

  // Things substitution cannot fix. Report, do not touch.
  if (/<(linearGradient|radialGradient|pattern)[\s>]/i.test(out))
    notes.push("gradient or pattern — needs a human decision");
  if (/<(filter|mask)[\s>]/i.test(out))
    notes.push("filter or mask — may not flatten cleanly");
  if (/<image[\s>]/i.test(out) || /data:image\//i.test(out))
    notes.push("embedded raster — cannot be vectorised here");
  if (/<text[\s>]/i.test(out))
    notes.push("live <text> — convert to outlines, or the club's font is a dependency");

  // Attribute fills and strokes. `none` is structural and survives; a
  // url(#...) reference is reported above and still pointed at the ink so the
  // shape does not vanish.
  out = out.replace(
    /\b(fill|stroke)\s*=\s*(["'])(.*?)\2/gi,
    (m, prop, q, value) => {
      const v = value.trim().toLowerCase();
      if (v === "none" || v === "transparent") return m;
      return `${prop}=${q}${INK}${q}`;
    },
  );

  // The same two properties inside style="" and inside <style> blocks.
  out = out.replace(
    /(fill|stroke)\s*:\s*([^;"'}]+)/gi,
    (m, prop, value) => {
      const v = value.trim().toLowerCase();
      if (v === "none" || v === "transparent") return m;
      return `${prop}:${INK}`;
    },
  );

  // A stroke is a second weight, and two sources rarely agree on it, so
  // dropping it usually makes a downloaded badge sit correctly beside the
  // others.
  //
  // BUT NOT WHERE THE STROKE IS THE MARK. An element with fill="none" is drawn
  // entirely by its stroke — a hollow ring, an outlined shield — and removing
  // it deletes the element rather than simplifying it. The first version of
  // this did a global substitution and turned a ring into nothing at all, so
  // the decision is per element.
  if (!keepStroke) {
    let dropped = 0;
    let kept = 0;
    out = out.replace(/<([a-z]+)\b([^>]*)>/gi, (tag, name, attrs) => {
      if (!/stroke\s*[:=]/i.test(attrs)) return tag;
      const unfilled =
        /\bfill\s*=\s*(["'])\s*none\s*\1/i.test(attrs) ||
        /fill\s*:\s*none/i.test(attrs);
      if (unfilled) {
        kept++;
        return tag;
      }
      dropped++;
      return (
        "<" +
        name +
        attrs
          .replace(/\bstroke\s*=\s*(["'])[^"']*\1/gi, 'stroke="none"')
          .replace(/stroke\s*:\s*[^;"']+/gi, "stroke:none") +
        ">"
      );
    });
    if (dropped)
      notes.push(
        `stroke dropped on ${dropped} element${dropped === 1 ? "" : "s"} (--keep-stroke to retain)`,
      );
    if (kept)
      notes.push(
        `stroke kept on ${kept} unfilled element${kept === 1 ? "" : "s"} — it is the mark there`,
      );
  }

  // The component sets the size; a fixed one fights it and MANIFEST.md
  // requires a viewBox instead.
  if (/<svg[^>]*\bviewBox\s*=/i.test(out)) {
    // Rewrite the opening tag as a unit. Chaining two global replaces over the
    // whole document dropped `width` and left `height`, because the regex had
    // already advanced past it.
    out = out.replace(/<svg\b[^>]*>/i, (open) =>
      open.replace(/\s(width|height)\s*=\s*(["'])[^"']*\2/gi, ""),
    );
  } else {
    notes.push("no viewBox — add one before this can be used");
  }

  // Opacity on a single-ink mark reads as a second, lighter ink.
  if (/\b(fill-opacity|stroke-opacity|opacity)\s*[:=]/i.test(out))
    notes.push("opacity present — reads as a second ink at 18px");

  // A stroke declared in a <style> block cannot be matched to the element it
  // paints, so the per-element rule above never sees it and it survives as a
  // second weight. Reported rather than guessed at: dropping every CSS stroke
  // would erase any outline-only shape styled by class, which is the same bug
  // the per-element rule exists to avoid.
  const styleBlock = out.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
  if (styleBlock && /stroke\s*:\s*(?!none)/i.test(styleBlock[1]))
    notes.push("stroke set in a <style> block — check it is not a second weight");

  return { out, notes };
}

let failed = false;
const [first, second] = inputs;
const singleOut = inputs.length === 2 && !second.startsWith("--") ? second : null;

for (const file of singleOut ? [first] : inputs) {
  let svg;
  try {
    svg = readFileSync(file, "utf8");
  } catch (e) {
    console.error(`  ${file}: ${e.message}`);
    failed = true;
    continue;
  }

  const { out, notes } = flatten(svg);
  const target = singleOut ?? (write ? file : null);

  if (target) {
    writeFileSync(target, out, "utf8");
    console.log(`  ${file} -> ${target}`);
  } else if (inputs.length === 1) {
    process.stdout.write(out.endsWith("\n") ? out : out + "\n");
  } else {
    console.log(`  ${file} (preview only; pass --write)`);
  }

  for (const n of notes) console.error(`      ! ${n}`);
  if (notes.some((n) => n.includes("cannot") || n.includes("no viewBox")))
    failed = true;
}

process.exit(failed ? 1 : 0);
