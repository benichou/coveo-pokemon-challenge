# Coveo API keys — how to (re)create them

This project uses **three Coveo API keys**, one per role, following a least-privilege pattern. Each key is created manually in the Coveo Admin Console (Coveo deliberately doesn't let API key creation itself be scripted — the key's secret value is shown to a human exactly once, then never again).

This document is the **single source of truth** for what those keys are, what they should be allowed to do, and how to recreate them on a fresh org. If you're onboarding to this repo, follow it top-to-bottom and you'll end up with a working `.env` ready for `scripts/bootstrap.sh`.

## TL;DR

| Key in `.env` | Console name | Coveo template | What it's for |
|---|---|---|---|
| `COVEO_PUSH_API_KEY` | `pokemon-push-source` | **Push API** | Used by the Python ingestion pipeline (Phase 4) to push documents into Source B. Never used in the browser. |
| `COVEO_ADMIN_API_KEY` | `pokemon-source-admin` | **Custom** (Sources + Fields Edit) | Used by the bash scripts in `scripts/` to manage source config, mappings, fields, and rebuilds. Never used in the browser. |
| `COVEO_SEARCH_API_KEY` | `pokemon-search` | **Anonymous search** | Used by the automated tests in `tests/` and by the Atomic UI in the browser to run search queries and send usage analytics. Safe to embed in browser-side code. |

All three keys are stored in the gitignored `.env` at the repo root. **Never commit them.**

## Why three keys instead of one

Coveo (sensibly) enforces a *security safeguard*: once an API key is created, its privileges cannot be changed. So if you want different levels of access for different jobs, you create different keys. This also lets us follow the principle of least privilege:

- The **push** key can push documents but cannot edit sources or query the index. If it leaks via a CI log, the blast radius is limited.
- The **admin** key can modify source config but cannot query or push. If it leaks, an attacker can't exfiltrate your indexed content via the Search API.
- The **search** key can query and send analytics, but cannot modify anything. It's the only one safe to ship to the browser, where end users can read it from the page source.

The validators in `scripts/validate/api_keys.sh` test that each key has *exactly* the privileges expected — including failing if the push key has Sources Edit (which would be a security regression).

## Common steps for every key

For each key below, the high-level Admin Console flow is the same. We only document the per-key differences in the sections below.

1. Open the **Coveo Admin Console** → left nav → **Organization → API keys**
2. Click **Add API key** (top right)
3. **Step 1 — Key purpose**: pick the template noted for that key
4. **Step 2 — Identification**: set `Name` and `Description` (see per-key sections)
5. **Step 3 — Configuration**:
   - Set `Expiration` to **30 days** (or longer; never "Never" — long-lived keys without rotation are a smell)
   - Leave `Allowed IPs` blank (we run from laptops and CI; pinning IPs introduces breakage faster than it adds security for this project)
6. **Step 4 — Access**: leave defaults. Your `Administrators` group has Edit access automatically.
7. **Step 5 — Review** → **Add API key**
8. ⚠️ **Copy the key value from the modal that appears.** Coveo never shows it again.
9. Paste it into `.env` next to the corresponding variable name (see TL;DR table).

Repeat for each key below.

## Key 1 — `pokemon-push-source` (Push)

| Setting | Value |
|---|---|
| **Template** | **Push API** (right column on the Key purpose page, labeled "Must remain private") |
| **Name** | `pokemon-push-source` |
| **Description** | `Authenticates the Python ingestion pipeline (push-pokemon/) that pushes Pokemon documents — scraped from pokemondb.net and enriched via pokeapi.co — into the pokemondb-push Source. Part of the FDE Pokemon Challenge.` |
| **`.env` variable** | `COVEO_PUSH_API_KEY` |

