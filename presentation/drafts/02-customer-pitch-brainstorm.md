# Customer-pitch brainstorm — ESDC EI · solution + ops mapping

> **Purpose**: deepen the Topic 2 pitch by mapping every Coveo component we *actually built* in the Pokémon Challenge to a specific ESDC EI workflow + operating rhythm. Goal: the panel hears "I have already shipped exactly this, here's how it lands in your reality."
>
> **Status**: brainstorm. To be reviewed with Franck before pushing pieces into `02-customer-pitch.md`. Nothing here is final-slide-ready yet.
>
> **Companion**: `presentation/drafts/02-customer-pitch.md` (the locked 4-slide structure)

---

## 1 · Solution mapping — Pokémon build ↔ ESDC EI workflows

For each component shipped in the public build, the concrete ESDC EI use case it serves. **Every row maps a working artifact to a real workflow** — no roadmap-future claims.

### 1.1 · Ingestion + index

| Pokémon build | ESDC EI equivalent | Why it fits |
|---|---|---|
| **Dual-source ingestion** (Sitemap A + Python Push B) | **Source A**: Service Canada policy/SOP corpus + Canada.ca · **Source B**: Push from policy databases, EI Modernization metadata, case-management notes, internal wikis | ESDC content is scattered across many silos. Same dual-source pattern unifies them in one ranked index. Sitemap source is throttle-safe (Coveo handles); Push gives control over per-record metadata and freshness. |
| **5-field indexed schema** (multi-value `pokemon_type`, faceted `generation`, etc.) | **Richer field schema**: `policy_section_id`, `last_reviewed_date`, `language` (en/fr), `sensitivity_classification` (Public / Protected A/B/C), `permission_groups`, `benefit_program` (EI Regular / Maternity / Parental / Sickness / Special), `jurisdictional_scope` (federal vs federal-provincial overlap) | Same fielded-document model; just denser metadata. Each field becomes a facet on the agent desktop. |
| **Versioned scraping/scripting config** (`config/`, `scripts/`) | Same pattern — one folder per resource, idempotent bootstrap, audit log per change | Crown procurement values code-as-source-of-truth; matches no-vendor-lock-in language in procurement frameworks. |

### 1.2 · ML models on the default pipeline

| Pokémon build | ESDC EI equivalent | Real-world example |
|---|---|---|
| **RGA** (Custom Prompt v1.1.0, 8 rules) | RGA on agent desktop — answer in natural language with citations back to the SOP | EI officer fielding a call about parental leave + provincial top-up. RGA composes a citizen-friendly answer and cites the exact SOP section. Officer reads it on screen, paraphrases to citizen. |
| **Semantic Encoder** | Recovers paraphrase / synonym queries that keyword-only retrieval misses | Officer types "can the dad take time off after baby"; SE finds "Parental Benefits — Standard vs Extended" policy doc even though that exact wording isn't in the SOP. |
| **Query Suggest** (152 seed queries) | Officer-history-seeded type-ahead | New officer (3-month tenure) types "EI" and sees the 20 most common queries from senior officers. Embedded coaching. |
| **Passage Retrieval** | Returns specific paragraph excerpts for citation in case notes | Officer needs to paste a defensible policy reference into the case file. PR returns the exact paragraph. Citation is auditable. |

### 1.3 · UI surfaces · which one for which workflow

| Pokémon build | ESDC EI workflow | Why this surface |
|---|---|---|
| **Atomic main page** (faceted list view, RGA panel, PR panel) | **Not used directly** — internal pattern reuse | The federal agent desktop wouldn't use Atomic as-is; it'd be a custom Headless+React surface embedded in the case management system. But the *components* (facets, RGA, PR) are reusable. |
| **Headless+React detail page** (hero + Featured Insights + Related grid, 3 parallel Coveo round-trips) | **The agent decision-support surface** — when an officer opens a claim, the page loads: hero (claim summary), passages (relevant policy excerpts), related (anonymised past cases) — all 3 queries in parallel | Sub-second load. Officer doesn't switch between systems. Same retrieval primitive that powered the Pokémon detail page, now agent-facing. |
| **Coveo MCP Server** (4 tools: search · fetch · get_passages · answer) | **The 2027-2030 path** — internal AI assistants ("Copilot for Service Canada"), voice IVR LLM agents, citizen-facing chatbots all hit MCP | Today the agent desktop hits the Search API directly. As ESDC adopts more LLM-driven interfaces, MCP is the consolidation layer. **One index, N consumption modes, zero per-client integration code.** |

