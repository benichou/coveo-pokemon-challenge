// Phase 6E — Vercel serverless proxy for query-level observability.
//
// Why this exists:
//   Grafana Cloud's Loki push endpoint (/loki/api/v1/push) doesn't enable
//   CORS — its OPTIONS preflight returns 405 Method Not Allowed. So we can't
//   POST from the browser directly. This function is the bridge:
//     Browser → POST /api/log-query → this function → Loki /push
//   The Loki auth string lives ONLY in Vercel's server-side env vars
//   (GRAFANA_LOKI_URL + GRAFANA_LOKI_AUTH, no VITE_ prefix), so it's never
//   bundled into the browser code — strictly stronger security than the
//   original "browser-direct" plan.
//
// How Vercel discovers this:
//   Any file in `api/` at the project root is auto-deployed as a serverless
//   function. Path becomes `/api/log-query`. No additional config needed.
//
// Request contract (from atomic-search/src/observability.js):
//   POST /api/log-query
//   Content-Type: application/json
//   Body: { timestamp, q, search_hub, sort_criteria, rga_requested,
//           rga_fired, total_count, response_time_ms, pipeline, client_id,
//           facets_active, status }
//
// Response:
//   - 204 No Content on Loki success
//   - 4xx / 5xx with brief JSON error on failure (does NOT echo the auth
//     header or any other secret)
//   - Browser side fires-and-forgets, so even if this fails, the search
//     UI keeps working.

export default async function handler(req, res) {
  // Only accept POST. GET / OPTIONS / etc. return 405.
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method Not Allowed" });
  }

  const LOKI_URL = process.env.GRAFANA_LOKI_URL;
  const LOKI_AUTH = process.env.GRAFANA_LOKI_AUTH;
  if (!LOKI_URL || !LOKI_AUTH) {
    // Configuration error: server missing env vars. Log and surface a
    // generic 500. Don't reveal which env var is missing in the response.
    console.error(
      "[log-query] missing env vars — GRAFANA_LOKI_URL and/or " +
        "GRAFANA_LOKI_AUTH not configured in this deployment",
    );
    return res
      .status(500)
      .json({ error: "Observability misconfigured (see server logs)" });
  }

  // Vercel parses JSON bodies automatically when content-type is JSON.
  // Defensive: validate it's an object with at least a `q` field.
  const payload = req.body;
  if (!payload || typeof payload !== "object") {
    return res.status(400).json({ error: "Body must be a JSON object" });
  }

  // Build Loki streams body. Labels (the `stream` map) are bounded-cardinality
  // dimensions we'll group by in Grafana. The full per-query record goes in
  // `values[0][1]` as a JSON string — queryable via Loki's JSON parser at
  // read time. Putting `q` as a label would blow up the index (every unique
  // query = new series) — keep it as a value, not a label.
  const nanos = String(Date.now() * 1_000_000); // ms → ns
  const lokiBody = {
    streams: [
      {
        stream: {
          app: "pokemon-search",
          search_hub: payload.search_hub || "unknown",
          status: String(payload.status || "200"),
          rga_fired: String(Boolean(payload.rga_fired)),
        },
        values: [[nanos, JSON.stringify(payload)]],
      },
    ],
  };

  try {
    const lokiResp = await fetch(LOKI_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Basic ${LOKI_AUTH}`,
      },
      body: JSON.stringify(lokiBody),
    });

    if (!lokiResp.ok) {
      // Forward Loki's status + a short snippet of the response body for
      // diagnostics, but NOT the full body (could be large + may include
      // request echo). Never include the auth header in any response.
      const text = (await lokiResp.text().catch(() => "")).slice(0, 500);
      console.error(
        `[log-query] Loki returned ${lokiResp.status}: ${text.slice(0, 200)}`,
      );
      return res
        .status(502)
        .json({ error: `Loki rejected: HTTP ${lokiResp.status}` });
    }

    // Loki returns 204 No Content on success; mirror that to the caller.
    return res.status(204).end();
  } catch (err) {
    // Network error, DNS failure, Loki down, etc.
    console.error("[log-query] fetch to Loki failed:", err?.message);
    return res.status(502).json({ error: "Failed to reach observability backend" });
  }
}
