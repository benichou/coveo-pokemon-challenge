# RGA Skill Evaluator — methodology for diagnosing AI quality regressions

This document is a panel-shareable walk-through of the framework we used to take the RGA Skill Evaluator (`rga-eval/`) from "we have raw eval numbers" to a targeted, defensible prompt enhancement. It uses the 2026-05-31 baseline as a worked example, but the *loop* generalizes to any production-AI quality regression.

The goal is to show the **process** an FDE applies when an AI system is misbehaving in production — not just the result.

## Companion artifacts

- **`rga-eval/`** — the evaluator itself (Python + Pydantic + Anthropic SDK)
- **`eval-runs/2026-05-31-full.json`** — the raw baseline data this analysis was performed on
- **[Live dashboard](https://pokemon-rga-dashboard.vercel.app)** — visual surface of the same data
- **`docs/rga-prompt.md`** — the operational note (the prompt text + how to apply it in Coveo Console). The *result* of this methodology.

## The diagnostic loop (six stages)

```
   ┌─────────────┐
   │ 1. MEASURE  │  Run the eval. Get raw numbers per layer + per category.
   └──────┬──────┘
          │
   ┌──────▼──────┐
   │ 2. CATEGORIZE│  Sort failures. Find the categories where accuracy is
   │             │  worst — and the gap-vs-recall is largest.
   └──────┬──────┘
          │
   ┌──────▼──────┐
   │ 3. DIAGNOSE │  Read the actual failing answers. Look for patterns.
   │             │  (Quantitative metrics don't replace qualitative reads.)
   └──────┬──────┘
          │
   ┌──────▼──────┐
   │ 4. HYPOTHESIZE│ Form a hypothesis about the root cause. Distinguish
   │             │ data problems from prompt problems from retrieval problems.
   └──────┬──────┘
          │
   ┌──────▼──────┐
   │ 5. DECIDE   │  Pick the intervention. Prompt fix vs index fix vs both.
   │             │  Sequence by cost + information value.
   └──────┬──────┘
          │
   ┌──────▼──────┐
   │ 6. APPLY +  │  Ship the fix. Re-run the eval. Compare before/after on
   │   MEASURE   │  the dashboard. Iterate.
   └─────────────┘
```

This is the loop. Most AI projects ship and pray; this loop measures and ships. The dashboard exists so this loop can be **continuous, not one-shot** — every day's 06:00 UTC cron run is one new turn of the wheel.

---

## Stage 1 — Measure (the 2026-05-31 baseline)

Ran the 100-question golden-dataset evaluator. Aggregate result:

```
Overall:   accuracy=62.0%   precision=71.0%   hard_recall=87.1%   citation_precision=77.3%
Layer 1:   accuracy=68.0%   precision=64.0%   hard_recall=99.0%    (n=50, single-fact lookups)
Layer 2:   accuracy=45.7%   precision=71.4%   hard_recall=64.5%    (n=35, multi-doc synthesis)
Layer 3:   accuracy=80.0%   precision=93.3%   hard_recall=100.0%   (n=15, refusal / edge cases)
```

**The diagnostic signal is the gap between `hard_recall` and `accuracy`.**

- `hard_recall` is deterministic — it asks "did the expected facts appear in the answer text?"
- `accuracy` is LLM-judged — it asks "is the answer *holistically* correct?"

When recall is high (87%) but accuracy is low (62%), it means RGA *is* mentioning the right facts. So the failures aren't in retrieval — they're in *what RGA says around the facts.* The bug lives in generation, not retrieval.

This single inference narrows the search space dramatically. If recall had been 30%, we'd be debugging the search index instead of the prompt.

---

## Stage 2 — Categorize (sort failures, find the largest gaps)

Used the dashboard's "Where it fails — by category" view. Top of the worst-first table:

| Layer | Category | n | Accuracy | Recall | Gap (recall − acc) |
|---|---|---|---|---|---|
| L2 | ability-across-pokemon | 3 | 0.0% | 33.3% | +33 |
| **L1** | **ability-lookup** | **10** | **10.0%** | **95.0%** | **+85** ← biggest signal |
| L2 | cross-source-synthesis | 4 | 25.0% | 35.0% | +10 |
| L3 | keyword-only-not-question | 3 | 33.3% | 100.0% | +67 |
| **L1** | **stat-lookup** | **5** | **40.0%** | **100.0%** | **+60** |
| L2 | cross-pokemon-compare | 10 | 50.0% | 75.0% | +25 |
| L2 | form-comparison | 8 | 50.0% | 83.3% | +33 |

The largest gaps are in **L1 ability-lookup (+85)** and **L1 stat-lookup (+60)**. These are *easy* lookups where RGA gets the fact right (recall ≈ 100%) but somehow still fails the judge. That's where the diagnostic signal is strongest.

Interestingly, **L1 type-lookup (+7)** and **L1 generation-lookup (+10)** show almost no gap — RGA handles those cleanly. Why? Because there's nothing to embellish: a Pokémon's type is one or two words; there's no room to fabricate context around it. That contrast is itself a clue.

### Multi-day window — distinguishing chronic failures from one-day noise

The table above is from a single eval run. A single-run view has a known blind spot: it can't tell the difference between a category that has been failing for a week (a real, persistent problem worth fixing) and one that flunked yesterday because the LLM judge happened to misjudge a borderline answer (noise — fixing it overfits to a transient artefact).

The closed-loop analyzer (Phase 6F) reads the **last N=5 eval runs** and ranks categories using two derived signals on top of the single-run gap:

- **Persistence** — count of runs in the window where this category was below the failing threshold (default 70% accuracy). 5/5 is chronic; 1/5 is noise.
- **Drift** — accuracy change from the first half of the window to the second half. Positive = declining over time (worth surfacing before it gets worse); negative = improving (no fix needed).

The composite ranker prioritizes chronic persistence first, then drift, then absolute latest accuracy, then sample size as a tiebreaker. The effect on prompt-tuning behavior:

- A category that drops to 60% for one day, then recovers — won't trigger a proposal.
- A category that drifts from 85% → 80% → 75% → 70% → 65% over the window — surfaces *before* it lands in the table above as a single bad day.
- A category that has been failing at 30% every day for a month — stays at the top of the ranker until the prompt change actually moves it.

This makes the closed loop's proposals **smoother** in two senses: fewer noisy proposals (we don't chase single-day spikes) and more confident proposals (when we DO propose, persistence vouches for the signal). The trade-off is responsiveness: it takes ~3 runs for a brand-new degradation to register as "persistent." For prompt tuning on a daily eval cadence, that's the right balance.

