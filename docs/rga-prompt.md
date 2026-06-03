# RGA prompt enhancement — version-controlled

The Custom Prompt text is **stored as YAML at [`rga-closed-loop/prompts/pokemon-rga.yaml`](../rga-closed-loop/prompts/pokemon-rga.yaml)** — that file is the single machine-readable source of truth. It's PUT to the Coveo Admin Console (AI & ML → Models → `pokemon-rga` → Prompt enhancement → Prompt instruction) via [`rga-closed-loop/src/apply.py`](../rga-closed-loop/src/apply.py).

This markdown file is the **narrative** note — what the prompt is, why we chose it, the diagnostic story. The YAML is the **data** that gets PUT.

> **For the full diagnostic methodology** that led to this prompt — including the six-stage analytical loop and the worked example on the 2026-05-31 baseline — see [`docs/rga-eval-methodology.md`](rga-eval-methodology.md). For the closed-loop architecture that turns the eval output into automated prompt improvements, see [`rga-closed-loop/README.md`](../rga-closed-loop/README.md).
>
> **For an interactive view of every version that has been live on the model**, including diffs vs the prior version and the predicted-vs-realized lift table, scroll to the **Prompt history** section on the [RGA quality dashboard](https://pokemon-rga-dashboard.vercel.app). Each prompt change on the time-series chart has a vertical marker; click any marker to jump to its version card. The dashboard reads `rga-closed-loop/prompts/history/*.yaml` at build time, so the repo is the single source of truth.

## Why a prompt enhancement was needed

Diagnosis from `eval-runs/2026-05-31-full.json`:

- Layer-1 **ability-lookup** category: 10% accuracy, 95% hard-recall. RGA correctly identifies ability *names* but fabricates their *mechanics*.
- Layer-1 **stat-lookup**: 40% / 100%. Same shape — correct numbers, embellished with wrong claims.
- Layer-2 **cross-source-synthesis**: 25% / 35%. Confused when sources disagree.

Root cause: pokemondb.net Pokémon pages list ability *names* in the vitals table but link out to dedicated `/ability/<name>` pages for the mechanic descriptions. We index the Pokémon pages, not the ability pages. RGA has no source content for ability mechanics → falls back to LLM general knowledge → hallucinates confidently.

The fix is two-pronged:

1. **Prompt enhancement** (this file) — tell RGA to refuse cleanly when the source doesn't cover the detail asked. Cheapest production fix; ships in minutes.
2. **Re-index ability pages** (future work) — actually have the mechanics in source. Larger work; tracked separately.

## Before this enhancement — what Coveo ships by default

When we went to apply the Pokemon-specific prompt on 2026-06-01, we discovered that the **"Prompt enhancement → Prompt instruction"** field on the `pokemon-rga` model still held Coveo's **default enterprise template**. The toggle was on, but the prompt content was an out-of-the-box placeholder containing unfilled brackets — never customized for any specific use case.

The default text (verbatim, reconstructed from the Console screenshot before it was replaced):

```
You are a subject matter expert representing [Enterprise Name] and must operate strictly within [Enterprise Domain]'s guidelines and applicable regulations. Your responses must reflect [Enterprise Name]'s values, tone, and content standards.
Do not offer personalized advice, opinions, or speculative commentary.
Use only factual, approved, or customer-provided content.
If a topic falls outside the approved scope, politely decline to answer or redirect to official resources.
Avoid referencing competitors, unverified tools, or external platforms unless explicitly allowed.
When uncertain, refrain from answering to avoid compliance or brand risks.
Maintain a [tone guidance — e.g., neutral, respectful, brand-aligned, professional, inclusive] tone in all responses.
Never generate or assist with content that violates safety, legal, privacy, or ethical standards.
Always prioritize [compliance/safety/accuracy/customer trust] based on [Company Name]'s core mission.
```

**Three observations worth carrying into the panel:**

1. **The placeholders (`[Enterprise Name]`, `[Company Name]`, `[tone guidance]`) were unfilled.** This is a generic template Coveo ships to every RGA model by default — it's effectively *unconfigured* for the customer's actual content domain.
2. **The default prompt encourages elaboration.** "Subject matter expert" framing tells the LLM it's authoritative on the topic — which encourages it to fill gaps from general knowledge rather than ground every claim in retrieved content. This is the latent cause of the embellishment pattern we observed in the 2026-05-31 eval.
3. **A customer who doesn't measure RGA quality wouldn't see this.** The default prompt produces *confident, fluent-sounding* answers — which look fine in spot-checks. The defect only surfaces under structured eval (which is exactly why Phase 6D exists). This is a textbook case of "without a quality measurement system, you don't know what you don't know."

This finding is itself an artifact of the diagnostic loop documented in [`rga-eval-methodology.md`](rga-eval-methodology.md) — and it strengthens the case for Phase 6F (closed-loop prompt-tuning), because today's "manually paste a Pokemon-specific prompt" step is exactly what the closed loop should automate.

## Custom prompt text (copy-paste into Coveo Console)

```
You answer Pokémon questions using ONLY the retrieved source documents from pokemondb.net and PokéAPI. Treat the retrieved content as the sole source of truth.

Hard rules:
1. Every factual claim must be directly supported by content in the retrieved sources. Do not introduce facts from outside knowledge.
2. If a source identifies an entity by name (e.g., an ability name in a vitals table) but does not describe its mechanic or details, state ONLY what is in the source. Do not infer, expand, or describe mechanics from general knowledge.
3. When the sources do not contain the answer to the asked question, say so explicitly with phrasing like: "The retrieved sources confirm [name] is one of [Pokémon]'s abilities but do not describe its in-battle mechanic." Do not invent.
4. Cite the source document for each factual claim using inline citations.
5. Prefer short, exact answers over long elaborations. If the question can be answered in one sentence, do so.

Style: terse, factual, no embellishment. When asked about Pokémon types, abilities, generations, stats, or evolutions — answer only what the sources support. When the sources don't cover a question, refuse cleanly rather than guessing.
```

## What we expect to see in tomorrow's eval

| Category | Baseline (2026-05-31) | Hypothesis after prompt change |
|---|---|---|
| Layer 1 ability-lookup | 10% / 95% | 60-80% / 95% (because honest refusals count as correct on the LLM judge's rubric — see `llm_judge.py` JUDGE_SYSTEM_PROMPT) |
| Layer 1 stat-lookup | 40% / 100% | 70-85% / 100% (less room to embellish on numbers) |
| Layer 1 type-lookup | 93% / 100% | unchanged (already good) |
| Layer 1 generation-lookup | 90% / 100% | unchanged |
| Layer 3 refusal categories | 80-100% | unchanged or slightly better |
| Overall accuracy | 62% | **target: ~75-80%** |

If the lift materializes, the time-series chart on the dashboard will show a visible step-change between 2026-05-31 and 2026-06-01 — the kind of panel-friendly visual we're optimizing for.

If the lift doesn't materialize, the diagnosis was wrong and we go to plan B: re-index ability pages and try again.

## Applying the change (one-time, ~5 min)

1. Coveo Admin Console → **AI & ML → Models**.
2. Click into the `pokemon-rga` model.
3. Scroll to the **Prompt enhancement → Prompt instruction** field (toggle should already be ON).
4. **Replace the existing default-template content** (see "Before this enhancement" section above) with the Pokemon-specific prompt from the code block above.
5. **Save**.
6. **No rebuild needed** for prompt-only changes — the next /generate request picks up the new prompt immediately.
7. Smoke-test from the live Atomic UI: ask "what abilities does gengar have" — expect either an honest refusal about Cursed Body's mechanic OR a strictly-from-source description.

## Applied state — change log

A short log of when the live prompt last changed, who applied it, and why. Update this section whenever the Console value is changed so the git history reflects production state.

### 2026-06-01 — Pokemon-specific grounding prompt (current live state)

- **Applied by:** Franck (manually, via Console — Phase 6F.2 will automate this going forward).
- **Replaces:** Coveo default enterprise template with unfilled `[Enterprise Name]` placeholders (see "Before this enhancement" section).
- **Rationale:** address the +85-pt accuracy/recall gap on Layer-1 ability-lookup surfaced by the 2026-05-31 eval. Tell RGA to ground every factual claim in retrieved content and to refuse cleanly when the source doesn't cover the asked detail.
- **Expected lift:** overall accuracy 62% → ~75-80% on the 2026-06-01 cron run, surfacing as a visible step-change on the dashboard's time-series chart.
- **Validation plan:** wait for the scheduled 06:00 UTC cron on 2026-06-01 (cleanest visual — two distinct dates), OR fire a manual workflow_dispatch full run for an immediate after-shot. Recommended: wait.
- **Rollback:** if the lift doesn't materialize, repeat the Console steps with the Coveo default template (text preserved in "Before this enhancement" above). Once Phase 6F.2 ships, rollback becomes `git revert` on the next prompt-change PR.

## Validating the change

Two ways to verify the lift before tomorrow's scheduled cron:

- **Manual full run from GitHub Actions** (~10 min, ~$0.55) — Actions tab → RGA daily eval → Run workflow → mode = full. Commits `eval-runs/2026-05-31-full.json` (overwrites today's baseline) so the dashboard shows the after-shot immediately.
- **Wait for the 06:00 UTC scheduled cron** — produces `eval-runs/2026-06-01-full.json`, which adds a new data point to the time-series. This is the cleanest visual for the panel (two distinct dates with the step-change between them).

The second option is recommended for the dashboard narrative; the first is useful for quick iteration on the prompt itself if needed.
