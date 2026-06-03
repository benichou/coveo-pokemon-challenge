// Phase 6E — query-level observability via a Vercel serverless proxy.
//
// One log line per completed search. Captures what the user searched for,
// which facets / sort they had on, how Coveo responded (latency, total
// count, status), and whether RGA fired. Fire-and-forget POST to our
// same-origin /api/log-query endpoint; never blocks the UI.
//
// Why a proxy (not browser-direct to Loki)?
//   Grafana Cloud's Loki push endpoint doesn't enable CORS — browser
//   OPTIONS preflight gets 405. Plus, putting the Loki write token in the
//   browser bundle was always a security compromise. The proxy keeps the
//   token server-side (Vercel env vars without the VITE_ prefix), and
//   browser POSTs are same-origin so no preflight is needed.
//   See atomic-search/api/log-query.js for the server side + the full
//   architecture story in docs/observability.md.
//
// Kill-switches (any disables logging):
//   - Running in dev mode (import.meta.env.DEV) → silent no-op. The proxy
//     endpoint doesn't exist on `npm run dev`; use `vercel dev` if you
//     want local proxying.
//   - VITE_OBSERVABILITY_ENABLED is the literal string "false".

const PROXY_ENDPOINT = "/api/log-query";

const IS_DEV = Boolean(import.meta.env.DEV);
const OBSERVABILITY_ENABLED =
  import.meta.env.VITE_OBSERVABILITY_ENABLED !== "false";

// In dev mode the proxy doesn't exist (unless you run `vercel dev`).
// Default to disabled on localhost to avoid console noise from failed
// fetches on every search.
const SAFE_TO_LOG = OBSERVABILITY_ENABLED && !IS_DEV;

// TEMP — diagnostic for Phase 6E launch. Remove after observability is verified
// working end-to-end in production. Will print once when the module loads.
console.log("[observability] module loaded", {
  SAFE_TO_LOG,
  IS_DEV,
  OBSERVABILITY_ENABLED,
});

// ---------- Pure helpers ----------

function activeFacetsFromState(state) {
  // Coveo Headless exposes facet state under state.facetSet, keyed by facet id.
  // Each entry has `request.currentValues` — an array of facet values with a
  // `state` field ("idle" / "selected" / "excluded").
  const out = [];
  const facetSet = state?.facetSet ?? {};
  for (const [facetId, val] of Object.entries(facetSet)) {
    const values = val?.request?.currentValues ?? [];
    for (const fv of values) {
      if (fv?.state === "selected") {
        out.push(`${facetId}:${fv.value}`);
      }
    }
  }
  return out;
}

function statusFromState(searchState) {
  if (!searchState?.error) return "200";
  const code = searchState.error?.statusCode;
  if (typeof code === "number") return String(code);
  return "5xx";
}

export function buildPayload(state) {
  // Defensive reads — Coveo Headless state shape varies across versions.
  // Anything we can't read falls back to a sensible default; we'd rather
  // log a partial record than skip logging entirely.
  const search = state?.search ?? {};
  const query = state?.query ?? {};
  const config = state?.configuration ?? {};
  const ga = state?.generatedAnswer ?? null;

  return {
    timestamp: new Date().toISOString(),
    q: query.q ?? "",
    search_hub: config.search?.searchHub ?? state?.searchHub ?? "",
    sort_criteria: state?.sortCriteria ?? "",
    rga_requested: Boolean(ga),
    rga_fired: Boolean(ga?.answer),
    total_count: search.response?.totalCount ?? 0,
    response_time_ms: search.duration ?? 0,
    pipeline: state?.pipeline ?? "default",
    client_id: config.analytics?.clientId ?? "",
    facets_active: activeFacetsFromState(state),
    status: statusFromState(search),
  };
}

// ---------- Network (side-effecting) ----------

async function pushToProxy(payload) {
  console.log("[observability] pushToProxy — fetching", PROXY_ENDPOINT);
  try {
    const r = await fetch(PROXY_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      // `keepalive: true` lets the request complete even if the user navigates
      // away mid-flight — important for the "user searches, clicks a result"
      // flow where the page navigates away ~ms after the search completes.
      keepalive: true,
    });
    console.log("[observability] pushToProxy result:", r.status);
  } catch (e) {
    console.log("[observability] pushToProxy threw:", e?.message);
    // Fire-and-forget. Never propagate; never break the UI.
  }
}

// ---------- Public API ----------

/**
 * Subscribe to a Coveo Headless engine's state changes and log one record
 * per completed search.
 *
 * Detection of "search completed":
 *   - The search has a `searchUid` (Coveo assigns one per successful search)
 *   - We track the last logged uid to dedupe re-renders within the same search
 *   - We skip while the engine is loading (in-flight requests)
 *
 * @param {import("@coveo/headless").SearchEngine} engine
 */
export function instrumentEngine(engine) {
  if (!SAFE_TO_LOG) {
    // Silent no-op (dev mode, or explicit kill-switch). No banner,
    // no console noise. Local `npm run dev` should feel normal.
    return;
  }
  if (!engine || typeof engine.subscribe !== "function") {
    console.warn(
      "[observability] instrumentEngine called without a valid Coveo engine; skipping",
    );
    return;
  }

  console.log("[observability] instrumentEngine OK — installing subscriber");

  let lastLoggedUid = null;
  let fireCount = 0;
  engine.subscribe(() => {
    fireCount++;
    const state = engine.state;
    const search = state?.search;
    if (!search) {
      if (fireCount <= 3) console.log("[observability] skip — no search state");
      return;
    }
    if (search.isLoading) {
      if (fireCount <= 3) console.log("[observability] skip — isLoading");
      return;
    }

    const uid =
      search.response?.searchUid ??
      search.searchResponseId ??
      search.searchUid;
    if (!uid) {
      if (fireCount <= 3) console.log("[observability] skip — no uid yet");
      return;
    }
    if (uid === lastLoggedUid) {
      // Common case (same search re-rendering) — don't spam
      return;
    }

    lastLoggedUid = uid;
    console.log("[observability] PUSH —", {
      uid: uid.slice(0, 8),
      q: state.query?.q ?? "",
      isLoading: search.isLoading,
    });
    pushToProxy(buildPayload(state));
  });
}

// Exposed for unit tests / debugging from the browser console
export const _internals = {
  buildPayload,
  activeFacetsFromState,
  statusFromState,
  PROXY_ENDPOINT,
  SAFE_TO_LOG,
};