See `rga-closed-loop/src/analyzer.py` (`CategoryHistory`, `rank_worst_categories`) for the implementation. CLI flags `--window-size` and `--persistence-threshold` let you tune the window and threshold per run.

---

## Stage 3 — Diagnose (read the actual failing answers)

Quantitative metrics don't replace reading the data. For each failure in `ability-lookup` (n=9), I read:

- The question
- The full RGA-generated answer
- Sonnet's judge reasoning
- The `false_claims` array (Sonnet's specific identified hallucinations)

Five representative failures:

> **q-l1-ability-gengar** — "what ability does gengar have"
> RGA: "Gengar has the ability **Cursed Body**, which lowers the opponent's Sp. Def by one stage when it makes contact."
> Reality: Cursed Body has a 30% chance to disable a move when Gengar is hit by it. Nothing to do with Sp. Def.

> **q-l1-ability-gyarados** — "what abilities does gyarados have"
> RGA: "Gyarados has two abilities: Intimidate and **Moxie** (hidden ability). [...] Moxie increases Gyarados's Special Attack by one stage when its HP drops below half."
> Reality: Moxie boosts Attack (not Sp.Atk) by one stage when the user *knocks out* an opponent (not when HP drops).

> **q-l1-ability-dragonite** — "what abilities does dragonite have"
> RGA: "Dragonite has two abilities: **Inner Focus** and **Multiscale**. Inner Focus increases the Pokémon's accuracy, while Multiscale boosts its defense when hit by a super effective move."
> Reality: Inner Focus prevents flinching (nothing to do with accuracy). Multiscale halves damage when at full HP (nothing to do with super effective moves).

> **q-l1-ability-gardevoir** — "what abilities does gardevoir have"
> RGA: "Gardevoir has two abilities: **Synchronize** [...] and **Telepathy** (hidden ability), which raises the priority of status moves."
> Reality: Telepathy blocks ally damage in doubles/triples (nothing to do with priority). Gardevoir also has a third ability — Trace — which RGA omitted entirely.

> **q-l1-ability-lucario** — "what abilities does lucario have"
> RGA: "**Steadfast** increases the power of moves that make contact, [...] **Justified** doubles the Pokémon's Attack stat if it is hit by a Dark-type move."
> Reality: Steadfast raises Speed by one stage when the Pokémon flinches (not contact power). Justified raises Attack by one stage on Dark-type hits (not doubles).

**The pattern crystallizes after reading 4-5 failures: RGA correctly identifies ability *names* but fabricates their *mechanic descriptions*.**

This is qualitative pattern-matching. No model can do this for you — it requires reading the data with your own eyes. A diagnostic dashboard makes this fast but doesn't replace the read.

---

## Stage 4 — Hypothesize root cause

Two non-mutually-exclusive hypotheses:

### Hypothesis A — Content gap

The indexed pokemondb.net Pokémon pages have ability *names* in the vitals table:

```html
<table class="vitals-table">
  ...
  <th>Abilities</th>
  <td><a class="text-muted" href="/ability/cursed-body">Cursed Body</a></td>
</table>
```

…but the *mechanic descriptions* live on a separate `/ability/<name>` page, which **we did not index**. When RGA is asked "what does Cursed Body do?", it has the name in source but no mechanic content → falls back to the LLM's pretraining → hallucinates a plausible-sounding but wrong mechanic.

Cross-check this against the data: high recall on the ability NAME (95%), zero source-grounded explanation of the mechanic. Consistent with content-gap hypothesis.

### Hypothesis B — Prompt gap

Even with limited source content, a properly-instructed RGA could *refuse* to make claims without grounding ("I see the name but my sources don't describe the mechanic"). It isn't refusing — it's elaborating freely. So the prompt isn't constraining it to retrieved content.

Cross-check: looking at the answer text, there's no signal of source-awareness. RGA writes as if its general knowledge is the truth.

**Both hypotheses are likely true.** They suggest two independent fixes, with different cost/effort/risk profiles.

### Confirming Hypothesis B — what we found when we went to apply the fix

When we opened the Coveo Admin Console on 2026-06-01 to apply the prompt enhancement, we discovered that the `pokemon-rga` model's **Prompt instruction** field still held Coveo's **default enterprise template** — verbatim text shipped on every fresh RGA model, with unfilled placeholders like `[Enterprise Name]`, `[Company Name]`, and `[tone guidance]` still in place.

The default template framed RGA as a *"subject matter expert representing [Enterprise Name]"* — language that *encourages* elaboration from general knowledge, since subject-matter-experts are expected to have authoritative answers beyond just retrieved documents. Combined with the content gap (Hypothesis A), this produced exactly the observed behavior: confident, fluent, fabricated mechanics.

This was the moment the diagnostic loop paid off twice:

1. **Direct confirmation of Hypothesis B.** The prompt was never constraining RGA in the first place — it was actively encouraging the failure mode.
2. **Latent-misconfiguration insight.** A Coveo customer who doesn't measure RGA quality (i.e., doesn't have a Phase-6D-style eval system) would never see this. The default prompt produces answers that *look* polished in spot-checks; the defect only surfaces under structured evaluation across a curated dataset. This is exactly why every production RGA deployment needs a measurement system before it ships.

