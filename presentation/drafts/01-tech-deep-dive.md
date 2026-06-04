# Presentation #1 · Topic 1 — Pokémon Challenge: Technical Deep Dive

**Audience**: Coveo experts. They know the platform. **Don't over-explain Coveo — explain your choices.**

**Time budget**: ~25 min total — 10 min slides + 3-5 min live demo + 10 min Q&A.

**Total slides**: 12 (excluding cover). Pace = ~50s per slide.

**Working title**: *"Pokédex Search — a production-grade Coveo build, plus three things Doc 2 didn't ask for"*

---

## Slide 0 — Cover (≈10s)

**Visual**:
- Title: **Pokédex Search**
- Subtitle: A Coveo FDE technical challenge by Franck Benichou
- Bottom-right corner: live URL `pokemon-search-one-chi.vercel.app` + GitHub `github.com/benichou/coveo-pokemon-challenge`
- Background: a screenshot of the live Atomic UI in the volcano theme (most visually striking of the 5)

**Speaker notes**:
- "Hi — I'm Franck. Over the next 10 minutes I'll walk through the Pokémon Challenge build, then we'll do a live demo and Q&A."

**Key message**: the URLs are live and you can follow along on your phone.

---

## Slide 1 — What I built, in one breath (≈30s)

**Visual**:
- One sentence: *"A Pokémon-themed search experience on Coveo Cloud — three UI surfaces, four ML models, two ingestion sources, one Coveo org, all of it code-as-source-of-truth."*
- Three small thumbnails of the three UI surfaces (Atomic list, Headless+React detail, Claude Code with MCP)

**Speaker notes**:
- "Doc 2's brief is essentially: index pokemondb.net into a Coveo org and ship a custom search experience on top. That's the deliverable."
- "But the challenge also asks for Advanced and Bonus tier work. I went full ambition — every advanced item, the bonus, plus three things Doc 2 didn't ask for. I'll get to those."
- "Single screenshot recap before we get into the *how*."

**Key message**: scope = full ambition, not the minimum that passes.

---

## Slide 2 — Architecture (≈90s, the anchor slide)

**Visual**: the mermaid flowchart from `README.md` (the one with 6 logical zones — data sources, ingestion, Coveo brain, three UI surfaces, AI quality loop, query observability — plus the Claude Code skills sub-zone). Color-coded by zone.

**Speaker notes**:
- "Four flows worth tracing on this diagram."
- *(point at top-down arrow)* "**Ingestion**: dual-source. pokemondb.net's sitemap into Source A. PokéAPI per-form variants pushed into Source B."
- *(point at three UI nodes)* "**Three surfaces, one brain**: Atomic list page at the root, Headless+React detail page at `/pokemon.html`, and Coveo's hosted MCP server — addressable from any MCP client like Claude Code or ChatGPT Enterprise."
- *(point at right-side closed-loop)* "**Closed loop**: daily eval measures RGA quality, daily analyzer proposes prompt refinements, guardrails decide whether to apply. The dotted arrow back to RGA is the loop closing."
- *(point at left-side observability)* "**Parallel observability**: every user search fires a fire-and-forget log to Grafana Cloud Loki via a Vercel proxy — Loki write token stays server-side."

**Key message**: one Coveo org, six logical zones, two narrative loops (quality + observability).

**Q&A trap**: *"Why didn't you do X?"* — most "didn't you" questions are about scope. Answer: "I did this within the scope of Y; here's how I'd add X next" — i.e. always have a roadmap answer ready.

---

## Slide 3 — Why dual-source (≈45s)

**Visual**: trade-off table.

| | Source A (Sitemap) | Source B (Python Push) |
|---|---|---|
| Effort | Zero code | Python pipeline |
| Throttling | Coveo handles | I handle (PokéAPI 100 req/min) |
| Freshness | Refresh schedule | On-demand re-push |
| Form variants | One doc per slug | One doc per form (Mega, Hisuian, Galarian) |
| Use for | Canonical pages | Enrichment + form coverage |

