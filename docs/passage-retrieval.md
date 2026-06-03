# Passage Retrieval — verbatim source content alongside RGA's synthesis

This document is the panel-shareable record of why we added Coveo's Passage Retrieval (PR) API to the Pokémon search experience, how it complements RGA rather than competing with it, and what we discovered along the way.

> **For the panel.** Doc 2's Bonus tier asks us to "explore the Passage Retrieval API." Most candidates will either skip Bonus or wire the API into a hidden route. We chose to surface it directly below RGA on the main search page — making the trade-off ("LLM-synthesized prose with citations" vs "verbatim source text") visible to every visitor. But the deeper story is that PR is Coveo's productized answer to the hardest part of RAG — *"the R"* — and the same API surface we wired up here is what Coveo's enterprise customers use to plug their own LLMs (Claude, GPT-4o, Gemini) into Coveo as the secure, permission-aware retrieval layer. Two parallel answers in our demo + a path to BYO-LLM integration in production = a Topic-1 ↔ Topic-2 bridge.

## Coveo's positioning — when PR is used in production

> *"Many organizations are adopting Retrieval-Augmented Generation (RAG) and quickly realizing that the hardest part — the **'R'** — lies in retrieving precise and relevant information from scattered enterprise systems."*
> — Coveo, [Passage Retrieval API press release](https://ir.coveo.com/en/news-events/press-releases/detail/420/fast-track-genai-success-coveo-launches-passage-retrieval)

That's the elevator pitch for PR in one sentence: **Coveo solves the R in RAG.** Generative LLMs are now commodities; the moat is *which content gets fed into them and how that content is retrieved securely from scattered enterprise sources*. PR is Coveo's productized answer.

### The three official use cases Coveo positions PR for

| # | Use case | What it looks like in practice |
|---|---|---|
| 1 | **Internal knowledge management** | Employees getting personalized, accurate answers grounded in enterprise knowledge — reducing search time, boosting productivity |
| 2 | **Customer-facing support + case deflection** | Self-service AI answers cited from support content — fewer escalations, lower cost, higher CSAT |
| 3 | **Bring-your-own-LLM integration with major AI platforms** | The strategic positioning. Coveo explicitly names Salesforce Einstein, Microsoft Azure AI / Copilot, AWS Bedrock, IBM Watson, Salesforce Agentforce, Amazon Q Business, SAP Joule — plus LLMs like Anthropic Claude, OpenAI GPT-4o, Google Gemini. *"If you're building GenAI with your own LLM, we're the retrieval layer."* |

### Five benefits Coveo emphasizes

1. **Accuracy** — grounds LLM outputs in factual enterprise content; reduces hallucinations
2. **Security** — content permissions are honored end-to-end; users only see what they're authorized to access. This is a major enterprise differentiator most RAG demos quietly ignore
3. **LLM flexibility** — works with any model: Claude, GPT-4o, Gemini, on-prem, regulated environments
4. **Semantic relevance** — uses the same Semantic Encoder + ART models that power the rest of Coveo's stack
5. **Speed-to-market** — leverages existing Coveo query pipelines; no separate vector DB to build/operate

### Named customers using PR in production (per Coveo's own materials)

**Xero, F5, SAP Concur, Forcepoint, United Airlines**, and others. Useful anchor when the panel asks *"who else uses this?"* — Coveo's own marketing names actual logos, not hypotheticals.

### Roadmap signal — Relevance-Augmented Passage Retrieval

Coveo launched a successor capability in 2025: **Relevance-Augmented Passage Retrieval** (the same PR API but with ART — Automatic Relevance Tuning — layered into the ranking). ART learns from real usage analytics over time, so PR's relevance improves as the customer's user base interacts with the system. We don't have ART deployed on our org, but this is the future state worth mentioning if asked *"how would you improve this in production?"* — *"deploy ART on the same passage flow to learn from real customer engagement signal."*

### How our build maps to this positioning

We use PR for **fact-checking RGA on the live page** — a narrow but defensible use case. But the same API surface we wired up (`/rest/search/v3/passages/retrieve`) is exactly what a customer would use to connect this Coveo org to a different LLM via CRGA, or to a Salesforce Einstein deployment, or to Microsoft Copilot. The technical surface we built **IS the customer-pitch primitive** — that's the Topic-1 ↔ Topic-2 bridge in our story.

## What it is

Coveo's Passage Retrieval API ("CPR" or "PR") returns *short verbatim text segments* extracted from indexed documents, ranked by relevance to a query. Unlike the standard Search API (which returns whole documents with metadata) and unlike RGA (which generates a synthesized paragraph via an LLM), PR returns the **actual passages** that an LLM-grounded system *would* use as context.

For *"what type is Charizard"*:

- **Standard Search**: returns the Charizard page document + facet counts + total hits.
- **RGA**: generates a paragraph like *"Charizard is a Fire / Flying type Pokémon introduced in Generation 1..."* with a citation.
- **Passage Retrieval**: returns the literal sentence on the Charizard page that says *"Type: Fire / Flying"*, plus 1–2 other relevant passages, each with a source URI.

PR's output is the **source-of-truth text** that grounds RGA's prose. Showing both side-by-side answers a panel question that every customer asks: *"how do I know the AI didn't make this up?"* — by exposing the source content right next to the AI's interpretation.

## Architecture

```
   Atomic UI search box  → engine fires search
        │
        ├── Standard /search/v2 → result list
        ├── /generate (RGA)     → AI paragraph above results
        └── /passages/v3        → top 3 extracted passages
                                  ↑
                            NEW: panel below RGA
```

Each of the three calls is independent — they fire in parallel on every search, render into their respective UI surfaces, and write the same `searchUid` into the query-observability log. The Passage Retrieval call has its own panel (`#passage-retrieval-panel`) populated by `atomic-search/src/passage-retrieval.js`.

## Endpoint discovery — the subdomain gotcha

Coveo's Passage Retrieval API does NOT live at `platform.cloud.coveo.com` like the rest of the platform APIs. It lives at an **org-scoped subdomain**:

```
POST https://<orgId>.org.coveo.com/rest/search/v3/passages/retrieve
```

For our org: `https://benichouu9fose4g.org.coveo.com/rest/search/v3/passages/retrieve`.

Authorization uses the same `COVEO_SEARCH_API_KEY` the Atomic UI uses for the Search API — no new key needed.

Required request fields:

| Field | What |
|---|---|
| `query` | The user's text |
| `maxPassages` | Cap on how many passages to return (we use 3) |
| `searchHub` | `pokemon-search` |
| `localization` | `{ "locale": "en-US", "timezone": "..." }` |
| `additionalFields` | Array of source fields to echo back (we request `clickableuri`, `pokemon_name`, `pokemon_type`) |

Prerequisites that bit us during the spike:

- A Coveo Passage Retrieval (CPR) model must exist on the org **AND** be associated with the active query pipeline. Without the association, the endpoint returns `422 UNPROCESSABLE_ENTITY` with message *"This API requires a Passage Retrieval model associated to the pipeline."*
- The pipeline must also have a Semantic Encoder (SE) model associated — Passage Retrieval depends on SE for chunk embeddings. We had this already from Phase 6A.

## Rendering — markdown tables become real HTML tables

A key observation during the spike: Coveo's PR often returns chunks that contain **markdown tables** — Pokémon stat tables, move lists, ability lists, evolution chains. The naive thing is to treat the `|` syntax as "chrome noise" and strip it. The right thing is to recognize these are **high-value structured content** that the original page author meant to display as a table, and to render them as real HTML tables in our UI.

We chose `markdown-it` for this:

```js
const md = new MarkdownIt({
  html: false,       // block raw HTML in source content — XSS guardrail
  linkify: false,    // don't auto-link bare URLs (adds noise)
  breaks: false,
});

// Strip anchor-only chrome links BEFORE markdown-it parses
function stripAnchorOnlyLinks(text) {
  return text.replace(/\[([^\]]*)\]\(#[^)]*\)/g, "$1");
}

// In the render path:
const cleaned = stripAnchorOnlyLinks(passage.text);
const html = md.render(cleaned);  // produces real <table>, <h>, <ul>, etc.
```

Safety: `html: false` blocks raw HTML in the markdown source, so if a malicious actor ever injected `<script>` into a Pokémon page that got indexed, our renderer would still treat it as text rather than execute it. Plus we run a one-line regex pre-pass to drop pure anchor-only links like `[Skip to main content](#main)` — those are page-chrome noise even when rendered properly.

The CSS in `style.css` styles `.passage-text--markdown table` for tight, scannable tables: 0.78rem font size, light alternating-row backgrounds, horizontal overflow scroll when a table is wider than the card.

**Panel-narrative value:** this is the kind of detail that separates a demo from production-grade. Every customer's documentation has tables — pricing matrices, feature comparisons, FAQ rows, spec sheets. A search UI that surfaces them as raw pipes is unfit for production; one that renders them as tables is what users expect. Topic 1 deep-dive material: *"we noticed PR was returning structured tables, treated them as high-value content, and rendered them properly. This is how an FDE thinks about preserving source-content semantics through the AI layer."*

## UI design — opt-in display gated on the RGA flow

A second design decision worth recording: the PR panel is **collapsed by default** and **hidden entirely when the RGA flow isn't in play**. The user opts in to verification by clicking "Verify with source passages — N passages available".

Two reasons:

1. **Default behavior should be clean.** RGA's synthesized answer is what most users want. PR is a *power-user verification surface* — most people will trust the AI; some will want to fact-check; both deserve a UI that respects their intent.
2. **PR's framing here is "verify the AI."** When the AI flow isn't running at all (the user picked a non-relevancy sort, RGA is hidden), there's nothing to verify — PR has no job. We hide it via the existing `body.rga-disabled` CSS gate.

The fetch IS still eager (fires on every search-settled), even though the panel is collapsed. Why: we want the observability layer (Phase 6E) to log PR fire-rate + content regardless of whether the user expanded the panel. The data is there when the user wants it; no first-click latency.

This mirrors production AI search UI patterns — Bing's "show sources", Perplexity's "view sources", ChatGPT's web mode. Clean default → explicit opt-in for source content.

## How we use PR in this build (and how those uses map to Coveo's positioning)

Coveo positions PR around three production use cases (see top of doc). Our build exercises **three patterns of our own** — two are within Coveo's official framing, one is a defensible variation specific to a demo context:

### 1. Fact-checking RGA on the live page (our primary use)

User asks a Pokémon question → RGA generates a paragraph → PR shows the verbatim source chunks below. The user can verify the AI didn't invent facts. **Trust narrative.** This isn't one of Coveo's three official use cases, but it's a defensible *demo-context* extension: showing both the AI's interpretation and the raw source content side-by-side answers the question every panel reviewer (and every real customer) silently asks — *"how do I know the AI didn't hallucinate?"*

### 2. Graceful degradation when RGA refuses

When RGA returns `cannotAnswer: true` (the model decided it couldn't ground confidently), PR still has results — *here's what's actually in the index that's semantically close to your question*. The system fails **informatively**, not silently. Maps directly to Coveo's "Customer-facing support + case deflection" use case: a frustrated user is what you avoid when the safety net says *"the AI couldn't synthesize anything, but here's the raw material — find what you need."*

### 3. The CRGA primitive — bring-your-own-LLM grounding (the bigger play)

For customers who can't use Coveo's hosted LLM (compliance, on-prem, specific model preference), CRGA flips the architecture: Coveo provides retrieval + passages (via the same PR API), the customer brings their own LLM and prompt. PR is the underlying building block. Maps directly to **Coveo's #3 official use case** — BYO-LLM integration with platforms like Salesforce Einstein, Microsoft Copilot, AWS Bedrock, Claude, GPT-4o, Gemini, etc.

We don't use this today because standard RGA + the Phase-6F closed-loop tuning fit our demo story better, but the path is open and PR is exactly what makes it scriptable. **This is the bridge between our Topic 1 deep dive and the Topic 2 customer pitch:** the API surface we built for our demo is the same primitive an enterprise customer would use to plug Coveo into their own GenAI stack.

## UI placement decision

We placed the panel **below RGA on the main search page**, not in a separate route. Trade-offs we considered:

| Placement | Pro | Con |
|---|---|---|
| ✅ **Below RGA on main page** | One-page demo flow; visible trade-off between RGA prose and PR verbatim; no extra route to navigate | Slightly busier page when search returns nothing relevant for PR |
| Separate `/passages` route | Cleaner "A/B" demo if you want to show PR-only mode | Extra navigation step; panel reviewers may never click |
| Embed on the Pokémon Detail Page (Phase 6C) | Naturally scoped to a single Pokémon ("featured passage about Charizard") | Couples Phase 8 to Phase 6C; Detail Page is a future build |

The main-page placement keeps the demo flow tight: type query → see results + RGA paragraph + extracted passages, all in one viewport.

## Architecture — RGA and PR are parallel, not chained

A subtle architectural point that's worth being explicit about (and panel-narrative material in its own right):

**Our standard RGA does NOT call the Passage Retrieval API.** Both use Coveo's Semantic Encoder (SE) under the hood, both run on the same indexed corpus, and both produce conceptually-similar chunks — but they're independent request paths. RGA performs its own internal chunk extraction during the answer-generation flow; PR is a separate endpoint that exposes a similar chunk-extraction primitive to developers.

```
                              query
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
       Search API           RGA pipeline       Passage Retrieval API
       (result list)        (chunks → LLM      (chunks → us)
                             → prose)
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                          Atomic UI
                          (3 surfaces)
```

So **PR's role in our app is fact-checking RGA**, not grounding it. The user sees the AI's synthesized answer above, and the verbatim source chunks below — they can verify with their own eyes that the AI didn't fabricate.

### Could PR ground RGA? Two paths

| Approach | Verdict |
|---|---|
| **Standard RGA** (what we use today) | **Can't inject custom chunks.** The pipeline is closed end-to-end: Coveo retrieves, chunks, grounds, and runs the LLM. We supply the prompt (Phase 6F closed loop) but not the chunks. |
| **CRGA — Custom RGA** | **Yes, this IS the path.** In CRGA, you bring your own LLM. Coveo's role is *just* retrieval + passages (via the PR API). You build the prompt template, you call your LLM, you control everything downstream of chunk extraction. CRGA is enabled on our org per Coveo's confirmation (2026-05-29). |

We didn't go with CRGA for our build because:

1. **Standard RGA's closed loop (Phase 6F) operates on Coveo's hosted LLM.** Moving to CRGA would require rebuilding the closed-loop tuning around a custom prompt template + a third-party LLM key (Anthropic / OpenAI / etc.)
2. **The eval (Phase 6D) measures Coveo's RGA quality**, which is the panel narrative we wanted
3. **Standard RGA = zero LLM-vendor decisions for the demo** — Coveo manages the model, we just measure + tune it

CRGA is a viable future migration path for a customer who needs to use their own LLM (compliance, on-prem, model choice). The fact that PR exists as a standalone API is precisely what makes that path possible — PR is the retrieval primitive that CRGA composes on top of.

## Why PR is complementary to RGA, not redundant

A panel question we anticipate: *"You already have RGA; why also Passage Retrieval?"* Three answers:

1. **Source-of-truth visibility.** RGA's answer is generated; the citations are pointers to documents but the panel reviewer has to click through to see the underlying sentence. PR surfaces that sentence directly. For "fact-check the AI" moments, PR is faster than clicking citations.

2. **Different speed/cost profile.** RGA has an LLM hop in the loop (token cost + ~1–3s of generation latency). PR has no LLM — it's pure retrieval, returning in ~100–300ms. For high-traffic queries where the customer cares more about speed than narrative, PR is the cheaper grounding answer.

3. **The "RAG building block" story.** This is Topic 1 deep-dive material. Coveo's PR API is the *exact* mechanism a customer would use to build their own LLM-powered application — RAG (Retrieval-Augmented Generation) systems need a retrieval source, and PR is that source. By using it ourselves, we're demonstrating the building block that customers would compose into their own AI features.

## Observability — Phase 6E cross-phase TODO closed

Per the cross-phase TODO from Phase 6E, the Grafana log payload now includes Passage Retrieval fields per search:

- `passage_retrieval_fired` — boolean; promoted to a Loki **stream label** so we can aggregate without `| json` parsing
- `passage_count` — integer; how many passages returned
- `passage_text` — top passage text, truncated to 500 chars
- `passage_source_uri` — `clickableuri` of the document the top passage came from

The dashboard now has a **Passage Retrieval fire rate** stat panel sitting next to the RGA fire rate. Side-by-side these tell the story: "are we returning AI prose + verbatim passages for the same queries?" When RGA fires but PR doesn't, that's a signal (and vice versa).

Implementation: a tiny shared in-memory state module (`passage-retrieval-state.js`) decouples `passage-retrieval.js` from `observability.js`. PR writes its result there keyed by `searchUid`; observability reads it when building the Grafana log payload. If PR hasn't settled by log time (rare; PR is faster than RGA), observability logs empty passage fields — empty is more honest than stale.

## Files involved

```
atomic-search/index.html                — <div #passage-retrieval-panel> below RGA
atomic-search/src/passage-retrieval.js  — subscribe → fetch → render
atomic-search/src/passage-retrieval-state.js — shared store for cross-module observability
atomic-search/src/observability.js      — reads PR state, adds 4 fields to log payload
atomic-search/api/log-query.js          — passage_retrieval_fired added as Loki stream label
atomic-search/src/style.css             — .passage-panel + .passage-card styles
observability/grafana-dashboard.json    — new "Passage Retrieval fire rate" panel
scripts/ml/associate_models.sh          — extended to wire pokemon-pr alongside RGA + SE + QS
```

## Kill-switch + fallback behavior

- **`VITE_PASSAGE_RETRIEVAL_ENABLED=false`** — disable the call entirely (silent no-op).
- **422 UNPROCESSABLE_ENTITY** — typically means the PR model is still building. We swallow the error silently rather than spamming console.error during the build window.
- **Network error / 5xx** — `console.warn` + hide the panel. The search experience stays intact.

## Sources

- [Use the Passage Retrieval API](https://docs.coveo.com/en/o86c8334/)
- [Coveo Passage Retrieval product page](https://www.coveo.com/en/platform/passage-retrieval-api)
- [Passage Retrieval API on AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-akx6trandwmjw)
