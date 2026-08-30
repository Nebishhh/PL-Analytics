/**
 * Project 03's reading.
 *
 * This tool has no refusal state -- every one of the 315 players has an
 * assignment -- but it has the opposite problem, and the harder one: a label
 * looks certain in a way a number does not. "Cluster 2" on a page reads as a
 * fact, and frequently it is not.
 *
 * So the tier is decided before anything renders and governs the wording, the
 * colour and the ORDER OF THE SENTENCE. For a contested player the rival is
 * named first, because leading with the assignment asserts what the geometry
 * does not support.
 */

import type { StyleAssignment, ToolMeta } from "../../lib/api";
import { num, ordinal, pct } from "../../lib/format";
import { COMMON, STYLE } from "../../lib/copy";
import { ZonedAxis, type AxisZone } from "../../components/marks/ZonedAxis";
import { Rail, Needle } from "../../components/marks/Rail";
import { Disclosure } from "../../components/ui/Disclosure";
import { Panel } from "../../components/ui/Panel";
import { StateChip } from "../../components/ui/StateChip";

const GROUP_LABEL: Record<string, string> = {
  ATTACKING_OUTPUT: "Attacking output",
  DEFENSIVE_ACTIVITY: "Defensive activity",
  DISCIPLINE: "Discipline",
};

export function StylePanel({
  data,
  meta,
}: {
  data: StyleAssignment;
  meta: ToolMeta | null;
}) {
  const a = data.assignment;
  const p = data.player as Record<string, unknown>;
  const q = (meta?.quality ?? {}) as Record<string, unknown>;
  const silhouette = typeof q.silhouette === "number" ? q.silhouette : null;
  const nPlayers = typeof q.n_players === "number" ? q.n_players : 315;

  const tierState =
    a.tier === "CONTESTED" ? "low" : a.tier === "BORDERLINE" ? "moderate" : "clear";

  const margin = num(a.margin_to_next, 3);

  // One sentence. Rival first when contested -- see the module docstring.
  const finding =
    a.tier === "CONTESTED" && a.negative_silhouette
      ? STYLE.contestedWithNegative(a.rival_cluster_name)
      : a.tier === "CONTESTED"
        ? STYLE.contested(a.rival_cluster_name, margin)
        : a.tier === "BORDERLINE"
          ? STYLE.borderline(a.rival_cluster_name, margin)
          : STYLE.placed(a.rival_cluster_name, num(a.margin_to_next, 2));

  const groups = [...new Set(data.rates.map((r) => r.group))];

  return (
    <Panel>
      <div className="mb-6">
        <h2 className="text-ink-100" style={{ fontSize: "var(--t-value)" }}>
          {String(p.name ?? "")}
        </h2>
        <div
          className="font-mono text-ink-300"
          style={{ fontSize: "var(--t-micro)" }}
        >
          {String(p.club ?? "")} · {String(p.pos ?? "")} ·{" "}
          {Number(p.age ?? 0).toFixed(0)} yrs ·{" "}
          {Number(p.minutes ?? 0).toLocaleString()} PL min
        </div>
      </div>

      <div className="mb-3">
        <div className="label mb-2">Assigned cluster</div>
        {/* Read from the artefact, never composed here. Terms like "inverted
            winger" would be claims about passing and carrying, and this
            dataset has no such columns (AGENTS.md §2.4). */}
        <div className="text-ink-100" style={{ fontSize: "var(--t-figure)", lineHeight: 1.35 }}>
          {a.cluster_name}
        </div>
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        <StateChip state={tierState}>{STYLE.tierChip[a.tier] ?? a.tier}</StateChip>
        {/* Its own chip, not folded into the tier: a negative silhouette is a
            different failure from a narrow margin, and only a handful of
            players trip both. A reader skimming must not miss it. */}
        {a.negative_silhouette && (
          <StateChip state="low">{STYLE.negativeSilhouetteChip}</StateChip>
        )}
        <StateChip state="null">
          {a.position_adjacent ? "Mostly restates position" : "Mixes positions"}
        </StateChip>
      </div>

      <ZonedAxis
        min={data.axis.min}
        max={data.axis.max}
        value={data.axis.value}
        zones={data.axis.zones as unknown as AxisZone[]}
        tier={a.tier}
      />

      <p className="font-prose mt-5 text-ink-200">{finding}</p>

      <div className="mt-3">
        <Disclosure label="What margin and silhouette each measure">
          <p>{STYLE.twoSignals}</p>
          {a.negative_silhouette && (
            <p className="mt-3">
              {STYLE.negativeSilhouetteDetail(
                num(a.silhouette, 3),
                19,
                nPlayers,
              )}
            </p>
          )}
          <p className="mt-3">
            {a.position_adjacent
              ? STYLE.positionAdjacent(
                  pct(a.cluster_position_share.share),
                  a.cluster_position_share.dominant,
                )
              : STYLE.positionMixed(
                  pct(a.cluster_position_share.share),
                  a.cluster_position_share.dominant,
                )}
          </p>
          <p className="mt-3">{STYLE.namingDetail}</p>
          {silhouette !== null && (
            <p className="mt-3">{STYLE.weakStructure(num(silhouette, 3))}</p>
          )}
        </Disclosure>
      </div>

      <p className="font-prose mt-4 text-ink-400" style={{ fontSize: "var(--t-body)" }}>
        {COMMON.positionHeldOut}
      </p>

      {/* The same rail again, third context: each rate as a percentile
          position rather than a bare number. */}
      <div className="mt-6 border-t pt-5" style={{ borderColor: "var(--ink-700)" }}>
        <div className="label mb-4">The ten rates that produced it</div>
        <div className="space-y-6">
          {groups.map((g) => (
            <div key={g}>
              <div className="label mb-3">{GROUP_LABEL[g] ?? g}</div>
              <div className="grid gap-4 md:grid-cols-2">
                {data.rates
                  .filter((r) => r.group === g)
                  .map((r) => (
                    <div key={r.key}>
                      <div className="mb-1 flex items-baseline justify-between">
                        <span className="text-ink-200" style={{ fontSize: "var(--t-body)" }}>
                          {r.label}
                        </span>
                        <span
                          className="font-mono text-ink-100"
                          style={{ fontSize: "var(--t-body)" }}
                        >
                          {num(r.value, 2)}
                          <span className="ml-2 text-ink-400">
                            {ordinal(r.percentile)} pct
                          </span>
                        </span>
                      </div>
                      <div style={{ ["--rail-h" as string]: "10px" }}>
                        <Rail ariaLabel={`${r.label}: ${ordinal(r.percentile)} percentile`}>
                          <Needle at={r.percentile / 100} state="clear" />
                        </Rail>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
}
