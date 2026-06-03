# Pokémon Detail Page — Headless + React alongside Atomic

This document is the panel-shareable record of the Pokémon Detail Page — a Headless + React surface that lives in the same project as the Atomic main app, and what we learned shipping it.

> **For the panel.** Doc 2's Advanced tier asks for "modules in Coveo Headless + React" alongside the Atomic main app. Most candidates either build one *or* the other. We built both in the same Vite project, sharing the same `.env` and the same Vercel deploy. Result: clicking a Pokémon from the Atomic list jumps to a Headless+React detail page, which fires *three* separate Coveo queries (Search, Passage Retrieval, a second Search filtered by generation) — composing them into a single rich view. Same org, same pipeline, same index. **Different UX layer per surface.** That's the FDE narrative: pick the right Coveo client library for the job, don't religion-marry one.

## What it is

A separate route — `/pokemon.html?name=charizard` — rendered by a React app on top of Coveo Headless. The Atomic main page's result template uses `href-template` so each click navigates to this page with the slug in the query string.

```
Atomic main page (/)                Headless + React detail page (/pokemon.html?name=X)
─────────────────────              ─────────────────────────────────────────────────────
list view                          single-Pokémon deep dive
broad facets (Type, Gen, ...)      no facets, rich layout
RGA + Passage Retrieval panel      hero card, featured insights, related grid
Atomic web components              custom React components, full styling control
```

Both surfaces hit the same Coveo org, same pipeline (`default`), same search hub (`pokemon-search`), same five indexed fields. The detail page just composes the queries differently.

## Architecture

```
                     Atomic main page                      Headless + React detail page
                      (index.html)                              (pokemon.html)
                            │                                          │
   ┌────────────────────────┴───┐                  ┌───────────────────┴───────────────────┐
   ▼                            ▼                  ▼                                       ▼
result click                  RGA panel        Hero query        Featured passages    Related grid
href-template                 PR panel         (Headless         (direct fetch to     (second Headless
"/pokemon.html?              (one engine,      ResultList,       PR endpoint, 3       engine, filtered
  name=${raw.                  multi-query)    1 result by       candidates ranked    by @generation)
  pokemon_name}"                              slug)              by readability)
   │                                          │                  │                    │
   └──────────────────► same Coveo org, same .env, same Vercel deploy ◄────────────────┘
```

Three Coveo surfaces composed on a single page:

1. **Hero query** — `buildSearchEngine()` + `buildResultList()` to fetch one canonical document by slug.
2. **Featured insights** — direct `fetch()` POST to `<orgId>.org.coveo.com/rest/search/v3/passages/retrieve` for 3 PR candidates.
3. **Related grid** — a **second** `buildSearchEngine()` instance with a `@generation==<value>` filter, returning 6 same-generation Pokémon.

### Why two Headless engines

Each Coveo Headless engine manages one query state at a time. The hero result and the related-list are independent queries, so they get independent engines. Engines are cheap (each is just a Redux-like store + an HTTP client), and using two instances keeps state changes from one surface from invalidating the other.

### Why a direct fetch for PR (no engine)

Coveo's Headless SDK doesn't ship a Passage Retrieval controller in v3 — PR is a separate endpoint (`<orgId>.org.coveo.com/rest/search/v3/passages/retrieve`, different subdomain from the standard `platform.cloud.coveo.com/rest/search/v2`). A bare `fetch()` is less code than building an unsupported controller wrapper, and it mirrors what `atomic-search/src/passage-retrieval.js` already does for the main page's PR panel.

## Multi-entry Vite build — why one project, not two

```
atomic-search/
├── index.html              ← Atomic main entry
├── pokemon.html            ← Headless + React entry
├── vite.config.js          ← rollupOptions.input: { index, pokemon }
├── tsconfig.json
└── src/
    ├── main.js             ← Atomic bootstrap
    ├── style.css           ← main page styles
    ├── passage-retrieval.js
    ├── observability.js
    ├── api/log-query.js    ← serverless proxy (shared by both surfaces)
    └── pokemon-detail/     ← Phase 6C
        ├── main.tsx        ← React mount
        ├── App.tsx         ← three composed Coveo surfaces
        └── detail.css      ← detail-page styles
```

Trade-offs we considered:

