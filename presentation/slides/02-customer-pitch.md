---
marp: true
theme: coveo-esdc
paginate: true
html: true
header: '<img src="images/logos/coveo-blue.svg" alt="Coveo"><span class="hdr-cross">×</span><img src="images/logos/esdc.svg" alt="ESDC">'
footer: "[github.com/benichou/coveo-pokemon-challenge](https://github.com/benichou/coveo-pokemon-challenge)"
---

<!-- _class: cover -->
<!-- _paginate: false -->
<!-- _header: "" -->
<!-- _footer: "" -->

<div class="logo-strip">
  <img class="logo-coveo" src="images/logos/coveo-blue.svg" alt="Coveo">
  <span class="logo-cross">×</span>
  <img class="logo-esdc" src="images/logos/esdc.svg" alt="ESDC">
</div>

<div class="mou-stamp">GoC × Coveo MOU · Dec 2025</div>

# AI-Relevance for ESDC EI

## Operationalizing the Government of Canada × Coveo MOU at Employment Insurance

**Franck Benichou** · Forward Deployed Engineer candidate

<div class="links">
  <div>🔍 Live app · <a href="https://pokemon-search-one-chi.vercel.app">pokemon-search-one-chi.vercel.app</a></div>
  <div>💻 GitHub · <a href="https://github.com/benichou/coveo-pokemon-challenge">github.com/benichou/coveo-pokemon-challenge</a></div>
  <div>🔬 RGA performance monitoring · <a href="https://pokemon-rga-dashboard.vercel.app">pokemon-rga-dashboard.vercel.app</a></div>
  <div>📊 Query observability · <a href="https://charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452">grafana public dashboard</a></div>
</div>

<!--
Speaker notes (transition from Topic 1 Q&A):

"Same Coveo platform you just saw running for the Pokémon build — now,
briefly, what it would mean for a real enterprise customer."

"I'm picking ESDC's Employment Insurance directorate for three reasons:
(1) the Government of Canada and Coveo signed a 5-year MOU in December
2025 — that framework explicitly anticipates this kind of work; (2) the
Benefits Delivery Modernization programme launched OAS on the new
platform in April 2025 and EI is next in the pipeline — the timing
aligns; and (3) I've operated as part of the EY Canada delivery team
for ESDC EI on first-generation RAG, so I know the policy surface and
workflows directly."

"This isn't 'should ESDC try Coveo' — it's 'extend the GoC × Coveo MOU
to the EI use case that fits it best.'"

"Five minutes. Four slides. One appendix for risk if you want it."

Key message: credibility = existing GoC-Coveo MOU + BDM timing + my
prior ESDC engagement. Same live URLs as Topic 1; proof is what just
ran.
-->

---

# Three signals · why ESDC EI · why now

<p class="callback">ESDC EI sits at the intersection of three independent timing signals — making <strong>AI-Relevance the right fit, not just a possible fit.</strong></p>

<div class="catalyst-row">

<div class="catalyst-card catalyst-1">
  <p class="catalyst-number">01</p>
  <h3>ESDC EI scale &amp; operational headroom</h3>
  <ul>
    <li><strong>~39,150</strong> ESDC employees · <strong>~2,625</strong> EI call-centre agents</li>
    <li><strong>2-3.1M</strong> EI claims/year · <strong>~$14.3B</strong> paid annually</li>
    <li><strong>20-25M+</strong> calls/year · bilingual FR/EN mandate</li>
    <li>Peak wait times <strong>&gt;1h</strong> · claim processing 17-18 days vs 28-day standard</li>
  </ul>
  <p class="catalyst-highlight">Zero operational headroom · every point of agent efficiency is consequential.</p>
</div>

