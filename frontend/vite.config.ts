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
// Verified end to end: /plots/01/04_age_curve.png returns 43,061 bytes of
// image/png through the proxy, byte-identical to the backend's direct
// response, and a missing file 404s rather than falling back to index.html.
//
// GOTCHA, if a scripted check ever reports connection refused on this port:
// Vite binds `localhost`, which Node 17+ resolves to ::1 without reordering,
// so the dev server listens on IPv6 only. Browsers follow the same resolution
// and work fine, but `curl http://127.0.0.1:5173` fails while
// `curl http://localhost:5173` succeeds. The binding is left alone
// deliberately -- forcing IPv4 risks breaking the browser's `localhost`, and
// `host: true` would expose the dev server on the network.
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
