// Phase 8 — Coveo Passage Retrieval (PR) integration for the Atomic UI.
//
// Lifecycle:
//   - Subscribes to the Coveo Headless engine's state, same pattern as
//     observability.js — listens for "search settled" events.
//   - When a new search completes (new searchUid + non-loading), fires a
//     POST to Coveo's Passage Retrieval endpoint with the same query the
//     Search API just ran.
//   - Renders the top 3 passages into #passage-retrieval-panel below RGA.
//
// Why a separate UI surface (vs reusing <atomic-generated-answer>):
//   Atomic v3 has no built-in passage-retrieval component. The endpoint
//   lives on a different subdomain (`<orgId>.org.coveo.com` instead of
//   `platform.cloud.coveo.com`) and the response shape is different from
//   the standard search response. A vanilla JS module is the minimum-
//   integration path that doesn't require forking an Atomic component.
//
// Why it's complementary (not redundant) to RGA:
//   - RGA synthesizes a paragraph from retrieved chunks. The answer is
//     LLM-generated prose with citations.
//   - Passage Retrieval returns the verbatim source text — the *exact*
//     passages from indexed pages that the LLM would have grounded on.
//   - For "what type is Charizard", RGA answers in natural language with a
//     citation; Passage Retrieval surfaces the actual sentence on the
//     Charizard page that says "Type: Fire / Flying".
//   - Showing both side-by-side demonstrates the trade-off: RGA reads
//     fluently but adds an LLM hop; PR is fast + verbatim + better when
//     the user wants source-truth.
//
// Kill-switch:
//   - VITE_PASSAGE_RETRIEVAL_ENABLED=false disables the call (silent no-op).
//   - Dev mode (import.meta.env.DEV) does NOT auto-disable since PR works
//     against the live Coveo backend, unlike observability which needs the
//     Vercel proxy that doesn't exist locally.

import MarkdownIt from "markdown-it";
import { setLatest as setLatestPassageState } from "./passage-retrieval-state.js";

const ORG_ID = import.meta.env.VITE_COVEO_ORG_ID;

// Coveo's Passage Retrieval surfaces chunks extracted from indexed pages.
// pokemondb-sitemap chunks often contain markdown tables (Pokémon stats,
// move lists, abilities, evolutions) — those are HIGH-VALUE structured
// data we want to render properly, not strip. We use markdown-it with
// safe defaults (html: false → no raw HTML pass-through, blocks XSS via
// injected source content) to render those passages into real HTML
// (tables, headers, lists). The browser then displays them via .innerHTML.
//
// We deliberately turn linkify off because anchor-only links like
// "[Skip to main content](#main)" are noise from the page chrome, and
// we'd rather strip them entirely (regex pre-pass below) than render
// them as clickable anchors that go to "#" within our app.
const md = new MarkdownIt({
  html: false,
  linkify: false,
  breaks: false,
  typographer: false,
});