<div class="catalyst-card catalyst-2">
  <p class="catalyst-number">02</p>
  <h3>BDM Programme phasing · EI is Phase 2</h3>
  <ul>
    <li>Benefits Delivery Modernization unifies <strong>OAS · GIS · CPP · EI</strong> · target 2030</li>
    <li><strong>OAS (Phase 1)</strong> migrated to BDM platform 2023-2025 ✓</li>
    <li><strong>EI (Phase 2) · migration window 2025-2028</strong></li>
    <li>First EI release (Benefits Estimator) in beta 2024 · build phase began 2025</li>
    <li>Current EI search: <strong>keyword-only</strong> · 50-year-old system · 6 RPA bots in call centres</li>
  </ul>
  <p class="catalyst-highlight">EI migration is already in flight · AI-Relevance layers <em>on top of</em> BDM, not against it.</p>
</div>

<div class="catalyst-card catalyst-3">
  <p class="catalyst-number">03</p>
  <h3>GoC × Coveo MOU · signed Dec 17, 2025</h3>
  <ul>
    <li><strong>5-year</strong> framework via Ministers <strong>Lightbound + Solomon</strong></li>
    <li>Signed through <strong>SSC</strong> (Shared Services Canada) + <strong>ISED</strong> (Innovation, Science and Economic Development Canada)</li>
    <li>MOU names: <em>enterprise search · generative + agentic AI · call-centre answers · self-serve services</em></li>
    <li>Têtu (Coveo): <em>"multi-billion-dollar opportunity in the Canadian government"</em></li>
  </ul>
  <p class="catalyst-highlight">ESDC EI is the natural first concrete application of the framework.</p>
</div>

</div>

<p class="slide-takeaway">The question isn't <em>should ESDC adopt AI-Relevance?</em> · it's <strong>which EI workflow lands first, and on what timeline?</strong></p>

<!--
Speaker notes:

"Three independent signals all pointing at the same intersection."

(point at column 1) "First — the scale. ~39,150 ESDC employees,
~2,625 call-centre agents, 2-3 million EI claims a year, 20-25 million
calls, bilingual mandate. Operationally there's NO headroom — peak
wait times over an hour, processing eating two-thirds of the 28-day
standard already. Every point of agent efficiency is real money and
real service delivery."

(point at column 2) "Second — BDM. The Benefits Delivery Modernization
Programme is consolidating OAS, GIS, CPP, and EI on one new platform.
OAS launched April 2025 — first major BDM milestone. EI is next in
the pipeline, planning phase active since 2023-24. The current EI
system is FIFTY years old. They're already running 6 RPA bots in
call centres on Automation Anywhere — automation appetite is there.
AI-Relevance layers ON TOP of the BDM platform — not against it,
not replacing it."

(point at column 3 — the punch) "Third — December 17, 2025. The
Government of Canada and Coveo signed a 5-year MOU. Ministers
Lightbound and Solomon, through Shared Services Canada and ISED.
And the MOU explicitly names the use cases — enterprise search,
generative and agentic AI, call-centre employees providing accurate
answers to citizens, self-serve government services. Coveo's
Executive Chairman Louis Têtu called it 'a multi-billion-dollar
opportunity in the Canadian government.'"

(close) "Put them together. The MOU is signed. The BDM platform is
ready and EI is next. The scale is unavoidable. The question isn't
'should ESDC adopt AI-Relevance' — it's 'which EI workflow lands
first.' That's slide two."

Key message: this is the strongest possible 'why now' — three timing
signals that align independently. Each one alone would justify a
conversation; together they make the conversation overdetermined.
-->

---

# AI-Relevance for ESDC EI · reuse what's built

<p class="callback">Five <strong>AI-Relevance™</strong> pillars · four shipped patterns adapt to ESDC · delivered by <strong>1-2 embedded FDEs</strong>.</p>

<div class="platform-pills">
  <span class="platform-pill">🧠 Intent modeling (not keyword)</span>
  <span class="platform-pill">📊 Behavioral ML ranking</span>
  <span class="platform-pill">🔌 BYO-LLM sovereign-flexible</span>
  <span class="platform-pill">🤖 MCP-ready agent surface</span>
  <span class="platform-pill">🇨🇦 Canadian-HQ infrastructure</span>
</div>

<div class="reuse-row">

