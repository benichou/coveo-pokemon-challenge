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

**Visual**:
- Title: **When the platform breaks**
- Subtitle: An FDE's playbook for incident response + recovery
- A small calendar icon showing the date the scenario starts

**Speaker notes**:
- "The scenario: large customer's Coveo search is failing intermittently under peak load. Real business impact. I'm the first technical responder. Here's how the next 24 hours go."

**Key message**: this is operational, not academic.

---

## Slide 1 — The scenario (≈45s)

**Visual**: timeline showing the first 24 hours.

```
T+0       Customer's CTO posts in our shared Slack: "Search is broken in prod"
T+5min    Acknowledge in Slack + open internal incident channel
T+15min   First exec update (initial ack — see Slide 7 for template)
T+1hr     Hypothesis ranked, first remediation deployed
T+4hr     Stabilized OR continuing to mitigate
T+24hr    Post-incident review scheduled, public RCA drafted
```

**Speaker notes**:
- "I'm anchoring the whole deck against this timeline. Each subsequent slide answers what happens in one of these windows."
- "Two things matter: speed of communication and quality of diagnosis. Both fail-fast — better to be wrong publicly at T+15min and corrected at T+1hr than silent until T+4hr."

**Key message**: incident response is a time-boxed game. The clock is the adversary.

---

## Slide 2 — My first hour: the RCA playbook (≈90s)

**Visual**: 6-step checklist with timing.

| # | Check | Where | Time-box |
|---|---|---|---|
| 1 | Open Coveo Admin Console — Activity Browser | Source rebuild status, recent failures | 2 min |
| 2 | Open Watchtower / Coveo platform status page | Region-level incidents | 1 min |
| 3 | Open the customer's APM (Datadog / NewRelic / equivalent) | Search-API latency percentiles vs baseline | 5 min |
| 4 | Pull recent Query Pipeline rule changes | Last 7 days, ordered by date | 5 min |
| 5 | Pull recent ML model retrains | Last 7 days | 3 min |
| 6 | Pull the customer's own deploy log | Frontend + backend, last 48h | 5 min |

**Speaker notes**:
- "Six checks in 20 minutes. Each one rules in or out a category of cause."
- *(1+2)* "First two are Coveo-side: is OUR platform healthy? Activity Browser + Status Page give the answer in 3 minutes."
- *(3)* "APM tells me the WHERE — is latency spiking on all queries, or one segment? Errors clustered around one endpoint?"
- *(4+5)* "Two most-common Coveo failure modes are misfiring Query Pipeline rules and ML model serving issues. Both have date-ordered change logs in the Console."
- *(6)* "Last check: did the customer ship something? More than half the time the root cause is on the customer side, not ours."

**Key message**: triage is a checklist, not improvisation. The checklist is yours before the incident starts.

---

## Slide 3 — Symptoms vs root causes (≈60s)

**Visual**: 2-column table.

| What the customer SEES | What might actually be broken |
|---|---|
| "Search is slow" | API rate-limit hit · regional CDN issue · indexing backlog crowding read traffic · noisy ML scoring stage |
| "Search returns wrong results" | Recent pipeline rule activation · ART model retrain regressed · source mapping drift · query parser change |
| "RGA panel is empty / silent" | Answer config disabled · LLM provider outage · `cannotAnswer` rate spike · pipeline association removed |
| "Site has 5xx errors" | Coveo-side platform issue · customer-side proxy / WAF / API gateway · DNS · auth token rotation gone wrong |
| "Some users see X, others see Y" | A/B test misconfiguration · session-stickiness · multi-region cache divergence · search-hub mis-routing |

**Speaker notes**:
- "Customers describe symptoms. The first hour is translating those into testable hypotheses."
- "One trap to avoid: the customer's first description is often wrong because they're in panic mode. Take it seriously, but verify with telemetry before acting."

**Key message**: don't let the customer's framing of the problem narrow your hypothesis space too early.

---

## Slide 4 — Hypothesis ranking (≈75s)

**Visual**: a 2x2 grid — Likelihood (vertical) × Verification cost (horizontal).

```
                  LOW verification cost              HIGH verification cost
                  ─────────────────────────────────────────────────────────
HIGH likely   →   ★ Recent pipeline rule change      Multi-region cache split
              →     (rollback in 30 seconds)         Customer-side deploy regression
              →     ★ ML model retrain regression
              →
LOW likely    →     Source crawl backlog            Coveo platform outage
              →     API rate limit hit              DNS / network-layer issue
```