**Speaker notes**:
- "Coveo's leading practices say: prefer Sitemap source when one exists. pokemondb publishes a sitemap with 12,915 URLs — 1,028 are individual Pokémon."
- "But Sitemap source can't preserve form-level identity — pokemondb has one Charizard page; the index needs one doc each for base, Mega-X, Mega-Y."
- "Source B (Python Push) reads PokéAPI's per-form endpoints and pushes 325 form-variant documents to compensate. Same field schema, so the index is unified."
- "Total: 1,353 docs."

**Key message**: not "one source is right" — different sources serve different facets of the same data.

---

## Slide 4 — Coveo config as code (≈60s)

**Visual**: a screenshot of the GitHub repo's `config/` tree expanded:
```
config/
├── fields.json                  ← 5 indexed fields
├── source/
│   ├── definition.json
│   ├── scraping.json
│   └── url_filter.json          ← single source of truth
├── ml/
│   └── default-queries.json     ← Phase 6B QS seed
└── mcp/
    └── pokemon-mcp.yaml         ← Phase 8.5 MCP server
```

**Speaker notes**:
- "Every Coveo resource we touched is versioned in this repo as JSON or YAML, with a bash or Python script that applies it via the REST API."
- "URL filter, scraping rules, mappings, fields, ML model prompt, MCP server config. ~95% reproducible from a fresh org."
- "The only manual step is API-key minting — Coveo shows secrets once at creation, by design."
- "Where Coveo's public API doesn't cover a surface — like MCP Server admin today — we still version the YAML and document the manual paste workflow. Code-as-source-of-truth even where the API gap forces a manual apply step."

**Key message**: nothing in this build lives only in the Console.

---

## Slide 5 — Four ML models on the default pipeline (≈60s)

**Visual**: simple grid of 4 boxes — pokemon-rga / pokemon-se / pokemon-qs / pokemon-pr — each with one-line role.

**Speaker notes**:
- "All four wired to the same `default` pipeline."
- "**RGA** generates the AI answer above the result list. Grounds on retrieved chunks. I rewrote its Custom Prompt from scratch — Coveo's default has `[Enterprise Name]` placeholders that bleed into answers."
- "**Semantic Encoder** improves ranking via embeddings — no UI change, but RGA + PR depend on it."
- "**Query Suggest** powers type-ahead. Cold-start solved via Default Queries CSV, not UA event synthesis."
- "**Passage Retrieval** returns verbatim chunks. Surfaced below RGA on the main page; also used on the detail page's Featured Insights card."
- "Five API keys, each least-privilege scoped. Different roles need different keys — Coveo enforces immutable post-creation privileges, so it's not optional."

**Key message**: not just "RGA is on" — four models, deliberately wired, deliberately scoped.

**Q&A trap**: *"Why did you rewrite the RGA Custom Prompt?"* — because the diagnostic loop (Phase 6D) measured the default at 62% accuracy with `[Enterprise Name]` showing up in answers as a literal string. Walk them through the eval methodology if asked. See `docs/rga-eval-methodology.md`.

---

## Slide 6 — Three UI surfaces, one retrieval brain (≈75s)

**Visual**: three columns side-by-side, screenshots of:
1. Atomic main page (with the GBC topbar visible)
2. Headless+React detail page (Charizard hero card)
3. Claude Code terminal showing the MCP tool call

**Speaker notes**:
- "Doc 2 asks for Atomic main + a Headless+React module. I built both, plus a third surface — Coveo's Hosted MCP Server."
- *(Surface 1)* "**Atomic main page** at `/` — list view, facets, sort, RGA panel, Passage Retrieval panel below RGA, Query Suggest type-ahead. The retro Game Boy Color landscape is CSS-only; refresh and one of five biomes rolls."
- *(Surface 2)* "**Pokémon Detail Page** at `/pokemon.html?name=X` — Headless+React in a multi-entry Vite build. Three composed Coveo queries on one page: Search API for the hero, Passage Retrieval for the Featured Insights card, a second Headless engine for the same-generation Related grid. Three parallel round-trips."
- *(Surface 3)* "**Coveo Hosted MCP Server** — Phase 8.5, beyond-bonus. Four MCP tools — search, fetch, get_passages, answer — exposed to any MCP-compatible LLM client. Claude Code, ChatGPT Enterprise, Cursor. Zero additional code per client."
- "Same Coveo org, same pipeline, same models, same index. Different UI optimization per surface. Picking the right Coveo SDK per surface is the FDE narrative compressed."