// Anchor-only markdown links (links to `#main`, `#dex-stats`, etc.) are
// pokemondb.net's table-of-contents chrome and have no value in our UI.
// Drop them BEFORE markdown-it parses, so they don't render as broken
// anchors that go nowhere when clicked.
function stripAnchorOnlyLinks(text) {
  return text.replace(/\[([^\]]*)\]\(#[^)]*\)/g, "$1");
}

// Render the source URI in two pieces — the hostname (small, muted) and
// the path (the meaningful identifier — typically /pokedex/<name>). This
// lets us show a compact, scannable source label in each passage card
// without the visual weight of a full URL. Falls back gracefully if the
// URI isn't well-formed.
function prettySourceUri(uri) {
  if (!uri) return null;
  try {
    const url = new URL(uri);
    return {
      host: url.hostname.replace(/^www\./, ""),
      path: url.pathname || "/",
      full: uri,
    };
  } catch {
    return { host: "", path: uri, full: uri };
  }
}
const SEARCH_TOKEN = import.meta.env.VITE_COVEO_SEARCH_TOKEN;
const ENABLED =
  import.meta.env.VITE_PASSAGE_RETRIEVAL_ENABLED !== "false";

// Coveo's Passage Retrieval lives on the org-scoped subdomain, not the
// standard platform.cloud.coveo.com. Confirmed via API spike 2026-06-03.
const ENDPOINT = ORG_ID
  ? `https://${ORG_ID}.org.coveo.com/rest/search/v3/passages/retrieve`
  : null;

const MAX_PASSAGES = 3;
const SEARCH_HUB = "pokemon-search";
const TARGET_SELECTOR = "#passage-retrieval-panel";

// Truncate long passages in the UI — Coveo's PR sometimes returns multi-
// paragraph chunks. 1200 chars is a sweet spot: long enough to keep most
// Pokémon stat tables intact (a typical 6-stat table is ~400-600 chars in
// raw markdown form), but short enough that the panel stays scannable
// across 3 passages stacked vertically.
const PASSAGE_MAX_CHARS = 1200;

function truncate(s, n) {
  if (typeof s !== "string") return "";
  return s.length > n ? s.slice(0, n).trimEnd() + "…" : s;
}

// Escape user-controlled text before injecting into HTML — Coveo's passage
// text comes from indexed content, which we trust, but the query text comes
// straight from the search box. Defensive.
function escapeHtml(s) {
  if (typeof s !== "string") return "";
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// ---------- API call ----------

async function fetchPassages(query) {
  if (!ENDPOINT || !SEARCH_TOKEN) return null;
  const body = {
    query,
    additionalFields: ["clickableuri", "pokemon_name", "pokemon_type"],
    maxPassages: MAX_PASSAGES,
    searchHub: SEARCH_HUB,
    localization: { locale: "en-US", timezone: "America/New_York" },
  };
  try {
    const resp = await fetch(ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${SEARCH_TOKEN}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
      // `keepalive: true` lets the request finish if the user navigates
      // away mid-search; same pattern as observability.js's POST.
      keepalive: true,
    });
    if (!resp.ok) {
      // 422 means "no PR model associated yet" — silent fail (the build
      // probably hasn't completed). Don't spam the console with errors
      // while the model is still building.
      if (resp.status === 422) return null;
      console.warn(`[passage-retrieval] HTTP ${resp.status}`);
      return null;
    }
    return await resp.json();
  } catch (e) {
    console.warn("[passage-retrieval] fetch failed:", e?.message);
    return null;
  }
}

// ---------- Rendering ----------

function renderPassages(passages) {
  const panel = document.querySelector(TARGET_SELECTOR);
  if (!panel) return;
  const body = panel.querySelector(".passage-panel-body");
  const countSlot = panel.querySelector("[data-passage-count]");
  if (!body) return;

  if (!passages || passages.length === 0) {
    panel.hidden = true;
    panel.open = false; // collapse the outer details when nothing's there
    body.innerHTML = "";
    if (countSlot) countSlot.textContent = "";
    return;
  }

  panel.hidden = false;
  // Outer panel stays COLLAPSED by default — the user explicitly opts in
  // by clicking the summary. We don't toggle `panel.open` programmatically
  // here, so a re-render for a new search keeps the user's preference (if
  // they already opened it for a previous query, native `<details>` keeps
  // it open; if not, it stays closed).
  if (countSlot) {
    countSlot.textContent = `— ${passages.length} passage${passages.length === 1 ? "" : "s"} available`;
  }
  body.innerHTML = passages
    .map((p, i) => {
      // Raw passage text from Coveo. Often contains markdown tables (stats,
      // moves, abilities) — high-value structured data we want to render.
      const rawText = p?.text ?? "";
      // Pre-pass: drop anchor-only chrome links before parsing.
      const cleaned = stripAnchorOnlyLinks(rawText);
      // Render markdown → HTML. Safe: md.html=false blocks raw HTML
      // pass-through, so injected source content can't run scripts.
      const renderedHtml = md.render(truncate(cleaned, PASSAGE_MAX_CHARS));

      // Document metadata: shape varies — newer PR returns it under
      // `document.fields`, older shape uses top-level. Try both.
      const fields =
        p?.document?.fields ??
        p?.document ??
        p?.documentExtensions ??
        {};
      const uri = fields.clickableuri ?? p?.document?.uri ?? "";
      const title = fields.title ?? p?.document?.title ?? "Source document";
      const score =
        typeof p?.relevanceScore === "number"
          ? p.relevanceScore.toFixed(2)
          : typeof p?.score === "number"
            ? p.score.toFixed(2)
            : "";
      // Collapsible card pattern (same as the prompt-history cards in the
      // RGA dashboard — Phase 6F.7c). Header is always visible; click
      // anywhere on it to expand the body. Inner anchor link gets
      // stopPropagation so it doesn't toggle the details when clicked.
      const titleSafe = escapeHtml(title);
      const src = prettySourceUri(uri);
      // Source row shown inside the expanded body — gives the user the
      // actual URL with an obvious external-link affordance. Different
      // from the summary's title-link: this is the literal source URI
      // they'd cite if they wrote a paper using this passage.
      const sourceRow = src
        ? `<div class="passage-source-row">
             <span class="passage-source-row-label">Source:</span>
             <a class="passage-source-row-link" href="${escapeHtml(src.full)}" target="_blank" rel="noreferrer" onclick="event.stopPropagation()">
               <span class="passage-source-row-host">${escapeHtml(src.host)}</span><span class="passage-source-row-path">${escapeHtml(src.path)}</span>
               <span class="passage-source-row-icon" aria-hidden>↗</span>
             </a>
           </div>`
        : "";
      return `
        <details class="passage-card">
          <summary class="passage-card-summary">
            <span class="passage-card-chevron" aria-hidden>▸</span>
            <span class="passage-rank">#${i + 1}</span>
            ${
              uri
                ? `<a class="passage-source" href="${escapeHtml(uri)}" target="_blank" rel="noreferrer" onclick="event.stopPropagation()">${titleSafe}</a>`
                : `<span class="passage-source">${titleSafe}</span>`
            }
            ${score ? `<span class="passage-score" title="Semantic similarity score from the Coveo Semantic Encoder model. Computed as cosine similarity between the query embedding and this passage's embedding. Higher = closer semantic match. Not a percentage; relative within this query's result set.">semantic similarity ${escapeHtml(score)}</span>` : ""}
          </summary>
          ${sourceRow}
          <div class="passage-text passage-text--markdown">${renderedHtml}</div>
        </details>
      `;
    })
    .join("");
}

// ---------- Engine subscription ----------

export function instrumentEngine(engine) {
  if (!ENABLED) return; // kill-switch
  if (!ENDPOINT) {
    console.warn("[passage-retrieval] org id missing; skipping");
    return;
  }
  if (!engine || typeof engine.subscribe !== "function") {
    console.warn(
      "[passage-retrieval] no valid engine passed; skipping",
    );
    return;
  }

  let lastFiredUid = null;
  engine.subscribe(() => {
    const state = engine.state;
    const search = state?.search;
    if (!search || search.isLoading) return;

    const uid =
      search.response?.searchUid ??
      search.searchResponseId ??
      search.searchUid;
    if (!uid || uid === lastFiredUid) return;

    const q = state?.query?.q ?? "";
    if (!q.trim()) {
      // Empty query — clear the panel.
      lastFiredUid = uid;
      renderPassages(null);
      return;
    }

    lastFiredUid = uid;
    // Fire-and-forget; if the request fails we silently hide the panel
    // rather than breaking the search experience.
    fetchPassages(q).then((data) => {
      const passages = data?.items ?? data?.passages ?? [];
      renderPassages(passages);
      // Stash the result for observability.js to include in its Grafana
      // log payload (cross-phase TODO from Phase 6E).
      const top = passages[0] ?? null;
      setLatestPassageState({
        searchUid: uid,
        fired: passages.length > 0,
        count: passages.length,
        top_text: truncate(top?.text ?? "", PASSAGE_MAX_CHARS),
        top_source_uri:
          top?.document?.clickableuri ??
          top?.documentExtensions?.clickableuri ??
          top?.document?.uri ??
          "",
      });
    });
  });
}

// Exposed for testing / browser-console debugging.
export const _internals = {
  ENDPOINT,
  MAX_PASSAGES,
  fetchPassages,
  renderPassages,
};
