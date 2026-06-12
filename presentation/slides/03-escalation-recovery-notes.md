# Presentation 2 — Escalation & Recovery · Rehearsal Notes

> Coaching notes for delivering `03-escalation-recovery.md` (cover + 11 content + 2 appendix = ~13 slides).
> Separate ~25-min slot: **~12 min slides + ~15 min Q&A.** Own Q&A (not shared with Pres 1).

## ⚠️ READ FIRST — what this presentation IS (and the muscle it tests)
- **Third distinct muscle.** Pres 1 Topic 1 = "what I built" (technical). Topic 2 = "what it means for a customer" (pitch). **This = "can you run an incident?"** — operational maturity, calm-under-pressure, diagnosis, communication, prevention. The panel is evaluating *judgment*, not code.
- **Scenario:** constructed Cyber Monday incident at Nespresso ANZ (Dec 1, 2025). Real Coveo×Nespresso partnership; fabricated incident.
- **Structure = 4 sections:** Diagnosis (slides 3–4) → Stabilization (5–6) → Communications (7–8) → Prevention (9–10), bookended by scenario (2) and wrap (11).

## 🚨 THE TWO HONESTY FRAMINGS — deliver BOTH on the cover, non-negotiable
1. **The incident is hypothetical.** Partnership is real + public (ClickZ ShopTalk 2025: YC Eu + Peter Curran). No known real incident like this at Nespresso.
2. **The FDE role is bent.** Coveo's real FDE job = prototype builder + use-case validator. Coveo's documented case process (docs.coveo.com/en/1489) puts the **Support Manager** in formal case ownership. **This deck shows the FDE plugging INTO that machinery — adding deep customer-specific technical fluency — NOT replacing the Support Manager.**
> Why this matters: a Coveo panel KNOWS their own FDE job description. Claiming "I'm the Incident Commander" without this caveat = overclaiming. WITH it = self-aware maturity. Say it as confidence, not apology.

## 🎯 The recurring FDE differentiator thread (the spine of the whole deck)
> **By-name fluency with Coveo's diagnostic toolkit IS what separates an embedded FDE from a generalist SRE.** Tools to name confidently: **Activity Browser** (audit log), **Relevance Inspector** (per-query forensics, paste searchUid), **`&debug=true`** (execution report), **Inspect ML Models**, **Data Health + Event Browser**, **Log Browser** (`LogResponseBodyWhenUnsuccessful`), **Coveo CLI** (snapshots/CI), **sandbox org**. A generalist would be requesting dashboard access at T+10min; the FDE is already three checks deep.

## 🌉 Bridge to Topic 1 (use it — ties the whole interview together)
Prevention items 6 + 7 (Coveo CLI + sandbox + version-controlled config) = the **exact same discipline** as the Pokémon build (`config/`, `scripts/`, `bootstrap.sh`). Also: "spawning Claude subagents per track" = same Claude Code pattern used to build Topic 1.

---

## 🎤 Cover — When the platform breaks

> ⏱️ **~25 sec.** Sets scenario + delivers BOTH honesty framings + names the 4 sections. Don't linger — but don't skip the framings.

### What's on the slide
Hazard bar · Coveo × Nespresso logo strip · "Hypothetical incident · public facts only" stamp · title "When the platform breaks · An FDE's playbook · Cyber Monday at Nespresso · Dec 1, 2025."

### What to say (~25 sec)
> "Presentation 2 — the operational scenario: a hypothetical search-platform incident, anchored in a real Coveo customer.
>
> Two honesty notes up front. **One — the partnership is real and public; the incident is constructed.** To my knowledge nothing like this has happened publicly at Nespresso. **Two — the role I depict bends Coveo's actual FDE job description**, which centres on prototype building and use-case validation, and Coveo's documented process puts the **Support Manager** in formal case ownership. So what I'm showing is how an **embedded FDE plugs INTO that machinery** and adds deep customer-specific technical fluency — not replaces the Support Manager.
>
> Twelve minutes, four sections: diagnosis, stabilization, communications, prevention."

### Why leading with the caveats is strong (not weak)
A Coveo panel will mentally check your role claim against their real job description within the first 30 seconds. **Beating them to it** signals you understand the org, respect the Support Manager's role, and aren't overclaiming. It's the same move as Topic 1's "is it really all code?" honesty — disarm the obvious objection before it's raised.

