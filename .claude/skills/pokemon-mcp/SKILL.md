---
name: pokemon-mcp
description: Demonstrate or explain the Coveo Hosted MCP Server integration (Phase 8.5). Args control mode — 'info' to explain the integration without API calls, 'demo' to run a 4-query panel demo through the four MCP tools (search / fetch / get_passages / answer), 'tools' to list the available MCP tools and their roles, 'compare <query>' to call the MCP server and explain what the live Vercel UI would show for the same input. Use this when the user asks to "demo MCP", "show the agent surface", "compare MCP to the live UI", or "explain how Coveo MCP works."
---

# Pokémon MCP Demo — Claude Code Skill

This skill is the panel-demo driver for Phase 8.5 (Coveo Hosted MCP Server integration). It explains the integration, runs a curated 4-query demo through the four MCP tools, and contrasts MCP-served answers with the live Vercel UI's responses.

## When this skill applies

Invoke this skill when the user asks any of:
- "Demo the MCP integration" / "show the agent surface" / "panel demo MCP"
- "What does the Coveo MCP server expose?" / "explain how MCP works here"
- "Compare MCP to our live UI for query X"
- "List the MCP tools"

The skill assumes the Coveo MCP server is wired into Claude Code via `.claude/mcp.json` (Phase 8.5a; see `docs/mcp-integration.md`). If the `coveo-pokemon` MCP server isn't connected, the skill must surface that and point the user at the wiring docs.

## Pre-check (always, before any mode)

Before running any mode, verify the MCP server is reachable:

1. Confirm `.claude/mcp.json` declares `coveo-pokemon` with `${COVEO_MCP_ENDPOINT}` + `${COVEO_MCP_API_KEY}` env-var refs.
2. Confirm both env vars are set (via `echo $COVEO_MCP_API_KEY | head -c 8` — print only the prefix, never the full key).
3. Mentally check: did Claude Code load the MCP server? (The `mcp__coveo-pokemon__*` tools should appear in the tool catalog. If not, ask the user to restart Claude Code with `set -a; source .env; set +a; claude --setting-sources project --strict-mcp-config --mcp-config .claude/mcp.json`.)

If the server isn't connected, STOP and point the user at `docs/mcp-integration.md` "Claude Code wiring" section.

## Arguments

| User-provided args | Mode | What to do |
|---|---|---|
| `info` or (none) | **Info** | Explain the integration without calling any MCP tool. Best for "tell me about the MCP integration" without burning API quota. |
| `tools` | **List** | Print a table of the four tools (`search`, `fetch`, `get_passages`, `answer`) with what each does and when to pick each. No API calls. |
| `demo` | **Demo** | Run the 4-query panel demo against the live MCP server. Print each tool name as it's called and a brief commentary on what the tool returned. **This is the mode for the live panel.** |
| `compare <query>` | **Compare** | Call the MCP server for `<query>`, then describe what the live Vercel UI at https://pokemon-search-one-chi.vercel.app would surface for the same input. Contrast surface types (Atomic list vs MCP agent). |

## Mode: info

Print this verbatim (no MCP calls). Tailor only the dynamic bits (endpoint URL, last-tested date).

```
## Coveo Hosted MCP Server — pokemon-mcp

The Coveo MCP Server is Coveo's productized 2026 release that exposes a
Coveo org as a set of MCP tools to any MCP-compatible LLM client (Claude
Code, Claude Desktop, ChatGPT Enterprise, Cursor, ...).

### What this build's MCP server exposes

Four tools:
1. `search`        — Coveo Search API (ranked retrieval)
2. `fetch`         — Coveo Search API by document ID (full content)
3. `get_passages`  — Coveo Passage Retrieval API (verbatim chunks)
4. `answer`        — Coveo RGA (synthesized answer + citations)

No MCP resources, no MCP prompts, no write tools. Read-only by design.

### Auth

Anonymous API key, scoped to the auto-created `MCP_pokemon-mcp` search
hub. Bearer token in the Authorization header. Key is in .env as
COVEO_MCP_API_KEY; never committed.

### Endpoint shape

https://platform.cloud.coveo.com/api/v1/organizations/{orgId}/mcp/server/{serverId}

Coveo issues a unique per-server URL. The marketing alias
`mcp.cloud.coveo.com/mcp` is NOT the URL you put in your MCP client.

### Configured in this repo at

- Console: Admin → AI & ML → MCP Server → pokemon-mcp
- Claude Code: .claude/mcp.json (env-var-substituted url + Authorization)
- Full architecture: docs/mcp-integration.md
- API key recipes: docs/api-keys.md (Key 6)

### Try it

  /pokemon-mcp demo            ← run the 4-query panel demo
  /pokemon-mcp tools           ← list the four tools
  /pokemon-mcp compare "what type is charizard"   ← MCP vs live UI
```

## Mode: tools

Print this table verbatim. No MCP calls.

```
| Tool          | Backed by              | Inputs                                  | When the LLM picks it                                       |
|---------------|------------------------|-----------------------------------------|-------------------------------------------------------------|
| search        | Coveo Search API       | query, numberOfResults (default 5)      | User asks for a list, ranked discovery                      |
| fetch         | Coveo Search API by ID | document id                             | User wants the full content of one doc                      |
| get_passages  | Coveo PR API           | query, numberOfPassages (default 5)     | User wants verbatim source text / fact verification         |
| answer        | Coveo RGA              | query                                   | User asks a NL question expecting a grounded paragraph      |
```

Then add this commentary:

