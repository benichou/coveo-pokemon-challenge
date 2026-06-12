# Presentation 1 — Tech Deep-Dive · Rehearsal Notes

> Coaching notes for delivering `01-tech-deep-dive.md` (14 slides).
> For each slide: **what to say**, **the build/config behind it**, **likely questions**.
> North star to repeat: **"Three UI surfaces · two loops · one Coveo brain."**

---

## 📊 Live numbers to use (verified 2026-06-10 — re-verify interview morning)

The slides hardcode "62% → 78%" — **stale**. Use these instead:

| Metric | Today (06-10) | v1.1.0 era (06-05→06-10) |
|---|---|---|
| Accuracy | **76%** | 76–80% (peaked 80% on 06-08) |
| Precision | **89%** | 89–92% |
| Hard recall | 85.8% | 85–87% |
| Citation precision | 77.7% | 77–78% |

- **Live RGA prompt: v1.1.0** (applied 2026-06-01), 8 rules. Unchanged since.
- **Talk track:** "v1.1.0 lifted accuracy from a 62% baseline to ~76–80% — currently 76% — with precision ~90%. The loop has held v1.1.0 steady since June 1: it measures every morning and correctly chose *not* to re-tune. That restraint is the guardrails working, not the loop being idle."
- Cron is healthy — eval-runs fresh through today. Re-run `ls eval-runs/*-full.json` the morning of to confirm the dashboard isn't stale.

---

## 🎤 Slide 1 — Cover: "Pokédex Search"

### What's on the slide
- Title: **Pokédex Search — A Coveo FDE technical challenge**
- Your name + "Forward Deployed Engineer candidate"
- **Four live URLs**: the app, GitHub repo, RGA quality dashboard, Grafana observability dashboard

### Main notes to say (≈30 sec — opener, keep it tight and confident)
> "Hi — I'm Franck. Over the next ~10 minutes I'll walk through the Pokémon Challenge build. I'll show you the **live demo early** — right after the architecture diagram — then drill into the choices behind each piece, and we'll leave time for Q&A at the end."

Then the line that earns attention:
> "Everything you'll see is **live right now**. There are four URLs on this slide — the app, the repo, an AI-quality dashboard, and a query-observability dashboard. Feel free to pull them up on your phone and follow along."

### The framing this slide sets up (your north star — repeat at the close)
**"Three UI surfaces · two loops · one Coveo brain."** Plant it now; it's also your closing slide.

### Why these four URLs matter (so you can speak to any of them if asked)
| URL | What it proves |
|---|---|
| `pokemon-search-one-chi.vercel.app` | The actual search experience (the core deliverable) |
| `github.com/benichou/coveo-pokemon-challenge` | Everything is as-code, public, reproducible |
| `pokemon-rga-dashboard.vercel.app` | You measure AI quality continuously (bonus) |
| Grafana public dashboard | Query observability loop (bonus) |

### Delivery coaching
- **Don't read the slide.** They can see the URLs. Your job here is tone-setting: calm, "I built something real and it's running."
- **Signal the structure** ("demo early, then the why, then Q&A") — panels relax when they know the shape.
- The phrase *"follow along on your phone"* is a confidence flex — only say it if the URLs are genuinely up. Have them pre-loaded.

### Likely questions at this stage
- **"Is this your own Coveo org?"** → Yes, a free trial org named `benichou`, provisioned end-to-end. One org, three surfaces.
- **"How long did this take?"** → Honest answer; tie it to "I went for full ambition — every advanced + bonus item, plus three things the brief didn't ask for."
- **"What's the AI-quality dashboard?"** → "That's the closed-loop quality system — slides 9 and 10; the most ambitious part."

---

## 🎤 Slide 2 — What I built (+ deep reservoir for the 3 UI surfaces)

> ⏱️ **Slide budget: ~40 sec.** This is a fast recap (3 thumbnails). Do NOT deliver the depth below here — it's your **Q&A reservoir** and the script for **Slide 8** (dedicated three-surfaces slide). Trim line if long: drop straight to "three surfaces, one Coveo brain — I'll come back to each."

### What's on the slide
Three clickable thumbnails: **Atomic main page** · **Pokémon Detail Page** · **Coveo MCP Server**. Tagline: *"three user-facing surfaces powered by one Coveo brain."*

### What to say on the slide (~40s)
> "The brief asks me to index pokemondb.net into a Coveo org and ship a search experience on top — that's the deliverable. I went for full ambition: every advanced item, the bonus, plus three things the brief didn't ask for.
>
> The headline is this: **one Coveo org — one index, one pipeline, four ML models — powering three different consumption surfaces.** A browser **list experience** built on Atomic. A **detail page** built on Headless + React. And an **MCP server** that exposes the same index to AI agents. Same brain, three front-doors. I'll walk through each."

Then advance. The "one brain, three surfaces" line is the whole point of this slide.

---

### 🧠 THE "ONE COVEO BRAIN" — what all three share (say this if asked "what do they have in common?")
All three hit **the same org** (`benichouu9fose4g`), the **same default query pipeline**, the **same 4 ML models** (RGA · Semantic Encoder · Query Suggest · Passage Retrieval), and the **same unified index** of 1,353 docs. They differ only in *how they consume* it:
- Atomic = declarative web components, browser list view
- Headless+React = programmatic SDK, custom detail page
- MCP = protocol endpoint, AI-agent clients

> One-liner: *"I didn't build three search systems. I built one Coveo brain and put three different front-doors on it."*

---

## SURFACE 1 — Atomic main page (the deep one)

### What it is / what to say
> "The main page is built with **Coveo Atomic** — Coveo's library of pre-built search web components. The entire search experience is **declarative HTML**: I drop `<atomic-search-interface>` on the page, nest `<atomic-search-box>`, `<atomic-facet>`, `<atomic-generated-answer>`, `<atomic-result-list>` inside it, and point the interface at my org with an access token and org ID. Atomic handles state, query lifecycle, facets, and analytics for me. That's the Atomic value proposition: **five components and you have faceted search with an AI answer panel** — minimal JavaScript."

### How it connects to the Coveo org (the key relationship)
- `<atomic-search-interface search-hub="pokemon-search" analytics ...>` — declared in `atomic-search/index.html`.
- In `atomic-search/src/main.js`: `await searchInterface.initialize({ accessToken, organizationId })` — that's the only wiring. `accessToken` = the **anonymous search API key**; `organizationId` = `benichouu9fose4g`.
- `search-hub="pokemon-search"` routes every query through the **default pipeline**, which has the 4 ML models associated — so the Atomic page gets RGA answers, semantic ranking, and query suggestions **for free**, just by talking to the right hub.
- `fields-to-include='[...15 fields...]'` tells Coveo which indexed fields to return per result.
- `analytics` attribute → fires Coveo UA events automatically (plus my own Grafana logging on top).
- `executeFirstSearch()` kicks off the initial query.

### How Atomic was loaded (a likely "gotcha" question)
Atomic is **loaded from Coveo's CDN**, not npm: `<script type="module" src="https://static.cloud.coveo.com/atomic/v3/atomic.esm.js">` + the CDN theme CSS. **Why:** self-hosting via `@coveo/atomic/loader` inside Vite serves the JS but doesn't pipe Atomic's **runtime assets (i18n locale files, icons)** through Vite's dev server — you get untranslated UI like "(between-parentheses)" instead of "(123)". The CDN serves JS + assets together transparently. (`package.json` only has `@coveo/headless`, not `@coveo/atomic` — be ready for that.)

### Where I dropped BELOW Atomic into Headless (shows depth — volunteer this)
Atomic is built *on top of* Coveo Headless. I reached into the same engine for three things Atomic's components don't do out of the box (all in `src/main.js`):
1. **First/last pager buttons («/»)** — `<atomic-pager>` only ships prev/next + numbered pages. I used `buildPager(engine)` on the **same engine** and called `selectPage(1)` / `selectPage(maxPage)`.
2. **RGA visibility gate** — RGA grounds its answer on the top-N results. When a user sorts by Name/Date, the top-N becomes alphabetical → off-topic → RGA correctly refuses → panel goes silently empty → looks broken. I `engine.subscribe()` to watch `sortCriteria` and hide the RGA panel (with an explanatory note) whenever sort ≠ relevancy.
3. **Empty-answer collapse** — the empty `<atomic-generated-answer>` host still takes a flex slot and misaligns the toolbar; I toggle a body class based on the `generatedAnswer` state slice.
4. **Source relabeling** — facet labels via i18n `caption-source` bundle (`pokemondb-sitemap`→"PokemonDb", `pokemondb-push`→"PokeAPI"); per-result via `<atomic-field-condition must-match-source=...>`. Underlying source names stay intact so scripts/tests/queries don't break.

