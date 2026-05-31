# Config

Versioned JSON descriptions of the Coveo org state — the *desired* shape that the bash scripts in `../scripts/` apply via the Coveo REST API.

Editing a file here is how you change source-level Coveo configuration. Re-run the corresponding script (or `scripts/bootstrap.sh`) to apply.

## In plain English

This folder is the **single source of truth for what the Coveo org should look like**, written as JSON files. Each file describes ONE category of configuration — the fields, the source connector, the scraping rules — and there's a corresponding script in `../scripts/` whose job is to read the file and make the org match.

The pattern is:

```
config/something.json          ← what we want (declarative, in git)
       ↓ read by
scripts/<category>/apply.sh    ← how we make Coveo match (imperative, REST calls)
       ↓ talks to
Coveo REST API                 ← updates the live org
```

This separation matters for two reasons:

1. **Reviewability.** When a Pokemon selector breaks at scale, the fix is a one-line diff in `source/scraping.json` — easy to PR, easy to roll back. Compare that with "open the Admin Console, find this section, click that button…"
2. **Reproducibility.** Anyone with the repo + an API key can recreate the org exactly. The JSON files capture the intent; the scripts execute it.

If you're new to the repo, the right mental model is: **don't edit Coveo in the web UI for things this folder covers.** Edit the JSON file, run the corresponding script, commit. Everything stays in sync.

## Folder layout

```
config/
├── fields.json                 ← index field schema (applies org-wide)
└── source/                       (everything specific to the pokemondb-sitemap source)
    ├── definition.json         ← static source config (name, URL, security level)
    ├── scraping.json           ← CSS/XPath selectors for metadata extraction
    └── url_filter.json         ← include regex + exclusions (read by scripts AND tests)
```

`fields.json` lives at the root because indexed fields are an **org-level** schema — they exist independently of any one source, and any source's documents can populate them.

Everything inside `source/` is scoped to a specific Coveo source (currently `pokemondb-sitemap`). When Phase 4 adds Source B (Push), we'll add `config/source_push/` or similar — keeping each source's config in its own subfolder.

## Files

### `fields.json`

The 5 custom indexed fields used by the Pokemon search experience.

| Field | Type | Purpose |
|---|---|---|
| `pokemon_name` | STRING | Search + display |
| `pokemon_type` | STRING (multi-value) | Facet |
| `image_url` | STRING | Result-tile image src |
| `dex_number` | LONG | Facet + sort (canonical order) |
| `generation` | STRING | Facet |

**Schema:** array of Coveo field-definition objects. Required keys per field: `name`, `type`. Useful extras: `facet`, `multiValueFacet`, `sort`, `stemming`, `includeInQuery`, `includeInResults`, `description`.

**Applied by:** `scripts/setup/fields.sh` (idempotent — skips fields whose names already exist on the org).

### `source/definition.json`

Static configuration for the `pokemondb-sitemap` Coveo Sitemap source. **Excludes** the three properties that other scripts manage:

| Property | Managed by |
|---|---|
| `urlFilters` | `scripts/source/widen.sh` (reads `source/url_filter.json`) |
| `scrapingConfiguration` | `scripts/setup/scraping.sh` (reads `source/scraping.json`) |
| `mappings` | `scripts/setup/mappings.sh` |

Keeping these out of `source/definition.json` keeps the responsibility for each piece of source state with exactly one script.

**Applied by:** `scripts/setup/source.sh` (idempotent — skips if a source with the same name exists; writes the new source ID to `../.env` as `COVEO_SITEMAP_SOURCE_ID`).

### `source/scraping.json`

The web scraping configuration — CSS/XPath selectors that tell Coveo how to extract per-page metadata (`pokemon_name`, `pokemon_type`, etc.) during crawling.

Two configurations in the array:

1. **`[Default Coveo web scraping configuration]`** — Coveo's standard exclusions (script, noscript, nav, header, footer, ads…). Pre-populated; usually leave it alone.
2. **`Pokemon page metadata extraction`** — our custom rules. The 5 selectors that produce the 5 indexed fields.

Selector pattern notes worth knowing if you touch this:

- **CSS** for simple selectors. Coveo extensions: `::text` (inner text), `::attr(name)` (attribute), `>>shadow` (Shadow DOM).
- **XPath** when positional logic matters. Use `(//thing)[1]/text()` to take the first match across the document; `//thing[1]/text()` does NOT do that (it applies `[1]` per-match).
- The default in the array applies to all URLs (`for.urls = [".*"]`); our config applies only to Pokemon detail pages via a regex.