Privileges this template grants (don't change them):
- `Push items to sources`: Allowed
- `Push identities to security providers`: Allowed
- `Sources`: View all
- `Security identity providers`: View
- `Organization`: View

## Key 2 — `pokemon-source-admin` (Custom)

| Setting | Value |
|---|---|
| **Template** | **Custom** (at the bottom of the Key purpose grid) |
| **Name** | `pokemon-source-admin` |
| **Description** | `Admin key for managing pokemondb-sitemap source mappings, fields, and configuration. Used by the bash scripts in scripts/.` |
| **`.env` variable** | `COVEO_ADMIN_API_KEY` |

Custom privileges to grant explicitly:

| Service → Domain | Access level | Used by |
|---|---|---|
| **Content → Sources** | **Edit** (on All sources) | `scripts/setup/source.sh`, `scripts/setup/scraping.sh`, `scripts/setup/mappings.sh`, `scripts/source/widen.sh`, `scripts/source/rebuild.sh`, `scripts/audit/purge_index.sh` |
| **Content → Fields** | **Edit** (on All) | `scripts/setup/fields.sh` |
| **Search → Query pipelines** | **Edit** (on All) | `scripts/ml/associate_models.sh` (creates pipeline ↔ model associations) |
| **Machine Learning → Models** | **View** (on All) | `scripts/ml/associate_models.sh` (looks up model IDs by display name) |
| **Organization → Organization** | **View** | All scripts (org metadata lookup) |

Leave everything else off. No Push, no Search-time, no Analytics — this key is admin-only.

Why Custom and not a template: no preset template matches "Sources Edit + Fields Edit + Pipelines Edit + ML Models View without Push and without Search-time." Custom lets us craft exactly that.

> **History note (2026-05-30):** This key originally only had Sources + Fields Edit. When we built `scripts/ml/associate_models.sh` for the RGA + SE wiring (end of Day 2), we discovered the additional Pipelines + ML privileges were needed. Because Coveo enforces immutable privileges post-creation, that meant minting a new admin key with the full set above and replacing the old one in `.env`. If you're recreating from scratch, just grant all five privileges from the start.

## Key 3 — `pokemon-search` (Anonymous search)

| Setting | Value |
|---|---|
| **Template** | **Anonymous search** (left column, top of the Key purpose grid, labeled "Can be public") |
| **Name** | `pokemon-search` |
| **Description** | `Used by the test suite (tests/) and the local Atomic UI for browser-side search queries. Anonymous Search template; public-safe.` |
| **Search hub** (Step 3 of the wizard, only asked for this template) | **`pokemon-search`** — the search hub created when the hosted search page was added. Locks the key to our search experience; cannot be changed after creation. |
| **`.env` variable** | `COVEO_SEARCH_API_KEY` |

Privileges this template grants (don't change them):
- `Execute queries`: Allowed
- `Execute agent queries`: Allowed
- `Analytics data`: Push
- `Analytics - Impersonate`: Allowed

> **Note on Search hubs.** Coveo Anonymous Search keys are scoped to a single Search Hub at creation time. The `pokemon-search` hub is created automatically when you create the hosted search page of the same name (covered in the Phase 3 of the plan). If you don't have that hub yet, create the hosted search page first, then come back to mint this key.

This is the **only one of the three that's safe to embed in browser code** (its template is explicitly tagged "Can be public" in the Coveo UI). Even so, prefer using search tokens minted server-side in production deployments — this key is fine for a hosted demo but a real customer engagement would step it up.

## After all three keys are in `.env`

Run the validator:

```bash
scripts/validate/api_keys.sh
```

It checks that each key:
- Authenticates against Coveo
- Has the privileges we expect
- Does **not** have privileges it shouldn't (e.g., push key correctly cannot edit sources)

If all three pass, you're ready to run `scripts/bootstrap.sh` (which expects the push and admin keys for setup) and `pytest tests/` (which uses the search key).

## What happens if a key leaks

| Key | Mitigation |
|---|---|
| `pokemon-push-source` | Revoke in Coveo Admin Console → API keys → … menu → Delete. Push pipeline stops. No impact on search experience. Mint a new key, update `.env`. |
| `pokemon-source-admin` | Same procedure. Source config can no longer be changed via API. Bash scripts fail. Mint a new key, update `.env`. |
| `pokemon-search` | Same procedure. **However, this key is publicly visible in any deployed Atomic app.** That's by design — Anonymous Search keys are meant to be public. The mitigations are the privilege scope (it can only query and send analytics) and Coveo's per-key rate limits, not secrecy. |

## What's deliberately NOT in this document

- The key values themselves. Those live in `.env` (gitignored) and Coveo's Admin Console. If a key value is in this file, the file is wrong.
- Org-level features (Passage Retrieval, RGA). Those are licensed by Coveo and enabled by Coveo support after a request; not a per-developer action. See top-level README for the enablement email pattern.
