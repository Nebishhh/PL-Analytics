/**
 * Project 03, wired to the real backend.
 *
 * Ports the Streamlit app's optional Position filter, which matches ANY listed
 * position -- 84 of the 315 players carry two, so a first-token match would
 * hide 30 forwards from anyone filtering on FW (AGENTS.md §5).
 *
 * Players are addressed by the slug the API supplies, never one constructed
 * here: three players appear twice after mid-season transfers, so the
 * disambiguation rule has to live in one place and clients must use what they
 * are given.
 */

import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  api,
  type StyleAssignment,
  type StylePlayerListItem,
  type ToolMeta,
} from "../../lib/api";
import { num } from "../../lib/format";
import { STYLE } from "../../lib/copy";
import { Combobox, type ComboOption } from "../../components/ui/Combobox";
import { Disclosure } from "../../components/ui/Disclosure";
import { Panel } from "../../components/ui/Panel";
import { StylePanel } from "./StylePanel";

const ALL = "__all__";
const POSITIONS = ["DF", "MF", "FW"];

export function StyleTool() {
  const { slug } = useParams();
  const navigate = useNavigate();

  const [players, setPlayers] = useState<StylePlayerListItem[] | null>(null);
  const [meta, setMeta] = useState<ToolMeta | null>(null);
  const [position, setPosition] = useState(ALL);
  const [result, setResult] = useState<StyleAssignment | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.style.meta().then(setMeta).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    api.style
      .players(position === ALL ? undefined : position)
      .then(setPlayers)
      .catch((e) => setError(String(e)));
  }, [position]);

  useEffect(() => {
    if (!slug) {
      setResult(null);
      return;
    }
    setResult(null);
    api.style.assignment(slug).then(setResult).catch((e) => setError(String(e)));
  }, [slug]);

  const options: ComboOption[] = useMemo(
    () =>
      (players ?? []).map((p) => ({
        id: p.slug,
        label: p.name,
        keywords: `${p.club} ${p.pos}`,
        hint: p.pos,
      })),
    [players],
  );

  const q = (meta?.quality ?? {}) as Record<string, unknown>;
  const silhouette = typeof q.silhouette === "number" ? q.silhouette : null;

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
          Activity profile
        </h1>
        <p className="font-prose mt-2 text-ink-300">
          Which activity cluster a player was grouped into — and how solid that
          grouping is. Activity profiles, not playing styles: this data has no
          passing, carrying or expected-goals columns.
        </p>
      </div>

      {/* The two-tier trust finding, stated once at the top rather than per
          player, because it qualifies every answer the tool can give. */}
      {silhouette !== null && (
        <Panel>
          <p className="font-prose text-ink-200">
            <strong className="text-ink-100">
              This clustering is most confident where it is least informative.
            </strong>
          </p>
          <div className="mt-2">
            <Disclosure label="Why does this matter?">
              <p>
                The two best-separated clusters are the ones that largely restate
                position — one holds 27 of the 28 pure forwards, another 73% of
                all defenders. The two that split defenders and midfielders by
                what they do rather than where they line up are the worst
                separated, and one of them contains 15 of the 19 players who sit
                closer to another cluster's members than their own.
              </p>
              <p className="mt-3">{STYLE.weakStructure(num(silhouette, 3))}</p>
            </Disclosure>
          </div>
        </Panel>
      )}

      <Panel>
        <div className="grid gap-4 md:grid-cols-[1fr_3fr]">
          <div>
            <div className="label mb-1">Position</div>
            <select
              value={position}
              onChange={(e) => {
                setPosition(e.target.value);
                navigate("/style");
              }}
              className="w-full rounded px-3 py-2"
              style={{
                background: "var(--ink-800)",
                border: "1px solid var(--ink-700)",
                color: "var(--ink-100)",
                fontSize: "var(--t-body)",
              }}
            >
              <option value={ALL}>All positions</option>
              {POSITIONS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <Combobox
            label="Player"
            options={options}
            value={slug ?? null}
            onChange={(id) => navigate(`/style/${id}`)}
            placeholder={
              players
                ? `Search ${players.length} player${players.length === 1 ? "" : "s"}…`
                : "Loading…"
            }
          />
        </div>
      </Panel>

      {result ? (
        <StylePanel data={result} meta={meta} />
      ) : (
        <Panel>
          <p className="font-prose text-ink-300">
            {slug
              ? "Loading…"
              : /* No minutes figure here on purpose. Project 03's artefact does
                   not record its minutes floor -- that lives in clean.py -- so
                   the frontend has no honest source for the number and must
                   not assert one (AGENTS.md §2.3). Adding min_pl_minutes to the
                   03 artefact would be a §0.1 extension if the figure is
                   wanted. */
                `Pick a player to see which cluster they were assigned to, and how solid that assignment is. ${
                  players?.length ?? "…"
                } outfielders are here — goalkeepers are excluded, since their statistical profile shares almost nothing with outfield players.`}
          </p>
        </Panel>
      )}
    </div>
  );
}