| Option | Pros | Cons | Choice |
|---|---|---|---|
| **Multi-entry inside `atomic-search/`** | Shared `.env`, shared Vite proxy, one Vercel deploy, one build, one CI matrix | Single bundle target → React + Headless ride alongside the Atomic page even when not needed | ✅ Picked |
| Separate Vite project (`detail-page/`) | Smaller per-page bundles; full isolation | Two `.env`s, two Vercel projects, two CI checks, env-var drift risk; more moving parts to demo | Rejected |
| Next.js app router | Same project, file-system routing, server components | Heavy redesign of the existing Atomic page; SSR isn't a benefit for this demo | Rejected |

Multi-entry won on **panel-narrative simplicity**: *"one project, two pages, same secrets — pick the right Coveo SDK per page."*

## The result-link handshake

Each Atomic result card has an `<atomic-result-link>` with a template:

```html
<atomic-result-link href-template="/pokemon.html?name=${raw.pokemon_name}">
  <atomic-result-text field="pokemon_name"></atomic-result-text>
</atomic-result-link>
```

`href-template` is a simple string-interpolation feature; it doesn't transform the field value. That means Charizard → `?name=Charizard` (capitalized). The detail page passes that string verbatim to Coveo's query box (`box.updateText(slug)`), and Coveo's tokenizer matches it against the indexed `pokemon_name` field case-insensitively. The lookup is forgiving by design — a user pasting `?name=mr-mime` or `?name=Mr.%20Mime` reaches the same Pokémon.

The detail page also has a "View source page ↗" link in the Hero block that points back to the original `pokemondb.net` document via the result's `clickUri` — preserving the source-of-truth path for users who want the upstream page.

## Featured insights — PR content quality

PR returns chunks of indexed content ranked by semantic similarity. For a slug-as-query like `"what is ${slug}?"` against a pokemondb.net page, the top-ranked chunk is often one of:

| Chunk type | Renders as | Quality |
|---|---|---|
| Descriptive paragraph (lead text) | clean prose | ⭐⭐⭐ ideal |
| Pokédex data table (Catch rate, EV yield, Egg groups, Base stats) | proper `<table>` if markdown-it sees the `\|---\|---\|` separator | ⭐⭐ good |
| Moveset table fragment (PR collapsed row separators) | inline pipe-soup unless reconstructed | ⭐ ugly without help |
| TOC chrome (`[Skip to main content](#main)`, contents list) | nav noise | ⭐ irrelevant |

We solve the quality problem in three stages, all client-side:

### 1. Fetch 3 candidates, not 1

```js
maxPassages: 3
```

A single candidate is fragile — one bad chunk leaves the panel empty of value. Three gives the panel something readable to lead with, plus structured data behind progressive disclosure.

### 2. Rank by readability ("noise score")

```ts
function noiseScore(text: string): number {
  const hasRenderableTable = GFM_TABLE_SEPARATOR.test(text);
  const pipes = (text.match(/\|/g) || []).length;
  const links = (text.match(/\[[^\]]*\]\([^)]*\)/g) || []).length;
  const pipeNoise = hasRenderableTable ? 0 : pipes;
  const linkNoise = links * 3;
  return (pipeNoise + linkNoise) / Math.max(text.length, 1);
}
```

**Key insight:** pipes are only noise when there's no `|---|---|` separator row. A well-formed GFM table scores 0 for pipes (markdown-it will render it as a real `<table>`); a fragment without a separator scores high (because markdown-it can't recognize it, so the pipes render literally).

We sort the 3 candidates ascending by score and default-expand the lowest — the prose chunk almost always wins.

### 3. Reconstruct flattened tables

PR's chunker sometimes returns what *was* a table on the source page but with newline boundaries collapsed: `| a | b | c | | d | e | f | | g | h | i |` instead of three separate lines. markdown-it can't render this — but we can split on `| |` to recover the rows and synthesize the missing header + separator:

```ts
function maybeReconstructTable(text: string): string {
  if (GFM_TABLE_SEPARATOR.test(text)) return text;        // already valid
  const pipes = (text.match(/\|/g) || []).length;
  if (pipes < 8) return text;                              // not table-shaped
  const rows = text.split(/\|\s*\|/).map((r) => r.trim()).filter(Boolean);
  if (rows.length < 2) return text;
  const cols = (rows[0].match(/\|/g) || []).length - 1;
  if (cols < 2) return text;
  const headerRow = "|" + " |".repeat(cols);
  const separator = "|" + "---|".repeat(cols);
  return [headerRow, separator, ...rows].join("\n");
}
```

The empty header cells aren't pretty (PR's chunker dropped the original `<th>` labels), but the data rows render cleanly. Three lines of code that turn an unrenderable fragment into a real HTML table.