**Key message**: list-view UX, detail-view UX, and agent UX are three different optimizations of the same retrieval layer.

**Demo trigger**: if the panel wants to see the surfaces live, mention now: *"I'll show all three in the demo segment in two slides."*

---

## Slide 7 — Three things Doc 2 didn't ask for (≈75s)

**Visual**: three callouts:
1. 🔬 **Continuous AI-quality measurement** (Phase 6D)
2. 🔁 **Closed-loop self-improvement** (Phase 6F + 6F.7)
3. 📊 **Query observability** (Phase 6E)

Plus a fourth, smaller: 🧠 **Code-as-source-of-truth even for AI configuration**.

**Speaker notes**:
- "These are the panel-defining adds. Doc 2 doesn't ask for them. I built them because they're what production AI actually requires."
- "**Continuous AI-quality measurement**: 100-question golden dataset, Sonnet 4.6 as judge with tool-use forcing, daily GitHub Actions cron writes time-series JSON to git, public Vercel dashboard renders it. Catches RGA regressions before customers notice."
- "**Closed-loop self-improvement**: same daily eval feeds an analyzer that reads the *last 5 runs* — distinguishes chronic failures from one-day judge noise. Proposes a prompt refinement, runs it through guardrails — confidence ≥ 0.80, lift ≥ +5 points, rate-limit ≥ 3 days, sanity checks, auto-rollback. If all pass, applies the new prompt via Coveo's ML Models API."
- "**Query observability**: every user search fires a fire-and-forget log to Grafana Cloud Loki. Same-origin Vercel proxy keeps the Loki write token server-side. Public dashboard, auto-deployed from `main` via CI."

**Key message**: most AI deployments ship a prompt and re-tune manually in Slack when something breaks. This system measures every day, proposes refinements when warranted, applies them through code with audit trail + auto-rollback.

**Q&A trap**: *"Could the closed loop break production?"* — answer: five guardrails + 36-hour auto-rollback. The conservative defaults are deliberate. Worth the longer answer if asked.

---

## Slide 8 — The closed loop, in detail (≈75s) — sequence diagram

**Visual**: the mermaid sequence diagram from `README.md` — "Sequence B" — showing eval cron → analyzer → guardrails → apply with alt blocks for rollback / blocked.

**Speaker notes**:
- "06:00 UTC: rga-eval-daily fires. Iterates 100 golden questions, calls RGA, judges each with Sonnet 4.6, writes the JSON to `eval-runs/`."
- "06:30 UTC: closed-loop-daily fires. Reads last 5 runs. **Rollback check first** — if accuracy dropped > 5pts within 36h of the last apply, auto-reverts to the previous prompt YAML."
- "Otherwise: analyzer with multi-day persistence + drift signals → Sonnet proposes a `PromptProposal` with rationale and predicted lift."
- "Five guardrails decide whether to apply."
- "If applied: archives the previous YAML to `prompts/history/`, writes the new YAML, PUTs to Coveo's ML Models API, re-fetches to verify, bot-commits everything."
- "Every outcome — apply, blocked, rollback — produces a bot-committed audit log."
- "The next day's 06:00 UTC eval measures the new prompt. **The loop closes by design.**"

**Key message**: the dotted arrow on the architecture diagram from earlier is a real, autonomous, daily Python process — not a one-off script.

---

## Slide 9 — Live demo (≈3-5 min)

