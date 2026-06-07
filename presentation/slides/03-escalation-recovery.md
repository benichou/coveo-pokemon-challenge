---
marp: true
theme: incident-amber
paginate: true
html: true
header: '<img src="images/logos/coveo-blue.svg" alt="Coveo"><span class="hdr-cross">×</span><img src="images/logos/nespresso.svg" alt="Nespresso">'
footer: "[github.com/benichou/coveo-pokemon-challenge](https://github.com/benichou/coveo-pokemon-challenge)"
---

<!-- _class: cover -->
<!-- _paginate: false -->
<!-- _header: "" -->
<!-- _footer: "" -->

<div class="hazard-bar"></div>

<div class="logo-strip">
  <img class="logo-coveo" src="images/logos/coveo-blue.svg" alt="Coveo">
  <span class="logo-cross">×</span>
  <img class="logo-nespresso" src="images/logos/nespresso.svg" alt="Nespresso">
</div>

<div class="hypo-stamp">Hypothetical incident · public facts only</div>

# When the platform breaks

## An FDE's playbook · *Cyber Monday at Nespresso · Dec 1, 2025*

<p class="speaker"><strong>Franck Benichou</strong> · Forward Deployed Engineer candidate</p>

<div class="wordmark">NESPRESSO ANZ × COVEO · CYBER MONDAY 2025</div>

<!--
Speaker notes (cover · ~20s):

"Presentation 2 — Doc 1's operational scenario. A hypothetical search-platform
incident, anchored in a real Coveo customer."

"Honesty framing: the Nespresso × Coveo partnership is real and publicly
documented — ClickZ covered Coveo's ShopTalk 2025 co-presentation with
Nespresso's e-business head. The incident itself is constructed. To my
knowledge no incident like this has happened publicly at Nespresso."

"Second honesty note: the FDE role I depict bends Coveo's actual FDE job
description, which centres on prototype building and use-case validation.
Coveo's documented case-management process puts the Support Manager in
formal case ownership. The deck shows how an embedded FDE would plug INTO
that machinery and add deep customer-specific technical fluency — not
replace the Support Manager's formal role."

"Twelve minutes of slides · fifteen minutes of Q&A. Four sections:
diagnosis · stabilization · communications · prevention."

Key message: real customer · real partnership · constructed incident ·
honest framing about the role bend.
-->

---

<!-- _class: scenario -->

# The scenario · Cyber Monday at Nespresso ANZ

<p class="moment">Dec 1, 2025 · 9:00 AM AEDT · biggest gifting day of the year</p>

<div class="scenario-split">

<div class="scenario-pane symptoms">
  <div class="pane-label">Symptoms · what's breaking</div>
  <ul>
    <li>Site search <strong>p95 latency: 200ms → 4-8s</strong></li>
    <li><strong>~8%</strong> of queries returning errors or 0 results</li>
    <li>Personalized recs regressing to generic for <strong>~75%</strong> of logged-in traffic</li>
  </ul>
</div>

<div class="scenario-pane impact">
  <div class="pane-label">Business impact · what's at stake</div>
  <ul>
    <li>Search conversion lift <strong>3:1 → 0.5:1</strong> (worse than browse)</li>
    <li><strong>~$4-6M AUD</strong> at risk over 4-hour peak window<br/><span class="dim tiny">industry benchmark · New Relic 2024 · $1M USD/hr median</span></li>
    <li>YC Eu (Head of E-Business, Nespresso Oceania) DMs me at <strong>07:47 AEDT</strong></li>
  </ul>
</div>

</div>

<div class="timeline-strip">
  <div class="tl-header">First-hour timeline · the FDE perspective</div>
  <div class="tl-row"><span class="ts">07:15</span><span class="ev">Nespresso Datadog SLO burn-rate alert · search-API p95</span></div>
  <div class="tl-row"><span class="ts">07:30</span><span class="ev">Nespresso's zero-result monitor (custom dashboard on Coveo Analytics) breaches → FDE paged</span></div>
  <div class="tl-row"><span class="ts">07:47</span><span class="ev">YC Eu DMs (informed by her ops team) — third signal, not first</span></div>
  <div class="tl-row peak"><span class="ts">09:00</span><span class="ev">PEAK HOUR · first hypothesis verified</span></div>
  <div class="tl-row"><span class="ts">11:00</span><span class="ev">Stabilized</span></div>
</div>

<!--
Speaker notes (~60s):

"Cyber Monday morning, 9 AM AEDT. Two hours before peak — the worst possible
timing. Visible enough to be obvious, late enough that we can't pre-mitigate."

"Symptoms left: p95 latency blown out 20-40× — our slowest 5% of queries
went from 200ms baseline to 4-8 seconds. ~8% of all queries returning errors
or zero results. Personalization regressing to generic for 75% of logged-in
users — that's the tell that the Sunday overnight ML retrain might be the
culprit, which sets up Slide 3's hypothesis ranking."

"Impact right: search now WORSE than browsing — Nespresso's normal 3:1
search-vs-browse conversion lift has collapsed to 0.5:1. That's a 6× swing.
The thing that's normally their biggest revenue lever has become a revenue
drag. Industry-benchmark revenue at risk is $4-6M AUD over the 4-hour peak
window — New Relic 2024 puts median retail outage cost at $1M USD per hour."

"Critical framing in the timeline: YC Eu's 07:47 DM is the THIRD signal,
not the first. Datadog fires at 07:15. Nespresso's zero-result monitor
breaches at 07:30 — important nuance: this is a custom dashboard Nespresso's
team built on top of Coveo Analytics data, not a shipped Coveo platform
alert. Coveo provides the analytics; Nespresso built the real-time
monitoring layer. If I'm doing my job, I should be in the war room BEFORE
YC Eu DMs me. If she's my first signal, monitoring is broken — and that
becomes a Slide 9 prevention item."

"As Coveo's embedded FDE I'm the Incident Commander on Coveo's side.
The 5 C's apply — Command · Control · Coordination · Communication ·
Collaboration. Critical anti-pattern: the IC does NOT debug the failure
themselves. I delegate technical work; I run coordination, decisions,
and customer-facing comms. Google SRE: 'the IC outranks the CEO during
incidents.'"

Key message: concrete stakes · real-customer scaffold · multi-source
signal detection means the FDE shouldn't first hear about it from
the exec DM.
-->

---

<!-- _class: rca -->

# My first hour · the RCA playbook

## Four checks · ~25 minutes · each rules in or out a category of cause

| # | Rules in / out | Check (Nespresso-specific) | Where | Time |
|---|---|---|---|---|
| 1 | Coveo-side recent changes | `Activity Browser` audit (last 7d) + Coveo Status Page · Friday Cyber Monday rule + Sunday ML retrain(s) visible w/ **model name** + timestamp + author | Coveo Admin Console | ~5 min |
| 2 | Coveo vs Nespresso stack + rate-limit | search-API p95 vs Sunday baseline · errors clustered by query type · **HTTP status-code breakdown (429s = rate-limit smoking gun)** · spike at 07:15 (32min before exec DM) | Shared Datadog · weekly sprint dashboard | ~5 min |
| 3 | Single query path + ML serving capacity | `Relevance Inspector` (paste searchUid) · `&debug=true` execution report · `Inspect ML Models` — **iterate every model deployed on Nespresso's pipeline** for live behavior + per-model concurrency + serving latency | Coveo Admin Console | ~7 min |
| 4 | Source push + data integrity | Push/Stream API queue depth · `Data Health Overview` + `Event Browser` · `Log Browser` w/ `LogResponseBodyWhenUnsuccessful` | Sources + Data Health + Log Browser | ~7 min |

