# `config/mcp/` — Coveo MCP Server configuration as code

## What's in here

| File | What it is |
|---|---|
| `pokemon-mcp.yaml` | Source-of-truth configuration for the `pokemon-mcp` Hosted MCP Server (Phase 8.5). Mirrors the Coveo Admin Console state, with the server instructions verbatim. |

## Why this exists

The Coveo Hosted MCP Server is configured through the Admin Console UI. As of 2026-06-03 (when we set this up), Coveo does **not** expose a public REST admin API for managing MCP Server configs — verified by `scripts/mcp/discover_api.sh`, which probed 8 plausible endpoint shapes against both our admin and ml-models API keys and got 404 INVALID_URI on every one.

But the rest of this repo follows a strict **code-as-source-of-truth** discipline for AI configuration:

| AI artifact | Source of truth in repo | How it's applied to Coveo |
|---|---|---|
| RGA Custom Prompt | `rga-closed-loop/prompts/pokemon-rga.yaml` | `rga-closed-loop/src/apply.py` (PUT) |
| Query Suggest seed queries | `config/ml/default-queries.json` | `scripts/ml/seed_query_suggest.sh` (multipart PUT) |
| ML model pipeline associations | `scripts/ml/associate_models.sh` | Script reads YAML, POSTs associations |
| MCP server config | **`config/mcp/pokemon-mcp.yaml`** | **Manual paste into Console (until Coveo publishes admin API)** |

We honor that discipline for MCP too — even when the API doesn't (yet) exist for full automation. The YAML is the truth; the Console is a downstream mirror.

## Workflow when editing the YAML

1. **Edit `pokemon-mcp.yaml`** with the desired change (e.g., updating `server_instructions`, adding a tool description, etc.)
2. **Open Coveo Admin Console** → AI & ML → MCP Server → `pokemon-mcp`
3. **Paste the relevant section** from the YAML into the matching Console tab:
   - `server_instructions` → **Server implementation tab** → Server instructions text area
   - Tool `description` → **Tools tab** → click the tool → Description field
   - Tool `answer_configuration` → **Tools tab** → answer tool → Answer configuration dropdown
   - Tool list changes → **Tools tab** → Add tool / Remove tool
   - `auth_methods` → **Overview tab** → Authentication methods section
4. **Save in the Console**
5. **Bump the version + add a `history` entry** at the bottom of `pokemon-mcp.yaml` with date + rationale
6. **Commit + push** — git diff captures what changed, the history entry captures why

## Workflow when Coveo publishes the admin API

The day Coveo publishes a public REST API for MCP Server config (likely under `/rest/organizations/{org}/machinelearning/mcp/...` based on conventional patterns), the manual workflow gets replaced with an apply script — same pattern as `rga-closed-loop/src/apply.py`:

- `scripts/mcp/apply_mcp_server.sh` (or `apply_mcp_server.py`)
- Reads `pokemon-mcp.yaml`
- PUTs to Coveo's MCP Server admin API
- Dry-run by default; `--apply` to write
- Post-PUT verification (GET the same endpoint, diff against YAML, exit non-zero on mismatch)

Until then, `scripts/mcp/discover_api.sh` can be re-run periodically (or automated via CI) to detect when the API surfaces. If it ever returns 200, build the apply script.

## Why YAML and not JSON

Matches the project's existing AI-config artifacts. `rga-closed-loop/prompts/pokemon-rga.yaml` is the precedent — readable multi-line strings, comments allowed, structured history blocks. The two AI-config YAMLs now sit in parallel.

## Why versioning matters even without automation

Three reasons the YAML is valuable even when the apply step is manual:

1. **Diffable history.** `git log -p config/mcp/pokemon-mcp.yaml` shows every server-instruction change with its rationale. Same panel-narrative value as the RGA prompt history dashboard.
2. **Onboarding.** A new contributor cloning the repo can see the exact Console state without logging into Coveo's org. The YAML is documentation that doesn't drift from code.
3. **Disaster recovery.** If the MCP server config is accidentally destroyed in the Console, the YAML rehydrates it via manual paste in ~2 minutes. Without the YAML, that's a lossy reconstruction.

## See also

- `docs/mcp-integration.md` — panel-shareable architecture doc covering the whole Phase 8.5 integration
- `docs/api-keys.md` → Key 6 (`pokemon-mcp` Anonymous API key)
- `.claude/mcp.json` — Claude Code wiring (consumes `COVEO_MCP_ENDPOINT` + `COVEO_MCP_API_KEY` env vars)
- `.claude/skills/pokemon-mcp/SKILL.md` — `/pokemon-mcp` demo skill
- `scripts/mcp/discover_api.sh` — read-only diagnostic that probes for the (currently nonexistent) admin REST API
