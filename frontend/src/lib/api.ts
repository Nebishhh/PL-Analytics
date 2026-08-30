/**
 * Typed client over the real backend.
 *
 * Types come from api-types.d.ts, which is GENERATED from the running
 * backend's /openapi.json. Hand-written types would be a third source of truth
 * after API.md and the Pydantic models -- the drift API.md §0 exists to
 * prevent. Regenerate with `npm run gen:types`.
 *
 * WHY THE NARROWED UNIONS BELOW
 *   OpenAPI cannot express "estimate is present exactly when status is ok", so
 *   the generated ValueEstimateResponse has an optional `estimate` and a
 *   `status` of "ok" | "not_calibrated". Read literally, a component could
 *   render `estimate.point_eur` after an optional-chain and silently show
 *   nothing for a refused player.
 *
 *   Splitting each response into its real variants makes the refusal path
 *   impossible to skip: narrowing on `status` is the only way to reach
 *   `estimate`, so forgetting to handle refusal is a compile error rather
 *   than a blank panel.
 */

import type { components } from "./api-types";

type Schemas = components["schemas"];

/* -- 01 value ------------------------------------------------------------- */

type ValueRaw = Schemas["ValueEstimateResponse"];

export type ValueOk = Omit<ValueRaw, "status" | "estimate" | "inputs"> & {
  status: "ok";
  estimate: NonNullable<ValueRaw["estimate"]>;
  inputs: NonNullable<ValueRaw["inputs"]>;
};

export type ValueRefused = Omit<ValueRaw, "status" | "calibration"> & {
  status: "not_calibrated";
  estimate: null;
  calibration: NonNullable<ValueRaw["calibration"]>;
};

/** Narrow on `status` before touching `estimate`. */
export type ValueEstimate = ValueOk | ValueRefused;

export type ValuePlayerListItem = Schemas["ValuePlayerListItem"];
export type ToolMeta = Schemas["ToolMeta"];

/* -- 02 match ------------------------------------------------------------- */

type MatchRaw = Schemas["HeldOutForecastResponse"];

export type ForecastOk = Omit<MatchRaw, "status" | "forecast" | "baseline"> & {
  status: "ok";
  forecast: NonNullable<MatchRaw["forecast"]>;
  baseline: NonNullable<MatchRaw["baseline"]>;
};

export type ForecastOutOfScope = Omit<MatchRaw, "status" | "coverage"> & {
  status: "out_of_scope";
  forecast: null;
  coverage: NonNullable<MatchRaw["coverage"]>;
};

export type HeldOutForecast = ForecastOk | ForecastOutOfScope;

/* -- 03 style ------------------------------------------------------------- */

export type StyleAssignment = Schemas["StyleAssignmentResponse"];
export type StylePlayerListItem = Schemas["StylePlayerListItem"];
export type MatchListItem = Schemas["MatchListItem"];

/* -- /about ---------------------------------------------------------------- */

export type AppMeta = Schemas["AppMeta"];
export type ToolSummary = Schemas["ToolSummary"];
export type Licensing = Schemas["Licensing"];

/* -- transport ------------------------------------------------------------ */

export class ApiError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    // A genuine failure. Refusal and out-of-scope arrive as HTTP 200 with a
    // status discriminant and must never reach here (API.md §2).
    throw new ApiError(res.status, `${res.status} on ${path}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => get<{ status: string }>("/health"),

  /** Aggregate headline + limitation + licence material, for /about. */
  meta: () => get<AppMeta>("/meta"),

  value: {
    meta: () => get<ToolMeta>("/value/meta"),
    players: (params?: { club?: string; position?: string }) => {
      const q = new URLSearchParams();
      if (params?.club) q.set("club", params.club);
      if (params?.position) q.set("position", params.position);
      const qs = q.toString();
      return get<ValuePlayerListItem[]>(`/value/players${qs ? `?${qs}` : ""}`);
    },
    estimate: (playerId: number) =>
      get<ValueEstimate>(`/value/players/${playerId}/estimate`),
  },

  match: {
    meta: () => get<ToolMeta>("/match/meta"),
    seasons: () => get<number[]>("/match/seasons"),
    clubs: (season: number) =>
      get<string[]>(`/match/clubs?season=${season}`),
    matches: (season: number, club?: string) => {
      const q = new URLSearchParams({ season: String(season) });
      if (club) q.set("club", club);
      return get<MatchListItem[]>(`/match/matches?${q}`);
    },
    /** Named for what it is: a stored forecast from a model that had not seen
     *  this season. Never computed per request (AGENTS.md §2.1). */
    heldOutForecast: (gameId: number) =>
      get<HeldOutForecast>(`/match/matches/${gameId}/held-out-forecast`),
  },

  style: {
    meta: () => get<ToolMeta>("/style/meta"),
    players: (position?: string) => {
      const qs = position ? `?position=${encodeURIComponent(position)}` : "";
      return get<StylePlayerListItem[]>(`/style/players${qs}`);
    },
    assignment: (slug: string) =>
      get<StyleAssignment>(`/style/players/${encodeURIComponent(slug)}/assignment`),
  },
};
