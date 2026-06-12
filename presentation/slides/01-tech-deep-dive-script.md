# Pres 1 / Topic 1 — Tech Deep-Dive · LIVE SCRIPT
> Fallback teleprompter. Read only if you stall. `[ ]` = stage cue. North star: **three surfaces · two loops · one Coveo brain.**

---

## 1 · Cover
"Hi — I'm Franck. Over ~10 minutes I'll walk through the Pokémon Challenge build — live demo early, then the choices behind it, then Q&A.
Everything's live right now: four URLs on this slide. Feel free to follow along on your phone."

## 2 · What I built
"The brief: index pokemondb into a Coveo org and ship a search experience. I went full ambition — every advanced item, the bonus, plus three things the brief didn't ask for.
The headline: **one Coveo org — one index, one pipeline, four ML models — powering three surfaces.** A list page on Atomic, a detail page on Headless+React, an MCP server for AI agents. Same brain, three front-doors."

## 3 · Architecture
"One org, three surfaces, two loops. Four flows.
[ingest] **Dual-source** — pokemondb's sitemap into a Sitemap source, PokéAPI variants through a Python Push source, into one index — 1,353 docs.
[org] One default pipeline, four ML models on it.
[surfaces] Three front-doors on that one brain.
[right] The closed quality loop — daily eval, analyzer, guardrails, apply.
[left] Parallel observability — every search logged to Grafana, token server-side.
Now let me show it running."

## 4 · Live Demo  [HARD CAP 4:00]
[0:00] "You've seen the architecture — let me show it running."
[Atomic] Type `charizard`. "AI answer, grounded, with a citation — same primitive an enterprise uses for their own LLM." Click Fire + Source facets. "Both sources, one ranked list."
[Detail] "Three Coveo queries in parallel — Headless+React, not Atomic. Right SDK per surface."
[MCP] `/pokemon-mcp demo`. "Same org, now from Claude Code. Zero code per client. Watch it chain tools — realizes fetch needs an ID, calls search first."
[Dashboard] "Eval runs every morning. Markers are the loop applying prompts. 62% baseline to ~76% today, precision near 90%. Production AI is a loop, not a deploy."
[Close] "That's it running — now the choices behind it, starting with ingestion."

## 5 · Why dual-source
"Remember the 1,353 docs mixing in the list? Two sources, unified. Why two?
**Sitemap source** — near-zero effort, Coveo crawls and throttles, one doc per canonical page.
**Python Push pipeline** — I own the code and the throttling, but I get on-demand freshness and **one doc per form** — Mega, Hisuian, Galarian — which the sitemap collapses.
Not 'one is right' — sitemap for breadth, Push for depth and form identity. **Ingestion is a data question, not a tooling question.**"

## 6 · Code vs Console
"Is it really all code? Let me be precise.
[left] Everything governing the search experience — fields, source, scraping, filter, ML behavior, MCP config — is versioned JSON/YAML applied via REST. One bootstrap script provisions a fresh org.
[right] Four one-time steps need the Console: org creation, API-key minting, ML-model creation, MCP-server creation. The MCP one has no admin API yet — I verified, eight endpoints all 404.
So: search-experience config is 100% code; the four Console steps are one-time, by Coveo's design."

## 7 · Four ML models
"Four models on one pipeline. The brief asks for RGA and Query Suggest — I added Semantic Encoder and Passage Retrieval.
**RGA** — the grounded answer; prompt as YAML, tuned overnight by the loop.
**Semantic Encoder** — why 'what type is charizard' finds the doc that never says that phrase.
**Query Suggest** — type-ahead; I solved cold-start with 152 seed queries via the Default Queries CSV.
**Passage Retrieval** — verbatim passages, the primitive an enterprise uses to ground their own LLM. That's my bridge to the pitch."

## 8 · Three surfaces + skills
"Same brain, three consumption modes — and the lens is *who each is for.*
Two are browser-first: Atomic for a standard list-and-facets page, Headless when you need composition.
The third — MCP — is for **AI agents.** Same index, any MCP client, zero per-client code. The 2026 question is 'how does our content power our AI agents?' — Coveo's answer is 'your index already does.'
And two Claude Code skills operate across all three — `/rga-eval` measures quality, `/rga-closed-loop` tunes the prompt. Next two slides."

## 9 · rga-eval (measure)
"The brief didn't ask for this. I built it because the enterprise question is: how do you know your AI is working?
Every morning a 100-question golden set — 50 fact, 35 synthesis, 15 edge — runs against RGA, scored two ways: a deterministic substring check, and Sonnet as judge for accuracy and precision. ~55 cents a month.
Output: one JSON per day committed to the repo — the commit history *is* the time-series database. Auto-published to the dashboard you saw."

## 10 · rga-closed-loop (act)
"Measurement without action is a dashboard nobody reads. The loop acts — only when five guardrails pass.
It reads the last five eval runs, computes persistence and drift, so noise doesn't trigger changes. Sonnet proposes a new prompt. Then five guardrails: confidence under 0.80, lift under 5 points, last apply under 3 days, a sanity check, and auto-rollback if tomorrow drops more than 5 points.
It ran for real — v1.0.0 to v1.1.0. Predicted 78%, measured 79% — within one point. Precision 71 to 92. And it hasn't changed the prompt since — it measures every day and correctly decides *not* to act. **That restraint is the guardrails working.**
**Production AI isn't a model — it's a loop.**"

## 11 · What I learned
"Three lessons.
**One** — inspect the data before choosing ingestion. The dual-source split came from reading HTML and JSON, not a pattern.
**Two** — closed loops compound, static prompts decay. Build the measurement loop first.
**Three** — vector plus LLM doesn't model *relationships.* 'Which Fire-types evolve from Water-types' — neither SE nor RGA traverses the edges between entities. That's a knowledge-graph problem, and where I'd take this next."

## 12 · Production hardening
"It runs and behaves — but it's not production-grade yet. Four honest gaps, all known engineering work.
**Hosting** — never load-tested; concurrency ceiling unknown. **Auth — the big one** — it uses a search API key; production needs short-lived per-user tokens, SSO, Security Identities. **Monitoring** — no APM, no SLOs. **The loop** — guardrails exist but have never fired in anger; I haven't fault-injected a bad prompt to prove rollback.
All four are well-known fixes. I shipped what time allowed and I know exactly what production looks like from here."

## 13 · Thank you / Q&A
"That's the build. Three surfaces, two loops, one Coveo brain. All four URLs are live — follow along during Q&A.
Happy to take questions — the build, the choices, what I'd ship next, or how it maps to a customer."
