# Caching strategy — what Coveo gives us and what we deliberately didn't add

This document is a panel-shareable record of how we thought about caching for the Pokémon search experience. The headline: Coveo provides multiple caching layers automatically, RGA answer text is deliberately non-deterministic, and we made a considered decision NOT to add an app-side cache for the demo. We did NOT skip this question — we *answered* it.

> **For the panel.** Production AI deployments routinely add a caching layer in front of the LLM call to control cost + latency + answer consistency. We thought through what we'd add, and why we chose Coveo's defaults for *this* build. Both halves are panel-worthy: knowing the tools, AND making considered scope decisions about which to deploy.

## The question

*If a user types `what type is Charizard` twice in a row, will they see exactly the same RGA answer?*

Answer: **almost identical citations and substance, slightly different prose**. The retrieved chunks are deterministic; the LLM's wording is not. For our demo and for most real customer use cases, that's the right behavior — but worth understanding why.

## Coveo's built-in caching (active by default; no work needed on our side)

| Layer | What it caches | Default behavior | How to tune |
|---|---|---|---|
| **Search API in-memory result cache** | Full result-list responses for identical query+user requests | ~30 min TTL by default | Pass `maximumAge` (ms) on the request to shorten or extend |
| **Index cache for constant query expressions** | The evaluation of `cq` (constant) parts of a query that don't vary per user | Always on for `cq` | Use `cq` instead of `aq` for static filters |
| **RGA GQPM (Generative Queries Per Month) dedup** | Billing-level — won't double-charge for the same generative query in a month | Automatic via Answer Manager | Confirm answer-config is attached to the search interface |

**These layers are working today on our org.** We don't see the result-list cache in our local dev because each browser session generates a fresh client identifier (Coveo's cache is keyed on user identity), but for repeat searches within the same session the in-memory cache kicks in.

## RGA non-determinism — a feature, not a bug

Per [Coveo's RGA model card](https://docs.coveo.com/en/nbpd4153/):

> *"RGA uses a third-party generative LLM that's hosted on an external foundation model service server. The LLM is a stateless model that's shared by all Coveo customers."*

So the answer-generation flow looks like:

```
query → first-stage retrieval (deterministic) → top-N docs
     → second-stage retrieval (deterministic) → top-K chunks
     → external LLM (NOT deterministic, slight wording variation)
     → final answer text + citations (citations deterministic, prose stochastic)
```

This means: same query → same citations + same factual substance + slightly different wording. For nearly all use cases this is the right behavior:

- **Demo value**: panel reviewers typing the same query twice see slightly different prose — that itself demonstrates "this is an LLM-grounded answer, not memorized."
- **Operational reality**: even with caching, real customers update content, RGA prompts evolve, and SE models retrain — meaning "same query" produces different upstream context over time anyway.
- **Forcing determinism via cache would mask quality regressions.** If RGA accuracy drifts (the exact thing our Phase 6D evaluator catches), a cached layer would hide that until the cache expires.

## Why we did NOT add an app-side caching layer

Three reasons specific to this build:

1. **Coveo already handles result-list caching transparently.** Adding another layer would be redundant.
2. **The closed loop (Phase 6F) needs to see *fresh* RGA answers** when the daily eval runs. An aggressive app-side cache would interfere with the eval pipeline reading current model behavior.
3. **Demo value of stochasticity** — described above.

For a *real* Coveo customer with production traffic, we'd absolutely add caching. Just not here, not yet.

## What we WOULD add in production (panel narrative material)

If asked *"how would you scale this to a real customer with N million queries/day?"*, here's the staged caching plan:

### Tier 1 — CDN edge cache on the search-fronting proxy

Pattern: put a CDN (Vercel Edge, Cloudflare Workers, AWS CloudFront) in front of the Search API. Cache hot-path queries (e.g., `support help reset password`) for ~5 minutes at the edge.

- **Pros**: cheapest tier-1; cuts Coveo cost + p50 latency for repeat queries; works for both result lists and RGA streams
- **Cons**: cache invalidation on prompt changes / index changes requires care
- **Effort**: ~2 hours to wire up; Vercel Edge Functions support cache-control headers natively

### Tier 2 — Redis/KV cache keyed by query + parameters + prompt version

Pattern: a small Redis or Vercel KV instance in front of our `/api/log-query` proxy. Key: `hash(query + sort + facets + active_prompt_version)`. TTL: 5–15 min.

- **Pros**: full control over invalidation (bust on prompt change automatically via `prompt_version` in the key); deterministic answer text for cached hits; very fast (sub-ms cache lookups)
- **Cons**: another service to operate; doesn't help cold queries
- **Critical detail**: include the *current RGA prompt version* in the cache key, so when the closed loop applies a new prompt (Phase 6F), all caches naturally invalidate

### Tier 3 — Browser-side `Cache-Control` headers

Pattern: send `Cache-Control: public, max-age=60` from the search proxy. The browser caches the response.

- **Pros**: zero infrastructure cost; free CDN
- **Cons**: only helps within a single user's session
- **When useful**: as a complement to Tier 1, not a replacement

### Where it fits in our deployment

Today's architecture: `browser → Vercel function (log proxy) → Coveo`. Adding caching = inserting a check at the Vercel function before calling Coveo:

```
browser → Vercel function
            ├── hash request → check Redis/KV
            │     │
            │     ├── hit → return cached response
            │     │
            │     └── miss → call Coveo → store response → return
            │
            └── log the search to Grafana regardless of cache hit/miss
```

The observability layer (Phase 6E) stays intact — every request still gets logged, with an added `cache_hit: true/false` field. That itself is panel-worthy: *"we'd observe cache hit-rate to right-size the layer."*

## Decision matrix (for the panel — "when would you add what?")

| Symptom | Add this | Don't add this |
|---|---|---|
| High Coveo Search API cost on hot-path queries | Tier 1 (CDN edge) | Tier 2 alone — won't help cold queries |
| Customer demands consistent RGA answer wording for identical queries | Tier 2 (Redis + prompt-version key) | Tier 1 alone — TTL too short |
| p99 latency complaints from users | Tier 1 + measure | Tier 2 — extra hop adds latency |
| Closed-loop eval is producing flaky numbers | Nothing — the eval *needs* to bypass cache | All three — would mask regressions |

## TL;DR

- Coveo gives us caching for free at the result-list layer + the index layer + the billing layer.
- RGA answer text is intentionally non-deterministic; same query → same substance + slightly different wording.
- We chose NOT to add app-side caching for the demo because (1) it'd be redundant, (2) it'd interfere with the closed-loop eval, and (3) the stochasticity itself is informative.
- For a real production deployment we'd add a CDN edge cache (Tier 1) + Redis keyed by prompt version (Tier 2), in that order, with cache invalidation tied to the closed-loop apply step.

## Sources

- [RGA data security + LLM architecture](https://docs.coveo.com/en/nbpd4153/) (Coveo)
- [Search API `maximumAge` parameter](https://coveo.github.io/search-ui/interfaces/iquery.html) (Coveo SDK reference)
- [Query pipelines + `cq` index cache](https://docs.coveo.com/en/1450/) (Coveo)
- [Improving Search Response Time](https://docs.coveo.com/en/1948/) (Coveo)