If reconstruction would produce something malformed (uneven column counts, < 2 rows), the function bails out and returns the original text — **we never make rendering worse than it was**.

### 4. Pipeline

```
PR chunk text
  → stripAnchorOnlyLinks       (drop `[Skip to main content](#main)` chrome)
  → maybeReconstructTable      (split on `| |`; synthesize header + separator)
  → markdown-it.render         (html:false, linkify:false — XSS-safe)
  → dangerouslySetInnerHTML    (rendered into a <details> card)
```

This is the exact same `markdown-it` config and `stripAnchorOnlyLinks` pre-pass as the main Atomic page's PR panel — so both surfaces behave identically. The only addition for the detail page is `maybeReconstructTable`, which is small enough to be worth duplicating across surfaces if needed.

## Related grid — same-generation Pokémon

A second Headless engine fires a search with `q = @generation==<value>` (Coveo's query syntax for field equality). We pull up to 6 results, filter out the hero itself client-side, and render them as cards linking to their own detail pages.

Why not filter by type, evolution chain, or stat similarity? Three reasons:
- **Generation is a clean grouping every Pokémon has** — types are multi-valued (Charizard is Fire AND Flying — which one defines "related"?), evolution chains are fields we'd have to enrich, base-stat similarity needs a vector.
- **Generation is the most narratively coherent** — same-era Pokémon, same game release, same canonical fan groupings.
- **It's a cheap and obvious second engine demo** — panel-defining moment: *"here we fire a totally separate Coveo query, on a totally separate Headless engine instance, filtered by a single indexed field, and it lights up the grid in <100ms."*

## What the panel demo says about Coveo

This page is a one-screen recap of the FDE story:

| Surface | What Coveo gives us | What we built on top |
|---|---|---|
| Hero | Search API | Single-result lookup by slug, with image + types + dex + gen |
| Featured insights | Passage Retrieval API | 3 candidates → noise-score ranking → table reconstruction → markdown-it |
| Related grid | Search API (second engine) | Field-filtered query, exclude hero, link to sibling detail pages |
| Source link | Result `clickUri` | Direct nav to upstream pokemondb.net document |

Three Coveo round-trips on initial page load, in parallel, against the same org. **List-view UX (Atomic) and detail-view UX (Headless+React) are two different optimizations of the same retrieval layer.** That's the production-grade Coveo deployment narrative.

## Connection to Topic 2 (customer pitch)

The choice of *which Coveo client library to use where* is exactly the conversation an FDE walks an enterprise customer through:

- *"For your knowledge-base list page, ship Atomic — five components, instant facets, zero JavaScript."*
- *"For your case-detail page where the agent needs a contextual answer + related cases + verifiable source passages, ship Headless on your existing React stack — full styling control, multiple parallel queries, real component composition."*

Same Coveo org. Same query pipeline. Same RGA / PR / ART models. Different UI surfaces optimized for different jobs. **Pick the right client library per surface.** That's the slide the customer sees in Topic 2 — and we have working code for both halves of the slide in this repo.

## Files

```
atomic-search/
├── pokemon.html                            ← new HTML entry
├── tsconfig.json                           ← minimal TS config for the .tsx files
├── vite.config.js                          ← multi-entry rollupOptions.input
└── src/
    ├── main.js (line ~204 in index.html)   ← `href-template` rewrite on the result link
    └── pokemon-detail/
        ├── main.tsx                        ← React mount, StrictMode
        ├── App.tsx                         ← three composed Coveo surfaces
        └── detail.css                      ← detail-page styles
```

## Future improvements (not built, panel material)

| Idea | Cost | Why we didn't build |
|---|---|---|
| **Server-side pre-rendering of the hero** | ~3-4h | Vercel serverless function calling Coveo + injecting hero data into the HTML response. Improves LCP. Not needed for a demo with sub-300ms client queries. |
| **Generation-aware sort in related grid** | ~30m | Sort related cards by dex number ascending. Currently uses Coveo's default ranking (semantic relevance to an empty query). |
| **A type-similarity related strip** | ~1h | Second related-row filtered by `@pokemon_type` instead of generation. More dimensions of "related" = richer detail page. |
| **Evolution-chain navigation** | ~2h | Requires enriching the index with an `evolution_chain` field via the Push source (Phase 4). Then a small visual treatment of the chain at the top of the detail page. |
| **Recommendations via Coveo's recommendation model** | ~3h | If we trained a recommendation model on user clicks, we could surface *"people who looked at Charizard also looked at..."* — but that needs real usage data we don't have. |
