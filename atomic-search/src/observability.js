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

// Wait this long after the search response lands before reading state + posting.
// Coveo's RGA streams in AFTER the search response — typically ~200-700ms.
// Logging immediately would capture empty rga_answer / 0 citations. Logging
// after this delay catches the full streamed answer ~95% of the time. The
// tradeoff is a tiny perceived latency in the log freshness, which is fine
// for observability (this isn't a hot path).
const RGA_STREAM_BUFFER_MS = 750;

const IS_DEV = Boolean(import.meta.env.DEV);
const OBSERVABILITY_ENABLED =
  import.meta.env.VITE_OBSERVABILITY_ENABLED !== "false";

// In dev mode the proxy doesn't exist (unless you run `vercel dev`).
// Default to disabled on localhost to avoid console noise from failed
// fetches on every search.
const SAFE_TO_LOG = OBSERVABILITY_ENABLED && !IS_DEV;

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

// Cap RGA answer text in the log. Loki's per-line ingest limit is generous
// (~64KB default) but bounded payloads keep the Grafana log-viewer readable
// and the time-series index lean. Most RGA answers are <500 chars anyway.
const RGA_ANSWER_MAX_CHARS = 500;

// How many top results to capture per search. 5 is panel-friendly: enough
// to spot relevance drift ("did Charizard fall out of the top 5?") without
// bloating the log payload.
const TOP_N_RESULTS = 5;

function topResultsFromState(searchState) {
  const results = searchState?.response?.results ?? [];
  return results.slice(0, TOP_N_RESULTS).map((r) => ({
    title: r?.title ?? "",
    // clickUri is the canonical link; uri is the indexed id. clickUri is what
    // the user actually navigated to and is more meaningful for the log.
    uri: r?.clickUri ?? r?.uri ?? "",
  }));
}

function truncate(s, n) {
  if (typeof s !== "string") return "";
  return s.length > n ? s.slice(0, n) + "…" : s;
}

function rgaCitationsCountFromState(ga) {
  if (!ga) return 0;
  const c = ga.citations ?? ga.citationsList ?? [];
  return Array.isArray(c) ? c.length : 0;
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
    // RGA answer (truncated). Captured ~750ms after search-completed so the
    // stream has time to land; bounded length keeps the log payload reasonable.
    rga_answer: truncate(ga?.answer ?? "", RGA_ANSWER_MAX_CHARS),
    rga_citations_count: rgaCitationsCountFromState(ga),
    // Top N result titles + clickUris. Lets us answer "did the top result for
    // 'charizard' suddenly change?" without re-running the query.
    top_results: topResultsFromState(search),
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
  try {
    await fetch(PROXY_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      // `keepalive: true` lets the request complete even if the user navigates
      // away mid-flight — important for the "user searches, clicks a result"
      // flow where the page navigates away ~ms after the search completes.
      keepalive: true,
    });
  } catch {
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

  let lastLoggedUid = null;
  let pendingTimer = null;
  engine.subscribe(() => {
    const state = engine.state;
    const search = state?.search;
    if (!search) return;
    if (search.isLoading) return;

    // Coveo's search uid lives in slightly different places depending on
    // Headless version. Try several locations; any one is enough.
    const uid =
      search.response?.searchUid ??
      search.searchResponseId ??
      search.searchUid;
    if (!uid) return;
    if (uid === lastLoggedUid) return;

    // Don't log immediately — RGA streams in AFTER the search response, so
    // a `rga_answer` field captured at search-completed would always be
    // empty. Debounce by ~750ms so the RGA answer + citations have time to
    // land before we read state and POST. New searches within the debounce
    // window reset the timer (the lastLoggedUid check still dedupes).
    lastLoggedUid = uid;
    if (pendingTimer) clearTimeout(pendingTimer);
    pendingTimer = setTimeout(() => {
      pendingTimer = null;
      pushToProxy(buildPayload(engine.state));
    }, RGA_STREAM_BUFFER_MS);
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