<div class="reuse-card">
  <div class="reuse-from">
    <p class="reuse-label">▸ Pokémon</p>
    <p class="reuse-name">Quality + tuning loop</p>
    <p class="reuse-detail">100-Q golden · Sonnet · 5 guardrails</p>
  </div>
  <p class="reuse-arrow">→</p>
  <div class="reuse-to">
    <p class="reuse-label">▸ ESDC EI</p>
    <p class="reuse-name">Bilingual eval + quality + compliance</p>
    <p class="reuse-detail">~250-Q FR/EN · per-program slices · A/B rollout</p>
  </div>
</div>

<div class="reuse-card">
  <div class="reuse-from">
    <p class="reuse-label">▸ Pokémon</p>
    <p class="reuse-name">Dual-source ingestion</p>
    <p class="reuse-detail">Sitemap + Push · 1,353 docs unified</p>
  </div>
  <p class="reuse-arrow">→</p>
  <div class="reuse-to">
    <p class="reuse-label">▸ ESDC EI</p>
    <p class="reuse-name">Policy + BDM content layer</p>
    <p class="reuse-detail">Procedures + BDM push · Security Identities</p>
  </div>
</div>

<div class="reuse-card">
  <div class="reuse-from">
    <p class="reuse-label">▸ Pokémon</p>
    <p class="reuse-name">Headless + React detail page</p>
    <p class="reuse-detail">3 parallel queries · hero · passages · related</p>
  </div>
  <p class="reuse-arrow">→</p>
  <div class="reuse-to">
    <p class="reuse-label">▸ ESDC EI</p>
    <p class="reuse-name">EI agent decision-support</p>
    <p class="reuse-detail">3 parallel calls · claim · policy · related</p>
  </div>
</div>

<div class="reuse-card">
  <div class="reuse-from">
    <p class="reuse-label">▸ Pokémon</p>
    <p class="reuse-name">Coveo MCP Server</p>
    <p class="reuse-detail">4 tools · search · fetch · passages · answer</p>
  </div>
  <p class="reuse-arrow">→</p>
  <div class="reuse-to">
    <p class="reuse-label">▸ ESDC EI</p>
    <p class="reuse-name">2027-2030 AI-client path</p>
    <p class="reuse-detail">Officer Copilot · LLM voice IVR · citizen chat</p>
  </div>
</div>

</div>

<div class="fde-callout">
  <div class="fde-callout-icon">🤝</div>
  <div class="fde-callout-text">
    <p class="fde-callout-label">▸ DELIVERY MODEL</p>
    <p class="fde-callout-body"><strong>1-2 FDEs embedded with ESDC BDM teams</strong> · configure · adapt · train · document. The bridge between Coveo's platform and ESDC's policy / bilingual / compliance reality.</p>
  </div>
</div>

<!--
Speaker notes:

"AI-Relevance is the Coveo brand. Five pillars at the top are how
Coveo describes the platform — intent modeling, behavioral ML, BYO-LLM,
MCP-ready, Canadian-HQ infrastructure. That's the marketing layer."

"What's more useful is what's BELOW — four concrete patterns I already
shipped for the Pokémon Challenge that map directly to ESDC EI."

(point at card 1 — quality + tuning loop) "Top-left: the closed-loop
quality system. 100 golden questions, Sonnet judge, 5 guardrails,
auto-rollback. For ESDC, scales to roughly 250 bilingual questions,
adds per-benefit-program slices, plugs into the AIA audit trail. The
Coveo native A/B framework handles rollout instead of full-apply."

(card 2 — dual-source) "Top-right: dual-source ingestion. Sitemap +
Push. For ESDC: Service Canada SOPs crawled, push from the BDM
platform and case management. Same field schema pattern, but with
Coveo Security Identities propagating upstream ACLs. The early-binding
permission model."

(card 3 — detail page) "Bottom-left: Headless+React composed retrieval.
3 parallel Coveo queries on one page, sub-second. For ESDC: the EI
agent decision-support surface — claim summary, policy excerpts,
related cases. Embedded inside the case management UI. Same pattern,
ESDC content."

