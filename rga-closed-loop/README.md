# rga-closed-loop — closed-loop RGA prompt-tuning (Phase 6F)

This is the system that **acts on** the measurements taken by [`rga-eval/`](../rga-eval/) and visualized by [`rga-dashboard/`](../rga-dashboard/). The three folders together form the production-grade AI quality story:

```
rga-eval/        →  measures quality      (Phase 6D)
rga-dashboard/   →  visualizes quality    (Phase 6D.6)
rga-closed-loop/ →  improves quality      (Phase 6F)  ← you are here
```

## What it does

```
DAILY CRON (rga-eval) writes eval-runs/YYYY-MM-DD-full.json
       │
       ▼
LAYER 2 — Analyzer (src/analyzer.py, ships in 6F.3)
       Reads latest eval-run vs previous
       Identifies worst-degraded categories
       Calls Sonnet 4.6: "given these failures, propose a prompt delta"
       Writes a new YAML to prompts/pokemon-rga.yaml
       Opens a PR (src/pr_opener.py)
       │
       ▼
HUMAN REVIEW GATE — you review + merge the PR
       │
       ▼
LAYER 1 — Apply script (src/apply.py, this commit)
       Reads prompts/pokemon-rga.yaml
       PUTs extraConfig.additionalAnswerInstructions to Coveo
       Verifies by re-fetch
       │
       ▼
Tomorrow's full eval shows lift (or not) on the dashboard
       │
       ▼
loop repeats
```

The PR review is the **safety gate**. Auto-apply (no human review) is explicitly out of scope — a bad prompt at 04:00 UTC silently degrading production is the failure mode we're preventing.

## Folder layout

```
rga-closed-loop/
├── README.md                   ← this file
├── pyproject.toml + uv.lock    ← uv-managed Python project
├── prompts/
│   ├── pokemon-rga.yaml        ← CURRENT live prompt + structured metadata
│   └── history/                ← previous versions, archived dated YAMLs
│       └── 2026-05-31-default.yaml  ← the Coveo default we replaced on 2026-06-01
├── src/
│   ├── schemas.py              ← Pydantic: PromptVersion + PromptProposal
│   ├── apply.py                ← Layer 1: PUT prompt to Coveo (this commit)
│   ├── analyzer.py             ← Layer 2: propose changes (Phase 6F.3, coming)
│   └── pr_opener.py            ← Layer 2: open PR with proposal (Phase 6F.4, coming)
└── tests/
    └── test_apply.py           ← unit tests (no live Coveo calls — respx mocks)
```

## Apply script — usage

```bash
cd rga-closed-loop
uv sync                                           # one-time setup
uv run python src/apply.py                        # dry-run (default): print diff, no write
uv run python src/apply.py --apply                # actually PUT to Coveo
uv run python src/apply.py --prompt-file path     # use a non-default YAML (e.g., for testing rollback)
```

**Dry-run is the default for a reason.** This script writes to a live production model. We want the no-flag invocation to be the safe one. The Phase 6F.5 cron workflow passes `--apply` explicitly because the PR-merge IS the human gate.

### Idempotency

If `prompts/pokemon-rga.yaml` matches what's already live in Coveo, the script reports `✓ Live prompt already matches YAML. No change needed.` and exits 0. Safe to run repeatedly.

### Auth

Needs `COVEO_ORG_ID` + `COVEO_ADMIN_API_KEY` in env (usually via `.env`). The admin key has `Models: View + Edit` — the judge key from Phase 6D is **not** enough. See [`docs/api-keys.md`](../docs/api-keys.md#phase-6f1--coveo-ml-models-api-surface-rga-prompt-management).

## YAML schema — what each field is for

See [`src/schemas.py`](src/schemas.py) for the canonical Pydantic definitions. Quick reference:

```yaml
model:
  display_name: pokemon-rga      # stable identifier (rebuild-safe)
  engine_id: genqa               # `genqa` = RGA. Only genqa models are valid targets.

prompt: |
  ...the actual Custom Prompt text that gets PUT to Coveo...

metadata:
  version: "1.0.0"                # bump major on breaking style changes
  applied_at: "2026-06-01T..."    # ISO 8601 UTC
  applied_by: "..."               # who/what applied it
  replaces: history/...yaml       # pointer to the version this replaced
  rationale: |                    # multi-line WHY we made this change
    ...
  expected_lift:                  # per-metric predictions for the analyzer
    overall_accuracy:        { from: 0.62, target: 0.78 }
    layer_1_ability_lookup:  { from: 0.10, target: 0.70 }
  validated_against: ""           # filled in by analyzer after post-change eval
  related_eval_run: "..."         # the eval that motivated this version
  related_methodology: "docs/rga-eval-methodology.md"
```

The metadata is what makes the closed loop work. The analyzer reads `expected_lift` vs `validated_against`'s actual numbers to detect "this change failed to deliver" patterns when proposing the next iteration.

## How to change the prompt manually (before the analyzer ships)

Until Phase 6F.3 lands, prompt changes happen in three steps:

1. Copy the current `prompts/pokemon-rga.yaml` to `prompts/history/YYYY-MM-DD-<slug>.yaml`
2. Edit the current `prompts/pokemon-rga.yaml`: update the `prompt` text, bump `metadata.version`, update `metadata.applied_at`/`applied_by`/`rationale`/`expected_lift`, point `metadata.replaces` at the history file you just wrote
3. Run `uv run python src/apply.py` (dry-run) to see the diff, then `--apply` to ship it

## How to roll back a bad prompt

```bash
# 1. Copy the desired previous version on top of the current YAML
cp prompts/history/2026-05-31-default.yaml prompts/pokemon-rga.yaml

# 2. Apply
uv run python src/apply.py --apply
```

The script's verification step re-fetches the model and confirms the live value matches what was sent. If it doesn't, exits with code 2 — fail loud, not silent.

## What's coming next (Phase 6F.3 onward)

- **6F.3** — `src/analyzer.py`. Reads eval-runs, identifies regressed categories, calls Sonnet 4.6 with tool-use forcing, returns a structured `PromptProposal`.
- **6F.4** — `src/pr_opener.py`. Wraps `gh pr create` with a templated body containing the analyzer's rationale + sample answer diffs.
- **6F.5** — GitHub Actions workflow chaining: eval cron commits → triggers analyzer → opens PR → human reviews + merges → triggers apply.py with `--apply` + smoke run.
- **6F.6** — `docs/rga-closed-loop.md` with the panel-quality narrative.
