/**
 * The masthead.
 *
 * There are no tool accents any more. The previous shell gave each tool its own
 * hue for wayfinding, which was three of the seven colours the old system spent;
 * the redesign has one. So the active item is marked by the accent and by an
 * ink rule under it, and the three tools are peers rather than three brands
 * sharing a bar.
 *
 * The double rule beneath is the masthead rule a broadsheet puts under its
 * nameplate. It is the one place the accent is allowed to run the full width,
 * because that is the job it does on paper.
 */

import { NavLink } from "react-router-dom";

const TOOLS = [
  { to: "/value", label: "Value" },
  { to: "/match", label: "Match" },
  { to: "/style", label: "Style" },
];

function item({ isActive }: { isActive: boolean }) {
  return {
    fontSize: "var(--t-body)",
    color: isActive ? "var(--ink-900)" : "var(--ink-500)",
    borderBottom: isActive
      ? "2px solid var(--accent)"
      : "2px solid transparent",
    paddingBottom: "2px",
  };
}

export function TopBar() {
  return (
    <header
      className="sticky top-0 z-40"
      style={{ background: "var(--paper-100)" }}
    >
      <div className="mx-auto flex max-w-[1100px] items-baseline gap-8 px-6 py-4">
        <NavLink
          to="/"
          className="font-mono"
          style={{
            fontSize: "var(--t-body)",
            letterSpacing: "0.10em",
            color: "var(--ink-900)",
          }}
        >
          PL·ANALYTICS
        </NavLink>

        <nav className="flex gap-5">
          {TOOLS.map((t) => (
            <NavLink key={t.to} to={t.to} className="hoverable" style={item}>
              {t.label}
            </NavLink>
          ))}
        </nav>

        <NavLink to="/about" className="hoverable ml-auto" style={item}>
          about
        </NavLink>
      </div>

      {/* Masthead rule: heavy ink over a hairline, the way a nameplate is ruled
          off from the columns beneath it. */}
      <div style={{ borderTop: "2px solid var(--ink-900)" }} />
      <div
        style={{
          borderTop: "var(--rule-w) solid var(--rule-200)",
          marginTop: "2px",
        }}
      />
    </header>
  );
}
