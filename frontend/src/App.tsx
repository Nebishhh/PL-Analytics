import { Navigate, Route, Routes } from "react-router-dom";
import { TopBar } from "./components/shell/TopBar";
import { ValueTool } from "./tools/value/ValueTool";

function Placeholder({ name }: { name: string }) {
  return (
    <p className="font-prose text-ink-300">
      {name} is not built yet. Step 5 ships the shell and project 01 end to end;
      the remaining marks and tools follow in Step 6 against a proven base.
    </p>
  );
}

export default function App() {
  return (
    <div className="min-h-full">
      <TopBar />
      <main className="mx-auto max-w-[1100px] px-6 py-10">
        <Routes>
          <Route path="/" element={<Navigate to="/value" replace />} />
          <Route path="/value" element={<ValueTool />} />
          <Route path="/match" element={<Placeholder name="Match predictor" />} />
          <Route path="/style" element={<Placeholder name="Style finder" />} />
        </Routes>
      </main>
    </div>
  );
}