**Speaker notes**:
- "Bayesian-style. Pick the hypothesis with the highest product of likelihood × ease-to-verify."
- "Top-left quadrant is where you start. Both starred candidates have a 30-second verify path AND are the two most common Coveo failure modes."
- "Bottom-right is where you finish — only get there if everything else has ruled out. Customer-side regression is high-likelihood but expensive to verify without their engineering team in the room."

**Key message**: this is decision under uncertainty. Optimize for fast learning, not for being right first try.

**Q&A trap**: *"What if you're wrong about ranking?"* — answer: you re-rank every 15 minutes as new data comes in. The grid is a starting heuristic, not a fixed prescription. See `Slide 9` (improvement plan) on how this gets better over time.

---

## Slide 5 — Stabilization playbook (≈75s)

**Visual**: decision tree.

```
                            ┌─ YES → revert pipeline rule (30s)
              Recent rule  ─┤
              changes?     └─ NO → ─┐
                                     │
                            ┌─ YES → disable ML model (fallback to standard relevance)
              Recent ML    ─┤
              retrain?     └─ NO → ─┐
                                     │
                            ┌─ YES → page Coveo escalation engineer
              Platform     ─┤
              incident?    └─ NO → ─┐
                                     │
                                     ▼
                          Customer-side issue likely
                          → ask for deploy diff
                          → run query against staging
                          → instrument the failing query path
```

**Speaker notes**:
- "Each branch has a default action. Fast, mostly reversible."
- "First reversible: pipeline rule rollback. 30-second action, can undo. Always try this first if recent changes are suspect."
- "Second reversible: disable the ML model on the suspect pipeline. Falls back to standard relevance — degraded but functional. **Customers prefer degraded + working over premium + broken.**"
- "If neither helps and Coveo platform is fine, the cause is downstream — customer-side. From there it's about getting their engineering team in the room with full session traces."

**Key message**: most stabilization actions are **reversible**. That's a feature — you can act fast because you can undo.

---

## Slide 6 — Communication cadence (≈75s)

**Visual**: timeline with 3 audience tracks.

```
T+0       T+15min   T+30min  T+60min  T+90min  T+2hr   T+4hr    T+24hr
────────────────────────────────────────────────────────────────────────
Customer execs:    ack  ──────────┬──────────┬──────────┬──── resolved + post-mortem
                                  │          │          │      committed
                                  update     update     update
                                  (30min)    (30min)    (30min)

Customer eng:    join Slack ──────┴─continuous, technical, no spin─────

My exec chain:   page on-call ──── update at hourly ───── ── full RCA in 24h
```

**Speaker notes**:
- "Three audience tracks. Different cadence per track."
- "**Customer execs**: 15-min initial ack, then every 30 minutes until resolved. The cadence is the message — 'we're on it, you'll hear from us.'"
- "**Customer engineering**: real-time Slack. Continuous. Technical. No spin."
- "**My own leadership**: paged on first contact, hourly updates, full RCA within 24 hours."
- "The trap to avoid: silence between updates. Even 'no new information' is information at hour-1 of an incident."

**Key message**: communication is half the recovery. Cadence is what builds the trust the technical fix earns.

---

## Slide 7 — Sample exec note (≈45s)

**Visual**: actual paragraph, formatted as if it's an email or Slack post.

```
Subject: Search platform incident — initial update (T+15min)

[Customer CTO],

We're seeing intermittent failures on your search platform that started
at [timestamp]. Initial scope: [N]% of requests on the [search-hub]
pipeline are returning [error / degraded results].

Our current hypothesis: a query pipeline rule change deployed at
[timestamp] is the likely cause. We're rolling it back now — expect
confirmation within the next 15 minutes.

I'm available on Slack continuously. I'll send the next update at
[T+30min] regardless of progress.

— Franck Benichou
   Forward Deployed Engineer, Coveo
```

**Speaker notes**:
- "Eighty words. Calibrated tone."
- "Three things to notice. First, **scope quantification** ([N]%, specific pipeline) — not 'search is having issues.' Specific is credible."
- "Second, **named hypothesis + named action**. Not 'investigating' — investigating is verb. Named hypothesis is data."
- "Third, **commitment to next update on a clock**. The exec doesn't have to chase. That's how you keep them out of your way to actually fix the thing."

**Key message**: the words you put on the page during an incident matter as much as the code you push.

**Q&A trap**: *"What if your hypothesis is wrong and you've already named it?"* — answer: that's why the next-update commitment exists. Update at T+30min with the corrected hypothesis. Naming a wrong hypothesis is recoverable; silence isn't.