```
Tool-selection nuance: the MCP server's system prompt (Server implementation
tab in the Console) tells the LLM client *when* to pick each tool. Without
that prompt, an LLM tends to default to `search` for everything; with it,
the LLM picks `answer` for NL questions, `search` for list-y discovery,
`get_passages` for verification, and `fetch` after `search` identifies a
specific doc. See the full system prompt in docs/mcp-integration.md.
```

## Mode: demo (the panel demo)

Run these four queries against the live MCP server, **in order**, narrating what each one demonstrates. Print the tool name being called before each one, then after the tool returns, write a one-paragraph commentary on what just happened.

The four canonical demo queries (in order):

### Query 1 — natural-language → `answer` tool

**User prompt to Claude (via the LLM, which will then call the MCP tool)**:
> *"Use the Coveo MCP server: what type is Charizard?"*

**What the LLM should do**: pick `answer` (because the server's system prompt says so for NL questions). The tool returns RGA's grounded paragraph with a citation.

**Your narration after the call**:
```
The LLM picked the `answer` tool because the server instructions tell it
to prefer `answer` for natural-language questions. RGA grounded on the
indexed Charizard doc and returned a synthesized paragraph with a citation
to pokemondb.net/pokedex/charizard. This is the same content the Vercel
UI's <atomic-generated-answer> panel surfaces — same backend, different
surface.
```

### Query 2 — list query → `search` tool

**User prompt**:
> *"Use the Coveo MCP server: search for fire-type Pokémon from Generation 1."*

**What the LLM should do**: pick `search`, return ranked results. Expect the LLM to also flag that "Generation 1" is being treated as a text search rather than a structured filter — that's a transparency moment.

**Your narration after the call**:
```
The LLM picked `search` for the list-y discovery query. Notice what it
flagged about its own results: the index returns 800+ "fire" matches
ranked by relevance, and the LLM noted that "Generation 1" was treated
as keyword text rather than as a structured filter on the @generation
indexed field. The LLM then offered to refine with an advancedQuery
expression. That's transparency-by-design — the agent explained where
its query strategy was weak, instead of pretending the results were
perfect. Customers ask for that in production AI; here it ships by
default.
```

### Query 3 — verbatim passages → `get_passages` tool

**User prompt**:
> *"Use the Coveo MCP server: get the top 3 passages about Mewtwo's psychic abilities."*

**What the LLM should do**: pick `get_passages`, return 3 ranked passages with relevance scores.

**Your narration after the call**:
```
The LLM picked `get_passages` because the user asked for source text
verification rather than a synthesized answer. The returned passages
include relevance scores — Coveo's PR API ranks by semantic similarity
to the query. Often all 3 passages come from the same source page,
because PR chunks long documents into multiple ranked snippets. The LLM
should flag this (multiple chunks, one source) and offer `answer` as a
synthesis alternative.
```

### Query 4 — multi-tool chaining → `search` → `fetch`

**User prompt**:
> *"Use the Coveo MCP server: fetch the full document for Bulbasaur."*

**What the LLM should do**: realize `fetch` requires a document ID, call `search` first to discover it, then chain into `fetch`. This is the agentic-composition moment.

**Your narration after the call**:
```
This is the panel moment. The LLM noticed that `fetch` requires a
document ID and `search` is the way to discover one — so it chained
`search` → `fetch` autonomously. Two tool calls, one user request. In
the fetch response the LLM also exposes the indexed metadata fields
(pokemon_name, pokemon_type, generation, dex_number, etc.), which lets
it reason about the index schema mid-conversation. If we'd ended Query
2 with an open advancedQuery question, the LLM could come back here and
propose a refined filtered search using the schema it just learned.

This is what "agentic composition" means in Coveo's MCP marketing — and
it works out of the box, against this org, with zero additional code on
our side.
```

After all four queries, print a closing recap:

```
## Demo recap

Four queries → four tool patterns:
  1. NL question     → answer
  2. List discovery  → search (+ self-flagged limitation)
  3. Source quotes   → get_passages (+ transparency about chunks)
  4. Full document   → search → fetch (multi-tool composition)

Same Coveo org, same pipeline, same models, same index that powers our
Vercel UI. New surface: any MCP client. Zero code added on top of the
existing build.
```

## Mode: compare <query>

1. Call the appropriate MCP tool for `<query>` (let the LLM pick based on server instructions).
2. Print the MCP response.
3. Then describe what the live Vercel UI at https://pokemon-search-one-chi.vercel.app would surface for the same input:
   - For NL questions: the RGA panel above the result list (same content as `answer` tool — same backend)
   - For list queries: the Atomic result list (sorted by Relevance) + the right-rail facets (type, generation)
   - For passage queries: the "Verify with source passages" PR panel below RGA (same content as `get_passages` — same backend)
   - For specific docs: clicking a result navigates to `/pokemon.html?name=<slug>` — the Headless+React detail page

Highlight: **same retrieval surface, three UIs (Atomic list / Headless+React detail / MCP agent), one Coveo brain.**

## Cost note

Each MCP query counts toward Coveo's consumption-based licensing. The 4-query demo is ~4 search-equivalent calls (Query 4 is 2 calls because of the search → fetch chain). Negligible for demos. Worth flagging if the user wants to run the demo dozens of times in a session.

## Related artifacts

- `docs/mcp-integration.md` — panel-shareable architecture doc (Topic 1 + Topic 2 framing)
- `docs/api-keys.md` — Key 6 (`pokemon-mcp`) recipe
- `.claude/mcp.json` — Claude Code wiring (env-var substitution)
- `.env.example` — `COVEO_MCP_ENDPOINT` + `COVEO_MCP_API_KEY` placeholders
- Coveo Console → AI & ML → MCP Server → pokemon-mcp — live configuration