(card 4 — MCP) "Bottom-right: MCP server. Today it's a Pokémon demo
of 4 tools. For ESDC, it's the 2027-2030 path — Copilot for Service
Canada, voice IVR LLM clients, eventually citizen self-serve where
policy allows. Same retrieval layer, N consumption modes."

(close — point at the FDE callout) "Delivery: one or two embedded
Forward Deployed Engineers working inside ESDC's BDM teams. Configure.
Adapt. Train. Document. The FDE is the bridge between the platform
and the customer's specific reality — bilingual mandate, AIA
constraints, policy surface, agent workflows. That's exactly the role
I'm interviewing for."

Key message: this isn't 'sign up and figure it out.' It's 'four
working patterns + an FDE who knows the customer' = de-risked
implementation aligned with BDM Phase 2 timeline.
-->

---

# Before vs After · two EI workflows

<p class="callback">Same officer · same case · with <strong>Coveo AI-Relevance</strong>, search collapses, citations get captured automatically, and edge cases get the senior-officer answer every time.</p>

<div class="workflow-stack">

<div class="workflow-card">
  <div class="workflow-context">
    <div class="workflow-icon">📋</div>
    <p class="workflow-title">Claim Processing Centre</p>
    <p class="workflow-subtitle">EI Processing Officer reviewing an EI claim</p>
  </div>
  <div class="workflow-before">
    <p class="workflow-label">Before AI-Relevance</p>
    <ul class="workflow-steps">
      <li>Open case in legacy management system</li>
      <li>Read ROE data · <strong>keyword-search the policy DB</strong> (typo? guess the right section?)</li>
      <li>Switch tabs: procedures · prior claims · federal-provincial overlap rules</li>
      <li>Re-paste citations into case notes by hand</li>
      <li>Edge case? Hold the case · escalate to a senior officer</li>
    </ul>
  </div>
  <div class="workflow-after">
    <p class="workflow-label">With Coveo AI-Relevance</p>
    <ul class="workflow-steps">
      <li>Open case → <strong>detail page loads in &lt;1s</strong>: claim summary + policy excerpts + similar past cases (3 Coveo calls in parallel)</li>
      <li>Edge case? <strong>Type the question · RGA grounded answer + citations</strong> in 2-3s</li>
      <li>Citation <strong>auto-captured</strong> in case notes (audit-ready)</li>
      <li>Decision documented · escalations rare · same answer every time</li>
    </ul>
  </div>
</div>

<div class="workflow-card">
  <div class="workflow-context">
    <div class="workflow-icon">📞</div>
    <p class="workflow-title">EI Call Centre</p>
    <p class="workflow-subtitle">Call-Centre Agent on a citizen call</p>
  </div>
  <div class="workflow-before">
    <p class="workflow-label">Before AI-Relevance</p>
    <ul class="workflow-steps">
      <li>Citizen calls · agent listens · opens citizen account</li>
      <li><strong>Keyword-searches</strong> legacy policy DB while citizen waits ("let me check that...")</li>
      <li>Switches between case mgmt · procedures · ROE history</li>
      <li>Complex case → hold · escalate to supervisor</li>
      <li>After call: documents call from memory · separately</li>
    </ul>
  </div>
  <div class="workflow-after">
    <p class="workflow-label">With Coveo AI-Relevance</p>
    <ul class="workflow-steps">
      <li>Citizen account <strong>pre-loaded</strong> from caller ID + recent context</li>
      <li>Agent types brief question · <strong>RGA answers in 2-3s with citation</strong></li>
      <li>Agent paraphrases confidently · citation auto-captured in call notes</li>
      <li><strong>First-contact resolution lifts</strong> · escalations drop · consistent answers across agents</li>
    </ul>
  </div>
</div>

</div>

<!--
Speaker notes:

