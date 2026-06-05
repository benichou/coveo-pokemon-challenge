# Presentation #1 · Topic 2 — Enterprise Customer Pitch

**Customer**: **Employment and Social Development Canada (ESDC) · Employment Insurance directorate** — specifically the EI Claim Processing Centres + EI Call Centres operated by Service Canada.

**Audience role**: **CIO / Director General of Digital, ESDC** — strategic, multi-year platform thinking. Procurement, enterprise architecture, and risk framing weigh heavily.

**Framing**: **Detailed reference** — the speaker has prior consulting experience deploying first-generation RAG systems for this exact customer (via EY Canada). The pitch leverages that experience as credibility ("I've been inside these workflows") without exposing confidential engagement details.

**Time budget**: **~5-7 min within the shared Presentation #1 slot** — this is the *short pitch* segment that piggy-backs on Topic 1's live demo (no separate demo needed). Topic 1 (technical deep dive) takes ~12-14 min before this; ~5-7 min of Q&A at the end covers both topics together. Total Presentation #1 slot ≈ 25 min.

> **⚠️ Scope-correction note**: Doc 2 specifies *"Prepare a short presentation"* for this topic. An earlier draft of this file treated it as its own 25-min presentation — that was wrong. This is now a tight 5-slide pitch, paced ~75s per slide, designed to land entirely within the budget above without a dedicated demo segment.

**Total slides**: 5 (excluding cover). Pace = ~75s per slide.

**Working title**: *"From first-generation RAG to production-grade AI — what Coveo brings to ESDC EI"*

---

## ⚠️ Source-material discipline — what's defensible vs not

The "detailed reference" framing allows specific references to the prior engagement, but **every claim about pain points should be backed by one of**:

1. **Public ESDC / Service Canada reporting** (Auditor General reports, Departmental Plans, Public Accounts of Canada, EI Monitoring and Assessment Report)
2. **Published Treasury Board policy** (Directive on Automated Decision-Making, AI Strategy for the Federal Public Service)
3. **General industry patterns** for first-gen RAG deployments at scale (hallucination, bilingual gaps, content silos, quality measurement maturity)

**Avoid**: naming the specific vendor / stack EY selected, internal architecture details, named individuals at ESDC, specific dollar figures or volumes you only know from the engagement. **Use public ESDC reporting numbers for any quantitative claim.**

If a panelist asks for specifics you can't share, say so directly: *"That detail is from a confidential engagement — happy to speak to the public pattern around it instead."*

---

## Slide 0 — Cover (≈10s — transition from Topic 1's Q&A or closing slide)

**Visual**:
- Title: **From first-gen RAG to production-grade AI — ESDC Employment Insurance**
- Subtitle (small): A short customer-pitch follow-up to the Pokémon Challenge deep dive
- Speaker line: Franck Benichou · FDE candidate, Coveo
- Background: same brand language as Topic 1's deck for visual continuity

**Speaker notes**:
- *(transition from Topic 1)* "Same Coveo platform you just saw running for the Pokémon build — now, briefly, what it would mean for a real enterprise customer. I'm picking ESDC's Employment Insurance directorate because I've been inside this customer through a prior consulting engagement with EY Canada, so this is informed pitch, not researched pitch."

**Key message**: this is a *short* pitch piggy-backing on Topic 1 — credibility comes from the speaker's direct prior experience inside this customer.

---

## Slide 1 — ESDC EI at a glance · the operational gap first-gen RAG can't close (≈90s)

**Visual** — single dense slide combining customer scale + operational backdrop + first-gen RAG limits:

**Scale** (all from public Canada.ca / Open Government Portal — verified 2026-06-04; check freshness day before panel):
- **~39,150 ESDC employees**; **~2,625 EI Call Centre officers** ⁽¹⁾⁽²⁾
- **2–3.1M EI claims/year** (~1.4M approved · ~$14.3B annual payouts) ⁽³⁾
- **20–25M+ EI call-centre calls/year** ⁽⁴⁾
- **Bilingual mandate** (FR/EN parity, Official Languages Act)

