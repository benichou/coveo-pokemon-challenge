# atomic-search/

Local Pokemon search UI built on **Coveo Atomic** (web-components flavor) + Vite.

## What this is

The "main app" half of the FDE deliverable (Phase 5). Consumes the dual-source Coveo index we built in Phases 1–4:

- **Source A — `pokemondb-sitemap`**: 1,028 Pokemon scraped from pokemondb.net via Coveo's Sitemap source.
- **Source B — `pokemondb-push`**: ~325 PokéAPI form variants (Mega, Hisuian, Galarian, Gigantamax, Deoxys-Attack, …) pushed via the Python pipeline in `../push-pokemon/`.

Both indexed under the same 5+8 field shape so the UI doesn't need source-specific rendering — facets and result tiles work uniformly across both.

## What it does

- **Search box** with type-ahead (the type-ahead model is preloaded in Phase 6B; this UI already renders suggestions when they arrive).
- **5 facets**: Type (multi-value), Generation, Source, Form variant, Abilities.
- **Sort dropdown**: Relevance, Pokédex #, Speed (highest), Attack (highest).
- **Result tiles**: artwork + name + type badges (per-type colored) + generation + form-variant flag.
- **RGA panel**: `<atomic-generated-answer>` at the top of the results column. Backed by the `pokemon-rga` model + Semantic Encoder semantic ranking attached to the default query pipeline in Phase 6A.
- **Pager** + result count + analytics events (Coveo's UA pipeline).

## Why hand-built rather than `coveo atomic:init`

Coveo's CLI (`@coveo/cli@latest atomic:init`) currently requires Node 22+ (a transitive `undici@8.3.0` dep calls a Node-22-only API). We're on Node 20 (the latest LTS at time of writing). Hand-building this project as a standard Vite + `@coveo/atomic` setup:

- Removes Node-version coupling.
- Makes the wire-up explicit (one `index.html`, one `main.js`, one `style.css` — no CLI magic).
- Is panel-narratively stronger: the resulting code reads like a textbook Atomic integration, with no scaffold-generated boilerplate to explain away.

The CLI's output would have generated equivalent files; we just write them ourselves.

## How to run

```bash
cd atomic-search
npm install
npm run dev
```

Then open http://localhost:3000. The Vite dev server reads `COVEO_ORG_ID` and `COVEO_SEARCH_API_KEY` from the repo-root `.env` (the gitignored one with your real values) and injects them as `VITE_COVEO_ORG_ID` / `VITE_COVEO_SEARCH_TOKEN` into the browser bundle. The anonymous-search-template key is public-safe.

If you see a red "Configuration error" banner at the top of the page, your `.env` is missing one of the variables — see `../docs/api-keys.md`.

## File layout

```
atomic-search/
├── package.json        — dev deps: vite, @coveo/atomic, @coveo/headless
├── vite.config.js      — loads .env from repo root, exposes VITE_-prefixed vars
├── index.html          — the entire Atomic markup (declarative)
├── README.md           — this file
└── src/
    ├── main.js         — registers Atomic custom elements + initialize(orgId, token)
    └── style.css       — Pokemon-themed CSS, per-type badge colors
```

There's no JS-level component code here. **All of the UI is declarative HTML** — that's the Atomic value proposition: you describe the search experience in markup, Coveo handles the rest.

## Gotchas worth knowing if you touch this code

**`<atomic-sort-expression>` field names are bare.** The `expression` attribute takes `fieldname ascending` / `fieldname descending`, *without* the leading `@`. Atomic prepends the `@` automatically when constructing the underlying API query. If you write `@fieldname ascending` you'll get a `400 Invalid field name: @@fieldname` from Coveo because the `@` ends up doubled. The native Search API does want the `@` (which is why a curl directly against `/rest/search/v2` with `"sortCriteria":"@fieldname asc"` works), but Atomic adds it for you. Discovered the hard way on 2026-05-31 — preserved as a footnote so the next person doesn't hit it.

**Result templates render in shadow DOM.** Page-level CSS in `src/style.css` does NOT reach inside `<atomic-result-template>`'s rendered cards. For card-internal styling, put a `<style>` block inside the `<template>` tag (it scopes to that template's shadow root). CSS custom properties on `:root` *do* pierce shadow DOM, so we use those for theming tokens.

**Push docs use a custom URI scheme.** Source B documents have `documentId: pokeapi://pokemon/<slug>`. Some Atomic components (like `<atomic-result-link>`) may behave oddly with non-`http(s)` URIs. If you see Push-doc-specific rendering issues, that's worth checking first.

## What's deliberately NOT here

- **Headless + React Detail Page** — that's Phase 6C, in `../detail-page/` (sibling project).
- **Vercel hosting config** — Phase 7.
- **Server-minted search tokens** — production deployments mint scoped JWTs server-side and pass them to the browser. For our hosted demo, the Anonymous Search template key (already public-safe by design) is sufficient. Documented in `../docs/api-keys.md`.