---

## Slide 8 — When stabilized: post-incident actions (≈60s)

**Visual**: 5 numbered items, "in the 24 hours after RESOLVED."

1. **Blameless post-mortem doc** — facts, timeline, decisions made, what we didn't know, what we'd do differently
2. **Runbook addition** — this failure mode now has a documented playbook entry; next person responds 50% faster
3. **Monitoring gap closure** — what alert SHOULD have fired earlier? Add it.
4. **Load test on the customer's staging org** — recreate the conditions, validate the fix holds
5. **Public RCA to the customer's stakeholders** — same content as internal post-mortem, executive-readable, no scapegoating

**Speaker notes**:
- "These are the deliverables. All five within 24 hours of stabilization."
- "Tone matters as much as content. Blameless internally; humble externally. Customers respect engineers who say 'we built X, X failed because Y, here's our fix for Z.'"

**Key message**: the incident's value is the prevention investment it pays for.

---

## Slide 9 — Structural prevention (longer horizon) (≈75s)

**Visual**: 5 structural changes (vs slide 8 which is tactical).

1. **SLO definition + error-budget tracking** — *"95% of queries < 500ms"* type. Once budget is exhausted, freeze releases until burn rate recovers.
2. **Change freezes** during peak windows. Black Friday, end-of-quarter, customer-specific high-traffic windows.
3. **Quarterly chaos game days** — pre-recorded customer with intentionally-staged incidents. Tests playbook + team readiness. Coveo runs these internally; can co-run with the customer.
4. **Customer-facing observability dashboard** — Grafana / Datadog public-share board. Customer can self-diagnose simple issues without paging us.
5. **Per-customer runbook ownership** — written for the customer's specific stack, reviewed in their language. Lives in their docs, not ours.

**Speaker notes**:
- "Tactical fixes from Slide 8 close the *specific* incident. Structural fixes prevent the *class* of incident."
- "SLO + error-budget is the cleanest. Once you've quantified 'acceptable failure rate', release decisions become data-driven, not vibes."
- "Chaos game days are unloved but the highest-ROI prevention investment. You learn what's actually fragile, not what you assume is fragile."

**Key message**: post-incident isn't over until structural prevention is funded + scheduled.

---

## Slide 10 — Wrap (≈30s)

**Visual**:
- *"Speed of communication. Quality of diagnosis. Discipline of prevention."*
- "Questions?"

**Speaker notes**:
- "Three things matter in this job. The first two get you through the incident. The third is what keeps you from being the one paged on the next one."
- "Open for questions."

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

## Trim levers if running long

Total budget is ~10 minutes of slides. If a dry-run hits 13 min, cut in this order:

1. **Slide 9 (structural prevention)** → drop to a 2-bullet summary. Save 60s.
2. **Slide 3 (symptoms vs causes)** → drop to a 2-row example table. Save 40s.
3. **Slide 7 (sample exec note)** → shorter visual, briefer commentary. Save 30s.

Total trimmable: ~130s. Slides 0, 1, 2, 5, 6, 8 are immovable — they answer the four core questions.

## Presentation-day notes

- **No live demo by design** — Doc 1's Topic 2 is hypothetical. Don't overprepare visuals at the expense of the verbal narrative.
- **Have a real anonymized incident story ready** — Q&A almost always asks. If you can't anonymize a true incident, use a publicly-known case (e.g., a documented Coveo customer outage from a SaaS provider's status page archive) and reason through it.
- **The exec-note slide is a panel favorite** — they almost always ask *"can you read that out as you'd actually send it?"* Practice it aloud.
- **Pace matters here more than in Topic 1**. The audience needs to *feel* the time pressure described in the scenario. Slow when describing technical depth; faster when reading the timeline.

## Companion docs to lean on if asked for depth

This presentation doesn't share direct artifacts from the Pokémon build (the scenario is independent), but you can cite the Pokémon work as evidence of operational discipline:

- [`docs/rga-eval-methodology.md`](../../docs/rga-eval-methodology.md) — measurement-first thinking under operational uncertainty
- [`docs/observability.md`](../../docs/observability.md) — same dashboard discipline you'd advocate for the customer
- [`rga-closed-loop/src/guardrails.py`](../../rga-closed-loop/src/guardrails.py) — production guardrail patterns (auto-rollback, etc.)

These are useful as "*here's an example of the discipline I'd bring*" references during Q&A, not in the main flow.
