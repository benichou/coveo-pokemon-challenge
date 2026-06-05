# Presentation #1 · Topic 2 — Enterprise Customer Pitch

**Customer**: **Employment and Social Development Canada (ESDC) · Employment Insurance directorate** — specifically the EI Claim Processing Centres + EI Call Centres operated by Service Canada.

**Audience role**: **CIO / Director General of Digital, ESDC** — strategic, multi-year platform thinking. Procurement, enterprise architecture, and risk framing weigh heavily.

**Framing**: **Detailed reference** — the speaker has prior consulting experience deploying first-generation RAG systems for this exact customer (via EY Canada). The pitch leverages that experience as credibility ("I've been inside these workflows") without exposing confidential engagement details.

**Time budget**: ~25 min total — 10 min slides + 5 min live demo (the Pokémon build as a working analog) + 10 min Q&A.

**Total slides**: 10 (excluding cover). Pace = ~60s per slide.

**Working title**: *"From first-generation RAG to production-grade AI — what Coveo brings to ESDC's next decade of citizen service"*

---

## ⚠️ Source-material discipline — what's defensible vs not

The "detailed reference" framing allows specific references to the prior engagement, but **every claim about pain points should be backed by one of**:

1. **Public ESDC / Service Canada reporting** (Auditor General reports, Departmental Plans, Public Accounts of Canada, EI Monitoring and Assessment Report)
2. **Published Treasury Board policy** (Directive on Automated Decision-Making, AI Strategy for the Federal Public Service)
3. **General industry patterns** for first-gen RAG deployments at scale (hallucination, bilingual gaps, content silos, quality measurement maturity)

**Avoid**: naming the specific vendor / stack EY selected, internal architecture details, named individuals at ESDC, specific dollar figures or volumes you only know from the engagement. **Use public ESDC reporting numbers for any quantitative claim.**

If a panelist asks for specifics you can't share, say so directly: *"That detail is from a confidential engagement — happy to speak to the public pattern around it instead."*

---

## Slide 0 — Cover (≈10s)

**Visual**:
- Title: **ESDC Employment Insurance — Production-grade AI for citizen service**
- Subtitle: From first-generation RAG to a measured, sovereign, multi-LLM future
- Bottom-left: speaker name + role (FDE candidate, Coveo)
- Bottom-right: live URLs + GitHub repo
- Background: a clean GBC-volcano-theme screenshot of the live Atomic UI (subtly bilingual / federal-feeling — neutral colour, not patronising)

**Speaker notes**:
- "I'm going to walk through how Coveo would partner with ESDC for the next generation of AI in Employment Insurance — specifically Claim Processing and Call Centres. The pitch comes from two places: my technical work on the Coveo platform, and prior consulting experience deploying first-generation RAG for this exact customer."

**Key message**: this isn't a cold pitch — it's informed by direct experience inside ESDC EI's AI rollout.

---

## Slide 1 — ESDC EI at a glance (≈60s)

**Visual**:
- ESDC + Service Canada logos
- Quick stats (all sourced from public Canada.ca / Open Government Portal pages — see source table below the slide notes; **re-verify the date stamp on each source before the panel**):
  - **~39,150 ESDC employees** (≈38,200 FTE; ~19,000 of these operate under the Service Canada banner) ⁽¹⁾
  - **~2,625 EI Call Centre officers** post-pandemic (more than double pre-pandemic capacity; moving toward ~2,450 officers for 2023-24) ⁽²⁾
  - **2 to 3.1 million EI initial + renewal claims processed annually** by Service Canada (~1.4M approved as regular benefits; ~$14.3B in annual payouts) ⁽³⁾
  - **20 to 25+ million calls per year** received by the Service Canada EI call centre (~23.6M in FY2122; 2M+ stabilized inquiries annually post-pandemic; wait times range from ~1 min off-peak to >1 hour at peak) ⁽⁴⁾
  - **100% bilingual mandate** (FR/EN parity required under the Official Languages Act)
  - Content surfaces: EI Act + Regulations, Service Canada SOPs, agent knowledge base, policy interpretation bulletins, court / SST decisions, internal training material

