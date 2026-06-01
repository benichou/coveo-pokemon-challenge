---
name: rga-closed-loop
description: Drive the closed-loop RGA prompt-tuning system. Args control mode — 'analyze' runs the LLM analyzer + asks the user to approve applying its proposal, 'apply' pushes the current YAML to Coveo, 'verify' read-only checks live-vs-YAML, 'rollback <date>' restores from history, no args shows the current state. Use this when the user asks to "tune the RGA prompt", "run the analyzer", "apply the prompt", "roll back the prompt", or anything about updating the system prompt on the pokemon-rga model.
---

# RGA Closed-Loop — Claude Code Skill

This skill operates the Phase 6F closed-loop system in `rga-closed-loop/`. It takes the RGA Skill Evaluator's measurements (Phase 6D), runs an LLM-assisted analyzer that proposes prompt refinements, and applies approved changes to Coveo's RGA model via REST API — all without touching the Coveo Console.

The skill is the **interactive driver**. The autonomous cron driver (Phase 6F.5, future) shares the same analyzer + apply core.

## When this skill applies

Invoke this skill when the user asks any of:
- "Run the closed-loop analyzer" / "let's tune the prompt" / "what would the analyzer suggest?"
- "Apply the prompt" / "push the prompt to Coveo" / "update the RGA system prompt"
- "Roll back the prompt" / "restore the previous prompt"
- "Verify the live prompt matches the repo"
- "Show me the current closed-loop state"

## Arguments

| User-provided args | What to do |
|---|---|
| (none) or `state` or `status` | Show the current closed-loop state: the YAML version currently committed, whether live Coveo matches it, time since last apply, last analyzer proposal date. No API writes. |
| `analyze` | Run the LLM analyzer against the latest eval. Present the proposal in chat with rationale + expected lift + sample answers. **Then ASK the user whether to apply.** If approved: archive current YAML to history/, update prompts/pokemon-rga.yaml, run apply.py --apply, verify via re-fetch. Print the per-step results. |
| `apply` | Run apply.py against the current YAML. Dry-run first (shows diff); ask user to confirm; then `--apply`. Skip the analyzer step entirely — use this when the user has manually edited the YAML and wants to ship it. |
| `force` | Same as `apply` but with `--force` to bypass the "already matches" early-exit. Useful for write-path drills / rollback recovery / re-syncing after a Console-side edit. |
| `verify` | Read-only check that live Coveo matches `prompts/pokemon-rga.yaml`. Reports byte-identical / differs / unreachable. |
| `rollback <date>` | Restore `prompts/history/<date>-*.yaml` over the current `prompts/pokemon-rga.yaml`. Archive what was current to history/ first. Then ask the user to confirm `apply` (do not auto-apply on rollback — extra safety). |

## How to execute each mode

All commands run from the **repo root**, not the `rga-closed-loop/` subdir — the apply / analyzer scripts handle their own working-directory resolution. Use `cd rga-closed-loop && uv run ...` for the Python commands.

### State / status (default)

```bash
cd rga-closed-loop && uv run python src/apply.py
```

This is the dry-run mode of apply.py — prints the YAML version + live status + diff (or "no change needed"). Read-only; safe default.

If you want a more thorough state report, also show:

```bash
# What's the live prompt's first 200 chars?
cd rga-closed-loop && uv run python -c "
import os, httpx
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('.env').resolve())
ORG = os.environ['COVEO_ORG_ID']; KEY = os.environ['COVEO_ML_MODELS_API_KEY']
models = httpx.get(f'https://platform.cloud.coveo.com/rest/organizations/{ORG}/machinelearning/models', headers={'Authorization': f'Bearer {KEY}'}).json()
rga = [m for m in models if m['modelDisplayName'] == 'pokemon-rga'][0]
print(rga['extraConfig']['additionalAnswerInstructions'][:200] + '...')
"
```

Mention to the user that the YAML is the source of truth in git; live Coveo is what gets queried.

### Analyzer + interactive apply

This is the full closed-loop run. Multi-step:

**Step 1 — run the analyzer, capture proposal to a temp JSON.**

```bash
cd rga-closed-loop && uv run python src/analyzer.py --emit /tmp/rga-proposal.json
```

The analyzer prints its proposal human-readably to stdout AND writes the structured JSON to `/tmp/rga-proposal.json`. Cost: ~$0.04 in Sonnet tokens. Time: ~10s.

**Step 2 — show the user the key fields from the proposal.** Highlight:
- The analyzer's confidence (be cautious of low confidence — below 0.6 means review extra carefully)
- The expected lift per metric
- The rationale (the most important field — this is the WHY)
- 1-2 sample before/after answers to make the change concrete

**Step 3 — ASK the user explicitly: "Approve and apply this prompt change?"**

The skill's safety gate is this interactive prompt. Do not skip it. Wait for the user's response.

**Step 4 — if the user approves:**

