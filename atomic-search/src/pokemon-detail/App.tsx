// Phase 6C — Pokémon Detail Page (Headless + React).
//
// Three Coveo surfaces composed on a single page:
//
//   1. Standard Search API (via Headless's SearchEngine + ResultList) to
//      pull the canonical Pokémon document the user clicked from the
//      Atomic main page.
//   2. Passage Retrieval API (direct fetch, same pattern as
//      atomic-search/src/passage-retrieval.js) to surface the most
//      semantically-relevant chunk about this specific Pokémon — the
//      "featured insight" card.
//   3. A second Headless engine pinned to the same generation as the
//      hero Pokémon → "Related Pokémon" grid below.
//
// Why two Headless engines: each engine manages one query state at a
// time. The hero result and the related-list run separate queries, so
// they get separate engines. Cheap (each engine is just a small redux-
// like store + an http client) and idiomatic.

import { useEffect, useMemo, useState } from "react";
import {
  buildSearchEngine,
  buildResultList,
  buildSearchBox,
  type SearchEngine,
  type Result,
} from "@coveo/headless";
import MarkdownIt from "markdown-it";

// Match the Atomic main page's PR rendering setup so the two surfaces
// behave consistently: real markdown (tables, headers) renders as HTML,
// but no raw HTML pass-through (XSS guard) and no auto-linkification
// (anchor-only TOC links like [Skip to main content](#main) are noise
// from pokemondb.net's page chrome — stripped pre-parse).
const md = new MarkdownIt({
  html: false,
  linkify: false,
  breaks: false,
  typographer: false,
});

function stripAnchorOnlyLinks(text: string): string {
  return text.replace(/\[([^\]]*)\]\(#[^)]*\)/g, "$1");
}

// PR sometimes returns a chunk that WAS a table on the source page but
// got linearized during chunking — newlines between rows are gone, so
// what arrives is `| a | b | c | | d | e | f | | g | h | i |` (rows
// separated by `| |` runs instead of `\n`). markdown-it can't render
// this as a table without a header separator row + per-line breaks, so
// it falls back to inline text rendering ("pipe soup").
//
// We rebuild the table client-side:
//   1. If the chunk already has a GFM separator row, leave it alone.
//   2. Otherwise, if it looks tabular (>= 8 pipes, splits cleanly on
//      `| |` into >= 2 segments with matching column count), insert
//      a synthetic header + separator row so markdown-it recognizes it.
// Falls back to the original text if reconstruction would produce a
// malformed table — we never want to make rendering worse.
function maybeReconstructTable(text: string): string {
  if (GFM_TABLE_SEPARATOR.test(text)) return text;
  const pipeCount = (text.match(/\|/g) || []).length;
  if (pipeCount < 8) return text;
  const rows = text
    .split(/\|\s*\|/)
    .map((r) => r.trim())
    .filter(Boolean)
    .map((r) => {
      if (!r.startsWith("|")) r = "| " + r;
      if (!r.endsWith("|")) r = r + " |";
      return r;
    });
  if (rows.length < 2) return text;
  const cols = (rows[0].match(/\|/g) || []).length - 1;
  if (cols < 2) return text;
  // Empty headers because the original <th> labels didn't survive PR's
  // chunker. Better than nothing — the data rows still render cleanly.
  const headerRow = "|" + " |".repeat(cols);
  const separator = "|" + "---|".repeat(cols);
  return [headerRow, separator, ...rows].join("\n");
}

// PR returns 1-N candidate chunks ranked by semantic relevance. The top
// one isn't always the most readable on a Pokémon-detail page: pages
// start with TOC chrome ("Skip to main content", "Contents - [Info]...")
// and contain large type-defense matchup TABLES that semantically match
// "what is X" queries but render as noisy pipe-syntax soup if not picked
// carefully. We score each candidate by signal-to-noise.
//
// Key insight: pipes are ONLY noise when they aren't part of a renderable
// GFM table. A chunk like `| a | b | c |\n|---|---|---|\n| 1 | 2 | 3 |`
// renders as a real <table>; we want THAT to score LOW. A chunk that's
// just `| a | b | c | 1 | 2 | 3` (fragment without a header separator
// row) renders as inline text soup; we want THAT to score HIGH.
const GFM_TABLE_SEPARATOR = /\n\s*\|?\s*:?-{3,}:?(\s*\|\s*:?-{3,}:?)+\s*\|?\s*\n/;

function noiseScore(text: string): number {
  if (!text) return 1;
  const hasRenderableTable = GFM_TABLE_SEPARATOR.test(text);
  const pipes = (text.match(/\|/g) || []).length;
  const links = (text.match(/\[[^\]]*\]\([^)]*\)/g) || []).length;
  // Pipes only count as noise when markdown-it CAN'T render the chunk
  // as a table — i.e., no header separator row present.
  const pipeNoise = hasRenderableTable ? 0 : pipes;
  const linkNoise = links * 3;
  return (pipeNoise + linkNoise) / Math.max(text.length, 1);
}