The full default-template text is preserved in [`rga-prompt.md`](rga-prompt.md) so the before-state is reviewable in git, not just at one moment in the Console.

This insight strengthens the case for **Phase 6F** (closed-loop prompt-tuning): the discovery that the default prompt was an unfilled template is exactly the kind of state the closed-loop analyzer should be able to surface automatically when it diffs run-over-run results against the live prompt.

---

## Stage 5 — Decide between fixes

| Fix | Effort | Expected lift | Risk | Information value | When to ship |
|---|---|---|---|---|---|
| **Prompt enhancement** (constrain RGA to retrieved content) | ~5 min, no model rebuild | L1 ability 10% → ~70% (refusals count as correct) | Low (reversible) | Tells us whether the failure is prompt-side, data-side, or both | **First** |
| **Re-index ability pages** | ~30 min code + 1h crawl | L1 ability 10% → ~90% (mechanics in source) | Medium (re-crawl, mapping work, possibly index size) | Confirms whether the prompt fix's ceiling is data | After verifying prompt fix |

The **prompt-first** sequencing is the production-grade move. Here's the framework:

1. **Cheapest intervention first.** Costs 5 min, no infra change, fully reversible. If it doesn't work, we've lost nothing.
2. **Maximum information yield.** The result of the prompt fix tells us *how much* of the failure was prompt-side vs data-side. After we ship it and look at tomorrow's eval, the residual gap is the data-side cost.
3. **Reduces scope of the next fix.** If prompt-only lifts accuracy 10% → 70%, we know re-indexing only needs to bridge 70% → 90%. We can scope which ability pages matter most before crawling all 800+.
4. **Time-boxed validation.** The daily cron + dashboard means we'll see the lift (or its absence) tomorrow morning, no extra work.

