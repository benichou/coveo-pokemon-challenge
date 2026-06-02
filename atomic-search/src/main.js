// Atomic search interface wiring.
//
// Atomic itself is loaded via <script type="module"> from Coveo's CDN in
// index.html — that pulls down the component definitions AND the runtime
// assets (i18n locale files, icons) in one shot. By the time this script
// runs the custom elements are registered globally; we just have to wait
// for the interface element to be upgraded, then call initialize() with
// our org credentials.

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
