# Coveo Pokemon Challenge

Forward Deployed Engineer technical challenge for Coveo. A custom search experience built on the **Coveo Cloud Platform**, indexing [pokemondb.net](https://pokemondb.net) and surfacing it through a custom UI.

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

## Repository layout

```
coveo-pokemon-challenge/
├── README.md                    ← you are here
├── .env.example                 ← copy to .env and fill with API keys
├── .gitignore
├── .pre-commit-config.yaml      ← hooks run by git commit (ruff + file hygiene)
├── ruff.toml                    ← linter + formatter config (line 80, PEP 8, isort, …)
├── .vscode/                     ← shared workspace settings (settings, launch, extensions)
│
├── docs/
│   ├── api-keys.md              ← how to create the 3 API keys + their privileges
│   └── ml-models.md             ← RGA + Semantic Encoder: what, why, how
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

Coming soon (each in its own subfolder):
- `push-pokemon/` — Python ingestion pipeline (Phase 4)
- `atomic-search/` — local Atomic UI (Phase 5)
- `detail-page/` — Headless + React Pokemon Detail Page (Phase 6C)

## Design decisions worth knowing

- **Sitemap source over Web Crawler.** pokemondb.net publishes a sitemap; Coveo's "Leading Practices" explicitly prefer Sitemap source when available — faster, more reliable, same scraping rules apply.
- **Three API keys, not one.** Coveo enforces "privileges are immutable post-creation," so we follow least-privilege: push key cannot edit sources, search key cannot edit anything, admin key cannot query.
- **Config as code.** Source URL filters, scraping rules, mappings, fields — everything is versioned JSON + a bash script that applies it via the REST API. The repo is ~95% reproducible via `scripts/bootstrap.sh`; the only manual step is API key minting (Coveo's secret-once design).
- **Dual-source ingestion.** Source A (Sitemap) captures Pokemon at the page level; Source B (Push, Phase 4) will capture them at the form level (Mega, Hisuian, Galarian, …) via PokéAPI — preserving form→type associations.

## License

MIT