**Applied by:** `scripts/setup/scraping.sh` (replaces the source's `scrapingConfiguration` field).

### `source/url_filter.json`

The URL inclusion regex and exclusion substrings that decide which pokemondb.net URLs get indexed. Three named modes (`narrow`, `spot-check`, `all`) for staged crawl rollouts.

This file is the **single source of truth** shared between the scripts and the test suite:

- `scripts/source/widen.sh <mode>` reads it and pushes the chosen mode's filter to the Coveo source.
- `tests/test_url_set_parity.py` reads it and recomputes the expected indexed set from the sitemap — failing if Coveo's actual indexed URIs don't match.

Because both sides read the same file, they can't drift. If a Pokemon-shaped URL pattern gets added or removed here, the test reflects it the next run.

**Applied by:** `scripts/source/widen.sh` (`narrow`, `spot-check`, or `all` — each writes the chosen filter to the source).

## Editing workflow

```bash
# 1. Edit the relevant JSON file (validate it's valid JSON locally first)
# 2. Apply via the corresponding script:
scripts/setup/fields.sh              # for fields.json
scripts/setup/source.sh              # for source/definition.json (rare — source rarely changes)
scripts/setup/scraping.sh            # for source/scraping.json
scripts/source/widen.sh <mode>       # for source/url_filter.json
# 3. Trigger a rebuild so existing items pick up the change:
scripts/source/rebuild.sh
```

## What's intentionally NOT in this directory

- **API keys, OrgID, secrets** — those live in `../.env` (gitignored). Never commit those.
- **License/feature flags** — those are managed by Coveo (e.g., Passage Retrieval, RGA enablement). Documented in the top-level README.
- **Field mappings between source metadata and Coveo fields** — managed dynamically by `scripts/setup/mappings.sh`; the 5 mappings are hardcoded in the script for now since they're tightly coupled to the field names.

---

## Glossary

Terms used in this README and the JSON files.

| Term | What it means |
|---|---|
| **Coveo Cloud** | The hosted SaaS search platform. Our org `benichou` lives there. |
| **Source** | A connector that ingests content into Coveo's index. Types include Sitemap (this project), Web Crawler, Push API, Salesforce, SharePoint, etc. |
| **Sitemap source** | A source that reads URLs from a sitemap.xml file and indexes each one. Recommended by Coveo when a sitemap is available. |
| **Index** | The internal database Coveo builds from crawled content. Queries hit the index, not the original sites. |
| **Field** | A typed, named property of an indexed item — like a column in a database. Fields can be marked searchable, displayable, sortable, facetable, etc. |
| **Multi-value field** | A field that can hold multiple values for a single item. E.g., `pokemon_type` is multi-value because dual-type Pokemon exist (Grass + Poison). |
| **Facet** | A filter shown in the search UI, usually a sidebar checklist letting users narrow results by a field's values. Comes in single-value and multi-value flavors. |
| **Mapping** | A rule that says "metadata key X on a crawled item populates field Y." Bridges what's extracted by scraping with what's queryable in the index. |
| **Scraping configuration** | The rules that tell Coveo how to pull structured data out of each crawled HTML page, using CSS or XPath selectors. Stored as a JSON array on the source. |
| **CSS selector** | A pattern for picking HTML elements by tag/class/attribute, like `.vitals-table a.type-icon`. Familiar from web development. |
| **XPath** | An alternative pattern language for picking elements, more powerful for positional and structural logic. Use `(//thing)[1]` for "first match across the document". |
| **URL filter** | Rules on a source that determine which URLs from the sitemap get indexed. Two kinds: inclusion (must match to be indexed) and exclusion (any match means skip). |
| **Rebuild** | Telling Coveo to re-crawl and re-process all matching items. Required after most config changes to apply them to existing indexed items. |
| **Refresh / Rescan** | Lighter operation than rebuild; only re-fetches items that have changed. |
| **REST API** | Coveo's HTTP/JSON interface. Every script in `../scripts/` is a thin wrapper around one or more REST calls. |
| **API key** | A secret token used to authenticate REST API requests. Coveo only shows the key value at creation; we store it in `../.env` (gitignored). |
| **Idempotent** | A property of a script that means "safe to run multiple times — running it twice has the same effect as running it once." All scripts in this project are idempotent. |
| **Org / Organization** | A Coveo Cloud tenant. Each org has its own indexes, sources, fields, API keys, and license. Our org is `benichou` (Test environment). |
| **Privilege** | A specific permission on an API key. E.g., "Sources: Edit" lets you modify source configurations. Coveo's least-privilege model means keys should have only what they need. |
| **JSON** | The plain-text data format used by both Coveo's API and these config files. Structured key/value pairs and arrays. |
| **Bash** | The Unix shell scripting language used by all the `.sh` files in `../scripts/`. Runs on macOS and Linux out of the box. |
| **Bootstrap** | Setting up an org from scratch. `../scripts/bootstrap.sh` runs everything end-to-end. |
| **Generation (Pokemon)** | The "release wave" a Pokemon was introduced in — Gen 1 (Red/Blue) through Gen 9 (Scarlet/Violet). Used here as a search facet. |
| **Mega / Hisuian / Galarian / Alolan / Paldean form** | Alternate forms of a Pokemon introduced in later games. Each has its own types and artwork on pokemondb.net. Source A captures the base form only; Source B (Phase 4) will preserve per-form data. |
