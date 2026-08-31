/**
 * Crest coverage: which clubs have artwork, and which use the typographic
 * monogram.
 *
 * THE MONOGRAM IS THE DESIGN. No artwork ships and none is pending -- see
 * public/crests/MANIFEST.md for why every sourcing route failed. So a club on
 * the monogram is the INTENDED state, not missing work, and this exits 0 for
 * it. It exits non-zero only for a file that is actually wrong: a crest that
 * fails the requirements, or a name the alias map does not cover.
 *
 *   node scripts/crests.mjs              # needs the backend on :8000
 *   node scripts/crests.mjs --json       # machine-readable
 *   node scripts/crests.mjs --api http://127.0.0.1:8000
 *
 * The club list comes from the API, not a hardcoded array, so it stays correct
 * if the dataset changes. The slug rule is imported from the same module the
 * Crest component uses -- a report with its own copy of that rule would drift
 * and then confidently tell you a file was present that the page never asks
 * for.
 *
 * Exit code is 0 when every club has artwork, 1 when any is missing, so this
 * can gate a deploy later if that is ever wanted. It is not wired into
 * anything today.
 */

import { readdirSync, existsSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { canonicalClub, crestSlug } from "../src/lib/crestSlug.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const CRESTS_DIR = join(here, "..", "public", "crests");

const args = process.argv.slice(2);
const asJson = args.includes("--json");
const apiBase =
  args[args.indexOf("--api") + 1]?.startsWith("http")
    ? args[args.indexOf("--api") + 1]
    : "http://127.0.0.1:8000";

/** Every club the dataset actually contains, from both player-bearing tools. */
async function clubsFromApi() {
  const seen = new Set();

  const players = await fetch(`${apiBase}/api/value/players`).then((r) => {
    if (!r.ok) throw new Error(`${r.status} on /api/value/players`);
    return r.json();
  });
  for (const p of players) if (p.club) seen.add(p.club);

  // Project 03 is a different season's squad list and can name a club that
  // project 01 does not, so both are asked.
  try {
    const style = await fetch(`${apiBase}/api/style/players`).then((r) =>
      r.ok ? r.json() : [],
    );
    for (const p of style) if (p.club) seen.add(p.club);
  } catch {
    /* style list is optional for this report */
  }

  return [...seen].sort((a, b) => a.localeCompare(b));
}

/**
 * What a crest file has to be, per public/crests/MANIFEST.md.
 *
 * Checked because these arrive one at a time over days, and a single
 * full-colour or raster-wrapped badge would be the one chromatic object on an
 * otherwise ink-on-paper page -- exactly what V1 exists to prevent, and the
 * kind of thing nobody notices until all 31 are in.
 *
 * @param {string} file
 * @returns {string[]} problems, empty when the file is fine
 */
function validate(file) {
  const bad = [];
  let svg;
  try {
    svg = readFileSync(join(CRESTS_DIR, file), "utf8");
  } catch {
    return ["unreadable"];
  }
  if (!/<svg[\s>]/i.test(svg)) bad.push("not an SVG");
  if (!/viewBox\s*=/i.test(svg)) bad.push("no viewBox");
  if (/<image[\s>]/i.test(svg) || /data:image\/(png|jpe?g|gif)/i.test(svg))
    bad.push("embedded raster");

  // Distinct explicit colours. currentColor and none do not count.
  const colours = new Set(
    [...svg.matchAll(/(?:fill|stroke)\s*[:=]\s*["']?\s*(#[0-9a-f]{3,8}|rgba?\([^)]*\)|[a-z]+)/gi)]
      .map((m) => m[1].toLowerCase())
      .filter((c) => c !== "none" && c !== "currentcolor" && c !== "inherit"),
  );
  if (colours.size > 1)
    bad.push(`${colours.size} colours (${[...colours].slice(0, 3).join(", ")})`);

  return bad;
}

function filesOnDisk() {
  if (!existsSync(CRESTS_DIR)) return { exists: false, files: [] };
  return {
    exists: true,
    files: readdirSync(CRESTS_DIR).filter((f) => /\.svg$/i.test(f)),
  };
}

const { exists, files } = filesOnDisk();
const present = new Set(files.map((f) => f.replace(/\.svg$/i, "")));

let clubs;
try {
  clubs = await clubsFromApi();
} catch (e) {
  console.error(
    `Could not reach the API at ${apiBase} — start the backend, or pass --api.\n  ${e.message}`,
  );
  process.exit(2);
}

/**
 * A heuristic guess at "same club, different spelling", used ONLY to catch an
 * alias the map is missing.
 *
 * With CLUB_ALIASES in place this should never disagree with crestSlug. When it
 * does, a new name has entered a dataset and needs an entry -- which is exactly
 * the failure that produced 43 filenames for 31 clubs before the map existed.
 */
function heuristicKey(club) {
  return club
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/\b(fc|afc)\b/g, "")
    .replace(/\butd\b/g, "united")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

const problems = new Map();
for (const f of files) {
  const bad = validate(f);
  if (bad.length) problems.set(f, bad);
}

const rows = clubs.map((club) => {
  const slug = crestSlug(club);
  return { club, slug, have: present.has(slug) };
});
const have = rows.filter((r) => r.have);
const missing = rows.filter((r) => !r.have);
const haveSlugs = new Set(have.map((r) => r.slug));
const missingSlugs = new Set(missing.map((r) => r.slug));

// A file that matches no club is worth surfacing: it is a typo or a club that
// left the dataset, and either way it will never be requested.
const unmatched = [...present].filter((s) => !rows.some((r) => r.slug === s));

// Group the raw names that look like one club under two spellings.
const groups = new Map();
for (const r of rows) {
  if (!groups.has(r.slug)) groups.set(r.slug, []);
  groups.get(r.slug).push(r);
}

// Two raw names the heuristic thinks are one club, that resolved to different
// slugs anyway -> CLUB_ALIASES is missing an entry.
const byHeuristic = new Map();
for (const r of rows) {
  const k = heuristicKey(r.club);
  if (!byHeuristic.has(k)) byHeuristic.set(k, new Set());
  byHeuristic.get(k).add(r.slug);
}
const collisions = [...byHeuristic.values()]
  .filter((slugs) => slugs.size > 1)
  .map((slugs) => [...slugs].map((slug) => rows.find((r) => r.slug === slug)));

if (asJson) {
  console.log(
    JSON.stringify(
      {
        total: rows.length,
        distinctClubs: groups.size,
        have: haveSlugs.size,
        missing: [...missingSlugs],
        unmatched,
        collisions: collisions.map((g) => g.map((r) => r.slug)),
        invalid: Object.fromEntries(problems),
      },
      null,
      2,
    ),
  );
} else {
  const pad = Math.max(...rows.map((r) => r.club.length));
  console.log(
    `\n  Club identity — ${groups.size} clubs, ${rows.length} dataset names\n` +
      `  ${haveSlugs.size} with crest artwork, ${groups.size - haveSlugs.size} on the typographic monogram\n`,
  );
  if (!exists) {
    console.log(`  ${CRESTS_DIR} does not exist yet; every club is on the monogram fallback.\n`);
  }
  for (const [slug, g] of [...groups.entries()].sort()) {
    const canonical = canonicalClub(g[0].club);
    const others = g.map((r) => r.club).filter((n) => n !== canonical);
    const also = others.length ? `  (also: ${others.join(", ")})` : "";
    console.log(
      `  ${g[0].have ? "have" : "  — "}  ${canonical.padEnd(pad)}  ${slug}.svg${also}`,
    );
  }
  if (problems.size) {
    console.log(`
  ${problems.size} file${problems.size === 1 ? " does" : "s do"} not meet MANIFEST.md's requirements:`);
    for (const [f, bad] of problems) console.log(`        ${f}  —  ${bad.join("; ")}`);
  }
  if (unmatched.length) {
    console.log(`\n  Files matching no club in the dataset (never requested):`);
    for (const s of unmatched) console.log(`        ${s}.svg`);
  }
  if (collisions.length) {
    console.log(
      `
  MISSING ALIAS — ${collisions.length} club${collisions.length === 1 ? " looks" : "s look"} like one club under two names,`,
    );
    console.log(`  but resolved to different files. Add to CLUB_ALIASES:
`);
    for (const g of collisions) {
      console.log(`        ${g.map((r) => `${r.slug}.svg`).join("   vs   ")}`);
    }
  }

  console.log(
    missing.length
      ? `\n  The monogram is the design, not a gap — see public/crests/MANIFEST.md.\n`
      : `\n  Every club has artwork.\n`,
  );
}

// Non-zero for a real defect only. A club on the monogram is the design
// working as intended -- a check that fails forever on the intended state is
// a broken check, and would be the first thing anyone disabled.
process.exit(problems.size || collisions.length ? 1 : 0);
