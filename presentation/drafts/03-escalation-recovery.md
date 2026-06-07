# Presentation #2 — Escalation & Recovery

**Source**: Doc 1's Topic 2 — operational scenario, independent of the Pokémon build. The "Senior Director, Technical Customer Success" mention in Doc 1 is a typo — the role is **FDE** everywhere.

**Audience**: Coveo experts + your own executives. You're presenting as the FDE responsible for this hypothetical customer.

**Time budget**: ~25 min total — 10 min slides + 15 min Q&A. **Q&A is the longer half**. Expect intense interaction.

**Format**: slides only, no live demo (this is a hypothetical).

**Total slides**: 10 (excluding cover). Pace = ~60s per slide.

**Working title**: *"When the platform breaks — an FDE's playbook"*

---

## The scenario (from Doc 1, restated)

A large customer's Coveo-powered search platform is **intermittently failing under peak traffic**. The customer is reporting **rapid business impact** — reduced conversion, support escalations, exec-level pressure. You — the FDE — are the first technical responder on Coveo's side.

The deck answers four questions in order:

1. **What's broken, and how do I find out fast?** → root-cause analysis approach
2. **How do I stop the bleeding?** → short-term remediation
3. **What do I tell the customer's execs, and when?** → communications
4. **How does this not happen again?** → prevention

---

## Concrete scenario · "Cyber Monday at Nespresso" (locked 2026-06-06)

> Real Coveo customer · all facts below come from public Coveo case studies + Coveo / Nespresso public co-presentations · framed as a **hypothetical-but-realistic** incident built on verified relationship details.

### Customer + Coveo footprint (public, verified)