### 🔧 Code refresher — Atomic
- `atomic-search/index.html` — all the declarative components, the result template (renders in **shadow DOM** → styles must be inline), CDN script tags.
- `atomic-search/src/main.js` — `initialize()`, the 4 Headless add-ons above, observability + PR hooks.
- Result-click navigation: `<atomic-result-link href-template="/pokemon.html?name=${raw.pokemon_name}">` → sends you to Surface 2.

### 🧠 Deep-Coveo Q&A — Atomic
- **"What auth does the frontend use?"** → "Today it passes an **anonymous search API key** as `accessToken` — fine for a public Pokémon demo. The variable's named `SEARCH_TOKEN` but it's the API key. **Production would mint short-lived per-user search tokens** from a backend — that's the auth gap I call out on the production-hardening slide."
- **"Why Atomic and not build from scratch / Headless?"** → "Atomic is the right tool for a standard list+facets+answer experience — fastest path, accessible, themeable. I used Headless where I needed *composition* — that's the detail page."
- **"How are facets configured?"** → 5 facets declared in HTML: type, generation, source, is_form_variant, abilities (the abilities facet uses `sort-criteria="occurrences"` + `with-search`). Facet fields are the indexed fields from `config/fields.json`.
- **"How does Query Suggest reach the box?"** → `<atomic-search-box number-of-queries="6">` pulls from the `pokemon-qs` model on the pipeline; I seeded it via Default Queries CSV (cold-start solve — slide 7).
- **Fallback if stumped:** "That specific behavior lives in `src/main.js` / `index.html` — happy to open it and walk the exact lines."

---

## SURFACE 2 — Pokémon Detail Page (Headless + React)

### What it is / what to say (~high level)
> "Click any result and you land on a **detail page I built with Coveo Headless + React** — same Vite project, second entry point, one Vercel deploy. This page composes **three Coveo round-trips in parallel** on load: a **Search** query to fetch the Pokémon I clicked (the hero card), a **Passage Retrieval** call for a 'featured insight' chunk, and a **second Search** filtered to the same generation for a 'related Pokémon' grid. This is the FDE narrative in miniature: **for a standard list page, ship Atomic; for a bespoke page that needs multiple composed queries and full styling control, drop to Headless on the customer's existing React stack.**"

### The three surfaces on the page (all in `src/pokemon-detail/App.tsx`)
1. **Hero** — `buildSearchEngine()` + `buildResultList()` + `buildSearchBox()`; submits the slug as the query, takes `results[0]`, renders image/dex#/types/generation + "View source page" link back to pokemondb.
2. **Featured insight** — a **direct `fetch()` POST** to the Passage Retrieval API: `https://{orgId}.org.coveo.com/rest/search/v3/passages/retrieve` (note the **org-scoped subdomain**, not platform.cloud.coveo.com), `Bearer` search token, `query: "what is {slug}?"`, `maxPassages: 3`. Then `sortPassagesByReadability()` picks the cleanest chunk.
3. **Related grid** — a **second** `buildSearchEngine()` with `q = @generation=="Generation N"`, returns 6 same-gen Pokémon, excludes the hero.

### Why two Headless engines (likely question)
Each Headless engine manages **one query state at a time**. Hero and Related run independent queries → two engines. Each engine is cheap (a small redux-like store + an HTTP client).

### The markdown/table heuristics (be honest these are pragmatic hacks)
Passage Retrieval's chunker sometimes **linearizes tables** (row separators collapse to `| |` runs) so markdown-it renders "pipe soup." I added `maybeReconstructTable()` (re-synthesizes a header + `|---|` separator) and a `noiseScore()` that treats pipes as noise **only when there's no GFM separator row** — so well-formed tables rank readable and fragments rank noisy. Rendering via markdown-it with `html:false` (XSS guard) + `linkify:false`.

