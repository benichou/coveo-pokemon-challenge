# CLAUDE.md — instructions for Claude Code sessions in this repo

This is the [Coveo FDE technical challenge](https://github.com/benichou/coveo-pokemon-challenge) — a Pokémon search experience built on the Coveo Cloud Platform, including a quantitative AI-quality evaluator and a closed-loop prompt-tuning system. The repo is intentionally **as-code** wherever possible.

> **For a richer narrative** of how the project got built, why each decision was made, and what's left: see [`README.md`](README.md) (panel-shareable) and [`~/.claude/plans/so-we-are-supposed-purrfect-bachman.md`](~/.claude/plans/so-we-are-supposed-purrfect-bachman.md) (working plan). This file is the **operational** doc — what to do, what not to do, where to find things.

## Repository at a glance

| Folder | What lives there | Phase |
|---|---|---|
| `config/` | Versioned Coveo configuration (fields, source defs, scraping rules, URL filters) | 1–2 |
| `scripts/` | Idempotent bash scripts driving the Coveo REST API (bootstrap, validate, audit) | 1–6A |
| `tests/` | pytest+httpx integration tests (URL parity, leak detection, field extraction) | 1+ |
| `push-pokemon/` | Python Push-source ingestion (Source B; PokéAPI-enriched per-form docs) | 4 |
| `atomic-search/` | Vite-hosted local Atomic UI (the main search experience) | 5 |
| `rga-eval/` | RGA Skill Evaluator — 100-Q golden dataset + Sonnet 4.6 LLM-as-judge | 6D |
| `eval-runs/` | One JSON per eval, committed as the time-series database | 6D |
| `rga-dashboard/` | Vercel-hosted dashboard reading eval-runs/*-full.json at build time | 6D.6 |
| `rga-closed-loop/` | Analyzer + apply script + guardrails (autonomous prompt tuning) | 6F |
| `.github/workflows/` | `rga-eval-daily.yml` (06:00 UTC eval cron) + `closed-loop-daily.yml` (post-eval analyzer + apply with guardrails) | 6D.7 + 6F.5 |
| `docs/` | API key recipes, ML-model notes, deploy runbook, prompt + methodology | cross-phase |

**Live URLs:**
- RGA quality dashboard: https://pokemon-rga-dashboard.vercel.app
- GitHub repo: https://github.com/benichou/coveo-pokemon-challenge

## Where to look first when working in this repo

When the user asks about… | Read this first
---|---
API keys, privileges, leak mitigation | [`docs/api-keys.md`](docs/api-keys.md)
GitHub Actions secrets / Vercel deploy | [`docs/deploy.md`](docs/deploy.md)
The current RGA Custom Prompt + history | [`rga-closed-loop/prompts/pokemon-rga.yaml`](rga-closed-loop/prompts/pokemon-rga.yaml)
Why the current prompt looks the way it does | [`docs/rga-prompt.md`](docs/rga-prompt.md) (narrative) + [`docs/rga-eval-methodology.md`](docs/rga-eval-methodology.md) (panel-shareable diagnostic loop)
RGA + Semantic Encoder model wiring | [`docs/ml-models.md`](docs/ml-models.md)
Coveo source / field / scraping config | `config/` (read the README inside)
Past eval results | `eval-runs/YYYY-MM-DD-full.json` + dashboard
The autonomous cron's behavior | [`rga-closed-loop/src/closed_loop_run.py`](rga-closed-loop/src/closed_loop_run.py) + [`rga-closed-loop/src/guardrails.py`](rga-closed-loop/src/guardrails.py)

## Claude Code skills available

```
/rga-eval               → run / inspect the RGA eval (Phase 6D)
/rga-closed-loop        → drive the closed-loop prompt tuning (Phase 6F)
```

Both auto-trigger on related natural-language asks ("what's the latest accuracy?", "tune the prompt", "roll back"). See `.claude/skills/<name>/SKILL.md` for each skill's full mode list.

## Common workflows

```bash
# Run the RGA evaluator locally (full 100-Q run; ~10 min, ~$0.60 Anthropic)
cd rga-eval && uv run python src/main.py

# Show the latest eval results
cd rga-eval && uv run python src/show.py

# Apply the current prompt YAML to Coveo (dry-run first; --apply to write)
cd rga-closed-loop && uv run python src/apply.py
cd rga-closed-loop && uv run python src/apply.py --apply

# Run the closed-loop orchestrator locally (analyzer + guards; no write without --apply)
cd rga-closed-loop && uv run python src/closed_loop_run.py --dry-run

# Run the dashboard dev server
cd rga-dashboard && npm install && npm run dev

# Run all unit + integration tests
cd tests && uv run pytest
cd rga-eval && uv run pytest
cd rga-closed-loop && uv run pytest
```

## Conventions to follow

### Git

- **The user commits manually.** Never auto-`git add`/`git commit`/`git push` — even when it seems obvious. Always present the commit command for the user to run themselves.
- **Commit messages:** Conventional Commits prefix (`feat:`, `fix:`, `docs:`, `chore:`). Subject ≤ 70 chars. Wrap body at ~72 chars. Always include the `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer when Claude meaningfully contributed.
- When the user asks for a shorter commit message, **shorter is much better than "complete"** — they review every commit themselves.
- **Pre-commit hooks** (ruff, ruff-format, trailing whitespace, end-of-file fixer, check-yaml, check-json) auto-modify files; if a commit aborts because "files were modified by this hook", just `git add -A` and retry — the hooks already fixed it.

### Branching — trunk-based development

This repo follows **trunk-based development**: `main` is the single shared trunk, and all work lands on it directly (or via very short-lived branches that merge within hours). No long-lived feature branches, no `develop`/`staging` mirror, no GitFlow.

**What that means in practice for Claude Code sessions in this repo:**

- **Default branch for all commits = `main`.** When the user says "commit + push", that goes to `main`. Don't ask which branch unless they explicitly say so.
- **Don't create branches without an explicit user ask.** Even for "experimental" work — small enough changes go straight to `main`; larger ones the user will explicitly request a branch for.
- **The four legacy `feature/*` branches** (essential/intermediate/advanced/bonus) exist from an earlier planning phase but are abandoned. Don't reference them, don't merge to them, don't push to them.
- **Continuous integration in spirit**: every push to `main` should be releasable. `pr-checks.yml` runs pre-commit + tests + build + TruffleHog on every push to `main` AND every PR — so the same gates apply whichever path is used.
- **PRs are optional, not required.** This is a personal repo with one human contributor. The user commits directly to `main`. If a change is risky enough to want PR review, the user will ask for a branch + PR explicitly.
- **Force-push to `main` is allowed but rare.** Per the security section, always back up the pre-rewrite SHAs to `refs/backup/*` first and confirm with the user before running.

**What this rules out:** Don't propose "let's create a feature branch for this", don't ask "should I open a PR?", don't suggest GitFlow-style release branches. If the change is large enough that a feature branch would help, the user will explicitly request one.

### Python

- All Python projects are `uv`-managed (`pyproject.toml` + `uv.lock` committed). Always invoke with `uv run python ...`, never bare `python ...`.
- Python 3.12+ required (rga-closed-loop uses 3.13).
- Type hints throughout; Pydantic for data validation at every boundary.
- Tests use `pytest`; respx for httpx mocking; no live API calls in unit tests.

### Code style

- `ruff` + `ruff-format` are the linters (config in `ruff.toml`). Pre-commit enforces.
- Line length: 88 chars (ruff default).
- Imports: alphabetical (`isort` via ruff).
- Function names: `snake_case` (ruff N802 enforced — fails on camelCase).

### Documentation

- New docs go in `docs/`. Cross-link generously.
- The README's "For the panel" callouts at the top should stay panel-shareable (no jargon, no insider context).
- Every panel-shareable doc has companion artifact references — methodology ↔ data ↔ code.

## Security — non-negotiable

- **Never paste credentials in chat.** Per `~/.claude/rules/security.md`, warn the user if they paste a real credential. **NB:** This repo's user has a recurring issue with their IDE auto-sharing selected `.env` lines into chat. When you see a credential in a system reminder, flag it briefly and recommend rotation. Don't read `.env` directly unless asked.
- **5 Coveo API keys live in `.env`** (gitignored), each least-privilege-scoped. See `docs/api-keys.md` for what each can/cannot do. Never recommend granting a key broader scope than its purpose requires.
- **`.env.example`** carries placeholder values only. Mirror its structure if adding a new env var.
- **GitHub Actions secrets** are a separate namespace from local `.env`. Both must be kept in sync for the daily eval + closed-loop crons to work.
- **Anthropic key is personal**, not corporate. Using a corporate Anthropic key on this repo would violate `~/.claude/rules/security.md`.
- **Force-pushing main:** allowed (this is a personal repo). But always back up the pre-rewrite SHAs to `refs/backup/*` first, and confirm with the user before running.

## What NOT to do

- ❌ Auto-commit or auto-push (user does git manually)
- ❌ Bypass pre-commit hooks (`--no-verify`)
- ❌ Read `.env` unprompted (creates a permanent record in chat if the IDE leaks)
- ❌ Apply changes to Coveo without explicit user confirmation, even when guardrails would allow it
- ❌ Modify `rga-eval/golden/questions.json` without explicit user instruction — it's the eval's ground truth; changes invalidate time-series comparisons
- ❌ Mutate `prompts/history/` entries — they're immutable archives
- ❌ Disable / loosen the closed-loop guardrails without an explicit user ask; the conservative defaults are deliberate
- ❌ Re-run a full daily eval if today's already exists unless asked (would overwrite the dashboard's source data)

## Decision sequencing the user prefers

- **Verify each step before claiming things work.** Empirical confirmation > optimistic claims. Read-only spike before any write.
- **Cost vs information value** beats appeal of the technical solution. Pick the cheapest intervention that yields the most information; ship that first.
- **Closed-loop > one-shot fixes.** When given the choice between "ship a fix once" and "build a system that proposes fixes," pick the loop.
- **Code-as-source-of-truth > manual UI ops.** When a feature can be done via API OR Console, prefer API + version-controlled config.
- **Human-in-the-loop on production writes.** Auto-apply without review is off the table unless gated by explicit guardrails. PR review or `/rga-closed-loop analyze` interactive review or guardrails-only — pick one, not none.

## When opening Claude Code in this repo

For project isolation (no Carta global skills or MCP servers loading), launch from the repo root with:

```
claude --setting-sources project --strict-mcp-config --mcp-config .claude/mcp.json
```

This restricts Claude Code to the repo's own `.claude/` configuration only. See `README.md` "Opening Claude Code with only this repo's tooling" for the full rationale + caveats.
