// Atomic search interface wiring.
//
// Atomic itself is loaded via <script type="module"> from Coveo's CDN in
// index.html — that pulls down the component definitions AND the runtime
// assets (i18n locale files, icons) in one shot. By the time this script
// runs the custom elements are registered globally; we just have to wait
// for the interface element to be upgraded, then call initialize() with
// our org credentials.

import { buildPager } from "@coveo/headless";
import { applyTheme } from "./theme.js";

// Pick a random Pokémon-biome theme on every page load. The theme
// repaints both the body background pattern and the topbar's GBC
// palette so the look is coherent end-to-end. ?theme=<name> overrides
// for panel demos. See src/theme.js for the implementation.
applyTheme();

const ORG_ID = import.meta.env.VITE_COVEO_ORG_ID;
const SEARCH_TOKEN = import.meta.env.VITE_COVEO_SEARCH_TOKEN;

if (!ORG_ID || !SEARCH_TOKEN) {
  const banner = document.createElement("div");
  banner.style.cssText =
    "background:#fee;border:1px solid #c33;padding:1em;margin:1em;color:#700;font-family:monospace;";
  banner.innerHTML = `
    <strong>Configuration error</strong><br>
    Atomic can't reach Coveo because env vars are missing. Check the repo
    root <code>.env</code> file contains:<br>
    &nbsp;&nbsp;<code>COVEO_ORG_ID=&lt;your org&gt;</code><br>
    &nbsp;&nbsp;<code>COVEO_SEARCH_API_KEY=&lt;your anonymous search key&gt;</code><br>
    Then restart <code>npm run dev</code>. See <code>docs/api-keys.md</code>.
  `;
  document.body.prepend(banner);
}

const searchInterface = document.querySelector("#search");
await customElements.whenDefined("atomic-search-interface");
await searchInterface.initialize({
  accessToken: SEARCH_TOKEN,
  organizationId: ORG_ID,
});

// Phase 6E — query-level observability via Grafana Cloud Loki.
// One fire-and-forget POST per completed search. Silent no-op when
// Grafana credentials aren't configured (local dev "just works"
// without setup). See atomic-search/src/observability.js for the
// implementation + docs/observability.md for the architecture story.
import("./observability.js").then(({ instrumentEngine }) => {
  // searchInterface exposes the underlying Coveo Headless engine after
  // initialize() completes. Pass it to the instrumentation; it subscribes
  // to state changes and logs each search-completed event.
  if (searchInterface.engine) {
    instrumentEngine(searchInterface.engine);
  }
});

// Phase 8 — Coveo Passage Retrieval below RGA.
// Fires a parallel POST to the PR API on every search settle, renders the
// top 3 extracted passages into #passage-retrieval-panel. Falls through to
// silent no-op if the PR model isn't ready yet (422) or the kill-switch
// VITE_PASSAGE_RETRIEVAL_ENABLED=false is set.
import("./passage-retrieval.js").then(
  ({ instrumentEngine: instrumentPassageRetrieval }) => {
    if (searchInterface.engine) {
      instrumentPassageRetrieval(searchInterface.engine);
    }
  },
);

// -----------------------------------------------------------------------------
// User-friendly captions for raw field values.
//
// Atomic v3 uses i18n resource bundles in the `caption-<fieldname>` namespace
// to translate field values into display strings. Doing it this way (vs
// renaming the underlying Coveo source) keeps `@source=pokemondb-push`
// queries, scripts, and tests working untouched — only the UI display
// changes. See docs.coveo.com/atomic/latest/usage/atomic-localization/
// -----------------------------------------------------------------------------
searchInterface.i18n.addResourceBundle("en", "caption-source", {
  "pokemondb-sitemap": "PokemonDb",
  "pokemondb-push": "PokeAPI",
});

searchInterface.executeFirstSearch();

