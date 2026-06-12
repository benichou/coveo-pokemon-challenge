# Pres 2 — Escalation & Recovery · LIVE SCRIPT
> Fallback teleprompter. ~12 min slides + ~15 min Q&A. `[ ]` = cue.
> Differentiator: **by-name Coveo tool fluency.** Bridge: **items 6+7 = the Topic 1 build discipline.**

---

## Cover
"Presentation 2 — a hypothetical search-platform incident, anchored in a real Coveo customer.
Two honesty notes. One — the partnership is real and public; the incident is constructed. Two — the role I depict bends Coveo's actual FDE job description, and their documented process puts the Support Manager in formal case ownership. So this is how an embedded FDE plugs *into* that machinery — not replaces the Support Manager.
Twelve minutes, four sections: diagnosis, stabilization, communications, prevention."

## 2 · The scenario
"Cyber Monday, 9 AM AEDT — two hours before peak. Worst possible timing.
Slowest queries blew out 20-to-40×, ~8% errors, personalization gone for three-quarters of logged-in users. The impact that matters: **search is now worse than browsing** — the 3-to-1 conversion lift collapsed to 0.5-to-1. ~$4–6M AUD at risk over the peak.
But notice the timeline: the exec's DM is the **third** signal, not the first. Datadog fired at 07:15, the monitor at 07:30. **If the exec is my first signal, monitoring is broken.**
My role is Incident Commander on Coveo's side — and the IC does *not* debug it themselves. I delegate the technical work and run coordination and comms."

## 3 · RCA playbook  [name, don't read the table]
"Four checks, ~25 minutes, each rules out a category. Triage is a checklist, not improvisation.
**One** — Coveo-side changes via the **Activity Browser**: every rule and retrain in 7 days, by name. Status page I don't trust as primary — it lags.
**Two** — the stack and rate-limit: HTTP status codes, and **a chunk of 429s is the rate-limit smoking gun.** This row *is* the FDE differentiator — I'm three checks deep while a generalist's still requesting access.
**Three** — the **Relevance Inspector**: paste a searchUid, see the whole query journey. Plus Inspect ML Models across *every* model.
**Four** — source and data integrity via Data Health and the Log Browser.
And a fifth, verbal check — did Nespresso ship anything in 48 hours? Half of incidents are customer-side."

## 4 · Hypothesis ranking
"Six root causes on two axes — likelihood and cost-to-verify. **Two starred — likely and cheap — run in parallel.**
First, **Friday's pipeline rule** — most recent change, 30-second rollback. Second, the **per-org QPS ceiling** — token-bucket overflow gives exactly the 8% intermittent 429 we see; CSM lifts it in ~15 minutes.
Likely-but-expensive: cache thundering-herd, and ML behavior across their models — retrain regression versus serving saturation. Low-likelihood: DNS/TLS, a 60-second check, always verify it's not DNS; and a platform sub-region issue — last resort, escalate internally.
The discipline: **wrong-and-corrected at T+30 beats 'still investigating' at T+60.** Re-rank every 15 minutes."

## 5 · Stabilization
"**Mitigation before RCA** — customers want the errors to stop, not a diagnosis. Four tracks, all concurrent, all reversible.
**A** — roll back Friday's rule, ~5 minutes. **B** — CSM lifts the QPS quota, ~15 minutes. **C** — troubleshoot the ML models: output regressed → dissociate in 2 minutes; serving saturated → Coveo scales the pool. **D** — edge throttling at their CDN, defense-in-depth.
Every track is a Jira ticket before it executes — owner named, linked to a PR. And all four reverse in a minute or two. **Speed without irreversibility.**"
[If asked re automation: "subagents are read-only on prod, they draft — every write goes through me."]

## 6 · Verification & handback
"Stabilization isn't 'pushed a fix and walked away.' Three phases.
**Step 1** — is the fix holding? Zero-result under 2%, p95 under 500ms, conversion restored.
**Step 2** — hold through peak, 4+ hours. **Most relapses happen here.**
**Step 3** — handback only when metrics held 3+ hours *and* the customer's team is verbally confident. Verbal matters.
And the **16-hour timezone gap** — ANZ to Montréal. If it runs past their end-of-day, the IC hands off cleanly: pinned summary, explicit 'you're now the Incident Commander, okay?', call recording. That's why one prevention item is geographic FDE distribution, not more Montréal FDEs."

## 7 · Communication architecture
"Five audiences, five channels, five cadences — FDE in a hub-and-spoke position.
Honesty note: the FDE function is new at Coveo, so this is industry best practice plugged into Coveo's Support-Manager-led process, not replacing it.
The key discipline: a **30-minute cadence to the exec during the hot phase** — the cadence itself defuses panic, not the content. And **single point of contact** — we feed her, she distributes; we don't go around her.
One embedded benefit: the shared Slack channel already exists from our weekly cadence — coordination starts at T+0."

## 8 · Sample exec note
"About 140 words, under pressure. CC the Support Manager and CSM for the record.
Five things: **scope quantified** — '~8%, ~07:15, 3:1 to 0.5:1', forwardable to her CMO. **Top two hypotheses named** — data, not 'we're investigating.' **Both cheap to verify** — discipline. **'Next update 08:32 regardless'** — she never chases me. And **no fake resolution ETA** — 'unknown' plus a committed next-update time.
Naming a wrong hypothesis is recoverable; **silence isn't.**"

## 9 · Post-incident actions (24h)
"Six deliverables, every one a Jira ticket or PR — no tribal knowledge.
A blameless joint post-mortem. A runbook addition. The one that matters most — **monitoring gap closure**: why didn't this alert at 07:15, before the exec DM'd me? We add that alert. **Next time we beat the customer to the report.**
Plus a sandbox load test, a public RCA she's proud to forward, and internal Coveo product feedback — the FDE is the product team's eyes inside the customer."

## 10 · Structural prevention
"Slide 9 was tactical. This is structural — eight Jira tickets, each with owner, priority, ETA, monthly review. Prevention is tracked, not aspirational.
**Peak-window change freeze** — no retrains or rule changes Black Friday to Boxing Day, a CI check. **24/7 regional FDE rotation** — removes the 16-hour single-point-of-failure. **Pre-negotiated peak QPS lifts** — moves the mid-incident scramble before the event.
And **items 6 and 7 are the bridge to my Pokémon build** — Coveo CLI, sandbox, version-controlled config: every rule and ML config ships through a PR. **That's the exact same discipline I shipped in Topic 1. Coveo supports it natively — most customers just haven't activated it. The FDE's job is to turn it on.**"

## 11 · Wrap
"Three things matter: **speed of communication, quality of diagnosis, discipline of prevention.** The cadence is the message; by-name fluency with Coveo's toolkit is the diagnosis edge; and two of my prevention items are the same code-as-source-of-truth discipline I shipped for the Pokémon build.
The first two get you through the incident. The third keeps you from being paged on the next one. Questions?"

---
### Appendix (Q&A only)
- **Sources 1** — Coveo case management (docs/en/1489), diagnostic toolkit, CLI/sandbox (Topic 1 bridge).
- **Sources 2** — Google SRE, incident.io/PagerDuty/Rootly, Nespresso partnership (ClickZ ShopTalk 2025).