### 🎤 Delivery
- Say the two caveats **briskly and confidently** — they're table-setting, not confession. Lingering makes them sound like weaknesses.
- "Twelve minutes, four sections" = the same disciplining promise as Topic 2's "five minutes, four slides."

---

## 🎤 Slide 2 — The scenario · Cyber Monday at Nespresso ANZ

> ⏱️ **~60 sec.** Sets stakes + two judgment signals (multi-signal detection · IC discipline). Don't read every number — land the *revenue-drag* swing + the *third-signal* point.

### What's on the slide
Symptoms (p95 200ms→4–8s · ~8% errors/zero-results · personalization →generic for 75%) · Business impact (conversion lift 3:1→0.5:1 · ~$4–6M AUD at risk) · First-hour timeline (07:15 Datadog → 07:30 zero-result monitor → 07:47 exec DM → 09:00 peak → 11:00 stabilized).

### What to say (~60 sec)
> "Cyber Monday, 9 AM AEDT — two hours before peak. The worst possible timing: visible enough to be obvious, late enough that we can't pre-mitigate.
>
> The symptoms: our slowest queries blew out 20-to-40×, ~8% returning errors or zero results, personalization regressing to generic for three-quarters of logged-in users. And the impact that matters — **search is now *worse* than browsing.** Nespresso's normal 3-to-1 search-vs-browse conversion lift has collapsed to 0.5-to-1. Their biggest revenue lever just became a revenue drag — roughly $4–6M AUD at risk over the four-hour peak.
>
> But the most important thing on this slide is the **timeline**. The exec's DM at 07:47 is the **third** signal, not the first — Datadog fired at 07:15, the zero-result monitor at 07:30. **If the executive is my first signal, monitoring is broken** — and that becomes a prevention item later.
>
> My role here is **Incident Commander on Coveo's side** — and the critical discipline is that the IC does **not** debug the failure themselves. I delegate the technical work and run coordination, decisions, and customer comms. Google SRE: 'the IC outranks the CEO during an incident.'"

### The two judgment signals to land (more important than the numbers)
1. **Multi-signal detection:** *"if the exec is my first signal, monitoring failed"* — proves you think about detection, not just response. Plants the Slide 9 prevention payoff.
2. **IC doesn't debug:** delegating + holding the global picture = senior incident judgment. The most common junior mistake is the lead diving into the logs and losing coordination.

### 🧠 Q&A — slide 2
- **"What are the 5 C's?"** → *"Command, Control, Coordination, Communication, Collaboration — the incident-command framework. The IC owns all five and delegates the actual debugging."*
- **"Why doesn't the IC debug it themselves?"** → *"Cognitive load. The moment the commander is head-down in a stack trace, nobody's holding the global picture, comms go silent, and parallel tracks collide. The IC's job is decisions and coordination — the technical work is delegated."*
- **"Is the $4–6M real?"** → *"It's an industry benchmark — New Relic 2024 puts median retail outage cost around $1M USD/hr — applied to a 4-hour peak, not a Nespresso-specific figure. I'm explicit it's a benchmark, not their P&L."*
- **"Why is this timing the worst case?"** → *"9 AM is two hours before peak — too late to pre-mitigate, early enough that the damage compounds across the whole peak window."*

---

## 🎤 Slide 3 — My first hour · the RCA playbook (DENSEST SLIDE)

> ⏱️ **~90 sec.** ⚠️ **DO NOT read the 4-row table.** Name the 4 checks + what each rules in/out + the toolkit. The table is on screen so the panel can follow; your voice = the *logic*, not the cells. This slide is pure FDE-differentiator — by-name Coveo tool fluency.

### The frame (say first)
> **"Four checks, roughly 25 minutes, each one rules in or out a *category* of cause. Triage is a checklist, not improvisation — and the checklist is built from knowing Nespresso's specific stack AND Coveo's diagnostic toolkit by name. A generalist SRE couldn't run this."**

