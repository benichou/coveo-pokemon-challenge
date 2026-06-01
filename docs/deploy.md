# Deploy runbook — RGA eval cron + dashboard

This is the operational counterpart to [`api-keys.md`](api-keys.md). It covers everything that can't be scripted from the repo: the GitHub Actions secret wiring + the Vercel project setup that together turn the RGA evaluator into a daily, self-publishing quality scorecard.

## Architecture recap (where secrets live)

```
GitHub Actions (cron + manual trigger)
    │  uses 5 secrets to call Coveo + Anthropic
    │
    ▼
runs rga-eval/src/main.py
    │  writes eval-runs/YYYY-MM-DD-<mode>.json
    │  commits + pushes back to the same branch
    │
    ▼
push to GitHub
    │  webhook
    ▼
Vercel rebuilds rga-dashboard
    │  reads eval-runs/*-full.json AT BUILD TIME (Vite glob)
    │  produces static HTML + JS — no runtime secrets
    │
    ▼
public dashboard URL
```

**The Vercel side needs zero secrets for the dashboard.** The eval runs in GitHub Actions; the dashboard just rebundles the resulting JSON files.

Other apps in this repo (`atomic-search`, eventually `detail-page`) will have their own Vercel projects with their own `VITE_*` env vars — none of those will need the secrets used by the eval cron.

## Part 1 — GitHub Actions secrets

These are the 5 secrets the daily eval workflow consumes. **Add them in the GitHub repo's Settings → Secrets and variables → Actions → "New repository secret"** for each one.

| Secret name | What it is | Where to get it |
|---|---|---|
| `COVEO_ORG_ID` | `benichouu9fose4g` (or whatever your org ID is) | Coveo Admin Console URL bar, or Organization → Settings |
| `COVEO_RGA_JUDGE_API_KEY` | `xx…` (`Knowledge.Answer Manager: Edit` privilege) | See `docs/api-keys.md` — this is the `pokemon-rga-judge` key. Used once per run to discover the answer-config ID. |
| `COVEO_SEARCH_API_KEY` | `xx…` (Anonymous Search template) | `pokemon-search` key from `docs/api-keys.md`. Used to stream the actual /generate responses. |
| `COVEO_RGA_CONFIG_ID` | `5b8c16ea-da79-4646-8877-948840a2dac7` (or whatever yours is) | Optional but recommended — caches the config-discovery API call so the workflow doesn't hit Coveo for it every day. Find it via `curl -H "Authorization: Bearer $COVEO_RGA_JUDGE_API_KEY" "https://platform.cloud.coveo.com/rest/organizations/$COVEO_ORG_ID/answer/v1/configs" \| jq '.items[0].id'`. |
| `ANTHROPIC_API_KEY` | `sk-ant-xx…` | Your personal Anthropic console (console.anthropic.com → API keys). **Do not use Carta's enterprise key** — this repo is on your personal GitHub. |

### Step-by-step

1. Open `https://github.com/<you>/coveo-pokemon-challenge/settings/secrets/actions`.
2. Click **New repository secret**.
3. Paste the name (one of the 5 above) and the value.
4. **Save**, then repeat for the next one.

GitHub never displays secret values back to you after creation — only the names. If you forget a value, you re-mint it (Coveo + Anthropic both let you create new keys; you delete the old one).

### Verifying the secrets work

The cleanest test is to fire the workflow manually with a small smoke run:

1. Open **Actions** tab → **RGA daily eval** → **Run workflow** button (top-right).
2. Pick **Mode = smoke**, **Limit = 5**. Click **Run workflow**.
3. Watch the run. The "Run RGA evaluator" step prints per-question results; the "Commit + push" step pushes `eval-runs/YYYY-MM-DD-smoke.json` to the branch.
4. When the run goes green, you have a working pipeline.

If the run fails at "Run RGA evaluator" with an env-var error, double-check the secret names — they're case-sensitive and must match exactly.

## Part 2 — Vercel project: rga-dashboard

The dashboard is a static Vite + React + recharts site. Vercel auto-detects everything; the only manual config is the **Root Directory**.

### Step-by-step

1. Go to https://vercel.com/new (you may need to authorize Vercel to read your GitHub repos).
2. **Import** `coveo-pokemon-challenge`.
3. On the configure-project screen:
   - **Project Name:** `pokemon-rga-dashboard` (or whatever you want — this becomes the subdomain).
   - **Framework Preset:** Vite (auto-detected).
   - **Root Directory:** click **Edit** and set to `rga-dashboard`. This is the one knob that matters.
   - **Build Command:** leave default (`npm run build`).
   - **Output Directory:** leave default (`dist`).
   - **Environment Variables:** none. (Confirm the section is empty — the dashboard has zero runtime secrets.)
