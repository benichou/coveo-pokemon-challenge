# Scripts

One-off and recurring operational scripts for managing the Coveo `benichou` org.

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
| `COVEO_SITEMAP_SOURCE_ID` | `add_mappings.sh` | — |
| `COVEO_ADMIN_API_KEY` | `add_mappings.sh` | Content > Sources > Edit |
| `COVEO_PUSH_API_KEY` | (future push pipeline) | Push items to sources |

Never commit `.env` (it's gitignored).

## Scripts

### `validate_org_features.sh`

Confirms the Coveo org has the licensed features this project depends on (Passage Retrieval, Relevance Generative Answering / CRGA, Automatic Relevance Tuning). Run it any time you want to re-verify org state — useful as a pre-demo check or after any org-level change.

```bash
scripts/validate_org_features.sh
```

Exit code: 0 if all required features are enabled, 1 otherwise.

### `validate_api_keys.sh`

Confirms both project API keys (`COVEO_PUSH_API_KEY`, `COVEO_ADMIN_API_KEY`) authenticate and have exactly the right privileges:

- Push key: Sources View (✓), Sources Edit (✗ — should NOT have it)
- Admin key: Sources View (✓), Sources Edit (✓)

```bash
scripts/validate_api_keys.sh
```

Exit code: 0 if both keys validate correctly, 1 otherwise.

### `add_mappings.sh`

Adds the 5 Pokemon Challenge field mappings (`pokemon_name`, `pokemon_type`, `image_url`, `dex_number`, `generation`) to the `pokemondb-sitemap` source.

**Idempotent.** Lists existing common mappings first and skips any field that's already mapped, so re-running is safe.

**Usage:**

```bash
scripts/add_mappings.sh
```

**What you should see on first run:**

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

**What you should see on re-run:**

```
Done: 0 created, 5 skipped.
```

### `update_scraping_config.sh`

Applies the web scraping configuration from `config/scraping_config.json` to the `pokemondb-sitemap` source.

The scraping config is what tells Coveo how to extract metadata (name, type, image, dex number, generation) from each Pokemon page using CSS/XPath selectors. Keeping it as a versioned JSON file means selector changes are diff-able in git and reproducible across orgs.

```bash
# edit config/scraping_config.json
scripts/update_scraping_config.sh
scripts/rebuild_source.sh
```

The config file lives at `config/scraping_config.json` at the repo root. It's a JSON array of configurations — typically the Coveo default (which excludes headers/footers/etc.) and our custom "Pokemon page metadata extraction" configuration.

### `widen_source.sh`

Updates the `pokemondb-sitemap` source's URL inclusion filter to one of three preset scopes, used to stage the crawl from a single Pokemon up to all ~1,025.

```bash
scripts/widen_source.sh narrow       # only bulbasaur (fast iteration)
scripts/widen_source.sh spot-check   # 8 diverse Pokemon (edge-case sweep)
scripts/widen_source.sh all          # all ~1,025 + 9 exclusion rules
```

Run a rebuild after to apply the new filter to indexed items:

```bash
scripts/rebuild_source.sh
```

The `spot-check` mode is recommended before `all`: it indexes 8 deliberately diverse Pokemon (Bulbasaur, Pikachu, Charizard, Mewtwo, Ho-Oh, Mr-Mime, Decidueye, Miraidon) covering multiple generations, single/dual types, and hyphenated names — so any scraping-config bugs surface in 30 seconds instead of after a 17-minute full crawl.

### `rebuild_source.sh`

Triggers a rebuild of `pokemondb-sitemap` via the REST API and polls the source status every 5 seconds until it returns to `IDLE`. Use this after any source-config change (mappings, URL filters, web scraping config) to apply the change to indexed items.

```bash
scripts/rebuild_source.sh
```

Single-Pokemon rebuilds complete in under 30 seconds.
