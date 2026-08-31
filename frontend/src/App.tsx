import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { TopBar } from "./components/shell/TopBar";
import { ValueTool } from "./tools/value/ValueTool";
import { MatchTool } from "./tools/match/MatchTool";
import { StyleTool } from "./tools/style/StyleTool";
import { About } from "./pages/About";

/**
 * Which accent the chrome wears, by route.
 *
 * Set once here as a custom property rather than threaded through props, so a
 * component can pick it up for a focus ring or an active state without being
 * handed a colour. Marks are not given it and must not read it -- V1 -- which
 * is why the marks/ directory is grepped for `--accent` in verification.
 */
const ACCENT: Record<string, string> = {
  "/value": "var(--tool-01)",
  "/match": "var(--tool-02)",
  "/style": "var(--tool-03)",
};

function accentFor(pathname: string): string {
  const key = Object.keys(ACCENT).find((k) => pathname.startsWith(k));
  // /about is not a fourth tool, so it stays unaccented.
  return key ? ACCENT[key]! : "var(--ink-400)";
}

export default function App() {
  const location = useLocation();

  return (
    <div
      className="min-h-full"
      style={{ ["--accent" as string]: accentFor(location.pathname) }}
    >
      <TopBar />
      <main className="mx-auto max-w-[1100px] px-6 py-10">
        {/* Keyed on the route so the cross-fade replays on each tool change.
            Opacity only -- see base.css. */}
        <div key={location.pathname.split("/")[1] ?? ""} className="route-in">
          <Routes location={location}>
            <Route path="/" element={<Navigate to="/value" replace />} />
            <Route path="/value" element={<ValueTool />} />
            <Route path="/match" element={<MatchTool />} />
            {/* game_id in the path so a fixture is linkable, and so a bookmarked
                out-of-scope match renders its explanation rather than 500-ing. */}
            <Route path="/match/:gameId" element={<MatchTool />} />
            <Route path="/style" element={<StyleTool />} />
            <Route path="/style/:slug" element={<StyleTool />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