"Let me get concrete about what changes for the EI officer day to day.
Two workflows. Top card: an EI Processing Officer reviewing a claim
in the Claim Processing Centre. Bottom card: a Call-Centre Agent on
a citizen call."

(point at Claim Processing BEFORE) "Today: open the case in the legacy
system. Read the ROE data, manually look up the applicable policy
section. Switch tabs — procedures, prior claims, federal-provincial
overlap rules. Re-paste citations into case notes by hand. Edge case?
Hold the case, escalate to a senior officer."

(point at AFTER) "With Coveo AI-Relevance: open the case, the detail
page loads in under a second — claim summary, policy excerpts, similar
past cases, all from three parallel Coveo calls. Edge case? Type the
question. RGA gives a grounded answer with citations in 2-3 seconds.
The citation auto-captures into the case notes. Audit-ready. Decision
documented. Escalations rare. Same answer every officer gives,
because they're all working from the same source."

(point at Call Centre BEFORE) "Today on the call centre side: citizen
calls, agent listens, opens the citizen account. Searches the legacy
policy DB while the citizen waits — 'let me check that…' is what the
citizen hears, multiple times. Switches between case management,
procedures, ROE history. Complex case — hold, escalate to supervisor.
After the call, documents the call from memory, separately."

(point at AFTER) "With Coveo: citizen account pre-loaded from caller
ID and recent context. Agent types the brief question — RGA answers
in 2-3 seconds with citation. Agent paraphrases confidently, citation
auto-captures. First-contact resolution lifts, escalations drop, and
consistent answers across all agents."

(close) "These are two specific workflows where time-to-answer drops
from minutes to seconds, citation discipline becomes automatic, and
the senior-officer answer becomes the every-officer answer. That's
the day-to-day value. Slide 4 is how I'd deliver it."

Key message: don't pitch percentages — pitch the officer's screen.
A CIO can see this happening to their staff. That's the buy.
-->

---

# Disciplined AI-Relevance delivery · industry-grade outcomes

<p class="callback"><strong>Keyword → AI-Relevance</strong> · bigger than typical RAG-to-AI-Relevance · FDE bridges pilot-to-production.</p>

<div class="anchor-row">
  <div class="anchor-card anchor-1">
    <p class="anchor-label">▸ Anchor 1</p>
    <h3>Built every layer myself</h3>
    <p>All layers in the public repo. <strong>Code shipped, not pitched.</strong></p>
  </div>
  <div class="anchor-card anchor-2">
    <p class="anchor-label">▸ Anchor 2</p>
    <h3>Measurement-first discipline</h3>
    <p>First ship: the <strong>bilingual eval</strong> · proves new RGA &gt; today's keyword.</p>
  </div>
  <div class="anchor-card anchor-3">
    <p class="anchor-label">▸ Anchor 3</p>
    <h3>Operated inside ESDC via EY</h3>
    <p><strong>EY Canada · ESDC EI · first-gen RAG.</strong> Policy + bilingual + workflows known · <strong>short ramp</strong>.</p>
  </div>
</div>

<div class="metrics-tier">
  <p class="metrics-tier-label">System-design outcomes <em>· defensible by architecture</em></p>
  <div class="metrics-row">
    <div class="metric-chip">
      <span class="metric-chip-label">Regressions:</span>
      <span class="metric-chip-before">weeks</span>
      <span class="metric-chip-arrow">→</span>
      <span class="metric-chip-after">&lt;24h</span>
    </div>
    <div class="metric-chip">
      <span class="metric-chip-label">Citations:</span>
      <span class="metric-chip-before">manual</span>
      <span class="metric-chip-arrow">→</span>
      <span class="metric-chip-after">100% auto</span>
    </div>
    <div class="metric-chip">
      <span class="metric-chip-label">Bilingual:</span>
      <span class="metric-chip-before">invisible</span>
      <span class="metric-chip-arrow">→</span>
      <span class="metric-chip-after">continuous</span>
    </div>
    <div class="metric-chip">
      <span class="metric-chip-label">Audit:</span>
      <span class="metric-chip-before">ad-hoc</span>
      <span class="metric-chip-arrow">→</span>
      <span class="metric-chip-after">by design</span>
    </div>
  </div>