### What to say (~90 sec) — name each check + its tool + what it rules out
> "**Check 1 — Coveo-side recent changes, first.** The **Activity Browser** is Coveo's audit log — every pipeline rule, ML retrain, and source mutation in the last 7 days, with model name, timestamp, and author. Friday's Cyber Monday rule and any Sunday retrain are right there by name. I check the Status Page in parallel but don't trust it as primary — status pages lag 15-to-30 minutes.
>
> **Check 2 — Coveo stack vs Nespresso stack, and rate-limit.** Their Datadog is already shared with me from our weekly sprint cadence — no access request, I'm already in the dashboard. I look at the **HTTP status-code distribution** of the failures: if a meaningful share is **429, that's the rate-limit smoking gun** — they're exceeding their negotiated QPS ceiling at peak. This row *is* the FDE differentiator: a generalist would be setting up access at T+10; I'm three checks deep.
>
> **Check 3 — single query path and ML serving.** The deepest tool is the **Relevance Inspector** — paste the searchUid from a failing query and see the whole journey: parameters before and after the pipeline, which pipeline routed it, every ranking expression. Backed by `&debug=true` and **Inspect ML Models** — and I *iterate every model* on their pipeline, not guess, which separates 'a model's output regressed' from 'a model's serving pool is saturated.'
>
> **Check 4 — source push and data integrity.** Push/Stream queue depth, **Data Health** for validation errors, **Log Browser** with response-body logging for source errors.
>
> And a **fifth, verbal check**: did Nespresso ship anything in the last 48 hours? **Half of customer incidents have a customer-side root cause** — that's a 5-minute conversation, no Coveo tool."

### 🔧 TOOL GLOSSARY — instant one-liners (your armor; a panelist WILL probe one)
- **Activity Browser** → Coveo's audit log: every pipeline rule / ML retrain / source change in the last 7d, with name + timestamp + author.
- **Relevance Inspector** → per-query forensics: paste a searchUid, see the full query journey — params pre/post pipeline, which pipeline, all ranking expressions applied.
- **`&debug=true`** → in-page query execution report (ranking breakdown) appended to a search request.
- **Inspect ML Models** → live behavior + serving status per ML model on a pipeline; iterate it across all deployed models.
- **Data Health (+ Event Browser)** → catalog/source validation errors + late/malformed push events.
- **Log Browser + `LogResponseBodyWhenUnsuccessful`** → captures the actual error body returned by a source on failed pushes.
- **Coveo CLI / snapshots** → programmatic org config push from CI (Topic 1 bridge).
- **Sandbox org** → safe-test environment paired to every prod org (docs.coveo.com/en/2959).
- **429** → HTTP "Too Many Requests" — the rate-limit / QPS-ceiling signature.

### 🧠 Q&A — slide 3
- **"Why not trust the Status Page?"** → *"Status pages lag actual incidents 15–30 min — a human confirms and assesses customer impact before publishing. I use it as a parallel confirmation, never the primary signal."*
- **"There's a Coveo connector for Adobe Commerce, right?"** → *"No native one — Nespresso pushes catalog data via Coveo's Push/Stream API to a Catalog source, same pattern as commercetools. Worth knowing so I check the right surface."* (Sharp detail — shows you know their actual integration.)
- **"How do you tell retrain regression from serving saturation?"** → *"Same symptom, different fix — and Inspect ML Models shows both. Regressed output = the model learned wrong on a novel query mix → dissociate it (~2 min, falls back to baseline). Saturated serving = concurrency overload → Coveo scales the ML pool. There's no 'rollback to previous model' button; dissociate IS the mechanism."*
- **"Why the verbal 5th check?"** → *"Because half of incidents are customer-side. A Cyber Monday frontend config change could bleed back into the search-API. Five-minute check, no tool — and it stops me chasing a Coveo-side ghost."*

### ⚠️ Pacing
This + Slide 4 are your overtime danger zone. If you find yourself reading cells, **stop and jump to the toolkit strip** — name the tools, say "that's the FDE differentiator," and move. Wrong to over-explain here.

---

## 🎤 Slide 4 — Hypothesis ranking · cheap-to-verify first

> ⏱️ **~80 sec.** Second dense slide (6-cell grid). ⚠️ **The METHODOLOGY is the point, not the 6 hypotheses.** Lead with the two axes + the two starred ones; name the rest fast. The 6 specific causes demonstrate Coveo fluency; the *ranking discipline* is what's being graded.

### The method (say this first — it's the real content)
> **"Six competing root causes, ranked on two axes: likelihood and verification cost. The two starred ones are high-likelihood AND cheap to verify — I run those two in parallel, not sequentially. And I re-rank every 15 minutes as data arrives. The grid is a heuristic, not a fixed prescription."**

