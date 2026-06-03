# Query Observability — production telemetry for the Pokémon search

This document is a panel-shareable walk-through of how the Pokémon search instruments **every user query**, ships the records to Grafana Cloud, and renders them as an operable dashboard. It is the operational counterpart to `docs/rga-eval-methodology.md`:

- `rga-eval/` answers *"is the AI still answering correctly?"* (daily, batch, against a golden dataset)
- This system (`atomic-search/api/`, `atomic-search/src/observability.js`, `observability/`) answers *"how is the app being used **right now**?"* (real-time, every real search a user fires)

> **For the panel.** Most candidates ship a search UI and stop. The observability layer is what turns a demo into a system an oncall could reasonably operate. *We measure quality (Phase 6D), we close the loop on it (Phase 6F), and we observe usage independently (Phase 6E) — three muscles of production AI.*

## Live URL

**Public dashboard** (no Grafana login required, read-only): [charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452](https://charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452)

The dashboard is hosted on Grafana Cloud's free tier (50 GB logs/month, more than enough for this demo). The link above is a public read-only snapshot of the same dashboard the operator sees.

## Companion artifacts

- **`atomic-search/src/observability.js`** — the browser-side instrumentation. Subscribes to Coveo Headless state, captures one record per completed search, fires-and-forgets POST.
- **`atomic-search/api/log-query.js`** — a Vercel serverless proxy. The reason we have it is below ("Why a proxy").
- **`observability/grafana-dashboard.json`** — the dashboard as code. 8 panels, version-controlled.
- **`.github/workflows/deploy-grafana-dashboard.yml`** — CI workflow that auto-deploys the dashboard JSON to Grafana Cloud on every push to `main` (when the JSON changes).
- **`.env.example`** — full env-var documentation, including the three GitHub Actions secrets the deploy workflow needs.

## Architecture

```
   ┌──────────────────────────────────┐
   │   Pokémon search UI (browser)    │
   │   atomic-search/src/main.js +    │
   │   observability.js (Vite bundle) │
   └─────────────┬────────────────────┘
                 │
                 │  user types a query → Enter
                 │  ──────────────────────────►  Coveo Search API
                 │      (~300 ms)
                 │  ◄──────────────────────────  results + RGA stream
                 │
                 │  one log record per completed
                 │  search (timestamp, q, sort,
                 │  rga_*, top_1..5, latency, ...)
                 │
                 │  POST /api/log-query                fire-and-forget,
                 │  Content-Type: application/json     keepalive: true,
                 │  Body: { timestamp, q, sort, … }    never blocks the UI
                 │
                 ▼
   ┌──────────────────────────────────┐
   │   Vercel serverless function      │
   │   atomic-search/api/log-query.js  │
   │   (same origin as the UI)         │
   └─────────────┬────────────────────┘
                 │
                 │  Adds server-side Loki auth header
                 │  (the Loki write token NEVER touches the browser)
                 │
                 │  POST $GRAFANA_LOKI_URL/loki/api/v1/push
                 │  Authorization: Basic <base64(user:token)>
                 │
                 ▼
   ┌──────────────────────────────────┐
   │   Grafana Cloud Loki              │
   │   (logs-prod-018.grafana.net)     │
   │   Stream labels:                  │
   │     app, search_hub, status,      │
   │     rga_fired                     │
   │   Value: full JSON payload        │
   └─────────────┬────────────────────┘
                 │
                 ▼
   ┌──────────────────────────────────┐
   │   Grafana dashboard (8 panels)    │
   │   ─ visualized from LogQL queries │
   │   ─ public read-only URL          │
   │   ─ auto-deployed from git via    │
   │     GitHub Actions                │
   └──────────────────────────────────┘
```

## Why a Vercel proxy (and not browser-direct to Loki)

The original plan was to POST from the browser straight to Grafana Loki. **Two reasons that didn't work**, and both led to a strictly better design:

1. **CORS.** Grafana Cloud's Loki push endpoint (`/loki/api/v1/push`) doesn't enable CORS. The browser's preflight `OPTIONS` request gets `405 Method Not Allowed`. There is no Grafana-side toggle to enable CORS on the push endpoint — it's not a configurable behavior.
2. **Security.** Even if CORS were enabled, exposing the Loki write token (`glc_...`) in the browser bundle would be a permanent trade-off: anyone could read DevTools, copy the token, and spam our log dataset.

**The Vercel proxy solves both at once.** The browser POSTs to `/api/log-query` (same-origin, no preflight required). The serverless function holds the Loki auth in `process.env.GRAFANA_LOKI_AUTH` — a Vercel env var with **no `VITE_` prefix**, so it's never bundled into the browser code. The browser never sees the credential at all.

This pattern is also what we'd recommend to any Coveo customer deploying observability: never put a write credential in a client.

## What we log per search

Every completed search emits one JSON record. Field-by-field:

| Field | What | Why we capture it |
|---|---|---|
| `timestamp` | ISO-8601 in UTC | Time-series indexing |
| `q` | User's literal query text | Top-queries panel, drill-down |
| `search_hub` | The Atomic search-hub key (`pokemon-search`) | Stream label, multi-app slicing |
| `sort_criteria` | `relevancy` / `name asc` / `date desc` / … | "Are users picking non-default sorts?" |
| `rga_requested` | Boolean (is RGA enabled for this search?) | Differentiates "RGA off" from "RGA failed" |
| `rga_fired` | Boolean (`isAnswerGenerated`) | Settled-state signal, panel headline metric |
| `rga_answer` | First 500 chars of the RGA text | Drill-down + spot-check answer quality |
| `rga_citations_count` | Integer | Sanity check (RGA without citations = weak grounding) |
| `top_results` | Array of `{title, uri}` (5) | Stored for forensic inspection |
| `top_1` .. `top_5` | First-N result titles (flat strings) | Sortable / filterable columns in the table panel |
| `total_count` | Coveo's reported result count | Spot 0-result queries, content gaps |
| `response_time_ms` | Coveo Search API latency | p50 / p95 / p99 panel |
| `pipeline` | The query pipeline used | Multi-pipeline diagnostics |
| `client_id` | `coveo_visitorId` cookie value | Join key to Coveo UA exports if ever cross-referenced |
| `facets_active` | List of `facet_id:value` | "Did facet filtering save the relevance?" |
| `status` | `200` / `4xx` / `5xx` | Error-rate panel, stream label |

## What we deliberately *do not* log

Three things, by policy:

- **PII.** `client_id` is Coveo's anonymous session ID — not a user identity. No IPs, no auth tokens, no API keys.
- **Result body content.** We log titles and URIs of top results, not the full result snippets. Smaller payloads, no risk of accidentally storing user data.
- **Error stack traces.** Reduced to top-level error code only — privacy and log-size hygiene.

The trade-off is documented as "the logging budget" — explicit about what we trade off for operational insight.

## The 8 panels — what each one answers

1. **Top queries (selected window)** — "What did users actually search for?" Bar chart, top 20 unique queries.
2. **RGA fire rate** — "Did the AI answer fire as often as expected?" Stat percentage. Watch for drops (model issue, sort=non-relevancy regression where RGA refuses to ground, or content gap).
3. **Error rate (4xx/5xx)** — "Is anything broken?" Stat percentage. Should be ~0%. Spikes mean rate-limiting, auth issues, pipeline misconfig, or platform incident.
4. **Query volume** — "Is traffic spiky or steady?" Time-series, searches per `$__interval`. Cliffs are diagnostic (the UI broke and stopped firing).
5. **Coveo response latency** — "Is Coveo healthy?" p50 / p95 / p99 over time. p95 is the user-perceived headline; p99 catches tail-latency events.
6. **Sort criteria distribution** — "Which sort do users actually pick?" Donut chart. Relevancy dominating is healthy.
7. **Search hub mix** — "How does traffic split across hubs?" Donut chart. Single-hub today; future-proofing for multi-app deployments.
8. **Live search logs (tabular)** — Per-search log records as a sortable, filterable table. One row = one search. Click any cell's inspect icon (magnifying glass on hover) to see the full value. Includes the `top_1`..`top_5` columns for at-a-glance relevance diffing ("did Charizard fall out of the top 5 today?").

## Dashboard-as-code (CI auto-deploy)

The dashboard is **not** maintained by hand in the Grafana UI. The source of truth is `observability/grafana-dashboard.json`, version-controlled in git. The deploy workflow does the rest:

```
edit observability/grafana-dashboard.json
       │
       │  git commit + push (to main)
       ▼
.github/workflows/deploy-grafana-dashboard.yml
       │
       │  1. Validate JSON parses
       │  2. Verify required secrets are present (named errors, not curl noise)
       │  3. Resolve Loki data source UID via Grafana API
       │     (so the JSON stays portable across orgs / stacks)
       │  4. Substitute ${DS_LOKI} placeholder → real UID
       │  5. POST /api/dashboards/db with overwrite: true
       │
       ▼
Dashboard updated in ~30 seconds. Public URL same; visitors see the new version on next refresh.
```

Three GitHub Actions secrets gate the workflow: `GRAFANA_URL`, `GRAFANA_API_TOKEN`, `GRAFANA_LOKI_DS_NAME`. See `.env.example` for full setup instructions.

If you edit the dashboard live in the Grafana UI (e.g., tweaking a panel during a debug session) and don't re-export the JSON, the next push from main will overwrite your tweak. By design — git remains the source of truth.

## Kill-switches

Two ways to disable observability without redeploying:

1. **`import.meta.env.DEV`** — `npm run dev` always silences the proxy POST (the proxy endpoint doesn't exist locally; we don't want console noise from failed fetches on every search). To exercise the proxy locally, run `vercel dev` instead.
2. **`VITE_OBSERVABILITY_ENABLED=false`** — set in Vercel env vars or `.env` to force-disable observability in any environment.

Either one falls through to a silent no-op. No console banner, no warning. The search UI stays normal.

## Cross-phase TODO — when Phase 8 (Passage Retrieval) lands

When `atomic-search/` starts using Coveo's Passage Retrieval API, extend `buildPayload()` in `observability.js` to capture passage-retrieval outcomes in parallel with RGA:

```js
passage_retrieval_fired: Boolean(...),
passage_text: truncate(..., 500),
passage_source_uri: ...,
passage_count: ...,
```

Then add a 9th panel to `observability/grafana-dashboard.json` mirroring the RGA fire-rate panel. The dashboard story stays symmetric — both AI surfaces (generative answer + extracted passage) are visible side-by-side, with the same kind of operational telemetry behind each.

## Where to look in code

| Path | Role |
|---|---|
| `atomic-search/src/observability.js` | Browser instrumentation — subscribe → build payload → POST |
| `atomic-search/src/main.js` | Wires `instrumentEngine(engine)` after the Atomic interface initializes |
| `atomic-search/api/log-query.js` | Vercel serverless proxy — receives JSON, forwards to Loki with auth |
| `atomic-search/vite.config.js` | Build-time env-var resolution (browser vs server-side split) |
| `observability/grafana-dashboard.json` | The dashboard, version-controlled |
| `.github/workflows/deploy-grafana-dashboard.yml` | CI auto-deploy |
| `.env.example` | Full env-var documentation, including the 3 GitHub Actions secrets |