</div>

<div class="metrics-tier">
  <p class="metrics-tier-label">Industry-grade outcomes <em>· refined vs ESDC baseline in first 90 days</em></p>
  <div class="metrics-row">
    <div class="metric-band-chip">
      <span class="metric-band-value">-15 to -25%</span>
      <span class="metric-band-label">Average Handle Time (call centre)</span>
    </div>
    <div class="metric-band-chip">
      <span class="metric-band-value">-20 to -35%</span>
      <span class="metric-band-label">Time-to-resolution · complex cases</span>
    </div>
    <div class="metric-band-chip">
      <span class="metric-band-value">-30 to -50%</span>
      <span class="metric-band-label">New officer/agent ramp time</span>
    </div>
  </div>
</div>

<div class="ask-box">
  <p class="ask-label">▸ First 30 days I'd ask for</p>
  <ul>
    <li><strong>Baseline:</strong> EI search metrics + officer feedback</li>
    <li><strong>Stakeholders:</strong> DG Service Delivery · Policy Owner · Security/Compliance</li>
    <li><strong>Pilot:</strong> one EI sub-workflow (maternity benefits)</li>
  </ul>
</div>

<!--
Speaker notes:

"Why me, what we'd measure, what I'd ask for."

(point at anchors) "Three anchors. One: I've built every layer myself
— the public repo is the proof. Two: measurement-first discipline —
the FIRST thing I'd ship at ESDC isn't the new RGA, it's the bilingual
eval framework that tells us whether the new RGA actually beats today's
keyword search. Three — and this is the credibility moment — I've
operated as part of the EY Canada delivery team for ESDC EI on
first-generation RAG. I know the policy surface, the bilingual
constraints, the officer workflows. My FDE ramp here is short."

(point at system-design metrics) "What we'd measure. Top row is
defensible by architecture — these outcomes come from how the system
is built, not from analog data. Regression detection: weeks of manual
review become less than 24 hours via daily eval. Citation capture:
zero or paraphrased today, 100% automatic with RGA. Bilingual parity:
invisible today (EN measured, FR trusted), continuous slices with our
golden set. Audit trail: ad-hoc today, 100% by construction."

(point at industry-analog metrics) "Bottom row is conservative
analogs — Coveo customer outcomes used as starting estimates. AHT
down 15-25%, time-to-resolution down 20-35%, new officer ramp time
down 30-50%. These get refined against ESDC's own baseline in the
first 90 days. I'm not committing to a point number; I'm committing
to measuring."

(point at ask box) "First 30 days I'd ask for: current EI metrics
and officer feedback as the baseline; stakeholder alignment with DG
Service Delivery, Policy Owner, Security/Compliance reviewer; a
scope-limited pilot on one EI sub-workflow — say maternity benefits
eligibility — for the 6-month foundation phase."

(close) "Pitching this isn't 'sign now.' It's 'open the conversation
with the right context.' I'd be at ESDC in week one ready to baseline,
not 90 days deep in onboarding. Happy to take any questions on this
or Topic 1."

Key message: short FDE ramp · architecture-defensible promises ·
measurable bands · scope-limited pilot ask. The conversation moves
from pitch to plan in 30 days.
-->

---

<!-- _class: cover -->
<!-- _paginate: false -->
<!-- _footer: "" -->

<div class="logo-strip">
  <img class="logo-coveo" src="images/logos/coveo-blue.svg" alt="Coveo">
  <span class="logo-cross">×</span>
  <img class="logo-esdc" src="images/logos/esdc.svg" alt="ESDC">
</div>

<div class="mou-stamp">GoC × Coveo MOU · Dec 2025</div>

# Thank you · Q&A

## Keyword → AI-Relevance · disciplined delivery · industry-grade outcomes

**1-2 embedded FDEs · BDM-aligned · measured against ESDC's own baseline**

