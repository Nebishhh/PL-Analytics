/**
 * Project 02, wired to the real backend.
 *
 * Ports the Streamlit app's Season -> Club -> Match chain exactly, including
 * that the club filter matches EITHER side and marks each fixture (H) or (A).
 *
 * Only seasons with a held-out forecast are listed, which mirrors the
 * Streamlit app's inner join. The 1,649 matches from earlier seasons are not
 * hidden silently -- the empty state says why they are absent -- and a direct
 * game_id in the URL still resolves, so a bookmarked out-of-scope match
 * renders its explanation rather than 500-ing.
 */

import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  api,
  type HeldOutForecast,
  type MatchListItem,
  type ToolMeta,
} from "../../lib/api";
import { Combobox, type ComboOption } from "../../components/ui/Combobox";
import { Select } from "../../components/ui/Select";
import { Notice, Sheet, Well } from "../../components/ui/Sheet";
import { MatchPanel } from "./MatchPanel";

const ALL = "__all__";

export function MatchTool() {
  const { gameId } = useParams();
  const navigate = useNavigate();

  const [seasons, setSeasons] = useState<number[]>([]);
  const [season, setSeason] = useState<number | null>(null);
  const [clubs, setClubs] = useState<string[]>([]);
  const [club, setClub] = useState(ALL);
  const [matches, setMatches] = useState<MatchListItem[]>([]);
  const [meta, setMeta] = useState<ToolMeta | null>(null);
  const [result, setResult] = useState<HeldOutForecast | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.match.seasons(), api.match.meta()])
      .then(([s, m]) => {
        setSeasons(s);
        setMeta(m);
        setSeason(s[s.length - 1] ?? null);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (season === null) return;
    setClub(ALL);
    api.match.clubs(season).then(setClubs).catch((e) => setError(String(e)));
  }, [season]);

  useEffect(() => {
    if (season === null) return;
    api.match
      .matches(season, club === ALL ? undefined : club)
      .then(setMatches)
      .catch((e) => setError(String(e)));
  }, [season, club]);

  useEffect(() => {
    if (!gameId) {
      setResult(null);
      return;
    }
    setResult(null);
    api.match
      .heldOutForecast(Number(gameId))
      .then(setResult)
      .catch((e) => setError(String(e)));
  }, [gameId]);

  const options: ComboOption[] = useMemo(
    () =>
      matches.map((m) => ({
        id: String(m.game_id),
        // No score in the label: putting the result in the selector would hand
        // over the answer before the model has spoken.
        label: `${m.date} · ${m.home_club} vs ${m.away_club}`,
        keywords: `${m.home_club} ${m.away_club}`,
        hint: m.venue ?? undefined,
      })),
    [matches],
  );

  if (error) {
    return (
      <Notice title="Backend unavailable">
        <p className="text-ink-700">
          {error}. The API should be running on 127.0.0.1:8000.
        </p>
      </Notice>
    );
  }

  const coverage = (meta?.coverage ?? {}) as Record<string, unknown>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-ink-900" style={{ fontSize: "var(--t-title)", lineHeight: 1.2, fontWeight: 600 }}>
          Match forecast
        </h1>
        <p className="mt-2 text-ink-500" style={{ maxWidth: "58ch", lineHeight: 1.55 }}>
          Win, draw or loss for a Premier League fixture — forecast by a model
          that had never seen that season.
        </p>
      </div>

      <Well>
        <div className="grid gap-4 md:grid-cols-[1fr_1.4fr_2.6fr]">
            <Select
              label="Season"
              value={season === null ? "" : String(season)}
              onChange={(v) => {
                setSeason(Number(v));
                navigate("/match");
              }}
              options={seasons.map((x) => ({ id: String(x), label: String(x) }))}
            />

            <Combobox
              label="Club"
              options={[
                { id: ALL, label: "All clubs" },
                ...clubs.map((c) => ({ id: c, label: c })),
              ]}
              value={club}
              onChange={(v) => {
                setClub(v);
                navigate("/match");
              }}
              placeholder="All clubs"
            />

          <Combobox
            label="Match"
            options={options}
            value={gameId ?? null}
            onChange={(id) => navigate(`/match/${id}`)}
            placeholder={`Search ${matches.length} match${matches.length === 1 ? "" : "es"}…`}
          />
        </div>
      </Well>

      {result ? (
        <MatchPanel data={result} meta={meta} />
      ) : (
        <Sheet>
          <p className="text-ink-500">
            {gameId
              ? "Loading…"
              : `Pick a match to see the forecast. ${
                  typeof coverage.forecasts_available === "number"
                    ? coverage.forecasts_available.toLocaleString()
                    : "…"
                } of ${
                  typeof coverage.matches_total === "number"
                    ? coverage.matches_total.toLocaleString()
                    : "…"
                } matches have one; seasons before ${
                  Array.isArray(coverage.seasons_available)
                    ? (coverage.seasons_available as number[])[0]
                    : "…"
                } are not listed because they have no earlier seasons to train on.`}
          </p>
        </Sheet>
      )}
    </div>
  );
}
