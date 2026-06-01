# Coveo Pokemon Challenge

Forward Deployed Engineer technical challenge for Coveo. A custom search experience built on the **Coveo Cloud Platform**, indexing [pokemondb.net](https://pokemondb.net) and surfacing it through a custom UI.

**Live:** 🔗 RGA quality dashboard — [pokemon-rga-dashboard.vercel.app](https://pokemon-rga-dashboard.vercel.app)
**For the panel:** the [RGA Skill Evaluator diagnostic methodology](docs/rga-eval-methodology.md) is the panel-shareable walk-through of how we used the dashboard to identify a prompt-tuning intervention.

## Status

🚧 Work in progress. As of 2026-05-30:

- ✅ Phase 0 — repo, GitHub, dev env, API keys, org acceptance
- ✅ Phase 1 — Sitemap source created, **1,028 Pokemon indexed**, all fields populated
- ✅ Phase 2 — 5 indexed fields, source mappings, clean values verified
- ✅ Phase 3 — Console hosted search page validated (search, facets, generation badges)
- ⏳ Phase 4 — Python Push source (Source B) — per-form documents via PokéAPI
- ⏳ Phase 5 — Local Atomic UI (the FDE deliverable)
- ⏳ Phase 6 — Advanced features: RGA, Query Suggest, Pokemon Detail Page
- ⏳ Phase 7 — Vercel hosting
- ⏳ Phase 8 — Bonus: Passage Retrieval

## Architecture

```
   pokemondb.net + pokeapi.co
        │
        ├──► Source A: Coveo Sitemap source       ✅ live
        │      (1,028 indexed via versioned scraping config)
        │
        └──► Python ingestion ──► Source B: Push source   ⏳ Phase 4
                                  (per-form docs via PokéAPI)
                                  │
                                  ▼
                       Coveo Cloud Org (benichou)
                       index + RGA + Query Suggest
                                  │
                                  ▼
                       Hosted Search App (Vercel)       ⏳ Phase 5+7
                       Atomic main + Headless+React Detail Page
```

## Getting started (new contributor onboarding)

The repo is designed so a fresh contributor can replicate the org setup with one bootstrap command, given a Coveo org and three API keys. The keys are the only manual step (Coveo shows the secret once at creation by design).

### 1. Prerequisites

- Node 20+, Python 3.12+, `git`, `gh` (GitHub CLI), `curl`
- A Coveo Cloud organization with these features licensed:
  - Passage Retrieval API
  - Relevance Generative Answering (CRGA)
  - Automatic Relevance Tuning
- Email Coveo (contact in the original challenge invite) requesting the above be enabled on your OrgID if they're not already

### 2. Clone and set up `.env`

```bash
git clone https://github.com/<your-username>/coveo-pokemon-challenge.git
cd coveo-pokemon-challenge
cp .env.example .env
```

### 3. Install pre-commit hooks (recommended)

This repo uses **[ruff](https://docs.astral.sh/ruff/)** (a fast Rust-based Python linter + formatter that replaces flake8 + isort + Black + pyupgrade) via the **[pre-commit](https://pre-commit.com/)** framework. Once installed, every `git commit` automatically lints + formats staged Python files. Catches style and logic issues before they land in git history, and keeps every contributor's code in the same shape.

**One-time install per machine:**

```bash
brew install pre-commit            # macOS, preferred
# or: uv tool install pre-commit
# or: pipx install pre-commit
```

**One-time install per clone** (registers the git hook in `.git/hooks/`):

```bash
pre-commit install
```

After that, `git commit` runs ruff on every staged `.py` file automatically. If ruff auto-fixes anything (Black-style reformatting, import order, removed unused imports, etc.), the commit aborts so you can review the diff, `git add` the changes, and re-commit.

To run the hooks manually any time — for example, before opening a PR or sanity-checking a refactor:

```bash
pre-commit run                     # only files staged for commit
pre-commit run --all-files         # every Python file in the repo
```

Config files (both at the repo root, both committed, both diffable):

- **`.pre-commit-config.yaml`** — which hooks run on commit (ruff lint, ruff format, plus file-hygiene checks for trailing whitespace, EOF newlines, large files, merge-conflict markers, JSON/YAML validation).
- **`ruff.toml`** — line length (80), enabled rule families (PEP 8 style, pyflakes, isort, bugbear, pyupgrade, simplify, naming), and format style. **The same file VS Code reads for format-on-save**, so the editor and pre-commit + CI all enforce the same rules.

If you use VS Code, the workspace also ships `.vscode/settings.json` that wires ruff as the format-on-save formatter for Python — so your code reaches the same canonical form whether you save in the editor or commit through git.

### 4. Create the three API keys

Follow **[docs/api-keys.md](docs/api-keys.md)** to mint the three keys in the Coveo Admin Console:

- `pokemon-push-source` (Push API template)
- `pokemon-source-admin` (Custom template — Sources + Fields Edit)
- `pokemon-search` (Anonymous search template — public-safe)

Paste each into `.env` next to the corresponding variable name. The doc walks through the exact privileges and reasoning for each.

### 5. Bootstrap the org

```bash
scripts/bootstrap.sh
```

This single command (idempotent):

1. Validates the org has the required licensed features
2. Validates the three API keys have correct privileges (least-privilege check)
3. Creates the 5 Coveo fields if missing
4. Creates the Sitemap source if missing
5. Applies the versioned web scraping configuration
6. Adds the 5 source mappings
7. Narrows the URL filter to a single Pokemon (safe starting scope)
8. Triggers an initial rebuild

Then run the script to widen the crawl to all ~1,025 Pokemon:

```bash
scripts/source/widen.sh all       # update URL filter to include all Pokemon
scripts/source/rebuild.sh         # ~17 minute crawl at 1 req/sec
```

### 6. Verify (optional, recommended)

```bash
cd tests && uv run pytest         # 21 tests against the live org + sitemap
```

## Opening Claude Code with only this repo's tooling

This repo ships a Claude Code skill (`/rga-eval`) and a project-scoped `.claude/` directory. To open Claude Code with **only this repo's skills + MCP** — ignoring any global skills or MCP servers configured in `~/.claude/` (e.g. corporate / org-level tooling that shouldn't load on personal projects) — invoke Claude Code from the repo root with:

```bash
claude --setting-sources project --strict-mcp-config --mcp-config .claude/mcp.json
```

What each flag does:

| Flag | Effect |
|---|---|
| `--setting-sources project` | Loads ONLY `./.claude/settings.json`; ignores user-level `~/.claude/settings.json` and any merged enterprise settings. |
| `--strict-mcp-config` | Disables user-level + enterprise MCP server discovery. |
| `--mcp-config .claude/mcp.json` | Loads MCP servers from the repo's `.claude/mcp.json` (which is empty by design — Phase 8.5 will add the Coveo MCP server here). |

**What this isolates:** project-scoped settings + project-scoped MCP servers.

**Caveat:** This does NOT block skills in `~/.claude/skills/` from auto-loading alongside the repo's `.claude/skills/`. If full skill isolation matters (e.g. you don't want Carta skills loading), add `--bare` to the command — at the cost of needing to manually register the `/rga-eval` skill in `.claude/settings.json` (vs. auto-discovery from `.claude/skills/rga-eval/`).

## Claude Code skill: `/rga-eval`

The repo includes a Claude Code skill that operates the RGA Skill Evaluator (Phase 6D) from the terminal. Invoke from inside a Claude Code session:

```
/rga-eval              # latest run summary + category breakdown (no API calls)
/rga-eval full         # full 100-question evaluation (~10 min, ~$0.60 Sonnet)
/rga-eval smoke        # 5-question smoke test (~30s)
/rga-eval failures     # latest run: every failing question + judge reasoning
/rga-eval hallu        # latest run: every hallucinated answer
/rga-eval compare 2026-05-31 2026-06-01   # diff two runs
```

The skill is defined in `.claude/skills/rga-eval/SKILL.md` and uses the pretty-printer in `rga-eval/src/show.py`. It's also auto-triggered when you ask things like *"what's the latest RGA accuracy?"* or *"where is RGA hallucinating?"* — no need to type the slash command explicitly.

What the eval does is documented in detail at the top of `~/.claude/plans/so-we-are-supposed-purrfect-bachman.md` (Phase 6D). Headline: it runs 100 hand-crafted Pokemon questions against Coveo's RGA endpoint, computes accuracy + precision + hard-recall using a Claude Sonnet 4.6 LLM-as-judge (with Pydantic-enforced structured output), and writes daily snapshots to `eval-runs/YYYY-MM-DD-<mode>.json`. Only `*-full.json` files feed the dashboard; smoke / layer-scan runs are diagnostic.

## Claude Code skill: `/rga-closed-loop`

Companion to `/rga-eval`. Drives the **closed-loop prompt-tuning** system (Phase 6F): runs an LLM-assisted analyzer against the latest eval, proposes refinements to the RGA Custom Prompt, and applies approved changes to Coveo via REST API. Invoke from inside Claude Code:

```
/rga-closed-loop              # current state: YAML version + live-Coveo diff
/rga-closed-loop analyze      # run analyzer → show proposal → ASK to apply → if approved, archive + update YAML + PUT to Coveo
/rga-closed-loop apply        # apply current YAML to Coveo (no analyzer — use after manual YAML edits)
/rga-closed-loop force        # apply with --force (write-path drills, rollback re-sync)
/rga-closed-loop verify       # read-only check that live Coveo matches the YAML byte-for-byte
/rga-closed-loop rollback <date>  # restore prompts/history/<date>-*.yaml, then ask to apply
```

`analyze` is the closed-loop one-shot: analyzer reads latest eval-run + identifies regressed categories + samples failing answers + calls Sonnet 4.6 with tool-use forcing → returns a structured `PromptProposal` (new prompt + rationale + expected lift + sample before/after answers + confidence). The skill shows you the proposal, asks for explicit approval, and only on yes archives the current YAML to `prompts/history/`, updates `prompts/pokemon-rga.yaml`, runs `apply.py --apply` to PUT to Coveo, and verifies via re-fetch.

**The skill is the interactive driver. A future autonomous cron driver (Phase 6F.5) would replace the interactive gate with rule-based guardrails (confidence threshold, rate limit, auto-rollback on next-day regression). Both drivers share the same `rga-closed-loop/src/analyzer.py` + `apply.py` core.**

## RGA quality dashboard

**🔗 Live dashboard: [pokemon-rga-dashboard.vercel.app](https://pokemon-rga-dashboard.vercel.app)**

The Vercel-hosted dashboard at `rga-dashboard/` reads every `eval-runs/*-full.json` at **build time** (Vite's `import.meta.glob`, no runtime fetch) and renders:

- A KPI snapshot of the latest run with Δ vs the previous run
- A time-series of accuracy / precision / hard-recall / citation-precision (overall + per layer)
- A per-category breakdown sorted worst-first — surfaces where RGA is degrading
- A per-question drill-down with judge reasoning + false claims + raw RGA answer

```bash
cd rga-dashboard
npm install
npm run dev      # local: http://localhost:5173
npm run build    # → dist/ for Vercel
```

To deploy: import the repo in Vercel, set **Root Directory** to `rga-dashboard`, framework auto-detects as Vite. Every push to the watched branch redeploys with whatever `eval-runs/*-full.json` files are in the commit — so the dashboard always reflects the latest committed history.

The full Vercel + GitHub-Actions-secrets runbook lives in **[`docs/deploy.md`](docs/deploy.md)**. It covers: the 5 secrets to add (and where they go — *not* in Vercel), the Vercel project config, the manual workflow-dispatch verification, and the cost ceiling (~$18/mo).

### Daily eval automation

A scheduled GitHub Actions workflow at `.github/workflows/rga-eval-daily.yml` runs the evaluator every day at **06:00 UTC**, commits the resulting `eval-runs/YYYY-MM-DD-full.json` back to the watched branch, and that push triggers a Vercel rebuild — so the dashboard is self-perpetuating without anyone touching it.

The workflow also exposes a **manual trigger** from the Actions UI (mode dropdown: smoke / layer1 / layer2 / layer3 / full + an optional question limit) for ad-hoc runs, panel-demo dry-runs, and prompt-tuning validation.

## Repository layout

```
coveo-pokemon-challenge/
├── README.md                    ← you are here
├── .env.example                 ← copy to .env and fill with API keys
├── .gitignore
├── .pre-commit-config.yaml      ← hooks run by git commit (ruff + file hygiene)
├── ruff.toml                    ← linter + formatter config (line 80, PEP 8, isort, …)
├── .vscode/                     ← shared workspace settings (settings, launch, extensions)
├── .github/
│   └── workflows/
│       └── rga-eval-daily.yml   ← daily 06:00 UTC RGA eval cron + manual trigger
├── .claude/                     ← project-scoped Claude Code config
│   ├── settings.json            ← marker for `--setting-sources project`
│   ├── mcp.json                 ← project-scoped MCP server set (currently empty)
│   └── skills/
│       ├── rga-eval/SKILL.md    ← /rga-eval slash command
│       └── rga-closed-loop/SKILL.md  ← /rga-closed-loop slash command (Phase 6F)
│
├── docs/
│   ├── api-keys.md              ← how to create the 3 API keys + their privileges
│   ├── ml-models.md             ← RGA + Semantic Encoder: what, why, how
│   ├── deploy.md                ← GitHub Actions secrets + Vercel project setup
│   ├── rga-prompt.md            ← version-controlled RGA Custom Prompt text + rationale
│   └── rga-eval-methodology.md  ← six-stage diagnostic loop (panel-shareable)
│
├── config/                      ← versioned Coveo configuration
│   ├── README.md                  (intro + glossary)
│   ├── fields.json              ← index field schema
│   └── source/                    (source-specific config)
│       ├── definition.json
│       ├── scraping.json
│       └── url_filter.json      ← single source of truth (read by scripts AND tests)
│
├── scripts/                     ← idempotent ops scripts (Coveo REST API)
│   ├── README.md                  (intro + glossary)
│   ├── bootstrap.sh             ← one-command full provisioning
│   ├── validate/                  (read-only preflight checks)
│   │   ├── org_features.sh
│   │   └── api_keys.sh
│   ├── setup/                     (idempotent resource creation)
│   │   ├── fields.sh
│   │   ├── source.sh
│   │   ├── mappings.sh
│   │   └── scraping.sh
│   ├── source/                    (source lifecycle ops)
│   │   ├── widen.sh
│   │   └── rebuild.sh
│   ├── ml/                        (machine learning wiring)
│   │   └── associate_models.sh  ← wires RGA + SE into the query pipeline
│   └── audit/                     (post-processing data quality)
│       ├── audit_index.py       ← PokéAPI + structural leak detector
│       └── purge_index.sh       ← filter-update + rebuild for confirmed leaks
│
├── rga-eval/                    ← RGA Skill Evaluator (Phase 6D — daily quality monitoring)
│   ├── README.md
│   ├── pyproject.toml + uv.lock
│   ├── golden/questions.json    ← 100 hand-crafted Q's (50 L1 / 35 L2 / 15 L3)
│   ├── src/
│   │   ├── schemas.py           ← Pydantic models (GoldenQuestion / JudgeVerdict / EvalRun)
│   │   ├── coveo_rga.py         ← /answer/v1/configs/{id}/generate SSE client
│   │   ├── llm_judge.py         ← Sonnet 4.6 with tool-use forcing → JudgeVerdict
│   │   ├── metrics.py           ← accuracy / precision / hard-recall computation
│   │   ├── publish.py           ← write eval-runs/YYYY-MM-DD.json
│   │   ├── show.py              ← pretty-printer for terminal display
│   │   └── main.py              ← orchestrator (--limit / --layer / --dry-run)
│   └── tests/test_schemas.py    ← 6 dataset-shape tests
│
├── eval-runs/                   ← one JSON per day; commit history = time-series database
│   └── YYYY-MM-DD-<mode>.json
│
├── rga-dashboard/               ← Vercel-hosted dashboard (Phase 6D.6 — Vite + React + recharts)
│   ├── src/
│   │   ├── App.tsx              ← page shell (header / sections / footer)
│   │   ├── loadRuns.ts          ← bundles eval-runs/*-full.json at build time (import.meta.glob)
│   │   ├── schemas.ts           ← TS mirror of rga-eval/src/schemas.py
│   │   └── components/
│   │       ├── SummaryCard.tsx       ← latest run KPIs + Δ vs previous
│   │       ├── TimeSeries.tsx        ← per-metric line charts (overall + per layer)
│   │       ├── CategoryBreakdown.tsx ← worst-category-first accuracy table
│   │       └── FailuresTable.tsx     ← per-question drill-down with judge reasoning
│   └── vercel.json
│
├── rga-closed-loop/             ← Phase 6F: closed-loop RGA prompt-tuning
│   ├── README.md                ← panel-shareable overview of the loop
│   ├── pyproject.toml + uv.lock
│   ├── prompts/
│   │   ├── pokemon-rga.yaml     ← CURRENT live prompt + structured metadata (YAML, single source of truth)
│   │   └── history/             ← previous prompt versions, dated YAMLs
│   │       └── 2026-05-31-default.yaml  ← the Coveo default we replaced
│   ├── src/
│   │   ├── schemas.py           ← Pydantic: PromptVersion + PromptProposal
│   │   ├── apply.py             ← Layer 1: PUT prompt to Coveo (dry-run default, --apply to write)
│   │   ├── analyzer.py          ← Layer 2: LLM-proposed prompt deltas (Phase 6F.3, coming)
│   │   └── pr_opener.py         ← Layer 2: open PR with proposal (Phase 6F.4, coming)
│   └── tests/test_apply.py      ← 9 unit tests, respx-mocked, no live Coveo calls
│
└── tests/                       ← pytest + httpx integration tests (21 tests, ~3s)
    ├── README.md                  (intro + glossary)
    ├── pyproject.toml + uv.lock
    ├── conftest.py
    ├── test_url_set_parity.py   ← sitemap-filtered set == indexed set
    ├── test_index_audit.py      ← every URI is a real Pokemon (PokéAPI + HTML check)
    ├── test_field_extraction.py ← 8 spot-check Pokemon, all 5 fields
    ├── test_facet_counts.py
    └── test_search_queries.py
```

Also in the repo (not shown above to keep the tree readable):
- `push-pokemon/` — Python ingestion pipeline (Phase 4) — pushes PokéAPI form variants to Source B
- `atomic-search/` — local Atomic UI (Phase 5) — Vite-hosted Pokemon search experience

Still coming:
- `detail-page/` — Headless + React Pokemon Detail Page (Phase 6C)
- Grafana Cloud query observability instrumentation (Phase 6E)

## Design decisions worth knowing

- **Sitemap source over Web Crawler.** pokemondb.net publishes a sitemap; Coveo's "Leading Practices" explicitly prefer Sitemap source when available — faster, more reliable, same scraping rules apply.
- **Three API keys, not one.** Coveo enforces "privileges are immutable post-creation," so we follow least-privilege: push key cannot edit sources, search key cannot edit anything, admin key cannot query.
- **Config as code.** Source URL filters, scraping rules, mappings, fields — everything is versioned JSON + a bash script that applies it via the REST API. The repo is ~95% reproducible via `scripts/bootstrap.sh`; the only manual step is API key minting (Coveo's secret-once design).
- **Dual-source ingestion.** Source A (Sitemap) captures Pokemon at the page level; Source B (Push, Phase 4) will capture them at the form level (Mega, Hisuian, Galarian, …) via PokéAPI — preserving form→type associations.

## License

MIT
