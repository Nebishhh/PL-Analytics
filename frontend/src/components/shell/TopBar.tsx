/**
 * Three tools under one shell (AGENTS.md §5), not one narrative in three
 * chapters. Each tool owns a route so it is linkable and the back button
 * works -- which is why this is react-router rather than Radix Tabs.
 *
 * The accent rule lives here: a tool's colour marks the ACTIVE NAV ITEM and
 * nothing else. Hue carries navigation; the semantic scale carries meaning.
 * These are raw custom properties rather than Tailwind utilities precisely so
 * that no `bg-tool-01` class exists to be applied to a chart by autocomplete.
 *
 * The active state was a 2px underline and nothing else, which is legible but
 * timid -- the one place the system is allowed to use hue with confidence was
 * using it apologetically. The active item now also takes the accent as its
 * text colour and a tinted ground. Still wayfinding, still nowhere near a
 * mark.
 */

import { NavLink } from "react-router-dom";

const TOOLS = [
  { to: "/value", label: "Value", accent: "var(--tool-01)" },
  { to: "/match", label: "Match", accent: "var(--tool-02)" },
  { to: "/style", label: "Style", accent: "var(--tool-03)" },
];

export function TopBar() {
  return (
    <header
      className="sticky top-0 z-40"
      style={{
        background: "var(--ink-900)",
        borderBottom: "1px solid var(--ink-700)",
      }}
    >
      <div className="mx-auto flex max-w-[1100px] items-center gap-8 px-6 py-4">
        <span
          className="font-mono text-ink-100"
          style={{ fontSize: "var(--t-body)", letterSpacing: "0.08em" }}
        >
          PL·ANALYTICS
        </span>

        <nav className="flex gap-1">
          {TOOLS.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className="hoverable rounded-t px-3 py-1.5"
              style={({ isActive }) => ({
                fontSize: "var(--t-body)",
                color: isActive ? t.accent : "var(--ink-300)",
                background: isActive
                  ? `color-mix(in srgb, ${t.accent} 10%, transparent)`
                  : "transparent",
                borderBottom: isActive
                  ? `2px solid ${t.accent}`
                  : "2px solid transparent",
              })}
            >
              {t.label}
            </NavLink>
          ))}
        </nav>

        {/* Right-aligned and unaccented, per DESIGN.md §9's shell sketch: it is
            not a fourth tool, so it does not take a tool colour. */}
        <NavLink
          to="/about"
          className="hoverable ml-auto rounded px-3 py-1.5"
          style={({ isActive }) => ({
            fontSize: "var(--t-body)",
            color: isActive ? "var(--ink-100)" : "var(--ink-300)",
            borderBottom: isActive
              ? "2px solid var(--ink-400)"
              : "2px solid transparent",
          })}
        >
          about
        </NavLink>
      </div>
    </header>
  );
}
