import { Navigate, Route, Routes } from "react-router-dom";
import { TopBar } from "./components/shell/TopBar";
import { ValueTool } from "./tools/value/ValueTool";
import { MatchTool } from "./tools/match/MatchTool";
import { StyleTool } from "./tools/style/StyleTool";
import { About } from "./pages/About";

export default function App() {
  return (
    <div className="min-h-full">
      <TopBar />
      <main className="mx-auto max-w-[1100px] px-6 py-10">
        <Routes>
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
      </main>
    </div>
  );
}