### What to say (~80 sec)
> "Six hypotheses on two axes — likelihood and cost-to-verify.
>
> **Two are starred — likely *and* cheap, so I run them in parallel.** First, **Friday's Cyber Monday pipeline rule** — most recent change, the #1 Coveo failure mode, a 30-second rollback via Activity Browser. Second, the **per-org QPS rate-limit ceiling** — at 5-to-7× traffic we may be exceeding Nespresso's negotiated QPS allocation; token-bucket overflow produces exactly the 8% intermittent 429 we're seeing. Fast to check, and the CSM can lift the quota in ~15 minutes.
>
> Top-right, high-likelihood but expensive: **cache TTL alignment** — the classic thundering-herd — and **ML behavior across their deployed models**, which I'd inventory first rather than guess; that splits into a Sunday retrain regression, with **ART the top suspect because it retrains on per-customer behavior**, versus serving saturation under concurrency.
>
> Bottom-left: **DNS, TLS, reachability** — the canonical SRE rule-out. 8% intermittent argues against it, but it's a 60-second `curl` and `dig`, so I always verify it's not DNS. Bottom-right, last resort: a **Coveo platform sub-region issue** — and there I escalate *internally* to Platform Engineering, while keeping the Support Manager looped on the formal case.
>
> The discipline: **wrong-and-corrected at T+30 beats 'still investigating' at T+60.**"

### The three judgment signals (these are what get graded)
1. **Likelihood × cost ranking** + **parallelize the two starred** — not serial guessing.
2. **Re-rank every 15 min** — the grid is a living heuristic, not a script.
3. **Don't let the customer's framing narrow the hypothesis space** — prioritize fast learning over being right first try.

### 🧠 Q&A — slide 4 (the deck even pre-stages these)
- **"What's a thundering herd at the TTL boundary?"** → *"Cache entries created together in a short window — Cyber Monday gift queries — all share the same TTL, so they expire within seconds of each other. Hit-rate collapses from ~85% to ~5%, origin suddenly handles 17× traffic, times out, clients retry, retries pile on — cascade. Industry name: cache stampede. Macy's, Best Buy have public postmortems on it."*
- **"Why rank DNS/TLS low if it's so easy to check?"** → *"Low *likelihood*, not low priority — DNS/TLS failures usually cause 100% breakage, not 8% intermittent. But it's a 60-second check and 'it's always DNS' is a meme for a reason, so I always run it."*
- **"What's a platform sub-region issue — and why escalate internally?"** → *"A fault in the geographic AWS deployment Nespresso ANZ routes to — ap-southeast-2, Sydney. The Status Page may still say 'operational' because it lags 5–30 min. I'm inside Coveo, so I page Platform Engineering directly — 5 min vs 30–60 via the external hotline — while the Support Manager keeps formal case ownership. Faster response, same discipline."*
- **"Why isn't the Push queue lag a hypothesis here?"** → *"It's a diagnostic check on the previous slide, not an active hypothesis — by peak the queue's had 12+ hours to drain. If Data Health still showed late events at T+0, I'd add it as a 6th."*
- **"What if your ranking is just wrong?"** → *"Re-rank every 15 minutes. The grid re-balances as I verify each one false."*

### ⚠️ Pacing
Same danger as slide 3. If you start narrating all six cells in detail, you'll blow 3 minutes. **Two starred + the method + the T+30 line** is the must-say; everything else is Q&A.

---

## 🎤 Slide 5 — Immediate stabilization · parallel tracks

> ⏱️ **~90 sec.** Four tracks. Lead with the principle, name the tracks, land "all reversible + every action a ticket." ⚠️ Handle the Claude-subagents line carefully (overclaim risk — see below).

### The headline principle (say it first — it's the senior signal)
> **"Mitigation before RCA. Google SRE: 'customers don't care whether you understand the cause; they want to stop receiving errors.' So I mitigate the top hypotheses in parallel — all reversible — before I've fully proven root cause."**

### What to say (~90 sec)
> "Four tracks for the top hypotheses, all running **concurrently** — we don't serialize.
>
> **Track A — roll back Friday's pipeline rule** via the Activity Browser. Most-suspected, fastest reversible action, ~5 minutes end-to-end. **Track B — the CSM lifts the per-org QPS quota** for the peak window; that's a documented Coveo operational lever, ~15 minutes, the FDE escalates and the CSM executes. **Track C — troubleshoot the deployed ML models**, inventory-first: iterate Inspect ML Models across all of them, then branch — if a model's *output* regressed, dissociate it in ~2 minutes; if it's *serving-saturated*, Coveo scales the pool. **Track D — edge throttling at Nespresso's CDN**: defense-in-depth, their eng owns it, buys 15 minutes of breathing room while A, B, and C verify.
>
> Critical discipline: **every track is a Jira ticket *before* it executes** — owner named, linked to the master incident ticket and to the PR or config commit that ships it. No ad-hoc work. And **all four are reversible** — if I'm wrong on any, I undo in a minute or two. Speed *without* irreversibility."

