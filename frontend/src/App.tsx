import { Route, Routes, useLocation } from "react-router-dom";
import { TopBar } from "./components/shell/TopBar";
import { ValueTool } from "./tools/value/ValueTool";
import { MatchTool } from "./tools/match/MatchTool";
import { StyleTool } from "./tools/style/StyleTool";
import { About } from "./pages/About";
import { Landing } from "./pages/Landing";

/**
 * The shell. There is one accent for the whole site now rather than one per
 * tool, so nothing here varies by route except which nav item is marked.
 */
export default function App() {
  const location = useLocation();

  return (
    <div className="min-h-full">
      <TopBar />
      <main className="mx-auto max-w-[1100px] px-6" style={{ paddingTop: "var(--s-7)", paddingBottom: "var(--s-9)" }}>
        {/* Keyed on the route so the cross-fade replays on each tool change.
            Opacity only -- see base.css. */}
        <div key={location.pathname.split("/")[1] ?? ""} className="route-in">
          <Routes location={location}>
            <Route path="/" element={<Landing />} />
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