<div class="toolkit">
<div class="toolkit-label">FDE's complete Coveo diagnostic toolkit</div>
<strong>Platform health</strong> Watchtower + Status page · <strong>Resource audit</strong> Activity Browser · <strong>Per-query forensics</strong> Relevance Inspector + <code>&debug=true</code> · <strong>ML behavior</strong> Inspect ML Models + Review Model Info · <strong>Source-side</strong> Log Browser + <code>LogResponseBodyWhenUnsuccessful</code> · <strong>Data integrity</strong> Data Health (Overview + Event Browser) · <strong>Programmatic ops</strong> Coveo CLI · <strong>Safe test</strong> sandbox organization
</div>

<!--
Speaker notes (~90s):

"Four checks in roughly 25 minutes. Each rules in or out one category
of cause."

"(1) Coveo-side recent changes first. The Activity Browser is Coveo's
truth — an audit log of every Query Pipeline rule, every ML model
retrain, every source mutation in the last 7 days, with the model
name, timestamp, and author of each event. The Friday Cyber Monday
rule AND any ML model that retrained overnight are visible there
by name. I check Coveo's Status Page in parallel — but I don't trust
it as the primary signal. Status pages lag actual incidents by
15-30 minutes."

"(2) Coveo stack vs Nespresso stack — AND rate-limit check. Nespresso's
Datadog is SHARED with me from the weekly sprint cadence. I don't need
access requests — I'm already in the dashboard. I can see search-API
p95 spiked at 07:15 AEDT, 32 minutes before YC Eu's DM. Critical signal
to look at here: HTTP status-code distribution of the failing queries.
If a meaningful share is HTTP 429, that's the rate-limit smoking gun —
Nespresso is exceeding their Coveo Care plan's QPS ceiling at peak.
This row IS the FDE differentiator. A generalist SRE would be setting
up access at T+10min; I'm already three checks deep."

"(3) Per-query deep-debug AND ML serving capacity. The deepest tool in
Coveo's surface is the Relevance Inspector — paste the searchUid from
a failing query and see the entire query journey: parameters before AND
after the pipeline, which pipeline routed it, all ranking expressions
applied. Backed by &debug=true for in-page debugging and Inspect ML
Models. Critical discipline here: I don't assume which ML models
Nespresso has deployed — I iterate Inspect ML Models for every model
on their pipeline and check each one's behavior, concurrency, and
serving latency. For a commerce customer at this scale I'd expect to
find ART, SE, Recommendations, Query Suggest, RGA, and Passage
Retrieval all present, but I confirm the inventory first instead of
guessing. That iteration is also what distinguishes 'this model's
output got worse' (retrain regression) from 'this model's serving
pool is overloaded' (serving saturation) — same symptom, different
fix, same diagnostic surface."

"(4) Source push + data integrity. Multi-tool check: Push/Stream API
queue depth · Data Health Overview for validation errors · Event Browser
for late or malformed events · Log Browser with LogResponseBodyWhenUnsuccessful
enabled to capture source error bodies. Worth noting: there's no native
'Coveo for Adobe Commerce' connector. Nespresso pushes catalog data via
Coveo's Push/Stream API to a Catalog source — same integration pattern
as commercetools."

"Before I commit to a root cause, I do a fifth check verbally — did
Nespresso ship anything in the last 48h? Cyber Monday campaign config
could have introduced a frontend regression that bleeds back to the
search-API. That's a 5-minute verbal check with their eng team, no
Coveo tool involved. Half of customer incidents have a customer-side
root cause."

"Triage is a checklist, not improvisation. The FDE's checklist is
informed by knowing Nespresso's specific stack AND Coveo's platform
diagnostic toolkit by name — Activity Browser, Relevance Inspector,
Data Health, Log Browser. A generalist SRE couldn't do this."

Key message: by-name fluency with Coveo's diagnostic surface IS the FDE
differentiator.
-->

---

<!-- _class: hypo -->

# Hypothesis ranking · cheap-to-verify first

## Six competing root causes · two starred · all parallelizable

<div class="hypo-grid">

<div class="axis-corner"></div>
<div class="axis-top">Low verification cost</div>
<div class="axis-top">High verification cost</div>

<div class="axis-left">High likelihood</div>

<div class="hypo-cell-stack">

<div class="hypo-cell starred compact">
  <div class="h-title">Query Pipeline rule misfire</div>
  <div class="h-meta">Friday's Cyber Monday rule · most recent change · #1 Coveo failure mode</div>
  <div class="h-action">→ rollback ~30 sec via Activity Browser</div>
</div>

<div class="hypo-cell starred compact">
  <div class="h-title">Per-org QPS rate-limit ceiling</div>
  <div class="h-meta">5-7× traffic exceeds Coveo Care plan's negotiated QPS allocation · token-bucket overflow → 8% intermittent HTTP 429 (matches symptom pattern exactly)</div>
  <div class="h-action">→ check HTTP 429 share in Activity Browser + Datadog · CSM lifts quota in ~15 min</div>
</div>

</div>

<div class="hypo-cell-stack">

<div class="hypo-cell compact">
  <div class="h-title">Cache TTL alignment under spike</div>
  <div class="h-meta">cache keys expire together at TTL boundary · thundering herd → origin overload · industry-known peak-event pattern</div>
  <div class="h-action">→ requires cache flush to verify · risky during peak</div>
</div>

<div class="hypo-cell compact">
  <div class="h-title">ML behavior anomaly · deployed models</div>
  <div class="h-meta">First inventory Nespresso's deployed models via <code>Inspect ML Models</code> (commerce stack typically: ART · SE · Recs · QS · RGA · PR). Two sub-causes share same surface: (a) Sunday retrain regression — ART is top suspect (retrains on per-customer UA) · (b) ML serving saturated under 5-7× concurrency</div>
  <div class="h-action">→ dissociate the affected model ~2 min · if serving-saturated, Coveo scales ML pool</div>
</div>

</div>

<div class="axis-left">Low likelihood</div>

<div class="hypo-cell">
  <div class="h-title">DNS · TLS · endpoint reachability</div>
  <div class="h-meta">Coveo org-subdomain TLS · ANZ → Coveo DNS resolution · CDN ↔ Coveo handshake · 8% intermittent argues against (DNS usually 100% failure) — but always verify it's not DNS</div>
  <div class="h-action">→ <code>curl -v</code> + <code>dig</code> from ANZ region · ~60 sec total</div>
</div>

<div class="hypo-cell">
  <div class="h-title">Coveo platform sub-region issue</div>
  <div class="h-meta">Status page says OK · but status pages lag actual incidents by 5-30 min · last resort only</div>
  <div class="h-action">→ page Coveo Platform Eng on-call · internal <code>#platform-eng</code> Slack · keep Support Manager looped in</div>
</div>

</div>

<!--
SPOKEN (~80s):

"Six competing hypotheses, ranked on two axes. Two are starred —
high-likelihood AND cheap to verify. I run those two in parallel."

"★ The Friday Cyber Monday Query Pipeline rule — most recent change,
#1 Coveo failure mode, 30-second rollback via Activity Browser."