### ⚠️ THE OVERCLAIM RISK — the "Claude subagents per track" line
The slide mentions spawning Claude subagents per track. **A Coveo panelist could hear "you'd let AI agents loose on a customer's production during a SEV1."** Pre-empt it — say the guardrails IN the same breath:
> *"On automation — I'd spawn a subagent per track, but they're **read-only on Coveo production**. They read the Activity Browser, pull the 429 distribution, iterate Inspect ML Models, draft the revert PR or the escalation message. **Every write goes through me, human-in-the-loop.** It's the same Claude Code subagent pattern I used to *build* the Pokémon Challenge — pointed at diagnosis, not autonomous remediation."*
- **Never** imply agents auto-apply prod changes mid-incident. Read + draft only; FDE reviews/approves every mutation.
- If you're not 100% confident delivering this nuance live, **it's safe to drop the subagent mention entirely** and just say "I parallelize the analysis." The tracks stand on their own without it.

### Code-as-source-of-truth bridge (Topic 1)
> *"For the most-reversible actions during a $5M SEV1 we might skip the sandbox gate; for less-reversible ones we test in Nespresso's Coveo sandbox first, ~5-10 min, then apply to prod via Coveo CLI snapshot push. Same `config/` + `scripts/` discipline I shipped for the Pokémon build."*

### 🧠 Q&A — slide 5
- **"Why mitigate before you know the cause?"** → *"Because the customer's revenue is bleeding now, and all four actions are reversible — so the risk of acting early is tiny, and the cost of waiting for certainty is ~$1M/hr. Stop the bleeding, then confirm."*
- **"Four parallel changes during peak isn't reckless?"** → *"It would be if they were irreversible — but each undoes in 1–2 minutes, each is a ticket with an owner, and I document the rationale even when a track turns out wrong. Speed without irreversibility, not cowboy changes."*
- **"Track B — Coveo really raises QPS mid-incident?"** → *"Yes — it's a documented operational lever for peak events. The FDE escalates, the CSM and Account Manager execute the raise. Slide 10 then moves that conversation *before* the peak so it's not a mid-incident scramble."*
- **"You rolled back the rule and it wasn't the cause — now what?"** → *"Reversible — I re-apply, and I've logged *why* I tried it. The grid re-ranks and Track B or C carries it. Nothing's lost."*
- **"Dissociate vs rollback again?"** → *"There's no 'previous model' button — dissociating the model IS the documented revert; it falls back to baseline relevance."*

---

## 🎤 Slide 6 — Verification & handback · don't walk away too soon

> ⏱️ **~60 sec.** Three phases + the timezone problem. The senior signal: **premature exit is the most common FDE failure.** Land that + the verbal-handback point + the 16h timezone setup.

### The headline (counterintuitive = memorable)
> **"Stabilization isn't 'pushed a fix and walked away.' Three phases — and the most common failure pattern is leaving too soon."**

### What to say (~60 sec)
> "Three phases.
>
> **Step 1, T+30 to T+60 — is the fix holding?** Four measurable metrics, each the mirror of a symptom: zero-result rate back under 2%, p95 under 500ms, conversion lift restored, personalization rendering. If any one fails, I restart from the hypothesis grid with a refined theory.
>
> **Step 2, through peak — the harder phase.** We stay in the war room watching dashboards for 4+ hours, because **most relapses happen here** — the cache warms up wrong, a freed pipeline reveals a second regression, traffic crests just past the verification window.
>
> **Step 3, handback.** I release the customer's team to normal ops only when metrics have held 3+ hours through peak **AND YC Eu's team verbally confirms confidence.** Verbal matters — a paper handoff leaves people still on edge until someone actually says 'we're good.'
>
> And the **16-hour timezone problem**: Nespresso ANZ is UTC+11, Coveo Montréal UTC-5. If this runs past their end-of-day, the IC role has to hand off cleanly — pinned summary, an *explicit* verbal transfer, 'you're now the Incident Commander, okay?', a call recording for context. The anti-pattern is a midnight handoff to a region with no coverage — which is exactly why one of my prevention items is **geographic FDE distribution, not 'more Montréal FDEs.'**"