**Demo script — golden path**:
1. *(0:00)* Open https://pokemon-search-one-chi.vercel.app (refresh to land on, say, the volcano theme — call it out: "this is one of five biomes, rotates on each load")
2. *(0:30)* Type "charizard" — point at the RGA answer streaming, the citation, the Passage Retrieval panel below it. *"Same retrieval primitive that an enterprise customer would use to ground their own LLM."*
3. *(1:00)* Click a Type facet — point at the result count refreshing. Click the Source facet to show dual-source items mixing.
4. *(1:30)* Click the Charizard result → lands on `/pokemon.html?name=Charizard`. Point at the hero card, Featured Insights (PR), Related Grid (second Headless engine). *"Three Coveo queries on this page, fired in parallel."*
5. *(2:30)* Back to main → open a separate terminal/tab with Claude Code, type `/pokemon-mcp demo` (or pre-arranged equivalent). Let it call the four MCP tools live. *"Same Coveo org, now answerable from Claude Code through MCP."*
6. *(4:00)* Open the RGA dashboard `pokemon-rga-dashboard.vercel.app`. Point at the time series. *"Every day at 06:00 UTC the eval runs. Chart markers show prompt-change applies; click one to scroll to the version diff."*
7. *(4:30)* Optional if time: Grafana dashboard quick peek.

**Demo tips**:
- Pre-load all tabs before the panel; don't fumble.
- Have a fallback **pre-recorded video** in case Wi-Fi dies. 60-second screen capture covers slides 1-3 of the demo path.
- If MCP demo flakes, fall back to a screenshot of a successful run from yesterday + narrate.

**Key message**: this is a working app, not a slide deck about an app.

---

## Slide 10 — What I learned (≈45s)

**Visual**: three numbered bullets. Honest, candid.

**Speaker notes**:
1. *"Filter is not truth."* — A URL inclusion regex that looked correct was admitting `/pokedex/shiny` as if it were a Pokémon. The integration test suite caught it post-index. Built the audit script + a structural HTML check (PokéAPI cross-reference) as a guard. **Independent verification matters even when the input source is "official".**
2. *"Default ML configurations carry latent bugs."* — Coveo's default RGA Custom Prompt has `[Enterprise Name]` placeholders that surface in answers verbatim until you rewrite the prompt. The eval system caught it at baseline (62% accuracy). **Measure before you trust.**
3. *"Code-as-source-of-truth scales further than you'd think."* — When I started, I thought the Coveo Console clicks would be the last 5% of manual work. The number turned out closer to <5% (just API key minting). Every other surface — fields, source config, scraping rules, ML model prompts, MCP server instructions, Query Suggest seed queries — fits in version-controlled JSON or YAML with an apply script.

**Key message**: the surprises were where I assumed less rigor was OK.

---

## Slide 11 — What I'd do next (≈45s)

**Visual**: 2-3 bullets, framed as customer-roadmap.

**Speaker notes**:
- "If this were a real customer deployment, three things in priority order."
- **1. Deploy ART** (Automatic Relevance Tuning) on the search + passage flow. We'd need real usage data over weeks. Would improve ranking against actual user clicks, not synthetic relevance assumptions.
- **2. Add personalization tokens** to the query pipeline. Right now the demo treats every visitor as anonymous; in a real deployment you'd attach Pokémon-type-favorite preferences or similar context to the user profile and let Coveo's personalization model bias retrieval.
- **3. Multi-region edge caching**. We have Coveo's built-in result-list cache + RGA dedup at the billing layer. For real scale we'd add Vercel CDN at edges + Redis keyed by `(query, prompt_version)` so the closed-loop apply naturally invalidates. Documented as Tier 1-3 in `docs/caching-strategy.md`.
- "All three would be unblocked by real user traffic, which we don't have in a demo."

**Key message**: there's a real path beyond the demo, and I know what it looks like.

---

## Slide 12 — One-line wrap + Q&A (≈30s)

**Visual**:
- Bottom line: *"Three UI surfaces, one Coveo brain, two autonomous loops, zero secrets in the bundle."*
- Repo + live URL one more time
- "Questions?"

**Speaker notes**:
- "Happy to take questions."

---

## Q&A — anticipated questions + prepared answers

