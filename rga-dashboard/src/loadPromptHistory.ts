// Phase 6F.7 — load prompt-version history at dashboard build time.
//
// Two data sources combined into a single chronological timeline:
//
//   1. rga-closed-loop/prompts/history/*.yaml — archived past versions.
//      Each was the live prompt at the time it was rotated out.
//
//   2. rga-closed-loop/prompts/pokemon-rga.yaml — the version currently
//      live in Coveo. Marked `is_current: true` in the output so the
//      history section can render it differently (e.g., "Live now" badge).
//
// We parse with js-yaml (small dep, added in 6F.7b) and read via Vite's
// import.meta.glob with query=?raw so the YAMLs land in the bundle as
// strings at build time. No runtime fetches; the dashboard stays
// statically-deployable.
//
// Output: PromptVersion[] sorted oldest → newest by applied_at, plus a
// derived PromptChangeEvent[] for the time-series chart markers.

import yaml from "js-yaml";
import type {
  PromptVersion,
  PromptChangeEvent,
  PromptChangeDayMarker,
} from "./schemas";

// ---- Source globs (raw strings; parsed below) -------------------------------

// History/ — past versions. Glob picks up every YAML in that subdir.
const HISTORY_RAW = import.meta.glob<string>(
  "../../rga-closed-loop/prompts/history/*.yaml",
  { eager: true, query: "?raw", import: "default" },
);

// Current — the live version. Single file, but globbing keeps the code
// symmetric and means we don't need a fallback if the file ever moves.
const CURRENT_RAW = import.meta.glob<string>(
  "../../rga-closed-loop/prompts/pokemon-rga.yaml",
  { eager: true, query: "?raw", import: "default" },
);

// ---- Helpers ----------------------------------------------------------------

function basename(path: string): string {
  return path.split("/").pop() ?? path;
}

function extractDate(applied_at: string): string {
  // applied_at is ISO 8601 (e.g., "2026-06-01T12:34:56+00:00"). Take the
  // YYYY-MM-DD prefix so the chart's date-string x-axis can match against it.
  return applied_at.slice(0, 10);
}

function makeAnchorId(version: string, filename: string): string {
  // Stable, URL-safe anchor for scroll-to behavior from chart markers.
  // Version alone isn't unique (1.0.0 could appear twice across renames);
  // pair with filename for safety.
  const slug = `${version}-${filename.replace(/\.yaml$/, "")}`;
  return `prompt-${slug.replace(/[^a-zA-Z0-9-]+/g, "-")}`;
}

type RawYaml = {
  prompt: string;
  metadata: {
    version: string;
    applied_at: string;
    applied_by: string;
    replaces?: string;
    rationale: string;
    expected_lift?: Record<
      string,
      { from?: number; from_?: number; target: number }
    >;
    validated_against?: string;
    related_eval_run?: string;
  };
};

function parseOne(
  path: string,
  raw: string,
  is_current: boolean,
): PromptVersion {
  const doc = yaml.load(raw) as RawYaml;
  const md = doc.metadata;
  return {
    filename: basename(path),
    is_current,
    applied_at: md.applied_at,
    applied_date: extractDate(md.applied_at),
    applied_by: md.applied_by,
    version: md.version,
    replaces: md.replaces ?? "",
    rationale: md.rationale,
    expected_lift: md.expected_lift ?? {},
    validated_against: md.validated_against ?? "",
    related_eval_run: md.related_eval_run ?? "",
    prompt: doc.prompt,
  };
}

// ---- Public API -------------------------------------------------------------

// Chronological timeline of every prompt version that has been live on the
// Coveo model. Oldest first. The current live version is the last entry and
// has is_current === true.
export const promptHistory: PromptVersion[] = (() => {
  const items: PromptVersion[] = [];
  for (const [path, raw] of Object.entries(HISTORY_RAW)) {
    items.push(parseOne(path, raw, false));
  }
  for (const [path, raw] of Object.entries(CURRENT_RAW)) {
    items.push(parseOne(path, raw, true));
  }
  // Sort oldest → newest. ISO 8601 strings sort lexicographically, so plain
  // string compare is correct.
  items.sort((a, b) => a.applied_at.localeCompare(b.applied_at));
  return items;
})();

// All prompt-change events (one per version that has a predecessor). The
// "very first" version is skipped because it isn't a change-from-something
// — there's no prior to compare against.
export const promptChangeEvents: PromptChangeEvent[] = promptHistory
  .filter((v) => v.replaces !== "")
  .map((v) => ({
    applied_date: v.applied_date,
    version: v.version,
    applied_by: v.applied_by,
    anchor_id: makeAnchorId(v.version, v.filename),
  }));

// What the TimeSeries chart actually renders — one marker per *date*, even
// when multiple versions were applied on the same day. Eval-run dates are
// truncated to YYYY-MM-DD, so two changes that landed at different UTC times
// on the same day would otherwise stack at the same x-position and visually
// occlude each other.
//
// Label rules: a single-change day renders just the version (e.g. "v1.1.0");
// a multi-change day renders the full chain in apply order (e.g. "v1.0.0
// → v1.1.0"). Three or more renders just first → last with a "(+N)" suffix
// to keep the label compact.
export const promptChangeDayMarkers: PromptChangeDayMarker[] = (() => {
  const byDate = new Map<string, PromptChangeEvent[]>();
  for (const evt of promptChangeEvents) {
    if (!byDate.has(evt.applied_date)) byDate.set(evt.applied_date, []);
    byDate.get(evt.applied_date)!.push(evt);
  }
  const out: PromptChangeDayMarker[] = [];
  for (const [date, events] of byDate.entries()) {
    // events are already in chronological order because promptChangeEvents
    // inherits the sort from promptHistory.
    let label: string;
    if (events.length === 1) {
      label = `v${events[0].version}`;
    } else if (events.length === 2) {
      label = `v${events[0].version} → v${events[1].version}`;
    } else {
      const first = events[0];
      const last = events[events.length - 1];
      label = `v${first.version} → v${last.version} (+${events.length - 2})`;
    }
    out.push({
      applied_date: date,
      versions: events,
      click_anchor_id: events[events.length - 1].anchor_id,
      label,
    });
  }
  return out.sort((a, b) =>
    a.applied_date.localeCompare(b.applied_date),
  );
})();

// Lookup by anchor_id, used by the marker-click → scroll-to handler.
export const promptByAnchorId: Record<string, PromptVersion> =
  Object.fromEntries(
    promptHistory.map((v) => [makeAnchorId(v.version, v.filename), v]),
  );

// Helper for the prompt-history section (6F.7c) — pairs each version with
// its predecessor so the diff view doesn't have to compute the relationship.
export function pairWithPrevious(): {
  current: PromptVersion;
  previous: PromptVersion | null;
}[] {
  // Render newest-first in the UI; for each entry pair it with its predecessor
  // from the chronological list.
  const reversed = [...promptHistory].reverse();
  return reversed.map((current) => {
    const idxInChrono = promptHistory.findIndex(
      (v) => v.filename === current.filename,
    );
    const previous = idxInChrono > 0 ? promptHistory[idxInChrono - 1] : null;
    return { current, previous };
  });
}