**Operational backdrop** — *zero headroom*:
- Peak EI call-centre wait times **>1 hour**; FY 2020-21 average was **1h 02m** ⁽⁴⁾
- Claim processing averages **17-18 days** against Service Canada's **28-day standard** ⁽³⁾ — two-thirds of the window already consumed before AI even helps

**Where first-gen RAG hits limits at this scale**:
1. **Hallucination on policy edge cases** — works on top intents, fails on the long-tail eligibility cases EI is dominated by (record-of-employment anomalies, parental-leave interactions, federal-provincial benefit stacking)
2. **Bilingual divergence** — EN-side accuracy and FR-side accuracy frequently differ; without per-language measurement, it's invisible
3. **No production-grade quality layer** — manual spot-checks, no daily eval, no regression detection, no closed-loop improvement

**Speaker notes**:
- "These numbers are the operational scale AI has to land in. **~2,600 highly-trained agents handling ~3M claims a year against ~23M annual calls. Bilingual. Legally-defensible accuracy required.**"
- "And look at the backdrop. Peak wait times over an hour. Processing already at two-thirds of the 28-day standard before AI even adds value. **No operational headroom — every percentage point of agent efficiency is consequential.**"
- "Now the patterns I keep seeing in first-generation RAG at federal scale — these are *industry patterns*, not engagement-specific. Hallucination on edge cases. Bilingual divergence. No measurement layer. **Each one costs more here than in lower-stakes contexts** because there's no room in the operational envelope to absorb the cost."

**Key message**: large-scale + bilingual + zero operational headroom + three predictable first-gen failure modes = next-generation production AI is not an upgrade, it's a service-delivery prerequisite.

### Sources

⁽¹⁾⁽²⁾ Google: *"how many employees at ESDC Canada and in particular in the EI claim processors and call support"* → AI Overview citing Canada.ca + Canada Open Government Portal QP Note "Employment Insurance Processing and Call Centre" (verified 2026-06-04)
⁽³⁾ Google: *"how many EI claims processed in a year in canada EI"* → AI Overview + Canada.ca *"Employment Insurance (EI) program statistics"* at `canada.ca/programs/ei/statistics` (verified 2026-06-04)
⁽⁴⁾ Google: *"how many calls volume to service canada EI"* → AI Overview citing Canada Open Government Portal QP Note "Investments in Service Canada EI Call Centre" + Canada.ca "Chapter 4: Program administration" 2023-05-26 (verified 2026-06-04)

> **Pre-panel check**: Re-run each Google query the day before; verify the *"Date modified"* footer on each Canada.ca page; substitute newer numbers if older than 12 months.

---

**Visual** — top: pain → Coveo capability mapping; bottom: 3 CIO-grade differentiators.

| First-gen RAG limit | Coveo's productized answer | Live proof |
|---|---|---|
| Hallucination on policy edge cases | RGA **+ closed-loop quality system** (golden dataset · daily eval · analyzer · guardrails · auto-rollback) | The dashboard you saw in Topic 1's demo |
| Bilingual divergence | Semantic Encoder across languages; eval slices **per-locale** (FR + EN dashboards side-by-side) | Architecture is per-locale-extensible (Pokémon is EN-only; federal would add FR) |
| No quality measurement layer | The eval + closed-loop system itself — **every prompt change diffable, every regression auto-rolled-back** | Live, transparent, code-as-source-of-truth in the repo |

**Three CIO-grade differentiators**:

