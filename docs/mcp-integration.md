# Coveo MCP Server integration — Pokémon index as an agent surface

This document is the panel-shareable record of why and how we wired the Coveo Hosted MCP Server into this build, what we observed in testing, and how it bridges Topic 1 (technical deep dive) to Topic 2 (customer pitch).

> **For the panel.** Doc 2's brief doesn't mention MCP — this is a beyond-bonus phase that earned its place during the build because Coveo released a hosted MCP Server in 2026 that turns any Coveo org into an AI-agent surface with zero additional code. Our Pokémon org now answers natural-language questions from Claude Code, Claude Desktop, ChatGPT Enterprise, and any other MCP-compatible client — using the same RGA model, the same Passage Retrieval API, the same Search API, the same index. No second integration, no separate vector DB, no bespoke connector per LLM. The slide writes itself: *"Your Coveo investment is your AI-agent investment."*

## Coveo's positioning — MCP as the interoperability layer

> *"Coveo extends the AI-Relevance Platform to support seamless integration with leading large language models, including ChatGPT Enterprise and Anthropic's Claude, while maintaining enterprise-grade security and governance."*
> — Coveo, [Hosted MCP Server announcement](https://www.prnewswire.com/news-releases/coveo-announces-hosted-mcp-server-to-expand-enterprise-ai-and-agentic-partner-ecosystem-302683287.html)

Coveo's bet: generative LLMs are commodities; the moat is **how content gets fed into them, securely, with permissions intact**. MCP is the protocol Anthropic introduced in late 2024 that lets any MCP-compatible LLM client (Claude Desktop, Claude Code, ChatGPT Enterprise, Cursor, etc.) talk to any MCP-compatible tool server through a standard interface. Coveo's hosted server makes a Coveo org one of those interoperable backends.

### MCP-server adoption (2026)

- 41% of surveyed software organizations are in limited or broad production with MCP servers (Stacklok 2026)
- 97M monthly SDK downloads
- 81k GitHub stars
- Supported by every major AI vendor: Anthropic, OpenAI, Google, Microsoft, AWS

MCP is the "USB-C of AI." When customers ask *"how do we make our search investment usable by ChatGPT Enterprise?"* — Coveo's answer is MCP.

## What the Coveo Hosted MCP Server exposes

Exactly **four MCP tools** (no resources, no prompts). Each maps to one Coveo API:

| MCP tool | Backed by | What it does | When the LLM picks it |
|---|---|---|---|
| **`search`** | Coveo Search API | Full-text ranked retrieval — "the broad survey." Returns multiple matching documents with metadata. | User asks *"what Pokémon are X"* or wants a list. |
| **`fetch`** | Coveo Search API (dataStream) | Precision retrieval of one full document by unique ID — "the scalpel." Returns full HTML/markdown body. | After `search` identifies a single doc; or when the user asks for a specific document by name. |
| **`get_passages`** | Coveo Passage Retrieval API | Verbatim semantically-ranked passages. Returns relevant chunks, not whole docs. | User wants a quoted source or to verify a factual claim. |
| **`answer`** | Coveo RGA (Relevance Generative Answering) | LLM-synthesized answer grounded in retrieved chunks, with citations. Requires answer-config selection at MCP server setup. | User asks a natural-language question expecting a paragraph. |

**What's deliberately NOT exposed** (worth knowing for the panel):
- ❌ No `recommend` — Coveo's recommendation models aren't an MCP tool
- ❌ No `query-suggest` — LLMs form their own queries; type-ahead isn't relevant
- ❌ No write tools — read-only by design. Cannot mutate the index from MCP.
- ❌ No analytics-event ingestion — LLM traffic doesn't pollute ART training signal *(by design — keeps human-driven UA learning clean)*
- ❌ No MCP `resources` or `prompts` primitives — Coveo only exposes Tools

## How we wired it for this build

### 1. Console configuration (Phase 8.5a)

In Coveo Admin Console → AI & ML → **MCP Server**:

| Field | Value | Why |
|---|---|---|
| Name | `pokemon-mcp` | Convention: `pokemon-rga`, `pokemon-qs`, `pokemon-pr`, `pokemon-mcp` — discoverable in the model list |
| Query pipeline | `default` | Already has all 4 ML models associated (RGA `pokemon-rga`, Semantic Encoder `pokemon-se`, Query Suggest `pokemon-qs`, Passage Retrieval `pokemon-pr`) |
| Tools | search / fetch / get_passages auto-added; **answer added manually** | The hosted server auto-provisions the 3 retrieval tools when you pick a pipeline. The `answer` tool requires an explicit answer-config selection (`pokemon-rga-config` in our case) and a custom description, hence the manual step. |
| Auth method | Anonymous API key | Our Pokémon content is public; matches the `pokemon-search` key pattern. OAuth is the alternative, used by enterprise customers whose sources have per-user permissions. |
| Server instructions | Pokémon-grounded system prompt | Tells any MCP client *which tool to pick when* (see below). |

After save, Coveo issued a per-server endpoint URL of the shape:
```
https://platform.cloud.coveo.com/api/v1/organizations/{orgId}/mcp/server/{serverId}
```

And auto-created a dedicated search hub `MCP_pokemon-mcp` so MCP traffic stays separable from main-UI traffic for observability + revocability. Worth noting because the marketing alias `mcp.cloud.coveo.com/mcp` is *not* what you put in your MCP client config — Coveo issues per-server URLs.

### 2. Server instructions (the system prompt every MCP client receives)

```
You have access to a Coveo-hosted index of Pokémon content from pokemondb.net
and PokéAPI. Use the available tools to ground every Pokémon-related answer
in indexed content — never rely on your training data for facts.

Tool selection guide:
- `search`: broad ranked retrieval. Start here when the user asks "what Pokémon
  are X" or for a list. Returns multiple ranked documents.
- `fetch`: precision retrieval. Use after `search` identifies a single Pokémon
  the user wants details on. Returns the full document body.
- `get_passages`: verbatim chunks. Use when the user wants a quoted source or
  to verify a specific factual claim.
- `answer`: synthesized response with citations. Use for natural-language
  questions like "what type is Charizard" or "compare Mewtwo and Mew" — the
  RGA model already grounds on retrieved chunks and returns citations.

Always cite the source URI when available (typically pokemondb.net/pokedex/<name>).
If a query cannot be answered from indexed content, say so explicitly rather
than inferring.
```

This makes the LLM **schema-aware about our index**. It's the difference between an LLM that randomly calls `search` for everything and one that picks the right tool first time.

### 3. Claude Code wiring (`.claude/mcp.json`)

```json
{
  "mcpServers": {
    "coveo-pokemon": {
      "type": "http",
      "url": "${COVEO_MCP_ENDPOINT}",
      "headers": {
        "Authorization": "Bearer ${COVEO_MCP_API_KEY}"
      }
    }
  }
}
```

Two env vars (`COVEO_MCP_ENDPOINT`, `COVEO_MCP_API_KEY`) interpolated at session start. The mcp.json file itself is committed; the secrets live in `.env` (gitignored). Launch Claude Code with:

```bash
set -a; source .env; set +a
claude --setting-sources project --strict-mcp-config --mcp-config .claude/mcp.json
```

The three flags keep the session project-scoped — only this repo's MCP servers, no global Carta MCP servers (per `~/.claude/rules/security.md`).

## What we observed in testing

Four test queries, four behaviors worth flagging:

### Test 1 — natural-language question
**Prompt**: *"What type is Charizard?"*
**Tool picked**: `answer`
**Result**: Charizard is a Fire / Flying type Pokémon, cited to `pokemondb.net/pokedex/charizard`.

Behavior worth flagging: the LLM read the server instructions and picked `answer` (not `search`) for a natural-language question. **Tool selection works.**

### Test 2 — ranked list with self-diagnosed limitation
**Prompt**: *"Search Coveo for fire-type Pokémon from Generation 1"*
**Tool picked**: `search`
**Result**: Top results returned, with the LLM **flagging that "generation 1" was treated as a keyword, not a structured filter** — so off-target results (Heatran, Gouging Fire, Typhlosion) leaked in. It filtered them out client-side and *proposed* refining via `advancedQuery` with `@pokemon_type==Fire AND @generation=="Generation 1"`.

Behavior worth flagging: **the LLM caught its own query strategy's blind spot and suggested a better one.** That's the transparency-by-design narrative customers want — not a black-box agent, an agent that explains where it's weak.

### Test 3 — verbatim passages
**Prompt**: *"Get the top 3 passages from Coveo about Mewtwo's psychic abilities"*
**Tool picked**: `get_passages`
**Result**: 3 passages with relevance scores (0.20 / 0.18 / 0.17), all from the same Mewtwo doc — Coveo's PR algorithm chunked one page into ranked snippets rather than surfacing 3 different documents.

Behavior worth flagging: the LLM **explained that all 3 chunks came from one document** (transparency again) and offered to consolidate via `answer` for a synthesized response. Same agent-self-awareness pattern as Test 2.

### Test 4 — multi-tool chaining (the panel moment)
**Prompt**: *"Fetch the full Coveo document for Bulbasaur"*
**Tool picked**: `search` → then `fetch` autonomously
**Result**: Full Bulbasaur document including base stats, type defenses, abilities, evolution chain, and **all indexed metadata fields** (`pokemon_name`, `pokemon_type`, `generation`, `dex_number`, etc.).

Behavior worth flagging: the LLM **recognized that `fetch` requires a document ID, so it first called `search` to discover the ID, then chained the `fetch` call**. Then in its response it noticed `@pokemon_type` and `@generation` are structured indexed fields, and **referred back to the Test 2 query**, proposing a refined `advancedQuery` to do a properly-filtered Gen-1 fire list.

That last detail is the panel moment. Within four queries, the agent:
1. Learned the index's tool surface
2. Discovered its schema (via fetch's response metadata)
3. Identified a query-strategy improvement for an earlier turn
4. Proposed it back to the user

**That's exactly the agentic-composition narrative Coveo's MCP positioning markets.** And it happened in real time, against our org, with zero additional code.

## Architecture

```
                       ┌──────────────────────────┐
                       │  MCP-compatible clients  │
                       │  - Claude Code           │
                       │  - Claude Desktop        │
                       │  - ChatGPT Enterprise    │
                       │  - Cursor / Zed / ...    │
                       └────────────┬─────────────┘
                                    │ MCP protocol (HTTP + Bearer auth)
                                    │ Authorization: Bearer ${COVEO_MCP_API_KEY}
                                    ▼
            ┌───────────────────────────────────────────────────┐
            │  Coveo Hosted MCP Server                          │
            │  https://platform.cloud.coveo.com/api/v1/         │
            │  organizations/{orgId}/mcp/server/{serverId}      │
            │                                                   │
            │  ┌─────────┬─────────┬───────────────┬─────────┐  │
            │  │ search  │  fetch  │ get_passages  │ answer  │  │
            │  └────┬────┴────┬────┴──────┬────────┴────┬────┘  │
            └───────┼─────────┼───────────┼─────────────┼───────┘
                    ▼         ▼           ▼             ▼
              Search API  Search API   Passage      RGA Answer
              (ranked)    (by ID)      Retrieval    API
                                       API
                          │  Same Coveo org, same pipeline,
                          │  same 1,353-doc index, same ML models
                          ▼
            ┌──────────────────────────────────────────────────┐
            │  Coveo Cloud Org (benichou)                      │
            │  - Pipeline: default                             │
            │  - Models: pokemon-rga, pokemon-pr,              │
            │            pokemon-se, pokemon-qs                │
            │  - Search hub for MCP: MCP_pokemon-mcp           │
            │    (auto-created, separable from main UI hub)    │
            └──────────────────────────────────────────────────┘
```

## What this unlocks (Topic 1 + Topic 2 framing)

### Topic 1 — technical deep dive

*"Our build ships three retrieval surfaces — a list-view (Atomic) at `/`, a detail-view (Headless + React) at `/pokemon.html`, and an agent-view via the Coveo MCP Server at `coveo-pokemon` in any MCP-compatible client. All three hit the same Coveo org, same pipeline, same ML models, same index. Three UIs, one retrieval brain. Picking the right Coveo client per surface — Atomic for list UX, Headless+React for detail UX, MCP for agent UX — is the production deployment pattern."*

### Topic 2 — customer pitch

*"Most enterprises building AI today face two integration problems. First: per-LLM connectors (your CRM needs one for ChatGPT, another for Claude, another for Salesforce Einstein). Second: per-content-source connectors (your AI agents need to read SharePoint, Confluence, Salesforce, internal wikis). Coveo's MCP Server solves both. Coveo already aggregates your content; MCP exposes the aggregated retrieval surface to any LLM. Your Coveo investment is now your AI-agent investment — zero new integrations, full permission inheritance, full ART relevance, full audit trail.* **Live demo**: *here's our Pokémon Coveo org answering natural-language questions from Claude Code through MCP. Same retrieval, same citations, same security posture — different UI."*

### Named Coveo customers using MCP

Coveo's marketing materials reference enterprise customers running on the Hosted MCP Server. The integration is GA, queries count toward existing Coveo consumption-based licensing (no new SKU), and the same auth mechanisms (OAuth, Anonymous API key) the Search API uses transfer directly.

## Security boundaries

- **MCP traffic is observable** — the auto-created `MCP_pokemon-mcp` search hub means every MCP query lands in a distinct hub bucket. Filter on it in Grafana to see only agent-driven traffic.
- **MCP queries count toward Coveo billing** — same consumption model as the Search/Answer/PR APIs, no separate quota.
- **No write surface** — MCP is read-only. An LLM agent cannot mutate our index, even if compromised.
- **Anonymous API key scope** — our MCP key is auto-scoped to the `MCP_pokemon-mcp` hub; can't query other hubs or admin endpoints.
- **Audit** — each MCP request is logged in Coveo's normal request log. The endpoint URL embeds the server UUID, so tracing is straightforward.

## Roadmap improvements (not built, panel material)

| Idea | Cost | Why we didn't build |
|---|---|---|
| **Observability extension** | ~1h | Add an MCP fire-rate panel to the Grafana dashboard, filtering on `searchHub: MCP_pokemon-mcp`. Mirrors how Phase 6E tracks per-feature behavior. |
| **OAuth flow for permissioned sources** | ~2h | Our Pokémon content is public so Anonymous API key suffices. Enterprise customers with permissioned sources would configure OAuth instead. Documented in Coveo's official Hosted MCP Server runbook. |
| **MCP traffic separately ART-trained** | not customer-doable | Coveo's ART model learns from human-driven UA signal, so MCP traffic naturally doesn't contaminate it. If a customer wanted MCP-specific relevance tuning, that'd be a Coveo-side feature request. |
| **Embed MCP integration in atomic-search/** | ~1h | A separate page (`/agent.html`) showing the same Coveo index queried via MCP from a browser, for visual parity with the Atomic list and Headless detail surfaces. Demo-friendly; not necessary. |

## Operational artifacts

| Artifact | What it does |
|---|---|
| **`config/mcp/pokemon-mcp.yaml`** ⭐ | **Source-of-truth** for the MCP server configuration — name, pipeline, tools, auth methods, server instructions (verbatim), history. Edit this YAML first, then mirror the change into the Console. See `config/mcp/README.md` for the workflow. |
| **Coveo Console: AI & ML → MCP Server** | Where the live configuration is applied. As of 2026-06-03 Coveo doesn't publish an admin REST API, so the YAML → Console flow is manual paste. |
| **`scripts/mcp/discover_api.sh`** | Read-only diagnostic that probes for a Coveo admin REST API. All 8 candidate paths returned 404 on 2026-06-03 — re-run periodically to detect when the API surfaces, at which point we can replace the manual paste with `scripts/mcp/apply_mcp_server.sh`. |
| **`.claude/mcp.json`** (committed) | Declares the `coveo-pokemon` MCP server for Claude Code with env-var-substituted endpoint + Bearer auth. |
| **`.env`** (gitignored) | Holds `COVEO_MCP_ENDPOINT` + `COVEO_MCP_API_KEY` actual values. |
| **`.env.example`** (committed) | Documents the new env vars with explanatory comments. |
| **`/pokemon-mcp` Claude Code skill** | Demo driver — runs curated test queries and explains what each tool is doing. See `.claude/skills/pokemon-mcp/SKILL.md`. |
| **`docs/api-keys.md`** | Records the 6th API key (`pokemon-mcp`, auto-created by the MCP server). |

### Code-as-source-of-truth — where MCP fits

The repo follows a strict pattern: AI configuration is versioned in git and applied to Coveo through code, not pasted into the Console by hand. Here's where MCP sits relative to the established artifacts:

| AI artifact | Source of truth in repo | How it's applied to Coveo |
|---|---|---|
| RGA Custom Prompt | `rga-closed-loop/prompts/pokemon-rga.yaml` | `rga-closed-loop/src/apply.py` (PUT to Coveo ML Models API) |
| QS seed queries | `config/ml/default-queries.json` | `scripts/ml/seed_query_suggest.sh` (multipart PUT to `/configs/DEFAULT_QUERIES`) |
| ML model associations | `scripts/ml/associate_models.sh` | Script reads desired state, POSTs associations |
| **MCP server config** | **`config/mcp/pokemon-mcp.yaml`** | **Manual paste into Console (until Coveo publishes admin API)** |

The manual step on the MCP row isn't ideal, but the YAML is honest about it — and the apply path is already structured so swapping in `scripts/mcp/apply_mcp_server.sh` is a drop-in change the day Coveo's admin API ships.

## Files added in Phase 8.5

```
atomic-search/  (no changes — MCP runs through Console + .claude/, not the Vite project)

config/mcp/
├── pokemon-mcp.yaml                  ← SOURCE OF TRUTH (server config + history)
└── README.md                         ← versioning rationale + manual-paste workflow

scripts/mcp/
└── discover_api.sh                   ← diagnostic probe for Coveo admin API (currently no public API)

.claude/
└── mcp.json                          ← was empty; now declares coveo-pokemon

.claude/skills/
└── pokemon-mcp/
    └── SKILL.md                      ← /pokemon-mcp demo driver

docs/
└── mcp-integration.md                ← this doc

.env.example                          ← adds COVEO_MCP_ENDPOINT + COVEO_MCP_API_KEY
```

## TL;DR for the panel

- **Coveo released a Hosted MCP Server in 2026.** It exposes any Coveo org as a tool surface to any MCP-compatible LLM client.
- **Four tools**: `search`, `fetch`, `get_passages`, `answer`. No resources, no prompts. Read-only.
- **We wired it in ~1 hour** end-to-end: Console config + Claude Code MCP declaration + four-tool smoke test.
- **The four test queries showed real agentic composition**: the LLM picked the right tool per query, chained tools when needed (search → fetch), discovered the index schema, and proposed a refined query strategy for an earlier turn. Live.
- **Same Coveo org, three UI surfaces**: Atomic list (`/`), Headless+React detail (`/pokemon.html`), MCP agent (`coveo-pokemon` in any MCP client). One retrieval brain.
- **Topic 2 slide**: *"Your Coveo investment is your AI-agent investment."* — backed by a working demo, not a screenshot.
