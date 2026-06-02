import { defineConfig, loadEnv } from "vite";
import { resolve } from "path";

// Resolve Coveo credentials with two-environment compatibility:
//
//   1. LOCAL DEV — read from the repo-root .env via Vite's loadEnv(). This
//      way Atomic shares the same secrets file as scripts/, tests/, and
//      push-pokemon/. We try the canonical COVEO_* names first, then
//      VITE_* fallbacks.
//
//   2. PRODUCTION (Vercel) — there's no .env file on the build runner;
//      Vercel injects env vars into process.env. We read those too.
//      Vercel users typically set VITE_-prefixed names in the project
//      settings UI; we also accept the non-prefixed names for symmetry
//      with local dev.
//
// First defined non-empty value wins. If everything is undefined, the
// build still succeeds — main.js shows a clear in-app banner explaining
// what's missing instead of failing silently.
const repoRoot = resolve(__dirname, "..");

function firstDefined(...vals) {
  for (const v of vals) {
    if (v !== undefined && v !== "") return v;
  }
  return undefined;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, "");

  const orgId = firstDefined(
    env.COVEO_ORG_ID,
    env.VITE_COVEO_ORG_ID,
    process.env.COVEO_ORG_ID,
    process.env.VITE_COVEO_ORG_ID
  );
  const searchToken = firstDefined(
    env.COVEO_SEARCH_API_KEY,
    env.VITE_COVEO_SEARCH_TOKEN,
    process.env.COVEO_SEARCH_API_KEY,
    process.env.VITE_COVEO_SEARCH_TOKEN
  );

  // Phase 6E — observability kill-switch only.
  // Loki credentials live SERVER-SIDE in Vercel env vars (GRAFANA_LOKI_URL +
  // GRAFANA_LOKI_AUTH, NO VITE_ prefix). The browser POSTs to /api/log-query;
  // the serverless function at atomic-search/api/log-query.js holds the auth.
  // This kill-switch is the only Grafana-related value that needs to be in
  // the bundle, and it's not a secret.
  const observabilityEnabled = firstDefined(
    env.VITE_OBSERVABILITY_ENABLED,
    process.env.VITE_OBSERVABILITY_ENABLED,
    "true"
  );

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
      "import.meta.env.VITE_COVEO_ORG_ID": JSON.stringify(orgId),
      "import.meta.env.VITE_COVEO_SEARCH_TOKEN": JSON.stringify(searchToken),
      "import.meta.env.VITE_OBSERVABILITY_ENABLED": JSON.stringify(observabilityEnabled),
    },
  };
});