### 1.4 · Quality & operations layer

| Pokémon build | ESDC EI equivalent | What it produces |
|---|---|---|
| **rga-eval** (100-Q golden, Sonnet 4.6 LLM-judge, daily 06:00 UTC cron) | **ESDC-scale eval**: ~200-500 Q hand-curated, layered (50% top-intent · 35% multi-source synthesis · 15% edge / refusal) — **FR + EN side-by-side** | Daily AI quality scorecard. Per-language, per-benefit-program, per-tier accuracy. This artifact IS the AIA reporting evidence. |
| **rga-closed-loop** (5-day window analyzer · Sonnet 4.6 proposer · 5 guardrails · daily 06:30 UTC cron) | **ESDC autonomous improvement loop** + AIA-aware guardrail · human-in-the-loop for any change touching legally-defensible policy interpretation · Coveo native A/B for actual rollout | Every prompt change is a versioned audit event. Auto-rollback if next-day quality drops. AIA reviewer sees the full decision trail. |
| **Public Vercel-hosted dashboard** (time-series · per-Q drill-down · chart markers per applied change · diff view) | **Internal AIA dashboard**: same UI, additional slices for per-language + per-benefit-program + per-tier · accessible to AIA reviewers, DG Service Delivery, Policy Owners | Single source of truth for "is the AI working." Replaces quarterly retrospective spreadsheets. |
| **Grafana Cloud query observability** (top queries · RGA fire rate · latency p95/p99 · errors · source mix) | **ESDC operational dashboard**: top agent queries (training-gap signal) · per-region query mix (Atlantic / Québec / Ontario / Prairies / BC) · FR/EN ratio over time · failed-RGA cases (where officer had to escalate vs got an answer) | Operational health for the platform team + training signal for Workforce Development. |
| **Claude Code skills** (`/pokemon-mcp`, `/rga-eval`, `/rga-closed-loop`) | **ESDC FDE skills kit**: `/esdc-eval`, `/esdc-closed-loop`, `/esdc-mcp` — same UX, same primitives, ESDC content | How the embedded Coveo FDE works from a terminal at ESDC. Cuts out a lot of manual Console clicking. |

### 1.5 · Code-as-source-of-truth

| Pokémon build | ESDC EI equivalent |
|---|---|
| `scripts/bootstrap.sh` (one-command full provisioning) | Same pattern → repeatable across dev / staging / production environments. Crown procurement requirement-friendly. |
| `.github/workflows/` (daily eval + closed-loop crons) | Same — except managed via Government of Canada's GitOps platform (or equivalent) instead of GitHub.com directly. Pattern is identical. |
| `prompts/history/` (every prior prompt version archived as YAML) | **Immutable AIA audit artifact**. Every prompt change is a YAML file with rationale, date, predicted lift. AIA reviewer can reconstruct any past system state. |
| `eval-runs/*.json` (commit history = time-series DB) | Same — daily JSON in version control. Auditable, diffable, no external DB required. |

---

## 2 · Operational rhythm — what living with this looks like at ESDC

The closed-loop story is most credible when paired with a concrete cadence. Daily / weekly / monthly / quarterly / annual rhythms.

### Daily
- **06:00 UTC** — eval runs (already chose UTC so Canadian operations work cleanly). ~200-500 questions, FR + EN, ~$1.50-$3/day in Sonnet 4.6 tokens.
- **06:30 UTC** — closed-loop runs. Analyzer reads 5-day window. If safety checks pass and a proposed change exists, A/B test starts at 10% via Coveo's native framework. Slack/Teams alert to the platform team.
- **Continuous** — query observability dashboard refreshes (Grafana Loki ingestion is near-real-time).

### Weekly
- **Bilingual delta review** — DG Digital reviews EN/FR accuracy gap report. Target: parity within 3 percentage points. If a gap appears, it's diagnosed (content silo? prompt? data?).
- **Top-failed-queries review** — Policy team sees what officers asked that RGA couldn't answer. SOPs get updated; eval set expands.
- **A/B test status** — which variants are live, what traffic ratios, projected verdict dates.