**Speaker notes**:
- "ESDC delivers the largest set of direct-to-citizen federal programs in Canada. The numbers on this slide are the operational scale that AI has to land in."
- "Two operational engines: **Claim Processing Centres** — where agents make eligibility decisions on filed claims — and **EI Call Centres** — where agents help citizens understand status, requirements, and policy."
- "Combined, that's ~2,600 highly-trained agents and ~3M claims a year operating against ~23M annual calls. **Bilingual. Legally-defensible accuracy required.** That's the workload AI was deployed to support."

**Key message**: large-scale, high-stakes, bilingual, regulated. Standard Coveo fit at the *most demanding* end of the spectrum.

### Sources for Slide 1 stats

> Cite these inline on the slide as footnotes ⁽¹⁾⁽²⁾⁽³⁾⁽⁴⁾ — panelists will check, and citing publicly-defensible sources is part of the discipline.

| # | Stat | Primary source | Found via |
|---|---|---|---|
| ⁽¹⁾ | ESDC employees: ~39,150 (≈38,200 FTE, ~19,000 under Service Canada) | Government of Canada Human Resources Statistics + Canada.ca workforce demographics pages | Google search: *"how many employees at ESDC Canada and in particular in the EI claim processors and call support"* → AI Overview citing Canada.ca +2 (verified 2026-06-04) |
| ⁽²⁾ | EI Call Centre officers: ~2,625 (pandemic peak >3,000; target ~2,450 for 2023-24) | Canada - Open Government Portal — Question Period Note: "Employment Insurance Processing and Call Centre" — `https://search.open.canada.ca/qpnotes/record/esdc-...` | Same Google search as ⁽¹⁾ → featured snippet |
| ⁽³⁾ | EI claims: 2–3.1M initial + renewal/year; ~1.4M approved as regular benefits; ~$14.3B annual payouts; ~17-18 day processing average; ~90% within 28-day standard | Canada.ca — "Employment Insurance (EI) program statistics" — `https://www.canada.ca/programs/ei/statistics` + Canada - Open Government Portal (Question Period Notes: Employment Insurance Processing - Question Period Notes) | Google search: *"how many EI claims processed in a year in canada EI"* → AI Overview citing Canada Open Government Portal +2 (verified 2026-06-04) |
| ⁽⁴⁾ | EI call volume: 20-25M+ calls/year; 23.6M in FY2122; 5.6M answered in 2020-21; 2M+ inquiries stabilized post-pandemic; wait times 1 min → 1+ hour | Canada - Open Government Portal — "Question Period Note: Investments in Service Canada EI Call Centre" — `https://search.open.canada.ca/qpnotes/record/esdc-...`; Canada.ca — "Chapter 4: Program administration" (published 2023-05-26) — links from Canada.ca's EI program pages | Google search: *"how many calls volume to service canada EI"* → AI Overview citing 5 sites (verified 2026-06-04) |

**Pre-panel check-list** for Slide 1:
- [ ] Re-run each Google query a day before the panel — confirm numbers haven't been superseded by newer reporting
- [ ] Click through each Canada.ca / Open Government Portal URL above and capture the date stamp on the source page (Canada.ca pages display a "Date modified" footer)
- [ ] If any number is older than ~12 months, find the most recent quarterly or annual update in the same source and use that instead
- [ ] If a panel member asks for the source mid-talk, have these URLs in a notes panel ready to read aloud

---

## Slide 2 — Current state: where first-generation RAG hits limits (≈90s)

**Visual**: an **operational backdrop callout** at the top, then three pain bullets.

> **Operational backdrop** — peak EI call-centre wait times exceed **1 hour** during high-volume periods; in 2020-21 the average answered-call wait time reached **1 hour, 2 minutes** ⁽⁵⁾. EI claim processing averages **17-18 days**, with ~90% landing within Service Canada's **28-day standard** ⁽³⁾ — leaving little headroom before the standard is breached. **Every percentage point of agent efficiency or AI accuracy is operationally consequential in this environment.**

Then the three first-gen RAG limits, each costing more here than in lower-stakes contexts:

