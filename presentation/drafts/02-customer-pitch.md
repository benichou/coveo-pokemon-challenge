# Presentation #1 · Topic 2 — Enterprise Customer Pitch

**Audience**: Coveo experts, but framed as if they're decision-makers at the target customer.

**Time budget**: ~25 min total — 10 min slides + 5 min live demo (the Pokémon build as a working analog) + 10 min Q&A.

**Total slides**: 9 (excluding cover). Pace = ~60s per slide.

**Working title** (placeholder): *"How Coveo would transform `<Customer>`'s search experience"*

---

## ⚠️ Decision needed before this draft is final: pick the customer

Doc 2's Topic 2 expects a **specific named enterprise customer**. The whole deck adapts to whoever you pick. Three candidates worth considering — each defensible, each with a clear pain narrative Coveo addresses.

### Candidate A — A B2B SaaS support / knowledge-base play

**Examples**: Notion · Linear · Figma · Pendo · GitHub · Datadog · ClickUp

**Why it works**:
- Public help-center / docs site you can audit before the panel
- Clear support-deflection economics (ticket cost × deflection rate = $)
- Coveo has named enterprise SaaS customers in its marketing (search engine, help-center vendor angle)
- Maps cleanly to RGA, Passage Retrieval, semantic ranking
- Easy to extend the live Pokémon demo: *"replace `pokemondb.net` with your help-center URLs and you'd get this exact UX"*

**Pain narrative**: support ticket volume + low self-serve resolution rates + AI-quality concerns about plugging an LLM into customer-facing surfaces.