1. 🇨🇦 **Canadian-HQ AI infrastructure** — Coveo HQ'd in Quebec City. Data sovereignty + procurement preference + Algorithmic Impact Assessment posture aligned to a Canadian vendor.
2. 🔌 **Bring-your-own-LLM** — Coveo is the secure permission-aware retrieval layer in front of *any* LLM (Claude, GPT-4o, Gemini, AWS Bedrock, or a future Canadian sovereign LLM). LLM choice is tactical; retrieval is strategic.
3. 🧠 **MCP-ready · retrieval investment compounds** — same Coveo content surface is addressable by any MCP-compatible agent today. Indexing investment in 2026 becomes the agent infrastructure of 2028-2030.

**Speaker notes**:
- *(table)* "Three first-gen limits, three Coveo answers, all already proven in the live build I just showed you. The third row is the differentiator — **most vendors say 'we have an AI feature.' I'm showing you a measurement and improvement system around the AI feature.** For a benefits administrator, that's the difference between trust and liability."
- *(differentiators)* "Three things a CIO loses sleep over: sovereignty, LLM lock-in, future-proofing. **All three line up with Coveo's positioning today, not as a roadmap promise.** Quebec-City HQ. BYO-LLM. MCP-ready. Last one is the unlock — the same Coveo org you stand up for EI in 2026 is your agent surface for the whole department in 2028."

**Key message**: Coveo solves the three first-gen pains AND aligns with the three CIO concerns — uniquely. None of the three differentiators is roadmap-future; they're shipping today.

---

## Slide 3 — Value bands · 24-month roadmap signposts (≈75s)

**Visual** — left: 12-month outcome bands; right: roadmap with 4 milestones.

**12-month outcome bands**:

| Outcome | Range |
|---|---|
| Average Handle Time (AHT) reduction in call centres | **-15 to -25%** |
| Agent ramp-up time (months 3+) | **-30 to -50%** |
| Time-to-resolution for complex eligibility cases | **-20 to -35%** |
| Hallucination regressions detected | **post-incident → within 24h** |

**Roadmap signposts**:

- **0-6 mo**: Connect Coveo to EI policy + SOP corpus · bilingual field schema · Protected B/C source-level security · ~200-Q golden eval · baseline AHT/FCR
- **6-12 mo**: RGA on agent desktop · per-language quality dashboards (FR + EN) · closed-loop tuning active
- **12-24 mo**: ART for usage-driven relevance · citizen-facing self-service (where policy allows) · MCP integration · AIA public reporting
- **24+ mo**: ESDC-wide expansion (CPP, OAS, internal HR/IT) on the same retrieval layer · 1+ LLM provider migration proven

**Speaker notes**:
- *(bands)* "12-month bands, not point estimates. **Honest framing**: Canadian-government peer ROI benchmarks aren't publicly available at this granularity yet — most federal AI reporting in 2025-26 is on the AIA input side, not outcomes. The ranges above use Coveo enterprise customer outcomes as conservative analogs. **We'd refine each band against ESDC's own baseline in the first 90 days.**"
- *(roadmap)* "Sequenced so each phase delivers measurable value before the next is funded. **Months 6-12 — the quality layer — is non-negotiable before scaling out. Measure first, scale second.** By month 24 the investment compounds — same retrieval layer serving CPP, OAS, internal departmental search."

**Key message**: realistic measurable bands + a defensible 24-month platform play that compounds beyond EI alone.

---

## Slide 4 — Why I'd be your FDE · open the conversation (≈45s)

**Visual**: three anchor lines + a "first 30 days" ask box.

**Three reasons**:
1. **I've built every layer myself** — ingestion, search, RGA, eval, closed-loop, observability, MCP — all in the public repo you just saw. Not pitching capabilities; pitching code I've shipped.
2. **Measurement-first discipline** — first thing I'd ship for ESDC isn't the new RGA, it's the eval framework that tells us whether the new RGA is actually better than the existing one.
3. **I've been inside this customer** — prior EY Canada engagement on first-generation RAG deployments inside ESDC EI Claim Processing + Call Centres. Policy surface, bilingual constraints, agent realities — known. **My FDE ramp on this account is short.**

