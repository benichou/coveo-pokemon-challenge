---
marp: true
theme: pokedex
paginate: true
footer: "[github.com/benichou/coveo-pokemon-challenge](https://github.com/benichou/coveo-pokemon-challenge)"
---

<!-- _class: cover -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Pokédex Search

## A Coveo FDE technical challenge

**Franck Benichou** · Forward Deployed Engineer candidate

<div class="links">
  <div>🔍 Live app · <a href="https://pokemon-search-one-chi.vercel.app">pokemon-search-one-chi.vercel.app</a></div>
  <div>💻 GitHub · <a href="https://github.com/benichou/coveo-pokemon-challenge">github.com/benichou/coveo-pokemon-challenge</a></div>
  <div>🔬 RGA performance monitoring · <a href="https://pokemon-rga-dashboard.vercel.app">pokemon-rga-dashboard.vercel.app</a></div>
  <div>📊 Query observability · <a href="https://charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452">grafana public dashboard</a></div>
</div>

<!--
Speaker notes (hidden in slide, visible in presenter mode):

"Hi — I'm Franck. Over the next ~10 minutes I'll walk through the Pokémon
Challenge build. We'll do the live demo early — right after the architecture
diagram — and then drill into the choices behind it. Q&A at the end."

Key message: the URLs are live and you can follow along on your phone.
-->

---

# What I built

<p class="tagline">
A Pokémon-themed search experience on Coveo Cloud —<br>
<strong>three user-facing surfaces</strong> powered by <strong>one Coveo brain</strong>.
</p>

<div class="three-up">
  <a href="https://pokemon-search-one-chi.vercel.app" target="_blank" rel="noreferrer">
    <img src="images/atomic-main.png" alt="Atomic main page">
    <p class="three-up-label">Atomic main page</p>
  </a>
  <a href="https://pokemon-search-one-chi.vercel.app/pokemon.html?name=charizard" target="_blank" rel="noreferrer">
    <img src="images/detail-page.png" alt="Headless + React detail page">
    <p class="three-up-label">Pokémon Detail Page</p>
  </a>
  <a href="https://www.coveo.com/en/developers/mcp-server" target="_blank" rel="noreferrer">
    <img src="images/mcp-claude-code.png" alt="Coveo MCP Server">
    <p class="three-up-label">Coveo MCP Server</p>
  </a>
</div>

<!--
Speaker notes:

"Doc 2's brief is essentially: index pokemondb.net into a Coveo org and ship
a custom search experience on top. That's the deliverable."

"But the challenge also asks for Advanced and Bonus tier work. I went full
ambition — every advanced item, the bonus, plus three things Doc 2 didn't
ask for. I'll get to those."

"Single screenshot recap before we get into the *how*."

Key message: scope = full ambition, not the minimum that passes.
-->

---

<!-- _class: architecture -->

# Architecture · one Coveo org, three UI surfaces, two loops

<div class="arch">

<div class="arch-row">
  <div class="arch-zone zone-data">
    <p class="arch-zone-title">📚 Data sources</p>
    <div class="arch-zone-body">
      <div class="arch-line">pokemondb.net <small>sitemap · 12,915 URLs · public site</small></div>
      <div class="arch-line">PokéAPI <small>per-form variants · Mega / Hisuian / Galarian</small></div>
    </div>
  </div>
  <div class="arch-arrow">→</div>
  <div class="arch-zone zone-ingest">
    <p class="arch-zone-title">🛠️ Ingestion · 95% as-code</p>
    <div class="arch-zone-body">
      <div class="arch-line">Source A · Coveo Sitemap source <small>1,028 docs · versioned scraping config</small></div>
      <div class="arch-line">Source B · Python Push pipeline <small>+325 form variants · enrichment via PokéAPI</small></div>
    </div>
  </div>
  <div class="arch-arrow">→</div>
  <div class="arch-zone zone-coveo">
    <p class="arch-zone-title">🧠 Coveo Cloud Org · benichou</p>
    <div class="arch-zone-body">
      <div class="arch-line">Unified index <small>1,353 docs · 5 indexed fields · least-privilege API keys</small></div>
      <div class="arch-line"><strong>4 ML models on default pipeline</strong><br><small>RGA · Semantic Encoder · Query Suggest · Passage Retrieval</small></div>
    </div>
  </div>