function sortPassagesByReadability(passages: Passage[]): Passage[] {
  return [...passages]
    .map((p) => ({ p, score: noiseScore(p.text || "") }))
    .sort((a, b) => a.score - b.score)
    .map((x) => x.p);
}

// ---------- Env + config ----------

const ORG_ID = import.meta.env.VITE_COVEO_ORG_ID as string;
const SEARCH_TOKEN = import.meta.env.VITE_COVEO_SEARCH_TOKEN as string;
const SEARCH_HUB = "pokemon-search";
const PR_ENDPOINT = ORG_ID
  ? `https://${ORG_ID}.org.coveo.com/rest/search/v3/passages/retrieve`
  : null;

// ---------- Types ----------

type PokemonFields = {
  pokemon_name?: string | string[];
  pokemon_type?: string | string[];
  image_url?: string | string[];
  dex_number?: number | string;
  generation?: string | string[];
  source?: string | string[];
};

type Passage = {
  text: string;
  relevanceScore?: number;
  document?: {
    title?: string;
    fields?: { clickableuri?: string };
    clickableuri?: string;
  };
};

// ---------- Helpers ----------

function firstString(v: string | string[] | number | undefined): string {
  if (v === undefined || v === null) return "";
  if (Array.isArray(v)) return v[0] ?? "";
  return String(v);
}