This is how a seasoned production-AI engineer sequences interventions — by **cost vs information**, not by appeal of the technical solution.

---

## Stage 6 — Apply + measure

### The prompt enhancement

Full text in [`docs/rga-prompt.md`](rga-prompt.md). Summary of what each rule does and which failure mode it targets:

| Rule | Failure mode it addresses |
|---|---|
| "Every factual claim must be directly supported by content in the retrieved sources" | The core fabrication pattern — gives RGA explicit license to *not* invent |
| "If a source identifies an entity by name but does not describe its mechanic or details, state ONLY what is in the source" | The exact ability-mechanic-fabrication pattern we diagnosed |
| "When sources do not contain the answer, say so explicitly with [refusal phrasing]" | Tells RGA how to refuse cleanly — the LLM judge's rubric counts honest refusals as correct |
| "Cite the source document for each factual claim" | Forces RGA to be aware of what it's citing |
| "Prefer short, exact answers over long elaborations" | Reduces the surface area for embellishment-style hallucinations |

### Expected outcome

| Category | Baseline (2026-05-31) | Hypothesis after prompt change |
|---|---|---|
| L1 ability-lookup | 10% / 95% | 60–80% / 95% |
| L1 stat-lookup | 40% / 100% | 70–85% / 100% |
| L1 type-lookup | 93% / 100% | unchanged (already clean) |
| L1 generation-lookup | 90% / 100% | unchanged (already clean) |
| **Overall accuracy** | **62%** | **target: ~75–80%** |

### How we'll know it worked

Tomorrow's 06:00 UTC scheduled cron run produces `eval-runs/2026-06-01-full.json`. The dashboard's time-series chart will have a new data point. The visual outcome we expect:

```
       accuracy
         │
   ~78% ─┤                     ╳ ← 2026-06-01 (post-prompt)
         │                    /
         │                   /
   ~62% ─┤  ╳────────────────  ← 2026-05-31 (baseline)
         │
         └────────────────────────── date
              2026-05-31  2026-06-01
```