"★ Per-org QPS rate-limit ceiling. At 5-7× peak traffic we may be
exceeding Nespresso's negotiated QPS allocation on their Coveo Care
plan. Token-bucket overflow produces exactly the 8% intermittent
HTTP 429 pattern we're seeing. Verification is fast — HTTP status-code
distribution check in Activity Browser + Datadog. Mitigation goes
through CSM: lift the quota for the peak window, ~15 minutes."

"Top-right: cache TTL alignment — the classic thundering-herd pattern.
High likelihood, but verification means flushing cache which makes
things temporarily worse at peak."

"Top-right also: ML behavior anomaly across Nespresso's deployed
models. Important discipline here — I don't assume which models
Nespresso has running. I'd inventory them first via Inspect ML
Models. For a commerce customer at this scale I expect to find ART,
SE, Recommendations, Query Suggest, RGA, and Passage Retrieval —
but I verify, not guess. Then two possible sub-causes share the
same diagnostic surface across all those models: either Sunday's
retrain on one of them regressed on a novel Cyber-Monday query mix
(ART is the top suspect because it's the one that retrains on
per-customer UA data), OR ML serving itself is saturated under 5-7×
concurrency, which would affect any model. The fix differs by
sub-cause: retrain regression → dissociate the affected model in
2 minutes. Serving saturation → Coveo scales the ML serving pool.
Note: Coveo doesn't have a 'rollback to previous model' button —
dissociate IS the documented mechanism."

"Bottom-left: DNS, TLS, endpoint reachability — the canonical SRE
rule-out. Symptom pattern argues against it (8% intermittent doesn't
fit DNS failure), but it's a 60-second `curl -v` + `dig` check.
Always verify it's not DNS."

"Bottom-right: Coveo platform sub-region. Last resort. I escalate
INTERNAL to Coveo Platform Engineering via #platform-eng Slack, not
the customer-facing Support hotline — but I loop in the Support
Manager because they own the formal case record."

"Closing discipline: re-rank every 15 minutes as data arrives. The
grid is a heuristic, not a fixed prescription — if I verify hypothesis
A false at T+15, the grid re-balances and B moves up. Two starred =
cheap AND high-likelihood, both run in parallel, not sequentially.
Wrong-and-corrected at T+30 is better than 'still investigating' at
T+60."

Key message: don't let customer framing narrow your hypothesis space ·
prioritize fast learning over being right first try.

---

Q&A BACKUP — deeper explanations to deploy if asked

Q: "What's a 'thundering herd at TTL boundary'?"
A: "Caching saves query results so the next identical query returns in
   5ms instead of 200ms. Each entry has a TTL — usually 1-5 min — then
   it expires and gets recomputed. Under normal traffic, ~5-10% of
   entries are expiring at any moment, the miss rate is steady. The
   failure mode: during peak warm-up, lots of new entries get created
   in a short window — Cyber Monday gift queries, capsule-pod bundles,
   etc. They all share the same TTL. Thirty minutes later they ALL
   expire within seconds of each other. Cache hit-rate collapses from
   85% to 5%. Origin starts handling 17× normal traffic, times out,
   clients retry, retries pile on origin — cascade failure. Industry
   name: cache stampede. Macy's, Lowe's, Best Buy all have public
   postmortems naming this exact mechanism."

Q: "Why is DNS/TLS hard to verify at peak?"
A: "It's not — that's the point, it's actually the EASIEST. 60 seconds
   total. `dig <orgId>.org.coveo.com` from the ANZ region shows what
   IP DNS resolves to. `curl -v` against the same URL shows every step
   of the TLS handshake — cert issuer, expiry, cipher, response code.
   If either is broken, you see it instantly. We rank it low-LIKELIHOOD
   because DNS/TLS failures usually cause 100% breakage, not 8%
   intermittent. But the SRE meme is 'it's always DNS' for a reason —
   every senior engineer has burned hours chasing a complex hypothesis
   that turned out to be a cert renewal."

Q: "What's a Coveo platform sub-region issue, and why escalate internal?"
A: "Coveo's platform runs in multiple AWS regions globally. Nespresso
   ANZ's traffic routes to ap-southeast-2 (Sydney). A sub-region issue
   is a fault affecting that geographic deployment specifically — AWS
   availability zone event, regional load-balancer misconfiguration, a
   Sydney-specific shard saturating. The Coveo Status Page might still
   say 'operational' because status pages lag actual incidents 5-30
   minutes — humans confirm and assess customer impact before publishing.
   Internal escalation: I'm inside Coveo, so I page Platform Engineering
   directly via PagerDuty + post in #platform-eng Slack. An engineer
   touches the problem in 5 minutes vs 30-60 via the external Support
   hotline route. But the Coveo Support Manager stays looped in — they
   formally own the case record, SLA accountability, and customer-
   comms continuity. Faster technical response, same organizational
   discipline."

Q: "What if you're wrong about your ranking?"
A: "Re-rank every 15 minutes. Wrong-and-corrected at T+45 is more
   useful than 'still investigating' at T+60."

Q: "Why isn't the Push/Stream API queue lag in this grid?"
A: "The 90-min Sunday delay is a diagnostic check on Slide 3 (Row 4,
   Source push + data integrity), not an active hypothesis here. By
   peak hour the queue has had 12+ hours to drain. If Data Health
   still shows late or malformed events at T+0 diagnosis, I'd add it
   as a 6th hypothesis."
-->

---

<!-- _class: tracks -->

# Immediate stabilization · parallel tracks

## Top hypotheses mitigated in parallel · per-track analysis automated by spawning Claude subagents · all reversible · tracked as Jira + GitHub PR

<div class="clock-strip">
  <span>T+0min</span><span>T+15min</span><span>T+30min</span>
</div>

<div class="track red">
  <div class="track-bar"></div>
  <div class="track-body">
    <div class="track-title">TRACK A · Query Pipeline rule rollback ★</div>
    <div class="track-jira"><strong>JIRA</strong> CVO-SUP-NES-CM01-A · git revert PR linked · Coveo FDE owner</div>
    <div class="track-steps">Revert Friday's Cyber Monday rule via <code>Activity Browser</code> → verify in Activity Browser → measure zero-result rate. <strong>Fastest reversible action</strong> · ~5 min end-to-end.</div>
  </div>
</div>

<div class="track amber">
  <div class="track-bar"></div>
  <div class="track-body">
    <div class="track-title">TRACK B · CSM lifts per-org QPS quota ★</div>
    <div class="track-jira"><strong>JIRA</strong> CVO-SUP-NES-CM01-B · Coveo CSM owner · Coveo FDE escalates</div>
    <div class="track-steps">Page Coveo CSM + Account Manager → temporarily raise Nespresso's QPS ceiling for the peak window. <strong>~15 min end-to-end</strong> · Coveo platform supports this as a documented operational lever for peak events.</div>
  </div>
</div>

<div class="track blue">
  <div class="track-bar"></div>
  <div class="track-body">
    <div class="track-title">TRACK C · Troubleshoot deployed ML models</div>
    <div class="track-jira"><strong>JIRA</strong> CVO-SUP-NES-CM01-C · Coveo FDE + Coveo Eng owner</div>
    <div class="track-steps">Iterate <code>Inspect ML Models</code> across Nespresso's deployed models (ART · SE · Recs · QS · RGA · PR) · check serving latency · per-model concurrency · retrain quality. <strong>Branch fix</strong> based on finding: <em>output regression</em> → dissociate offending model ~2 min (falls back to baseline) · <em>serving saturation</em> → Coveo scales ML pool.</div>
  </div>
</div>