// -----------------------------------------------------------------------------
// RGA visibility gate
//
// Why this exists: RGA grounds its answer on the top-N retrieval results from
// the current pipeline. When the user switches sort from Relevance to Name /
// Date / Generation, the top-N becomes alphabetical / chronological — which
// has nothing to do with the typed question. RGA correctly refuses to ground
// on off-topic content, so the panel silently stays empty. To users this
// looks broken even though it's working as designed.
//
// Mitigation: subscribe to the Headless engine's state, watch sortCriteria,
// and toggle a body class. CSS hides the RGA panel when sort is non-relevancy
// and shows a small explanatory note in its place.
// -----------------------------------------------------------------------------
function watchSortForRgaGate() {
  const engine = searchInterface.engine;
  if (!engine || typeof engine.subscribe !== "function") return;

  const readSort = () => {
    // Atomic's underlying Headless redux state keeps the active sort criterion
    // at state.sortCriteria.sortCriteria (a string). Default is "relevancy".
    // Fall back through a couple of plausible paths so this still works if
    // Atomic versions shift the shape.
    const s = engine.state || {};
    return (
      s.sortCriteria?.sortCriteria ??
      s.sortCriteria ??
      s.criteria ??
      "relevancy"
    );
  };

  const apply = () => {
    const sort = String(readSort());
    const isRelevancy = sort === "relevancy" || sort.startsWith("relevancy");
    document.body.classList.toggle("rga-disabled", !isRelevancy);
  };

  engine.subscribe(apply);
  apply();
}

watchSortForRgaGate();

// -----------------------------------------------------------------------------
// Collapse empty <atomic-generated-answer> so the results toolbar aligns
// flush with the Type facet card to its left.
//
// Why this exists: Atomic's <atomic-generated-answer> custom element is
// :host { display: block } by default, so even before any query has been
// run (or when RGA decides it cannot answer) the empty host element still
// takes a flex slot inside .results — that slot + 1rem flex-gap above the
// next visible child pushes the results toolbar (Results 1-N of Y / Sort
// by) down by ~40-50px relative to the top of the Type facet card.
//
// Fix: subscribe to engine state, toggle body.has-rga-content based on
// whether the RGA slice has any actual content (streaming, loading, or
// non-empty answer text). CSS hides atomic-generated-answer when that
// class isn't present, so the empty box is truly display:none and the
// toolbar slides up to align with Type.
//
// The same gating pattern would apply to the PR panel if we ever found
// the same alignment issue there — but PR is wrapped in <details hidden>
// which already truly collapses when no passages exist, so no extra
// handling is needed today.
// -----------------------------------------------------------------------------
function watchAnswerVisibility() {
  const engine = searchInterface.engine;
  if (!engine || typeof engine.subscribe !== "function") return;

  const apply = () => {
    const s = engine.state || {};
    const ga = s.generatedAnswer || {};
    const hasContent = Boolean(
      ga.isLoading ||
        ga.isStreaming ||
        (typeof ga.answer === "string" && ga.answer.length > 0) ||
        ga.cannotAnswer ||
        ga.error,
    );
    document.body.classList.toggle("has-rga-content", hasContent);
  };

  engine.subscribe(apply);
  apply();
}

watchAnswerVisibility();

// -----------------------------------------------------------------------------
// First/last skip buttons for the pager.
//
// Atomic's <atomic-pager> ships only prev/next + numbered pages. The
// «/» buttons we added in index.html are vanilla <button>s wired to a
// Coveo Headless pager controller — same engine, same pagination
// state Atomic's pager component uses internally, just exposing
// selectPage(n) directly. Subscription syncs the :disabled state on
// every render so the « button greys out on page 1 and » greys on
// the last page.
// -----------------------------------------------------------------------------
function wireSkipPagerButtons() {
  const engine = searchInterface.engine;
  if (!engine) return;
  const pager = buildPager(engine);
  const firstBtn = document.querySelector(".pager-first");
  const lastBtn = document.querySelector(".pager-last");
  if (!firstBtn || !lastBtn) return;

  firstBtn.addEventListener("click", () => pager.selectPage(1));
  lastBtn.addEventListener("click", () => {
    const max = pager.state.maxPage;
    if (max > 0) pager.selectPage(max);
  });

  const sync = () => {
    const { currentPage, maxPage } = pager.state;
    firstBtn.disabled = !currentPage || currentPage <= 1;
    lastBtn.disabled = !maxPage || currentPage >= maxPage;
  };
  pager.subscribe(sync);
  sync();
}

wireSkipPagerButtons();
