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
import { crestSlug } from "../src/lib/crestSlug.mjs";

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
 * Names that are probably the same club spelled two ways.
 *
 * Project 01 carries Transfermarkt naming ("Arsenal FC") and project 03 carries
 * FBref naming ("Arsenal"); only 8 of them match exactly. This does NOT merge
 * anything -- the app still asks for one file per name it is handed -- it only
 * reports the collision, because supplying 43 files for 31 clubs is a symptom
 * rather than a task.
 */
function collisionKey(club) {
  const explicit = {
    "manchester utd": "manchester united",
    wolves: "wolverhampton wanderers",
    brighton: "brighton and hove albion",
    spurs: "tottenham hotspur",
  };
  const base = club
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/\b(fc|afc)\b/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
  return explicit[base] ?? base;
}

const rows = clubs.map((club) => {
  const slug = crestSlug(club);
  return { club, slug, have: present.has(slug) };
});
const have = rows.filter((r) => r.have);
const missing = rows.filter((r) => !r.have);

// A file that matches no club is worth surfacing: it is a typo or a club that
// left the dataset, and either way it will never be requested.
const unmatched = [...present].filter((s) => !rows.some((r) => r.slug === s));

// Group the raw names that look like one club under two spellings.
const groups = new Map();
for (const r of rows) {
  const k = collisionKey(r.club);
  if (!groups.has(k)) groups.set(k, []);
  groups.get(k).push(r);
}
const collisions = [...groups.values()].filter((g) => g.length > 1);

if (asJson) {
  console.log(
    JSON.stringify(
      {
        total: rows.length,
        distinctClubs: groups.size,
        have: have.length,
        missing: missing.map((r) => r.slug),
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
    `\n  Crest coverage — ${have.length}/${rows.length} clubs have artwork\n`,
  );
  if (!exists) {
    console.log(`  ${CRESTS_DIR} does not exist yet; every club is on the monogram fallback.\n`);
  }
  for (const r of rows) {
    console.log(
      `  ${r.have ? "have" : "  — "}  ${r.club.padEnd(pad)}  ${r.slug}.svg`,
    );
  }
  if (unmatched.length) {
    console.log(`\n  Files matching no club in the dataset (never requested):`);
    for (const s of unmatched) console.log(`        ${s}.svg`);
  }
  if (collisions.length) {
    console.log(
      `
  ${collisions.length} club${collisions.length === 1 ? "" : "s"} appear under more than one name, so each currently needs a`,
    );
    console.log(
      `  file per spelling. ${rows.length} names cover ~${groups.size} real clubs:
`,
    );
    for (const g of collisions) {
      console.log(`        ${g.map((r) => `${r.slug}.svg`).join("   =   ")}`);
    }
    console.log(
      `
  Project 01 carries Transfermarkt naming and project 03 carries FBref
` +
        `  naming. Until an alias map exists, the same club also renders a
` +
        `  different monogram in Value than in Style.`,
    );
  }

  console.log(
    missing.length
      ? `\n  ${missing.length} still on the typographic monogram.\n`
      : `\n  Complete — no club is falling back.\n`,
  );
}

process.exit(missing.length ? 1 : 0);