</div>

<div class="arch-down">↓</div>

<div class="arch-row arch-row-surfaces">
  <div class="arch-zone zone-surfaces" style="flex: 1;">
    <p class="arch-zone-title">🎯 Three UI surfaces · one retrieval brain</p>
    <div class="arch-three-surfaces">
      <div class="arch-surface">
        <strong>Atomic main page</strong>
        <code>/</code>
        <small>list view · RGA panel · PR panel · Query Suggest type-ahead · GBC-themed UI</small>
      </div>
      <div class="arch-surface">
        <strong>Pokémon Detail Page</strong>
        <code>/pokemon.html?name=X</code>
        <small>Headless + React · three parallel Coveo queries (hero · passages · related)</small>
      </div>
      <div class="arch-surface">
        <strong>Coveo MCP Server</strong>
        <code>coveo-pokemon</code>
        <small>4 MCP tools (search · fetch · get_passages · answer) addressable from any MCP client</small>
      </div>
    </div>
  </div>
</div>

<div class="arch-row arch-row-compact">
  <div class="arch-zone zone-obs">
    <p class="arch-zone-title">📊 Query observability loop</p>
    <div class="arch-zone-body">
      <div class="arch-line">Atomic → Vercel proxy → Grafana Cloud Loki → Public dashboard</div>
      <p class="arch-loop-label">↑ log every search · fire-and-forget · token stays server-side</p>
    </div>
  </div>
  <div class="arch-zone zone-quality">
    <p class="arch-zone-title">🔬 Continuous AI quality (closed loop)</p>
    <div class="arch-zone-body">
      <div class="arch-line">Daily eval → analyzer (5-run window) → 5 guardrails → apply via Coveo ML Models API ↺</div>
      <p class="arch-loop-label">↑ closed loop · auto-rollback on next-day drop &gt; 5pts · audit trail per run</p>
    </div>
  </div>
</div>

</div>

<!--
Speaker notes:

"Four flows worth tracing on this diagram."

(point at top-down arrow) "INGESTION: dual-source. pokemondb.net's sitemap
into Source A. PokéAPI per-form variants pushed into Source B."

(point at three UI nodes) "THREE SURFACES, ONE BRAIN: Atomic list page at
the root, Headless+React detail page at /pokemon.html, and Coveo's hosted
MCP server — addressable from any MCP client like Claude Code or ChatGPT
Enterprise."

(point at right-side closed-loop) "CLOSED LOOP: daily eval measures RGA
quality, daily analyzer proposes prompt refinements, guardrails decide
whether to apply. The dotted arrow back to RGA is the loop closing."

(point at left-side observability) "PARALLEL OBSERVABILITY: every user
search fires a fire-and-forget log to Grafana Cloud Loki via a Vercel
proxy — Loki write token stays server-side."

(closing transition) "That's the architecture. Now let me show you it
actually running, then we'll drill into the choices behind each piece."

Key message: one Coveo org, six logical zones, two narrative loops
(quality + observability).
-->

---

<!-- _class: demo -->

# Live demo · switching to the browser