<div class="links">
  <div>🔍 Live app · <a href="https://pokemon-search-one-chi.vercel.app">pokemon-search-one-chi.vercel.app</a></div>
  <div>💻 GitHub · <a href="https://github.com/benichou/coveo-pokemon-challenge">github.com/benichou/coveo-pokemon-challenge</a></div>
  <div>🔬 RGA performance monitoring · <a href="https://pokemon-rga-dashboard.vercel.app">pokemon-rga-dashboard.vercel.app</a></div>
  <div>📊 Query observability · <a href="https://charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452">grafana public dashboard</a></div>
</div>

<!--
Speaker notes (wrap):

"That's the pitch. Three signals point at ESDC EI · four shipped
patterns adapt from the Pokémon Challenge · 1-2 embedded FDEs deliver."

"Same Live URLs as Topic 1's cover — the proof is what just ran."

"Happy to take any questions on this pitch or on Topic 1's build."

Key message: visual bookend to the cover. The conversation continues
in Q&A.
-->

---

# Appendix · Risk register

<p class="callback">Honest CIO-grade risks · pre-prepared mitigations · pull up if Q&A goes there.</p>

<div class="risk-row">

<div class="risk-card">
  <h4>▸ Vendor lock-in</h4>
  <p><strong>Mitigation:</strong> Index exportable · LLM is BYO · closed-loop code in our repo · golden set is our IP</p>
  <p class="risk-mitigation">Residual: re-implementing full stack elsewhere ≈ 6-12 months</p>
</div>

<div class="risk-card">
  <h4>▸ Data sovereignty</h4>
  <p><strong>Mitigation:</strong> Canadian-region deployment · Coveo HQ Montréal · source content can stay on-prem via Crawling Modules</p>
  <p class="risk-mitigation">Residual: verify Canadian-region SLA contractually</p>
</div>

<div class="risk-card">
  <h4>▸ Compliance accountability</h4>
  <p><strong>Mitigation:</strong> 100% audit trail · per-decision citations · officer-in-the-loop (not citizen-facing in Phase 1)</p>
  <p class="risk-mitigation">Residual: citizen could misinterpret officer-paraphrased answer</p>
</div>

<div class="risk-card">
  <h4>▸ LLM cost volatility</h4>
  <p><strong>Mitigation:</strong> BYO-LLM lets us switch providers · already on cost-efficient model (Sonnet) · A/B for cost-quality tradeoffs</p>
  <p class="risk-mitigation">Residual: quarterly budget review required</p>
</div>

<div class="risk-card">
  <h4>▸ Workforce displacement concerns</h4>
  <p><strong>Mitigation:</strong> Officer augmentation framing · same headcount + higher service standards · no replacement narrative</p>
  <p class="risk-mitigation">Residual: PSAC (union) engagement non-negotiable</p>
</div>

<div class="risk-card">
  <h4>▸ BDM integration collision</h4>
  <p><strong>Mitigation:</strong> Adjacency, not collision · agent/decision-support layer alongside BDM core transformation · same content, different access path</p>
  <p class="risk-mitigation">Residual: BDM PMO coordination overhead in months 0-6</p>
</div>

</div>

<!--
Speaker notes:

"Six honest risks. Each one has a real mitigation, and I've named the
residual risk that remains so we can have an honest conversation if it
comes up."

"Vendor lock-in: index is exportable, LLM is BYO. Sovereignty: Canadian-
region deployment + Coveo HQ Montréal. Compliance: 100% audit trail by
construction. LLM cost: BYO-LLM means we switch providers if needed.
Workforce displacement: this is augmentation, not replacement — PSAC
engagement is non-negotiable. BDM integration: AI-Relevance is the
decision-support layer ALONGSIDE BDM's core transformation, not
competing with it."

Key message: I've thought about what could go wrong, and there's a
mitigation for each. The residual risks are the ones to surface
honestly in Q&A.
-->

---

# Appendix · References

<p class="callback">Every claim in the deck links to a public source · pre-panel re-verification recommended.</p>