| Dimension | Detail |
|---|---|
| **Customer** | **Nespresso** — Nestlé Group premium coffee brand · Coveo customer (global partnership · explicitly named on Coveo's customer roster) |
| **Geo of incident** | **Nespresso ANZ** (Australia + New Zealand) — region with public Coveo co-presentation at ShopTalk 2025 |
| **Key Nespresso public figure** | **YC Eu**, Head of E-Business, Nespresso Oceania (co-presented at ShopTalk 2025 with Coveo's Peter Curran, GM E-commerce). *Reference in speaker notes only, never on slides.* |
| **Working model** | **Weekly check-ins · shared roadmaps · weekly sprints with Coveo team** — co-creation partnership (ClickZ-quoted) |
| **Strategic positioning** | Nespresso ANZ repositioned *"the E in e-commerce from electronic to experiential"* — Coveo powers the experiential search/discovery layer |
| **Adjacent stack (verified)** | Adobe Commerce (Magento) backend in some markets · Salesforce Sales Cloud (Switzerland) · Monetate for product-finder personalization · Contentsquare for behavioral analytics · Nestlé Group AI digital twins on NVIDIA Omniverse |
| **Public KPI benchmark** | Premium brand search conversion lift: typically **3:1 to 9:1 over browse** (Curran, ShopTalk 2025) |
| **Recognition** | Nespresso ANZ shortlisted for **CX Awards 2025 · "Best use of technology to revolutionize CX"** |

### What Coveo specifically powers at Nespresso (the surfaces that will fail)

All four below are publicly documented Coveo capabilities at Nespresso — verified in the ClickZ ShopTalk 2025 article:

1. **Site search** (with real-time zero-result monitoring)
2. **Personalized product recommendations** — driven by interest cohorts + clickstream behavior, re-orders product displays based on intent signals
3. **Content discovery panel** — recipes · sustainability practices · machine care — woven into the search/discovery experience
4. **A/B-tested search placements** for conversion + engagement optimization

> **Note (correction made 2026-06-06)**: an earlier draft mentioned the "Find Your Match" Coffee Quiz. That product (the Coffee Quiz) is publicly documented as **powered by Monetate**, not Coveo ([Retail TouchPoints source](https://www.retailtouchpoints.com/topics/personalization/nespresso-awakens-new-coffee-discovery-pathways-with-online-quiz)). Removed from the mass-failure surfaces to keep the scenario technically accurate.

### The incident (Cyber Monday morning)

| Field | Detail |
|---|---|
| **Date / time** | **Dec 1, 2025 · 9:00 AM AEDT** (Cyber Monday — single biggest gifting day of year for Nespresso) |
| **First page** | YC Eu DMs Coveo's CSM at 7:47 AM AEDT: *"search is degraded — getting reports across our team"* |
| **Mass-failure symptoms** | (a) Site search **p95 latency: 200ms → 4-8s** · (b) **~8% of queries returning errors or 0 results** · (c) Personalized recommendations **regressing to generic** for logged-in users (~75% of traffic) · (d) Content-discovery panel intermittently failing to render recipe/care content · (e) Coveo's real-time zero-result monitoring dashboards firing constantly |
| **Business impact** | Search conversion lift **drops from 3:1 → 0.5:1** (search now WORSE than browsing) · cart abandonment **+40%** · estimated **~$5M AUD revenue at risk over 4 hours of peak** · Cyber Monday paid social campaigns driving traffic INTO the broken experience |
| **Exec pressure** | YC Eu calling Coveo's account team **every 30 minutes** · escalation to Coveo Support Manager + FDE within first hour |
| **The mystery** | Issue started ~7am AEDT (2 hours before peak) · **Nespresso made no recent code deploys** · Coveo platform status page shows *"all systems operational"* · **Coveo ML models retrained overnight** as scheduled · **Coveo Push/Stream API queue from Nespresso's Adobe Commerce backend had a 90-min processing delay Sunday night** before items hit the Coveo Catalog source · query volume **~5-7× normal** (industry benchmark: Cyber Monday drives 512% consumer activity surge per Adobe Analytics 2025) |
| **First-hour clock (FDE perspective)** | T+5min ack · T+15min first exec update · T+1hr first hypothesis applied · T+4hr stabilized · T+24hr public RCA drafted |

### Hypothesis space (for RCA slides)

The mystery has 4-5 plausible competing root causes — enough to drive the deck's hypothesis-ranking content without being trivially solvable:

1. **ML model retrain regression** — overnight retrain produced a model that ranks poorly during Cyber Monday's specific query mix (gifts, machine bundles, capsule pods)
2. **Index push lag colliding with traffic spike** — the 90-min delayed Adobe Commerce index push means stale inventory data + missing seasonal SKUs at peak hour
3. **Cache TTL alignment under high query volume** — classic Black Friday API failure pattern (per Bhagya Rana postmortem)
4. **Query pipeline rule misfire** — a rule shipped Friday for the Cyber Monday campaign is over-boosting unavailable products, creating zero-result fallbacks
5. **Coveo platform sub-region issue** — despite the status page saying "operational," there may be a regional capacity issue (status pages lag actual incidents)

### Hypothesis-to-remediation table (for short-term stabilization slides)

| Hypothesis | Short-term remediation | Time to verify |
|---|---|---|
| ML retrain regression | **Dissociate** ML model from pipeline (returns to baseline relevance) · OR re-import prior pipeline export from git | ~2 min Console action |
| Push/Stream API queue lag | Force re-push catalog data via Coveo Push/Stream API to Catalog source · trigger source refresh | 15 min |
| Cache TTL alignment | Coveo cache warm-up + extended TTL · Nespresso CDN edge throttling | 10 min |
| Query pipeline rule misfire | Revert the rule via Activity Browser (config flip in Console) | ~5 min |
| Coveo platform regional issue | Escalate via Coveo Support hotline (S1, phone) | Depends on Coveo eng |

The FDE doesn't pick one — they parallelize the cheap-to-verify ones FIRST.

### FDE positioning in this scenario

I'm **Coveo's embedded FDE on the Nespresso account** — weekly sprints with their team, know YC Eu's e-business org, know the Adobe-Commerce-to-Coveo push pipeline. When this breaks at 7:47 AM AEDT, **Coveo's Support Manager handles formal case management; I drive the technical decisions and customer-facing technical communication.**

My value vs. a generalist SRE:
- **Speak Coveo platform deeply** — index push behavior, ML retrain timing, query pipeline mechanics
- **Speak Nespresso architecture** — know which CMS backend pushes what, who owns what runbook
- **Trusted relationship** — YC Eu picks up my call instantly because I'm in the weekly sprint cadence

This is the FDE differentiator the deck makes explicit.

### Real-world analogs (for credibility + appendix)

- **[Black Friday API postmortem · Bhagya Rana](https://medium.com/@bhagyarana80/12-post-mortem-lessons-from-api-outages-at-scale-a2153cf70425)** — cache TTL alignment + retry cascade · 36-min MTTR via rate limit + stale-while-revalidate + circuit breaker
- **[Google SRE Shakespeare Search postmortem](https://sre.google/sre-book/example-postmortem/)** — search platform cascading failure under unexpected query (newly-discovered Shakespeare sonnet term not in index) · 66 min outage · 1.21B queries lost
- **[Retail Dive on Black Friday outages](https://www.retaildive.com/news/5-issues-most-likely-to-cause-holiday-e-commerce-outages/540902/)** — Macy's, Lowe's, John Lewis all hit Black Friday outages · industry-typical
- **[New Relic Observability Forecast (retail)](https://finance.yahoo.com/news/relic-report-reveals-retailers-turning-140000838.html)** — median hourly cost of a retail outage: **$1M USD** · median detection time 30 min · median resolution 42 min · **1 in 3 retailers hit critical outages weekly**

### Public sources for the Nespresso scenario (will go into appendix)

| Source | URL |
|---|---|
| Coveo official Nespresso case study | [coveo.com/en/resources/case-studies/nespresso](https://www.coveo.com/en/resources/case-studies/nespresso) |
| Coveo blog: Nespresso B2C e-commerce search | [coveo.com/blog/nespresso-b2c-ecommerce-search](https://www.coveo.com/blog/nespresso-b2c-ecommerce-search/) |
| ClickZ ShopTalk 2025 coverage (YC Eu + Peter Curran) | [clickz.com · How Nespresso Is Rewriting E-Commerce](https://www.clickz.com/how-nespresso-is-rewriting-e-commerce-one-search-bar-at-a-time/271874/) |
| Retail TouchPoints (Coffee Quiz · Monetate-powered, NOT Coveo) | [retailtouchpoints.com · Nespresso online coffee quiz](https://www.retailtouchpoints.com/topics/personalization/nespresso-awakens-new-coffee-discovery-pathways-with-online-quiz) |
| Concentrix · Nespresso AI transformation | [concentrix.com · Nespresso AI](https://www.concentrix.com/insights/case-studies/nespressos-ai-transformation-digital-optimization/) |

### Honest framing for the deck

Cover slide + opening should set **two** expectations upfront:

**1. The scenario is hypothetical:**

> *"Hypothetical incident scenario, anchored in Coveo's publicly-documented partnership with Nespresso (Australia + New Zealand). All facts about the partnership and Coveo's footprint at Nespresso are sourced from public Coveo case studies and Nespresso × Coveo joint presentations. The incident itself is constructed to demonstrate FDE incident-response thinking — to my knowledge, no incident like this has occurred publicly at Nespresso."*

**2. The FDE role I'm depicting bends the official Coveo FDE role:**

> *"Per [Coveo's public FDE job description](https://www.fwddeploy.com/jobs/forward-deployed-engineer-fde-933b1cf2), the Coveo FDE is primarily a **prototype builder + use-case validator**, working with Technical Engagement Managers (TEMs) and Technical Success Architects (TSAs). The deck depicts the FDE as the **first technical responder during a customer incident** — which isn't the canonical FDE role. In Coveo's documented incident process ([docs.coveo.com/en/1489](https://docs.coveo.com/en/1489/)), the **Support Manager formally owns case escalation**. This deck shows how the embedded FDE would plug INTO that machinery and add deep customer-specific technical fluency — not replace the Support Manager's formal role."*

That's defensible AND earns honesty points by acknowledging where the hypothetical extends the actual role.

### The Coveo support machinery — who's who

For accuracy, the full Coveo support cast (so I don't suggest the FDE acts alone):

| Role | Owns |
|---|---|
| **Customer Success Manager (CSM)** | Strategic relationship · contract terms · SLA credit conversations |
| **Coveo Support Manager** | Formal case management · escalation path · customer advocate role per docs.coveo.com/en/1489 |
| **Technical Engagement Manager (TEM)** | Customer architecture during the engagement |
| **Technical Success Architect (TSA)** | Long-term architectural direction for the account |
| **Forward Deployed Engineer (FDE)** | Per public Coveo JD: builds working prototypes · validates new use cases · pushes product boundaries · generates reusable solution patterns |
| **Coveo Product Specialists** | Take ownership of cases under the Support Manager · work with development team if fix needed |

**During an incident in this scenario, the FDE plays an out-of-canon role** as embedded technical lead because:
- Existing customer relationship (the FDE knows Nespresso's stack)
- Already has access to Nespresso's APM (Datadog) and shared Slack Connect
- Technical credibility to act quickly

But the **Support Manager remains the formal IC for case management** — and that's a defensibility detail the deck should not gloss over.

---

## Locked positioning decisions (2026-06-06)

These decisions shape every slide below. **If editing the slides, hold these as constraints.**

### 1. Drop Coveo severity classification as structuring concept

Earlier drafts used Coveo's S1-S4 case-management taxonomy as the deck's spine. **Removed.** The deck structures around five sequential questions:

1. **Symptoms** — what's the customer seeing?
2. **Impact** — what's at stake?
3. **Diagnosis** — what's actually broken?
4. **Response** — what we do
5. **Prevention** — how this doesn't recur

Coveo's internal classification gets a one-line backdrop mention only if useful (e.g., "Coveo's case-management process would classify this as a Complete Loss of Service requiring phone submission · the FDE plugs into that machinery").

### 2. FDE-appropriate communication architecture (not Coveo-inherited)

The FDE role at Coveo is **new** — so the FDE-led incident comms playbook isn't established by inheritance. We **draw from industry best practices** (incident.io, PagerDuty, Atlassian Statuspage, Rootly) and propose an FDE-appropriate architecture that **plugs into** existing Coveo channels rather than re-using them wholesale.

**The architecture (informs Slides 6 + 7)**:

| Audience | Channel | Cadence | Purpose |
|---|---|---|---|
| **Coveo war room** | Internal Slack `#inc-nespresso-cm2025-search` (technical responders only) | Real-time | FDE + Coveo Engineering + Support Manager coordinate diagnosis & remediation |
| **Customer technical team** (Nespresso ANZ) | **Shared Slack Connect channel** (already in place from the weekly sprint cadence) + phone bridge / Zoom war room | Real-time | Tactical updates · joint decisions · the FDE's primary external surface |
| **Customer execs** (YC Eu + her leadership) | **Email + duplicate to shared Slack Connect** | **Every 30 min during hot phase · hourly once stabilizing** | Calibrated status updates · always names the next update time |
| **Coveo internal leadership** | Coveo Slack `#incident-updates` broadcast channel | Every milestone change | Visibility for Coveo's CEO / CRO / CSO without interrupting the war room |
| **Nespresso wider stakeholders** | Customer routes via YC Eu (we don't go around her) | She decides cadence to her org | Single point of contact discipline — feed her, not her org directly |

**The FDE's unique communication advantage**: the shared Slack Connect channel exists *because* of the weekly sprint cadence with Nespresso. A generalist SRE would have to set up new channels mid-incident; the FDE is already in.

**Anti-patterns to avoid explicitly** (industry research):
- Silent gaps >30 min during hot phase (silence breeds executive drive-bys + customer churn)
- Fake ETAs (*"unknown at this time"* + commit to next update time is the trust-builder)
- Split-brain communication (Zoom war room + Slack thread without one source of truth)
- War room staying open after the incident is over

### 3. Keep the written exec note (Slide 7)

Option A locked. The exec note is the panel-defining artifact for the **"Communications to Executives"** brief item — a panelist can read the actual paragraph and judge whether the writer can calibrate under pressure. Concrete > abstract.

The exec note is addressed to **YC Eu (she/her)** — Head of E-Business, Nespresso Oceania — at her 30-min cadence. **She is the customer's gateway**; we don't write to her CMO/COO directly.

### 4. Re-balance the slide budget (per earlier feedback)

The original 10-slide outline was RCA-heavy. Re-balanced:

| Brief item | New slide(s) | Count |
|---|---|---|
| RCA approach | Slide 2 (first hour) + Slide 3 (hypothesis ranking, merges old 3+4) | 2 |
| Short-term remediation | Slide 4 (immediate stabilization) + Slide 5 (verification & handback) | 2 |
| Communications to executives | Slide 6 (architecture + cadence) + Slide 7 (sample exec note) | 2 |
| Prevention | Slide 8 (post-incident actions) + Slide 9 (structural prevention) | 2 |
| Plus Slide 0 (cover) + Slide 1 (the scenario) + Slide 10 (wrap) | | 3 |
| **Total** | | **11** (10 content + cover) |

### 5. Industry comms sources to cite in the appendix

- [incident.io · Incident Communication Best Practices](https://incident.io/blog/incident-communication-best-practices)
- [PagerDuty · Dedicated Incident Channels](https://www.pagerduty.com/blog/insights/why-dedicated-incident-channels-are-the-modern-standard-for-slack-based-incident-response/)
- [Atlassian Statuspage · Incident Communication Best Practices](https://www.atlassian.com/blog/statuspage/incident-communication-best-practices)
- [Rootly · Incident Response Communication](https://rootly.com/incident-response/communication)
- [Runframe · Incident Communication Templates](https://runframe.io/blog/incident-stakeholder-communication-templates)

---

## Operational discipline backbone (referenced from multiple slides)

> *Added 2026-06-06 in response to feedback that the brainstorm under-addressed ticketing, code workflow, internal Coveo coordination, documentation, and backlog management. This section is the operational infrastructure that sits behind every slide.*

### A. Failure-detection signal sources (referenced from Slide 1 + Slide 2)

**YC Eu's 7:47 AEDT DM is the second or third signal, not the first.** A well-instrumented FDE should already be aware. Real-world signal flow for a Cyber Monday incident:

```
T-30min   Nespresso Datadog SLO burn-rate alert fires
          (shared dashboard from weekly sprint cadence)
          ─► alerts Coveo FDE on-call + Nespresso SRE on-call

T-15min   Nespresso customer-support team sees ticket inflow spike
          (search-related complaints)
          ─► posts to Nespresso internal #ops Slack

T-5min    Coveo's zero-result monitoring dashboard breaches threshold
          ─► alerts Coveo FDE + Support Manager

T+0       YC Eu (now alerted by her ops team) DMs Coveo FDE
```

**FDE practice**: I should be in the war room before YC Eu DMs. **If she's the first signal, the monitoring is broken** — that's a Slide 9 structural prevention item.

**Signal sources at Nespresso ANZ specifically**:
- **Nespresso's Datadog** (shared dashboard from sprint cadence) — SLO burn-rate alerts on search-API
- **Nespresso's customer support ticketing** — leading indicator via volume spike
- **Nespresso's internal `#ops-search` Slack** — front-line ops chatter
- **Coveo platform alerts** — zero-result rate, latency p95, error rate
- **Coveo's shared Slack Connect channel with Nespresso** — ground-floor signals from their team
- **PagerDuty / on-call rotation** (Coveo side) — automated paging if SLO breaches

### B. Ticketing infrastructure — Jira (referenced from Slides 2, 4, 8, 9)

**Two Jira instances are in play:**

1. **Nespresso's Jira** — their existing engineering + support ticket system
2. **Coveo's internal Jira** — engineering, support, and product backlogs

**During the incident** (Slides 2-5):

| Ticket | Where | Purpose |
|---|---|---|
| Master incident ticket `NES-INC-2025-CM01` | Nespresso Jira | Single record-of-truth · linked to all child actions · YC Eu and her CMO can subscribe |
| Coveo-side internal ticket `CVO-SUP-NES-CM01` | Coveo Jira (Support project) | Coveo's internal tracking · linked to platform engineering if needed |
| Child tickets per stabilization action (Slide 4) | Both Jiras (linked) | One ticket per parallel track (rule rollback · ML swap · edge throttling) · each has owner + status |
| Verification checklist (Slide 5) | Master ticket subtasks | 3 verification steps as checklist items |

**Post-incident** (Slides 8, 9):

| Ticket | Where | Purpose |
|---|---|---|
| Post-mortem ticket | Both Jiras | Permanent record of timeline · decisions · what we'd do differently |
| Each structural prevention item from Slide 9 | Coveo Jira (FDE project) | One ticket per item · prioritized · ETA assigned · linked back to root post-mortem |
| Nespresso-side action items | Nespresso Jira | What Nespresso commits to fix on their side (e.g., monitoring gaps, change-freeze policy) |
| Internal Coveo "lesson learned" or platform-bug ticket | Coveo Jira (Product or Platform Eng project) | If incident reveals a Coveo platform bug or feature gap |

**Discipline**: every action during the incident gets a ticket BEFORE it gets executed. *No ad-hoc work.* Each ticket has owner, status, ETA, and outcome.

### C. Code workflow — GitHub (referenced from Slides 4, 5, 8)

**Coveo's configuration is code-as-source-of-truth** (verified for our own Pokémon build — `config/`, `scripts/`, `prompts/`). At a real customer like Nespresso, the same discipline applies:

| What lives in GitHub | Where |
|---|---|
| Coveo Query Pipeline rules (YAML / JSON) | Coveo's customer-config repo OR a Nespresso-specific repo · git-versioned |
| ML model configs (training params, retrain schedule) | Same |
| Custom Indexing Pipeline Extensions (IPE Python) | Coveo customer-config repo |
| Coveo MCP server config (if applicable) | Coveo customer-config repo |
| Nespresso's Adobe Commerce frontend code (where search is integrated) | Nespresso's own GitHub |

**During the incident**:

- **Roll back a Query Pipeline rule** = revert a git commit + apply via PR or fast-forward
- **Swap ML model to Friday version** = git tag-based rollback or config flip in versioned config
- **Customer-side fix** (e.g., CDN throttle) = Nespresso's GitHub PR · we sit on the PR review

**Post-incident**:

- Fixes ship as **GitHub PRs** with full context · linked to the Jira ticket · reviewed by Coveo eng + the FDE
- The post-mortem references the PR(s) that resolved the incident
- Long-term prevention items become **GitHub issues** in the relevant repo, linked to backlog Jira tickets

**The FDE's value**: I know which repo each piece of config lives in · I can navigate the rollback in <5 minutes · a generalist SRE would have to ask.

### D. Internal Coveo coordination (referenced from Slides 2, 8)

**Coveo-internal channels during the incident** (in addition to the customer-facing comms architecture):

| Channel | Audience | Used for |
|---|---|---|
| Coveo Slack `#fde-on-call` | FDE org + Coveo Support Manager | First-page channel · who's available · paging |
| Coveo Slack `#inc-nespresso-cm2025-search` | Tight war room · FDE + Coveo Eng + Support Manager | Real-time technical coordination |
| Coveo Slack `#platform-eng` (if needed) | Coveo platform engineering team | If the root cause is a Coveo platform bug, escalate here |
| Coveo Slack `#product-feedback` (post-incident) | Coveo product management | File feature requests / platform-gap feedback that emerged from the incident |
| Coveo Slack `#incident-updates` (broadcast) | Coveo leadership (CEO, CRO, CSO) | Per-milestone visibility · doesn't interrupt the war room |
| Coveo Jira (FDE-internal) | FDE org · Customer Success org | Knowledge management · pattern library across customers |

**Internal feedback loop discipline**: every incident produces at least one entry in `#product-feedback` or the Coveo product Jira backlog if it reveals a platform gap. Examples:

- *"Status page didn't reflect actual incident state for 25 min → product/platform should reduce status-page lag"*
- *"Query Pipeline rules need staging-test mode before production → feature request for Coveo platform"*
- *"FDE wished there was a 'pause auto-retrain' button on ML models → product feature request"*

**The FDE is the eyes and ears of Coveo product team inside the customer.** Internal feedback is part of the deliverable.

### E. Documentation discipline (referenced from Slide 8)

**Three layers of post-incident documentation**:

1. **Customer-specific runbook** (Nespresso ANZ runbook) — owned by the FDE · lives in Coveo's customer-config repo or Confluence · documents the exact stack + integration points + escalation paths · updated after every incident
2. **Coveo FDE pattern library** — owned by the FDE org · cross-customer · captures "Cyber Monday-class incidents," "Friday rule rollback patterns," "ML retrain regression handling," etc. · feeds into onboarding new FDEs
3. **Public RCA for customer's stakeholders** — Slide 8's Action 5 · customer-readable · YC Eu's leadership consumes this

**Tooling**:
- Customer runbook: Markdown in Coveo's customer-config repo (parallel to our Pokémon `docs/` discipline)
- Pattern library: Confluence or Notion in Coveo's FDE org
- Public RCAs: PDF or status-page post on Coveo's customer portal

### F. Backlog management for Slide 9 structural items

**Each Slide 9 structural prevention item becomes a tracked ticket with**:

| Field | Example |
|---|---|
| Title | *"Define + publish Coveo SLO + error-budget for Nespresso ANZ"* |
| Owner | Coveo CSM + FDE (joint) |
| Priority | P1 · blocks next peak |
| ETA | 6 weeks (Q1 2026) |
| Linked tickets | Master post-mortem ticket · Nespresso CSM brief · internal Coveo product ticket if needed |
| Status | Backlog → In Progress → Review → Done |
| Review cadence | Monthly Nespresso + Coveo CSM review · quarterly chaos game day reviews progress |

**The Slide 9 table can show these 5 items as Jira-style tickets, not just bullets**, with priority and ETA visible. That signals to a panel that prevention isn't aspirational — it's planned, owned, and timeboxed.

### G. The FDE's daily tool stack (worth mentioning if asked in Q&A)

| Layer | Tools |
|---|---|
| Communication | Slack (internal · Slack Connect with customer) · email · phone bridge · Zoom for war room when needed |
| Ticketing | Coveo Jira · Nespresso Jira (Slack Connect bridges these) |
| Code | GitHub (Coveo customer-config repo · Nespresso's own repos) |
| Observability | Coveo Admin Console · Nespresso's Datadog (shared) · Grafana boards · Coveo platform status page |
| Documentation | Markdown in repos · Confluence / Notion for FDE pattern library |
| On-call | PagerDuty (Coveo side) |

A panelist asking *"how do you actually work day-to-day"* should hear a concrete answer with named tools, not abstractions.

### H. Sources for these patterns

- Coveo's documented Case management process — [docs.coveo.com/en/1489](https://docs.coveo.com/en/1489/)
- Industry incident response tooling synthesized from earlier research (incident.io · PagerDuty · Rootly)
- "Code-as-source-of-truth" pattern from our own Pokémon Challenge build (`config/`, `scripts/`, `prompts/`)

---

## Self-reflection · research-driven additions (2026-06-06)

> *Added in response to feedback that the brainstorm should be pressure-tested against industry best practices. Each section below addresses a gap identified in the audit + cites the source research.*

### I. Incident Commander (IC) role — the FDE IS the IC

**The deck must explicitly name the FDE as the Incident Commander** during this incident. Research (Google SRE · Rootly · Coralogix · Xurrent) consistently emphasizes: **the IC is the single decision authority**, NOT the engineer debugging the code.

**The 5 C's of incident command** (apply throughout the deck):
- **Command** — establish authority and direction (single decision-maker)
- **Control** — keep the response structured and focused
- **Coordination** — align multiple teams (Coveo · Nespresso · Adobe Commerce vendor if needed)
- **Communication** — keep everyone informed
- **Collaboration** — foster teamwork to resolve efficiently

**Critical anti-pattern**: the engineer closest to the broken system should NOT be the IC. Why: they end up debugging the failure, paging in subject-matter experts, AND fielding *"what's the status?"* from leadership all at once. **All three jobs slow down when one person juggles them.** The FDE is uniquely positioned to be the IC precisely because the embedded relationship gives technical credibility + customer-facing skill without requiring me to be the bottom-of-stack engineer.

**IC's decision authority during incidents** (Google SRE quote): *"The incident commander outranks the CEO when you have an incident."* During the active phase, my call goes.

**IC's primary responsibility**: maintain a **living incident document** with timestamp, actor, action, expected effect, observed result, link to evidence. This becomes the source for the post-incident review.

**Source**: [Google SRE · Managing Incidents](https://sre.google/sre-book/managing-incidents/) · [Rootly · Incident Commander Guide](https://rootly.com/incident-response/incident-commander) · [Coralogix · What Is an Incident Commander](https://coralogix.com/blog/incident-commander/)

### J. War room facilitation rules (apply to Slide 2 + 6 speaker notes)

| Rule | Why |
|---|---|
| Channel naming: `#inc-YYMMDD-description` | Searchability · post-mortem reconstruction · `#inc-251201-nespresso-search` for this scenario |
| Pinned message at top: severity · affected services · current hypothesis · next actions · key metrics | New responders load context in seconds without re-asking |
| Scribe role — owns the incident timeline document | Frees IC + technical responders to focus on their jobs |
| Mitigation BEFORE RCA — Google SRE doctrine | *"Customers don't care whether or not you fully understand the cause; they want to stop receiving errors"* — bias toward reversible action |
| Document decision rationale — *"Rolled back X because Y, even though we weren't 100% sure"* | Post-mortem context · audit trail · accountability |
| Conference call for decisions · Slack for the ledger | Voice is faster for decisions · Slack captures the record |
| Single conference call number for ALL incidents (Google pattern) | No "which call were they on?" confusion |

**Source**: [Google SRE · Managing Incidents](https://sre.google/sre-book/managing-incidents/) · [Upstat · War Room Protocols](https://upstat.io/blog/war-room-protocols)

### K. Multi-vendor coordination (Adobe Commerce + Monetate + Contentsquare seams)

**Nespresso's stack has shared-responsibility seams** with multiple vendors. If the incident's root cause sits at one of those seams, coordination becomes a major issue.

**Vendor responsibility map** (publicly documented from Adobe Commerce shared-responsibility doc):

| Layer | Owner | Responsibility |
|---|---|---|
| Coveo platform (search, recs, content discovery, RGA) | **Coveo** | Coveo handles platform availability + core code · Coveo-side patches |
| Adobe Commerce (Magento backend · product catalog · index push source) | **Adobe + Nespresso** | Adobe maintains infrastructure · Nespresso owns custom extensions, security incidents on their side, custom integrations |
| Monetate (Coffee Quiz · product-finder) | **Monetate + Nespresso** | Monetate maintains their service · Nespresso owns the integration |
| Contentsquare (behavioral analytics) | **Contentsquare + Nespresso** | Vendor maintains the platform · Nespresso owns the integration |
| Nespresso frontend (Cyber Monday campaign · CDN config · custom Magento extensions) | **Nespresso** | Their code, their responsibility |

**Handling vendor-seam incidents**:
1. **Notify the vendor's incident channel immediately** — Adobe Commerce, Monetate, Contentsquare each have their own SaaS incident response process. Their status pages should be the first check (often faster than questioning telemetry).
2. **Single internal point of contact** — the FDE owns the Coveo-side coordination; Nespresso's tech lead owns vendor relationships on their side.
3. **Joint runbook** for each vendor seam — written in advance, lives in Nespresso's runbook repo (we should make this a Slide 9 structural item).
4. **SLA contract review** — different vendors have different SLA mechanics; the FDE needs to know who owes credits if the multi-vendor seam was the issue.

**Source**: [Adobe Commerce · Shared Responsibility Security and Operational Model](https://experienceleague.adobe.com/en/docs/commerce-operations/security-and-compliance/shared-responsibility) · [Panorays · Third-Party Incident Response](https://panorays.com/blog/third-party-incident-response/) · [PagerDuty · Managing Vendor Incidents](https://www.pagerduty.com/blog/incident-management-response/managing-vendor-incidents/)

### L. Time-zone handoff — the 16-hour Nespresso ANZ ↔ Coveo Montréal challenge

**This is potentially the biggest under-addressed risk in the scenario.**

**The math**:
- Nespresso ANZ (AEDT) is UTC+11
- Coveo Montréal HQ (EST) is UTC-5
- **Offset: 16 hours**

**The implications during a 4-hour Cyber Monday incident**:
- 7:47 AM AEDT Monday Dec 1 = **3:47 PM EST Sunday Nov 30** in Montréal
- 11:00 AM AEDT (stabilization target) = 7:00 PM EST Sunday in Montréal
- 7:00 PM AEDT (Nespresso end-of-day) = 3:00 AM EST Monday Dec 1 in Montréal

**If the incident persists into Nespresso's evening**, the FDE in Australia goes to bed and someone else has to pick up the war room. **This is a follow-the-sun handoff problem.**

**Handoff requirements** (from incident.io and Rootly research):

1. **Structured handoff artifact** — pinned in war room: incident summary · current hypothesis · actions taken · what's been verified · what's still unknown · next planned action · escalation contacts
2. **Verbal handoff with explicit transfer of IC role** — Google SRE: *"You're now the incident commander, okay?"* and don't hang up until firm acknowledgment
3. **Pre-positioned regional FDE on-call** — if Coveo has an APAC-based FDE or an EMEA-based FDE who can take the handoff before Australian end-of-day
4. **Conference call recording** — every war-room call is recorded so the new IC can reconstruct what they missed

**Anti-pattern**: midnight handoffs to a region with fewer staff available — that's exactly what happens at Nespresso ANZ evening if Coveo only has Montréal-based FDEs.

**Structural implication for Slide 9**: 24/7 FDE rotation must include **regional coverage** (APAC + EMEA + Americas), not just "more FDEs in Montréal." This is the real meaning of "follow-the-sun" for an FDE org serving global customers.

**Source**: [Rootly · Distributed and Global On-Call Best Practices](https://rootly.com/blog/distributed-and-global-on-call-best-practices-for-24-7-teams) · [incident.io · On-Call Best Practices](https://incident.io/blog/on-call-best-practices-guide-2026) · [SRE School · Follow the Sun](https://sreschool.com/blog/follow-the-sun/)

### M. SLA credits and contractual remedies

**Coveo Care has contractual SLA obligations.** If SLAs are breached during an incident, Coveo may owe Nespresso credits.

**What the FDE needs to know**:
- **What's Nespresso's SLA tier?** (Coveo Care Pro vs Enterprise · different commitments)
- **What's the breach threshold?** (e.g., "99.9% uptime monthly" — needs to be quantified)
- **Who calculates and applies credits?** (Coveo CSM + finance · not the FDE)
- **When is credit conversation appropriate?** — NOT during the incident · in the post-incident phase only

**The FDE should NEVER promise credits or refunds during the incident**. That conversation belongs to the Coveo CSM and Nespresso's procurement team during contract review.

**Slide 8 (post-incident actions)** should add: *"Coveo CSM reviews SLA breach calculation with Nespresso's procurement team — credits applied per Coveo Care contract terms"* as a quiet line item, not foregrounded.

### N. Public RCA discipline (the Cloudflare model)

Industry's best public-RCA practitioners (Cloudflare, GitLab, Stripe) follow this discipline:

1. **Don't rush the RCA** — accuracy over speed. *"It is very difficult to pin this down to a specific number of days, as we want to be thorough."*
2. **Management review BEFORE publishing** — content + commitments + professional presentation
3. **Audience-segmented delivery** — via status page to affected subscribers only · don't over-communicate to unaffected customers (creates unnecessary worry)
4. **Public RCA is a TRUST INVESTMENT, not a compliance checkbox** — Cloudflare's stated philosophy: *"openness and transparency are intrinsic to the delivery of our service"*

**For Nespresso specifically**: the public RCA goes to YC Eu (she controls Nespresso-side distribution to her CMO/COO/CEO). Coveo's external RCA might go to Coveo's status page subscribers if multi-customer impact emerged.

**Source**: [Cloudflare · Customer Incident Management Policy](https://developers.cloudflare.com/support/customer-incident-management-policy/)

### O. What I'm leaving out of slides (Q&A material only)

These gaps are real but don't need slide treatment — they belong in Q&A:

- **Press / PR considerations** — if Nespresso/Nestlé public traded entity gets press attention, Coveo's PR + Nespresso's PR coordinate; the FDE doesn't talk to press
- **Legal involvement** — GDPR, privacy law during incident response — Coveo legal owns
- **Cognitive load / FDE burnout management** — addressed by FDE rotation (Slide 9)
- **What if customer's ops team is junior / overwhelmed** — the FDE adjusts the role split, takes more of the IC burden

These can be answered if asked but don't earn slide real estate.

### P. Updated source list (industry best practices for IC + war room + multi-vendor + time zone)

- [Google SRE Book · Managing Incidents](https://sre.google/sre-book/managing-incidents/)
- [Rootly · Incident Commander Guide](https://rootly.com/incident-response/incident-commander)
- [Coralogix · What Is an Incident Commander](https://coralogix.com/blog/incident-commander/)
- [Upstat · War Room Protocols](https://upstat.io/blog/war-room-protocols)
- [Adobe Commerce · Shared Responsibility Security Model](https://experienceleague.adobe.com/en/docs/commerce-operations/security-and-compliance/shared-responsibility)
- [Panorays · Third-Party Incident Response](https://panorays.com/blog/third-party-incident-response/)
- [PagerDuty · Managing Vendor Incidents](https://www.pagerduty.com/blog/incident-management-response/managing-vendor-incidents/)
- [Rootly · Distributed and Global On-Call Best Practices](https://rootly.com/blog/distributed-and-global-on-call-best-practices-for-24-7-teams)
- [incident.io · On-Call Best Practices 2026](https://incident.io/blog/on-call-best-practices-guide-2026)
- [SRE School · Follow the Sun](https://sreschool.com/blog/follow-the-sun/)
- [Cloudflare · Customer Incident Management Policy](https://developers.cloudflare.com/support/customer-incident-management-policy/)

---

## Technical-accuracy review (2026-06-06 · second-round audit)

> *Pressure-tested the Coveo-specific claims in the brainstorm against Coveo's actual documentation. Surfaced 6 corrections / clarifications. Applied as surgical edits to affected slides.*

### Q. ML model rollback — there is NO single-button rollback

**Reality** ([Coveo docs](https://docs.coveo.com/en/2816/), [Inspect ML Models](https://docs.coveo.com/en/mc2g0297/)):
- Coveo does NOT provide a "swap to previous model" button.
- The documented rollback patterns are:
  1. **Dissociate the model** from the query pipeline → returns to baseline relevance (no ML personalization). Fast action via Console.
  2. **A/B test the prior model** → split traffic to compare new vs. previous. Coveo's *leading practice* for any ML change.
  3. **Re-import a previous pipeline export** → if you've exported pipeline configurations as code (best practice), you can re-apply a known-good version.

**Implication for our Slide 4 Track B**: Don't claim "swap to Friday model in 5 min." Use the documented patterns:
- **"Dissociate the Sunday-retrained model from the production pipeline — instant fallback to baseline relevance · ~2 min Console action"**
- Or **"Re-import the previously-exported pipeline config from before Sunday's retrain · ~5 min if config is versioned in git"**

This is more accurate AND demonstrates I know Coveo's actual operational primitives.

### R. Adobe Commerce + Coveo integration — Push/Stream API, not native connector

**Reality** ([Coveo Indexing Pipeline docs](https://docs.coveo.com/en/1893/index-content/coveo-indexing-pipeline), [Coveo for Adobe](https://docs.coveo.com/en/m9fe0471/)):
- **"Coveo for Adobe"** documentation focuses on **Adobe Experience Manager (AEM)**, NOT Adobe Commerce / Magento.
- Adobe Commerce → Coveo integration uses **Coveo Push API or Stream API** to deliver catalog data into a **Coveo Catalog source**.
- Object types: `Product`, `Variant`, `Availability` (per [Coveo Catalog object types](https://docs.coveo.com/en/o57a0186/)).
- The integration pattern is similar to **commercetools** or **SAP Commerce Cloud** integrations — push-based, custom-coded, not a turn-key connector.

**Implication for Slide 1, 2, 4**: When mentioning "index push from Adobe Commerce backend," frame it more precisely:
- **"Push/Stream API delivering Nespresso's Adobe Commerce catalog data to a Coveo Catalog source"**
- The 90-min delay claim becomes: **"the Push API queue from Nespresso's Adobe Commerce backend was lagging — 90-min processing delay before items hit the Coveo index"**

### S. Coveo Care SLA specifics — soften citations

**Reality** ([Coveo Care plans](https://docs.coveo.com/en/1484/), [Coveo Care Guide](https://docs.coveo.com/en/1352/)):
- Public docs confirm Pro vs Enterprise tiers exist with different response-time commitments.
- Specific response-time numbers per severity tier are NOT published in publicly-accessible docs — they're in the customer-side contract.
- Enterprise tier includes Delivery Assurance services (which is where the FDE role sits).

**Implication**: Avoid claiming specific SLA hours (e.g., "Coveo guarantees 15-min response for S1"). Instead, frame as:
- **"Coveo Care Enterprise's published response-time commitments for our severity tier"** — without naming hours
- Or **"per the SLA terms in Nespresso's Coveo Care contract"** — pointer not claim

### T. "Real-time zero-result monitoring" — clarify origin

**Reality**: The [ClickZ ShopTalk 2025 article](https://www.clickz.com/how-nespresso-is-rewriting-e-commerce-one-search-bar-at-a-time/271874/) explicitly mentions Nespresso has "zero-result monitoring to patch search failures in real time" — but this is **not a documented Coveo platform feature**. It's almost certainly a **custom dashboard the Nespresso team built on top of Coveo Analytics data** (Coveo provides the analytics; Nespresso built the real-time alerting layer).

**Implication for Slide 1**: Reframe as:
- **"Nespresso's real-time zero-result monitoring dashboard (built on Coveo Analytics) firing constantly"**
- This is more accurate and signals I know which layer of the stack owns what.

### U. Revenue impact — anchor to industry benchmark, not specific AUD

**Reality**:
- The $5M AUD over 4 hours figure is napkin math · not verifiable from public sources for Nespresso ANZ specifically.
- **Industry benchmark**: [New Relic Observability Forecast for Retail](https://finance.yahoo.com/news/relic-report-reveals-retailers-turning-140000838.html) — median hourly cost of a critical retail outage = **$1M USD** (~$1.5M AUD).
- For a 4-hour Cyber Monday peak window at a premium DTC retailer: $4M-$6M AUD range is defensible WITH the benchmark cited.

**Implication for Slide 1**: Reframe as:
- **"~$4M-$6M AUD revenue at risk over the 4-hour peak (industry benchmark: median retail outage = $1M USD/hour per New Relic 2024)"**

### V. Cyber Monday traffic multiplier — actually MORE dramatic than I claimed

**Reality** ([Adobe Analytics 2025 Cyber Monday data](https://news.adobe.com/news/2026/01/adobe-holiday-shopping-season), [Digital Commerce 360](https://www.digitalcommerce360.com/article/cyber-monday-online-sales/)):
- **US consumer activity surges 512% on Cyber Monday vs. average day**
- **Peak velocity reaches $16M in online sales per minute (8-10pm EST)**
- **AI-driven traffic from chatbots up 670% YoY in 2025**
- Cyber Monday 2025 total US online: **$14.25B**

**Implication for Slide 1**: Reframe traffic multiplier:
- **"Query volume ~5-7× normal during peak hour (industry benchmark: 512% consumer activity surge on Cyber Monday · Adobe Analytics 2025)"** — was "3.5× normal" which was too conservative.

### W. Coveo's actual debugging toolkit (add to Slide 2 RCA playbook)

**Reality** ([Coveo Inspect ML Models](https://docs.coveo.com/en/mc2g0297/), [Troubleshoot query pipeline rules](https://docs.coveo.com/en/2088/), [Manage query pipelines · Activity log](https://docs.coveo.com/en/1791/)):

| Tool | What it does | When to use |
|---|---|---|
| **Activity Browser** | Audit log of all pipeline + ML changes · who shipped what, when | Slide 2 Check #1 (already mentioned) · also for tracking the Friday rule change |
| **Execution report** (via `&debug=true` URL param) | Per-query debugging · expand `executionReport.children` to see the whole path the query took | Slide 2 Check #3 (deep-debug a specific failing query) |
| **Inspect ML Models page** | Live ML model debugging · per-query model behavior | Slide 2 Check #4 (verify Sunday retrain regression) |
| **Review model information page** | ML model status · errors · limitations · archived models | Slide 2 Check #3 (auxiliary) |
| **Query pipeline export/import** | Versioned pipeline configurations · enables rollback | Slide 4 Track B (re-import previous export) |

**Implication for Slide 2**: Add Coveo's actual toolset by name in the speaker notes — signals deep platform knowledge.

### X. Updated source list (technical accuracy)

- [Coveo · Inspect ML Models (debug)](https://docs.coveo.com/en/mc2g0297/)
- [Coveo · Review model information](https://docs.coveo.com/en/1894/)
- [Coveo · Manage model associations with query pipelines (A/B + dissociate)](https://docs.coveo.com/en/2816/)
- [Coveo · ML Overview + retraining](https://docs.coveo.com/en/1727/)
- [Coveo · ML FAQ (retrain frequency)](https://docs.coveo.com/en/1803/)
- [Coveo · Manage query pipelines (activity log + export/import)](https://docs.coveo.com/en/1791/)
- [Coveo · Troubleshoot query pipeline rules](https://docs.coveo.com/en/2088/)
- [Coveo · Indexing Pipeline (Push API + Stream API + Catalog source)](https://docs.coveo.com/en/1893/index-content/coveo-indexing-pipeline)
- [Coveo · Catalog object types (Product, Variant, Availability)](https://docs.coveo.com/en/o57a0186/)
- [Coveo Care Plans · Pro vs Enterprise](https://docs.coveo.com/en/1484/)
- [Adobe Analytics 2025 Cyber Monday report (via news.adobe.com)](https://news.adobe.com/news/2026/01/adobe-holiday-shopping-season)
- [Digital Commerce 360 · Cyber Monday 2025 online sales](https://www.digitalcommerce360.com/article/cyber-monday-online-sales/)
- [New Relic Observability Forecast (retail outage cost)](https://finance.yahoo.com/news/relic-report-reveals-retailers-turning-140000838.html)

---

## Additional Coveo platform tooling discovery (third-round audit · 2026-06-06)

> *Deeper exploration of docs.coveo.com surfaced significant operational tooling we hadn't covered. These add real depth to the FDE's diagnostic + remediation + prevention toolkit, and create a powerful bridge from the Topic 1 Pokémon build to this presentation.*

### Y. Coveo CLI — the FDE's operational backbone

**This is a major bridge from Topic 1.** Coveo has a full-featured CLI ([docs.coveo.com/en/cli](https://docs.coveo.com/en/cli/)) that **enables exactly the code-as-source-of-truth discipline we demonstrated in the Pokémon build**.

**Key CLI capabilities relevant to the incident scenario**:

| Command | What it does | When the FDE uses it |
|---|---|---|
| `coveo auth:login` | Connects to a Coveo organization | First step of every operational session |
| `coveo org:resources:push` | Pushes resources (Query Pipelines · ML model configs · IPE Python · sources · etc.) from local files to a Coveo org | **Apply a fix as code** · the inverse of `:pull` |
| `coveo org:resources:pull` | Pulls resources from a Coveo org to local files | **Snapshot current state for rollback** before making changes |
| `coveo ui:deploy -p <HOSTED_PAGE_ID>` | Updates a hosted search page on the Coveo Platform | Roll out a UI fix |
| **Snapshot models** | JSON file targeting specific resource IDs · enables selective pull/push | Surgical config changes (rollback ONE rule without touching others) |
| **CI/CD pipeline integration** | GitHub Actions pattern for daily backups · automated deployment | Continuous infrastructure-as-code · audit trail |

**Implication for incident response**:
- **Pre-incident**: nightly `coveo org:resources:pull` to git keeps a known-good snapshot — *automatic rollback baseline*
- **Mid-incident**: `coveo org:resources:push` re-applies a known-good config in seconds (faster than Console clicks)
- **Post-incident**: every fix is a git commit + a CLI push — full audit trail · diff-reviewable PR · linked to the Jira ticket

**This is the EXACT pattern we shipped for the Pokémon build** (`config/`, `scripts/`, `bootstrap.sh`). The FDE's value at Nespresso would be establishing this discipline if it's not already there. **Direct bridge from Topic 1.**

**Source**: [Coveo CLI · Command-line interface](https://docs.coveo.com/en/cli/) · [Coveo CLI · Usage](https://docs.coveo.com/en/nake8092/) · [Coveo CLI · CI/CD pipeline](https://docs.coveo.com/en/mbmc0091/) · [Coveo CLI · Manage organization snapshots](https://docs.coveo.com/en/mape0408/)

### Z. Sandbox organizations — where fixes get tested

**Critical gap I missed**: Coveo provides **sandbox organizations** ([docs.coveo.com/en/2959](https://docs.coveo.com/en/2959/)) as permanent test environments paired with each production org.

**Key facts**:
- Sandbox is a **permanent test organization that comes with your production organization** (not a feature you have to buy separately)
- Most customers have **1-2 sandboxes** (often: 1 dev + 1 QA/UAT)
- Coveo releases new platform features to sandboxes **BEFORE production** — so sandboxes also serve as early-warning for platform changes
- *"Good practice to keep your sandbox as similar as possible to your production organization"*

**Why this matters for our scenario**:
- **Slide 4 (Stabilization)**: before applying the dissociate-ML-model fix to Nespresso's production org, the FDE can **test in the Nespresso sandbox first** — assuming sandbox is current, this takes 5-10 min but prevents a fix that makes things worse
- **Slide 5 (Verification)**: load test on the Nespresso sandbox to confirm fix holds under Cyber Monday-class traffic
- **Slide 9 (Structural prevention)**: "**Keep Nespresso sandbox synchronized with production**" becomes a backlog ticket · the sandbox is only useful if it mirrors production
- **Slide 8 (Post-incident)**: deploy fix to sandbox → verify → deploy to production · via Coveo CLI snapshot push

**Critical Updates mechanism** ([docs.coveo.com/en/2957](https://docs.coveo.com/en/2957/)): Coveo's official way to test platform changes — activate in sandbox first → monitor in Activity Browser + Log Browser → then activate in production. This is the platform-change discipline.

### AA. Relevance Inspector — the FDE's per-query deep-debug tool

**A more powerful diagnostic than `&debug=true`**: [Relevance Inspector](https://docs.coveo.com/en/mbad0273/) is a dedicated Admin Console page.

**How the FDE uses it during the incident**:
1. Find a failing query in Nespresso's APM traces (e.g., a 0-result query for "vertuo gift set")
2. Get the **`searchUid` or `responseId`** from the failing query (visible in browser dev tools · Network tab)
3. Open Relevance Inspector · paste searchUid · click Inspect
4. See: **query journey** with expandable steps · query params **before AND after** pipeline · which pipeline routed · all ranking expressions applied

**This is the deep-debug tool**. The execution report (`&debug=true`) gives in-page debugging; Relevance Inspector gives historical query-by-query inspection after the fact — critical for post-incident forensics.

**Implication for Slide 2 (RCA)**: add Relevance Inspector to the toolkit.

### BB. Data Health Monitoring + Log Browser — operational observability

Two more Coveo platform tools I hadn't surfaced:

**Data Health Monitoring** ([docs.coveo.com/en/m44f6381](https://docs.coveo.com/en/m44f6381/))
- Admin Console page with **Overview** + **Event browser** tabs
- **Overview**: data validation breakdown by syntax rules / commerce rules / etc. · severity levels · impacted event counts
- **Event browser**: tracks the latest events sent to Coveo · filter by status
- **Why this matters**: could detect the Push/Stream API queue lag in our scenario as data integrity errors (events arriving late or malformed)

**Log Browser** (separate from Activity Browser):
- Source-level logs with response body and headers when failures occur
- Configurable via `LogResponseBodyWhenUnsuccessful` and `LogResponseHeadersWhenUnsuccessful` parameters
- Direct diagnostic for source-side incidents (e.g., the Adobe Commerce push pipeline failing)

**Implication for Slide 2**: add Data Health + Log Browser to the diagnostic checklist.

### CC. The complete diagnostic toolkit (consolidated from rounds 2 + 3)

The FDE's actual Coveo platform diagnostic toolkit (for Slide 2 speaker notes):

| Layer | Tool | What it shows |
|---|---|---|
| Platform health | **Watchtower section** (Console home) + **Coveo Status page** | Coveo-side issues at platform level |
| Source-level | **Log Browser** + source LogResponseBody* params | Push/Stream API failures · source push errors · headers + bodies |
| Data integrity | **Data Health page** (Overview + Event browser) | Analytics events: validation errors, integrity issues, late events |
| Resource audit | **Activity Browser** | Who changed what · query pipelines · ML models · sources |
| ML behavior | **Inspect ML Models** + **Review Model Information** | Live model behavior · status · errors · limitations |
| Per-query forensics | **Relevance Inspector** + **`&debug=true` URL param** | Single-query journey · before/after pipeline · ranking applied |
| Search Hub routing | Search Hub config · pipeline associations | Which pipeline serves which interface |
| Programmatic ops | **Coveo CLI** | Apply fixes as code · snapshot rollback · CI/CD integration |
| Test environment | **Sandbox organization** | Safely test fixes before production |

**This is a serious operational toolkit.** The FDE who knows all of these by name signals deep platform fluency to the panel.

### DD. Implications for the slides + structural prevention

**Updates needed**:

| Slide | Addition |
|---|---|
| **Slide 2 (RCA playbook)** | Add Relevance Inspector, Log Browser, Data Health to Check #3 (deep-debug) and Check #5 (source-side) |
| **Slide 4 (Stabilization)** | Add a "Test in sandbox first" gate · "Apply via Coveo CLI snapshot push" pattern |
| **Slide 5 (Verification)** | "Load test on Nespresso sandbox" as part of verification |
| **Slide 8 (Post-incident)** | "Snapshot the post-fix Coveo org state to git via CLI" as Action 7 (or fold into Action 2 runbook) |
| **Slide 9 (Structural prevention)** | Add as Item 6: **Sandbox synchronization discipline** — keep Nespresso's sandbox current with production · CLI-driven daily snapshot |

### EE. The strongest bridge from Topic 1 to Topic 2

**This is the powerful narrative the deck can now make**:

> *"For the Pokémon Challenge, I established code-as-source-of-truth — bash scripts, idempotent operations, audit logs, daily evals, closed-loop apply via API. Coveo's own platform provides exactly this discipline at scale: the Coveo CLI for resource snapshot management, sandbox organizations for safe testing, Critical Updates mechanism for platform-change discipline, and snapshots committed to git for full audit trail. **The Pokémon build was me practicing on a small index what Coveo's platform supports at enterprise scale.**"*

That's a panel-defining moment.

### FF. Updated sources from this round

- [Coveo CLI · main page](https://docs.coveo.com/en/cli/)
- [Coveo CLI · Usage](https://docs.coveo.com/en/nake8092/)
- [Coveo CLI · CI/CD pipeline](https://docs.coveo.com/en/mbmc0091/)
- [Coveo CLI · Manage organization snapshots](https://docs.coveo.com/en/mape0408/)
- [Coveo CLI · Deploy your project](https://docs.coveo.com/en/atomic/latest/usage/manage-project/cli-deploy/)
- [Coveo · About non-production organizations (Sandbox)](https://docs.coveo.com/en/2959/)
- [Coveo · Apply critical updates](https://docs.coveo.com/en/2957/)
- [Coveo · Relevance Inspector](https://docs.coveo.com/en/mbad0273/)
- [Coveo · Enable debug information in REST queries](https://docs.coveo.com/en/406/)
- [Coveo · Inspect your query pipeline and rules](https://docs.coveo.com/en/mc2g0358/)
- [Coveo · Data Health Monitoring](https://docs.coveo.com/en/m44f6381/)
- [Coveo · Data Health Overview](https://docs.coveo.com/en/n3re0517/)
- [Coveo · Event browser](https://docs.coveo.com/en/n3re0108/)
- [Coveo · System issue notifications (Watchtower)](https://docs.coveo.com/en/1684/)
- [Coveo · REST API source troubleshooting (Log Browser config)](https://docs.coveo.com/en/o5nb2216/)
- [Coveo · Troubleshoot query error codes](https://docs.coveo.com/en/1471/)

---

## Research foundation · Coveo's official playbook + industry SRE patterns

> *Added 2026-06-05. Researched Coveo's documented escalation process + 2026 industry best practices for production AI / search platform incident response. The slides below should ground their claims in this section.*

### A. Coveo's formal escalation process (docs.coveo.com/en/1489)

Coveo has a **publicly documented case escalation process** under the Coveo Care framework. Key mechanics (cite when describing how the FDE plugs into Coveo's machinery):

- **Severity Levels 1-4** classify all cases. **Severity 4 is NOT eligible for escalation** — only S1-S3 qualify.
- **Severity 1 incidents require phone-call submission** (not just web form) to trigger the Initial Response Time SLA.
- **Escalation request channels**: customer calls the Coveo Support hotline (region-specific) OR logs into Coveo Connect, opens the case, clicks "Request an escalation," fills justification form.
- **Standard process gets time first** — escalations only granted after the regular resolution process has had a reasonable window to produce a fix or workaround.
- **Once accepted**, a **Coveo Support Manager** is assigned as **"customer advocate within Coveo"**. Their job: understand business impact, document scope, establish a resolution path with the customer, set expectations, involve management as needed.
- **Customer obligations**: customer commits internal resources to assist with resolution. Failure to provide resources can trigger **de-escalation**.
- **Status visibility**: backend statuses track escalation progression; Support Manager communicates updates at customer-agreed cadence.
- **Case auto-close**: 2 follow-up attempts over 4 business days; no response → automatic closure. **Reopen window: 30 days.**

**Source**: [Case management process · docs.coveo.com/en/1489](https://docs.coveo.com/en/1489/) · [Coveo Care · Customer Support and Success Guide · docs.coveo.com/en/1352](https://docs.coveo.com/en/1352/)

### B. Coveo's own AI-augmented support operations (worth referencing)

Coveo partnered with **SupportLogic** for AI-driven case routing + escalation prediction. Documented outcomes within 6 months:
- **−53% MTTR** (Mean Time To Resolution)
- **+31% First Day Resolution rate**
- **−56% escalation requests**

SupportLogic monitors live cases for "pre-escalation" signals via **sentiment score · attention score · inactivity**, flagging cases that need proactive intervention before the customer asks for a manager. Worth namedropping: Coveo applies ML to its own support ops at the same rigor it sells.

**Source**: [SupportLogic Coveo case study](https://www.supportlogic.com/resources/case-studies/coveo-slashes-case-resolution-time-with-intelligent-routing/)

### C. The Coveo Care framework (the support contract surface)

Coveo Care is the umbrella covering everything Coveo provides post-sale:
- **Coveo Support** — case management, severity-tiered SLAs, escalation path
- **Customer Success Manager (CSM)** — strategic relationship owner. **CSM hours are PLANNED, not committed; unused hours don't roll over month-to-month** (an important contract detail for the customer-facing conversation)
- **Delivery Assurance services** — proactive guidance; the FDE typically operates under this banner
- **Coveo Connect Community** — the customer-facing portal for case management + escalation

**Source**: [Coveo Care · docs.coveo.com/en/1352](https://docs.coveo.com/en/1352/)

### D. Industry SRE best practices for production AI / search platforms (2025-2026)

Synthesized from InfoQ, Pylon, Sygnia, Microsoft Azure Well-Architected, Rootly, and incident.io's playbook guidance:

| # | Best practice | What it means for our scenario |
|---|---|---|
| 1 | **Severity classification (P1-P5 standard)** | Map P1 = customer-facing outage + revenue impact (this scenario); P2 = degraded performance; P3 = minor regression; P4 = cosmetic |
| 2 | **Communication cadence by severity** | P1: every 30 min · P2: hourly · P3: every 4h. This is the basis for Slide 7's exec-comms cadence. |
| 3 | **Role assignment** | Incident Commander · Technical Lead · Customer Comms · Scribe — separate roles, separate people |
| 4 | **Common governed data platform** | Avoid each engineer fetching telemetry from their own laptop; centralize. Maps to Coveo's Admin Console + Activity Browser as the single source of truth |
| 5 | **Staged autonomy model** | Read-only → Advised → Approved → Autonomous. **Don't go from zero to autonomous remediation.** Apply to any auto-rollback / auto-throttle changes |
| 6 | **Correlation layer** | Tie signals together — logs + deploys + config drift + traces. Maps to Slide 2's six-check playbook |
| 7 | **Eliminate data silos** | Customer's APM + Coveo's Admin Console + GitHub deploys + customer's own deploy log — all need to be reachable in <5 min |
| 8 | **Reduce 3 on-call burnout vectors** | Alert noise · missing context · manual postmortem. AI tools (PagerDuty AIOps, incident.io, Rootly) address all three |
| 9 | **Centralize incident context** | One channel · one war room · one timeline. Don't fragment across Slack threads + Zoom calls + status pages |
| 10 | **Business-context awareness** | A latency spike during a maintenance window ≠ a latency spike at peak hours. Build context into severity classification |
| 11 | **Causal/deterministic analysis** over probabilistic guessing | Dynatrace Davis AI pattern: real-time topology maps + data lakehouses → deterministic root-cause identification incl. blast radius + dependency chain |
| 12 | **Match automation tolerance to domain** | Regulated industries (gov, finance, healthcare) want lower autonomy than B2C SaaS |

**Sources**:
- [Microsoft Azure Well-Architected — SaaS Incident Management](https://learn.microsoft.com/en-us/azure/well-architected/saas/incident-management)
- [Pylon · Incident Response Playbooks: Build trust with customers](https://www.usepylon.com/blog/incident-response-playbook)
- [Sygnia · SaaS Incident Response strategies](https://www.sygnia.co/blog/saas-incident-response/)
- [InfoQ · AI-Powered SRE for Autonomous Incident Response](https://www.infoq.com/presentations/ai-sre-incident-response/)
- [Rootly · AI SRE Guide 2026](https://rootly.com/ai-sre-guide)
- [Reco · Incident Management in SaaS](https://www.reco.ai/learn/incident-management-saas)

### E. Notable AI SRE platforms (for "what we'd add to be world-class" framing)

If the prevention slide (Slide 10) wants to point at "world-class," these are the names to drop:

| Platform | Differentiator |
|---|---|
| **PagerDuty AIOps + AI Agent Suite** | Enterprise incident management with ML-based noise reduction; MCP server integration |
| **incident.io · AI SRE** | Slack-native; AI alert triage, AI postmortems, Scribe transcription |
| **Rootly** | AI-native incident management with LLM-powered investigation across the observability stack |
| **Dynatrace Davis AI** | Hypermodal (predictive + causal + generative); production since 2017; default for large enterprises |
| **Resolve AI** | Autonomous SRE by OpenTelemetry co-creators; targets 80% autonomous resolution |

**Worth noting**: PagerDuty + incident.io both ship MCP servers, meaning a Coveo MCP integration could expose Coveo incident telemetry to these tools — a natural cross-product story.

### F. How the FDE role fits into Coveo's escalation machinery

Reading Coveo's documented process + the FDE role description, the FDE sits in this position when an incident hits:

```
Customer's CTO  ────► Coveo Support hotline (S1: phone) ────► Support Manager
                                                                   │ (customer advocate)
                                                                   ▼
                                                              Engages FDE
                                                              + Engineering
                                                              + Product Specialists
                                                              + Management (when needed)
                                                                   │
                                                                   ▼
                                                              FDE on the front line ─► customer + internal
```

The FDE is the **technical face** of Coveo to the customer during the incident — pre-positioned by Delivery Assurance, activated by the Support Manager. Slide 1's timeline (T+0 through T+24hr) is from the FDE's perspective inside this machinery.

### G. Honest framing for the deck

The deck should NOT pretend to invent incident response. Frame it as:
- **"This is how I'd plug into Coveo's existing escalation machinery"** — not "I'm building one from scratch"
- **"My playbook draws from the documented Coveo case management process + 2026 industry SRE patterns"** — credible, sourced, defensible
- **"What I'd add specifically as an FDE: the technical depth in the Coveo platform that the Support Manager doesn't have time to dive into"** — that's the FDE differentiator

---



## Slide 0 — Cover (≈10s)

**Visual** (using `incident-amber` theme — dark navy/black base, amber + red accents, Coveo blue for Coveo refs):
- Title: **When the platform breaks**
- Subtitle: An FDE's playbook · *Cyber Monday at Nespresso · Dec 1, 2025*
- Top-right corner: small amber stamp "**HYPOTHETICAL INCIDENT · PUBLIC FACTS ONLY**" — sets framing
- Speaker line: Franck Benichou · Forward Deployed Engineer candidate
- Bottom right wordmark: NESPRESSO × COVEO · CYBER MONDAY 2025

**Speaker notes**:
- "Hypothetical incident scenario, anchored in the publicly-documented Nespresso × Coveo partnership. The relationship facts come from Coveo's case study and Nespresso's ShopTalk 2025 co-presentation. The incident itself is constructed — to my knowledge no incident like this has occurred publicly at Nespresso. The framing lets me show FDE incident-response thinking against a real, recognizable Coveo customer."
- "The next 25 minutes: four sections — diagnosis, stabilization, communications, prevention."

**Key message**: real customer · real partnership · constructed incident · honest framing.

---

## Slide 1 — The scenario (≈60s)

**Visual**: split layout · left side = symptoms (red-bordered), right side = business impact (amber-bordered), timeline strip at the bottom.

**Customer + moment**:
- **Customer**: Nespresso ANZ · Coveo customer since 2022 · global partnership
- **Moment**: Cyber Monday · Dec 1, 2025 · 9:00 AM AEDT (single biggest gifting day of year for Nespresso machines + capsules)

**Symptoms (left pane · red)**:
- Site search **p95 latency: 200ms → 4-8s**
- **~8% of queries returning errors or 0 results**
- Personalized recommendations regressing to generic for logged-in users (~75% of traffic)
- Content-discovery panel (recipes / machine care) intermittently failing to render
- **Nespresso's real-time zero-result dashboard (built on Coveo Analytics)** firing constantly

**Business impact (right pane · amber)**:
- Search conversion lift **drops from 3:1 → 0.5:1** (search now WORSE than browsing)
- Cart abandonment **+40%**
- **~$4M-$6M AUD revenue at risk over 4 hours** (industry benchmark: median retail outage = $1M USD/hour per New Relic 2024 Observability Forecast)
- Cyber Monday paid social campaigns driving traffic INTO the broken experience
- YC Eu (Head of E-Business, Nespresso Oceania) DMs me at 7:47 AM AEDT

**Timeline (bottom strip · honest version showing earlier signals)**:
```
07:15 AEDT   Nespresso Datadog SLO burn-rate alert (search-API p95)
07:25 AEDT   Nespresso #ops-search Slack: support tickets spiking
07:30 AEDT   Coveo zero-result monitoring threshold breached → FDE paged
07:47 AEDT   YC Eu DM (now informed by her ops team)
07:52 AEDT   Acknowledge · open Coveo war room · file Jira master ticket
08:02 AEDT   First exec update to YC Eu (T+15min from her DM)
09:00 AEDT   PEAK HOUR · first hypothesis verified
11:00 AEDT   Stabilized OR continuing to mitigate
T+24h        Post-incident review · public RCA · backlog tickets filed
```

**Speaker notes**:
- "Two hours before peak. That's the worst possible timing — visible enough to be obvious, late enough that we can't pre-mitigate."
- "Important framing detail: **YC Eu's 7:47 DM is the THIRD signal, not the first**. The Datadog SLO alert fires at 7:15. Nespresso's ops team is already in their #ops-search Slack channel by 7:25. The Coveo zero-result threshold breaches by 7:30. If I'm doing my job, **I should be in the war room before YC Eu DMs me.** If she's my first signal, the monitoring is broken — and that becomes a Slide 9 prevention item."
- "Nespresso's whole gifting season pivots on this 4-hour window. ~$5M AUD at risk · social campaigns driving traffic into the broken experience."
- "YC Eu and I have a weekly sprint cadence — she DMs me directly, not Coveo Support, because that's our existing channel."
- "Two things matter from here: speed of communication and quality of diagnosis. Both fail-fast — better to be wrong publicly at T+15min and corrected at T+1hr than silent until T+4hr."

**Key message**: real customer · concrete stakes · 4-hour window before the day is lost · **the FDE should be aware before the exec DM — multi-source signal detection (Datadog SLO + customer support tickets + Coveo monitoring + Slack Connect) is the front-line**.

**Important framing**: I'm the **Incident Commander** for the Coveo-side of this incident — the single decision authority during the active phase. The 5 C's apply: Command · Control · Coordination · Communication · Collaboration. Critical anti-pattern to avoid: the IC must NOT also be debugging the failure. I delegate technical debugging to Coveo engineering; I run the coordination + decisions + customer-facing comms. *(Per [Google SRE doctrine](https://sre.google/sre-book/managing-incidents/) — the IC outranks the CEO during incidents.)*

---

## Slide 2 — My first hour: the RCA playbook (≈90s)

**Visual**: 6-step checklist with time-boxes (dark cards with amber border-left for "in-progress" feel · monospace for the data sources).

| # | Check (Nespresso-specific) | Where | Time-box |
|---|---|---|---|
| 1 | **Coveo platform health** — Activity Browser (audit log) + Status Page · zero-result rate trend · latency by region | Coveo Admin Console · `platform.cloud.coveo.com/status` | 3 min |
| 2 | **Nespresso APM** — search-API latency percentiles vs Sunday baseline · error clustering by query type | Nespresso's Datadog (shared dashboard from weekly sprint) | 5 min |
| 3 | **Per-query deep-debug** — **Relevance Inspector** (paste searchUid from failing query) · `&debug=true` execution report · Inspect ML Models · Review Model Information | Coveo Admin Console · Relevance Inspector + ML Models | 5-7 min |
| 4 | **Coveo Query Pipeline rules** (last 7 days · who shipped what for Cyber Monday) · **Activity Browser** shows the audit trail | Coveo Admin Console · Query Pipeline tab | 5 min |
| 5 | **Coveo Catalog source push status + Data Health** — Push/Stream API queue depth · **Data Health Overview** for validation errors · **Event Browser** for late/malformed events · **Log Browser** with `LogResponseBodyWhenUnsuccessful` enabled for source-level error bodies | Coveo Admin Console · Sources + Data Health + Log Browser | 5-7 min |
| 6 | **Nespresso-side deploy log** (frontend + Adobe Commerce backend · last 48h · esp. Cyber Monday campaign config) | Nespresso eng team · their deploy bot | 5 min |

**Speaker notes**:
- "Six checks in ~25 minutes. Each one rules in or out a category of cause."
- *(1)* "Coveo platform status page says 'all systems operational' — but status pages lag actual incidents. **Activity Browser** tells me Coveo's truth · the audit log of every pipeline change and ML retrain in the last 7 days."
- *(2)* "Nespresso's Datadog is shared with me from the weekly sprint cadence — I don't need to wait for them to grant access. I can see search-API p95 spiked at 7:15 AEDT, 32 min before YC Eu's DM."
- *(3)* "For per-query deep-debug, my primary tool is the **Relevance Inspector** — Admin Console page where I paste the searchUid from a failing query and see the entire query journey: parameters before AND after the pipeline · which pipeline routed it · all ranking expressions applied. Backed by `&debug=true` for in-page debugging and **Inspect ML Models** for live model behavior. The Relevance Inspector is the FDE's deepest diagnostic tool."
- *(4)* "**Query Pipeline rule audit** via **Activity Browser**. The Friday rule shipped for the Cyber Monday campaign is visible there with timestamp + author. Reproduce in the **sandbox organization** to test the suspected rule before reverting in production."
- *(5)* "Multi-tool check for the source side: **Coveo Catalog source push status** (Push/Stream API queue depth) · **Data Health Overview** for validation errors · **Event Browser** for late/malformed events · **Log Browser** with `LogResponseBodyWhenUnsuccessful` enabled to capture source-level error response bodies. The Push/Stream API queue from Nespresso's Adobe Commerce backend was 90 min delayed Sunday night — Data Health may flag this as event-arrival anomalies. **Note**: there's no native 'Coveo for Adobe Commerce' connector — Nespresso pushes catalog data via the Coveo Push/Stream API to a Catalog source (similar pattern to commercetools)."
- *(6)* "Last check: did Nespresso ship something? Cyber Monday campaign config could have introduced a regression in the frontend that's bleeding back to the search-API. More than half of Coveo customer incidents have a customer-side root cause."

**Key message**: triage is a checklist, not improvisation. The FDE's checklist is informed by **knowing Nespresso's specific stack** — Adobe Commerce backend, the weekly sprint cadence, the campaign-rollout pattern — AND **knowing Coveo's platform diagnostic toolkit by name** (Activity Browser · Relevance Inspector · Data Health · Log Browser · Inspect ML Models). Generic SRE checklist couldn't do this.

**The FDE's complete Coveo diagnostic toolkit** (worth listing if a panelist asks):
- **Platform health**: Watchtower section (Admin Console home) + Coveo Status page
- **Resource audit**: Activity Browser
- **Per-query forensics**: Relevance Inspector + `&debug=true` execution report
- **ML model debug**: Inspect ML Models + Review Model Information
- **Source-side**: Log Browser + `LogResponseBodyWhenUnsuccessful` parameter
- **Data integrity**: Data Health page (Overview + Event Browser)
- **Programmatic ops**: Coveo CLI (`coveo org:resources:pull`/`push`, snapshots)
- **Test environment**: Sandbox organization (paired with production org)

---

## Slide 3 — Hypothesis ranking (≈90s · merges old 3+4)

**Visual**: 2x2 grid (Likelihood × Verification cost) overlaid with the 5 specific Nespresso hypotheses. The starred ones are the FDE's top picks.

```
                       LOW verification cost              HIGH verification cost
                       ─────────────────────────────────────────────────────────
HIGH likely   →   ★ Query pipeline rule misfire        Cache TTL alignment under
              →     (Friday's Cyber Monday rule)         3.5× traffic spike
              →     - rollback in 30 sec
              →
              →   ★ ML model retrain regression
              →     (Sunday overnight retrain)
              →     - dissociate model: ~2 min Console
              →     - OR re-import prior pipeline export
              →
LOW likely    →     Push/Stream API queue lag           Coveo platform sub-region issue
              →     (90-min delay Sun night)            (despite status page saying OK)
              →     - force re-push to Catalog          - escalate via Support hotline
              →       source: 15 min                    - Coveo's "platform" status page
                                                         lags actual incidents
```

**Speaker notes**:
- "Five competing hypotheses. Two starred: cheapest to verify AND high-likelihood. Start there."
- "Top-left: **the Cyber Monday Query Pipeline rule shipped Friday** is suspect because (a) it's the most recent change, (b) misfiring rules are the #1 Coveo failure mode in my experience, (c) rollback is 30 seconds. Test first."
- "Also top-left: **the Sunday overnight ML retrain**. The retrain happens every week, but this Sunday it had to learn from a query mix that didn't exist before — Cyber Monday gift queries. If the retrain regressed on those, we'd see relevance collapse. Swap to Friday's model: 5-minute action."
- "Top-right: **cache TTL alignment under traffic spike** is the Bhagya Rana Black Friday postmortem pattern — keys aligned, cache hit rate collapses, retries cascade. High-likelihood but harder to verify without dropping cache."
- "Bottom-right: **Coveo platform sub-region** — only if everything else rules out. Status page says operational but status pages lag. Last resort because escalation is expensive."
- "Re-rank every 15 minutes as new data comes in. The grid is a heuristic, not a fixed prescription."

**Key message**: don't let the customer's framing narrow your hypothesis space too early · prioritize fast learning over being right first try.

**Q&A trap**: *"What if you're wrong about your ranking?"* — *"Re-rank every 15 minutes. The wrong answer in writing at T+30 (corrected at T+45) is more useful than 'still investigating' at T+60."* See Slide 9 on how this improves over time.

---

## Slide 4 — Immediate stabilization (≈75s · was old slide 5, part 1)

**Visual**: parallel-tracks diagram showing 3 stabilization actions running concurrently in the first 30 minutes (NOT sequential — parallelize cheap-to-verify hypotheses). **Each track is a Jira ticket with owner + status**.

```
T+0min        T+15min                            T+30min
────────────────────────────────────────────────────────
TRACK A (red): Query Pipeline rule rollback (Coveo FDE)
              JIRA: CVO-SUP-NES-CM01-A · git revert PR linked
              ├─ revert Friday's Cyber Monday rule   ──→  verify in Activity Browser
              │   (config change via Console)            ──→ measure zero-result rate

TRACK B (amber): Dissociate Sunday-retrained ML model from production
                 pipeline (Coveo FDE + Eng)
              JIRA: CVO-SUP-NES-CM01-B · or re-import prior pipeline export
              ├─ dissociate model · fall back to       ──→  verify in Inspect ML Models
              │   baseline relevance · ~2 min Console   ──→ measure relevance metrics
              │   action (NOT a "rollback button")

TRACK C (blue): Edge throttling at Nespresso CDN (Nespresso eng team)
              JIRA: NES-INC-2025-CM01-C · Nespresso PR linked
              ├─ rate-limit search-API at edge       ──→  protect upstream
              │                                           ──→ measure latency p95
```

**Speaker notes**:
- "Three actions, parallelized. Cheap-to-verify hypotheses run concurrently — we don't serialize."
- "**Each track is a Jira ticket BEFORE it executes.** No ad-hoc work. Owner named · status visible · linked to the master incident ticket and to the GitHub PR or config commit that ships the fix. Track A rolls back via a git revert PR; Track B uses a git tag-based model-config rollback; Track C is Nespresso's eng team filing a PR on their CDN config. **All actions trace to code.**"
- "**Track A (red · most likely)**: roll back the Friday Cyber Monday Query Pipeline rule via the Activity Browser. Fast reversible action — config flip in the Console. If zero-result rate drops, we have our answer."
- "**Track B (amber · second-most likely)**: **dissociate** the Sunday-retrained ML model from the production pipeline — this is Coveo's actual mechanism, NOT a 'rollback button' (Coveo doesn't have one). Dissociation returns the pipeline to baseline relevance (no ML personalization) in ~2 min via Console. Alternative: **re-import the prior pipeline export** if we have versioned config in git. Falls back to slightly-less-personalized but stable relevance. **Customers prefer degraded + working over premium + broken.**"
- "**Track C (blue · protect-and-buy-time)**: ask Nespresso eng to rate-limit at their CDN edge. Doesn't fix the root cause, but prevents cascade. Buys us 15 minutes to verify Tracks A + B."
- "All three are **reversible**. That's the discipline — if I'm wrong, I undo in under a minute. Speed without irreversibility."

**Key message**: parallelize cheap-to-verify hypotheses · **every action is a ticket linked to a PR** · all actions reversible · buy time at the edge while you diagnose at the core.

**Mitigation-before-RCA discipline** ([Google SRE](https://sre.google/sre-book/managing-incidents/)): *"Customers do not care whether or not you fully understand what caused an outage. What they want is to stop receiving errors."* Bias toward reversible action — roll back first, prove root cause after. **Document the decision rationale even if it turns out wrong**: *"Rolled back the Friday Query Pipeline rule at 08:02 AEDT because it was the most recent change AND cheapest to verify — even though we weren't 100% sure it was the cause."* Post-mortem context > silent action.

**The Coveo CLI + sandbox pattern** (when there's time to be safe):
- For each track, the safer-but-slower path is: **test in Nespresso's sandbox organization first** (5-10 min) before applying to production
- Apply the fix via **Coveo CLI** (`coveo org:resources:push`) so every change is code-versioned · git committed · diff-reviewable
- This is **the exact discipline I shipped for the Pokémon build** — Coveo's own platform supports it via CLI + sandboxes. The bridge between the two presentations.
- During a SEV1 with $5M+ at risk, we might skip the sandbox gate for the *most-reversible* actions (Query Pipeline rule revert) but use it for the *less-reversible* ones (ML model dissociation). Calibrated speed-vs-safety call.

---

## Slide 5 — Verification & handback (≈60s · NEW · was part of old slide 5)

**Visual**: 3-step verification checklist + the "handback" criteria when the FDE returns control to the customer's normal operations.

```
STEP 1 · Verify the fix is holding (T+30 to T+60)
  ☐ Zero-result rate back to baseline (<2%)
  ☐ Search-API p95 latency back to <500ms
  ☐ Conversion lift restored (search vs browse)
  ☐ Personalization recommendations rendering for logged-in users
  ☐ Content-discovery panel rendering recipes/care

STEP 2 · Watch for relapse (T+60 to T+4hr)
  ☐ No degradation as traffic ramps to Cyber Monday peak
  ☐ Joint Coveo + Nespresso eng on call · shared Slack Connect active
  ☐ Cache hit rate trending healthy

STEP 3 · Handback to normal ops (T+4hr)
  ☐ All Step 1 metrics holding for 3+ hours through peak
  ☐ YC Eu's team confident in recovery (verbal handoff)
  ☐ Post-incident review scheduled (T+24hr)
  ☐ War room channel transitioned to read-only / archive
```

**Speaker notes**:
- "Stabilization isn't 'pushed a fix and walked away.' It's verified, monitored through peak, and handed back deliberately."
- "Step 1 is the first 30 minutes after the fix lands — does the data say it worked?"
- "Step 2 is the harder part: holding through peak. We're still in the war room watching dashboards for 4+ hours. Most relapses happen here."
- "Step 3 is the handback — when do I release the customer's team to normal operations? When metrics have held for 3+ hours through the peak AND YC Eu's team is confident. Verbal handoff matters · paper handoff doesn't."
- "If anything degrades in Step 2 or Step 3, we restart from Slide 4 with a refined hypothesis."

**Key message**: stabilization has 3 phases · the FDE doesn't release until the customer's team is verbally confident · relapse is the failure mode to watch for.

**The 16-hour timezone challenge** (must address explicitly): Nespresso ANZ is UTC+11, Coveo Montréal is UTC-5 — that's a 16-hour offset. If the incident is still active at Nespresso's end-of-day (7pm AEDT = 3am EST in Montréal), the IC role must hand off cleanly. **Handoff requirements**: structured pinned summary in war room · verbal transfer with explicit *"You're now the Incident Commander, okay?"* · call recording for context · pre-positioned regional FDE on-call (APAC or EMEA). **Anti-pattern**: midnight handoff to a region without coverage. This is exactly why **24/7 regional FDE rotation (Slide 9 Item 5)** matters — not "more Montréal FDEs" but **geographic FDE distribution** so Nespresso ANZ always has a daylight-time FDE available. ([Source: Rootly · Distributed and Global On-Call Best Practices](https://rootly.com/blog/distributed-and-global-on-call-best-practices-for-24-7-teams))

---

## Slide 6 — Communication architecture (≈90s)

**Visual**: 5-audience matrix · channel + cadence per audience. NOT inherited from Coveo's existing comms playbook — the FDE function is new at Coveo, so we **plug into** existing channels and add an FDE-appropriate layer on top.

| Audience | Channel | Cadence | What goes there |
|---|---|---|---|
| **Coveo war room** (internal) | Internal Slack `#inc-nespresso-cm2025-search` | Real-time | Diagnosis · technical detail · decisions |
| **Nespresso tech team** | **Shared Slack Connect channel** (from weekly sprint cadence) + phone bridge | Real-time | Tactical updates · joint action · paste log output |
| **YC Eu + her execs** | **Email + dup. to Slack Connect** | **Every 30 min hot · hourly stabilizing** | Calibrated status · always names next update time |
| **Coveo internal leadership** | Coveo Slack `#incident-updates` broadcast | Per milestone | Visibility for CEO/CRO/CSO without interrupting war room |
| **Nespresso's wider org** | Routed via YC Eu (we don't go around her) | She decides | Single point of contact discipline |

**The FDE's unique communication advantage** (callout box):

> The shared Slack Connect channel with Nespresso ANZ already exists from the **weekly sprint cadence**. A generalist SRE would have to set up new channels mid-incident. **The FDE is already in.**

**Anti-patterns to avoid** (callout box · red):
- Silent gaps >30 min during hot phase (silence breeds executive drive-bys)
- Fake ETAs (*"unknown"* + commit to next update time is the trust-builder)
- Split-brain (Zoom war room + Slack thread without one source of truth)
- War room staying open after the incident is over

**Speaker notes**:
- "Five audiences · five channels · five cadences. The architecture deliberately puts the FDE in a hub-and-spoke position — I'm in the Coveo war room AND the Nespresso shared channel AND writing to YC Eu directly. That's the integration value of an embedded role."
- "The 30-min cadence to YC Eu is the most important discipline. The cadence IS the message — *we're on it, you'll hear from us at X, even if X is 'unknown still.'*"
- "Single point of contact is critical. We don't email her CMO or COO directly — YC Eu controls her own org's narrative. We feed her, she distributes."
- "The shared Slack Connect channel is the FDE differentiator. It exists because of the relationship investment from weekly sprints. A new vendor or generalist SRE wouldn't have this — they'd be setting up channels at T+10min while we're already coordinating."

**Key message**: communication is half the recovery · cadence is what builds the trust the technical fix earns · the FDE's embedded relationship is the unique comms advantage.

---

## Slide 7 — Sample exec note (≈60s)

**Visual**: actual paragraph in an email-style frame · annotations to the side highlighting **what makes it work**.

```
To:       YC Eu <yc.eu@nespresso.com>
Cc:       [Coveo Support Manager] · [Coveo CSM]
Subject:  [INCIDENT] Search platform · T+15min · 08:02 AEDT

YC,

We're seeing intermittent search failures at Nespresso ANZ that started
~07:15 AEDT. Initial scope: ~8% of search queries are returning errors
or zero results, and personalized recommendations are regressing to
generic for logged-in users. Estimated impact: search conversion lift
dropping from your 3:1 baseline toward 0.5:1.

Top two hypotheses right now: (1) the Friday Cyber Monday query
pipeline rule misfiring, (2) Sunday's overnight ML retrain regressing
on Cyber Monday query mix. Both are cheap to verify — we're rolling
back the rule and swapping to Friday's ML model in parallel. Expect
confirmation in the next 15 min.

Nespresso eng is in the shared Slack Connect channel with me.

Next update: 08:32 AEDT regardless of progress.

— Franck Benichou
  Forward Deployed Engineer · Coveo
```

**Side annotations** (amber callouts):
- **"~8% · ~07:15 AEDT · 3:1 → 0.5:1"** → *scope quantification · specific is credible*
- **"Top two hypotheses (1) + (2)"** → *named hypothesis is data, not vibes*
- **"Both are cheap to verify"** → *signals discipline, not random fixes*
- **"Next update: 08:32 AEDT regardless of progress"** → *commitment to a clock · removes "is he ignoring us?" anxiety*
- **No fake ETA on resolution** → *trust-preserving · honest uncertainty*

**Speaker notes**:
- "About 140 words. Calibrated tone. Written *to YC Eu specifically* — first-name basis because we work weekly. Cc's the Coveo Support Manager and CSM so the institutional record is preserved."
- "Five things to notice. **One**: scope quantification — '~8% · ~07:15 AEDT · 3:1 → 0.5:1' — not 'search is having issues.' Specific numbers are credible. They also let her forward this to her CMO and have him understand the stakes."
- "**Two**: I name the top two hypotheses explicitly. Not 'we're investigating' — investigating is a verb. Named hypothesis is data. If I'm wrong, I correct in 30 min."
- "**Three**: I tell her what we're doing in parallel. Two cheap-to-verify actions, both reversible. Discipline shows."
- "**Four**: I name the next update time on a clock. *08:32 AEDT regardless of progress.* That commitment is the trust-builder. She doesn't have to chase me; she doesn't have to chase anyone. She gets back to running her business."
- "**Five**: I don't give a fake ETA on resolution. If I said 'fixed by 09:00' and missed, I'd lose her trust for the rest of Cyber Monday. *Unknown* + *commit to next update* is the industry-standard discipline."

**Key message**: the words on the page during an incident matter as much as the code you push · YC Eu is the single point of contact and she manages her own org's narrative.

**Q&A trap**: *"What if your hypothesis is wrong and you've already named it?"* — *"That's exactly why the next-update commitment exists. Update at 08:32 AEDT with the corrected hypothesis. Naming a wrong hypothesis at 08:02 is recoverable; silence isn't."*

**Sources for the format**:
- [incident.io · Incident Communication Best Practices](https://incident.io/blog/incident-communication-best-practices)
- [Runframe · 8 Incident Communication Templates](https://runframe.io/blog/incident-stakeholder-communication-templates)

---

## Slide 8 — Post-incident actions (≈60s)

**Visual**: 5 numbered cards in a row · "within 24 hours of stabilization" timestamp at top.

| # | Action | What it produces | Owner |
|---|---|---|---|
| 1 | **Blameless post-mortem** (Coveo + Nespresso joint) — **filed as Jira ticket in both instances** | Facts · timeline · decisions made · what we didn't know · what we'd do differently · permanent record-of-truth | FDE (me) drafts · joint review |
| 2 | **Runbook addition** to Coveo's Nespresso ANZ runbook **(Markdown in customer-config GitHub repo)** + Coveo FDE pattern library (Confluence) | Documented playbook for "Cyber Monday-class search platform incident" · next person responds 50% faster · feeds new-FDE onboarding | FDE (me) |
| 3 | **Monitoring gap closure** — *the alert that should have fired at 07:15 AEDT is now added* | New Datadog SLO burn-rate alert · Coveo zero-result threshold tightened · linked Jira tickets · committed via GitHub PR | Joint Coveo + Nespresso |
| 4 | **Load test on Nespresso's Coveo staging org** — code committed to staging-repo · CI-runnable | Reproduce Cyber Monday conditions · validate fix holds · catch regressions before next peak (Boxing Day) | Coveo engineering |
| 5 | **Public RCA to Nespresso's stakeholders** | Same content as internal post-mortem · executive-readable · no scapegoating · YC Eu can share with her CMO/COO/CEO | FDE (me) + Coveo CSM |
| 6 | **Internal Coveo product feedback** — file ticket in Coveo Product Jira if incident revealed a platform gap | E.g., status-page lag · ML retrain pause control · staging-test mode for Query Pipeline rules | FDE (me) |

**Speaker notes**:
- "**Six deliverables. All within 24 hours of stabilization. Every one of them is a Jira ticket or GitHub PR — no ad-hoc work.**"
- "**Action 1**: blameless joint post-mortem, filed as Jira tickets in both instances (Nespresso's and Coveo's). The 'joint' is critical — Nespresso eng team + Coveo team in the same room, going through the same data. Builds the relationship trust that survives the next incident."
- "**Action 2**: runbook addition. This is where the FDE earns long-term value. Customer-specific runbook lives as Markdown in the customer-config GitHub repo (parallel to the discipline I shipped for the Pokémon Challenge). Cross-customer patterns go into the Coveo FDE pattern library in Confluence. Knowledge compounds."
- "**Action 3**: the monitoring gap. The most important question after any incident is *why didn't this alert at 07:15 AEDT, 32 minutes before YC Eu had to DM me?* We add the alert. The alert addition is a GitHub PR to the monitoring config. Next time, we beat the customer to the report."
- "**Action 4**: load testing on staging. Specifically targeting Cyber-Monday-class query patterns. The test itself is code (CI-runnable), committed to a staging-test repo. Reproducible by anyone."
- "**Action 5**: public RCA. Tone matters as much as content. **Blameless internally; humble externally.** YC Eu will share this with her CMO + CEO — write it so she's proud to forward."
- "**Action 6** (the often-forgotten one): file a feedback ticket in Coveo's internal Product Jira. The FDE is Coveo product team's eyes and ears inside the customer. Every incident reveals at least one platform gap — feature gap, missing tooling, wished-for feature. If we don't file it, the product team never learns. *The FDE is the feedback loop.*"

**Key message**: every post-incident deliverable is a tracked artifact — Jira tickets · GitHub PRs · committed runbook · Confluence pattern entry · product feedback. **No tribal knowledge.** The 24h after stabilization is the highest-leverage time of the whole engagement.

**Two operational disciplines added here** (Q&A material if asked, in speaker notes if time):

1. **Public RCA discipline (Cloudflare model)**: don't rush the RCA · accuracy over speed · management review before publication · audience-segmented delivery (via Coveo's status page subscribers, not all customers). The public RCA is a TRUST INVESTMENT, not a compliance checkbox. ([Source: Cloudflare · Customer Incident Management Policy](https://developers.cloudflare.com/support/customer-incident-management-policy/))

2. **SLA credits / contractual remedies**: Coveo Care has SLA breach calculations that may owe Nespresso credits. The FDE doesn't promise credits during the incident · that conversation belongs to Coveo CSM + Nespresso procurement during the post-incident review. Mentioning it quietly here as part of the joint review process.

**Multi-vendor coordination if applicable**: if root cause involved Adobe Commerce, Monetate, or Contentsquare vendor seam, the joint post-mortem includes vendor liaisons. ([Source: Adobe Commerce · Shared Responsibility Model](https://experienceleague.adobe.com/en/docs/commerce-operations/security-and-compliance/shared-responsibility))

---

## Slide 9 — Structural prevention (longer horizon) (≈75s)

**Visual**: 5 structural changes that prevent the *class* of incident · **each is a tracked Jira ticket with owner + priority + ETA** · framed as the FDE's prevention investment proposal to Nespresso + Coveo.

| Ticket | Change | Owner | Priority | ETA |
|---|---|---|---|---|
| `CVO-FDE-NES-2025-001` | **Coveo SLO + error-budget for Nespresso ANZ** — *"99% of search queries <500ms · 99.5% non-zero-result rate"* · burn-rate freezes ML retrains + pipeline rule changes | Coveo CSM + FDE | **P1** · blocks next peak | 6 wks (Q1 2026) |
| `CVO-FDE-NES-2025-002` | **Peak-window change freeze** — no ML retrains · no Query Pipeline rule changes · no index schema changes from Black Friday through Boxing Day | Joint Coveo + Nespresso | **P1** · blocks next peak | 4 wks |
| `CVO-FDE-NES-2025-003` | **Quarterly chaos game day** with Nespresso ANZ — Coveo runs a pre-recorded incident · Nespresso eng + I respond against the runbook · we measure response time | FDE (me) | **P2** | First game day in Q1 2026 |
| `CVO-FDE-NES-2025-004` | **Public-share Coveo observability dashboard** for Nespresso — YC Eu's team can self-diagnose simple issues without paging me | FDE (me) | **P2** | 8 wks |
| `CVO-FDE-NES-2025-005` | **24/7 FDE rotation during Nov–Dec peak window** — at least one Coveo FDE on-call for all Nespresso markets during peak shopping season | Coveo (org-level commitment) | **P1** · blocks next peak | Q3 2026 (organizational change) |
| `CVO-FDE-NES-2025-006` | **Sandbox synchronization discipline** — daily `coveo org:resources:pull` from Nespresso production · sync to sandbox · enables safe-test-before-deploy for ALL future changes | FDE (me) + Nespresso eng | **P1** · blocks next peak | 4 wks |
| `CVO-FDE-NES-2025-007` | **Coveo CLI + git-based deployment pipeline** for Nespresso config — every Query Pipeline rule, ML model config, IPE Python change goes through PR review · `coveo org:resources:push` from CI/CD · automated daily snapshots committed to git as backup | FDE (me) | **P1** · blocks next peak | 6 wks |

**Speaker notes**:
- "Slide 8 was tactical — fixes the *specific* incident. Slide 9 is structural — prevents the *class* of incident."
- "**Five Jira tickets, not five bullets.** Each one has owner · priority · ETA · monthly review with Nespresso + Coveo CSM · quarterly chaos game day measures progress. Prevention isn't aspirational; it's tracked."
- "**SLO + error-budget**: once we've quantified 'acceptable failure rate,' release decisions become data-driven, not vibes. If budget exhausted → automatic freeze of ML retrains + pipeline rule changes until burn rate recovers."
- "**Peak-window change freeze**: this is the unloved but high-ROI move. Nespresso doesn't ship features during Black Friday → Cyber Monday → Boxing Day window. Coveo doesn't retrain ML models. Period. Codified as a check-in-CI for the customer-config repo — PRs blocked during the freeze window."
- "**Chaos game day**: I'd run one per quarter with Nespresso eng. We rehearse the playbook. We find the gaps. Best case: we discover the runbook is wrong before YC Eu DMs us in anger."
- "**Public-share dashboard**: ideally Nespresso eng can self-diagnose 80% of issues without me. This is investment in their independence, not job-security risk for me — the FDE who removes themselves from the critical path of small issues is the FDE who's free to handle big ones."
- "**24/7 FDE rotation during peak**: this is the org-level ask of Coveo. Nespresso's peak window deserves dedicated coverage. If I'm the only FDE on the account, I'm a single point of failure. Rotation removes that."

**Key message**: post-incident isn't over until structural prevention is funded + scheduled · **each item is a tracked Jira ticket with owner + ETA · prevention is operationalized, not aspirational** · **these 7 items turn the next Cyber Monday into a non-event** AND establish the code-as-source-of-truth discipline I demonstrated in the Pokémon Challenge at Coveo-enterprise scale.

**Items 6 + 7 are the bridge to Topic 1**: the same Coveo CLI + sandbox + version-controlled config pattern I'd recommend for Nespresso is exactly what I shipped for the Pokémon build (`config/`, `scripts/`, `bootstrap.sh`). **Coveo's platform supports this discipline — it just needs to be activated at the customer.**

---

## Slide 10 — Wrap + Q&A (≈30s)

**Visual** (mirroring the cover · dark base + amber + red accents):
- Title: **"Speed of communication · Quality of diagnosis · Discipline of prevention"**
- Subtitle small: *Cyber Monday at Nespresso · an FDE's playbook*
- Bottom-right: "Questions?"
- Same hypothetical-framing footer as the cover

**Speaker notes**:
- "Three things matter in this job. **Speed of communication** — the cadence is the message; YC Eu didn't have to chase me. **Quality of diagnosis** — five hypotheses ranked, two cheap-to-verify run in parallel, all reversible. **Discipline of prevention** — the post-mortem becomes the next runbook, and the structural fixes turn the next Cyber Monday into a non-event."
- "The first two get you through the incident. The third is what keeps you from being the one paged on the next one."
- "I'm happy to take questions — on the Nespresso scenario, on the FDE role, on how this would scale to a real Coveo engagement, or on anything from Topic 1's Pokémon build."

**Key message**: closing visual bookend · panel knows it's time for Q&A · cleanly hands off.

---

## Q&A — anticipated questions + prepared answers

| Q | Prepared answer (compressed) |
|---|---|
| "Walk me through a specific incident you've handled." | *(Have a real story ready — anonymized if needed. Even if you don't have a Coveo-specific one, a comparable production-incident story from prior work works. Structure: scenario → first action → key decision point → resolution → what I'd do differently next time. Honest about what surprised you.)* |
| "How do you handle a customer who panics?" | Acknowledge feelings, redirect to facts. *"I hear you — I'd be worried too. Here's what we know in the last 5 minutes that we didn't know 5 minutes ago."* Cadence + specificity defuses panic better than reassurance does. |
| "When would you escalate internally vs handle it yourself?" | I escalate at T+0 (paging on-call) for visibility, not because I need help. I ask for help when (a) I've ruled out the top 3 hypotheses, OR (b) the customer is at exec-CEO level and needs a Coveo VP in the room, OR (c) the fix requires a permission I don't have. Escalation is cheap; not escalating is expensive. |
| "What if you're wrong about the root cause?" | Acknowledge in the next exec update. State the corrected hypothesis. Continue the action plan. Customers respect honest course-correction more than they respect "we figured it out the first time." |
| "What if the incident is a Coveo platform-wide issue (not customer-specific)?" | Same playbook, different escalation path. I'm the first responder to my customer; Coveo's incident commander coordinates platform-wide. My job during a platform incident: customer-specific updates at the cadence, plus internal triage of what's customer-specific vs platform-specific blast radius. |
| "How much technical depth do you need to be effective here?" | Enough to read APM traces, run Coveo Admin Console queries, and form testable hypotheses. Not enough to fix kernel issues. Coveo's platform team is the backup for the deep stuff. The FDE role is the *coordinator* with technical credibility, not the bottom-of-stack engineer. |
| "What's the most important thing in the first 15 minutes?" | Acknowledging the customer. Within 5 minutes of the first report. Specific over generic — "I see [N]% error rate on your [hub], opening an internal incident channel now." Acknowledging buys you 30 minutes of patience to actually diagnose. |
| "What about customer-side issues — how do you keep the relationship good when it's *their* fault?" | Lead with collaborative framing, not vindication. *"Walking through our trace data with your team is the fastest path to root-causing — even if it turns out to be a deploy regression on your side, we'll have ruled out our layer first."* Customers know when something's their fault; never make them say it. |
| "How do you balance speed vs over-communication?" | Schedule the next update. *"I'll send the next update at T+30, regardless of progress."* That commitment means you don't get pinged every 5 minutes AND the customer knows when to expect news. Removes the "is he ignoring us?" anxiety. |
| "What's the worst incident pattern in your experience?" | The slow-burning one. Latency creeping up 2% per day for 2 weeks before anyone notices. By the time alarms fire, the customer has 2 weeks of degraded user experience. Mitigation: SLO-based monitoring with burn-rate alerts (catches slow burns), not just threshold alerts (only catch cliff drops). |
| "How do you decide what to share publicly in the RCA?" | Default to transparency. Withhold only when: (a) it'd expose a security vulnerability, (b) it implicates a third-party vendor (give them notice first), or (c) the customer's legal asks specifically. Otherwise, public RCAs build trust faster than discretion does. |
| "Have you handled a multi-customer incident?" | *(If you have, share that story — multi-customer is fundamentally different because coordination across many customer touchpoints is the work. If you haven't, lean into the playbook above + acknowledge that experience would refine your specifics. Honesty about experience > faking it.)* |

---

## Nespresso-specific Q&A traps (additions to the generic table above)

| Q | Prepared answer |
|---|---|
| *"Is this incident based on something that actually happened at Nespresso?"* | **No — this is hypothetical.** All the relationship facts (Coveo partnership · YC Eu's role · weekly sprint cadence · Coveo's specific surfaces at Nespresso) come from public Coveo case studies and Nespresso × Coveo joint presentations. The incident itself is constructed to demonstrate FDE incident-response thinking. To my knowledge no incident like this has occurred publicly at Nespresso. |
| *"Why pick Nespresso vs another Coveo customer?"* | Three reasons: (1) public case study with named Coveo footprint · (2) Cyber Monday is the highest-stakes peak-traffic moment in commerce · (3) the brand is recognizable enough that a panel can imagine the stakes. The scenario would work for Caleres, LCBO, Nespresso, or any other named Coveo commerce customer — Nespresso is the most dramatic. |
| *"What if the root cause was actually a Coveo platform issue you couldn't fix?"* | Then I'm the FDE coordinating with Coveo's platform team. My job shifts from technical lead to *customer-facing incident commander* — translating Coveo's progress into Nespresso-readable updates at the agreed cadence, while Coveo's platform team owns the fix. YC Eu doesn't care who fixes it; she cares that someone is on it and that I'm telling her the truth. |
| *"You mentioned YC Eu by name — would you use her name in a real panel without permission?"* | YC Eu is a public figure who co-presented with Coveo's Peter Curran at ShopTalk 2025 (covered by ClickZ). Her role at Nespresso ANZ is on her public profile. I'd never share private engagement details — the scenario uses only public-domain information. If she ever attended a panel, I'd want her in the audience. |
| *"How would the FDE role be different if Nespresso wasn't already a Coveo customer?"* | I'd lose the embedded relationship advantage — shared Slack Connect, weekly sprints, prior runbook knowledge. The FDE's value is the cumulative trust; the first 6 months of an FDE engagement are an investment that pays off exactly during incidents like this. |
| *"What's your day-to-day operational tool stack as an FDE?"* | **Comms**: Slack (Coveo-internal + Slack Connect with customer) · email · phone bridge · Zoom war room when needed. **Ticketing**: Coveo Jira + customer's Jira (Slack Connect bridges them). **Code**: GitHub for Coveo customer-config repos + customer's own GitHub repos. **Observability**: Coveo Admin Console + customer's APM (Datadog at Nespresso) + Coveo platform status page. **Documentation**: Markdown in repos + Confluence for FDE pattern library. **On-call**: PagerDuty (Coveo side). Concrete tools, not abstractions. |
| *"How do issues get logged and tracked during the incident?"* | Every action becomes a Jira ticket BEFORE it executes — no ad-hoc work. Master incident ticket in Nespresso Jira (their record of truth) · linked Coveo-internal ticket (our side) · child ticket per parallel stabilization action (Slide 4) · each linked to the GitHub PR that ships the fix. Post-incident: post-mortem ticket · runbook addition ticket · platform feedback ticket if applicable · 5 backlog tickets for structural prevention (Slide 9). |
| *"Where does the code actually live, and how does a rollback work?"* | Coveo's customer-side config (Query Pipeline rules, ML model configs, IPE Python, MCP server config) lives in a Coveo customer-config GitHub repo — code-as-source-of-truth, same discipline as my Pokémon build. Rollback = git revert + apply via PR or direct fast-forward. Customer-side code (CDN config, frontend integration) lives in Nespresso's own GitHub. Every action traces to a commit. |
| *"How do you share findings with Coveo's product team?"* | Two channels. **During the incident**: if the root cause is a Coveo platform bug, I escalate via the Coveo Slack `#platform-eng` channel — the Support Manager and I jointly engage Coveo's platform engineering team. **Post-incident**: I file a feedback ticket in Coveo Product's Jira backlog if the incident revealed a platform gap (e.g., status-page lag, missing "pause ML retrain" button, lack of staging-test mode for Query Pipeline rules). **The FDE is Coveo product team's eyes and ears inside the customer** — internal feedback is part of the deliverable. |
| *"How do you ensure the long-term remediation plan actually gets executed?"* | Slide 9's 5 items are filed as Jira tickets with owner + priority + ETA. Monthly review cadence with Nespresso's tech lead + Coveo CSM. Quarterly chaos game day reviews progress against the structural items. If a P1 item slips past its ETA → escalation via the CSM. **The plan is the backlog; the backlog is the plan.** |
| *"Who is the Incident Commander in this scenario, and what's that role?"* | **I am, on the Coveo side.** The Incident Commander is the single decision authority during the incident — they coordinate, communicate, and decide. Critically, they do NOT debug the failure themselves; debugging is delegated to Coveo engineering. The 5 C's apply: Command · Control · Coordination · Communication · Collaboration. Google SRE's quote: *"The incident commander outranks the CEO during incidents."* Nespresso also has their own IC on their side (likely their tech lead during the active phase) — we coordinate across IC roles. |
| *"What happens at end-of-Nespresso-day if the incident is still active?"* | **Big consideration — 16-hour offset between Nespresso ANZ (UTC+11) and Coveo Montréal (UTC-5).** If the incident extends into Nespresso's evening, I'd hand off the IC role to a regional Coveo FDE — APAC or EMEA-based. The handoff requires a structured pinned summary, verbal transfer with explicit *"You're now the Incident Commander, okay?"* per Google SRE doctrine, and a call recording for context. This is exactly why **24/7 regional FDE rotation (Slide 9 Item 5)** is structurally important — not "more Montréal FDEs," but geographic distribution so Nespresso ANZ always has a daylight-time FDE on call. |
| *"What if the root cause turns out to be at a vendor seam, like Adobe Commerce or Monetate?"* | Multi-vendor coordination is real. Adobe Commerce has a publicly documented shared-responsibility model — they own platform availability, Nespresso owns custom integrations. If the root cause is at the Adobe seam, I'd engage Adobe's incident response process via Nespresso's tech lead (who owns the vendor relationship). The FDE doesn't bypass the customer's vendor management — I stay in my lane while making sure the comms cadence to YC Eu reflects the cross-vendor reality. Joint playbooks for each vendor seam are part of Slide 9 prevention items. |
| *"How do you balance speed of mitigation vs being sure of root cause?"* | Google SRE doctrine: **mitigation BEFORE RCA**. *"Customers don't care whether or not you fully understand what caused an outage. What they want is to stop receiving errors."* I bias toward reversible action — roll back first (it's cheap), prove root cause after. I document the decision rationale even if it turns out wrong: *"Rolled back the Query Pipeline rule because it was most recent change AND cheapest to verify, even though we weren't 100% sure."* Bad decision context > silent action. |
| *"Will SLA credits be owed if Coveo's SLA was breached?"* | Possibly — Coveo Care has SLA breach mechanics. But **the FDE doesn't have that conversation during the incident** — it would erode trust in the active phase. The credit conversation belongs to Coveo CSM + Nespresso procurement during the post-incident phase. I mention it quietly as part of joint review (Slide 8 Action 1). |
| *"How do you write the public RCA — what's the discipline?"* | **Cloudflare model**: don't rush · accuracy over speed · management review before publication · audience-segmented delivery (status-page subscribers, not all customers). Public RCAs are trust investments, not compliance checkboxes. For Nespresso: the RCA goes to YC Eu first (she controls her org's distribution to her CMO/COO/CEO). Coveo's external RCA might post to Coveo status-page subscribers if multi-customer impact emerged. |
| *"What's the deepest diagnostic tool you'd use for a specific failing query?"* | **The Relevance Inspector** ([docs.coveo.com/en/mbad0273](https://docs.coveo.com/en/mbad0273/)) — Admin Console page where I paste the searchUid from a failing query (visible in browser dev tools · Network tab) and see the entire query journey: parameters before AND after the pipeline · which pipeline routed it · all ranking expressions applied · all triggers and conditions. Backed by `&debug=true` for in-page debugging and the Inspect ML Models page for live model behavior. |
| *"Where do you test a fix before applying to Nespresso's production org?"* | **Nespresso's Coveo sandbox organization** ([docs.coveo.com/en/2959](https://docs.coveo.com/en/2959/)). Every Coveo production org comes paired with permanent sandbox orgs (usually 1-2). Coveo also releases new platform features to sandboxes before production — so they serve as early-warning for platform changes too. For our incident: test the dissociate-ML-model fix in Nespresso's sandbox first (5-10 min) before applying to production. The Critical Updates mechanism is Coveo's official sandbox-first discipline. |
| *"How do you apply fixes — do you click in the Console or use code?"* | **Coveo CLI** ([docs.coveo.com/en/cli](https://docs.coveo.com/en/cli/)) — `coveo auth:login` then `coveo org:resources:push` to apply config-as-code. Same discipline I demonstrated in the Pokémon build: every Query Pipeline rule, ML model config, IPE Python lives in a git-versioned repo · changes ship as PRs · `:push` deploys from CI/CD. Console clicks are for one-off exploration; production changes go through the CLI + PR pipeline. Coveo's CLI even supports snapshot models for selective resource pull/push. |
| *"How does what you did for the Pokémon Challenge translate to Coveo at customer scale?"* | **Directly.** Coveo's platform provides exactly the code-as-source-of-truth tooling I showed: **Coveo CLI** for resource snapshots · **organization sandbox orgs** for safe testing · **Critical Updates mechanism** for platform-change discipline · **Activity Browser + Relevance Inspector + Data Health + Log Browser** as the diagnostic toolkit · **Push/Stream API** for catalog data. The Pokémon Challenge was me practicing on a small index what Coveo's platform supports at enterprise scale. For Nespresso, my Slide 9 prevention items #6 + #7 would establish exactly this discipline. |

---

## Trim levers if running long

Total budget is ~12-13 minutes of slides. If a dry-run hits 15+ min, cut in this order:

1. **Slide 5 (verification & handback)** → fold into Slide 4 as a 3-bullet "what comes next" addendum. Save 60s.
2. **Slide 9 (structural prevention)** → drop to a 3-bullet summary instead of 5 table rows. Save 45s.
3. **Slide 6 (comms architecture)** → drop the anti-patterns box, keep just the audience matrix. Save 30s.

Total trimmable: ~135s. **Slides 0, 1, 2, 3, 4, 7, 8, 10 are immovable** — they cover the four brief items (RCA · remediation · comms · prevention) with minimum viable content.

## Presentation-day notes

- **No live demo by design** — Doc 1's Topic 2 is hypothetical. Don't overprepare visuals at the expense of the verbal narrative.
- **The hypothetical framing is critical** — open the deck with it explicitly so a panel can't trap you on *"did this happen?"* Set the expectation upfront, defend it confidently when asked.
- **Have a real anonymized incident story ready** — Q&A almost always asks *"walk me through a real one."* If you can't anonymize a true incident, the [Bhagya Rana Black Friday API postmortem](https://medium.com/@bhagyarana80/12-post-mortem-lessons-from-api-outages-at-scale-a2153cf70425) is a useful 3rd-party reference to reason through.
- **The exec-note slide (Slide 7) is a panel favorite** — they almost always ask *"can you read that out as you'd actually send it?"* Practice it aloud. It should sound natural at speaking pace.
- **Pace matters here more than in Topic 1**. The audience needs to *feel* the time pressure described in the scenario. Slow when describing technical depth; faster when reading the timeline.
- **YC Eu pronouns**: she/her. Be consistent.
- **Don't claim FDE patterns are Coveo-established practice** — frame them as *"my proposal for how the FDE role should run incidents at Coveo, drawing from industry best practices + Coveo's existing case-management infrastructure."*

## Companion docs to lean on if asked for depth

This presentation doesn't share direct artifacts from the Pokémon build (the scenario is independent), but you can cite the Pokémon work as evidence of operational discipline:

- [`docs/rga-eval-methodology.md`](../../docs/rga-eval-methodology.md) — measurement-first thinking under operational uncertainty
- [`docs/observability.md`](../../docs/observability.md) — same dashboard discipline you'd advocate for the customer
- [`rga-closed-loop/src/guardrails.py`](../../rga-closed-loop/src/guardrails.py) — production guardrail patterns (auto-rollback, etc.)

These are useful as "*here's an example of the discipline I'd bring*" references during Q&A, not in the main flow.
