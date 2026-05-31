import type { EvalRun, EvalRunWithMeta } from "./schemas";

// Vite bundles every `eval-runs/*-full.json` into the page at build time.
// `eager: true` returns the parsed JSON inline (no async fetch needed).
// Only `-full` files count; smoke and layer-scan runs are diagnostic.
const modules = import.meta.glob<EvalRun>("../../eval-runs/*-full.json", {
  eager: true,
  import: "default",
});

const FILENAME_DATE_RE = /(\d{4}-\d{2}-\d{2})-full\.json$/;

function extractDate(path: string): string {
  const m = path.match(FILENAME_DATE_RE);
  if (!m) {
    throw new Error(`eval-run filename missing YYYY-MM-DD: ${path}`);
  }
  return m[1];
}

export const runs: EvalRunWithMeta[] = Object.entries(modules)
  .map(([path, run]) => ({
    ...run,
    date: extractDate(path),
    filename: path.split("/").pop()!,
  }))
  .sort((a, b) => a.date.localeCompare(b.date));

export const latestRun: EvalRunWithMeta | undefined = runs[runs.length - 1];
export const previousRun: EvalRunWithMeta | undefined = runs[runs.length - 2];