<div class="appendix-row">

<div class="appendix-col">

<p class="appendix-col-header">▸ ESDC + Government of Canada</p>

<div class="appendix-section">
  <p class="appendix-section-title">GoC × Coveo MOU (Dec 17, 2025)</p>
  <ul>
    <li><a href="https://www.canada.ca/en/shared-services/news/2025/12/canada-signs-memorandum-of-understanding-with-coveo-to-advance-ai-innovation.html">Canada.ca · MOU announcement</a></li>
    <li><a href="https://www.canada.ca/en/shared-services/news/2025/12/memorandum-of-understanding-between-the-government-of-canada-and-coveo.html">Canada.ca · MOU backgrounder</a></li>
    <li><a href="https://betakit.com/feds-sign-five-year-mou-with-coveo-in-latest-ai-partnership/">BetaKit · 5-year MOU coverage</a></li>
  </ul>
</div>

<div class="appendix-section">
  <p class="appendix-section-title">BDM Programme</p>
  <ul>
    <li><a href="https://www.oag-bvg.gc.ca/internet/English/att__e_44349.html">Auditor General Report 8 · BDM Programme</a></li>
    <li><a href="https://www.canada.ca/en/employment-social-development/corporate/reports/esdc-transition-binders/2025-march-transition-binder-mackinnon.html">ESDC briefing · March 2025</a></li>
    <li><a href="https://www.canada.ca/en/employment-social-development/corporate/reports/esdc-transition-binders/2025-may-transition-binder-hajdu.html">ESDC briefing · May 2025</a></li>
  </ul>
</div>

<div class="appendix-section">
  <p class="appendix-section-title">EI operations + scale</p>
  <ul>
    <li><a href="https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/reports/monitoring2024/chapter4.html">EI Monitoring 2024 · Ch 4 (incl. 6 RPA bots)</a></li>
    <li><a href="https://www.canada.ca/en/employment-social-development.html">ESDC main</a></li>
  </ul>
</div>

</div>

<div class="appendix-col">

<p class="appendix-col-header">▸ Coveo + Pokémon build</p>

<div class="appendix-section">
  <p class="appendix-section-title">Coveo AI-Relevance™ positioning</p>
  <ul>
    <li><a href="https://www.coveo.com/en">coveo.com · AI-Relevance Platform</a></li>
    <li><a href="https://ir.coveo.com/en/news-events/press-releases/detail/468/government-of-canada-partners-with-coveo-to-modernize">Coveo IR · GoC partnership</a></li>
    <li><a href="https://www.coveo.com/en/company/customers">Coveo customers</a></li>
  </ul>
</div>

<div class="appendix-section">
  <p class="appendix-section-title">Coveo brand assets (logos)</p>
  <ul>
    <li><a href="https://www.coveo.com/en/company/brand">Coveo Media Kit</a></li>
    <li><a href="https://commons.wikimedia.org/wiki/File:Employment_and_Social_Development_Canada_logo.svg">ESDC logo · Wikimedia (public domain)</a></li>
  </ul>
</div>

<div class="appendix-section">
  <p class="appendix-section-title">Pokémon build · the live proof</p>
  <ul>
    <li><a href="https://pokemon-search-one-chi.vercel.app">Atomic main app</a></li>
    <li><a href="https://github.com/benichou/coveo-pokemon-challenge">GitHub repo</a></li>
    <li><a href="https://pokemon-rga-dashboard.vercel.app">RGA performance dashboard</a></li>
    <li><a href="https://charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452">Grafana query observability</a></li>
  </ul>
</div>

</div>

</div>

<!--
Speaker notes:

"Reference appendix. Every claim on the deck has a public source · the
GoC × Coveo MOU is documented across multiple Canadian government and
press sources · BDM is sourced from the Auditor General's Report 8 + ESDC
ministerial briefings · the EI 6 RPA bots claim comes from the EI
Monitoring 2024 Chapter 4."

Key message: I cite my sources. Verify anything.
-->
