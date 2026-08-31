/**
 * The landing page. Persuade mode, broadsheet density (PRODUCT.md, DESIGN.md §6.1).
 *
 * PRODUCT.md's ordering rule governs this page and is easy to get wrong in one
 * specific way: credibility leads, but the tools are never gated. So the three
 * readings and the three links sit in the first viewport together. A visitor who
 * wants to skip the argument does not have to scroll past it.
 *
 * The refusal counts are a HEADLINE here, not a caveat at the bottom. That is
 * the whole positioning: 163 of 661 players get no estimate and 1,649 of 4,616
 * matches get no forecast, and a product that leads with that is making a claim
 * a competitor cannot cheaply copy.
 *
 * Every figure is read from /api/meta at request time. Nothing on this page is
 * typed in (§2.3) -- including the refusal counts, which are differences of
 * served numbers rather than remembered ones.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type AppMeta, type ToolMeta } from "../lib/api";
import { num } from "../lib/format";
import { Notice } from "../components/ui/Sheet";

interface Headline {
  id: string;
  name: string;
  technique: string;
  figure: string;
  caption: string;
  to: string;
}

function n(o: unknown, k: string): number | null {
  if (typeof o !== "object" || o === null) return null;
  const v = (o as Record<string, unknown>)[k];
  return typeof v === "number" ? v : null;
}

export function Landing() {
  const [meta, setMeta] = useState<AppMeta | null>(null);
  const [valueMeta, setValueMeta] = useState<ToolMeta | null>(null);
  const [matchMeta, setMatchMeta] = useState<ToolMeta | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.meta(), api.value.meta(), api.match.meta()])
      .then(([m, v, mm]) => {
        setMeta(m);
        setValueMeta(v);
        setMatchMeta(mm);
      })
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <Notice title="Backend unavailable">
        <p style={{ maxWidth: "58ch" }}>
          {error}. The API should be running on 127.0.0.1:8000.
        </p>
      </Notice>
    );
  }

  const headlines: Headline[] = [];
  if (meta) {
    for (const t of meta.tools) {
      const h = t.headline;
      if (t.id === "value") {
        const r2 = n(h, "cv_r2_mean");
        const sd = n(h, "cv_r2_std");
        if (r2 !== null && sd !== null)
          headlines.push({
            id: t.id,
            name: t.name,
            technique: t.technique,
            figure: `R² ${num(r2, 3)} ± ${num(sd, 3)}`,
            caption: "cross-validated, log space",
            to: "/value",
          });
      } else if (t.id === "match") {
        const acc = n(h, "accuracy");
        const base = n(h, "baseline_accuracy");
        if (acc !== null && base !== null)
          headlines.push({
            id: t.id,
            name: t.name,
            technique: t.technique,
            figure: `${num(acc, 3)} vs ${num(base, 3)}`,
            caption: "against always-predict-home",
            to: "/match",
          });
      } else {
        const sil = n(h, "silhouette");
        if (sil !== null)
          headlines.push({
            id: t.id,
            name: t.name,
            technique: t.technique,
            figure: `silhouette ${num(sil, 3)}`,
            caption: "below 0.25, the conventional threshold",
            to: "/style",
          });
      }
    }
  }

  // Refusals, computed from served counts rather than remembered.
  const listed = n(valueMeta?.criteria, "players_listed");
  const modelled = n(valueMeta?.criteria, "players_modelled");
  const refused = listed !== null && modelled !== null ? listed - modelled : null;
  const fc = n(matchMeta?.coverage, "forecasts_available");
  const total = n(matchMeta?.coverage, "matches_total");
  const noForecast = fc !== null && total !== null ? total - fc : null;

  return (
    <div>
      <h1
        className="font-display"
        style={{
          fontSize: "var(--b-display)",
          lineHeight: 0.95,
          letterSpacing: "-0.012em",
          margin: 0,
          maxWidth: "15ch",
        }}
      >
        Three models that tell you when they don’t know.
      </h1>

      <p
        style={{
          fontSize: "var(--b-lead)",
          lineHeight: 1.5,
          color: "var(--ink-700)",
          maxWidth: "54ch",
          marginTop: "var(--s-4)",
        }}
      >
        Market value, match outcome and playing-style clusters for the Premier
        League — each shown with what it cannot do.
      </p>

      <hr className="rule" style={{ margin: "var(--s-6) 0 var(--s-5)" }} />

      {/* Readings and links together: the ordering rule is about sequence, not
          about gating (PRODUCT.md). */}
      <div className="grid gap-6 md:grid-cols-3">
        {headlines.map((h) => (
          <div key={h.id}>
            <div
              className="font-mono"
              style={{ fontSize: "var(--t-figure)", color: "var(--ink-900)" }}
            >
              {h.figure}
            </div>
            <div
              className="mt-1"
              style={{ fontSize: "var(--b-caption)", color: "var(--ink-500)" }}
            >
              {h.caption}
            </div>
            <Link
              to={h.to}
              className="hoverable mt-3 inline-block"
              style={{
                fontSize: "var(--t-body)",
                color: "var(--ink-900)",
                borderBottom: "var(--rule-w) solid var(--accent)",
                paddingBottom: "1px",
              }}
            >
              {h.name} →
            </Link>
            <div
              className="font-mono mt-1"
              style={{ fontSize: "var(--t-micro)", color: "var(--ink-300)" }}
            >
              {h.technique}
            </div>
          </div>
        ))}
      </div>

      <hr className="rule" style={{ margin: "var(--s-6) 0 var(--s-5)" }} />

      {refused !== null && noForecast !== null && (
        <div>
          <p
            className="font-display"
            style={{
              fontSize: "var(--b-heading)",
              lineHeight: 1.2,
              margin: 0,
              maxWidth: "24ch",
            }}
          >
            {refused.toLocaleString()} of {listed?.toLocaleString()} players get
            no estimate.
            <br />
            {noForecast.toLocaleString()} of {total?.toLocaleString()} matches get
            no forecast.
          </p>
          <p
            style={{
              fontSize: "var(--b-body)",
              lineHeight: 1.6,
              color: "var(--ink-700)",
              maxWidth: "56ch",
              marginTop: "var(--s-4)",
            }}
          >
            Not gaps. Both are the models declining to answer outside the range
            they were tested on — the first because per-90 rates stop measuring
            anything below about a season of football, the second because a
            forecast for a season the model trained on would report roughly twice
            the accuracy it actually has.
          </p>
          <Link
            to="/about"
            className="hoverable mt-4 inline-block"
            style={{
              fontSize: "var(--t-body)",
              color: "var(--ink-900)",
              borderBottom: "var(--rule-w) solid var(--accent)",
              paddingBottom: "1px",
            }}
          >
            How these models work, and where they fail →
          </Link>
        </div>
      )}
    </div>
  );
}
