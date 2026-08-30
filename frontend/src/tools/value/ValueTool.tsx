/**
 * Project 01, wired to the real backend.
 *
 * Ports the Streamlit app's controls exactly (AGENTS.md §5): optional Club and
 * Position filters defaulting to "All", then a searchable player picker.
 *
 * Sub-threshold players stay in the list and are marked, never hidden. They
 * are there precisely so the refusal can be shown -- removing them would hide
 * the limitation rather than communicate it.
 */

import { useEffect, useMemo, useState } from "react";
import { api, type ToolMeta, type ValueEstimate, type ValuePlayerListItem } from "../../lib/api";
import { Combobox, type ComboOption } from "../../components/ui/Combobox";
import { Panel } from "../../components/ui/Panel";
import { ValuePanel } from "./ValuePanel";

const ALL = "__all__";

export function ValueTool() {
  const [players, setPlayers] = useState<ValuePlayerListItem[] | null>(null);
  const [meta, setMeta] = useState<ToolMeta | null>(null);
  const [club, setClub] = useState(ALL);
  const [position, setPosition] = useState(ALL);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<ValueEstimate | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.value.players(), api.value.meta()])
      .then(([p, m]) => {
        setPlayers(p);
        setMeta(m);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (selected === null) return;
    setResult(null);
    api.value.estimate(selected).then(setResult).catch((e) => setError(String(e)));
  }, [selected]);

  const clubs = useMemo(
    () => [...new Set((players ?? []).map((p) => p.club))].sort(),
    [players],
  );
  const positions = useMemo(
    () => [...new Set((players ?? []).map((p) => p.position))].sort(),
    [players],
  );

  const shortlist = useMemo(
    () =>
      (players ?? []).filter(
        (p) =>
          (club === ALL || p.club === club) &&
          (position === ALL || p.position === position),
      ),
    [players, club, position],
  );

  const options: ComboOption[] = shortlist.map((p) => ({
    id: String(p.player_id),
    label: p.name,
    keywords: `${p.club} ${p.position}`,
    // The refusal is visible before selection, not a surprise after it.
    hint: p.eligible ? undefined : "not calibrated",
    hintMuted: true,
  }));

  const bandCoverage =
    meta && typeof meta.quality === "object" && meta.quality !== null
      ? ((meta.quality as Record<string, unknown>).band_coverage as
          | { out_of_fold: number }
          | undefined)?.out_of_fold ?? null
      : null;

  if (error) {
    return (
      <Panel title="Backend unavailable">
        <p className="font-prose text-ink-200">
          {error}. The API should be running on 127.0.0.1:8000.
        </p>
      </Panel>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-ink-100" style={{ fontSize: "var(--t-display)" }}>
          Market value estimate
        </h1>
        <p className="font-prose mt-2 text-ink-300">
          What a Premier League player is worth, from his career-to-date league
          record — and how much of that estimate to trust.
        </p>
      </div>

      <Panel>
        <div className="grid gap-4 md:grid-cols-[1fr_1fr_2fr]">
          <SimpleSelect
            label="Club"
            value={club}
            onChange={setClub}
            options={[{ id: ALL, label: "All clubs" }, ...clubs.map((c) => ({ id: c, label: c }))]}
          />
          <SimpleSelect
            label="Position"
            value={position}
            onChange={setPosition}
            options={[
              { id: ALL, label: "All positions" },
              ...positions.map((p) => ({ id: p, label: p })),
            ]}
          />
          <Combobox
            label="Player"
            options={options}
            value={selected === null ? null : String(selected)}
            onChange={(id) => setSelected(Number(id))}
            placeholder={
              players
                ? `Search ${shortlist.length} player${shortlist.length === 1 ? "" : "s"}…`
                : "Loading…"
            }
          />
        </div>
      </Panel>

      {result ? (
        <ValuePanel data={result} bandCoverage={bandCoverage} />
      ) : (
        <Panel>
          <p className="font-prose text-ink-300">
            {selected === null
              ? `Pick a player to see an estimate. ${players?.length ?? "…"} Premier League players are available — including those the model declines to price, which are marked in the list.`
              : "Loading…"}
          </p>
        </Panel>
      )}
    </div>
  );
}

/** Short lists only. Under ~40 options there is nothing to search. */
function SimpleSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { id: string; label: string }[];
}) {
  return (
    <div>
      <div className="label mb-1">{label}</div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded px-3 py-2"
        style={{
          background: "var(--ink-800)",
          border: "1px solid var(--ink-700)",
          color: "var(--ink-100)",
          fontSize: "var(--t-body)",
        }}
      >
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
