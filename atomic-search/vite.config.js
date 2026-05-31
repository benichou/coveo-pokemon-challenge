import { defineConfig, loadEnv } from "vite";
import { resolve } from "path";

// Load .env from the repo root (where COVEO_* vars already live) AND from
// the local atomic-search/ folder. The repo-root .env wins; this way Atomic
// shares the same secrets-file as scripts/, tests/, and push-pokemon/.
const repoRoot = resolve(__dirname, "..");

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, "");
  return {
    server: {
      port: 3000,
      strictPort: true,
    },
    // ES2022 lets us use top-level await in main.js (for the
    // searchInterface.initialize() call). All modern browsers support it
    // natively as of mid-2022; only ancient targets would need a polyfill.
    build: { target: "es2022" },
    optimizeDeps: { esbuildOptions: { target: "es2022" } },
    // Expose only the VITE_-prefixed vars to the browser bundle. Coveo's
    // anonymous search key is public-safe (Anonymous Search template); the
    // admin/push keys must never reach the client.
    define: {
      "import.meta.env.VITE_COVEO_ORG_ID": JSON.stringify(
        env.COVEO_ORG_ID || env.VITE_COVEO_ORG_ID
      ),
      "import.meta.env.VITE_COVEO_SEARCH_TOKEN": JSON.stringify(
        env.COVEO_SEARCH_API_KEY || env.VITE_COVEO_SEARCH_TOKEN
      ),
    },
  };
});