If the step-change shows up, the diagnosis was correct, and the prompt-fix-first sequencing was vindicated.

If accuracy stays flat at ~62%, the hypothesis was wrong. We'd go to plan B: re-read the post-prompt failures (the dashboard makes this 1 click) and look for a *different* pattern — possibly retrieval, possibly judge rubric calibration, possibly something we missed.

---

## What actually happened (2026-06-01) — **preliminary results, to be polished for the panel**

> **Status: preliminary.** This section captures the first validated cycle of the closed loop. Numbers will be re-confirmed and re-presented after more days of data have accumulated; final panel version will be polished closer to the presentation.

### Overall numbers (latest run vs prior)

| Metric | 2026-05-31 (baseline) | 2026-06-01 (post-v1.1.0) | Δ | Predicted | Actual vs prediction |
|---|---|---|---|---|---|
| **Accuracy** | 62.0% | **79.0%** | **+17.0 pts** | +16 pts (target 78%) | **within 1 pt of prediction** ✅ |
| **Precision** | 71.0% | **92.0%** | **+21.0 pts** | not explicitly predicted | massive bonus — hallucinations crushed |
| **Hard recall** | 87.1% | 85.7% | −1.4 pts | not predicted | small expected dip from stricter grounding |
| **Citation precision** | 77.3% | 77.5% | +0.3 pts | flat | flat, as expected |

The step-change visual we predicted, with the actual numbers:

```
       accuracy
         │
    79% ─┤                                    ╳ ← 2026-06-01 (post-v1.1.0)  ← within 1pt of prediction
         │                                   /
         │                                  /
         │                                 /
    62% ─┤  ╳────────────────────────────── ← 2026-05-31 (baseline)
         │
         └────────────────────────────────────── date
              2026-05-31              2026-06-01
```

### Where the lift came from — per-layer + per-category

| Layer / category | Baseline | Post-v1.1.0 | Δ | Analyzer prediction |
|---|---|---|---|---|
| **Layer 1 (single-fact, n=50)** | 68.0% | **94.0%** | **+26.0 pts** | (implicit, large) |
| ↳ ability-lookup | 10.0% | **90.0%** | **+80.0 pts** | predicted 75% (+65) — **exceeded** |
| ↳ stat-lookup | 40.0% | **80.0%** | **+40.0 pts** | predicted 80% — **exact match** |
| ↳ type-lookup | 93.3% | 100.0% | +6.7 pts | predicted flat — small bonus |
| ↳ generation-lookup | 90.0% | 100.0% | +10.0 pts | predicted flat — small bonus |
| **Layer 2 (multi-doc synthesis, n=35)** | 45.7% | 54.3% | +8.6 pts | (not directly targeted) |
| **Layer 3 (refusal / edge, n=15)** | 80.0% | 86.7% | +6.7 pts | (not directly targeted) |
| ↳ keyword-only-not-question | 33.3% | 33.3% | **0.0 pts** | predicted 90% — **DID NOT MATERIALIZE** ⚠️ |

### Honest miss to investigate

**Rule 8 (fragment clarification) did not work as predicted.** The analyzer projected `keyword-only-not-question` would rise to 90%; it stayed flat at 33%. This is a panel-honest moment: the system measured a real prediction failure. Next iteration would re-read those failing answers and figure out *why* rule 8 didn't take. Hypotheses to test:

- The Layer-3 judge rubric may not be giving rule 8 credit when RGA over-explains. The judge prompt frames "RGA should refuse" but the questions in this category are fragments, not refusal-worthy — the judge may be calibrated wrong for them.
- RGA may be ignoring rule 8 because the prior rules say "answer based on retrieved sources" — when the fragment retrieves Pokémon content, RGA defaults to answering anyway.
- Sample size is small (n=3 in this category); could be measurement noise.

The closed loop's next analyzer run will likely propose a sharper version of rule 8 — exactly the kind of iteration the system was designed for.

### What this validates