<div class="track green">
  <div class="track-bar"></div>
  <div class="track-body">
    <div class="track-title">TRACK D · Edge throttling at Nespresso CDN</div>
    <div class="track-jira"><strong>JIRA</strong> NES-INC-2025-CM01-D · Nespresso eng owner · their PR · <em>defense-in-depth</em></div>
    <div class="track-steps">Rate-limit search-API at CDN edge · protect upstream · buys 15 min to verify A, B, C. Doesn't fix root cause — prevents cascade.</div>
  </div>
</div>

<div class="principle">
<strong>Mitigation BEFORE RCA</strong> (Google SRE) · <em>"Customers don't care whether or not you fully understand the cause; they want to stop receiving errors."</em>
</div>

<!--
Speaker notes (~90s):

"Four parallel tracks for the top hypotheses from the previous slide.
All four run concurrently — we don't serialize. Both starred
hypotheses (Track A + Track B) get a direct mitigation. The third
starred hypothesis class — ML behavior — gets a troubleshooting track
that branches on what's found. The fourth is defense-in-depth."

"Critical discipline up front: each track is a JIRA TICKET BEFORE it
executes. No ad-hoc work. Owner named · status visible · linked to
the master incident ticket and to the GitHub PR or config commit
that ships the fix. Tracks A and C are git revert / config-flip PRs.
Track B is a CSM action (no code commit but a logged Jira change).
Track D is Nespresso's eng team's PR on their CDN config. Every
action traces to a ticket and most trace to a commit."

"Track A — Query Pipeline rule rollback. Most-suspected hypothesis,
fastest reversible action. Revert the Friday Cyber Monday rule via
the Activity Browser, verify in Activity Browser, measure zero-result
rate. About 5 minutes end-to-end. If the rate drops, we have our
answer in one of the four tracks."

"Track B — CSM lifts the per-org QPS quota. This is the new starred
hypothesis from Slide 4. If we're hitting Nespresso's negotiated QPS
ceiling at 5-7× peak traffic, lifting the quota temporarily is the
documented Coveo operational lever for peak events. About 15 minutes
end-to-end — the FDE escalates, the CSM + Account Manager execute
the raise. This is a track the customer didn't know to ask for."

"Track C — troubleshoot deployed ML models. This is the inventory-
first discipline carried into the mitigation phase. I don't presume
which model is misbehaving — I iterate Inspect ML Models across
every model on Nespresso's pipeline. For a commerce customer at this
scale I expect ART, SE, Recommendations, Query Suggest, RGA, and
Passage Retrieval all deployed — I verify, not guess. Two findings
branch to two different fixes: if a model's OUTPUT regressed
(retrain learned wrong), I dissociate it — ~2 min Console action,
falls back to baseline relevance. Important Coveo note: there's no
'rollback to previous model' button — dissociate IS the documented
mechanism. If a model is SERVING-saturated under 5-7× concurrency,
the fix isn't dissociation — it's Coveo engineering scaling the
ML serving pool. Same diagnostic surface, different fix, decision
made based on what Inspect ML Models shows."

"Track D — edge throttling at Nespresso CDN. Defense-in-depth. Doesn't
map to a hypothesis; it's a 'protect upstream while we verify A, B,
C' move. Nespresso eng owns the action — rate-limit their CDN edge
to keep the request rate just below the new QPS ceiling. Buys us 15
minutes of breathing room. Reversible — they unflip it as soon as
A/B/C lands."

"All four tracks are reversible — if I'm wrong on any, I undo in
under a minute or two. Speed WITHOUT irreversibility. I document
decision rationale even if a track turns out wrong: 'Rolled back the
Friday rule at 08:02 AEDT because it was the most recent change AND
cheapest to verify, even though we weren't 100% sure.' Post-mortem
context > silent action."

"On automation — what 'spawning Claude subagents per track' actually
looks like in this scenario. I spawn four subagents in parallel, one
per track. Subagent A reads the Activity Browser audit, identifies
the Friday rule plus any Sunday model retrains, and drafts the
revert PR. Subagent B pulls HTTP status-code distribution from
Datadog and the Coveo Activity Browser, computes the 429 share, and
drafts the Coveo-internal CSM escalation message. Subagent C
iterates Inspect ML Models across every deployed model on Nespresso's
pipeline and reports per-model serving latency, concurrency
saturation, and retrain quality. Subagent D drafts the Nespresso
CDN throttling config — which the FDE then forwards to Nespresso
eng for their PR. Each subagent is read-only on Coveo production;
every write goes through the FDE with human-in-loop review. Same
Claude Code subagent pattern I used to build the Pokémon Challenge —
direct tooling bridge from Topic 1."

"Code-as-source-of-truth bridge to Topic 1: for the most-reversible
actions during a $5M-at-risk SEV1, we might skip the sandbox gate.
For less-reversible ones we test in Nespresso's Coveo sandbox first —
5-10 min — then apply to prod via Coveo CLI snapshot push. Same
discipline I shipped for the Pokémon build (config/ + scripts/ +
bootstrap.sh). Coveo's platform supports it natively at enterprise
scale — it's just usually not activated."

Key message: parallelize the top hypotheses · every action = ticket +
PR or CSM-driven · all reversible · code-as-source-of-truth bridges
to the Pokémon build.
-->

---

<!-- _class: verify -->

# Verification & handback · don't walk away too soon

## Stabilization has three phases · the FDE doesn't release until the customer's team is verbally confident

<div class="verify-steps">

<div class="v-step amber">
  <div class="v-header">Step 1</div>
  <div class="v-title">Fix is holding</div>
  <div class="v-clock">T+30 to T+60</div>
  <ul>
    <li>Zero-result rate &lt; 2% baseline</li>
    <li>Search-API p95 &lt; 500ms</li>
    <li>Conversion lift restored (search vs browse)</li>
    <li>Personalization rendering for logged-in users</li>
  </ul>
</div>

<div class="v-step green">
  <div class="v-header">Step 2</div>
  <div class="v-title">Hold through peak</div>
  <div class="v-clock">T+60 to T+4hr</div>
  <ul>
    <li>No degradation as traffic ramps to peak</li>
    <li>Joint Coveo + Nespresso eng in shared Slack Connect</li>
    <li>Cache hit rate trending healthy</li>
    <li>Watch for relapse · most failures happen here</li>
  </ul>
</div>

<div class="v-step blue">
  <div class="v-header">Step 3</div>
  <div class="v-title">Handback to normal ops</div>
  <div class="v-clock">T+4hr</div>
  <ul>
    <li>Step 1 metrics held 3+ hrs through peak</li>
    <li>YC Eu's team verbally confident</li>
    <li>Post-incident review scheduled (T+24hr)</li>
    <li>War room channel transitioned to read-only</li>
  </ul>
</div>

</div>

<div class="handoff-note">
<strong>The 16-hour timezone problem</strong> · Nespresso ANZ is UTC+11 · Coveo Montréal is UTC-5. If the incident persists past Nespresso's end-of-day, the IC role must hand off — structured pinned summary · verbal transfer <em>"You're now the Incident Commander, okay?"</em> per Google SRE · call recording for context · pre-positioned regional FDE on-call. <strong>Slide 10 Item 5: geographic FDE distribution</strong> · not "more Montréal FDEs."
</div>

<!--
Speaker notes (~60s):

"Stabilization isn't 'pushed a fix and walked away.' Three phases."

"Step 1 — the first 30 minutes after the fix lands. Does the data say
it worked? Four measurable metrics, each one the mirror of a symptom
or impact we saw on the scenario slide. If any one is failing, restart
from Slide 4 with a refined hypothesis."

