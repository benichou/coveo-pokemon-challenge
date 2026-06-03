// Phase 6C — entry point for the Pokémon Detail Page (React).
//
// Mounted at pokemon.html. The URL carries the Pokémon name as a query
// param (?name=charizard). We hand that to App.tsx which sets up a Coveo
// Headless engine, fires the Pokémon-specific query, and renders the
// detail view.
//
// Why React for this surface (and not Atomic web components like the
// main app): Coveo's Headless library is framework-agnostic but pairs
// cleanly with React via its observer pattern (engine.subscribe is a
// natural fit for React's render-on-state-change model). The panel
// narrative gets two Coveo SDKs in the same repo — Atomic for "fast
// list-view UI" and Headless+React for "rich custom detail UI" — which
// is exactly the choice an FDE walks a customer through.

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";

const root = document.getElementById("pokemon-detail-root");
if (!root) {
  throw new Error("pokemon-detail-root element missing from pokemon.html");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