1. **Hallucination + accuracy gaps on policy edge cases.** First-generation RAG deployments tend to ground well on top-frequency questions and fail on the long-tail edge cases that EI eligibility is dominated by. Sources: industry pattern + Treasury Board's Directive on Automated Decision-Making (which mandates impact assessments precisely *because* AI accuracy varies by case complexity).
2. **Bilingual content disparity.** Federal departments must serve FR and EN at parity, but RAG quality often diverges between languages — typically because retrieval corpora aren't equally curated across both. Sources: Office of the Commissioner of Official Languages reports on AI fairness across languages.
3. **No production-grade AI-quality measurement loop.** Most first-gen deployments ship a RAG and rely on manual spot-checks or anecdotal agent feedback. There's no daily eval, no regression detection, no closed-loop improvement, no public quality dashboard. Sources: industry pattern + federal AI maturity reporting.

**Speaker notes**:
- *(Backdrop)* "Before we get to where AI hits limits, look at the operational backdrop. **Peak wait times over an hour. Processing times against a 28-day service standard with 17-18 day averages — that's two-thirds of the standard, not half.** There's no operational headroom. The cost of an inaccurate AI answer isn't user-frustration; it's a missed service standard or a regulatory exposure."
- "Now — these are general patterns about first-generation RAG at federal scale. I want to be careful to talk about the pattern rather than confidential specifics from my prior engagement."
- *(Pain 1)* "EI eligibility cases distribute heavily into the long tail. Top 20 question intents are easy; the **right** 80% of citizen need is in cases the system has never seen — record-of-employment anomalies, dependency overlaps, parental-leave interactions, federal-provincial benefit stacking. First-gen RAGs ground confidently on training data they don't actually have for those cases. **In a 17-day processing window, agents who can't trust AI answers re-verify manually — and that consumes the headroom**. It's hallucination as service-standard risk, not just UX inconvenience."
- *(Pain 2)* "Bilingual divergence is its own discipline. You can have a 90%-accurate EN-side RAG and a 70%-accurate FR-side RAG sharing the same dashboard — and unless you're measuring per-language, you'll think you're at 85%. The Official Languages compliance bar makes this not optional."
- *(Pain 3)* "And the meta-issue is the absence of a quality measurement layer in the first place. Most government AI rollouts in 2024–2026 published ROI projections but not quality metrics. That changes the conversation about what 'production-grade' means."

**Key message**: AI deployed; AI under production-grade operational discipline — those are two different things. In ESDC's specific operational envelope (28-day standard, 1+ hr peak wait times), the gap between the two is service-delivery risk, not theoretical risk.

**Q&A trap**: *"Are you criticising the existing system?"* — answer: *"No. I'm describing the general pattern that first-generation RAGs in any sector run into at scale. ESDC is among many federal organisations navigating this. The question isn't whether the first deployment was correct — it's what the next-generation platform should look like."*

### Sources for Slide 2 operational backdrop

⁽⁵⁾ **Peak wait times >1 hr; 2020-21 average 1h02m**: Canada - Open Government Portal — "Question Period Note: Investments in Service Canada EI Call Centre" — `https://search.open.canada.ca/qpnotes/record/esdc-...` (found via Google search *"how many calls volume to service canada EI"* — same QP Note as Slide 1 footnote ⁽⁴⁾; verified 2026-06-04).

⁽³⁾ **Processing time 17-18 days average; ~90% within 28-day standard**: Same source as Slide 1 footnote ⁽³⁾ — Canada.ca EI Program Statistics + Canada Open Government Portal "Employment Insurance Processing - Question Period Notes". The 28-day Service Canada standard is publicly published as the service commitment for EI initial claim processing.

---

## Slide 3 — The Coveo answer, mapped to each pain (≈90s)

**Visual**: 3-row table — Pain · Coveo capability · Live proof from the Pokémon build.