"Step 2 — the harder phase. Holding through peak. We're still in the
war room watching dashboards for 4+ hours. MOST relapses happen here —
the cache warms up wrong, the freed pipeline reveals a second
regression, traffic crests just slightly higher than the verification
window covered."

"Step 3 — handback. When do I release the customer's team to normal
operations? When metrics have held for 3+ hours through the peak AND
YC Eu's team verbally confirms confidence. Verbal handoff matters. Paper
handoff doesn't — people slip back into 'still on edge' if nobody says
'we're good.'"

"The 16-hour timezone note is critical. If the incident extends past
Nespresso's end-of-day (7pm AEDT = 3am EST Montréal), the IC role has
to hand off cleanly. Google SRE's discipline: structured pinned summary
· verbal transfer with explicit 'You're now the Incident Commander,
okay?' · call recording for context. Anti-pattern: midnight handoff
to a region without coverage. This is exactly why Slide 10 Item 5 —
24/7 regional FDE rotation — is structurally important. Not 'more
Montréal FDEs.' Geographic distribution so Nespresso ANZ always has
a daylight-time FDE on call."

Q&A trap: 'How long do you stay in the war room?' Answer: 'Until the
customer's team is verbally confident AND we've held through peak.
Premature exit is the most common FDE failure pattern.'

Key message: stabilization has 3 phases · verbal handoff matters ·
relapse during peak is the failure mode to watch for.
-->

---

<!-- _class: comms -->

# Communication architecture · plug into existing channels

## Five audiences · five channels · five cadences · FDE in hub-and-spoke position