4. **Deploy.** First build takes ~30s.
5. Vercel issues you a URL like `pokemon-rga-dashboard.vercel.app`. Open it; you should see the dashboard with whatever eval runs are in your repo.

### Picking the deploy branch

Vercel watches a "Production Branch" — by default `main`. If you're still on `feature/essential` and haven't merged to `main` yet:

- Either merge `feature/essential` → `main` first, then deploy (clean public URL),
- Or in Vercel's project settings → **Git** → change Production Branch to `feature/essential` until you merge.

Every subsequent push to that branch (including the cron's daily commits) triggers an automatic redeploy.

## Part 3 — End-to-end verification

After Parts 1 + 2 are done, prove the whole loop works:

1. **Fire the workflow manually** (Actions → RGA daily eval → Run workflow → mode = smoke, limit = 5). Wait ~1 min.
2. **Check the commit** — `git pull` locally; you should see a new `eval-runs/YYYY-MM-DD-smoke.json` committed by `github-actions[bot]`.
3. **Check Vercel** — a new deployment should be running on the dashboard project. ~30s after it finishes, refresh the URL — the smoke run won't appear in the time-series (only `*-full.json` files do), but the deploy itself confirms the webhook pipe is healthy.
4. **Tomorrow at 06:00 UTC**, the scheduled cron fires automatically and writes `YYYY-MM-DD-full.json`. The dashboard's time-series chart gains a new data point.

## Cost ceiling

A worst-case daily full run costs:
- **Coveo:** zero billable units — RGA is included in the licensed feature set.
- **Anthropic:** ~$0.55–0.65 per 100-question run with Sonnet 4.6. At one run/day for a month: ~$18. Well under the personal Anthropic budget.
- **GitHub Actions:** unlimited free minutes on public repos. (Private repo: ~10 min × 30 days = 300 min/mo, easily inside the 2,000 free minutes for personal accounts.)
- **Vercel:** Hobby tier is free for personal projects. Static-site builds use minimal compute.

Total: under $20/month, durable indefinitely.

## Troubleshooting

**Workflow fails with `RGA generate failed (HTTP 403)`** — the search key lost its `Search.Execute Query` privilege, or it expired. Re-mint per `docs/api-keys.md`, update the secret in GitHub.

**Workflow fails with `Coveo returned no answer configs`** — the answer config was deleted (e.g., the RGA model was rebuilt from scratch in the Coveo Console). Recreate the config per `docs/ml-models.md`, then update `COVEO_RGA_CONFIG_ID` in GitHub secrets.

**Workflow succeeds but no commit happens** — the eval ran but produced an existing date's file (re-run on the same day). The "Commit + push" step silently exits when `git status` shows no changes — this is by design.

**Vercel deploy succeeds but the new run doesn't appear on the dashboard** — confirm the file is named `YYYY-MM-DD-full.json` (smoke / layerN files are intentionally excluded from the time-series).

---

## Part 4 — Branch protection (recommended, one-time, ~3 min)

To actually enforce the CI checks in `.github/workflows/pr-checks.yml`, configure branch protection on `main`:

1. GitHub → Settings → Branches → **Add branch protection rule**
2. Branch name pattern: `main`
3. Enable **Require status checks to pass before merging**
4. Search and check these required status checks (they appear after the first PR-checks workflow runs once):
   - `Pre-commit hooks (ruff lint + format + file hygiene)`
   - `Python tests (rga-eval)`
   - `Python tests (rga-closed-loop)`
   - `rga-dashboard TypeScript + build`
   - `Secret scan (TruffleHog)`
5. Enable **Require branches to be up to date before merging**
6. **Restrict force pushes** — but allow admins (so you can still force-push from your own laptop if a history rewrite is needed)
7. **Allow GitHub Actions to bypass** — the daily eval + closed-loop crons need to commit directly to `main` without going through a PR
8. **Save**

The PR-checks workflow runs on every `pull_request` AND on direct `push` to main. The cron commits will still go green (the workflow runs after the push, and the checks pass) — they just won't be blocked by review requirements.

### What the PR checks gate against

| Check | Catches |
|---|---|
| **pre-commit** | ruff lint errors, formatting drift, trailing whitespace, missing EOF newlines, invalid YAML/JSON, large file commits, merge-conflict markers |
| **python-tests (rga-eval)** | Eval / schema / metrics regressions |
| **python-tests (rga-closed-loop)** | Apply script / guardrails regressions (38 unit tests) |
| **dashboard-build** | TypeScript errors, broken eval-runs glob, build failures |
| **secret-scan (TruffleHog --only-verified)** | Live API keys accidentally committed (defense against the IDE auto-share-selection pattern) |

`tests/` integration suite is **NOT** in the gate — those tests hit the live Coveo org and would require uploading API keys to a public-PR-triggerable workflow, which we explicitly avoid.
