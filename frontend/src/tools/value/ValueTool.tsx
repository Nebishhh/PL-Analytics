/**
 * Project 01. Blueprint density (Operate).
 *
 * Ports the Streamlit app's controls exactly: optional Club and Position
 * filters defaulting to "All", then a searchable player picker.
 *
 * Sub-threshold players stay in the list and are marked, never hidden. They are
 * there precisely so the refusal can be shown -- removing them would hide the
 * limitation rather than communicate it.
 *
 * Club is a Combobox rather than a Select, decided in Step 5: 30-plus options
 * is past the point where scanning beats searching, and Select is left to the
 * genuinely short lists.
 */

import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  api,
  classifyError,
  type ToolMeta,
  type ValueEstimate,
  type ValuePlayerListItem,
} from "../../lib/api";
import { Combobox, type ComboOption } from "../../components/ui/Combobox";
import { Select } from "../../components/ui/Select";
import { Notice, Section, Well } from "../../components/ui/Sheet";
import { ValuePanel } from "./ValuePanel";

const ALL = "__all__";

export function ValueTool() {
  // The selected player lives in the path, not in component state, so a
  // reading is linkable and the back button works -- the same contract
  // /match/:gameId and /style/:slug already had.
  const { playerId } = useParams();
  const navigate = useNavigate();
  const selected = playerId ? Number(playerId) : null;

  const [players, setPlayers] = useState<ValuePlayerListItem[] | null>(null);
  const [meta, setMeta] = useState<ToolMeta | null>(null);
  const [club, setClub] = useState(ALL);
  const [position, setPosition] = useState(ALL);
  const [result, setResult] = useState<ValueEstimate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    Promise.all([api.value.players(), api.value.meta()])
      .then(([p, m]) => {
        setPlayers(p);
        setMeta(m);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (selected === null) {
      setResult(null);
      return;
    }
    setResult(null);
    api.value.estimate(selected)
      .then(setResult)
      .catch((e) => { const c = classifyError(e); if (c.notFound) setMissing(true); else setError(c.message); });
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

  const clubOptions: ComboOption[] = [
    { id: ALL, label: "All clubs" },
    ...clubs.map((c) => ({ id: c, label: c })),
  ];

  const bandCoverage =
    meta && typeof meta.quality === "object" && meta.quality !== null
      ? ((meta.quality as Record<string, unknown>).band_coverage as
          | { out_of_fold: number }
          | undefined)?.out_of_fold ?? null
      : null;

  if (missing) {
    return (
      <Notice title="No such player">
        <p style={{ maxWidth: "58ch" }}>
          This URL names a player that is not in the dataset. The backend is
          answering normally — the identifier just does not resolve.{" "}
          <Link to="/value" style={{ borderBottom: "var(--rule-w) solid var(--accent)" }}>
            Start from the picker
          </Link>
          .
        </p>
      </Notice>
    );
  }

  if (error) {
    return (
      <Notice title="Backend unavailable">
        <p style={{ maxWidth: "58ch" }}>
          {error}. The API should be running on 127.0.0.1:8000.
        </p>
      </Notice>
    );
  }

  return (
    <div>
      <header style={{ marginBottom: "var(--s-6)" }}>
        <h1
          style={{
            fontSize: "var(--t-title)",
            lineHeight: 1.2,
            margin: 0,
            fontWeight: 600,
          }}
        >
          Market value estimate
        </h1>
        <p
          style={{
            marginTop: "var(--s-2)",
            color: "var(--ink-700)",
            maxWidth: "58ch",
            lineHeight: 1.55,
          }}
        >
          What a Premier League player is worth, from his career-to-date league
          record — and how much of that estimate to trust.
        </p>
      </header>

      <Well>
        <div className="grid gap-4 md:grid-cols-[2fr_1fr_2fr]">
          <Combobox
            label="Club"
            options={clubOptions}
            value={club}
            onChange={(id) => { setClub(id); navigate("/value"); }}
            placeholder="All clubs"
          />
          <Select
            label="Position"
            value={position}
            onChange={(v) => { setPosition(v); navigate("/value"); }}
            options={[
              { id: ALL, label: "All positions" },
              ...positions.map((p) => ({ id: p, label: p })),
            ]}
          />
          <Combobox
            label="Player"
            options={options}
            value={selected === null ? null : String(selected)}
            onChange={(id) => navigate(`/value/${id}`)}
            placeholder={
              players
                ? `Search ${shortlist.length} player${shortlist.length === 1 ? "" : "s"}…`
                : "Loading…"
            }
          />
        </div>
      </Well>

      <div style={{ marginTop: "var(--s-7)" }}>
        {result ? (
          <ValuePanel data={result} bandCoverage={bandCoverage} />
        ) : (
          <Section ruled>
            <p style={{ color: "var(--ink-500)", maxWidth: "60ch" }}>
              {selected === null
                ? `Pick a player to see an estimate. ${players?.length ?? "…"} Premier League players are available — including those the model declines to price, which are marked in the list.`
                : "Loading…"}
            </p>
          </Section>
        )}
      </div>
    </div>
  );
}