### Monthly
- **A/B test verdicts** — what variants reached 100% rollout this month, what got killed, what's still ramping.
- **Cost dashboard** — LLM spend vs budget. Coveo licensing usage. Per-officer-served cost.
- **AIA audit log export** — full month's prompt changes, applies, rollbacks, eval results. Single PDF or markdown report.

### Quarterly
- **Golden set expansion** — Policy team contributes 20-30 new edge cases discovered in production. Coveo FDE reviews and integrates.
- **Roadmap signpost check** — are we on track for the 6/12/24-month milestones? Adjust if not.
- **Coveo Customer Success review** — same as any enterprise SaaS, but informed by the dashboard data not by anecdote.

### Annual
- **AIA assessment renewal** — the closed-loop audit trail + golden set + dashboard + per-prompt history *is* the renewal package. **What used to take 6 weeks of retrospective evidence gathering becomes a 2-day curation exercise.**
- **Procurement review** — Coveo Standing Offer extension if applicable; review BYO-LLM provider choice; review Canadian-region deployment.
- **Roadmap reset** — what's the 24-month from-today picture given everything that's shipped?

---

## 3 · Differentiation sharpening — where this build genuinely beats first-gen RAG

Where it's hard to be precise: the EY engagement details stay confidential. So differentiation needs to be framed against **general industry patterns**, not specific competitor stacks.

### What we have that typical first-gen RAG deployments at federal scale lack

| First-gen pattern | What we built instead |
|---|---|
| "Ship and check manually after complaints" | **Measure every day, apply only when improvement is statistically meaningful** |
| Slack-thread engineering for prompt changes | **Git-versioned prompts with rationale + predicted lift documented** |
| Human notices regression and reverts manually | **Auto-rollback on next-day quality drop — before next day's traffic sees degradation** |
| Retrospective AIA evidence gathering | **Proactive audit — every change is a record from creation** |
| EN-only golden set, "trust the LLM for FR" | **Per-language eval slices, scored side-by-side** |
| Top-intent golden set only | **Three-tier eval (top-intent · multi-source · edge/refusal) — specifically catches long-tail eligibility failures** |
| Full-apply at 100% with human "we'll watch it" | **Native A/B at 10% → 50% → 100% with real-user click signal + auto-kill on signal worse than control** |

### What's the same as first-gen RAG
- Using an LLM for grounded answer generation
- Citing source content
- Retrieval before generation

### What's better than typical first-gen but not unique to Coveo
- Permission-aware retrieval (some vendors have this)
- Per-source crawling/push split (some have this)

### What's truly Coveo-specific (the moat)
- **BYO-LLM** — most pure-play RAG vendors are tied to one LLM provider
- **MCP-ready hosted server** — very few vendors offer this
- **Quebec-City HQ** — sovereignty + procurement preference for Canadian federal
- **Native A/B framework for ML rollout** — Coveo's documented leading practice
- **Security Identities pattern** — early-binding ACL propagation from source systems

---

## 4 · Risk register — honest CIO concerns + mitigations

What a CIO at ESDC would *actually* worry about, not what a vendor pitches around. Frame these honestly in Q&A; pre-empt the top two in the slides themselves.