| Q | Prepared answer (compressed) |
|---|---|
| "Why Sitemap source over Web Crawler?" | Coveo's leading practices recommend it when a sitemap exists. Faster, more predictable. Web crawler would have done unnecessary link discovery. |
| "How did you handle Mega/regional forms?" | Source B (Python Push) reads PokéAPI's per-form endpoints. Source A's sitemap source only has one doc per canonical name. |
| "Why a personal Anthropic key?" | The eval system uses Sonnet 4.6 as judge. Carta's enterprise key on a personal GitHub project would be a compliance + audit-trail concern. Per `~/.claude/rules/security.md`. |
| "What if the closed loop proposes a bad prompt?" | Five guardrails (confidence, lift, no-op, sanity, rate-limit) + auto-rollback on next-day drop > 5pts within 36h. Deliberately conservative. |
| "How does ART interact with MCP traffic?" | MCP traffic lands on a separate auto-created search hub (`MCP_pokemon-mcp`), so ART learns from human-driven UA — not LLM-driven. By design. |
| "What's the bundle size?" | Pokemon detail page bundle = 405KB gzipped, down from 731KB after Vite started sharing the Headless chunk with the main page (both import `buildPager`/`buildSearchEngine`). |
| "Why didn't you use Coveo's MCP labs version?" | The labs version (github.com/coveo-labs/coveo-mcp-server) is explicitly marked "not production-ready" and only exposes 3 tools (no `fetch`). The hosted MCP Server is GA and adds the fourth tool. |
| "How do you handle credentials in `.env`?" | Six Coveo keys + one Anthropic, all gitignored. CI uses GitHub Secrets. The Loki write token never reaches the browser — same-origin Vercel proxy. |
| "What metrics would you watch post-launch?" | Search abandonment rate, click-through per result position, RGA accept/reject feedback, facet usage distribution, Coveo ML model confidence trend over time, and the eval dashboard's accuracy/precision/hard-recall daily numbers. |
| "Biggest risk in your config?" | Web scraping config brittleness — pokemondb changes their DOM, our selectors break. Mitigation: Source B (Push) gives us a parallel path that doesn't depend on HTML scraping. |
| "Why not use Coveo's MCP server admin REST API to version pokemon-mcp.yaml end-to-end?" | I ran a read-only spike (`scripts/mcp/discover_api.sh`) — 8 candidate endpoint shapes all returned 404 INVALID_URI. No public admin API exists yet. The YAML stays as source of truth; the Console mirror is currently a manual paste. The day Coveo publishes the API, swap in an apply script. |

---

## Trim levers if running long

Total budget is ~10 minutes of slides. If a dry-run hits 13 min, cut in this order:

1. **Slide 8 (sequence diagram detail)** → fold into Slide 7 as a 15-second mention. Save 60s.
2. **Slide 4 (config as code)** → mention briefly during Slide 5. Save 45s.
3. **Slide 11 (what I'd do next)** → cut to ONE bullet instead of three. Save 30s.

Total trimmable: ~2 min. Demo time + Slide 0/1/2/3/6/7/9 are immovable — that's the core story.

## Visual style hints

- Use the project's GBC color palette where possible — accent `#ee1515` for headers, `#e8c878` (sandy) or `#88c8e8` (cyan) for callouts.
- Press Start 2P or similar pixel font for slide titles (matches the live UI).
- Real screenshots from the live deploy, not mockups.
- Architecture + sequence diagrams: copy directly from README, they're already panel-shareable.

## Companion docs to lean on (don't re-explain — link)

- [`docs/rga-eval-methodology.md`](../../docs/rga-eval-methodology.md) — the diagnostic loop
- [`docs/observability.md`](../../docs/observability.md) — query observability architecture
- [`docs/caching-strategy.md`](../../docs/caching-strategy.md) — caching tiers
- [`docs/passage-retrieval.md`](../../docs/passage-retrieval.md) — PR positioning
- [`docs/detail-page.md`](../../docs/detail-page.md) — Headless+React detail page
- [`docs/mcp-integration.md`](../../docs/mcp-integration.md) — MCP server integration

If a panelist asks for depth on any of these, point at the doc on GitHub (or hand them the URL) rather than burning 2 minutes re-explaining in the room.