<div class="demo-grid">
  <a class="demo-main" href="https://pokemon-search-one-chi.vercel.app" target="_blank" rel="noreferrer">
    <img src="images/atomic-main.png" alt="Atomic main page">
    <p class="demo-label">🔍 Atomic main page · <code>pokemon-search-one-chi.vercel.app</code></p>
  </a>
  <a class="demo-ui-1" href="https://pokemon-search-one-chi.vercel.app/pokemon.html?name=charizard" target="_blank" rel="noreferrer">
    <img src="images/detail-page.png" alt="Pokémon Detail Page (Headless + React)">
    <p class="demo-label">🃏 Pokémon Detail Page <small>(Headless + React)</small></p>
  </a>
  <a class="demo-ui-2" href="https://www.coveo.com/en/developers/mcp-server" target="_blank" rel="noreferrer">
    <img src="images/mcp-claude-code.png" alt="Coveo MCP Server">
    <p class="demo-label">🤖 Coveo MCP Server <small>(coveo-pokemon)</small></p>
  </a>
  <a class="demo-ops-1" href="https://pokemon-rga-dashboard.vercel.app" target="_blank" rel="noreferrer">
    <img src="images/rga-dashboard.png" alt="RGA performance monitoring dashboard">
    <p class="demo-label">🔬 RGA performance monitoring</p>
  </a>
  <a class="demo-ops-2" href="https://charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452" target="_blank" rel="noreferrer">
    <img src="images/grafana-dashboard.png" alt="Grafana query observability dashboard">
    <p class="demo-label">📊 Query observability</p>
  </a>
</div>

<p class="demo-footnote">Follow along — full source at <strong>github.com/benichou/coveo-pokemon-challenge</strong></p>

<!--
Speaker notes — demo script (3-5 min, do NOT read aloud, drive the browser):

OPENER (delivered as you switch to the browser):
"You've seen the architecture. Let me show you it actually running. We'll
touch all four flows from the diagram in ~4 minutes."

(0:00) Open https://pokemon-search-one-chi.vercel.app
        Refresh once or twice to roll the theme. Call out:
        "5 biomes — Grassland, Beach, Cave, Volcano, Ice — random per load.
         The whole topbar is CSS-only Pokémon-themed."

(0:30) Type "charizard" in the search box. Point at:
        • RGA answer streaming in
        • Citation back to pokemondb
        • Passage Retrieval panel below RGA
       Say: "Same retrieval primitive an enterprise customer would use to
             ground their own LLM."

(1:00) Click a Type facet (e.g., Fire). Then click the Source facet to
       reveal PokemonDb + PokeAPI items mixing together. Say:
       "Both ingestion sources unified — 1,353 docs in one ranked list."

(1:30) Click the Charizard result. Lands on /pokemon.html?name=Charizard.
       Point at:
        • Hero card (image, type badges, dex #)
        • Featured Insights card (Passage Retrieval)
        • Related grid (second Headless engine, same generation)
       Say: "Three Coveo queries on this page, fired in parallel."

(2:30) Open a separate terminal/tab with Claude Code (pre-launched with
       MCP wired). Type "/pokemon-mcp demo".
       Watch the four MCP tools fire (search, fetch, get_passages, answer).
       Say: "Same Coveo org, now answerable from Claude Code through MCP.
             Zero additional code per client."

(4:00) Open https://pokemon-rga-dashboard.vercel.app
       Point at:
        • Time-series chart (accuracy / precision / hard-recall)
        • Chart markers showing prompt-change applies
        • Click a marker to scroll to the diff view
       Say: "Every day at 06:00 UTC the eval runs. Chart markers are the
             closed loop applying new prompts. This is what 'production AI'
             actually means."

(4:30) Optional if time permits:
       Open the Grafana public dashboard URL from the cover slide. Show
       1-2 panels (top queries, RGA fire rate). Say:
       "Same query-observability story — every user search logged here.
        Public dashboard, deployed as code."

CLOSING (back to slides):
"OK — that's the build running. Now let me walk you through the choices
behind each piece, starting with how we ingest content."

Demo tips:
• Pre-load ALL tabs before the panel starts. Don't fumble.
• Have a 90-second screen-recording as fallback if Wi-Fi dies.
• If the MCP demo flakes, fall back to a screenshot of yesterday's run.

Key message: this is a working app, not a slide deck about an app.
-->
