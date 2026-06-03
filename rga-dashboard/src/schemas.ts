// Mirror of rga-eval/src/schemas.py — keep these in sync.
// (Pydantic on the producer side, plain TS on the consumer side.)

export type LayerStats = {
  accuracy: number;
  precision: number;
  hard_recall: number;
  citation_precision: number;
  n_questions: number;
};

export type JudgeVerdict = {
  is_correct: boolean;
  has_hallucination: boolean;
  false_claims: string[];
  reasoning: string;
};

export type PerQuestionResult = {
  question_id: string;
  question: string;
  layer: 1 | 2 | 3;
  category: string;
  rga_fired: boolean;
  answer_text: string;
  cited_uris: string[];
  hard_recall: number;
  citation_precision: number;
  verdict: JudgeVerdict;
};

export type EvalRun = {
  timestamp: string;
  coveo_org_id: string;
  judge_model: string;
  overall: LayerStats;
  by_layer: Record<"1" | "2" | "3", LayerStats>;
  per_question: PerQuestionResult[];
};

export type EvalRunWithMeta = EvalRun & {
  // Date string extracted from the filename (YYYY-MM-DD).
  date: string;
  // Source filename for debugging.
  filename: string;
};

// ---------- Prompt history (Phase 6F.7) ----------
//
// Mirror of rga-closed-loop/src/schemas.py PromptVersion. We parse the
// YAMLs at dashboard build time and use them to (a) annotate the time-series
// chart with vertical markers on prompt-change dates, and (b) render the
// prompt-history section below the chart with expandable version-to-version
// diffs.
//
// The metadata is the same dict structure that the closed-loop apply script
// PUTs to Coveo's API — single source of truth across the closed loop.

export type ExpectedLift = {
  // Pydantic emits this with a serialization alias of "from" (not "from_"),
  // so the on-disk YAML uses "from". Reading both keys defensively because
  // an older history file might have it serialized either way.
  from?: number;
  from_?: number;
  target: number;
};

export type PromptVersion = {
  // File the version was loaded from (basename, e.g. "2026-06-01-pre-analyzer-v1.yaml").
  filename: string;
  // True for prompts/pokemon-rga.yaml (the version currently live in Coveo).
  is_current: boolean;
  // ISO 8601 UTC timestamp the apply script PUT this version to Coveo.
  applied_at: string;
  // Date prefix extracted from applied_at for chart x-axis alignment.
  applied_date: string;
  applied_by: string;
  version: string;
  // Path (relative to repo root) to the predecessor history/ YAML. Empty
  // string for the very first version.
  replaces: string;
  rationale: string;
  expected_lift: Record<string, ExpectedLift>;
  validated_against: string;
  related_eval_run: string;
  // The literal prompt text — needed for the diff view (6F.7c).
  prompt: string;
};

// What the time-series chart consumes. A trimmed-down view of PromptVersion —
// just the fields the marker needs (position + label + reference into the
// full history list when clicked).
export type PromptChangeEvent = {
  applied_date: string; // YYYY-MM-DD for chart x-axis
  version: string;
  applied_by: string;
  // Anchor id matching the history-section card so a click on the marker
  // can scroll-to the corresponding card.
  anchor_id: string;
};

// One chart marker per *date*. Multiple prompt changes that all landed on
// the same day collapse into one marker; the label renders the full chain
// (e.g. "v1.0.0 → v1.1.0") and the click target is the LAST version applied
// that day (which is what's most relevant to scroll to).
export type PromptChangeDayMarker = {
  applied_date: string; // YYYY-MM-DD; matches the x-axis tick
  // Versions applied on this date, in the order they were applied (oldest →
  // newest). All elements are PromptChangeEvent entries from that day.
  versions: PromptChangeEvent[];
  // The anchor of the LAST version on this day — that's what marker-click
  // scrolls to (most recent change = most relevant card).
  click_anchor_id: string;
  // Pre-rendered label for the chart, e.g. "v1.1.0" or "v1.0.0 → v1.1.0".
  label: string;
};
