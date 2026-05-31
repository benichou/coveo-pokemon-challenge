---
name: rga-eval
description: Run or inspect the RGA Skill Evaluator. Args control mode — 'run' / 'full' for a fresh 100-question eval, 'smoke' for a 5-question smoke test, 'failures' to drill into failing questions, 'hallu' to drill into hallucinations, no args for the latest run summary. Use this when the user asks to "run the eval", "check RGA quality", "see the latest accuracy", or to investigate specific failures.
---

# RGA Skill Evaluator — Claude Code Skill

This skill operates the RGA Skill Evaluator (Phase 6D) in `rga-eval/`. It evaluates Coveo RGA answer quality against a 100-question golden dataset, computes accuracy / precision / hard-recall / citation-precision, and writes time-series JSON to `eval-runs/`.

## When this skill applies

Invoke this skill when the user asks any of:
- "Run the RGA eval" / "let's evaluate RGA" / "kick off the evaluator"
- "What's the latest RGA accuracy?" / "show the latest eval results"
- "What questions are failing?" / "where is RGA hallucinating?"
- "Run a smoke test of the evaluator"

## Arguments

| User-provided args | What to do |
|---|---|
| (none) or `latest` or `show` | Show the latest eval run summary + category breakdown (no API calls; cheap; instant) |
| `run` or `full` | Run a fresh 100-question evaluation (~10 min, ~$0.60 in Sonnet tokens). Confirm with user before kicking off if the latest run is fresh (same day). |
| `smoke` | Run a 5-question smoke test (~30s, ~$0.03). Useful after code changes. |
| `failures` | Show the latest run's failing questions in detail (with question text, RGA answer, judge reasoning). |
| `hallu` or `hallucinations` | Same but filtered to questions where RGA hallucinated. |
| `compare <date1> <date2>` | If both dates exist, diff the metrics between two runs. Read both JSON files and present a side-by-side table. |

## How to execute each mode

All commands run from `rga-eval/` directory. The project is uv-managed; `uv run` handles deps automatically.

### Latest results (default)

```bash
cd rga-eval && uv run python src/show.py
```

Output: summary metrics + category breakdown. Pipe through `| head -40` if the user wants only the headline.

### Full eval run

```bash
cd rga-eval && uv run python src/main.py
```

This takes ~10 minutes. **Run in the background** (Bash `run_in_background: true`) and tell the user you'll be notified when it completes. While waiting, you can show the previous results so they have something to look at.

After completion, automatically run `src/show.py` to display the new results.

### Smoke test (5 questions)

```bash
cd rga-eval && uv run python src/main.py --limit 5
```

Foreground is fine (~30s).

### Failure detail

```bash
cd rga-eval && uv run python src/show.py --failures
```

Shows every failing question with the judge's reasoning. For long output, suggest piping through `head` or grepping by `--category`.

### Hallucination detail

```bash
cd rga-eval && uv run python src/show.py --hallu
```

Same shape as `--failures` but filtered to questions where the judge flagged a hallucination.

### Compare two runs

```bash
ls eval-runs/
```

List all available dates, then:

```bash
cd rga-eval && uv run python src/show.py 2026-05-31 --quiet
cd rga-eval && uv run python src/show.py 2026-06-01 --quiet
```

Build a side-by-side table from the two outputs. Highlight which metrics moved up/down and by how much.

## Interpreting results

When presenting metrics, remind the user what each means in plain terms:

| Metric | What it measures | Range |
|---|---|---|
| **Accuracy** | % of questions where the overall answer is correct (LLM judge) | 0–100% |
| **Precision** | % of answers without any hallucinated/false claim (LLM judge) | 0–100% |
| **Hard recall** | % of expected key facts mentioned in the answer (deterministic substring) | 0–100% |
| **Citation precision** | % of citations RGA gave that match the golden citation set | 0–100% |

Common patterns to call out:
- **Hard recall >> accuracy** → RGA mentions the right facts but embellishes with extras that may be wrong (the "helpful elaboration" problem). Suggests tuning the RGA prompt for conciseness.
- **High Layer 1 hallucination on ability-lookup specifically** → known content gap; abilities are unstructured body text on Source A. Fix would be to push abilities to Source B for all Pokemon.
- **Layer 3 accuracy < 80%** → RGA over-fires on non-questions or refuses appropriately. Check the specific Layer 3 failures.

## What this skill should NOT do

- Don't modify `rga-eval/golden/questions.json` without explicit user instruction — the dataset is the eval's ground truth and changing it invalidates time-series comparisons.
- Don't re-run a full eval if one already exists for today's date unless the user explicitly asks (it would overwrite the existing `eval-runs/YYYY-MM-DD.json`).
- Don't push to remote or commit new eval runs automatically — that's a user decision.

## Auxiliary commands worth knowing

```bash
# List all past eval runs
ls -la eval-runs/

# Quick view of just the headline number
cd rga-eval && uv run python src/show.py --quiet

# Re-run today's eval (overwrites today's JSON)
cd rga-eval && uv run python src/main.py
```

## What to mention if relevant

- The eval uses **Sonnet 4.6** (`claude-sonnet-4-5-20250929`) as the LLM judge via Anthropic's tool-use forcing — guaranteed structured output via a Pydantic schema.
- A full run is ~$0.60 in Anthropic tokens; cost the user incurs is the per-eval Sonnet cost.
- The eval requires three env vars in `.env`: `COVEO_RGA_JUDGE_API_KEY`, `COVEO_SEARCH_API_KEY`, `ANTHROPIC_API_KEY`.
- The full architecture is documented in the plan (`~/.claude/plans/so-we-are-supposed-purrfect-bachman.md` — Phase 6D section).