| Pain | Coveo capability | Demonstrated in my live build |
|---|---|---|
| Hallucination on policy edge cases | Relevance Generative Answering (RGA) **plus** the closed-loop AI-quality measurement system (100-Q golden dataset + daily Sonnet 4.6 judge + analyzer + guardrails + auto-rollback) | The dashboard at `pokemon-rga-dashboard.vercel.app` shows the loop running daily; the analyzer caught a hallucination pattern in our baseline and proposed a prompt fix that lifted accuracy from 62% to ~78% on a single revision — applied through code, audit-trailed, reversible |
| Bilingual disparity | Semantic Encoder operates across languages; Coveo's connectors handle multilingual sources natively; the same closed-loop eval can run **per-language** | The eval framework I built doesn't currently slice by language because Pokémon content is English-only — but the architecture is per-locale-extensible. A federal deployment would have FR and EN dashboards side-by-side. |
| No quality measurement layer | The eval system + closed-loop is the answer. Every prompt change is diffable, every applied change is traceable, every regression is auto-rolled-back. | All of it is live + open-source-style transparent at `pokemon-rga-dashboard.vercel.app` — the same primitive a federal customer would operate. |

**Speaker notes**:
- "Three pains. Three Coveo capabilities. And — critically — a working live proof for each, that you can see in the demo I'll show in two slides."
- "The third row is the one that distinguishes Coveo from any other vendor in this market. **Most vendors will say 'we have an AI feature.' I'm showing you a measurement and improvement system around the AI feature.** For a department whose AI accuracy directly impacts citizens' benefit eligibility, that's not a 'nice to have'."

**Key message**: every pain has a Coveo capability AND a live demo, not just a slide. The third pain's answer is uniquely Coveo's positioning advantage.

---

## Slide 4 — Why Coveo specifically — three CIO-grade differentiators (≈75s)

**Visual**: three big callouts.

1. 🇨🇦 **Canadian-headquartered AI infrastructure** — Coveo is HQ'd in Quebec City. Federal data sovereignty + procurement preference + Algorithmic Impact Assessment posture aligned to a Canadian platform vendor.
2. 🔌 **Bring-your-own-LLM** — Coveo is the secure permission-aware retrieval layer in front of *any* LLM. Anthropic Claude, OpenAI GPT-4o, Microsoft Azure AI, AWS Bedrock, Google Gemini, **or a domestic / departmental LLM**. The choice of LLM provider can change quarter-by-quarter; Coveo doesn't.
3. 🧠 **MCP-ready — your retrieval investment compounds into your agent investment** — the same Coveo content surface is addressable by any MCP-compatible AI agent (Claude Enterprise, ChatGPT Enterprise, internal agents) without per-LLM integrations. Your investment in indexing today becomes the agent infrastructure of 2027–2030.

**Speaker notes**:
- "Three reasons this is the right partnership for ESDC specifically — and these are the lenses I'd expect a CIO + DG Digital to weigh most."
- *(1)* "Sovereignty matters more in 2026 than it did in 2022. Coveo's Canadian HQ + federal-readiness posture is procurement gold for a federal department."
- *(2)* "LLM choice is a tactical decision; the retrieval layer is a strategic one. BYO-LLM means ESDC's LLM strategy can evolve — including to a future Canadian sovereign LLM — without re-platforming the search/retrieval base."
- *(3)* "And the platform compounds. Index for the call centre today; that same Coveo organisation is your agent infrastructure when ESDC ships internal agents in 2028. Demonstrated live in my build — same Coveo org powers a web UI, a detail page, AND Claude Code through MCP. **Three surfaces, one platform investment.**"

**Key message**: the three things a CIO would lose sleep over (sovereignty, LLM lock-in, future-proofing) all align with Coveo's positioning today, not as a roadmap promise.

---

## Slide 5 — Quantified value: 12-month outlook (≈75s)

**Visual**: 4 outcome rows, framed in CIO-grade metrics. Bands, not point estimates. Footnoted assumptions.