| # | Risk | Mitigation we can point to | Residual risk |
|---|---|---|---|
| 1 | **Vendor lock-in** — what's our exit plan if Coveo doubles pricing or gets acquired? | Index is exportable · LLM is BYO · closed-loop code is in *our* repo · golden set is *our* IP | Re-implementing the full stack elsewhere is still 6-12 months. Honest answer. |
| 2 | **Data sovereignty** — where does the index live, who can compel disclosure? | Canadian-region deployment available · source content can stay on-prem via Crawling Modules · Coveo HQ in Quebec | Verify cardinality of Canadian-region nodes and SLA contractually. Sovereignty is *positional*, not absolute. |
| 3 | **AIA accountability** — if RGA gives a wrong answer that costs a citizen access, who's liable? | Closed-loop audit trail · per-decision citations · human officer is always in the loop (not citizen-facing in Phase 1) | A citizen *could* still misinterpret an officer-paraphrased answer. The agent layer is the human-in-the-loop. |
| 4 | **LLM cost volatility** — what if Claude pricing 5×s next year? | BYO-LLM means we can switch providers without re-architecture · already using Sonnet 4.6 (cost-efficient) · A/B framework lets us measure cost-quality tradeoffs | Even cheap LLMs aren't free; budget reviews quarterly. |
| 5 | **Operational dependency** — what if the daily cron fails for 5 days? | Existing prompt continues serving (no degradation) · rate-limit guardrail prevents stuck-state · audit log catches the failure | A multi-day cron outage delays improvements but doesn't degrade live service. |
| 6 | **Skills sourcing** — who maintains this after Franck rotates off? | Code-as-source-of-truth · docs · Claude Code skills enable knowledge transfer · Coveo's Customer Success org backs you | Niche skillset (Coveo + closed-loop + LLM-as-judge) limits pool of replacements. Mitigate via documentation depth. |
| 7 | **AI model governance** — Treasury Board Directive on Automated Decision-Making Level 2/3 transparency | The eval framework + closed-loop produces every artifact AIA reviewers need · per-prompt audit trail · citation-based recourse | Federal AI governance is still evolving (2026). Our framework is *ahead* of where current policy sits, which means policy changes might add requirements. |
| 8 | **Crown procurement** — is Coveo on Standing Offer / Supply Arrangement? | **Need to verify before pitch** · Coveo's federal/public-sector posture · Quebec-City HQ is Canadian-content positive | If no SOA exists, longer procurement cycle (possibly competitive bid). Verify by panel day. |
| 9 | **Workforce displacement narrative** — will this replace officers? | **AHT reduction = same officers handle more cases / service standards improve at same headcount.** Not a replacement story. | PSAC (Public Service Alliance of Canada) is unionised. Any displacement framing kills the deal politically. Lead with *officer augmentation*. |
| 10 | **Integration with EI Modernization** — there's already a 5-year transformation underway, won't this collide? | **Adjacency, not collision.** EI Modernization rebuilds the *transactional* core; Coveo sits in the *agent / decision-support* layer alongside it. Same content, different access path. **Means Coveo delivers value DURING the modernization, not after.** | Coordination overhead with Modernization PMO. Stakeholder alignment is real work in months 0-6. |

---

## 5 · Concrete examples / scenarios to weave into the pitch

Where useful, drop a specific scenario rather than abstract benefit-language. Two strong candidates:

### Scenario A — bilingual divergence catch

**Setup**: First-gen RAG deployed at federal scale, EN-only golden set, FR-side accuracy assumed via LLM trust.

**What goes wrong**: A French-language SOP gets updated in Q2. FR-side accuracy silently drops 12 points over 6 weeks. Officers in Québec start escalating cases that EN officers don't. Surfaces eventually via a citizen complaint, traced back via spreadsheet review. **6-week regression window before detection.**

**With our build**: Per-language eval slice catches it the next morning. Auto-rollback if a prompt change caused it; if it's a content issue, the closed-loop analyzer flags it for the policy team. **<24h detection window.**

### Scenario B — long-tail eligibility edge case

**Setup**: An officer takes a call about EI + provincial parental top-up + record-of-employment timing — a known long-tail eligibility case.

**First-gen pattern**: RGA gives a confident but slightly wrong answer. Officer paraphrases it. Citizen receives misinformation. Discovered weeks later when a downstream system flags the case.

**With our build**: Layered eval (15% Tier 3 = edge cases) means this category gets measured daily. If accuracy drops, the closed-loop pauses (rate-limit) and humans review. **Layered eval is the difference between "we average 87% accuracy" and "we know our edge cases sit at 71% and we're actively pushing them up."**

---

## 6 · What to push into specific slides (recommendations)

