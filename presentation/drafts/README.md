# Presentation drafts

Working drafts for the two panel presentations the Coveo FDE technical challenge requires. **These are drafts, not finals** — written as slide-by-slide markdown so you can iterate on content + flow before moving to actual slide software (Slides / Keynote / Pitch / etc.).

## What's in here

| File | What it is | Audience | Time | Phase |
|---|---|---|---|---|
| [`01-tech-deep-dive.md`](01-tech-deep-dive.md) | **Presentation #1, Topic 1** — Pokémon Challenge technical deep dive | Coveo experts | ~25 min total (10 talk + 5 demo + 10 Q&A) | 9A |
| [`02-customer-pitch.md`](02-customer-pitch.md) | **Presentation #1, Topic 2** — How Coveo transforms `<enterprise customer>`'s search | Coveo experts (framed as customer decision-makers) | ~25 min total (10 talk + 5 demo + 10 Q&A) | 9B |
| [`03-escalation-recovery.md`](03-escalation-recovery.md) | **Presentation #2** — Operational incident response & recovery | Coveo experts + your own executives | ~25 min total (10 talk + 15 Q&A) | 10 |

## Doc-overlay rules (from the project plan)

Two authoritative docs underpin the challenge:

- **Doc 1** — `Technical_Challenge_-_FDE.pdf` — the FDE-specific brief. **Wins when in conflict with Doc 2** on panel mechanics. Its Topic 2 is the operational scenario in `03-escalation-recovery.md`.
- **Doc 2** — `Pokemon Challenge (Pre-Sales) - 2026.pdf` — defines the Pokémon-related presentation with two sub-topics, both covered in `01-tech-deep-dive.md` and `02-customer-pitch.md`.

> The "Senior Director, Technical Customer Success" role mention in Doc 1 is a typo — the role is **FDE** everywhere.

## Pending inputs before finalizing

- [ ] **Topic 2 — which enterprise customer to target.** `02-customer-pitch.md` includes 3 candidate options with rationale; pick one (or substitute) and the template adapts.
- [ ] Final slide-software choice (Slides / Keynote / Pitch / Reveal.js)
- [ ] Whether to record a backup demo video in case live demo fails on panel day

## Conventions inside each draft

Each slide has a standard block:

```markdown
## Slide N — Title (≈Xs)

**Visual**: short description of what should be on the slide

**Speaker notes**:
- bullets you actually say
- one bullet per sentence-ish, in delivery order

**Key message**: the one-line takeaway

**Q&A trap**: known pushback to pre-arm for (optional)
```

The drafts also flag where to lean on the panel-shareable docs in [`docs/`](../../docs/) — `rga-eval-methodology.md`, `observability.md`, `caching-strategy.md`, `passage-retrieval.md`, `detail-page.md`, `mcp-integration.md` — instead of re-explaining material verbatim.

## Live URLs to reference in any deck

- Atomic main page: https://pokemon-search-one-chi.vercel.app
- Pokémon Detail Page: https://pokemon-search-one-chi.vercel.app/pokemon.html?name=charizard
- RGA quality dashboard: https://pokemon-rga-dashboard.vercel.app
- Grafana query-observability dashboard: https://charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452
- GitHub repo: https://github.com/benichou/coveo-pokemon-challenge

## How to use these drafts

1. Read top-to-bottom once for flow
2. Time yourself reading the speaker notes aloud — adjust pacing
3. Cut ruthlessly anywhere over time budget
4. Lock the slide deck (visual) only after the narrative is final
5. Two dry-runs before panel day; record one to self-critique