| Outcome | 12-month range | Assumption / source |
|---|---|---|
| Average Handle Time (AHT) reduction in call centres | -15 to -25% | Coveo enterprise customer benchmarks (Xero, SAP Concur, Forcepoint); production gains from unified retrieval + RGA on agent desktops |
| Agent ramp-up time | -30 to -50% (months 3+) | Industry pattern for unified-retrieval deployments; new agents reach productivity faster when policy + procedure + bulletins are one ranked surface |
| Hallucination / accuracy regressions detected before citizen impact | shifts from "discovered post-incident" → "caught within 24h" | Direct consequence of the daily eval + closed-loop; demonstrated in live build |
| Time-to-resolution for complex eligibility cases | -20 to -35% | Single ranked surface + Passage Retrieval citations vs multiple separate searches against siloed sources |

**Speaker notes**:
- "I'm giving 12-month ranges, not point estimates. Government ROI math is usually multi-year, but a 12-month horizon is where the platform investment starts to pay back AHT, ramp, and risk."
- "Notice row 3. **The biggest value isn't the headline accuracy number — it's catching regressions before citizens feel them.** For a benefits administrator, a hallucination that reaches an EI claim decision is a Form 1391 or worse downstream. The closed-loop turns 'discovery' into 'prevention'."
- *(If asked about the source of the bands)* "Honest framing: Canadian government-peer ROI benchmarks at this granularity aren't publicly available yet — most federal AI reporting in 2025-26 is on the AIA / input side, not on outcomes. The ranges above use **Coveo enterprise customer outcomes as conservative analogs**. We'd refine each band against ESDC's own baseline measurement in the first 90 days of the engagement."

**Key message**: realistic ranges, the right metrics for the CIO chair, with a risk-reduction line item that's specific to government scrutiny. Honest about the source for the bands.

---

## Slide 6 — Live proof: the Pokémon analog (≈4-5 min demo)

**Visual**: switch from slides to the live deployed app.

**Demo script — "imagine pokemondb is your EI policy + SOP corpus"**:

1. *(0:00)* Open https://pokemon-search-one-chi.vercel.app (let theme rotation pick a biome). *"Replace pokemondb.net with EI Act + Service Canada SOPs + court rulings in your mental model. Same retrieval primitive, same surface."*
2. *(0:30)* Type a query → RGA streams. *"Notion AI today returns an answer. Your agents would see this PLUS the citation back to the source policy section. Verification is one click — and that's what an EI determination requires."*
3. *(1:30)* Click the Source facet to show dual-source items. *"Your SOPs + the EI Act + bulletins + court rulings would all surface here, ranked together."*
4. *(2:00)* Click a result → detail page loads. *"Hero card with the canonical answer, related content surfaced semantically, verifiable passages from the source documents. Same Coveo brain."*
5. *(3:00)* Open the RGA quality dashboard at `pokemon-rga-dashboard.vercel.app`. *"Every day at 06:00 UTC, the system measures 100 questions against ground truth. The chart markers show every prompt change with a clickable diff. **This is the auditable measurement layer that doesn't currently exist in most government AI deployments.**"*
6. *(4:00)* Quick MCP demo via `/pokemon-mcp demo` in Claude Code. *"And the same content surfaces to any MCP-compatible agent — Claude, ChatGPT Enterprise, future internal agents. **Zero additional integration. Your retrieval investment compounds.**"*

**Demo tips**:
- Keep the narration *about ESDC's hypothetical experience*, not Pokémon. Every "Charizard" becomes "an EI eligibility question" in your delivery.
- Pre-record a 90-second fallback in case Wi-Fi drops.

**Key message**: this is what the next-generation production AI platform for ESDC EI could look like — not a slide deck, working code.

---

## Slide 7 — Roadmap: 0 / 6 / 12 / 24 months (≈75s)

**Visual**: 4-milestone timeline.

**0–6 months — Foundation**:
- Phase 1: Connect Coveo to EI policy + SOP corpus (Coveo connectors for SharePoint, file-share, internal CMS as relevant)
- Define unified bilingual field schema; respect Protected B/C content classifications via source-level security
- Stand up the eval framework: ~200-question bilingual golden dataset spanning top + long-tail EI scenarios
- Baseline metrics: AHT, first-contact resolution, agent confidence scores

