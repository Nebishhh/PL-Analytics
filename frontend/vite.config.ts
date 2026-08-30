import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Proxies to the REAL backend on 127.0.0.1:8000. There is deliberately no mock
// layer, no MSW, no fixtures: a shape mismatch should fail here and now rather
// than at integration, and the refusal / out-of-scope states are only
// exercisable against real data.
//
// /plots is proxied because the methodology pages serve the committed PNGs from
// the backend rather than copying them into the frontend (AGENTS.md §1.3).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/plots": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});