| Slide (existing) | What to ADD from this brainstorm |
|---|---|
| **Slide 1 — Scale + backdrop + first-gen limits** | Keep current. Possible addition: the "two-thirds of the 28-day claim window already consumed" line is a strong panel quote — already there in speaker notes. |
| **Slide 2 — Coveo answer mapping + 3 CIO differentiators** | Replace generic "RGA + closed-loop quality system" with the explicit ESDC mapping table from Section 1 above (collapsed to 3-4 rows). Push the AIA-ready audit trail story HARDER — that's the differentiator that justifies the buy. |
| **Slide 3 — Value bands + roadmap** | Add an **"AIA renewal at month 12"** milestone (it's the moment the platform pays for itself in compliance work avoided). Consider replacing one of the AHT/ramp-up/resolution bands with a **bilingual-parity band** ("EN/FR accuracy gap < 3pts") — uniquely defensible vs first-gen pattern. |
| **Slide 4 — Why I'd be your FDE + first-30-days** | Make the "I've been inside this customer" anchor more pointed. Specific phrasing: *"I've operated as part of the EY Canada delivery team for ESDC EI on first-generation RAG. I understand the policy surface, the bilingual constraint, and how the officer workflows actually function — not from a deck, from a desk."* That sells short-ramp credibility without naming engagement details. |

### Optional Slide 4.5 / appendix slide — risk register

If the Q&A skews to risk questions, having a one-slide risk-register table (Section 4 above, compressed to 4-5 rows) is useful to *pull up* rather than necessarily *present*. Could live as an appendix in the deck.

---

## 7 · Open questions to discuss with Franck before slide-converting

1. **EY engagement framing** — currently the drafts say "informed pitch, not researched pitch" without naming EY. Section 6 above proposes naming EY explicitly ("I've operated as part of the EY Canada delivery team for ESDC EI"). **Is that the right level of explicitness, or too direct?**

2. **Risk register placement** — should we add a 5th slide / appendix slide with the risk register? Or keep all risks for verbal Q&A? Recommendation: keep verbal, but build an appendix slide as a fallback the panel can ask you to pull up.

3. **Bilingual delivery moments** — should we drop deliberate French phrases in the spoken delivery (e.g., *"en français comme en anglais"*, *"service aux citoyens"*)? Federal CIO panel will notice. Authentic if natural; risky if forced. **Is your spoken FR comfortable enough for 2-3 turns of phrase?**

4. **Competitive framing** — the drafts deliberately don't name competitors. Should we have a *defensive* slide / talking point if a panelist asks "why Coveo over Microsoft Copilot / ServiceNow Knowledge / Salesforce Einstein"? Prepared answer: each is excellent in their lane (M365 productivity, ITSM, CRM), but the **retrieval layer is independent of and complementary to all of them** — Coveo sits in front, they remain downstream.

5. **Officer vs agent terminology** — Service Canada uses both "officer" and "agent" depending on context. With AI-agent overloading the word "agent" now, suggest leaning toward "EI officer" or "Service Canada officer" in the deck. **Confirm preference.**

6. **Confidential-disclosure boundary** — at what point in Q&A do we say "that's from a confidential engagement, happy to speak to the public pattern instead"? Pre-drafting that line as a fallback for 3-4 obvious traps would be useful. (Section 4 Q&A list in `02-customer-pitch.md` has some — should we extend?)

7. **Procurement / Standing Offer verification** — open action: confirm Coveo's federal procurement posture before panel day. Where would we check this? Public Services and Procurement Canada (PSPC) buyandsell.gc.ca?

8. **Citizen-facing rollout timing** — the drafts position citizen-facing in phase 2 (months 12-24). **Realistic given AIA constraints?** Public-facing AI for benefits info is politically sensitive; might want to push to 24-36 mo or keep as "where policy allows."

---

## 8 · Companion-doc cross-reference (for your skim convenience)

Existing docs in the repo that already cover pieces of this story — pull from these rather than re-explain:

| ESDC topic | Existing doc |
|---|---|
| The eval methodology | `docs/rga-eval-methodology.md` |
| Why Passage Retrieval matters for grounding | `docs/passage-retrieval.md` |
| MCP positioning + the BYO-LLM story | `docs/mcp-integration.md` |
| Production query observability | `docs/observability.md` |
| Caching strategy for production scale | `docs/caching-strategy.md` |
| Three-surface platform play | `docs/detail-page.md` |

---

## 9 · Next steps after Franck's review

1. Franck reviews this brainstorm, answers the Section 7 open questions
2. Apply selected insights to `02-customer-pitch.md` (the 4-slide draft)
3. Convert `02-customer-pitch.md` to Marp slides under `presentation/slides/02-customer-pitch.md`
4. Dry-run Topic 2 timing (~5-7 min target)
5. Combined dry-run of Topic 1 + Topic 2 + Q&A within the ~25-min Presentation #1 slot

---

*Brainstorm written 2026-06-05 by Claude (Opus 4.7) at Franck's request — pre-lunch session. Not panel-ready; meant to be refined together.*
