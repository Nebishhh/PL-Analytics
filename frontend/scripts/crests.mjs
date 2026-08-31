/**
 * Crest coverage: which clubs have artwork, and which are still on the
 * typographic monogram fallback.
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

import { readdirSync, existsSync } from "node:fs";
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
      },
      null,
      2,
    ),
  );
} else {
  const pad = Math.max(...rows.map((r) => r.club.length));
  console.log(
    `\n  Crest coverage — ${haveSlugs.size}/${groups.size} clubs have artwork  (${rows.length} dataset names)\n`,
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
      ? `\n  ${missingSlugs.size} still on the typographic monogram.\n`
      : `\n  Complete — no club is falling back.\n`,
  );
}

process.exit(missing.length ? 1 : 0);