**Best fit if**: you want the strongest demo-to-pitch bridge (the live UX is closest in shape to what they'd actually build).

### Candidate B — A regulated industry (financial services / asset management)

**Examples**: Vanguard · Morningstar · Bloomberg · Charles Schwab · BlackRock · Robinhood

**Why it works**:
- Permission-aware retrieval is a real differentiator (Coveo brand promise)
- Compliance + audit trails are non-optional, which the closed-loop work showcases directly
- High consequences for AI errors — your eval framework matters more here than anywhere else
- Coveo has named customers in adjacent verticals

**Pain narrative**: advisors / analysts spend hours hunting across siloed knowledge, regulatory boundaries make sharing tricky, AI rollouts blocked by hallucination risk.

**Best fit if**: you want to lean hard on the AI-quality + closed-loop story as the headline.

### Candidate C — An e-commerce / commerce platform

**Examples**: Shopify · BigCommerce · Wayfair · Best Buy · Etsy · Ulta

**Why it works**:
- Coveo has a dedicated Commerce product line — pitch lands in their fastest-growing segment
- Conversion-rate uplift math is the cleanest ROI story enterprise buyers know
- Product discovery + recommendations + personalization map directly to Coveo's commerce model
- Passage Retrieval less central; semantic + ART more central

**Pain narrative**: search abandonment rate, low click-through on results below the fold, cart conversion bleeding for searches with > 0 results but low relevance.

**Best fit if**: you want to flex the *commerce* side of Coveo — different conversation than the "knowledge base" path.

### My recommendation

If you don't have a strong tie to a specific company, pick **Candidate A** (B2B SaaS support). It's the closest UX match to your live Pokémon demo, the pitch transitions cleanest into the live demo segment ("imagine pokemondb is your help center"), and B2B SaaS is the segment with the most Coveo case studies you can cite in passing.

**The rest of this draft uses Candidate A as a working example** — specifically `Notion` because (a) panel members will know it, (b) its help center is publicly auditable, (c) it's a search-heavy product that genuinely needs RGA. **Swap any `Notion` reference with your final pick before locking the deck.**

---

## Slide 0 — Cover (≈10s)

**Visual**:
- Title: **How Coveo would transform Notion's search experience**
- Subtitle: A customer-pitch perspective — Franck Benichou, FDE candidate
- Bottom-right: live URL + GitHub repo
- Background: a screenshot of the live Pokémon search UI (volcano theme), positioned to look like a help-center search

**Speaker notes**:
- "I'm going to walk through how Coveo would transform Notion's search experience. The story has three beats: what's hurting today, what Coveo specifically fixes, and a credible 90-day path to ROI."

**Key message**: this is a deliberate, specific pitch — not a generic capabilities deck.

---

## Slide 1 — Notion at a glance (≈45s)

**Visual**:
- Logo + 3 quick stats: ~30M+ users (varies — verify before panel), ~10K+ enterprise customers, multi-billion ARR
- Content surfaces: help center (~1,500 articles), academy (videos + transcripts), community forum (~50K threads), customer-facing docs (API ref, integration guides)
- Annotation: "approximate; verify each number against most recent public source before the panel"

**Speaker notes**:
- "Notion has built one of the largest collaborative-workspace user bases in SaaS. Their content surface is large and growing."
- "The help center has roughly 1,500 articles, the academy has hundreds of videos, the community forum has tens of thousands of threads, and the API reference is its own beast. **Five-plus content silos**, none of them speaking to each other natively."

**TODO**: replace approximate numbers with verified figures before locking. Source: Notion's public site + analyst reports.

**Key message**: large customer, large content surface, multiple silos. Standard Coveo fit.

---

## Slide 2 — Current state pain (≈75s)

**Visual**: three pain bullets, each anchored to observable evidence.

1. **Search abandonment in the help center.** Public help-search URLs return zero results for common queries like "share specific blocks" or "automate database updates" — verify with 3-4 example searches before the panel.
2. **Multi-silo retrieval gap.** A user looking for "how to set up a workflow" gets help-center articles only — community threads, academy videos, and API docs don't surface in the same query.
3. **AI assistant in beta, but no measurable quality system.** Notion AI is shipped; quality measurement is opaque to customers and likely also to Notion's own product team beyond manual spot-checks. (Educated guess — defensible because *most* shipped AI features lack a measurement layer.)

**Speaker notes**:
- "These aren't hypothetical. I ran searches before the panel; you can do the same."
- *(Pain 1)* "Try 'share specific blocks' in their help search — empty result set. Their information exists; the retrieval doesn't surface it. Search abandonment for a help center query is industry-typical 30-50%."
- *(Pain 2)* "If I'm a user looking for 'workflow automation', I want articles + community examples + academy videos in one ranked list. Today I'd have to search 3 places."
- *(Pain 3)* "Notion AI generates answers; no public-facing metric on how often the answer is correct, hallucinated, or cites the wrong source."

**Key message**: pain is observable, not speculative.

**Q&A trap**: *"How do you know Notion doesn't already measure AI quality?"* — answer: I don't, definitively. But I built the equivalent for this challenge and the evaluation framework is what an enterprise should expect to see surfaced in their AI roadmap. If Notion already has it, the pitch shifts to "and here's how Coveo's framework compares / complements." Either way the slide stands.

---

## Slide 3 — The Coveo solution, mapped to each pain (≈90s)

**Visual**: 3-column table — Pain · Coveo capability · Live proof (Pokémon analog)

| Pain | Coveo capability | Live proof from my Pokémon build |
|---|---|---|
| Empty results / poor relevance | Semantic Encoder + ART model on the search pipeline | Type "what type is char" → ranked answer + relevant Pokémon, even with partial query |
| Multi-silo retrieval | Dual-source ingestion + unified pipeline | pokemondb sitemap + PokéAPI = 1,353 docs in one ranked list; same pattern applies to help-center + community + academy |
| AI without measurement | RGA + the 100-Q golden eval + closed-loop self-improvement | Live dashboard at `pokemon-rga-dashboard.vercel.app`; daily eval, automated prompt tuning, full audit trail |

**Speaker notes**:
- "Three pains. Three Coveo capabilities. And — crucially — a working proof for each, visible in the demo I'll show in two slides."
- "Notice the third row. Most vendors at this stage say 'we have an AI feature.' I'm showing you a measurement + improvement system around the AI feature. That's the difference between 'we shipped AI' and 'we operate AI in production.'"

**Key message**: every pain has a Coveo answer AND a live demo, not just slideware.

---

## Slide 4 — Quantified value (≈75s)

**Visual**: 3 ROI rows. Bands, not point estimates. Footnoted assumptions.

| Outcome | Range | Assumption |
|---|---|---|
| Self-serve resolution lift | +15–25% | Industry benchmark for unified-retrieval + RGA deployments; Coveo case studies cite similar ranges (Xero, F5, SAP Concur) |
| Support ticket deflection | $X–$Y annually | Notion's ticket volume × $25-50 per-ticket average × deflection rate |
| Search abandonment reduction | -30–50% | Coveo customer benchmarks; baseline-dependent |
| Time-to-resolution for advanced users | -20–35% | Single ranked surface vs 3 separate searches |

**Speaker notes**:
- "I'm deliberately giving ranges, not point estimates — I don't know Notion's internal numbers."
- "But here's the calibration: Coveo publishes named customer outcomes — Xero, F5, SAP Concur, Forcepoint, United Airlines. The ranges above are conservative against those references."
- "The math customers care about is `support cost per resolved ticket` × `deflection rate`. With ~50% of tickets being repeats of issues the help center already covers, even a 20% deflection lift compounds."

**TODO**: tighten numbers if Notion has any disclosed support / NPS data publicly available. Otherwise keep ranges and footnote.

**Key message**: I'm not selling you a magic number. I'm sizing the prize honestly.

---

## Slide 5 — Live proof (≈3-5 min demo)

**Visual**: switch from slides to the live deployed app.

**Demo script — "imagine this is your help center"**:
1. *(0:00)* Open https://pokemon-search-one-chi.vercel.app (let theme rotation pick a biome — call it out as UX polish). *"Replace pokemondb.net with help.notion.so in your mental model."*
2. *(0:30)* Type "what type is charizard" → RGA streams. *"Notion AI today returns an answer; your customers will see this PLUS a citation back to the source article. They can verify."*
3. *(1:00)* Click the Source facet to show dual-source items. *"Your help center + community + academy would surface here, ranked together."*
4. *(1:30)* Click a result → detail page loads. *"Single source of truth, three surfaces composed: hero card, related content, verifiable passages. Same Coveo brain."*
5. *(2:30)* Open the RGA quality dashboard in a separate tab — `pokemon-rga-dashboard.vercel.app`. *"Every day at 06:00 UTC, our system measures 100 questions. The chart markers show every prompt change with a clickable diff."*
6. *(3:30)* Optional: show the Coveo MCP Server demo via Claude Code — `/pokemon-mcp demo`. *"And the same content surfaces to your customers via ChatGPT Enterprise, Claude, or any other LLM your enterprise team is deploying. Zero additional integration."*

**Demo tips**:
- Keep the demo *about Notion's hypothetical experience*, not about Pokémon. Every "Charizard" should become "an article" in your narration.
- Pre-record a 90-second fallback in case Wi-Fi drops.

**Key message**: this is what your help center could look like in 60 days.

---

## Slide 6 — Roadmap to value: 30 / 60 / 90 days (≈60s)

**Visual**: timeline with 3 milestones.

**Day 0–30 — Discovery + index setup**:
- Connect Coveo to help-center + community + academy sources (Coveo connectors for each)
- Define the unified field schema
- Stand up Coveo Search API behind the existing search box (no UI change yet)
- Initial relevance baseline measurement (search abandonment, CTR, MRR)

**Day 31–60 — RGA + measurement layer**:
- Deploy RGA on the help-center + community pipeline (BYOLM if Notion has a preferred LLM provider — Coveo supports Claude, GPT-4o, Gemini, internal models)
- Stand up the eval framework (Notion-specific golden dataset, ~150-200 questions covering top user journeys)
- Public-facing quality dashboard for the Notion search team

**Day 61–90 — Personalization + production hardening**:
- Layer ART for usage-driven relevance tuning
- Multi-region edge caching for read-heavy traffic
- Closed-loop prompt tuning system (autonomous overnight improvements)
- Permission-aware retrieval for enterprise-tier customer data

**Speaker notes**:
- "Three months. Realistic, sequenced so each milestone is independently deployable."
- "If month 1 doesn't show a measurable improvement on the baseline, we pause and diagnose before adding more. Same discipline I used in the Pokémon build — measure first."

**Key message**: not a vague roadmap. Each month has one shippable thing, in priority order.

---

## Slide 7 — Why Coveo, why now (≈45s)

**Visual**: three positioning bullets.

1. **Coveo solves the "R" in RAG** — the retrieval layer is the hardest part of any enterprise AI rollout. RGA + Passage Retrieval are productized answers, not DIY frameworks. (Lifted from Coveo's own Passage Retrieval positioning.)
2. **BYO-LLM friendly** — Notion stays in control of which LLM grounds the answers. ChatGPT, Claude, Gemini, internal — Coveo is the secure permission-aware retrieval surface in front of any of them.
3. **MCP-ready** — your AI investment compounds: Coveo's index is addressable from any MCP-compatible client (ChatGPT Enterprise, Claude, Cursor, internal agents) without per-LLM integrations. **Today's content investment becomes tomorrow's agent infrastructure.**

**Speaker notes**:
- "Three reasons this is the right partnership."
- *(1)* "LLMs are commoditizing fast. The differentiator is what you ground them on. Coveo productized that retrieval layer; you don't have to build it."
- *(2)* "You're not locked into one LLM provider. Pick Claude this quarter, Gemini next. Coveo's neutral."
- *(3)* "And the same Coveo investment that powers your help center *today* will power your internal agents *next year*, through MCP. Already shipped, already GA."

**Key message**: this isn't just a search upgrade — it's the foundation for everything AI-grounded that Notion ships in the next 24 months.

---

## Slide 8 — Why I'd be your FDE (≈30s)

**Visual**: 3 small headshots (or icons) → "Build, measure, operate" caption.

**Speaker notes**:
- "I built every layer of this Pokémon project myself — ingestion, search, AI grounding, measurement, observability, closed-loop. Same scope I'd own as your FDE."
- "I lean toward measurement before optimization. The first thing I'd ship for Notion isn't the new RGA, it's the eval framework that tells us whether the new RGA is better than the old."
- "And I write everything as code — config, prompts, MCP server instructions, even diagrams. Reproducible across orgs, diffable in PR review, audit-friendly."

**Key message**: I do production-grade work, not demoware.

---

## Slide 9 — Wrap + open conversation (≈30s)

**Visual**:
- *"30/60/90 days. Measurable from day 30. Compounding from day 90."*
- Repo + URLs one more time
- "What would you want to see first?"

**Speaker notes**:
- "Happy to dig into any layer in depth — the relevance pipeline, the eval framework, the closed loop, the MCP server, or the commercial framing."

---

## Q&A — anticipated questions + prepared answers

| Q | Prepared answer (compressed) |
|---|---|
| "How do you handle our content's update frequency?" | Sitemap source (or per-system connector) re-indexes on a schedule + delta push for high-change content. Closed-loop monitors quality after each re-index. |
| "What about permissions / multi-tenancy?" | Coveo's source-level security model. Per-user permissions inherited from the source system at index time. Demonstrated in the Pokémon build at the source-hub layer. |
| "Cost of running the eval system?" | ~$0.60/day in Sonnet tokens for our 100-Q version. For Notion's 200-Q version, ~$1.20/day. Production-tier ROI for a measurement layer. |
| "What's the time-to-deploy for the first quality gain?" | Realistically 30-45 days to measurable lift on a well-scoped golden dataset. Caveat: we'd need 2-3 weeks of baseline data before we know what "lift" means. |
| "Why not just use Notion AI's existing system?" | If it meets the quality bar Notion's team has defined, no need. But the bar should be measured publicly — and that's what Coveo brings whether or not the LLM changes. |
| "We already have Algolia / Elastic / etc." | Possible to layer Coveo on top as the grounding + AI layer while keeping the existing retrieval. We've seen customers run hybrid stacks during migration. |
| "How does Coveo handle our scale?" | Coveo's largest customers (Xero, F5, SAP Concur, United Airlines) are at or above Notion's scale. Pricing scales with consumption; not a per-seat or per-doc tax. |
| "What if Coveo can't index a content surface we have?" | Push API is the universal fallback — anything we can read programmatically, we can push. Source B in the Pokémon build is exactly this pattern (Python pipeline pushing PokéAPI-enriched docs). |
| "What's the lock-in risk?" | Lower than building DIY because Coveo exposes everything through standard REST + MCP. The retrieval layer is portable; the value-add (ART, RGA, PR) is what you'd lose. |
| "Who owns the prompt engineering?" | Notion's product + content team should own it; Coveo's FDE coaches on patterns. The closed-loop system here is exactly that division of labor — analyzer proposes, humans approve, system applies via code. |

---

## Trim levers if running long

Total budget is ~10 minutes of slides + 5 min demo. If a dry-run hits 13 min talking, cut in this order:

1. **Slide 4 (quantified value)** → drop to 1-bullet headline + footnote. Save 40s.
2. **Slide 8 (why me)** → cut entirely; let the work speak for itself. Save 30s.
3. **Slide 7 (why Coveo)** → cut bullet 3 (MCP). Save 30s.

Total trimmable: ~100s. Demo time + Slide 0/2/3/5/6 are immovable — that's the core pitch.

## Customizing for different customer choices

If you swap Notion for one of the other candidates (B2B SaaS variant other than Notion, financial services, or commerce), update these slides specifically:

- **Slide 1**: replace stats, content surfaces
- **Slide 2**: re-research current-state pain (the *specific* observable evidence)
- **Slide 3**: keep table structure, swap the "Live proof" column language to fit the customer's domain
- **Slide 4**: update value-band names (e.g., "conversion uplift" for commerce, "advisor productivity" for finance)
- **Slide 5**: re-narrate the live demo with customer's domain language
- **Slide 6**: keep timeline structure; rename milestones for domain
- **Slide 7**: leaves intact (Coveo positioning is customer-agnostic)

The other 4 slides (0, 8, 9, plus Q&A) are template-agnostic.

## Companion docs to lean on (don't re-explain — link)

- [`docs/rga-eval-methodology.md`](../../docs/rga-eval-methodology.md) — the eval framework
- [`docs/passage-retrieval.md`](../../docs/passage-retrieval.md) — Coveo's "R in RAG" positioning, named customers, use cases
- [`docs/mcp-integration.md`](../../docs/mcp-integration.md) — MCP positioning for the BYOLM slide
- [`docs/caching-strategy.md`](../../docs/caching-strategy.md) — production hardening for slide 6
- [`docs/observability.md`](../../docs/observability.md) — measurement layer (slide 3 row 3)