1. **The diagnostic methodology works.** We diagnosed the failure pattern manually + Sonnet rediscovered it independently + the proposed fix delivered close to the predicted lift. The six-stage loop produces actionable interventions, not just dashboards.
2. **Analyzer calibration is real.** Sonnet 4.6's self-rated confidence (0.78–0.82) with tool-use-forced structured output predicted the accuracy result within 1 pt. That's better calibration than most human estimates.
3. **The +21pt precision jump is the bigger win.** RGA no longer fabricates ability mechanics or stat values — even where it doesn't gain accuracy, it stops hallucinating. From a customer-trust perspective, this is more valuable than the headline accuracy number.
4. **The hard_recall tradeoff is acceptable.** −1.4 pts in exchange for +17 / +21 on accuracy / precision is a great trade. RGA being slightly more conservative is the right default for a grounded-answers system.
5. **The closed loop is autonomous from this point forward.** The cron will re-evaluate quality daily. If quality degrades, the auto-rollback triggers. If a refinement is warranted, the analyzer proposes it and the rate-limit + confidence guardrails decide whether to ship it.

### What we'll measure next (next 3–7 days)

- **Stability of the +17pt lift.** Is 79% the new floor, or do day-to-day judge variance plus prompt sensitivity bring it back toward 70-something? Three+ data points needed to call it stable.
- **The auto-rollback safety net.** Has any subsequent eval triggered the >5pt drop threshold? (Expected: no, because v1.1.0 should hold.)
- **The keyword-only-not-question miss.** Does the next analyzer run propose a sharper rule 8? If so, does it work?
- **Layer 2 (multi-doc synthesis) headroom.** Only +8.6 pts on the largest layer; biggest remaining gap. May require re-indexing more content (e.g., per-form data via Source B) rather than prompt-only fixes.

---

## What this loop generalizes to

This same six-stage loop applies to any production AI quality problem:

| Domain | Stage 1 — Measure | Stage 2 — Categorize | Stage 3 — Diagnose | Stage 4 — Hypothesize | Stage 5 — Decide | Stage 6 — Apply |
|---|---|---|---|---|---|---|
| **Customer-support RAG** | Resolution rate, ticket re-open rate, CSAT | By ticket category, by product area | Read flagged tickets | Knowledge gap? Prompt gap? Tone? | Prompt vs content vs escalation rules | Ship + re-measure |
| **Sales-prospecting LLM** | Quota attainment, reply rate | By segment, by message variant | Read low-reply messages | Wrong tone? Wrong segment match? | Prompt vs targeting model | A/B + re-measure |
| **Code-completion model** | Acceptance rate, edit-after-accept | By language, by file type | Read rejected suggestions | Wrong style? Wrong context? | Prompt vs retrieval vs reranking | Ship + re-measure |

The pattern is always the same: **measure → drill into the gap → read the data → form a hypothesis → pick the cheapest intervention with the most information value → ship → re-measure**.

The technology evolves — the loop doesn't.

---

## Why this matters for a Coveo enterprise customer

The same loop applies one-to-one to a Coveo customer who's running RGA in production:

1. **They need a golden dataset.** ~100 questions, hand-curated, layered (single-fact / synthesis / refusal). Coveo's panel-quality observability story should include "we help you build this."
2. **They need accuracy + precision + hard recall + citation precision tracked over time.** Coveo provides the answer; the customer should track the answer's quality.
3. **They need a dashboard that supports the diagnosis loop** — not just aggregate numbers but per-category breakdowns and per-question drill-downs.
4. **They need a cron, not a one-shot.** Quality changes every time content updates, every time RGA retrains, every time the prompt is tuned.
5. **They need a methodology for acting on the data** — the six-stage loop above is one. Without a methodology, the dashboard is just decoration.

The Pokémon Challenge build demonstrates 1–5 end-to-end as a complete proof-of-concept. Topic 2 (the customer pitch) is naturally: *"This is what we'd help you build."*