### The three signals to land
1. **Don't exit early** — *"premature exit is the most common FDE failure pattern."*
2. **Verbal > paper handback** — trust is social; metrics holding isn't enough until someone says it out loud.
3. **The 16h timezone gap is a structural single-point-of-failure** — plants Slide 10's regional-rotation item.

### 🧠 Q&A — slide 6
- **"How long do you stay in the war room?"** (the deck pre-stages this) → *"Until the customer's team is verbally confident AND we've held through peak. Premature exit is the most common FDE failure — the relapse usually comes during peak warm-up, after the junior instinct says 'we're done.'"*
- **"Why does verbal confirmation matter if the metrics are green?"** → *"Because trust is social, not just numeric. The customer's team stays anxious until someone with authority says 'we're good' — and that verbal close is also what lets *them* stand down their own people."*
- **"Why the explicit 'you're now the IC, okay?' phrasing?"** → *"Google SRE discipline — incidents die in the gaps when ownership is ambiguous. An explicit, acknowledged transfer means there's never a moment where nobody owns it."*
- **"Isn't a 4-hour war-room watch expensive?"** → *"Cheaper than a relapse at peak. The cost of an FDE watching dashboards for 4 hours is trivial against ~$1M/hr if it silently breaks again."*

---

## 🎤 Slides 7 + 8 — Communications (the most FDE-distinctive pair)

> ⏱️ **~90 sec (S7) + ~60 sec (S8) = ~2.5 min.** Comms-under-pressure is where the *embedded* relationship pays off — this is your strongest FDE-fit material. S7 = the architecture; S8 = the proof.

### THE governing principle (say it on S7, it carries both slides)
> **"The cadence IS the message. 'You'll hear from me at X, even if X is still unknown' defuses panic better than any status content. The customer never has to chase me."**

---

## SLIDE 7 — Communication architecture

