// Quick Puppeteer screenshot helper for the slides.
//
// Captures the 3 thumbnails Slide 1 needs (Atomic main page, Detail page,
// Coveo MCP developer page) at 1200×900 directly from the live URLs, with
// a deviceScaleFactor of 2 for retina-crisp embeds in the Marp PDF.
//
// Run from the repo root:
//   npx --yes -p puppeteer node presentation/slides/screenshot.mjs
//
// First run downloads Chromium (~170MB, cached after that). Subsequent
// runs are fast (~10s for all 3 screenshots).

import puppeteer from "puppeteer";

const targets = [
  {
    name: "Atomic main page (grassland theme)",
    url: "https://pokemon-search-one-chi.vercel.app/?theme=grassland",
    output: "presentation/slides/images/atomic-main.png",
    waitMs: 4000,
  },
  {
    name: "Headless + React detail page (Charizard)",
    url: "https://pokemon-search-one-chi.vercel.app/pokemon.html?name=charizard&theme=grassland",
    output: "presentation/slides/images/detail-page.png",
    waitMs: 6000,
  },
  {
    name: "Coveo MCP developer page",
    url: "https://www.coveo.com/en/developers/mcp-server",
    output: "presentation/slides/images/mcp-claude-code.png",
    waitMs: 3000,
  },
  {
    name: "RGA performance monitoring dashboard",
    url: "https://pokemon-rga-dashboard.vercel.app",
    output: "presentation/slides/images/rga-dashboard.png",
    waitMs: 5000,
  },
  {
    name: "Grafana query observability public dashboard",
    url: "https://charmingporridge966.grafana.net/public-dashboards/cf105c8dabc64e5b95a33a86ef502452",
    output: "presentation/slides/images/grafana-dashboard.png",
    waitMs: 7000,
  },
];

console.log("Launching headless Chromium...");
const browser = await puppeteer.launch({
  headless: "new",
  defaultViewport: { width: 1200, height: 900, deviceScaleFactor: 2 },
});

for (const t of targets) {
  console.log(`\n→ ${t.name}`);
  console.log(`  ${t.url}`);
  const page = await browser.newPage();
  try {
    await page.goto(t.url, {
      waitUntil: "networkidle2",
      timeout: 60000,
    });
    // Give SPA frontends extra time to settle (RGA streams, theme rolls, etc.)
    await new Promise((r) => setTimeout(r, t.waitMs));
    await page.screenshot({
      path: t.output,
      fullPage: false,
      type: "png",
    });
    console.log(`  ✓ saved → ${t.output}`);
  } catch (e) {
    console.error(`  ✗ failed: ${e.message}`);
  } finally {
    await page.close();
  }
}

await browser.close();
console.log("\nDone.");