**In the first 30 days I'd ask for**:
- Access to current AI deployment metrics + agent-side feedback (baseline)
- Stakeholder alignment with DG Service Delivery + Policy Owner + Security/AIA reviewer
- A scope-limited pilot (one EI sub-workflow — e.g., maternity benefits eligibility) for the 6-month foundation phase

**Speaker notes**:
- "Three reasons I'd be the right FDE. Built every layer. Measurement before optimisation. **And — credibility moment — I've been inside this customer before through EY Canada. I know the workflows. I know what 'first-gen' looks like in production.** That's a rare combination on a Coveo FDE bench."
- *(close)* "If this conversation continues, those three asks in the next 30 days move us from pitch to plan. Open to questions on this or Topic 1."

**Key message**: I bring Coveo platform fluency AND customer-specific operating knowledge — rare combination, short ramp.

**Q&A trap**: *"Conflict-of-interest risk from the EY engagement?"* — answer: *"Standard professional discipline. Confidential details from the EY engagement stay confidential. Patterns and publicly-defensible observations inform the pitch. Same separation any FDE maintains when re-engaging a customer through a different vendor."*

---

## Q&A — anticipated questions + prepared answers (ESDC-specific)

| Q | Prepared answer (compressed) |
|---|---|
| "Are you saying our current RAG is bad?" | No. First-generation RAG deployments at federal scale all hit the same patterns — long-tail accuracy, bilingual divergence, no measurement layer. ESDC is among many. The conversation is about *what's next*, not what was wrong with what came first. |
| "What's the conflict-of-interest with your EY engagement?" | Confidential engagement details stay confidential. Patterns and public-domain observations inform the pitch. Standard professional discipline. |
| "How does this work with our Algorithmic Impact Assessment requirements?" | Coveo's closed-loop quality system + audit trail + per-prompt version history is *exactly* the documentation that AIA reviewers expect. It produces the artifacts that an AIA renewal would otherwise require building from scratch. |
| "What about Treasury Board's Directive on Automated Decision-Making?" | The Directive requires impact assessment, transparency, and recourse mechanisms. The eval framework provides Level 2/3 transparency artifacts; Coveo's citations provide source recourse; the closed loop with auto-rollback addresses ongoing monitoring requirements. |
| "Where does the data live?" | Configurable per deployment. Coveo offers Canadian-region deployment options. Source content can stay on-premise via Crawling Modules or be cloud-hosted depending on classification. |
| "Can this handle Protected B / Protected C content?" | Coveo's source-level security model. Permissions inherited from source systems at index time; users see only what they're authorised to. Federal customers in regulated sectors have deployed under similar classification constraints. |
| "How would this fit alongside our EI Modernization program?" | The Modernization program is rebuilding the core EI processing engine. Coveo sits in the agent / decision-support layer *adjacent* to that — same content, different access path. The retrieval investment is independent of the core system refresh, which means it can deliver value during Modernization, not after. |
| "What's the realistic deployment risk?" | The closed-loop + auto-rollback is the risk mitigation. Pilot scope to one sub-workflow first (e.g., maternity benefits eligibility), measure for 90 days against baseline, scale by sub-workflow over months 6–24. Don't ship to all of EI at once. |
| "Cost framing?" | Coveo's consumption-based licensing scales with use. The eval system runs on ~$0.60-$1.20/day in Sonnet tokens for 100-200 questions. The platform investment compounds — by month 24, the same Coveo organisation is serving multiple ESDC programs from a single retrieval layer. |
| "What about French-language LLM choice — could we use a Canadian LLM provider for FR content?" | Yes. BYO-LLM means you can route FR queries to one LLM and EN to another, or to the same model with different prompts. Coveo is the retrieval layer; the LLM choice is yours and can evolve. |
| "What if we already have a vendor commitment that overlaps?" | Coveo can layer on top as the grounding + AI quality layer while existing retrieval (e.g., an existing search engine) continues to serve. Hybrid stacks are common during migration. |
| "How do we measure success at month 12?" | Three numbers: AHT delta, first-contact resolution delta, eval accuracy. All three measurable from the framework live today in my repo. No new instrumentation needed. |
| "Who owns prompt engineering — your team or ours?" | ESDC policy + content teams own the prompts; Coveo's FDE coaches patterns and operates the apply mechanics. The closed-loop system is exactly that division of labor — analyzer proposes, humans review, system applies via code. |
| "What's the LLM cost for production scale?" | Generative answer costs scale with query volume. Coveo's RGA dedups identical queries at billing layer. For ~30M call centre interactions, only ~5-10% would route through RGA initially (longest-tail complex questions); pilot scope is much smaller. |

