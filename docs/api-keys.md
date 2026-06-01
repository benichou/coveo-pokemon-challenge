# API keys — how to (re)create them

This project uses **five Coveo API keys** (one per role, least-privilege) plus **one Anthropic API key** (for the LLM-as-judge in Phase 6D and the closed-loop analyzer in Phase 6F). Each is created manually in its respective console — both Coveo and Anthropic show the secret value to a human exactly once at creation, then never again.

This document is the **single source of truth** for what those keys are, what they should be allowed to do, and how to recreate them on a fresh setup. If you're onboarding to this repo, follow it top-to-bottom and you'll end up with a working `.env` ready for `scripts/bootstrap.sh`.

## TL;DR

| Key in `.env` | Provider / Console name | Template / Scope | What it's for |
|---|---|---|---|
| `COVEO_PUSH_API_KEY` | Coveo / `pokemon-push-source` | **Push API** | Used by the Python ingestion pipeline (Phase 4) to push documents into Source B. Never used in the browser. |
| `COVEO_ADMIN_API_KEY` | Coveo / `pokemon-source-admin` | **Custom** (Sources + Fields Edit) | Used by the bash scripts in `scripts/` to manage source config, mappings, fields, and rebuilds. Never used in the browser. *Note: this key does NOT have Machine Learning Models: Edit — that's a separate scope that lives on the dedicated key below.* |
| `COVEO_SEARCH_API_KEY` | Coveo / `pokemon-search` | **Anonymous search** | Used by the automated tests in `tests/`, by the Atomic UI in the browser, AND by the RGA evaluator's `/generate` calls (Anonymous Search includes Search.Execute Query + Answer Manager:Use, which the RGA streaming endpoint requires). Safe to embed in browser-side code. |
| `COVEO_RGA_JUDGE_API_KEY` | Coveo / `pokemon-rga-judge` | **Custom** (Knowledge.Answer Manager: Edit) | Used by the RGA Skill Evaluator (Phase 6D) to **discover the answer-config id** at startup. NOT used for generation (that needs Search.Execute Query, which this key doesn't have — discovery is the only thing it does). |
| `COVEO_ML_MODELS_API_KEY` | Coveo / `pokemon-ml-models-editor` | **Custom** (Machine Learning Models: Edit) | Used by the **Phase 6F closed-loop apply script** (`rga-closed-loop/src/apply.py`) to PUT RGA Custom Prompt updates to `/machinelearning/models/{id}`. Minted 2026-06-01 after the 6F.1 spike empirically found that the admin key's Sources+Fields scope didn't include ML Models:Edit (got a 403 on PUT despite working for GET). Least-privilege key — only ML model read/write, nothing else. |
| `ANTHROPIC_API_KEY` | Anthropic / personal account | **Workspace-scoped** (limited spend, no admin) | Used by `rga-eval/src/llm_judge.py` (Sonnet 4.6 LLM-as-judge for the 100-Q eval) and `rga-closed-loop/src/analyzer.py` (closed-loop prompt-refinement analyzer). **Personal Anthropic account, NOT a corporate / enterprise key** — using corporate AI vendor keys on a personal GitHub repo is an audit/compliance concern (see `~/.claude/rules/security.md`). Free $5 signup credit covers most of the build phase. |

All six keys are stored in the gitignored `.env` at the repo root. **Never commit them.**

## Why five keys instead of one

Coveo (sensibly) enforces a *security safeguard*: once an API key is created, its privileges cannot be changed. So if you want different levels of access for different jobs, you create different keys. This also lets us follow the principle of least privilege:

- The **push** key can push documents but cannot edit sources or query the index. If it leaks via a CI log, the blast radius is limited.
- The **admin** key can modify source config but cannot query, push, or write ML models. If it leaks, an attacker can't exfiltrate your indexed content via the Search API.
- The **search** key can query and send analytics, but cannot modify anything. It's the only one safe to ship to the browser, where end users can read it from the page source.
- The **judge** key (added in Phase 6D) can list/edit answer configs but cannot query — it's used solely for discovering the RGA config id at eval startup. Wrong privilege scope to do anything more dangerous.
- The **ml-models** key (added in Phase 6F) can read and write ML model configurations only. It's the apply-script's key for PUTting RGA Custom Prompt updates. Nothing else.

The validators in `scripts/validate/api_keys.sh` test that the first three keys have *exactly* the privileges expected — including failing if the push key has Sources Edit (which would be a security regression). The judge and ml-models keys aren't yet covered by the validator (TODO).

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

## Key 4 — `pokemon-rga-judge` (Custom)

| Setting | Value |
|---|---|
| **Template** | **Custom** |
| **Name** | `pokemon-rga-judge` |
| **Description** | `Used by the Phase 6D RGA Skill Evaluator to discover the answer-config id at startup. Knowledge.Answer Manager only — does NOT execute queries.` |
| **`.env` variable** | `COVEO_RGA_JUDGE_API_KEY` |

Custom privileges to grant explicitly:

| Service → Domain | Access level | Used by |
|---|---|---|
| **Knowledge → Answer Manager** | **Edit** (on All) | `rga-eval/src/coveo_rga.py` (calls `GET /answer/v1/configs` to discover the config id) |

Leave everything else off. This key deliberately doesn't have `Search.Execute Query` — the generate-endpoint streaming calls in `rga-eval/src/main.py` use the search key instead (which has Execute Query as part of its Anonymous Search template). Two-key pattern by design: judge key for config discovery, search key for execution.

> **History note (2026-05-31):** Originally Phase 6D was supposed to use a single key for both config discovery and generation. The generation call returned 403 because Knowledge.Answer Manager doesn't include Execute Query. Pivoted to the two-key pattern documented above. The split is also a security feature — the judge key's blast radius is limited to "list/edit answer configs," nothing more.

## Key 5 — `pokemon-ml-models-editor` (Custom)

| Setting | Value |
|---|---|
| **Template** | **Custom** |
| **Name** | `pokemon-ml-models-editor` |
| **Description** | `Used by rga-closed-loop/src/apply.py (Phase 6F) to PUT RGA Custom Prompt updates to /machinelearning/models/{id}. Least-privilege key dedicated to ML model writes.` |
| **`.env` variable** | `COVEO_ML_MODELS_API_KEY` |

Custom privileges to grant explicitly:

| Service → Domain | Access level | Used by |
|---|---|---|
| **Machine Learning → Models** | **Edit** (on All) | `rga-closed-loop/src/apply.py` — GET to fetch current model state + PUT to update `extraConfig.additionalAnswerInstructions` |

Leave everything else off. This key only reads/writes ML models — it can't query, push, or touch source config.

> **History note (2026-06-01):** Originally Phase 6F's plan said "reuse the admin key, no new key needed." The 6F.1 spike empirically found that wrong — the admin key has `Sources + Fields Edit` but not `ML Models Edit`, so its PUT to `/machinelearning/models/{id}` returned 403. The fix was to mint this dedicated key with exactly the right scope (and nothing else). A useful diagnostic moment: we verified an architectural assumption before shipping.

## Key 6 — Anthropic API key (personal, not Coveo)

This is the only non-Coveo key in `.env`. Used by the LLM-as-judge (Phase 6D) and the closed-loop analyzer (Phase 6F).

| Setting | Value |
|---|---|
| **Provider** | Anthropic (https://console.anthropic.com) |
| **Account** | **Personal** — sign up with a personal email, not a corporate SSO |
| **`.env` variable** | `ANTHROPIC_API_KEY` |
| **GH Secret name** | `ANTHROPIC_API_KEY` (also needed in GitHub Actions for the daily cron) |

### Why a personal account, not corporate

Using a corporate AI vendor key (e.g., Carta's enterprise Anthropic key) on a **personal GitHub repo intended for a Coveo job application** is an audit + compliance concern. Three reasons:

1. **Audit trail.** Corporate Anthropic usage gets logged against your employer's account. Personal-project tokens showing up in the audit log invite questions you don't want.
2. **Cost attribution.** Personal project work shouldn't bill against the employer's enterprise contract.
3. **`~/.claude/rules/security.md`** — Carta's security policy explicitly flags this pattern.

The free $5 signup credit covers most of the build phase. Cost forecast: ~$0.55/day if the daily eval cron runs every day (Sonnet 4.6, ~$0.006 per question × 100 questions × 1 run/day) plus ~$0.04 per closed-loop analyzer run. Roughly ~$18/month worst-case at full daily cadence.

### Step-by-step

1. Open https://console.anthropic.com → sign up with a **personal email** (not your employer's)
2. Settings → **API keys** → **Create key**
3. Name: `pokemon-rga` (or whatever; it's only for your reference)
4. **Workspace:** Default
5. **Permissions:** "User" is fine (you're the only consumer)
6. Click **Create key**
7. ⚠️ **Copy the secret value from the modal.** Anthropic only shows it once, exactly like Coveo.
8. Paste into `.env` as `ANTHROPIC_API_KEY=sk-ant-api03-...`
9. Also add it to **GitHub Actions Secrets** (Settings → Secrets and variables → Actions → New repository secret → name `ANTHROPIC_API_KEY`). Both must match for the daily cron to work.

### Rotation cadence

Anthropic doesn't expire keys by default. Rotate proactively:
- **Every 90 days** as a baseline
- **Immediately** if the key value ever appears in chat or logs (the IDE auto-share-selection pattern on `.env` files has triggered this several times during the build — see the recurring security flag in project memory)
- **Immediately** if the GitHub Actions Secret gets rotated for any reason (the two must always match)

### Cost monitoring

Anthropic's console shows daily / monthly usage. Set a billing alert at $25/month so unexpected runaway usage triggers an email. With the daily cron + closed-loop, normal cadence is ~$18/month worst case.

## After all six keys are in `.env`

Run the validator:

```bash
scripts/validate/api_keys.sh
```

It checks that each key:
- Authenticates against Coveo
- Has the privileges we expect
- Does **not** have privileges it shouldn't (e.g., push key correctly cannot edit sources)

If all keys pass, you're ready to run `scripts/bootstrap.sh` (push + admin keys), `pytest tests/` (search key), `uv run python rga-eval/src/main.py` (judge + search + admin keys), and `uv run python rga-closed-loop/src/apply.py` (ml-models key).

> **Note (2026-06-01):** the validator in `scripts/validate/api_keys.sh` was written when the project only had 3 keys. The judge key and ml-models key are not yet validator-aware — they're verified manually by running the eval and the apply script's dry-run. Updating the validator to cover all five keys is a small future improvement.

## What happens if a key leaks

| Key | Mitigation |
|---|---|
| `pokemon-push-source` | Revoke in Coveo Admin Console → API keys → … menu → Delete. Push pipeline stops. No impact on search experience. Mint a new key, update `.env`. |
| `pokemon-source-admin` | Same procedure. Source config can no longer be changed via API. Bash scripts fail. Mint a new key, update `.env`. |
| `pokemon-search` | Same procedure. **However, this key is publicly visible in any deployed Atomic app.** That's by design — Anonymous Search keys are meant to be public. The mitigations are the privilege scope (it can only query and send analytics) and Coveo's per-key rate limits, not secrecy. |
| `pokemon-rga-judge` | Same procedure. RGA eval stops working until rotated. Blast radius limited to listing/editing answer configs. |
| `pokemon-ml-models-editor` | Same procedure. Closed-loop apply script stops working until rotated. Blast radius limited to reading/writing ML models (no source / push / search access). |
| `ANTHROPIC_API_KEY` | Revoke at https://console.anthropic.com → API keys → … menu → Delete. Mint a fresh key. Update **both** `.env` AND the GitHub Actions Secret (they must match). Eval cron + closed-loop analyzer stop until both are updated. Blast radius limited to Anthropic API spend on the personal account (no Coveo / no Carta exposure). |

## Local `.env` ↔ Vercel env vars — the naming reference

Confusion-prone: a few of these keys are read under one name locally (`.env`) and another name in the browser bundle (`import.meta.env.VITE_*`). The table below is the canonical mapping.

### How to read this table

- The **left column** is the variable name in your local `.env` — the canonical source of truth.
- The **middle column** is what the Vite-built apps read from `import.meta.env.*` (only `VITE_`-prefixed vars get exposed to the browser bundle, per Vite security defaults).
- The **right column** is what to set in **Vercel project settings → Environment Variables** for each deployed app. Vercel injects these into `process.env` at build time; `vite.config.js` in each app translates `process.env.*` → `import.meta.env.VITE_*`.

| `.env` variable (local) | Read at runtime as | Set in Vercel as (recommended) | Used by |
|---|---|---|---|
| `COVEO_ORG_ID` | `import.meta.env.VITE_COVEO_ORG_ID` | `COVEO_ORG_ID` | `atomic-search/` |
| `COVEO_SEARCH_API_KEY` | `import.meta.env.VITE_COVEO_SEARCH_TOKEN` | `COVEO_SEARCH_API_KEY` | `atomic-search/` |
| (no env vars needed) | n/a | (leave empty) | `rga-dashboard/` (static, build-time data only) |

### Why the local + Vercel names match (intentional)

Both `atomic-search/vite.config.js` and any future Vite app in the repo accept **either** the canonical `COVEO_*` names **or** the `VITE_COVEO_*` names. The `firstDefined()` helper checks both, then falls back to `process.env` (which is what Vercel populates).

**Why this matters:** the same `.env` file works locally for ALL apps in the repo. You don't have to maintain a separate `.env` in `atomic-search/` with `VITE_*` mirrors — the Vite config does the translation. And on Vercel, you can use the same canonical names you already know, no mental remapping.

### Why the canonical names are recommended over `VITE_*` in Vercel

- **Mental load**: pasting `COVEO_SEARCH_API_KEY` matches what you see in `.env`. Pasting `VITE_COVEO_SEARCH_TOKEN` requires you to remember "the *value* I want for VITE_COVEO_SEARCH_TOKEN actually lives under `COVEO_SEARCH_API_KEY` in .env" — extra reasoning every time you set up a new environment.
- **Source-of-truth alignment**: docs/api-keys.md, `.env`, scripts, tests, Python projects, and Vercel all use the same name. One source of truth.
- **The `VITE_COVEO_SEARCH_TOKEN=` line in `.env`** is intentionally empty — it's a placeholder that the Vite config never actually reads when `COVEO_SEARCH_API_KEY` is populated.

### What does NOT go in Vercel

The four other Coveo keys (`COVEO_PUSH_API_KEY`, `COVEO_ADMIN_API_KEY`, `COVEO_RGA_JUDGE_API_KEY`, `COVEO_ML_MODELS_API_KEY`) and the `ANTHROPIC_API_KEY` are **never** Vercel env vars. They're:

- Used by Python scripts that run locally OR in GitHub Actions (not in a Vercel build)
- Sensitive in ways the search key is not (can edit sources, push docs, query, edit ML models, spend Anthropic credit)
- Stored in **GitHub Actions Secrets** for the daily cron workflows — see [`docs/deploy.md`](deploy.md) Part 1 for the GH Secrets list

Mixing the two namespaces is a common security mistake. **The Vercel UI is the wrong place for the admin/push/judge/ml-models keys** — they'd be readable by anyone with project-settings access and would expand the blast radius of a Vercel account compromise.

## What's deliberately NOT in this document

- The key values themselves. Those live in `.env` (gitignored) and the respective consoles. If a key value is in this file, the file is wrong.
- Org-level features (Passage Retrieval, RGA). Those are licensed by Coveo and enabled by Coveo support after a request; not a per-developer action. See top-level README for the enablement email pattern.
- Anthropic billing setup. Just enough is covered above to mint a working key; full billing / spend-cap / team-seat configuration is the user's call.

---

## Phase 6F.1 — Coveo ML Models API surface (RGA prompt management)

This section records the spike findings from 2026-06-01 that unlocked Phase 6F (closed-loop RGA prompt-tuning). It's the technical reference for the apply script ([`rga-closed-loop/src/apply.py`](../rga-closed-loop/src/apply.py), shipped 2026-06-01) and the analyzer ([`rga-closed-loop/src/analyzer.py`](../rga-closed-loop/), ships in 6F.3).

### Where the prompt lives in the API

The "Prompt enhancement → Prompt instruction" field visible in the Coveo Admin Console (AI & ML → Models → `pokemon-rga`) is stored as:

```
extraConfig.additionalAnswerInstructions   (string)
```

…on the `genqa` model object returned by the **Machine Learning Models API**.

### Endpoints (verified end-to-end)

| Operation | Endpoint | Auth | Status |
|---|---|---|---|
| List all models on the org | `GET /rest/organizations/{orgId}/machinelearning/models` | Admin or ML Models key | ✅ 200 verified |
| Get one model by id | `GET /rest/organizations/{orgId}/machinelearning/models/{modelId}` | Admin or ML Models key | ✅ 200 verified |
| Update one model's config | `PUT /rest/organizations/{orgId}/machinelearning/models/{modelId}` (**full body**) | **ML Models key required** (Machine Learning Models: Edit) | ✅ 200 verified on 2026-06-01 via `rga-closed-loop/src/apply.py --apply --force` (no-op PUT that re-fetched and confirmed byte-identical match) |
| `PUT /machinelearning/models/{modelId}/details` | sub-resource | — | ❌ 405 Method Not Allowed (endpoint doesn't accept PUT) |
| `PATCH /machinelearning/models/{modelId}` | partial update | — | ❌ 405 Method Not Allowed (endpoint doesn't accept PATCH) |

The single write path is full-body PUT to `/machinelearning/models/{id}`. The apply script fetches the current model, mutates `extraConfig.additionalAnswerInstructions`, PUTs the whole object back.

### Privilege scoping — what each key can and can't do

Three keys were tested against the ML Models API. Verified empirically on 2026-06-01:

| Key | Scope | GET models | PUT model | Notes |
|---|---|---|---|---|
| `COVEO_RGA_JUDGE_API_KEY` | Knowledge.Answer Manager: Edit | ❌ 403 | ❌ 403 | Wrong privilege domain entirely. |
| `COVEO_ADMIN_API_KEY` | Sources + Fields Edit | ✅ 200 | ❌ 403 | Can READ models (because View is implicitly granted to any Edit'er on the platform), but cannot write. Models:Edit was not selected when this key was created. |
| `COVEO_ML_MODELS_API_KEY` | Machine Learning Models: Edit | ✅ 200 | ✅ 200 | The right key. Least-privilege — does nothing besides ML model read/write. |

The minting of the 5th key was driven by this finding — the original Phase 6F plan said "reuse the admin key, no new key needed," and the spike empirically proved that wrong. A useful diagnostic moment: we verified an architectural assumption before shipping.

### Model identity (for the pokemon-rga model)

These IDs are the ones in this org as of 2026-06-01. They will differ on a different org / on a freshly-rebuilt model:

```
id:                benichouu9fose4g_genqa_9463d004_1a3c_4f40_ba32_4ea245fdfb78
modelDisplayName:  pokemon-rga                  ← stable human-readable identifier
engineId:          genqa                        ← RGA = "Generative QA"
status:            ONLINE
```

The apply script discovers the model id at runtime by listing models and filtering on `modelDisplayName == "pokemon-rga"`, so a rebuild that changes the underlying id is automatically handled.

### Co-located models worth knowing about

A second model — `pokemon-se` (`engineId: "embeddings"`) — is the Semantic Encoder we associated to the same pipeline. It has the same top-level shape but **does not have an `additionalAnswerInstructions` field** under `extraConfig`. The prompt-API surface is RGA-specific.

### Endpoints that DON'T expose the prompt

For future reference, so we don't re-walk the dead ends:

- `GET /rest/organizations/{org}/answer/v1/configs/{configId}` — returns the answer config wrapper (`id`, `name`, `answerType`, timestamps) but NOT the prompt. The answer config points to the model; the prompt lives on the model.
- `GET /rest/organizations/{org}/machinelearning/configurations` — returns 404. This is the "Advanced Model Configurations" naming from an older Coveo doc; the actual surface is `/machinelearning/models`.
- `GET /rest/organizations/{org}/machinelearning/model/{id}` (singular) — Coveo uses the plural form.

### What the PUT body looks like (verified live 2026-06-01)

The apply script uses the **full-body PUT** shape: fetch the current model, mutate only `extraConfig.additionalAnswerInstructions`, PUT the whole object back to `/models/{id}`. See [`rga-closed-loop/src/apply.py`](../rga-closed-loop/src/apply.py) — `patch_model_body()` does the field surgery and the verification step re-fetches to confirm the live value matches what was sent.

This was verified end-to-end via a no-op `--apply --force` invocation — same prompt content sent back to Coveo, then re-fetched and confirmed byte-identical. PUT returned 200; re-fetch matched. The script's exit code 2 on a verification failure (post-PUT live ≠ what we sent) is the safety net if Coveo ever silently transforms the body in transit.

Alternative PUT shapes (`PUT /models/{id}/details`, `PATCH /models/{id}`) were tested and both return 405 Method Not Allowed. Full-body PUT is the only write path.

### Reproducibility

Anyone with the admin key can run the spike themselves:

```bash
set -a; source .env; set +a
curl -sS -H "Authorization: Bearer $COVEO_ADMIN_API_KEY" \
  "https://platform.cloud.coveo.com/rest/organizations/$COVEO_ORG_ID/machinelearning/models" \
  | jq '.[] | select(.modelDisplayName == "pokemon-rga") | .extraConfig.additionalAnswerInstructions | length'
```

This prints the length of the currently-live prompt — a one-liner sanity check that the prompt was saved and is what you expect. Currently returns `1201` (the Pokemon-specific prompt landed in the Console on 2026-06-01).