### 🔧 Code refresher — Detail page
- `atomic-search/pokemon.html` + `atomic-search/src/pokemon-detail/{main.tsx,App.tsx}`.
- Multi-entry Vite: `vite.config.js` `rollupOptions.input: { index, pokemon }`, `@vitejs/plugin-react@^4` (NOT ^6 — needs Vite 8; we're on Vite 6).
- React 19, `@coveo/headless` ^3.51.

### 🧠 Deep-Coveo Q&A — Detail page
- **"How do you fetch one Pokémon by slug — is that a key lookup?"** → "It's a relevance query for the slug and I take the top result, not a true primary-key fetch. For a single-doc lookup an exact field query (`@pokemon_name==`) would be more precise; the relevance query works because slugs are distinctive. Honest trade-off for demo speed."
- **"Why `q` and not `cq` for the generation filter?"** → "`cq` (constant query) isn't exposed via a top-level Headless controller, and for a single-shot fetch putting `@generation==` in `q` works fine. At scale I'd use the advanced query / `cq` via engine config."
- **"Passage Retrieval prerequisites?"** → "A CPR (Passage Retrieval) model **and** a Semantic Encoder on the same pipeline. The endpoint is org-subdomain-scoped, not the platform host — that tripped me up initially."
- **"Why phrase the PR query as a question ('what is X?')?"** → "Empirically surfaces more useful passages than the bare slug — gives the semantic ranker more to ground on."
- **Fallback:** "It's ~410 lines in `App.tsx` — I can open the exact hook."

---

## SURFACE 3 — Coveo MCP Server

### What it is / what to say (~high level)
> "The third surface is for **AI agents, not humans**. Coveo ships a **Hosted MCP Server** — Model Context Protocol, the open standard for connecting LLMs to tools. I configured a `pokemon-mcp` server on my org and wired it into Claude Code. Now the *same* index — same pipeline, same RGA model — is addressable by any MCP client: Claude Code, Claude Desktop, ChatGPT Enterprise, Cursor — with **zero additional code per client**. It exposes four tools: **search**, **fetch**, **get_passages**, and **answer**. This is the 2026 enterprise story: 'how does our content power our AI agents?' — Coveo's answer is 'your existing index already does, via MCP.'"

### The four tools → which Coveo surface each maps to
- `search` → Search API (ranked list)
- `fetch` → single-document retrieval by ID
- `get_passages` → Passage Retrieval (chunks + scores)
- `answer` → **RGA** (grounded answer + citations) — uses answer config `pokemon-rga-config`

### How it's configured (the as-code honesty point)
- Source-of-truth: `config/mcp/pokemon-mcp.yaml`. **But there is no public admin REST API for MCP config yet** — I verified by probing 8 candidate endpoints (all 404, via `scripts/mcp/discover_api.sh`). So the YAML is versioned and **manually mirrored** into the Console; the day Coveo ships the API, I swap in an apply script (same pattern as the RGA prompt's `apply.py`).
- `search`/`fetch`/`get_passages` are **auto-added** when you pick a pipeline; **`answer` I added manually** (it needs an explicit answer-config + custom description).
- **Server instructions** = the system prompt every client gets on connect — a Pokémon-grounded tool-selection guide. Without it, LLMs default to `search` for everything.
- Endpoint shape gotcha: `https://platform.cloud.coveo.com/api/v1/organizations/{orgId}/mcp/server/{UUID}` — NOT the marketing alias `mcp.cloud.coveo.com/mcp`.
- Wired into Claude Code via `.claude/mcp.json` with env-var substitution; 6th API key `pokemon-mcp` (anonymous, hub-scoped to `MCP_pokemon-mcp`).

### The demo moment to mention (agentic composition)
> "In the live demo, the most interesting moment is the agent **chaining tools autonomously**: asked for 'Bulbasaur's full document,' it recognized `fetch` needs an ID, called `search` first to discover it, learned the index schema mid-conversation, and then *proposed an `advancedQuery` refinement for an earlier question*. Four queries and it taught itself the tool surface. Zero code on my side."

### 🧠 Deep-Coveo Q&A — MCP
- **"What about permissioned/enterprise content — security?"** → "I use the **anonymous API key** because Pokémon is public. For permissioned content the server supports **OAuth**, and MCP inherits Coveo's **Security Identities** — so an agent only sees what that user is allowed to see. Same permission model as the search UI."
- **"Is MCP traffic observable / isolated?"** → "Coveo auto-creates a separate search hub `MCP_pokemon-mcp`, so agent traffic is segregated from UI traffic for analytics + revocability."
- **"Why is `answer` special?"** → "It runs RGA, so it needs an answer-configuration binding (`pokemon-rga-config`) — that's why it's the one tool you add by hand."
- **Fallback:** "The full config is in `config/mcp/pokemon-mcp.yaml` with the server instructions verbatim — happy to open it."

---

## 🎤 Slide 3 — Architecture (THE most important slide · Coveo choices + config)

> ⏱️ **Slide budget: ~90 sec.** This is the spine of the talk — earns the most time. Trim line if long: trace only the top row (ingestion → org) + the two loops by name; skip narrating individual UI surfaces (slide 8 covers them).

### What's on the slide (6 zones, 4 flows)
- **Top row:** 📚 Data sources → 🛠️ Ingestion (95% as-code) → 🧠 Coveo Cloud Org
- **Middle:** 🎯 Three UI surfaces (one retrieval brain)
- **Bottom:** 📊 Query observability loop · 🔬 Continuous AI quality (closed) loop

### What to say — trace the 4 flows (don't read boxes; trace arrows)
> "One Coveo org, three UI surfaces, two loops. Four flows worth tracing.
>
> **(1) Ingestion — dual-source.** pokemondb.net's sitemap into a Coveo **Sitemap source**; PokéAPI per-form variants pushed through a Python **Push source**. Both land in one unified index.
>
> **(2) Three surfaces, one brain.** Atomic list page, Headless+React detail page, and the MCP server for AI agents — all reading the *same* org, the *same* default pipeline, the *same* four ML models.
>
> **(3) The closed quality loop** (right side): daily eval measures RGA quality → analyzer proposes prompt refinements → guardrails decide → applies via Coveo's ML Models API → the dotted arrow back is the loop closing.
>
> **(4) Parallel observability** (left side): every user search fires a fire-and-forget log to Grafana Cloud Loki through a Vercel proxy — the write token stays server-side.
>
> That's the architecture. Now let me show it running, then drill into the choices."

---

### 🟦 COVEO CHOICES & CONFIGURATION — highlight these (the heart of this slide)

**This is what makes you sound like an FDE, not a frontend dev. Hit these explicitly:**

1. **Sitemap source over Web Crawler (a deliberate Coveo Leading-Practices call).**
   > "Coveo's leading practice is: when a site publishes a sitemap, prefer the **Sitemap source** over the Web Crawler — it's faster, lighter, and Coveo handles throttling. pokemondb publishes a 12,915-URL sitemap, so that's Source A. I pivoted to this on day one after reading the leading-practices doc."

2. **Dual-source — a data-shape decision, not redundancy.**
   > "Source A (Sitemap) gives canonical pages, zero code. But a Sitemap source can't preserve **form-level identity** — pokemondb has one Charizard page covering base + Mega-X + Mega-Y. So Source B is a **Python Push source** reading PokéAPI's per-form endpoints, adding 325 form-variant docs **plus enrichment** (base stats, abilities) that pokemondb's HTML doesn't expose cleanly. Two sources, one index, one ranked list — 1,353 docs."

3. **Org-level field schema — 14 custom indexed fields.** *(Use 14, not 5 — see flag below.)*
   > "Indexed fields are an **org-level schema** — they exist independently of any source. I defined 14 custom fields: 5 populated by the Sitemap's scraping selectors (name, type, image, dex#, generation), and 9 more populated by the Push source from PokéAPI (the six base stats, abilities, is_form_variant, base_species)."

4. **Versioned scraping + URL-filter config (the as-code + quality story).**
   > "The Sitemap source's behavior is fully versioned: `scraping.json` holds the XPath selectors that extract each field, and `url_filter.json` is a single source-of-truth for which URLs are in scope — read by *both* the apply script and the test suite so they can never disagree. That filter caught a real leak — pokemondb's `/pokedex/shiny` list page was being indexed as a Pokémon."

5. **One default pipeline = the single retrieval brain.**
   > "All four ML models — RGA, Semantic Encoder, Query Suggest, Passage Retrieval — are associated with **one default pipeline**. Every surface routes through it via a search hub, so they all inherit the same relevance and AI treatment. I didn't build per-surface pipelines; one brain, consistently applied."

6. **Two search hubs, same pipeline (segregation for observability).**
   > "`pokemon-search` is the UI hub; Coveo auto-created `MCP_pokemon-mcp` for agent traffic. Both route to the same default pipeline, but separating the hubs lets me isolate agent traffic from human traffic in analytics."

7. **6 least-privilege API keys.**
   > "Six API keys, each scoped to exactly one job: push, admin, anonymous-search, Anthropic-judge, ML-models-editor, and MCP. For example the ML-models-editor key can *only* edit ML models — I found empirically that the admin key's scope did **not** include Models:Edit, so I minted a dedicated key rather than widen the admin one. Least privilege by default."

8. **95% as-code.**
   > "Everything governing the search experience — fields, source defs, scraping rules, URL filter, mappings, ML model behavior — is versioned JSON/YAML applied via Coveo's REST API. `scripts/bootstrap.sh` provisions a fresh org end-to-end. The only Console-gated steps are one-time setup Coveo's product design requires — I'll detail those on the config slide."

---

### ⚠️ FIELD-COUNT FLAG (don't get contradicted)
- `config/fields.json` defines **14 custom fields** — the deck and `config/README.md` say "5."
- **Say 14** ("five from the sitemap scrape, nine from PokéAPI enrichment"). The "5" refers only to the Sitemap selectors.
- Also note: the Atomic `fields-to-include` lists **15** — that's the 14 custom fields + the standard `source` field. (Indexed fields ≠ fields-to-return — different concepts.)
- Consider fixing the deck + README to "14" before interview day for consistency.

### 🔧 Code refresher — config
- `config/fields.json` — 14 custom fields (org-level schema)
- `config/source/definition.json` — `pokemondb-sitemap`, type SITEMAP · `config/source/scraping.json` — XPath selectors · `config/source/url_filter.json` — scope (read by script + tests)
- `config/source_push/definition.json` — `pokemondb-push`, type PUSH
- `scripts/bootstrap.sh` — one-command full provisioning · `scripts/setup/mappings.sh` — mappings via REST (no Console UI for mappings on modern orgs)

### 🧠 Deep-Coveo Q&A — architecture/config
- **"Why Sitemap over Web Crawler?"** → leading practice when a sitemap exists; Coveo handles throttling; lighter + faster. (docs.coveo.com/en/malf0160)
- **"Push vs Crawler/Sitemap trade-offs?"** → Push = you control freshness (on-demand re-push) + per-form identity + enrichment, but you own throttling (PokéAPI 100 req/min). Sitemap = zero code, scheduled refresh, Coveo throttles, but one doc per canonical slug.
- **"How do both sources share fields?"** → fields are org-level; each source maps its extracted/pushed values into the same field schema. Mappings via `scripts/setup/mappings.sh`.
- **"Why one pipeline, not per-surface?"** → consistency + single source of relevance truth; search hubs differentiate traffic without forking the brain.
- **"How do you delete a bad doc?"** → Push API DELETE works only on Push sources; for the Sitemap source the durable fix is updating `url_filter.json` + rebuild (surgical delete doesn't survive refresh). The `/pokedex/shiny` leak is the worked example.
- **Fallback:** "The whole org is reproducible from `config/` + `scripts/bootstrap.sh` — I can walk the exact resource declarations."

---

## 📎 Coveo concepts cheat-sheet (Q&A reference — came up while prepping)

### Search hub — what it is + where in the Console
A **search hub** is a *label identifying which interface a query came from* — a string sent with every query (yours: `pokemon-search`). It does three jobs:
1. **Pipeline routing** — pipeline *conditions* match on search hub ("when hub is X, use this pipeline") → selects the pipeline → selects the ML models + ranking.
2. **Analytics segmentation** — it's the `originLevel1` dimension in Usage Analytics; slice metrics per interface.
3. **Traffic isolation** — keeps surfaces' traffic distinct even on a shared pipeline (why Coveo auto-made `MCP_pokemon-mcp` for agent traffic).

**Mental model:** NOT an object you create — a value you assign client-side (`search-hub="pokemon-search"` on `<atomic-search-interface>`); the Console only *references* it.
**Where it surfaces in the Console:**
- **Search → Search Pages** — hosted pages each carry a hub
- **Search → Query Pipelines → [pipeline] → Conditions** — *only if* a condition references the hub (you route to **default**, so likely no explicit condition — normal)
- **Analytics** — as `originLevel1`; live Atomic traffic shows `pokemon-search` here = end-to-end proof
- ⚠️ No dedicated "Search Hubs" list page exists — it's a string, seen where referenced. If asked exact path, say *"under Search in Query Pipeline conditions, and as originLevel1 in Analytics"* (menu labels shift between console versions).

### Search Page — purpose + does it affect results?
A **Coveo Search Page** = a **Console-hosted search UI** (box + facets + result list), hosted by Coveo, no front-end deploy needed. You built `pokemon-search` (Simple Builder) in Phase 3 as a **validation surface** before the Atomic app.

**The FDE one-liner:** **"The search page is *presentation*; the query pipeline is *relevance*."**

A search page affects results in only 3 ways — one ranking, two not:
1. **Indirectly via its search hub → pipeline routing** (the only ranking lever — the page picks *which* pipeline runs the ML/ranking).
2. **Baked-in filters / advanced query (`cq`)** — a page can scope results (yours doesn't).
3. **Facets / sort / displayed fields** — presentation + *user-driven* filtering, not relevance.

→ Two pages on the same pipeline rank **identically**. Your hosted page is NOT what powers the live demo — the **Atomic app on Vercel** is. They share the `pokemon-search` hub → both hit the default pipeline → same ranking. Deleting the hosted page wouldn't change the Atomic app at all.

**Say it:** *"A Search Page is a Console-hosted UI — I used one for early validation. But it's presentation; ranking lives in the pipeline. The page only influences results by which hub it sends, which selects the pipeline. My hosted page and Atomic app share the hub, so they rank identically — the page isn't where relevance is decided."* → bridges to pipeline + 4 ML models (slide 7).

---

## 🎤 Slide 4 — LIVE DEMO (⏱️ HARD CAP 4:00 — your #1 overtime risk)

> The demo is where minutes disappear. Discipline > completeness. **If you hit a checkpoint late, SKIP to the next surface — do not finish the current one.** Better to show 4 surfaces shallow than 2 surfaces deep and blow the clock.

### ✅ PRE-FLIGHT (do this BEFORE the panel starts — never fumble live)
Pre-load these **5 tabs in order**, left to right:
1. `pokemon-search-one-chi.vercel.app` (Atomic main)
2. `pokemon-search-one-chi.vercel.app/pokemon.html?name=charizard` (Detail)
3. Claude Code terminal, **MCP pre-launched**, ready to type `/pokemon-mcp demo`
4. `pokemon-rga-dashboard.vercel.app` (RGA dashboard)
5. Grafana public dashboard URL
- Have a **90-sec screen recording** of the full flow saved locally as Wi-Fi-death fallback.
- Have **yesterday's MCP run screenshot** ready in case the live MCP call flakes.

### ⏱️ TIMED SCRIPT (4:00 cap, with checkpoints)

**Opener (say while switching to browser):**
> "You've seen the architecture — let me show it running. We'll touch all four flows in about four minutes."

**[0:00–0:45] Atomic main page** — Tab 1
- Refresh once → *"5 random biome themes, all CSS — Grassland, Volcano, Ice…"* (1 sentence, don't linger)
- Type **`charizard`**. Point at: RGA answer streaming in → citation to pokemondb → Passage Retrieval panel below.
- **Say:** *"The AI answer is grounded on retrieved content with a citation — same retrieval primitive an enterprise would use to ground their own LLM."*
- Click the **Fire** type facet, then the **Source** facet → show PokemonDb + PokeAPI items mixing.
- **Say:** *"Both ingestion sources, unified — one ranked list."*
- ✅ **CHECKPOINT: at 0:45 you must be clicking into the detail page. If not, stop facet-clicking and move.**

**[0:45–1:30] Detail page** — click the Charizard result (or Tab 2)
- Point at: Hero card (image, type badges, dex#) → Featured Insights (Passage Retrieval) → Related grid.
- **Say:** *"Three Coveo queries fired in parallel on this one page — built with Headless and React, not Atomic. Right SDK per surface: Atomic for the list, Headless where I need composition."*
- ✅ **CHECKPOINT: at 1:30 move to MCP.**

**[1:30–2:45] MCP via Claude Code** — Tab 3
- Type **`/pokemon-mcp demo`**. Let the 4 tools fire (search / fetch / get_passages / answer).
- **Say:** *"Same Coveo org — now answerable from Claude Code through MCP. Zero extra code per client. Watch it chain tools: it realizes fetch needs an ID, calls search first, learns the schema mid-conversation."*
- ⚠️ **If it flakes → cut immediately to the screenshot, say the same line, move on. Don't debug live.**
- ✅ **CHECKPOINT: at 2:45 move to dashboard.**

**[2:45–3:45] RGA dashboard** — Tab 4
- Point at: time-series chart (accuracy / precision / hard-recall) → chart markers = prompt-change applies → click a marker → diff view.
- **Say:** *"Every morning at 06:00 UTC the eval runs. These markers are the closed loop applying new prompts. Accuracy went from a 62% baseline to the high 70s — sitting around 76% today, precision near 90%. This is what 'production AI' actually means — a loop, not a one-time deploy."*
- ✅ **CHECKPOINT: at 3:45, START WRAPPING regardless of where you are.**

**[3:45–4:00] Grafana (OPTIONAL — only if on time)** — Tab 5
- Show 1–2 panels (top queries, RGA fire rate). One sentence: *"Same observability story — every user search logged here, public dashboard, deployed as code."*

**Closing (back to slides):**
> "That's the build running. Now let me walk through the choices behind each piece — starting with how we ingest content."

### ✂️ TRIM ORDER (if running long, cut in THIS order)
1. **Grafana** (it's already optional — cut first)
2. **Facet-clicking** on the Atomic page (show RGA + citation only)
3. **Related grid** narration on the detail page (just point, don't explain)
4. NEVER cut: the RGA dashboard (it's your differentiator) or the MCP tool-chaining moment (your wow).

### 🧠 Likely questions DURING/AFTER the demo
- **"Is that answer cached / same every time?"** → *"No — RGA's retrieval is deterministic but the LLM generation is stochastic, so wording varies while facts + citations stay stable. I deliberately didn't cache — it'd mask the quality regressions my eval is built to catch."*
- **"What happens if you ask something not in the index?"** → *"RGA refuses rather than hallucinating — that's rule 3 in my prompt, and I test it with 15 refusal questions in the golden set."*
- **"Why did the AI answer disappear when you sorted by name?"** → *"RGA grounds on the top-N results; non-relevance sorting makes those off-topic, so it correctly declines. I gate the panel + show a note explaining it."* (only comes up if you demo sorting — probably skip sorting in the demo)
- **Fallback if anything breaks:** *"Let me show you the recording / a screenshot of yesterday's run"* — calm, pre-prepared, move on.

### Demo delivery rules
- **Talk while it loads** — never narrate dead air watching a spinner.
- **One sentence per surface** for the framing line — the panel reads the screen, you add the *why*.
- **Watch the clock, not the screen** — a 4-min demo that lands beats a 7-min demo that's "thorough."

---

## 🎤 Slide 5 — Why dual-source ingestion (NOT a repeat of slide 3)

> ⏱️ **Slide budget: ~60 sec.** The trade-off table is the whole slide.

### ⚠️ How this slide differs from slide 3 — READ THIS FIRST
- **Slide 3 = WHAT** (named it, gave the *data-shape* reason: form identity). ~10 sec.
- **Slide 5 = WHY** (defends it via the *operational trade-off* matrix: effort / throttling / freshness). ~60 sec.
- **THE FIX so they don't overlap:** on slide 3, keep it to "a sitemap can't preserve form-level identity, so a Push source adds the variants + enrichment." **Move all effort/throttling/freshness talk to slide 5.** Don't say "zero code / Coveo throttles" until this slide.
- **Open slide 5 with the demo callback** — a fresh hook, not a re-statement: *"Remember the 1,353 docs mixing in the result list? That's two sources unified. Here's why two."*

### What's on the slide
A trade-off table: **Source A (Sitemap)** vs **Source B (Push)** across 5 rows — Effort · Throttling · Freshness · Form variants · Use for. Takeaway: *"different sources serve different facets of the same data."*

### What to say (~60 sec) — walk the TABLE, that's the new content
> "Remember the 1,353 documents mixing in the result list during the demo? That's two ingestion sources unified into one index. Here's *why* two — and it's a deliberate split, not redundancy.
>
> **Source A is a Coveo Sitemap source.** Effort: basically zero — just a versioned scraping config; Coveo does the crawling. **Throttling: Coveo handles it automatically.** Freshness: scheduled refresh. It gives me one clean doc per canonical Pokémon page.
>
> **Source B is a Python Push pipeline.** Here the trade-offs flip: **I** own the code, and **I** own the throttling — PokéAPI caps at 100 requests a minute, so the pipeline rate-limits itself. In exchange I get on-demand freshness — I re-push whenever I want — and, critically, **one document per form**: Mega, Hisuian, Galarian variants each get their own doc, which the sitemap collapses into a single page.
>
> So the rule isn't 'one source is right.' **Sitemap for breadth and zero-effort canonical coverage; Push for depth, form-level identity, and the PokéAPI enrichment.** The choice fell out of an hour inspecting the actual data — which is the real lesson: **ingestion architecture is a data question, not a tooling question.**"

### The meta-lesson to land (this is the FDE signal, and it's unique to slide 5)
> *"I didn't pick 'Web Crawler' off a menu of design patterns. I looked at the data shape first — pokemondb's HTML vs PokéAPI's JSON — and the dual-source split fell out of that. Source choice = data inspection × downstream use case."*

### 🧠 Deep-Coveo Q&A — dual-source
- **"Why not just Push everything / why keep the Sitemap source at all?"** → *"Pushing 1,028 canonical pages means I own scraping + throttling + freshness for content Coveo will crawl for free. Sitemap is the leading practice for breadth; I only drop to Push where it buys me something the sitemap can't — form identity + enrichment."*
- **"Why not just the Sitemap + scrape the forms from pokemondb too?"** → *"pokemondb puts all forms on one page (tabs), so there's no per-form URL to index. PokéAPI exposes per-form endpoints — that's the only clean source of form-level identity."*
- **"How do you avoid duplicate docs across the two sources?"** → *"Different doc identities — canonical slug vs per-form slug — and `is_form_variant` flags the Push docs. They're complementary, not overlapping."*
- **"PokéAPI throttling — how?"** → *"PokéAPI's fair-use cap is ~100 req/min; the Push pipeline self-rate-limits. Coveo's Push API itself I batch into the documents endpoint."*
- **Fallback:** *"The Push pipeline is in `push-pokemon/` — scrape, enrich via PokéAPI, transform, POST to the Push documents endpoint. Happy to open it."*

### 🔧 Code refresher — ingestion
- Source A: `config/source/{definition,scraping,url_filter}.json` (`pokemondb-sitemap`, SITEMAP)
- Source B: `push-pokemon/` Python pipeline + `config/source_push/definition.json` (`pokemondb-push`, PUSH)
- Numbers: 1,028 sitemap + 325 push form-variants = **1,353 docs**

---

## 🎤 Slide 6 — Coveo config: code vs Console

> ⏱️ **Slide budget: ~50 sec.** ⚠️ **This is the #1 TRIM candidate in the deck** — if you're running long, fold it into slide 7 (see trim note below) and save ~45 sec. The two file-trees are for *visual credibility*, not for reading aloud.

### What's on the slide
Two columns: **✅ Code-as-source-of-truth** (config/ + scripts/ + push-pokemon/ + rga-eval/ + rga-closed-loop/ + .github/workflows/ trees) vs **⚠️ Console-only** (4 items: org creation · 6 API keys · ML model creation · MCP server creation).

### The ONE message (everything else supports this)
> **"100% of the search *experience* is reproducible from code. The handful of manual steps are one-time, and they're Coveo product-design choices — not gaps I left."**

### What to say (~50 sec) — narrate the PRINCIPLE, don't read the tree
> "The obvious question about everything I've shown is: *is it really all code?* Let me be precise about where that line is drawn.
>
> *[gesture at left column]* **Everything that governs the search experience is versioned in this repo** — fields, the source definition, scraping rules, the URL filter, mappings, the ML model *behavior* (prompts, seed queries, pipeline associations), and the MCP config — all JSON or YAML, each applied via Coveo's REST API. `scripts/bootstrap.sh` provisions a fresh org end-to-end.
>
> *[gesture at right column]* **What Coveo's product design requires the Console for is on the right — four one-time steps.** Org creation. API-key minting — Coveo shows each secret once, by design. The *act* of creating an ML model. And creating the MCP server itself.
>
> That last one's the most interesting: **Coveo doesn't publish an admin REST API for MCP config yet — I verified, eight candidate endpoints all 404.** So I version the YAML as source-of-truth and document the manual paste. The day Coveo ships that API, I drop in an apply script — same pattern as my RGA prompt.
>
> So the honest framing: **search-experience config is 100% code; the four Console steps are one-time and by Coveo's deliberate design.**"

### ✂️ TRIM VERSION (if folding into slide 7, ~10 sec)
> "All four ML models are wired to one pipeline — and that pipeline, the prompts, and the seed queries all live as code, with the obvious Console-gated exceptions for *creating* a model and minting API keys."

### ⚠️ FIELD-COUNT FLAG (again — this slide also says "5")
The left-column tree shows `fields.json · 5 indexed fields`. It's **14**. If you narrate a number, say 14 (or just don't read that line). Fix the deck before interview day for consistency with slides 3 + 6 + README.

### The precision that wins the point
The distinction to hold firm on: **behavior vs creation.**
- **Behavior** = prompts, seed queries, pipeline associations, builds, scraping, filters → **all API-scriptable, all in repo.**
- **Creation** = the org, the keys, the ML model objects, the MCP server object → **Console-only, one-time, Coveo's design.**

### 🧠 Deep-Coveo Q&A — code vs Console
- **"So it's NOT fully as-code?"** → *"Correct — and I'm precise about it. The search *experience* is 100% code; four one-time *setup* steps are Console-only because Coveo gates them that way. Those aren't things I'd script even if I could re-run them — they happen once per org."*
- **"Why can't you create an ML model via API?"** → *"Coveo documents model creation as Console-only; the generic ML Models API doesn't publish the engine IDs needed to create RGA/SE/etc. But every post-creation operation — prompt, seed queries, pipeline association, build trigger — IS API-documented, and I script all of it."*
- **"Why version the MCP YAML if you can't apply it?"** → *"Two reasons: it's a tracked record of Console state so a git diff shows every change, and it's apply-script-ready the day Coveo ships the admin API. Documentation-as-code now, source-of-truth later."* (this is the control-plane vs data-plane point)
- **"What does bootstrap.sh actually do?"** → *"Idempotent end-to-end provisioning: validate keys + org features, create fields, create + configure the source, apply scraping + mappings, widen the URL filter, rebuild, associate ML models, seed Query Suggest. One command, fresh org to working index."*
- **Fallback:** *"The whole left column is `config/` + `scripts/` — `bootstrap.sh` is the entry point. Happy to open it."*

### 🔧 Code refresher — the as-code surface
- `config/` — fields, source def, scraping, url_filter, ml seeds, mcp yaml
- `scripts/bootstrap.sh` — one-command provisioning · `scripts/validate/`, `scripts/setup/`, `scripts/source/`, `scripts/ml/`, `scripts/mcp/discover_api.sh`, `scripts/audit/`
- `.github/workflows/` — `rga-eval-daily.yml` (06:00) + `closed-loop-daily.yml` (06:30)

---

## 🎤 Slide 7 — Four ML models · one pipeline (highest deep-Q density)

> ⏱️ **Slide budget: ~75 sec.** Four cards. One sentence each + the "brief asked 2, I added 2" framing. The Q&A reservoir below is the biggest in the deck — a Coveo panel WILL probe how these relate.

### What's on the slide
Four model cards on one default pipeline: **RGA** · **Semantic Encoder (SE)** · **Query Suggest (QS)** · **Passage Retrieval (PR)**.

### The framing line (say first)
> "Four ML models, all on one default pipeline. The brief asks for **RGA and Query Suggest** — I added **Semantic Encoder and Passage Retrieval** because the index already supports them and they shape the experience meaningfully."

### What to say — one line per model (~75 sec)
> "**RGA — Relevance Generative Answering** — is the grounded AI answer above the results. Its Custom Prompt lives as YAML in the repo, v1.1.0, eight rules, and it's the thing the closed loop tunes overnight.
>
> **Semantic Encoder** is invisible but critical — embedding-based relevance. It's why *'what type is charizard'* lands the Charizard doc even though the page never literally says that phrase. Embedding similarity bridges the gap that keyword matching misses.
>
> **Query Suggest** powers the type-ahead. The interesting part was **cold-start**: a fresh org has no usage history, so QS has nothing to learn from. I solved it via Coveo's **Default Queries CSV endpoint** — 152 weighted seed queries — no need to synthesize fake analytics events.
>
> **Passage Retrieval** is the bonus tier — it returns ranked verbatim passages. That's exactly the primitive an enterprise would use to ground *their own* LLM. It powers two of my surfaces, and it's the bridge to the customer-pitch topic."

### The mental model to hold (so the Q&A doesn't rattle you)
**Each model acts at a different stage of the query lifecycle:**
- **QS** → fires on *keystrokes*, before a query is submitted (the `/querySuggest` endpoint). Separate request lifecycle.
- **SE** → fires on *query submit*; it shapes *ranking* (which docs come back, in what order).
- **RGA** → fires *after* retrieval; it *generates* a prose answer grounded on the top-N retrieved results.
- **PR** → a *separate* `/passages/retrieve` call; returns verbatim chunks (needs SE on the pipeline).

→ **One-liner:** *"SE decides what's retrieved; RGA composes language from it; PR exposes the raw chunks; QS helps you ask in the first place."*

### 🧠 Deep-Coveo Q&A — THE big one (drill these)
- **"What's the difference between Semantic Encoder and RGA?"** → *"Different layers. SE is **retrieval/ranking** — embeddings that decide which docs are relevant. RGA is **generation** — an LLM that composes an answer from the docs SE helped surface. SE makes retrieval smarter; RGA turns retrieval into a sentence."*
- **"RGA vs Passage Retrieval — isn't that redundant?"** → *"No. PR returns **verbatim ranked passages** — raw chunks with scores. RGA **synthesizes** a paragraph with citations. PR is for verification or grounding your own LLM; RGA is the finished answer. On my main page PR sits *below* RGA as a 'verify with source passages' panel — they're complementary."*
- **"Which LLM does RGA use? Can you pick it?"** → *"RGA runs a **Coveo-hosted, stateless LLM shared across customers** — per their model card. You don't pick the model; you control the **grounding** (retrieved content) and the **Custom Prompt**. That's actually the right abstraction — I tune behavior via the prompt, Coveo manages the model."*
- **"How did you solve QS cold-start?"** → *"Default Queries CSV — `PUT` to the `/configs/DEFAULT_QUERIES` endpoint, multipart with field name `configFile`, two columns query+importance. Uploading triggers a rebuild and the queries become candidates directly. **Two dead-ends first**, both documented in `docs/ml-models.md`: (1) `extraConfig.defaultQueries` — that's a *Drill* engine param, the API accepts it silently but QS ignores it; (2) synthesizing fake UA search+click events — they ingested but never cleared the engagement threshold to become candidates."*
- **"How are models associated to the pipeline?"** → *"`scripts/ml/associate_models.sh` — REST calls associating RGA, SE, QS to the default pipeline. Model **creation** is Console-only; **association** is API. PR I associated in the Console (its API was queryable once associated)."*
- **"Does RGA run on every query?"** → *"It fires when the generated-answer component requests it, and only on relevance-sorted results — I gate it off for name/date sorts because the top-N would be off-topic and RGA correctly refuses."*
- **"What are PR's prerequisites?"** → *"A Passage Retrieval (CPR) model **and** a Semantic Encoder on the same pipeline — PR rides on the embeddings SE produces."*
- **Fallback:** *"The model wiring is `scripts/ml/associate_models.sh` + `docs/ml-models.md`; the RGA prompt is `rga-closed-loop/prompts/pokemon-rga.yaml`. Happy to open any of them."*

### Topic 2 bridges baked into this slide (mention to set up the pitch)
- **PR** = the BYO-LLM / CRGA grounding primitive an enterprise customer would use.
- **RGA + the closed loop** = "production AI you can trust to operate itself" (slides 9–10).

### 🔧 Code refresher — ML models
- RGA prompt: `rga-closed-loop/prompts/pokemon-rga.yaml` (v1.1.0, 8 rules — **live, verified**)
- Associations: `scripts/ml/associate_models.sh` (RGA + SE + QS)
- QS seeds: `config/ml/default-queries.{json,csv}` (152 queries) + `scripts/ml/seed_query_suggest.sh`
- Model notes + the two QS dead-ends: `docs/ml-models.md`

---

## 🎤 Slide 8 — Three UI surfaces + cross-cutting skills

> ⏱️ **Slide budget: ~60 sec.** The implementation depth for the 3 surfaces is already in the **Slide 2 reservoir above** — don't re-spend it. This slide has a DIFFERENT job (below).

### ⚠️ How this differs from slide 2 + the demo (avoid the 3rd repeat)
By now the panel has: seen the surface *names* (slide 2), seen them *placed* in the architecture (slide 3), and seen them *running* (slide 4). So slide 8 must add NEW angles, not re-list:
1. **WHO each surface is for** — browser users (Atomic + Detail) vs **AI agents** (MCP). The audience split is the new lens.
2. **WHY each SDK** — the "right tool per job" FDE narrative (Atomic vs Headless).
3. **The MCP 2026 dwell** — 30 sec on the agent story.
4. **The cross-cutting Claude Code skills** — genuinely new content; bridges to slides 9–10.
> If you catch yourself re-describing *what* a surface does, stop — that was slide 2. Here it's *who it's for* and *why the SDK*.

### What's on the slide
Three surface cards tagged by audience (🌐 browser ×2, 🤖 AI agents ×1), plus a strip showing two cross-cutting skills (`/rga-eval`, `/rga-closed-loop`) that operate across all three.

### What to say (~60 sec)
> "Same Coveo brain, three consumption modes — and the useful lens here is **who each is for.**
>
> Two are **browser-first**: the Atomic list page and the Headless+React detail page. The SDK choice between them is the FDE call: **Atomic when you want a standard list-and-facets experience fast; Headless when you need composition** — multiple parallel queries, full styling control, on the customer's own React stack. Same org, different tool per job.
>
> The third is the one I want to dwell on — **MCP, for AI agents, not humans.** *[30 sec]* Coveo's hosted MCP server exposes this same index to any MCP client — Claude Code, ChatGPT Enterprise, Cursor — with zero per-client code. Four tools, including `answer`, which fires RGA. **Why it matters in 2026: every CIO is asking 'how does our content power our AI agents?' — and Coveo's answer is 'your existing index already does, via MCP.'** That's the customer-pitch angle.
>
> And these *[point at skills strip]* are two Claude Code skills I built that operate **across** all three surfaces — they're the FDE *operational* layer, not new surfaces. `/rga-eval` measures answer quality; `/rga-closed-loop` tunes the prompt. The next two slides go deep on both."

### The two framings unique to this slide
1. **Audience split:** *"Two surfaces for humans, one for agents — same brain."*
2. **Skills = ops layer:** *"The surfaces are the product; the skills are how an FDE operates it. They sit across all three because all three share the RGA model."*

### 🧠 Deep-Coveo / FDE Q&A — slide 8
- **"When would you pick Atomic vs Headless for a real customer?"** → *"Atomic for the 80% case — a standard search/list/facet page where speed-to-ship and accessibility matter; you get components + analytics out of the box. Headless when the page is bespoke — multiple composed queries, a design system to match, a framework already in play. I used both deliberately: Atomic for the list, Headless for the detail page's three parallel queries."*
- **"Why build Claude Code skills at all — isn't that just for you?"** → *"They're the operational interface to the system. An FDE doesn't hand a customer a dashboard and walk away — they leave runnable operations. `/rga-eval` and `/rga-closed-loop` make 'measure quality' and 'tune the prompt' one keystroke each, and the same logic runs in the daily cron. The skill and the cron share code."*
- **"What does MCP change for an enterprise vs just calling the Search API?"** → *"Two integration problems collapse into zero. Without MCP you write a connector per LLM client AND wire per content source. With Coveo MCP, the index is already agent-addressable over an open protocol — and it inherits Coveo's permissions, relevance, and audit trail. Your search investment becomes your agent investment."*
- **(Implementation specifics → see Slide 2 reservoir: Atomic CDN, two Headless engines, MCP tool list, etc.)**

### 🔧 Code refresher — surfaces + skills
- Atomic: `atomic-search/index.html` + `src/main.js` · Detail: `src/pokemon-detail/App.tsx` · MCP: `config/mcp/pokemon-mcp.yaml` + `.claude/mcp.json`
- Skills: `.claude/skills/{rga-eval,rga-closed-loop,pokemon-mcp}/SKILL.md`

---

## 🎤 Slides 9 + 10 — The closed loop (THE DIFFERENTIATOR · paired)

> ⏱️ **Combined budget: ~2.5 min** (≈70 sec slide 9 + ≈90 sec slide 10). This is where "I built a search UI" becomes "I built production AI." The demo already showed the dashboard — so here you explain the *machinery*, don't re-tour the chart.
> **Pairing:** Slide 9 = MEASURE. Slide 10 = ACT on the measurement. The bridge is literal: slide 9 produces the JSON; slide 10 reads it.

### ✅ VERIFIED METRIC DEFINITIONS (drill these — most-probed thing in the deck)
- **Hard recall** (deterministic, free): *"did the expected golden facts appear as substrings in the answer?"* Catches retrieval misses.
- **Accuracy** (LLM-judged): *"is the answer **holistically** correct?"* The headline number.
- **Precision** (LLM-judged): *"of the claims the answer makes, how many are supported — i.e., no hallucination?"* (When precision jumped 71→92, that was "hallucinations crushed.")
- **Citation precision**: are the cited sources actually relevant to the claims.

### 💡 THE DIAGNOSTIC INSIGHT (your single best talking point on slide 9 — memorize it)
> **"The signal isn't any one number — it's the GAP between hard-recall and accuracy. When recall is high but accuracy is low, RGA is retrieving the right facts but saying wrong things *around* them — so the bug is in **generation**, not retrieval. That tells me a prompt fix will help and a re-index won't. The eval doesn't just score; it localizes the bug."**

Concrete example to cite: *"RGA said Dragonite's ability 'Inner Focus increases accuracy' — it actually prevents flinching. Recall counted the ability name as present; accuracy caught the fabricated mechanic. That gap is the hallucination."*

---

## SLIDE 9 — rga-eval (measure every day)

### What's on the slide
A pipeline: CRON (06:00 UTC) → GOLDEN (100 Q, 3 layers) → RUN (POST to Coveo RGA, ~10 min) → JUDGE (Sonnet 4.6 + deterministic) → ARCHIVE (JSON in repo) → DASHBOARD (public Vercel). Driven by `/rga-eval`.

### What to say (~70 sec)
> "The brief didn't ask for this. I built it because the difference between shipping an MVP and deploying AI at an enterprise is one question: **how do you know your AI is working?** Most deployments ship, regress silently, and get retuned in a Slack thread after a customer complains. That's not production-grade.
>
> So every morning at 06:00 UTC, GitHub Actions runs a **100-question golden dataset** — hand-curated, three layers: 50 single-fact lookups, 35 multi-doc synthesis, 15 edge cases including **refusal tests**. It POSTs each to Coveo's RGA streaming endpoint and scores two ways: a **deterministic substring check** for hard-recall — fast and free — and **Sonnet 4.6 as an LLM judge** for accuracy and precision, which catches paraphrases and hallucinations a substring can't. About 55 cents a month.
>
> The output is **one JSON file per day, committed to the repo — the commit history *is* the time-series database.** No vendor lock-in; `git log eval-runs/` shows how quality evolved. And it auto-publishes to the public dashboard you saw — with markers for every prompt change the loop applied."

### 🧠 Deep Q&A — slide 9 (the judge questions)
- **"How do you know the LLM judge is right? Who judges the judge?"** → *"Three defenses. One — the **deterministic hard-recall** runs alongside the judge as a non-LLM backstop; if the judge drifts, the gap between them flags it. Two — the judge scores against **hand-written golden answers**, not free-form, so it's grading against a key, not vibing. Three — the judge prompt is **versioned and tool-use-forced** for structured output. The honest next step is periodic human spot-checks of judge verdicts — that's a gap I'd close at scale."*
- **"Isn't using an LLM to grade an LLM circular?"** → *"Different roles. RGA *generates*; the judge *compares against a golden answer*. And the deterministic recall metric is fully non-LLM — it's the anchor. They'd have to fail in the same direction to fool me, and recall can't hallucinate."*
- **"How did you build the golden set / can you change it?"** → *"Hand-curated 100 questions across three difficulty layers. I deliberately **don't modify it** — changing the questions invalidates the time-series comparison. It's the eval's ground truth."*
- **"Why commit JSON instead of a real DB?"** → *"For this signal, git IS the time-series DB — diff-reviewable, versioned, zero infra, no lock-in. At enterprise scale with high-frequency evals I'd move to a proper store, but the principle — every eval is an immutable, reviewable artifact — stays."*
- **Fallback:** *"Golden set is `rga-eval/golden/questions.json`, judge is `src/llm_judge.py`, recall is `src/metrics.py`."*

### 🔧 Code refresher — slide 9
- `rga-eval/golden/questions.json` (100 Q, 50/35/15) · `src/main.py` (runner) · `src/llm_judge.py` (Sonnet, accuracy+precision) · `src/metrics.py` (hard recall) · `eval-runs/*-full.json`
- Judge model: `claude-sonnet-4-5-20250929`, **personal** Anthropic key (security rule). `.github/workflows/rga-eval-daily.yml` @ 06:00 UTC.

---

## SLIDE 10 — rga-closed-loop (the system tunes itself)

### What's on the slide
A loop: READ (5-day eval window) → ANALYZE (Sonnet 4.6, tool-use forced → PromptProposal) → PROPOSE (new YAML vN+1, archive prior) → APPLY (PUT to Coveo ML Models API) → ↺. Plus **5 guardrails** and the `/rga-closed-loop` skill.

### What to say (~90 sec)
> "Measurement without action is just a dashboard nobody reads. The closed loop **acts** on yesterday's eval — and only when **five guardrails** pass.
>
> At 06:30 UTC the analyzer reads the **last five eval runs** — not just yesterday's. It computes per-category **persistence** — how many of the last five days a category has been failing — and **drift** — is it getting worse. So one bad day of judge noise doesn't trigger a change. Sonnet 4.6, with tool-use forced, returns a structured proposal: new prompt text, a rationale, a predicted lift, and a sample answer.
>
> Then the **five guardrails**: confidence below 0.80 — block. Predicted lift below five points — block. Last apply less than three days ago — block, because ML rebuilds take time and I don't want prompt churn. A sanity check — empty or runaway-length prompt — block. And **auto-rollback**: if tomorrow's eval drops more than five points, the loop reverts on its own. If all five pass, it PUTs the new prompt to Coveo's ML Models API and the bot commits the audit log.
>
> This already ran for real: **v1.0.0 → v1.1.0 on June 1.** The analyzer predicted 78% accuracy; the eval next day measured **79% — within one point.** Precision went from 71 to 92 — hallucinations crushed. And here's the part I like most: **it hasn't changed the prompt since.** Every morning it measures, and every morning it correctly decides *not* to act, because nothing has cleared the five-point bar. **That restraint is the guardrails working — not the loop being idle.**"

### ⚠️ UPDATED NUMBERS (verified today — use these, deck may be stale)
- v1.1.0 apply result: **62% → 79% accuracy** (predicted 78%, within 1 pt) · **precision 71% → 92%** · hard-recall dipped 87→86 (expected, stricter grounding).
- **Current live: still v1.1.0, accuracy ~76% today** (drifted from the 79% peak; range 76–80%). Frame as "lifted to ~79%, holding in the high-70s."
- Loop has applied **nothing since June 1** — guardrails holding. This is a feature, say it as one.

### 🧠 Deep Q&A — slide 10 (the autonomy questions)
- **"Why apply autonomously — no human review?"** → *"I deliberately chose guardrail-gated auto-apply over a PR-gate, because five guardrails plus auto-rollback are stronger than a human rubber-stamping a diff they don't fully evaluate. But the `/rga-closed-loop` skill gives me an **interactive review** path for development — so it's guardrails-only in the cron, human-in-the-loop on demand. Not 'no review' — 'review by policy.'"*
- **"What if the analyzer proposes a genuinely bad prompt?"** → *"Three nets: the lift + confidence guards block low-quality proposals before apply; the sanity guard blocks malformed ones; and auto-rollback catches anything that slips through by next morning. **Honest gap (slide 12): I haven't fault-injected a known-bad prompt to *prove* rollback fires under stress** — that's the next thing I'd do before trusting it fully unattended."*
- **"What exactly does the apply write to Coveo?"** → *"A PUT to the ML Models API setting `extraConfig.additionalAnswerInstructions` on the RGA model. It needs the dedicated ML-models-editor key — I found the admin key's scope didn't cover Models:Edit."*
- **"How is the analyzer not overfitting to noise?"** → *"The 5-day window + persistence/drift smoothing, plus the 3-day rate-limit. It needs a chronic, persistent failure — not a one-day dip — to propose a change."*
- **"Is the predicted lift trustworthy?"** → *"Empirically yes here — Sonnet's self-rated confidence predicted the result within one point. But n=1 apply; I wouldn't over-claim calibration on one data point."* (honest)
- **Fallback:** *"Guardrails are pure functions in `src/guardrails.py`, the orchestrator is `src/closed_loop_run.py`, prompts + history are in `prompts/`."*

### 🔧 Code refresher — slide 10
- `rga-closed-loop/src/analyzer.py` (5-day window, persistence+drift, Sonnet proposal) · `src/guardrails.py` (5 checks: confidence ≥0.80, lift ≥+5pts, rate-limit ≥3d, sanity, rollback) · `src/closed_loop_run.py` (orchestrator) · `src/apply.py` (PUT, dry-run default)
- `prompts/pokemon-rga.yaml` (v1.1.0 live) · `prompts/history/` (immutable archives) · `.github/workflows/closed-loop-daily.yml` @ 06:30 UTC

### The closing line for the pair (the climax of the whole deck)
> **"Most production AI is shipped and forgotten. This is production AI you can trust to operate itself overnight — and to know when *not* to. That's what production-grade AI actually means: not a model, a loop."**

---

## 🎤 Slide 11 — What I learned (maturity signal · 3 lessons)

> ⏱️ **Slide budget: ~60 sec.** Three lessons, ~20 sec each. Tone: genuine reflection, NOT humble-brag. Lesson 3 is the deep-question magnet (GraphRAG) — arm it.

### What to say (~60 sec)
> "Three honest lessons.
>
> **One — inspect the data before choosing the ingestion strategy.** The dual-source split didn't come from a design pattern; it came from an hour reading pokemondb's HTML and PokéAPI's JSON. If I'd picked 'Web Crawler' off a menu I'd have lost half the data. **Ingestion is a data question, not a tooling question.**
>
> **Two — closed loops compound; static prompts decay.** The eval-plus-tuning machinery felt like over-engineering before it ran. The day after it shipped, the cognitive load of *'is the prompt still good?'* went to zero — the system answers that for me. **Build the measurement loop first; you only know a prompt is final by measuring it over time.**
>
> **Three — vector plus LLM doesn't model *relationships* — and that's the 2026 frontier.** Some queries are relational: *'which Fire-types evolve from Water-types?'* Semantic Encoder embeds entities; RGA composes language; **neither models the edges *between* entities.** That's a knowledge-graph problem — and it's where I'd take this build next."

### 🧠 Deep Q&A — slide 11 (GraphRAG is the magnet)
- **"Why can't Coveo's stack do relational/multi-hop today?"** → *"I checked carefully. **Catalog** has entities but they're scoped to commerce taxonomies. **Knowledge Hub** is content-management insights, not graph traversal. The `$correlate` query extension surfaces related items by keyword overlap, not structured edges. So there's no Coveo GraphRAG layer yet — multi-hop reasoning is a future layer."*
- **"Give a query that fails today."** → *"'Which abilities counter Fire moves?' or 'which Fire-types evolve from Water-types?' — SE finds semantically similar docs, RGA writes a fluent paragraph, but nothing **traverses** type→counter or evolves-from relationships. You'd get a plausible answer that's only as good as what a single retrieved doc happens to state."*
- **"So is this a knock on Coveo?"** → *"No — it's the frontier for the whole industry. Vector + LLM is necessary but not sufficient for relational reasoning. Microsoft GraphRAG, Neo4j, WRITER are all chasing it. For an enterprise asking 'which regulations conflict with which policies?', a KG-augmented retrieval layer is the natural next step on top of what Coveo already does well."*
- **Tone watch:** lesson 3 must land as *forward-looking sophistication*, not *"Coveo is missing something."* Frame it as where YOU'd extend the build.

---

## 🎤 Slide 12 — Production hardening (honest audit · 4 gaps)

> ⏱️ **Slide budget: ~75 sec.** ⚠️ **Trim candidate** — if long, name the 4 gaps in one breath each and skip the "next steps." Tone: **confident, not apologetic.** "Here's exactly what's missing and how I'd close it" = senior. Hand-wringing = junior.

### The framing (say first AND last)
> **"The build runs and behaves — but it's not production-grade yet. Four honest gaps. None of this is research; all of it is well-known engineering work."**

### What to say (~75 sec) — 4 gaps, ~15 sec each
> "**Hosting and scale.** Vercel was right for a demo — serverless, zero ops. But I've **never load-tested** the integrated path; I don't know the concurrency ceiling, whether Coveo has per-key rate limits we'd hit, or if the log-proxy cold-starts at load. Next: k6 or Locust ramp + soak tests to find the real ceiling, then AWS managed functions behind a load balancer in a VPC, multi-region for tier-1.
>
> **Auth and data access — the most important gap.** Today the frontend talks to Coveo with a **search API key** — fine for public Pokémon, **unsafe** for an enterprise where users have differential access. The production pattern is **short-lived per-user search tokens** minted by a backend, plus SSO, plus **Coveo Security Identities** so results are filtered to what each user is allowed to see, plus a vault and rotation.
>
> **Monitoring beyond AI quality.** I have AI-quality and query observability — but no **APM**, no error tracking, no uptime checks, and critically **no SLOs**. Production defines 'what counts as up' before you ship.
>
> **And the autonomous loop itself.** The guardrails exist — but they've **never fired in anger.** I haven't fault-injected a known-bad prompt to prove auto-rollback works under stress, the eval scores *my* 100 questions not real-user clicks, and applies are silent commits with no alert. Next: fault-inject to prove rollback, roll out 10→50→100% via Coveo A/B testing, and alert on every apply.
>
> All four are known engineering work. I shipped what the time allowed — and I know exactly what 'truly production' looks like from here."

### 🧠 Deep Q&A — slide 12 (auth + scale are the magnets)
- **"What's a Coveo search token vs an API key?"** → *"An API key is a long-lived static secret with fixed scope — fine server-side, dangerous in a browser. A **search token** is a short-lived JWT a backend mints per-user; it can carry the user's identity so Coveo filters results per their permissions. Production = backend mints a token per session, never ships a raw key to the client."*
- **"What are Coveo Security Identities?"** → *"Coveo indexes the source's permissions (ACLs) at ingestion time; at query time the search token carries the user identity and Coveo filters results to what that user can access — early/late binding. So an agent or user only ever sees permitted documents. Same model whether the surface is the search UI or MCP."*
- **"How would you load-test this?"** → *"k6 or Locust — ramp test to find the breakpoint, soak test for memory/quota leaks over time. I'd specifically probe Coveo's per-key query rate limits, the Vercel proxy's cold-start under burst, and the Atomic UI at ~50 concurrent searches."*
- **"How do you safely roll out a prompt change at scale?"** → *"Coveo A/B testing on the pipeline — 10% of traffic on the new prompt, watch the live metrics, then 50, then 100. Plus fault-inject a bad prompt in staging to prove rollback fires. Right now I apply at 100% on guardrail-pass — fine at demo scale, not enterprise scale."*
- **"Which Coveo capabilities would you activate at scale?"** (the depth strip) → *"**ART** — relevance trained on real clicks, once I have UA volume. **DNE** — ML-tuned facet ordering. **IPE** — index-time Python for richer document transforms. **UA Data Service** — native analytics export. **Catalog** — entity hierarchies. I deferred all of these because they need either traffic or scale I don't have in a demo."*
- **Self-leak honesty (only if asked about secrets handling):** *"I also leaked the env via IDE chat several times during the build — every leaked key should've been rotated. That's a process gap too."*

### Coveo capability glossary (so the depth strip doesn't trip you)
- **ART** = Automatic Relevance Tuning — boosts results from click behavior (needs UA data).
- **DNE** = Dynamic Navigation Experience — ML-tuned facets.
- **IPE** = Indexing Pipeline Extensions — Python that runs at index time to transform docs.
- **UA Data Service** = native usage-analytics export.
- **Catalog** = commerce entity hierarchies.

### The transition out
> "So that's the honest audit. Let me wrap up." → straight into slide 13 (Thank you / Q&A).

---
