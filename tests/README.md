# Tests

Hybrid integration tests that hit the live Coveo org via the REST API and assert the indexed data matches our intent.

## In plain English

These tests answer one question continuously: **"Is the Coveo org doing what our configuration says it should be doing?"**

They do this by **computing the expected state from two independent sources** and comparing them:

```
   pokemondb.net sitemap.xml             config/source/url_filter.json
              │                                   │
              └──────► apply filter ◄─────────────┘    (Python, in tests)
                            │
                            ▼
                     Set A — expected URIs
                            │
                            ▼
                       compared to ════════════════════════════════════ Coveo Search API
                            ▲                                                  │
                            │                                                  ▼
                     Set B — indexed URIs ◄────────────────────── enumerate all indexed items
```

If Set A != Set B, something is wrong: a Pokemon got dropped during the crawl, a regex change wasn't applied, the source got modified outside our scripts, or pokemondb.net grew without us re-crawling. The diagnostic output tells you exactly which URLs disagree.

## What's covered

| File | Asserts |
|---|---|
| `test_url_set_parity.py` | Indexed URIs == sitemap URLs that pass our filter. The most important test — universal "did the crawl match intent" check. |
| `test_index_audit.py` | Every indexed URI is independently verified as a real Pokemon page, via PokéAPI cross-reference + structural check on the page HTML. Catches the `/pokedex/shiny` class of leak where the filter itself is wrong. Mirrors `scripts/audit/audit_index.py`. |
| `test_field_extraction.py` | For 8 representative Pokemon, the indexed `pokemon_name`, `pokemon_type`, `image_url`, `dex_number`, `generation` match canonical values. Catches scraping-config regressions. |
| `test_facet_counts.py` | Per-generation facet counts are at least the canonical Bulbapedia numbers (151 for Gen 1, 100 for Gen 2, etc.). |
| `test_search_queries.py` | Searching "charizard" returns Charizard top; cross-facet filters work; empty query returns all items. |

## Prerequisites

- Python 3.12+
- `.env` at the repo root with all required variables (see `docs/api-keys.md`)
- The org bootstrapped (`scripts/bootstrap.sh`) and crawl widened (`scripts/source/widen.sh all && scripts/source/rebuild.sh`)

## Running

The fastest way (no manual virtualenv needed):

```bash
# Using uv (recommended)
cd tests
uv run pytest
```

`uv run` reads `pyproject.toml` + `uv.lock`, creates a `.venv` if missing, syncs deps from the lockfile, and runs the command. First run takes a few seconds to install; subsequent runs are near-instant.

Or with traditional venv:

```bash
cd tests
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pytest
```

Run a single test file:

```bash
uv run pytest test_url_set_parity.py
```

Run with extra verbosity (shows the parity diffs in full when they fail):

```bash
uv run pytest -vv
```

## Why `uv.lock` is committed

This directory ships both `pyproject.toml` (declared dependency ranges) **and** `uv.lock` (resolved transitive versions, hashes, and source URLs for every package the tests pull in). Together they make installs reproducible:

| File | Purpose | Should be committed? |
|---|---|---|
| `pyproject.toml` | Declares what we *depend on* (e.g., `pytest>=8.0`) | ✅ yes |
| `uv.lock` | Pins exactly what we *resolved* (e.g., `pytest==8.4.2` with SHA-256) | ✅ yes — same role as `package-lock.json` or `Cargo.lock` |
| `.venv/` | Local virtualenv with installed packages | ❌ no — gitignored |

Without the lock, two developers running `uv run pytest` a week apart could resolve subtly different versions and get different test results. With the lock, both get bit-for-bit identical environments.

Regenerate the lock when you change `pyproject.toml` deps:

```bash
uv lock                # update uv.lock to match pyproject.toml
uv lock --upgrade      # also bump within the declared version ranges
```

## Glossary

| Term | What it means |
|---|---|
| **Integration test** | A test that exercises the real system (Coveo's API, pokemondb.net's sitemap), not mocks. Catches real-world drift. |
| **Parity test** | A test that computes "what we expect" two independent ways and asserts they agree. Stronger than hardcoding expectations. |
| **Facet** | A grouping-and-counting view of indexed data. The Generation facet returns counts per generation; the test validates those counts. |
| **Search hub** | A Coveo label attached to every search request, used here to scope queries to our `pokemon-search` experience. |
| **Canonical** | The "official" Pokemon count per generation, sourced from Bulbapedia. Used as the lower bound in facet assertions. |
| **pytest** | The Python test runner. Each `test_*` function is a test; `parametrize` lets one function run with multiple input sets. |
| **fixture** | Shared test setup that pytest provides to tests as function parameters. See `conftest.py`. |
| **httpx** | Modern Python HTTP client. We use it for both async-capable code and (here) simple synchronous REST calls. |