---

## Trim levers if running long

Total budget is ~5-7 min of slides (no demo — Topic 1's demo serves as proof; shared Q&A at the end). If a dry-run hits 8+ min, cut in this order:

1. **Slide 3 right side (roadmap)** → drop the 24+ mo signpost; finish at 12-24 mo. Save ~15s.
2. **Slide 4 anchor #1 ("I've built every layer")** → cut; Topic 1 already established it. Save ~10s.
3. **Slide 3 left side (bands table)** → drop to 2 rows (AHT + hallucination regressions). Save ~20s.

Total trimmable: ~45s. **Slides 1 + 2 + Slide 4's "I've been inside this customer" anchor are immovable** — that's the core pitch.

## Presentation-day notes

- **The "I know this customer" angle is your strongest credibility lever.** Don't bury it; surface it early (Slide 0 frames the talk that way; Slide 8 makes it explicit).
- **Bilingual framing matters.** When delivering, drop the occasional French phrase if natural ("en français comme en anglais", "service aux citoyens"). It signals you understand the federal-bilingual operational reality without being performative.
- **CIO audience listens for risk + sovereignty + multi-year platform.** Resist the urge to talk tactically about agent productivity. The DG Service Delivery audience would want that; the CIO wants the architecture story.
- **The "first-generation RAG" framing must stay diplomatic.** Never name a vendor, never disparage. The story is "what's next," not "what was wrong."

## Companion docs to lean on (don't re-explain — link)

- [`docs/rga-eval-methodology.md`](../../docs/rga-eval-methodology.md) — the eval framework (the slide-3-row-3 anchor)
- [`docs/passage-retrieval.md`](../../docs/passage-retrieval.md) — Coveo's "R in RAG" positioning + named enterprise customers
- [`docs/mcp-integration.md`](../../docs/mcp-integration.md) — MCP positioning for the BYO-LLM + future-agent slide
- [`docs/observability.md`](../../docs/observability.md) — measurement layer (slide 3 row 3)
- [`docs/caching-strategy.md`](../../docs/caching-strategy.md) — production hardening for the roadmap
- [`docs/detail-page.md`](../../docs/detail-page.md) — three-surface platform play (slide 4 row 3)

---

## Files this deck draws from (in delivery order)

| Slide | Companion artifact | Why |
|---|---|---|
| 0, 1 | Public ESDC reporting + speaker bio | Cover + credibility |
| 2 | Auditor General reports + industry pattern | Pain framing without confidentiality risk |
| 3 | Live builds — `pokemon-rga-dashboard.vercel.app` + `pokemon-search-one-chi.vercel.app` | Working proof |
| 4 | `docs/passage-retrieval.md` + `docs/mcp-integration.md` | Differentiation |
| 5 | Coveo customer benchmarks + Pokémon eval framework | Quantified value |
| 6 | Live demos | Working proof at scale |
| 7 | `docs/caching-strategy.md` + project plan | Sequenced roadmap |
| 8 | Speaker's prior EY engagement (general references) + repo | Credibility |
| 9 | — | Open conversation |