**6–12 months — Production AI quality layer**:
- Deploy RGA in the agent desktop (Service Canada agent UI integration)
- Public-facing (or internal-facing) quality dashboard for the EI digital team
- Closed-loop prompt tuning system active (autonomous overnight improvements with auto-rollback)
- Per-language eval dashboards (FR + EN side-by-side)

**12–24 months — Platform extension**:
- Layer ART (Automatic Relevance Tuning) for usage-driven relevance
- Citizen-facing self-service search (where policy allows) — informed by agent-side learnings
- MCP integration for future ESDC agent initiatives (LLM-of-choice flexibility maintained)
- Algorithmic Impact Assessment public reporting framework

**24+ months — Compounded platform**:
- ESDC-wide expansion beyond EI: CPP, OAS, ESDC-internal HR / policy / IT search all served by the same retrieval layer
- LLM provider portability proven through 1+ provider migrations
- Coveo serves as the canonical retrieval + grounding layer for departmental AI

**Speaker notes**:
- "This is the CIO-horizon view — a 24+ month platform play, sequenced so each phase delivers measurable value before the next is funded."
- "Two things to notice. **First**, the AI-quality layer (months 6–12) is non-negotiable before scaling out — measure first, scale second. **Second**, the platform compounds — by month 24, the investment that started in EI is serving CPP, OAS, and internal departmental AI without re-platforming."

**Key message**: a sequenced, defensible, milestone-driven roadmap that respects government risk posture while still delivering compounding value.

---

## Slide 8 — Why I'd be your FDE (≈45s)

**Visual**: three quick anchor points — building, measuring, knowing the customer.

**Speaker notes**:
- "Three reasons I'd be the right Forward Deployed Engineer for ESDC specifically."
- **1. I've built every layer myself.** "Ingestion, search, AI grounding, eval, observability, closed-loop, MCP integration — all live in the public repo I've been showing you. I'm not pitching capabilities; I'm pitching code I've shipped."
- **2. I lead with measurement before optimisation.** "First thing I'd ship for ESDC isn't the new RGA — it's the eval framework that tells us whether the new RGA is actually better than the existing one. That's the discipline I demonstrated in the Pokémon build."
- **3. I know this customer.** "I've done prior consulting work on first-generation RAG deployments at ESDC EI through EY Canada. I've been inside Claim Processing and Call Centre workflows. I know the policy surface, the bilingual constraints, the agent realities, and what 'first-gen' looks like in production. **My ramp curve as your FDE on this account is short.**"

**Key message**: I bring both the Coveo platform fluency AND prior customer-specific operating knowledge. Rare combination, low onboarding cost.

**Q&A trap**: *"What's the conflict-of-interest risk given your prior engagement?"* — answer: *"Standard professional discipline. Confidential details from the EY engagement stay confidential. Patterns and publicly defensible observations inform the pitch. The same separation any FDE would maintain when re-engaging a customer through a different vendor."*

---

## Slide 9 — What I'd want from you in 30 days (≈30s)

**Visual**:
- *"To move from pitch to plan, what I'd need:"*
- 3 bullets:
  - **Access** to current AI deployment metrics + agent-side feedback for baseline
  - **Stakeholder alignment** — DG Service Delivery, Policy Owner, Security/AIA reviewer
  - **A scope-limited pilot scope** — one EI sub-workflow (e.g., maternity benefits eligibility) for the 6-month foundation phase
- "Open to questions."

**Speaker notes**:
- "If this conversation continues, here's what I'd ask for in the first 30 days. Concrete, scoped, measurable."

**Key message**: ready to start; concrete first-30-days asks; not abstract.

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

Total budget is ~10 minutes of slides + 5 min demo. If a dry-run hits 13 min, cut in this order:

1. **Slide 5 (quantified value)** → drop to 1-bullet headline + footnote. Save 40s.
2. **Slide 7 (roadmap)** → cut the 24+ months column; finish at 12-24. Save 30s.
3. **Slide 8 (why me)** → cut bullet 1; keep 2 and 3. Save 20s.

Total trimmable: ~90s. Slides 0, 1, 2, 3, 4, 6, 9 are immovable — that's the core pitch.

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