```bash
# (a) Archive the current YAML to history/ — use today's date + a descriptive slug.
TODAY=$(date -u +%F)
SLUG="pre-analyzer-vN"  # Increment vN by reading current YAML's version field, e.g., v1.0.0 → v1.0.1
cp rga-closed-loop/prompts/pokemon-rga.yaml \
   "rga-closed-loop/prompts/history/${TODAY}-${SLUG}.yaml"

# (b) Read /tmp/rga-proposal.json and merge into a new pokemon-rga.yaml.
# Use a Python one-liner or just construct it carefully:
cd rga-closed-loop && uv run python -c "
import json, yaml
from pathlib import Path
proposal = json.loads(Path('/tmp/rga-proposal.json').read_text())
current = yaml.safe_load(Path('prompts/pokemon-rga.yaml').read_text())
# Bump version (minor for refinements; major for breaking style changes).
old_version = current['metadata']['version']
new_version = bump_minor(old_version)  # Substitute the real bump logic in your head — e.g., 1.0.0 → 1.1.0
current['prompt'] = proposal['new_prompt']
current['metadata']['version'] = new_version
current['metadata']['applied_at'] = '<today's ISO 8601 UTC>'
current['metadata']['applied_by'] = 'Franck via /rga-closed-loop skill (analyzer-proposed)'
current['metadata']['replaces'] = f'history/{TODAY}-{SLUG}.yaml'
current['metadata']['rationale'] = proposal['rationale']
current['metadata']['expected_lift'] = {k: dict(v) for k, v in proposal['expected_lift'].items()}
current['metadata']['validated_against'] = ''  # filled in by analyzer next time
Path('prompts/pokemon-rga.yaml').write_text(yaml.safe_dump(current, sort_keys=False, allow_unicode=True))
"

# (c) Run apply.py --apply
cd rga-closed-loop && uv run python src/apply.py --apply
```

Then tell the user: (1) the change is live in Coveo, (2) tomorrow morning's eval cron will measure the impact, (3) the YAML is updated in their working tree — they need to `git add` + `git commit` + `git push` to land it in the repo.

**Step 5 — if the user declines:**

Discard. Leave the YAML untouched. Print "no change applied; proposal saved to /tmp/rga-proposal.json for review."

### Apply (no analyzer — manual YAML edits)

```bash
# Dry-run first to show the diff
cd rga-closed-loop && uv run python src/apply.py

# Then confirm + apply
cd rga-closed-loop && uv run python src/apply.py --apply
```

Use this when the user has manually edited `prompts/pokemon-rga.yaml` and wants to push their hand-crafted change to Coveo without running the analyzer.

### Force-apply

```bash
cd rga-closed-loop && uv run python src/apply.py --apply --force
```

Bypasses the "already matches" early-exit. The PUT happens even if there's nothing semantically different to change. Useful for write-path drills, rollback re-syncs, and confirming the live value is byte-identical to the YAML (not just semantically equivalent).

### Verify (read-only)

```bash
cd rga-closed-loop && uv run python src/apply.py
```

Same command as the default state mode. If the script exits with `✓ Live prompt already matches YAML. No change needed.`, live Coveo matches the repo's YAML. If it shows a diff, they're out of sync — explain to the user that either (a) the YAML has uncommitted edits that haven't been pushed yet, or (b) someone made a Console-side edit bypassing the apply script.

### Rollback

```bash
# List available history entries
ls -la rga-closed-loop/prompts/history/

# Restore one over the current YAML
cp rga-closed-loop/prompts/history/<date>-<slug>.yaml \
   rga-closed-loop/prompts/pokemon-rga.yaml

# Then show a diff against live and ask the user to confirm apply
cd rga-closed-loop && uv run python src/apply.py
# If user confirms:
cd rga-closed-loop && uv run python src/apply.py --apply
```

Always require explicit user confirmation before the apply step on a rollback — never auto-apply on rollback even if the rest of the skill would.

## Interpreting analyzer output

When showing the proposal to the user, frame it in panel-friendly terms:

| Analyzer output | What it means |
|---|---|
| **confidence ≥ 0.8** | Analyzer is highly confident this change will deliver the predicted lift. Reasonable to apply. |
| **confidence 0.6-0.8** | Calibrated uncertainty. The change is plausible but worth reading the rationale carefully before applying. |
| **confidence < 0.6** | Experimental — the analyzer is flagging this as a guess. Review the rationale + sample answers carefully; consider holding off and waiting for more eval data. |
| **new_prompt == current_prompt** | Analyzer determined no change is needed. Healthy state. |
| **Expected lift target close to 1.0 across all metrics** | Be suspicious — analyzer may be overconfident. Verify by reading the sample before/after answers — do they actually look better? |

## What this skill should NOT do

- Don't auto-apply analyzer proposals without user approval. The interactive safety gate is the skill's primary safety guarantee.
- Don't commit + push the YAML change after applying — git is the user's domain (per their stated preference).
- Don't modify `rga-closed-loop/prompts/history/` entries — those are immutable archives.
- Don't run the analyzer on a different day's eval data than the latest available — the analyzer expects to operate on the most recent measurement.
- Don't change the apply.py / analyzer.py source as part of skill operation — those are infrastructure code, not config.

## What to mention if relevant

- The analyzer uses **Sonnet 4.6** (`claude-sonnet-4-5-20250929`) via Anthropic tool-use forcing. ~$0.04 per call.
- The apply step PUTs to `/rest/organizations/{org}/machinelearning/models/{id}` with the full model body. Verified live on 2026-06-01.
- The five API keys involved: `COVEO_ML_MODELS_API_KEY` for the apply (Machine Learning Models: Edit), `ANTHROPIC_API_KEY` for the analyzer. The other three keys (push / admin / search / judge) are not used by the closed-loop system.
- The full architecture is documented in the plan (`~/.claude/plans/so-we-are-supposed-purrfect-bachman.md` — Phase 6F section) and in [`rga-closed-loop/README.md`](../../rga-closed-loop/README.md).
- The autonomous cron path (Phase 6F.5, not yet built) would replace this skill's interactive gate with rule-based guardrails (confidence threshold, rate limit, auto-rollback if next-day eval regresses by >5pts).
