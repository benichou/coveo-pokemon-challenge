# Scripts

One-off and recurring operational scripts for managing the Coveo `benichou` org. Organized into subfolders by lifecycle stage.

## In plain English

Think of this folder as the **control panel for the Coveo organization**, written as text files instead of being a website you click around.

Coveo (the search engine company) provides an "Admin Console" — a web UI where you'd normally go to set up search sources, define fields, configure how content gets indexed, etc. **All the scripts here do the same setup work via Coveo's REST API instead.** Why bother?

- **Reproducibility.** Anyone with the repo + an API key can recreate the entire Coveo setup with one command (`bootstrap.sh`). No "open the Admin Console and click here, then here…" instructions.
- **Version control.** Every change to the org's configuration shows up as a git diff with a commit message — you can see who changed what and roll it back.
- **No drift.** If someone tweaks the org in the UI, running the scripts brings it back to the known-good state described in the config files.
- **Speed.** A web UI is one click per action. A script can do ten things in 30 seconds.

If you wanted to take this whole project and redeploy it on a fresh Coveo organization, you'd: (1) mint three API keys via Coveo's UI (Coveo only lets you see API key secrets once — that part can't be automated), (2) paste them into `.env`, (3) run `scripts/bootstrap.sh`. Five minutes later, the new org is configured identically.

The bash scripts here are mostly thin wrappers around Coveo's REST API. Each one does ONE thing: validate a feature, create a field, apply a configuration, trigger a rebuild. They're all **idempotent** (safe to run more than once — they detect what already exists and skip it). They source secrets from `../.env` (which is gitignored, never committed).

## Folder layout

```
scripts/
├── bootstrap.sh                  ← top-level orchestrator (calls everything below)
├── validate/                       (read-only preflight checks)
│   ├── org_features.sh             — confirms required Coveo features are licensed
│   └── api_keys.sh                 — confirms each API key has the right privileges
├── setup/                          (idempotent resource creation)
│   ├── fields.sh                   — creates the 5 indexed fields from config/fields.json
│   ├── source.sh                   — creates the Sitemap source from config/source/definition.json
│   ├── mappings.sh                 — adds the 5 metadata→field mappings
│   └── scraping.sh                 — applies config/source/scraping.json to the source
├── source/                         (source lifecycle ops)
│   ├── widen.sh                    — switches the URL filter between narrow / spot-check / all
│   └── rebuild.sh                  — triggers a rebuild and polls until IDLE
├── ml/                             (machine learning wiring)
│   └── associate_models.sh         — attaches pokemon-rga + pokemon-se to the default pipeline
└── audit/                          (post-processing data quality)
    ├── audit_index.py              — PokéAPI + structural leak detector (PEP 723)
    └── purge_index.sh              — filter-update + rebuild for confirmed leaks
```

The folder name carries the category, so script filenames inside drop the redundant prefix (`scripts/validate/api_keys.sh` instead of `scripts/validate_api_keys.sh`).

## Why these exist

Some Coveo configuration (notably **source mappings**) wasn't exposed in the new Admin Console UI as of May 2026. The REST API still supports it, so we manage that configuration here. Keeping it in scripts (rather than ad-hoc curl in the terminal):

- Makes the work reproducible
- Documents the API surface we depend on
- Gives the panel something concrete to read during the Topic 1 deep dive

## Prerequisites

All scripts source `../.env` from the repo root. Required variables:

| Variable | Used by | Privilege needed |
|---|---|---|
| `COVEO_ORG_ID` | All | — |
| `COVEO_SITEMAP_SOURCE_ID` | `setup/mappings.sh`, `source/widen.sh`, `source/rebuild.sh` | — |
| `COVEO_ADMIN_API_KEY` | All setup / source / ml / audit scripts | See `docs/api-keys.md` (Sources Edit, Fields Edit, Query pipelines Edit, ML Models View, Organization View) |
| `COVEO_PUSH_API_KEY` | (future push pipeline — Phase 4) | Push items to sources |
| `COVEO_SEARCH_API_KEY` | `audit/audit_index.py` | Execute queries (Anonymous Search) |

Never commit `.env` (it's gitignored).

## Pre-commit hooks (linting + formatting)

Before contributing code, install the pre-commit hook so every commit is auto-linted and formatted by **ruff** (the Rust-based, ~100x faster replacement for flake8 + isort + Black + pyupgrade):

```bash
brew install pre-commit      # or: uv tool install pre-commit
pre-commit install           # installs the git hook in this repo
```

After that, `git commit` automatically runs ruff on every staged `.py` file. If ruff auto-fixes anything, the commit is aborted so you can review the diff, re-stage, and re-commit. Rules + line length live in `ruff.toml` at the repo root — the same file VS Code reads for "format on save".

To run the hooks manually:

```bash
pre-commit run                # only files staged for commit
pre-commit run --all-files    # every Python file in the repo
```

The hook list is in `.pre-commit-config.yaml` at the repo root — ruff (lint), ruff-format, plus a few file-hygiene checks (trailing whitespace, large files, merge-conflict markers).

## One-command bootstrap

If you're setting up a fresh Coveo org (or rebuilding state from scratch):

```bash
scripts/bootstrap.sh
```

Runs validators, creates fields, creates the source, applies the scraping config and mappings, sets URL filter to the safe `narrow` scope, and triggers an initial rebuild. Fully idempotent — safe to re-run.

Use `scripts/bootstrap.sh --skip-rebuild` to do everything except the final rebuild (e.g., if you want to widen the scope before crawling).

---

## `bootstrap.sh`

End-to-end orchestrator. Runs (in order): `validate/org_features.sh`, `validate/api_keys.sh`, `setup/fields.sh`, `setup/source.sh`, `setup/scraping.sh`, `setup/mappings.sh`, `source/widen.sh narrow` (with safety guard, see below), `source/rebuild.sh`. Stops on first failure. Idempotent — re-running is a no-op for already-present resources.

**Flags:**
- `--skip-rebuild` — run everything except the final source rebuild.
- `--reset-filter` — force step 7 to apply the `narrow` filter even if the source is already at `spot-check` or `all`. Without this flag, step 7 detects the current filter mode and **skips the downgrade** to preserve an existing populated index.

**The safety guard (added 2026-05-30):** earlier versions of bootstrap unconditionally applied `widen.sh narrow` at step 7. Re-running on a populated org with the filter at `all` would silently collapse the index back to one Pokemon (Coveo deletes items that no longer match the filter on config-change refreshes). The guard now reads the source's current `urlFilters[0].filter` value, looks it up in `config/source/url_filter.json`, and:

- If current mode is `narrow` (or no source exists yet) → applies `narrow` normally.
- If current mode is `spot-check` or `all` → **skips** with a clear message, unless `--reset-filter` is passed.

## `validate/` — read-only preflight checks

### `validate/org_features.sh`

Confirms the Coveo org has the licensed features this project depends on (Passage Retrieval, Relevance Generative Answering / CRGA, Automatic Relevance Tuning). Run it any time you want to re-verify org state — useful as a pre-demo check or after any org-level change.

```bash
scripts/validate/org_features.sh
```

Exit code: 0 if all required features are enabled, 1 otherwise.

### `validate/api_keys.sh`

Confirms all three project API keys (`COVEO_PUSH_API_KEY`, `COVEO_ADMIN_API_KEY`, `COVEO_SEARCH_API_KEY`) authenticate and have exactly the right privileges:

- Push key: Sources View (✓), Sources Edit (✗ — should NOT have it)
- Admin key: Sources Edit (✓), Fields Edit (✓), Pipelines Edit (✓), ML Models View (✓)
- Search key: Execute queries (✓), Sources Edit (✗ — should NOT have it)

```bash
scripts/validate/api_keys.sh
```

Exit code: 0 if all keys validate correctly, 1 otherwise.

## `setup/` — idempotent resource creation

### `setup/fields.sh`

Reads `config/fields.json` and creates any missing Coveo fields. Idempotent — skips fields whose names already exist on the org.

```bash
scripts/setup/fields.sh
```

### `setup/source.sh`

Reads `config/source/definition.json` and creates the Sitemap source if it doesn't already exist. On success, writes `COVEO_SITEMAP_SOURCE_ID` to `.env` (if not already there).

```bash
scripts/setup/source.sh
```

Idempotent — skips if a source with the same name already exists.

### `setup/mappings.sh`

Adds the 5 Pokemon Challenge field mappings (`pokemon_name`, `pokemon_type`, `image_url`, `dex_number`, `generation`) to the `pokemondb-sitemap` source.

**Idempotent.** Lists existing common mappings first and skips any field that's already mapped, so re-running is safe.

```bash
scripts/setup/mappings.sh
```

**First run output:**

```
Fetching existing common mappings...
  52 existing common mappings on this source.

  [create]  pokemon_name ... HTTP 201 ✓
  [create]  pokemon_type ... HTTP 201 ✓
  [create]  image_url ... HTTP 201 ✓
  [create]  dex_number ... HTTP 201 ✓
  [create]  generation ... HTTP 201 ✓

Done: 5 created, 0 skipped.
Trigger a source rebuild for changes to apply to indexed items.
```

**Re-run output:** `Done: 0 created, 5 skipped.`

### `setup/scraping.sh`

Applies the web scraping configuration from `config/source/scraping.json` to the `pokemondb-sitemap` source.

The scraping config is what tells Coveo how to extract metadata (name, type, image, dex number, generation) from each Pokemon page using CSS/XPath selectors. Keeping it as a versioned JSON file means selector changes are diff-able in git and reproducible across orgs.

```bash
# edit config/source/scraping.json
scripts/setup/scraping.sh
scripts/source/rebuild.sh
```

The config file is a JSON array of configurations — typically the Coveo default (which excludes headers/footers/etc.) and our custom "Pokemon page metadata extraction" configuration.

## `source/` — source lifecycle operations

### `source/widen.sh`

Updates the `pokemondb-sitemap` source's URL inclusion filter to one of three preset scopes, used to stage the crawl from a single Pokemon up to all ~1,025.

```bash
scripts/source/widen.sh narrow       # only bulbasaur (fast iteration)
scripts/source/widen.sh spot-check   # 8 diverse Pokemon (edge-case sweep)
scripts/source/widen.sh all          # all ~1,025 + 9 exclusion rules
```

Run a rebuild after to apply the new filter to indexed items:

```bash
scripts/source/rebuild.sh
```

The `spot-check` mode is recommended before `all`: it indexes 8 deliberately diverse Pokemon (Bulbasaur, Pikachu, Charizard, Mewtwo, Ho-Oh, Mr-Mime, Decidueye, Miraidon) covering multiple generations, single/dual types, and hyphenated names — so any scraping-config bugs surface in 30 seconds instead of after a 17-minute full crawl.

### `source/rebuild.sh`

Triggers a rebuild of `pokemondb-sitemap` via the REST API and polls the source status every 5 seconds until it returns to `IDLE`. Use this after any source-config change (mappings, URL filters, web scraping config) to apply the change to indexed items.

```bash
scripts/source/rebuild.sh
```

Single-Pokemon rebuilds complete in under 30 seconds. Full-scope (~1,025 Pokemon) rebuilds take ~17 minutes at the throttled 1 req/sec crawl rate; the script polls for up to ~25 minutes.

## `ml/` — machine learning wiring

### `ml/associate_models.sh`

Associates the `pokemon-rga` (Relevance Generative Answering) and `pokemon-se` (Semantic Encoder) ML models with the default query pipeline. Required step after creating the models in the Coveo Admin Console — without the association, the models exist but don't affect search.

```bash
scripts/ml/associate_models.sh             # apply (idempotent)
scripts/ml/associate_models.sh --dry-run   # show what would change
```

**Why this is scripted** when model *creation* is Console-only: Coveo separates models from pipelines. Model creation for RGA isn't exposed in the public REST API, but **the pipeline ↔ model association IS** (`/rest/search/v1/admin/pipelines/{id}/ml/model/associations`). So we automate the part Coveo lets us automate, which is also the part that benefits most from reproducibility (config drift on which models live in which pipelines is a real risk).

**Idempotent:** the script lists existing associations and skips models already wired in, so re-running is safe.

**Requires extra admin privileges:** `Search > Query pipelines > Edit` and `Machine Learning > Models > View` — see `docs/api-keys.md`.

Full context (what models we deployed, why each one, the Console steps, the API endpoints) is in `docs/ml-models.md`.

---

## `audit/` — post-processing data quality

### Why we built these scripts

The URL filter in `config/source/url_filter.json` is the *intent* — a regex plus a list of substring exclusions that say "index these, skip those." But intent is not truth. The filter passes any URL whose shape happens to match, and pokemondb.net occasionally publishes new aggregate / list pages whose URL shape we didn't anticipate. When that happens, non-Pokemon pages quietly slip into the index.

That's exactly what happened on **2026-05-30** with `https://pokemondb.net/pokedex/shiny` — a list of shiny sprite previews. It matches our include regex (`^https://pokemondb\.net/pokedex/[a-z0-9-]+$`), it wasn't in the exclusion list, so the crawler indexed it as if it were a Pokemon. The parity test `test_non_pokemon_urls_are_excluded` caught it, but only because we'd happened to hardcode `/pokedex/shiny` into the suspect list. We needed something that would catch the *next* leak we hadn't seen yet.

So we built two scripts that work as a pair: one detects, the other corrects.

- **`audit/audit_index.py`** finds leaks by cross-referencing the indexed URIs against PokéAPI (a curated external source of Pokemon truth) and then confirming each candidate by fetching the page and checking for a structural signature only real Pokedex entries have. Read-only. Suitable for CI.
- **`audit/purge_index.sh`** applies the durable fix: it appends the offending path segments to `config/source/url_filter.json` and triggers a widen + rebuild, so the source filter excludes them going forward and the orphaned items drop out of the index. The fix lives in version control as a diff, not as a magic API call.

### Why filter-update, not surgical DELETE

Coveo's Push API exposes a `DELETE /push/v1/.../sources/{id}/documents` endpoint that can surgically delete one item by ID. We deliberately did **not** use it here. Two reasons:

1. **It doesn't apply to Sitemap sources.** Push DELETE works for Push-type sources (Source B in Phase 4). For Sitemap and Crawler sources, individual items are derived from the sitemap on every refresh — there's no addressable handle to delete that survives the next crawl. We'd delete the orphan, the next refresh would re-fetch it, and we'd be exactly where we started.
2. **The filter would still be wrong.** Even if surgical delete *worked* on a Sitemap source, the source's URL filter would still admit the leaked URL on the next rebuild. The cause is the filter; deleting the symptom doesn't fix the cause.

Updating `config/source/url_filter.json` fixes the cause, leaves a git diff that documents what we excluded and why, and keeps the parity test honest (the tests read the same file the source reads — they can't diverge).

### `audit/audit_index.py`

Read-only audit of the Coveo index against external truth. Run it after any crawl widening, before a panel demo, or on a CI schedule.

```bash
scripts/audit/audit_index.py             # writes audit_report.json at the repo root
scripts/audit/audit_index.py --verbose   # show each candidate's verification result
scripts/audit/audit_index.py --report /tmp/leaks.json
```

Three passes:

1. **URL shape regex** — every indexed URI must match `^https://pokemondb\.net/pokedex/[a-z0-9-]+$`.
2. **PokéAPI cross-reference** — diff the indexed slugs against PokéAPI's canonical Pokemon list. PokéAPI is advisory: pre-release Gen 10 Pokemon show up on pokemondb before PokéAPI ingests them, and PokéAPI splits forms (`deoxys-normal`, `deoxys-attack`) where pokemondb uses one canonical slug (`deoxys`). So "not in PokéAPI" means "look closer," not "delete."
3. **Structural verification** — for each candidate, fetch the page and look for `<th>National №</th>` in the vitals table. Every real Pokedex entry has it; no aggregate or list page does. Pass C is authoritative.

Exits non-zero if any leak is found, so this is safe to wire into CI as a drift detector.

Self-contained Python: uses `uv run --script` with inline dependency metadata (PEP 723), so it runs anywhere `uv` is installed — no separate virtualenv needed.

### `audit/purge_index.sh`

Reads `audit_report.json` (or accepts `--uri` flags) and applies the filter-update + rebuild cycle.

```bash
scripts/audit/purge_index.sh             # use audit_report.json
scripts/audit/purge_index.sh --dry-run   # show diff, don't write
scripts/audit/purge_index.sh --uri https://pokemondb.net/pokedex/some-leak
```

What it does:

1. Reads the leak URIs from the audit report (or `--uri` args).
2. Computes the path segments to add to `modes.all.exclusions_contains` (e.g., `/pokedex/shiny`).
3. Shows the proposed diff, asks for explicit y/N confirmation.
4. On confirm: rewrites `config/source/url_filter.json`, runs `source/widen.sh all`, runs `source/rebuild.sh`.

Don't forget to commit the updated `config/source/url_filter.json` — the whole point is that the fix lives in version control.

---

## Glossary

Terms used in this README, the scripts, and the wider Coveo world.

| Term | What it means |
|---|---|
| **API key** | A secret token (like `xxbbbefdc0-...`) that authorizes requests to Coveo's REST API. Each key has a specific set of *privileges*. Coveo only shows the key value once at creation — we store it in `../.env`. |
| **Association** (ML) | The wiring that connects an ML model to a query pipeline. Without it, the model exists but doesn't affect search. See `ml/associate_models.sh` and `docs/ml-models.md`. |
| **Bash** | The Unix shell scripting language all the `.sh` files in this folder are written in. Runs natively on macOS and Linux. |
| **Bootstrap** | The act of setting up an empty system to a known working state. `bootstrap.sh` is our top-to-bottom "make this org match the desired state" script. |
| **Coveo Cloud** | Coveo's hosted SaaS platform — the company runs the search infrastructure, you point content at it and customize the search experience. |
| **CRGA** | Coveo Relevance Generative Answering. Coveo's name for the LLM-powered "AI answer" feature that summarizes search results into a written response with citations. Often called "RGA". |
| **CSS selector** | A pattern for picking HTML elements (e.g., `.vitals-table` picks every element with `class="vitals-table"`). Comes from the world of CSS stylesheets but used here to pull data out of crawled pages. |
| **Facet** | A filter shown in the search UI sidebar — usually checkboxes letting users narrow results by some field value (e.g., "Pokemon Type: Grass, Fire, Water…"). |
| **Field** | A named property of a search result, like a column in a database table. E.g., `pokemon_name`, `pokemon_type`. |
| **HTTP status code** | The number a web server returns to indicate what happened. 200 = OK, 201 = Created, 403 = Forbidden, 412 = body had a problem. Our scripts check these to know if calls worked. |
| **Idempotent** | A script you can run any number of times and the end state will be the same as running it once. Lets you re-run without breaking things. |
| **Index** | The internal database Coveo builds from crawled content. When you search, you're searching the index, not the original websites. |
| **JSON** | The data format used by both Coveo's API and our config files. Plain text with structured `{ "key": "value" }` shape. |
| **Mapping** | A rule telling Coveo "when you find metadata X on a page, store it in field Y." The bridge between what we extract and what's queryable. |
| **ML model** | A trained algorithm Coveo runs at query time to improve search. We use **RGA** (Relevance Generative Answering — generates AI answers) and **SE** (Semantic Encoder — semantic retrieval). Created in the Console, associated with a query pipeline via API. See `docs/ml-models.md`. |
| **Org / Organization** | A tenant in Coveo Cloud. Our org is `benichou` (Test environment). Each org has its own keys, sources, fields, etc. |
| **Pipeline** (Query pipeline) | The path a query takes inside Coveo: rules, filters, ML models. Every org has a default pipeline; we attach our RGA + SE models to it. |
| **Passage Retrieval API** | A Coveo feature that returns specific paragraphs (passages) within documents that best match a query, not just whole documents. Bonus tier of this challenge. |
| **PEP 723** | Python convention that lets a single-file script declare its own dependencies in a `# /// script` comment block. `uv run --script foo.py` reads it and runs the script in a one-off env. Used by `audit/audit_index.py`. |
| **PokéAPI** | A free, public REST API at `https://pokeapi.co` serving canonical Pokemon data (species, types, stats, sprites). Curated by maintainers, so it's the de-facto external source of truth for "what counts as a Pokemon." Used as an advisory ground truth in `audit/audit_index.py`. |
| **Rebuild** | Telling Coveo to re-crawl and re-process all items from scratch. Triggered via `source/rebuild.sh`. Slower than a "refresh" but applies all config changes. |
| **REST API** | A web-based interface where you send HTTP requests and get structured JSON back. Coveo's REST API is how all the scripts talk to the platform. |
| **RGA** | See CRGA. |
| **Scraping configuration** | Rules (CSS or XPath selectors) that tell Coveo how to extract structured data from each crawled HTML page. Stored on the source. Versioned for us in `../config/source/scraping.json`. |
| **Sitemap source** | A type of Coveo source that reads URLs from a sitemap.xml file and indexes each one. Recommended over the Web Crawler when a sitemap exists. |
| **Source** | A connector that ingests content into Coveo. Different types (Sitemap, Web, Push, Salesforce, etc.) for different content origins. We use a Sitemap source for pokemondb.net. |
| **URL filter** | An include/exclude rule on a source that decides which URLs from the sitemap actually get indexed. We use it to narrow down to Pokemon-detail pages only. |
| **XPath** | An alternative to CSS selectors, more powerful for positional logic (e.g., "the first table on the page"). Used by Coveo's web scraping for selectors that CSS can't express cleanly. |