function asArray(v: string | string[] | undefined): string[] {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

function titleize(slug: string): string {
  return slug
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getNameFromUrl(): string {
  if (typeof window === "undefined") return "";
  const params = new URLSearchParams(window.location.search);
  return (params.get("name") ?? "").trim();
}

// Build a Headless engine pre-configured for our org. The two engines on
// this page are identical in setup, just different in what they query.
function makeEngine(): SearchEngine {
  return buildSearchEngine({
    configuration: {
      organizationId: ORG_ID,
      accessToken: SEARCH_TOKEN,
      search: { searchHub: SEARCH_HUB },
    },
  });
}

// ---------- Hero Pokémon hook ----------
//
// Fires one Coveo search for the slug we got from ?name=X. Returns the
// top result + loading state. We keep numberOfResults=1 — the detail
// page is single-Pokémon by design; if the slug matches multiple
// (mega/regional variants), the user can pivot via the related grid.

function usePokemonHero(slug: string): {
  hero: Result | null;
  loading: boolean;
  error: string | null;
} {
  const engine = useMemo(makeEngine, []);
  const [state, setState] = useState<{
    hero: Result | null;
    loading: boolean;
    error: string | null;
  }>({ hero: null, loading: true, error: null });

  useEffect(() => {
    if (!slug) {
      setState({ hero: null, loading: false, error: "missing-slug" });
      return;
    }
    const resultList = buildResultList(engine, {
      options: { fieldsToInclude: ["pokemon_name", "pokemon_type", "image_url", "dex_number", "generation", "source"] },
    });
    const unsubscribe = resultList.subscribe(() => {
      const s = resultList.state;
      // Headless's ResultList controller doesn't expose isLoading; the
      // search controller does. Watch the engine.state.search shape.
      const search = engine.state.search;
      if (search.isLoading) return;
      setState({
        hero: s.results[0] ?? null,
        loading: false,
        error: s.results.length === 0 ? "not-found" : null,
      });
    });

    const box = buildSearchBox(engine);
    box.updateText(slug);
    box.submit();

    return () => {
      unsubscribe();
    };
  }, [engine, slug]);

  return state;
}

// ---------- Passage Retrieval hook (for featured insight) ----------

function useFeaturedPassage(slug: string): {
  passages: Passage[];
  loading: boolean;
} {
  const [state, setState] = useState<{ passages: Passage[]; loading: boolean }>(
    { passages: [], loading: true },
  );

  useEffect(() => {
    if (!slug || !PR_ENDPOINT) {
      setState({ passages: [], loading: false });
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const resp = await fetch(PR_ENDPOINT, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${SEARCH_TOKEN}`,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            // Phrasing the query as a natural-language question gives the
            // PR algorithm something to ground its semantic ranking on.
            // The bare slug ("charizard") works too but the question form
            // empirically surfaces more useful passages.
            query: `what is ${slug}?`,
            additionalFields: ["clickableuri", "pokemon_name"],
            // Fetch 3 candidates so pickBestPassage() can drop the
            // table-heavy / nav-chunk noise that PR sometimes ranks
            // semantically high (the type-defense matchup table scores
            // high on "what is X" queries but reads as pipe-soup).
            maxPassages: 3,
            searchHub: SEARCH_HUB,
            localization: { locale: "en-US", timezone: "America/New_York" },
          }),
        });
        if (!resp.ok) {
          setState({ passages: [], loading: false });
          return;
        }
        const data = await resp.json();
        if (cancelled) return;
        const candidates: Passage[] = data.items ?? data.passages ?? [];
        setState({
          passages: sortPassagesByReadability(candidates),
          loading: false,
        });
      } catch {
        if (!cancelled) setState({ passages: [], loading: false });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  return state;
}

// ---------- Related Pokémon hook ----------
//
// Pulls 6 Pokémon from the same generation as the hero (chosen because
// generation is the cleanest grouping our index supports — same-type
// would also work but type ties feel less natural for a "you might also
// like" surface). Excludes the hero itself.

function useRelatedPokemon(
  generation: string,
  excludeName: string,
): { related: Result[]; loading: boolean } {
  const engine = useMemo(makeEngine, []);
  const [state, setState] = useState<{ related: Result[]; loading: boolean }>({
    related: [],
    loading: true,
  });

  useEffect(() => {
    if (!generation) {
      setState({ related: [], loading: false });
      return;
    }
    const resultList = buildResultList(engine, {
      options: {
        fieldsToInclude: ["pokemon_name", "pokemon_type", "image_url", "dex_number"],
      },
    });
    const unsubscribe = resultList.subscribe(() => {
      const search = engine.state.search;
      if (search.isLoading) return;
      const filtered = resultList.state.results.filter(
        (r) =>
          firstString((r.raw as PokemonFields).pokemon_name).toLowerCase() !==
          excludeName.toLowerCase(),
      );
      setState({ related: filtered.slice(0, 6), loading: false });
    });

    // Filter by generation via Coveo's query syntax `@field==value`.
    // We use the search box's q parameter rather than cq (constant query)
    // because cq isn't exposed via a top-level Headless controller — and
    // putting the filter in q works fine for a single-shot fetch like this.
    // JSON.stringify wraps the value in quotes, which Coveo's query syntax
    // requires when the value contains spaces ("Generation 1").
    const box = buildSearchBox(engine);
    box.updateText(`@generation==${JSON.stringify(generation)}`);
    box.submit();

    return () => {
      unsubscribe();
    };
  }, [engine, generation, excludeName]);

  return state;
}

// ---------- View components ----------

function TypeBadge({ type }: { type: string }) {
  const klass = `type-badge type-${type.toLowerCase()}`;
  return <span className={klass}>{type}</span>;
}

function Hero({ result }: { result: Result }) {
  const f = result.raw as PokemonFields;
  const name = firstString(f.pokemon_name) || titleize(getNameFromUrl());
  const types = asArray(f.pokemon_type);
  const image = firstString(f.image_url);
  const dex = firstString(f.dex_number);
  const gen = firstString(f.generation);
  const sourceUri = result.clickUri || result.uri;

  return (
    <section className="hero">
      {image ? (
        <img className="hero-image" src={image} alt={name} loading="eager" />
      ) : (
        <div className="hero-image-placeholder" aria-hidden>
          ?
        </div>
      )}
      <div className="hero-meta">
        <p className="hero-dex">
          {dex ? `№ ${String(dex).padStart(4, "0")}` : ""}
        </p>
        <h1 className="hero-name">{name}</h1>
        <div className="hero-types">
          {types.map((t) => (
            <TypeBadge key={t} type={t} />
          ))}
        </div>
        {gen && <p className="hero-gen">{gen}</p>}
        {sourceUri && (
          <p className="hero-source">
            <a href={sourceUri} target="_blank" rel="noreferrer">
              View source page ↗
            </a>
          </p>
        )}
      </div>
    </section>
  );
}

// One passage card — renders the chunk through markdown-it. The same
// pipeline as atomic-search/src/passage-retrieval.js so the detail page
// and the main page's PR panel behave identically: anchor-only TOC links
// stripped, markdown rendered as HTML, tables come out as <table>.
function PassageCard({
  passage,
  defaultOpen,
  index,
}: {
  passage: Passage;
  defaultOpen: boolean;
  index: number;
}) {
  const rawText = passage.text.slice(0, 1200);
  // Pipeline: drop anchor-only TOC links → reconstruct flattened tables
  // (synthesize missing header + separator rows) → markdown-it render.
  const preprocessed = maybeReconstructTable(stripAnchorOnlyLinks(rawText));
  const html = md.render(preprocessed);
  const sourceUri =
    passage.document?.fields?.clickableuri ??
    passage.document?.clickableuri ??
    "";
  return (
    <details className="passage-card" open={defaultOpen}>
      <summary className="passage-card-summary">
        <span className="passage-card-chevron" aria-hidden>▸</span>
        <span className="passage-card-rank">Passage {index + 1}</span>
        {sourceUri && (
          <span className="passage-card-source-hint">
            from {new URL(sourceUri).pathname}
          </span>
        )}
      </summary>
      <div
        className="passage-card-body"
        dangerouslySetInnerHTML={{ __html: html }}
      />
      {sourceUri && (
        <footer className="passage-card-source">
          <a href={sourceUri} target="_blank" rel="noreferrer">
            Source: {new URL(sourceUri).hostname}
            {new URL(sourceUri).pathname} ↗
          </a>
        </footer>
      )}
    </details>
  );
}

function FeaturedPassage({ slug }: { slug: string }) {
  const { passages, loading } = useFeaturedPassage(slug);
  if (loading) {
    return (
      <section className="featured-passage featured-passage--loading">
        Loading featured passages…
      </section>
    );
  }
  if (!passages.length) {
    return null;
  }
  return (
    <section className="featured-passage">
      <header className="featured-passage-header">
        <h2>Featured insights</h2>
        <p className="featured-passage-subtitle">
          Top semantically-ranked passages from the indexed content,
          ordered by readability. Pulled via Coveo's Passage Retrieval API
          — the same primitive an enterprise customer would use to ground
          their own LLM. The first card is the cleanest prose chunk; the
          others often contain structured tables (movesets, stats) worth
          expanding.
        </p>
      </header>
      <div className="passage-card-list">
        {passages.map((p, i) => (
          <PassageCard
            key={i}
            passage={p}
            // Only the cleanest passage is expanded by default; the rest
            // are progressive disclosure so the panel stays scannable.
            defaultOpen={i === 0}
            index={i}
          />
        ))}
      </div>
    </section>
  );
}

function RelatedGrid({
  generation,
  excludeName,
}: {
  generation: string;
  excludeName: string;
}) {
  const { related, loading } = useRelatedPokemon(generation, excludeName);
  if (loading) {
    return (
      <section className="related related--loading">
        Loading related Pokémon…
      </section>
    );
  }
  if (related.length === 0) {
    return null;
  }
  return (
    <section className="related">
      <h2>Other Pokémon from {generation}</h2>
      <div className="related-grid">
        {related.map((r) => {
          const f = r.raw as PokemonFields;
          const name = firstString(f.pokemon_name);
          const types = asArray(f.pokemon_type);
          const image = firstString(f.image_url);
          const slug = name.toLowerCase().replace(/[\s.]+/g, "-");
          return (
            <a
              key={r.uniqueId}
              className="related-card"
              href={`/pokemon.html?name=${encodeURIComponent(slug)}`}
            >
              {image && <img src={image} alt={name} loading="lazy" />}
              <div className="related-card-name">{name}</div>
              <div className="related-card-types">
                {types.map((t) => (
                  <TypeBadge key={t} type={t} />
                ))}
              </div>
            </a>
          );
        })}
      </div>
    </section>
  );
}

// ---------- App ----------

export default function App() {
  const slug = getNameFromUrl();
  const { hero, loading, error } = usePokemonHero(slug);

  if (!ORG_ID || !SEARCH_TOKEN) {
    return (
      <main className="detail-app">
        <BackLink />
        <div className="detail-error">
          <h1>Configuration error</h1>
          <p>
            The Coveo org id or search token isn't configured. Check the env
            vars on the Vercel deploy (or the .env file in local dev).
          </p>
        </div>
      </main>
    );
  }

  if (!slug) {
    return (
      <main className="detail-app">
        <BackLink />
        <div className="detail-error">
          <h1>No Pokémon specified</h1>
          <p>
            This page expects a <code>?name=&lt;slug&gt;</code> query
            parameter. Try{" "}
            <a href="/pokemon.html?name=charizard">/pokemon.html?name=charizard</a>
            .
          </p>
        </div>
      </main>
    );
  }

  if (loading) {
    return (
      <main className="detail-app">
        <BackLink />
        <div className="detail-loading">
          <p>Loading {titleize(slug)}…</p>
        </div>
      </main>
    );
  }

  if (error === "not-found" || !hero) {
    return (
      <main className="detail-app">
        <BackLink />
        <div className="detail-error">
          <h1>Not found</h1>
          <p>
            No Pokémon found for <code>{slug}</code> in the index.{" "}
            <a href="/">Back to search</a> to try another query.
          </p>
        </div>
      </main>
    );
  }

  const generation = firstString((hero.raw as PokemonFields).generation);
  const name = firstString((hero.raw as PokemonFields).pokemon_name) || slug;

  return (
    <main className="detail-app">
      <BackLink />
      <Hero result={hero} />
      <FeaturedPassage slug={slug} />
      <RelatedGrid generation={generation} excludeName={name} />
      <Footer />
    </main>
  );
}

function BackLink() {
  return (
    <nav className="detail-nav">
      <a href="/" className="back-link">
        ← Back to search
      </a>
    </nav>
  );
}

function Footer() {
  return (
    <footer className="detail-footer">
      <p>
        Powered by Coveo Headless + React. Hero result via Search API;
        featured insight via Passage Retrieval API; related grid via a
        second Headless engine filtered by generation. See{" "}
        <a
          href="https://github.com/benichou/coveo-pokemon-challenge/blob/main/docs/passage-retrieval.md"
          target="_blank"
          rel="noreferrer"
        >
          docs/passage-retrieval.md
        </a>{" "}
        for the architecture.
      </p>
    </footer>
  );
}