| Audience | Channel | Cadence | What goes there |
|---|---|---|---|
| **Coveo war room** (internal) | `#inc-nespresso-cm2025-search` Slack | Real-time | Diagnosis · technical detail · decisions |
| **Nespresso tech team** | **Shared Slack Connect** (from weekly sprint cadence) + phone bridge | Real-time | Tactical updates · joint action · paste logs |
| **YC Eu + her execs** | Email + Slack Connect | **Every 30 min hot · hourly stabilizing** | Calibrated status · always names next update time |
| **Coveo internal leadership** | `#incident-updates` broadcast | Per milestone | Visibility for Technical Success Director · SVP Customer & Value Engineering · Chief Customer Success Officer · doesn't interrupt war room |
| **Nespresso wider org** | Routed via YC Eu (we don't go around her) | She decides | Single point of contact discipline |

<div class="anti-patterns">
<span class="ap-label">Anti-patterns to avoid</span>
<ul>
  <li>Silent gaps &gt; 30 min during hot phase (silence breeds exec drive-bys)</li>
  <li>Fake ETAs · use <em>"unknown"</em> + commit to next update time</li>
  <li>Split-brain · Zoom war room + Slack thread with no single source of truth</li>
  <li>War room staying open after the incident is over</li>
</ul>
</div>

<!--
Speaker notes (~90s):

"Five audiences · five channels · five cadences. The architecture puts
the FDE in a hub-and-spoke position — I'm in the Coveo war room AND in
the Nespresso shared channel AND writing to YC Eu directly. That's the
integration value of an embedded role."

"Honesty framing: the FDE function is new at Coveo, so this isn't
inherited from an existing FDE-led incident playbook. I'm drawing from
2026 industry best practices — incident.io, PagerDuty, Atlassian
Statuspage, Rootly — and proposing an FDE-appropriate architecture that
plugs INTO Coveo's existing Support Manager-led case management,
rather than replacing it."

"The 30-min cadence to YC Eu is the most important discipline. The
cadence IS the message — 'we're on it, you'll hear from us at X, even
if X is unknown still.' Industry best practice is that the cadence
commitment itself defuses panic, not the content of each update."

"Single point of contact is critical. We don't email her CMO or COO
directly — YC Eu controls her own org's narrative. We feed her, she
distributes."

"Worth noting: the shared Slack Connect channel with Nespresso ANZ
already exists from the weekly sprint cadence — public from the
ClickZ ShopTalk 2025 coverage. So coordination starts at T+0, not
at the moment of incident detection. It's a small but real benefit
of the embedded engagement model."

"Anti-patterns from industry research (incident.io 2026 + Rootly):
silent gaps > 30 min during the hot phase breed executive drive-bys
and customer churn. Fake ETAs erode trust faster than 'unknown' +
commit to next update. Split-brain communication — Zoom war room
running in parallel with Slack threads but no single source of truth —
is one of the most-cited postmortem causes of mishandled incidents."

Key message: communication is half the recovery · cadence builds the
trust the technical fix earns · the embedded relationship is the
unique comms advantage.
-->

---

<!-- _class: exec-note -->

# Sample exec note · T+15min · written under pressure

## ~140 words · scope quantified · hypothesis named · next update time committed

<div class="note-row">

<div class="email-frame">
  <div class="email-header">
    <div><span class="h-label">To:</span> YC Eu &lt;yc.eu@nespresso.com&gt;</div>
    <div><span class="h-label">Cc:</span> Coveo Support Manager · Coveo CSM</div>
    <div><span class="h-label">Subject:</span> <span class="h-subject">[INCIDENT] Search platform · T+15min · 08:02 AEDT</span></div>
  </div>
  <div class="email-body">
    <p>YC,</p>
    <p>We're seeing intermittent search failures at Nespresso ANZ that started <strong>~07:15 AEDT</strong>. Initial scope: <strong>~8% of search queries</strong> are returning errors or zero results, and personalized recommendations are regressing to generic for logged-in users. Estimated impact: search conversion lift dropping from your <strong>3:1 baseline toward 0.5:1</strong>.</p>
    <p>Top two hypotheses right now: <strong>(1)</strong> the Friday Cyber Monday query pipeline rule misfiring, <strong>(2)</strong> we may be hitting your contracted Coveo throughput ceiling at this traffic level. <strong>Both are cheap to verify</strong> — we're rolling back the rule and engaging Coveo's CSM to temporarily raise your throughput ceiling, in parallel. Expect confirmation in the next 15 min.</p>
    <p>Nespresso eng is in the shared Slack Connect channel with me.</p>
    <p><strong>Next update: 08:32 AEDT regardless of progress.</strong></p>
    <p class="signoff">— Franck Benichou<br/>Forward Deployed Engineer · Coveo</p>
  </div>
</div>

<div class="annotations">

<div class="anno">
  <div class="anno-quote">"~8% · ~07:15 AEDT · 3:1 → 0.5:1"</div>
  <div class="anno-text"><strong>Scope quantification</strong> · specific is credible · forwardable to her CMO</div>
</div>

<div class="anno">
  <div class="anno-quote">"Top two hypotheses (1) + (2)"</div>
  <div class="anno-text"><strong>Named hypothesis is data, not vibes</strong> · wrong is recoverable, silent isn't</div>
</div>

<div class="anno">
  <div class="anno-quote">"Both cheap to verify"</div>
  <div class="anno-text"><strong>Signals discipline</strong>, not random fixes</div>
</div>

<div class="anno">
  <div class="anno-quote">"Next update: 08:32 AEDT regardless"</div>
  <div class="anno-text"><strong>Commitment to a clock</strong> removes <em>"is he ignoring us?"</em> anxiety</div>
</div>

<div class="anno">
  <div class="anno-quote">No fake ETA on resolution</div>
  <div class="anno-text"><strong>Trust-preserving honest uncertainty</strong> · industry standard</div>
</div>

</div>

</div>

<!--
Speaker notes (~60s):

"About 140 words. Calibrated tone. Written to YC Eu specifically —
first-name basis because we work weekly. CC's the Coveo Support
Manager and CSM so the institutional record is preserved — that's
important because the Support Manager formally owns case management
per docs.coveo.com/en/1489, and the CSM owns the SLA-credit
conversation that will come up later."

"Five things to notice. ONE: scope quantification. '~8% · ~07:15
AEDT · 3:1 → 0.5:1' — not 'search is having issues.' Specific
numbers are credible. They also let YC Eu forward this to her CMO
and have him understand the stakes without re-explanation."

"TWO: I name the top two hypotheses explicitly. Not 'we're
investigating' — that's a verb. Named hypothesis is data. If I'm
wrong, I correct in 30 min. Wrong-and-corrected is recoverable;
silent isn't."

"THREE: I tell her what we're doing in parallel. Two cheap-to-verify
actions, both reversible. Discipline shows."

"FOUR: I name the next update time on a clock. '08:32 AEDT regardless
of progress.' That commitment is the trust-builder. She doesn't have
to chase me, she doesn't have to chase anyone. She gets back to
running her business."

"FIVE: I don't give a fake ETA on resolution. If I said 'fixed by
09:00' and missed, I'd lose her trust for the rest of Cyber Monday.
'Unknown' + 'commit to next update' is the industry-standard
trust-preserving discipline."

Q&A trap: 'What if your hypothesis is wrong and you've already named
it?' Answer: 'That's exactly why the next-update commitment exists.
Update at 08:32 with the corrected hypothesis. Naming a wrong
hypothesis at 08:02 is recoverable; silence isn't.'

Key message: the words on the page during an incident matter as much
as the code you push.
-->

---

<!-- _class: actions -->

# Post-incident actions · within 24 hours of stabilization

## Every deliverable is a Jira ticket or GitHub PR · no tribal knowledge · no ad-hoc work

<div class="actions-row">

<div class="action-card">
  <div class="num">1</div>
  <div class="title">Blameless post-mortem · joint Coveo + Nespresso</div>
  <div class="produces"><strong>Filed as Jira ticket</strong> in both instances · facts · timeline · decisions · what we didn't know · permanent record</div>
  <div class="owner">FDE drafts · joint review</div>
</div>

<div class="action-card">
  <div class="num">2</div>
  <div class="title">Runbook addition · Nespresso ANZ playbook</div>
  <div class="produces"><strong>Markdown in customer-config GitHub</strong> + Coveo FDE pattern library (Confluence) · same pattern doesn't burn the same hours twice</div>
  <div class="owner">FDE</div>
</div>

<div class="action-card">
  <div class="num">3</div>
  <div class="title">Monitoring gap closure</div>
  <div class="produces"><strong>The alert that should have fired at 07:15</strong> is now added · Datadog SLO burn-rate + tightened zero-result alert in Nespresso's monitoring dashboard · GitHub PR</div>
  <div class="owner">Joint Coveo + Nespresso</div>
</div>

<div class="action-card">
  <div class="num">4</div>
  <div class="title">Load test on Nespresso sandbox</div>
  <div class="produces"><strong>Reproduce Cyber Monday conditions</strong> · validate fix holds · catch regressions before Boxing Day · CI-runnable</div>
  <div class="owner">Coveo engineering</div>
</div>

<div class="action-card">
  <div class="num">5</div>
  <div class="title">Public RCA to Nespresso stakeholders</div>
  <div class="produces"><strong>Executive-readable</strong> · no scapegoating · accuracy over speed · management review before publish · YC Eu shares with her CMO/COO/CEO</div>
  <div class="owner">FDE + Coveo CSM</div>
</div>

<div class="action-card">
  <div class="num">6</div>
  <div class="title">Internal Coveo product feedback</div>
  <div class="produces"><strong>File Coveo Product Jira</strong> if incident revealed platform gap · status-page lag · pause-ML-retrain control · staging-test mode for rules</div>
  <div class="owner">FDE</div>
</div>

</div>

<!--
Speaker notes (~60s):

"Six deliverables. All within 24 hours of stabilization. Every one is a
Jira ticket or GitHub PR. No ad-hoc work."

"Action 1: blameless joint post-mortem, filed as Jira tickets in both
instances — Nespresso's and Coveo's. The 'joint' is critical — Nespresso
eng team + Coveo team in the same room, going through the same data.
Builds the relationship trust that survives the next incident."

"Action 2: runbook addition. This is where the FDE earns long-term
value. Customer-specific runbook lives as Markdown in the
customer-config GitHub repo — parallel discipline to my Pokémon
Challenge docs folder. Cross-customer patterns go into the Coveo FDE
pattern library in Confluence. The same pattern doesn't burn the
same hours twice."

"Action 3: the monitoring gap. The most important question after any
incident: WHY didn't this alert at 07:15 AEDT, 32 minutes before YC Eu
had to DM me? We add the alert. The addition is a GitHub PR to the
monitoring config — tightening Nespresso's existing zero-result
dashboard on Coveo Analytics plus a new Datadog SLO burn-rate alert.
Next time, we beat the customer to the report."

"Action 4: load testing on Nespresso's Coveo sandbox organization —
sandbox is paired with every production org per docs.coveo.com/en/2959.
The test itself is code, CI-runnable, committed to a staging-test
repo. Reproducible by anyone."

"Action 5: public RCA. Tone matters as much as content. Four
disciplines I'd hold to: don't rush — accuracy over speed; management
review before publishing; audience-segmented delivery — go to
status-page subscribers only, not all customers; blameless internally,
humble externally. YC Eu will share with her CMO and CEO — write it
so she's proud to forward."

"Action 6 — the often-forgotten one. File a feedback ticket in Coveo's
internal Product Jira. The FDE is Coveo product team's eyes and ears
INSIDE the customer. Every incident reveals at least one platform gap.
If we don't file it, the product team never learns. The FDE is the
feedback loop."

"SLA credits sit in here too — quietly. Coveo Care has breach
calculations. The FDE doesn't promise credits during the incident; that
conversation belongs to Coveo CSM + Nespresso procurement during the
post-incident review."

Key message: post-incident is the highest-leverage 24h of the whole
engagement.
-->

---

<!-- _class: prevention -->

# Structural prevention · the FDE's investment proposal

## Each item is a tracked ticket · owner · priority · ETA · monthly review with Nespresso + Coveo CSM

| Ticket | Root cause / issue | Change | Owner | Priority | ETA |
|---|---|---|---|---|---|
| `CVO-FDE-NES-2025-001` | No quantified failure budget · no auto-freeze when burn-rate spikes | **Coveo SLO + error-budget** · *99% queries &lt;500ms · 99.5% non-zero* · burn-rate freezes retrains + rule changes | Coveo CSM + FDE | <span class="p1">P1</span> | 6 wks |
| `CVO-FDE-NES-2025-002` | Risky changes shipped during peak window (Friday rule + Sunday retrain landed mid-peak) | **Peak-window change freeze** · no ML retrains · no Query Pipeline rule changes · Black Friday → Boxing Day | Joint | <span class="p1">P1</span> | 2 wks |
| `CVO-FDE-NES-2025-003` | Runbook untested between incidents · response skills decay without practice | **Quarterly incident-response drill** · simulated incident run with Nespresso eng + FDE · stress-test the runbook · update gaps before next peak event | FDE | <span class="p2">P2</span> | Q1 26 |
| `CVO-FDE-NES-2025-004` | Nespresso eng can't self-diagnose · FDE-as-bottleneck on small issues | **Public-share Coveo observability dashboard** · YC Eu's team self-diagnoses simple issues without paging me | FDE | <span class="p2">P2</span> | 8 wks |
| `CVO-FDE-NES-2025-005` | 16h Montréal ↔ ANZ gap · midnight IC handoff with no coverage | **24/7 regional FDE rotation** · APAC + EMEA + Americas coverage · removes the 16h timezone single-point-of-failure | Coveo (org-level) | <span class="p1">P1</span> | Q3 26 |
| `CVO-FDE-NES-2025-006` | Sandbox drift from prod · changes deploy without safe-test gate | **Sandbox synchronization discipline** · daily `coveo org:resources:pull` from prod → sandbox · safe-test-before-deploy | FDE + Nespresso | <span class="p1">P1</span> | 4 wks |
| `CVO-FDE-NES-2025-007` | Console clicks · no PR review · no audit trail · no rollback path | **Coveo CLI + git-based deployment** · every rule, ML config, IPE Python ships through PR · CLI push from CI/CD | FDE | <span class="p1">P1</span> | 6 wks |
| `CVO-FDE-NES-2025-008` | Peak QPS exceeded contracted ceiling · mid-incident scramble for CSM | **Pre-negotiated peak-window QPS ceiling lifts** · CSM + FDE forecast peak QPS for each known event (Cyber Monday · Black Friday · Boxing Day · Valentine's) · contracted ceiling raises arranged in advance | Coveo CSM + FDE | <span class="p1">P1</span> | 4 wks |

<div class="bridge">
<strong>Items 6 + 7 = direct bridge to Topic 1</strong> · the same Coveo CLI + sandbox + version-controlled config pattern I shipped for the Pokémon Challenge (<code>config/</code>, <code>scripts/</code>, <code>bootstrap.sh</code>). <strong>Coveo's platform supports this discipline natively at enterprise scale — it just needs to be activated at the customer.</strong>
</div>

<!--
Speaker notes (~80s):

"Slide 9 was tactical — fixes the SPECIFIC incident. Slide 10 is
structural — prevents the CLASS of incident."

"Eight Jira tickets, not eight bullets. Each one has a clearly-named
root cause, an owner, a priority, an ETA, and a monthly review cadence
with Nespresso + Coveo CSM. Quarterly chaos game day measures progress
against the structural items. If a P1 item slips past ETA, escalation
via the CSM. Prevention isn't aspirational — it's tracked."

"Item 1 — SLO + error-budget. Once we've quantified 'acceptable failure
rate,' release decisions become data-driven. If the budget is
exhausted, automatic freeze of ML retrains and pipeline rule changes
until burn rate recovers."

"Item 2 — peak-window change freeze. The unloved but high-ROI move.
Nespresso doesn't ship features during Black Friday → Cyber Monday →
Boxing Day. Coveo doesn't retrain ML. Codified as a check-in-CI for
the customer-config repo — PRs blocked during the freeze window."

"Item 3 — quarterly incident-response drill. One simulated incident
per quarter, run with Nespresso eng + the FDE. We rehearse the
playbook end-to-end against a constructed scenario. We find the gaps —
steps that don't work, tools that aren't available, decisions that
take too long. We update the runbook before the next real peak event.
Best case: we discover the runbook is wrong BEFORE YC Eu DMs us in
anger."

"Item 4 — public-share dashboard. Ideally Nespresso eng can self-
diagnose 80% of issues without me. This is investment in their
independence, not job-security risk for me — the FDE who removes
themselves from the critical path of small issues is the FDE who's
free to handle the big ones."

"Item 5 — 24/7 regional FDE rotation. This is the org-level ask of
Coveo. The 16-hour timezone gap between Nespresso ANZ and Coveo
Montréal is a single-point-of-failure. Geographic distribution
removes it. 'More Montréal FDEs' doesn't solve the same problem."

"Items 6 + 7 — the bridge to Topic 1. The same Coveo CLI + sandbox +
version-controlled config pattern I shipped for the Pokémon Challenge
(config/, scripts/, bootstrap.sh). Coveo's platform supports this
discipline natively. The FDE's role at Nespresso would be to
ACTIVATE it. If they don't already have it — most enterprise
customers don't — that's the highest-ROI long-term commitment we
can make."

"Item 8 — pre-negotiated peak-window QPS ceiling lifts. This closes
the gap from Slide 4's second starred hypothesis. Mid-incident the
CSM lifts the quota (Slide 5 Track B), which works but burns ~15
minutes of peak time. Item 8 moves that conversation BEFORE the peak
event — joint forecasting between Coveo CSM, Coveo Account Manager,
and Nespresso eng for each known peak day. Contracted ceiling raises
are arranged in advance. The Cyber Monday scramble becomes a routine
calendar event with paperwork done weeks ahead."

Key message: prevention is operationalized as backlog tickets · these
eight items turn the next Cyber Monday into a non-event · items 6+7
bridge to the Pokémon build discipline · item 8 closes the QPS
hypothesis gap.
-->

---

<!-- _class: wrap -->

# Speed of communication · Quality of diagnosis · Discipline of prevention

## *Cyber Monday at Nespresso · an FDE's playbook*

<div class="qa">Questions?</div>

<div class="footnote">Hypothetical incident scenario · public Coveo × Nespresso partnership facts only</div>

<!--
Speaker notes (~30s):

"Three things matter in this job."

"SPEED OF COMMUNICATION — the cadence is the message; YC Eu didn't
have to chase me. 30-minute heartbeats during the hot phase. Named
hypothesis even when wrong; committed next-update time even when
unknown."

"QUALITY OF DIAGNOSIS — five hypotheses ranked on likelihood × cost,
two starred cheap-to-verify run in parallel, all reversible. By-name
fluency with Coveo's diagnostic toolkit — Activity Browser, Relevance
Inspector, Inspect ML Models, Data Health, Log Browser, Coveo CLI.
That's the FDE differentiator."

"DISCIPLINE OF PREVENTION — the post-mortem becomes the next runbook,
and the seven structural fixes turn the next Cyber Monday into a
non-event. Two of those seven items (CLI + git-based deployment ·
sandbox synchronization) ARE the same discipline I shipped for the
Pokémon Challenge."

"The first two get you through the incident. The third is what keeps
you from being the one paged on the next one."

"Happy to take questions — on the Nespresso scenario, on the FDE role
calibration, on how this would scale to a real Coveo engagement, or
on anything from Topic 1's Pokémon build."

Key message: closing visual bookend · panel knows it's time for Q&A.
-->

---

<!-- _class: appendix -->

# Appendix · sources (1 of 2)

## Coveo platform tooling · escalation process · operational discipline

<div class="src-row">

<div class="src-col">
<h3>Coveo escalation + case management</h3>
<ul>
<li><a href="https://docs.coveo.com/en/1489/">Case management process · docs.coveo.com/en/1489</a></li>
<li><a href="https://docs.coveo.com/en/1352/">Coveo Care · Customer Support &amp; Success Guide</a></li>
<li><a href="https://docs.coveo.com/en/1484/">Coveo Care Plans · Pro vs Enterprise</a></li>
<li><a href="https://www.fwddeploy.com/jobs/forward-deployed-engineer-fde-933b1cf2">Coveo FDE public job description · fwddeploy.com</a></li>
<li><a href="https://www.supportlogic.com/resources/case-studies/coveo-slashes-case-resolution-time-with-intelligent-routing/">Coveo × SupportLogic · −53% MTTR</a></li>
</ul>
</div>

<div class="src-col">
<h3>Coveo diagnostic toolkit</h3>
<ul>
<li><a href="https://docs.coveo.com/en/mbad0273/">Relevance Inspector</a></li>
<li><a href="https://docs.coveo.com/en/406/">Debug query info · &amp;debug=true execution report</a></li>
<li><a href="https://docs.coveo.com/en/mc2g0297/">Inspect ML Models</a></li>
<li><a href="https://docs.coveo.com/en/1894/">Review Model Information</a></li>
<li><a href="https://docs.coveo.com/en/m44f6381/">Data Health Monitoring + Event Browser</a></li>
<li><a href="https://docs.coveo.com/en/o5nb2216/">Log Browser · LogResponseBodyWhenUnsuccessful</a></li>
<li><a href="https://docs.coveo.com/en/1791/">Manage Query Pipelines · Activity log</a></li>
</ul>
</div>

<div class="src-col">
<h3>Code-as-source-of-truth (Topic 1 bridge)</h3>
<ul>
<li><a href="https://docs.coveo.com/en/cli/">Coveo CLI · main page</a></li>
<li><a href="https://docs.coveo.com/en/mape0408/">CLI · Manage organization snapshots</a></li>
<li><a href="https://docs.coveo.com/en/mbmc0091/">CLI · CI/CD pipeline pattern</a></li>
<li><a href="https://docs.coveo.com/en/2959/">Sandbox organizations</a></li>
<li><a href="https://docs.coveo.com/en/2957/">Critical Updates mechanism</a></li>
<li><a href="https://docs.coveo.com/en/2816/">Manage ML model associations · dissociate, A/B</a></li>
</ul>
</div>

<div class="src-col">
<h3>Indexing pipeline + content</h3>
<ul>
<li><a href="https://docs.coveo.com/en/1893/index-content/coveo-indexing-pipeline">Coveo Indexing Pipeline</a></li>
<li><a href="https://docs.coveo.com/en/o57a0186/">Catalog object types · Product · Variant · Availability</a></li>
<li><a href="https://docs.coveo.com/en/m9fe0471/">Coveo for Adobe (AEM, not Commerce)</a></li>
<li><a href="https://docs.coveo.com/en/1471/">Troubleshoot query error codes</a></li>
<li><a href="https://docs.coveo.com/en/1727/">ML overview + retraining</a></li>
</ul>
</div>

</div>

<!--
Speaker notes (~10s):

"First appendix — Coveo-specific references. Case management process is
the canonical doc for Coveo's escalation machinery. The diagnostic
toolkit lives across half a dozen docs pages; this is the consolidated
list. The Code-as-source-of-truth column is the direct bridge to my
Pokémon Challenge build — Coveo CLI + sandboxes + Critical Updates =
exactly the discipline I shipped in 'config/' and 'scripts/'."

Use during Q&A if asked: 'How does the CLI relate to the build?' /
'What does dissociate vs rollback mean?' / 'Where in the docs?'
-->

---

<!-- _class: appendix -->

# Appendix · sources (2 of 2)

## Industry SRE patterns · Nespresso scenario anchors · IC + war-room references

<div class="src-row">

<div class="src-col">
<h3>Incident command + war room (industry)</h3>
<ul>
<li><a href="https://sre.google/sre-book/managing-incidents/">Google SRE · Managing Incidents</a></li>
<li><a href="https://sre.google/sre-book/example-postmortem/">Google SRE · Shakespeare Search postmortem</a></li>
<li><a href="https://rootly.com/incident-response/incident-commander">Rootly · Incident Commander Guide</a></li>
<li><a href="https://coralogix.com/blog/incident-commander/">Coralogix · What is an Incident Commander</a></li>
<li><a href="https://upstat.io/blog/war-room-protocols">Upstat · War Room Protocols</a></li>
</ul>
</div>

<div class="src-col">
<h3>Communications + RCA discipline</h3>
<ul>
<li><a href="https://incident.io/blog/incident-communication-best-practices">incident.io · Incident Communication Best Practices</a></li>
<li><a href="https://www.pagerduty.com/blog/insights/why-dedicated-incident-channels-are-the-modern-standard-for-slack-based-incident-response/">PagerDuty · Dedicated Incident Channels</a></li>
<li><a href="https://www.atlassian.com/blog/statuspage/incident-communication-best-practices">Atlassian Statuspage · Incident Comms</a></li>
<li><a href="https://runframe.io/blog/incident-stakeholder-communication-templates">Runframe · 8 Incident Communication Templates</a></li>
<li><a href="https://developers.cloudflare.com/support/customer-incident-management-policy/">Cloudflare · Customer Incident Management Policy</a></li>
</ul>
</div>

<div class="src-col">
<h3>Multi-vendor + on-call + Adobe</h3>
<ul>
<li><a href="https://experienceleague.adobe.com/en/docs/commerce-operations/security-and-compliance/shared-responsibility">Adobe Commerce · Shared Responsibility</a></li>
<li><a href="https://www.pagerduty.com/blog/incident-management-response/managing-vendor-incidents/">PagerDuty · Managing Vendor Incidents</a></li>
<li><a href="https://rootly.com/blog/distributed-and-global-on-call-best-practices-for-24-7-teams">Rootly · Distributed Global On-Call</a></li>
<li><a href="https://sreschool.com/blog/follow-the-sun/">SRE School · Follow the Sun</a></li>
<li><a href="https://medium.com/@bhagyarana80/12-post-mortem-lessons-from-api-outages-at-scale-a2153cf70425">Bhagya Rana · 12 Postmortem Lessons</a></li>
</ul>
</div>

<div class="src-col">
<h3>Nespresso scenario · Cyber Monday benchmarks</h3>
<ul>
<li><a href="https://www.coveo.com/en/resources/case-studies/nespresso">Coveo case study · Nespresso</a></li>
<li><a href="https://www.coveo.com/blog/nespresso-b2c-ecommerce-search/">Coveo blog · Nespresso B2C search</a></li>
<li><a href="https://www.clickz.com/how-nespresso-is-rewriting-e-commerce-one-search-bar-at-a-time/271874/">ClickZ ShopTalk 2025 · YC Eu + Peter Curran</a></li>
<li><a href="https://www.retailtouchpoints.com/topics/personalization/nespresso-awakens-new-coffee-discovery-pathways-with-online-quiz">Retail TouchPoints · Nespresso Coffee Quiz (Monetate, NOT Coveo)</a></li>
<li><a href="https://news.adobe.com/news/2026/01/adobe-holiday-shopping-season">Adobe Analytics 2025 · Cyber Monday data</a></li>
<li><a href="https://finance.yahoo.com/news/relic-report-reveals-retailers-turning-140000838.html">New Relic · retail outage cost benchmark</a></li>
</ul>
</div>

</div>

<!--
Speaker notes (~10s):

"Second appendix — industry SRE + Nespresso scenario anchors. Google
SRE Book is the canonical incident-management reference. Cloudflare's
customer incident management policy is the gold standard for public
RCA discipline. The Nespresso scenario column is the public-source
trail for the partnership facts I cited."

Use during Q&A if asked: 'Where did the 5 C's come from?' / 'Why
Nespresso specifically?' / 'How do you know this happens at scale?'
-->
