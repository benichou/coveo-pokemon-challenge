// Pokémon-biome theme rotation.
//
// Applied to <body> on page load — on every refresh, a random theme from
// the set below paints both the topbar's GBC landscape (main page) and a
// subtle full-body pattern (both pages). Each theme is a coherent palette
// + pattern targeting one Pokémon-overworld biome.
//
// Override via ?theme=<name> query param (useful for panel demos —
// "?theme=volcano" guarantees the same look every time).
//
// Why per-load random and not per-day: a fresh-feeling theme on every
// refresh gives the panel a moment of delight + showcases the breadth
// of the visual system. Per-day would feel static during a demo
// session where you reload the page often.

export const THEMES = ["grassland", "beach", "cave", "volcano", "ice"];

export function applyTheme() {
  if (typeof document === "undefined") return null;
  const url = new URL(window.location.href);
  const override = url.searchParams.get("theme");
  const theme =
    override && THEMES.includes(override)
      ? override
      : THEMES[Math.floor(Math.random() * THEMES.length)];
  document.body.classList.add(`theme-${theme}`);
  document.body.setAttribute("data-theme", theme);
  return theme;
}