### What's on the slide
5 audiences × 5 channels × 5 cadences, FDE in hub-and-spoke: Coveo war room (Slack, real-time) · Nespresso tech (shared Slack Connect + phone, real-time) · **YC Eu + execs (email/Slack, every 30 min hot)** · Coveo leadership (#incident-updates, per milestone) · Nespresso wider org (routed *via* YC Eu). Anti-patterns: silent gaps >30 min · fake ETAs · split-brain · war room left open.

### What to say (~90 sec)
> "Five audiences, five channels, five cadences — and the architecture puts the FDE in a **hub-and-spoke** position: I'm in the Coveo war room, in the Nespresso shared channel, *and* writing to YC Eu directly. That's the integration value of an embedded role.
>
> **Honesty note:** the FDE function is new at Coveo, so this isn't inherited from an existing FDE playbook — I'm drawing from 2026 industry best practice, incident.io, PagerDuty, Rootly, and proposing an architecture that **plugs into Coveo's Support-Manager-led case management, not replaces it.**
>
> The most important discipline is the **30-minute cadence to YC Eu during the hot phase** — the cadence itself defuses panic, not the content of any single update. **Single point of contact** is the other rule: we don't email her CMO or COO — she controls her org's narrative; we feed her, she distributes.
>
> And one embedded-model benefit: the **shared Slack Connect already exists** from our weekly sprint cadence — so coordination starts at T+0, not at incident detection."

### S7 signals to land
1. **Hub-and-spoke = the embedded-FDE value** (you're already in every channel).
2. **Cadence is the message** (the trust-builder is the rhythm, not the content).
3. **Single point of contact** (respect the exec's narrative control — and the Support Manager's formal ownership).
4. **The honesty framing** (industry best practice plugged INTO Coveo's process — same role-bend discipline as the cover).

### 🧠 Q&A — slide 7
- **"Isn't this just generic incident comms?"** → *"The architecture is industry best practice — I'm honest the FDE function is new at Coveo. What's *not* generic is the embedded position: the shared Slack Connect with Nespresso already exists from our sprint cadence, so I'm coordinating at T+0, not requesting a channel mid-incident."*
- **"Why 30 minutes specifically?"** → *"It's the interval where the cadence commitment itself keeps the exec calm — long enough to have something to say, short enough that they never wonder if we've gone dark. Hourly once stabilizing."*
- **"Why route everything through YC Eu?"** → *"She owns her organization's narrative. If we brief her CMO directly we fracture her control and create conflicting messages. We feed one point of contact; she distributes."*

---

## SLIDE 8 — Sample exec note · T+15min

### What's on the slide
A ~140-word email to YC Eu (CC: Support Manager + CSM) with 5 annotated disciplines.

### What to say (~60 sec) — walk the 5 annotations, don't read the email
> "About 140 words, written under pressure. First-name to YC Eu because we work together weekly; CC the Support Manager and CSM so the institutional record is preserved — the Support Manager formally owns the case, the CSM owns the SLA-credit conversation later.
>
> Five things to notice. **One — scope quantification:** '~8%, started ~07:15, 3-to-1 toward 0.5-to-1' — specific is credible, and she can forward it to her CMO without re-explaining. **Two — I name the top two hypotheses explicitly** — not 'we're investigating'; named hypothesis is data, and if I'm wrong I correct in 30 minutes. **Three — both are cheap to verify** — signals discipline, not random fixes. **Four — I commit to a clock: 'next update 08:32 regardless'** — she never has to chase me. **Five — no fake ETA on resolution** — 'unknown' plus a committed next-update time is the trust-preserving standard."

### The two trust-builders to emphasize
- **"Next update 08:32 regardless"** — removes the *"is he ignoring us?"* anxiety entirely.
- **"No fake resolution ETA"** — *"if I'd said 'fixed by 09:00' and missed, I'd lose her trust for the rest of Cyber Monday."*

### 🧠 Q&A — slide 8
- **"What if you named a hypothesis and you're wrong?"** (the deck pre-stages this) → *"That's exactly why the next-update commitment exists — I update at 08:32 with the corrected hypothesis. Naming a wrong hypothesis at 08:02 is recoverable; **silence isn't.**"*
- **"Why CC the Support Manager and CSM?"** → *"Institutional record. The Support Manager formally owns the case per Coveo's process; the CSM owns the SLA-credit conversation that comes up in the post-incident review. I keep them on the thread from minute 15."*
- **"Why first-name / informal tone?"** → *"Because we have a real weekly working relationship — that's the embedded model. Formality would read as distance at exactly the moment she needs to feel I'm on it."*

### ⚠️ This pair is your FDE-fit showcase — slow down slightly
Diagnosis slides prove you're technical; *these* prove you can hold a customer relationship under fire. Deliver them with calm authority — they're where a pre-sales/FDE panel decides "I'd put this person in front of my customer."

---

## 🎤 Slides 9 + 10 — Prevention (+ the Topic 1 bridge)

> ⏱️ **~60 sec (S9) + ~80 sec (S10) = ~2.5 min.** The framing: **S9 fixes THIS incident (tactical); S10 prevents the CLASS of incident (structural).** S10 items 6+7 are where the whole interview ties together.

### The governing contrast (say it bridging into S9)
> **"Everything so far fixed the specific incident. Prevention is where the FDE earns long-term value — and I operationalize it as backlog tickets, not good intentions."**

---

## SLIDE 9 — Post-incident actions · within 24h

### What's on the slide
6 deliverables, each a Jira ticket or GitHub PR: blameless joint post-mortem · runbook addition · **monitoring gap closure** · sandbox load test · public RCA · internal Coveo product feedback.

### What to say (~60 sec) — name the 6, dwell on #3 and #6
> "Six deliverables within 24 hours, every one a Jira ticket or GitHub PR — no tribal knowledge.
>
> A **blameless joint post-mortem** filed in both instances. A **runbook addition** — Markdown in the customer-config repo plus the Coveo FDE pattern library, so the same incident doesn't burn the same hours twice.
>
> The one that matters most: **monitoring gap closure.** The key question after any incident — why didn't this alert at 07:15, 32 minutes *before* the exec had to DM me? We add that alert as a PR. **Next time, we beat the customer to the report.**
>
> Then a **sandbox load test** reproducing Cyber Monday conditions, a **public RCA** written so YC Eu is proud to forward it to her CEO — accuracy over speed, blameless internally, humble externally — and the often-forgotten one: **internal Coveo product feedback.** The FDE is the product team's eyes inside the customer; every incident reveals a platform gap, and if we don't file it, the product never learns."

### S9 signals to land
1. **Everything is a ticket/PR** — no ad-hoc, no tribal knowledge.
2. **Monitoring gap closure pays off Slide 2** — *"the exec was my third signal; now the alert fires first."*
3. **FDE as the product feedback loop** (Action 6) — the embedded role's unique upstream value.

### 🧠 Q&A — slide 9
- **"What's a blameless post-mortem?"** → *"Focus on systems and process, never individuals — so people speak freely about what actually happened. Blame produces silence; silence produces repeat incidents."*
- **"What about SLA credits?"** → *"Those sit in the post-incident review, quietly — the FDE doesn't promise credits mid-incident. The CSM and Nespresso procurement own that conversation against the Coveo Care breach calculations."*
- **"Why a *joint* post-mortem?"** → *"Same data, same room, both teams — it builds the relationship trust that survives the next incident. A one-sided RCA reads as defensive."*

---

## SLIDE 10 — Structural prevention · the investment proposal (Topic 1 bridge)

### What's on the slide
8 Jira tickets, each with root cause · owner · priority · ETA · monthly review: SLO+error-budget · **peak-window change freeze** · quarterly drill · self-serve dashboard · **24/7 regional FDE rotation** · **sandbox sync** · **CLI + git deployment** · pre-negotiated QPS lifts.

### What to say (~80 sec) — it's 8 *tickets*, not 8 bullets; highlight 4
> "Slide 9 was tactical. This is structural — eight Jira tickets, each with a named root cause, an owner, a priority, an ETA, and a monthly review. **Prevention isn't aspirational; it's tracked.**
>
> The high-ROI unloved one is **Item 2 — a peak-window change freeze**: no ML retrains, no pipeline rule changes from Black Friday through Boxing Day, codified as a CI check that blocks PRs during the freeze. **Item 5 — 24/7 regional FDE rotation** — the org-level ask that removes the 16-hour timezone single-point-of-failure; 'more Montréal FDEs' doesn't solve it, geographic distribution does. **Item 8 — pre-negotiated peak QPS lifts** — moves that mid-incident CSM scramble *before* the event: forecast each known peak day, arrange the ceiling raise weeks ahead.
>
> And **Items 6 and 7 are the direct bridge to my Pokémon build** — Coveo CLI plus sandbox plus version-controlled config: every rule, ML config, and IPE Python ships through a PR, pushed from CI. **That's the exact same `config/`, `scripts/`, `bootstrap.sh` discipline I shipped for Topic 1. Coveo's platform supports it natively — most enterprise customers just haven't activated it. The FDE's job is to turn it on.**"

### 🌉 The Topic 1 bridge is the interview's payoff — land it deliberately
Items 6+7 prove the two presentations are *one coherent capability*: the version-controlled, PR-reviewed, sandbox-tested config discipline you *built* for Pokémon is the same thing you'd *bring* to Nespresso to prevent Console-click incidents. **Make eye contact and connect it explicitly** — *"the discipline I demonstrated in Topic 1 is the prevention strategy here."*

### S10 signals to land
1. **8 tickets, not bullets** — owner/priority/ETA/review = prevention is operationalized.
2. **Item 5 pays off Slide 6** (the timezone SPOF).
3. **Item 8 pays off Slide 4/5** (the QPS scramble, moved pre-event).
4. **Items 6+7 = the Topic 1 bridge** (Console-clicks → git-based deployment; the discipline you already shipped).

### 🧠 Q&A — slide 10
- **"A change freeze slows the customer down — worth it?"** → *"During the four highest-revenue days of the year, stability beats features. It's codified as a CI check so it's not a debate mid-peak — and it's lifted the moment peak ends. Highest-ROI, least-loved prevention there is."*
- **"Why not just hire more Montréal FDEs for coverage?"** → *"The gap is *geographic*, not headcount. Ten more Montréal FDEs are all asleep at 3 AM EST when ANZ is at peak. APAC + EMEA + Americas rotation removes the single-point-of-failure; more of the same timezone doesn't."*
- **"How do items 6+7 relate to the Pokémon build?"** → *"Identically. For Pokémon, every field, source, ML config is JSON/YAML applied via the API and CLI, version-controlled, reproducible with one bootstrap script. For Nespresso it's the same — Console clicks become PR-reviewed, sandbox-tested CLI pushes. Coveo supports it; I'd activate it."*
- **"Item 8 vs the Track B mid-incident lift?"** → *"Track B is the emergency scramble — ~15 minutes of peak burned. Item 8 makes it routine: the CSM and I forecast peak QPS for Cyber Monday, Black Friday, Boxing Day, Valentine's, and the ceiling raises are contracted weeks ahead. The scramble becomes paperwork done in advance."*

---
