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

// Fallback timeout — if RGA never reaches a settled state (e.g., backend hang,
// model timeout, network issue), log the search anyway after this many ms with
// whatever rga_answer/citations exist at that point. 5s is generous; most RGA
// responses complete in 1-2s. Without this, a stuck RGA stream would prevent
// ANY log from being emitted for that search.
const RGA_SETTLE_TIMEOUT_MS = 5000;

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
    rga_requested: Boolean(ga?.isEnabled),
    // `isAnswerGenerated` is Headless's authoritative "stream finished, answer is
    // final" signal. Using it (vs Boolean(answer)) means we don't false-positive
    // on mid-stream partial text, and we don't false-negative when cannotAnswer
    // fires (no answer text, but RGA did "fire" — it just refused to ground).
    rga_fired: Boolean(ga?.isAnswerGenerated),
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
 * Detection of "search completed + RGA settled":
 *   - Search has a `searchUid` (Coveo assigns one per successful search)
 *   - Engine is not loading (no in-flight request)
 *   - Either RGA isn't in play, OR generatedAnswer.isAnswerGenerated is true,
 *     OR cannotAnswer is true — i.e. the RGA stream has reached a terminal state
 *   - We dedupe per searchUid so re-renders during the same search log once
 *   - A safety fallback timer logs anyway after RGA_SETTLE_TIMEOUT_MS if the
 *     terminal state never arrives (backend hang, network issue, etc.)
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
  let fallbackTimer = null;
  let pendingUidForFallback = null;

  const logOnce = (uid, state) => {
    if (uid === lastLoggedUid) return;
    lastLoggedUid = uid;
    if (fallbackTimer) {
      clearTimeout(fallbackTimer);
      fallbackTimer = null;
      pendingUidForFallback = null;
    }
    pushToProxy(buildPayload(state));
  };

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

    // RGA streams AFTER the search response settles, so we can't log immediately
    // or rga_answer/citations will be empty. Instead of a fixed debounce, watch
    // Headless's own signals:
    //   - isEnabled=false   → RGA isn't in play for this search; log right away
    //   - isAnswerGenerated → stream finished, answer is final; log now
    //   - cannotAnswer      → RGA refused to ground (still a valid log line; we
    //                         want to capture refusal-rate over time)
    // Fallback timer covers the pathological case where none of those signals
    // ever fire (backend hang, malformed response) — log with whatever we have.
    const ga = state?.generatedAnswer;
    const rgaInPlay = Boolean(ga?.isEnabled);
    const rgaSettled =
      !rgaInPlay ||
      Boolean(ga?.isAnswerGenerated) ||
      Boolean(ga?.cannotAnswer);

    if (rgaSettled) {
      logOnce(uid, state);
      return;
    }

    // RGA still streaming. Arm a single fallback timer per uid so a stuck
    // stream still eventually logs. The next subscribe() tick that observes
    // the settled state will fire logOnce() first and clear this timer.
    if (pendingUidForFallback !== uid) {
      pendingUidForFallback = uid;
      if (fallbackTimer) clearTimeout(fallbackTimer);
      fallbackTimer = setTimeout(() => {
        fallbackTimer = null;
        pendingUidForFallback = null;
        logOnce(uid, engine.state);
      }, RGA_SETTLE_TIMEOUT_MS);
    }
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
