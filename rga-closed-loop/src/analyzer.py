"""Phase 6F Layer 2 — LLM-assisted analyzer for RGA prompt-tuning.

What it does:
  1. Loads the last N eval-runs/*-full.json (default N=5) for a multi-day
     view of the index's behavior. Older runs anchor the trend.
  2. Computes per-category metrics across the window. Ranks categories
     by a composite signal: chronic persistence (failing on most days)
     dominates, then drift (gradual decline), then absolute accuracy,
     then sample size. Multi-day ranking reduces noise — a one-day
     spike from LLM-judge variance won't trigger a proposal.
  3. Samples failing answers from the LATEST run only (older failures
     were against earlier prompt versions and don't reflect what to fix
     in the current one).
  4. Calls Sonnet 4.6 with tool-use forcing to return a structured
     PromptProposal: new prompt text + rationale + per-metric expected
     lift + sample before/after answers + self-rated confidence.
  5. Prints the proposal human-readably, or emits as JSON for the
     /rga-closed-loop skill to consume.

What it deliberately does NOT do:
  - Mutate prompts/pokemon-rga.yaml (that's the apply step's job)
  - Apply to Coveo (that's apply.py's job)
  - Open PRs (deferred / optional — see plan)
  - Commit to git
  - Run automatically (the cron in 6F.5 will, but with guardrails)

The analyzer is a pure proposal engine. Everything downstream of it is
either the skill (interactive) or the cron (auto-apply with guardrails).

Usage:
  uv run python src/analyzer.py                              # multi-day window, stdout
  uv run python src/analyzer.py --emit PATH                  # also write JSON to PATH
  uv run python src/analyzer.py --no-llm                     # skip the LLM call (data-pipeline test)
  uv run python src/analyzer.py --top-categories 5           # how many worst categories to sample from (default 3)
  uv run python src/analyzer.py --samples-per-category 3     # how many failing answers per category (default 3)
  uv run python src/analyzer.py --window-size 5              # how many recent eval-runs to consider (default 5)
  uv run python src/analyzer.py --persistence-threshold 0.70 # category accuracy < this = "failing" (default 0.70)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml
from anthropic import Anthropic
from dotenv import load_dotenv
from schemas import PromptProposal, PromptVersion

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

EVAL_RUNS_DIR = REPO_ROOT / "eval-runs"
CURRENT_PROMPT_YAML = (
    Path(__file__).resolve().parent.parent / "prompts" / "pokemon-rga.yaml"
)

# Pin the Sonnet snapshot so analyzer outputs are reproducible across runs.
# Same model as the rga-eval judge; sharing the snapshot means cost forecasts
# and quality assumptions stay aligned.
JUDGE_MODEL = "claude-sonnet-4-5-20250929"


# ---------- Data shapes (internal to the analyzer) ----------


@dataclass
class CategoryStats:
    """Per-category aggregate for one eval run."""

    layer: int
    category: str
    n: int
    accuracy: float
    hard_recall: float
    gap: float  # recall - accuracy. Big positive = "RGA elaborates wrongly"

    @property
    def key(self) -> str:
        return f"L{self.layer}:{self.category}"


@dataclass
class FailingAnswer:
    """One failing per-question record, ready to feed the LLM."""

    question_id: str
    layer: int
    category: str
    question: str
    answer_text: str
    judge_reasoning: str
    false_claims: list[str]


@dataclass
class RunSummary:
    """What the analyzer carries forward from an eval-run JSON."""

    date: str
    overall_accuracy: float
    overall_precision: float
    overall_hard_recall: float
    by_category: dict[str, CategoryStats]


# Default window of eval-runs the analyzer considers. 5 days balances signal
# (enough runs to detect drift + distinguish chronic from one-day noise)
# against responsiveness (a real degradation still gets picked up within ~3
# runs once it becomes persistent).
DEFAULT_WINDOW_SIZE = 5

# A category whose accuracy is below this threshold counts as "failing" for
# the purpose of `persistence`. 0.70 is deliberately lenient — we want to
# catch categories with sustained underperformance, not just ones that
# occasionally dip on bad LLM-judge days.
DEFAULT_PERSISTENCE_THRESHOLD = 0.70


@dataclass
class CategoryHistory:
    """Trajectory of one category across a multi-day eval-runs window.

    Holds the per-run CategoryStats in chronological order (oldest → newest)
    and exposes the two derived signals the ranker uses:

      - persistence: how many runs in the window had accuracy below the
        failing threshold. A category at 5/5 is chronically broken; one at
        1/5 is most likely noise.
      - drift: the change in accuracy from the first half of the window to
        the second half. Positive = declining (getting worse). Negative =
        improving. Helps surface gradual regressions before they hit
        catastrophic levels.
    """

    layer: int
    category: str
    runs: list[CategoryStats]  # chronological, oldest first

    @property
    def key(self) -> str:
        return f"L{self.layer}:{self.category}"

    @property
    def latest(self) -> CategoryStats:
        return self.runs[-1]

    @property
    def n_runs(self) -> int:
        return len(self.runs)

    def persistence(
        self, threshold: float = DEFAULT_PERSISTENCE_THRESHOLD
    ) -> int:
        """Count of runs in the window where this category was failing."""
        return sum(1 for cs in self.runs if cs.accuracy < threshold)

    def drift(self) -> float:
        """Accuracy decline from the first half of the window to the second.

        Positive = getting worse over time. Negative = improving. Zero when
        there's only one run in the window (no trend to measure).

        We split the window into halves rather than computing a slope so a
        single noisy run in the middle doesn't dominate. The midpoint uses
        integer division: for N=5 the first half is runs[0:2], the second
        half is runs[2:5]. For N=2 it's [0:1] vs [1:2] which collapses to
        the simple latest-vs-prior delta.
        """
        if len(self.runs) < 2:
            return 0.0
        mid = len(self.runs) // 2
        first = self.runs[:mid]
        second = self.runs[mid:]
        if not first or not second:
            return 0.0
        avg_first = sum(c.accuracy for c in first) / len(first)
        avg_second = sum(c.accuracy for c in second) / len(second)
        return avg_first - avg_second  # positive = decline

    def trajectory_str(self) -> str:
        """Compact rendering of accuracy values for the user message.

        Example: "10% 12% 11% 15% 14%" — visually scannable trajectory.
        """
        return " ".join(f"{c.accuracy:.0%}" for c in self.runs)


def compute_category_histories(
    runs: list[RunSummary],
) -> dict[str, CategoryHistory]:
    """Reorganize per-run categories into per-category histories.

    Input is a list of RunSummary in chronological order (oldest first).
    Output is keyed by category (e.g., "L1:ability_lookup"); each value
    is a CategoryHistory whose `runs` list is in the same chronological
    order as the input.

    A category that appears in some runs but not others (e.g., a question
    set evolved over time) will simply have a shorter `runs` list — we
    don't pad with synthetic zeros, since "category didn't exist yet" is
    not the same as "category had 0% accuracy."
    """
    histories: dict[str, CategoryHistory] = {}
    for run in runs:
        for key, cs in run.by_category.items():
            if key not in histories:
                histories[key] = CategoryHistory(
                    layer=cs.layer, category=cs.category, runs=[]
                )
            histories[key].runs.append(cs)
    return histories


# ---------- Eval-run loading + summarization ----------


def list_full_runs(eval_runs_dir: Path) -> list[Path]:
    """Return *-full.json files sorted oldest-first."""
    paths = sorted(eval_runs_dir.glob("*-full.json"))
    return paths


def parse_run_date(path: Path) -> str:
    """Extract YYYY-MM-DD from a filename like '2026-05-31-full.json'."""
    return path.name.removesuffix("-full.json")


def summarize_run(path: Path) -> tuple[RunSummary, list[dict]]:
    """Load + summarize an eval-run JSON. Returns (summary, raw per_question list)."""
    data = json.loads(path.read_text())
    overall = data["overall"]
    by_cat: dict[str, CategoryStats] = {}
    buckets: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for q in data["per_question"]:
        buckets[(q["layer"], q["category"])].append(q)
    for (layer, category), qs in buckets.items():
        n = len(qs)
        acc = sum(1 for q in qs if q["verdict"]["is_correct"]) / n
        recall = sum(q["hard_recall"] for q in qs) / n
        cs = CategoryStats(
            layer=layer,
            category=category,
            n=n,
            accuracy=acc,
            hard_recall=recall,
            gap=recall - acc,
        )
        by_cat[cs.key] = cs
    return (
        RunSummary(
            date=parse_run_date(path),
            overall_accuracy=overall["accuracy"],
            overall_precision=overall["precision"],
            overall_hard_recall=overall["hard_recall"],
            by_category=by_cat,
        ),
        data["per_question"],
    )


def rank_worst_categories(
    histories: dict[str, CategoryHistory],
    top_n: int = 3,
    persistence_threshold: float = DEFAULT_PERSISTENCE_THRESHOLD,
) -> list[CategoryHistory]:
    """Pick the categories most worth fixing, using the full multi-day window.

    Ranking is a composite of four signals, in priority order:

      1. **Persistence** — categories failing on most runs in the window
         dominate. A 5/5 chronic failure is almost certainly a real prompt
         or content gap; a 1/5 spike is almost certainly LLM-judge noise.

      2. **Drift** — categories whose accuracy is declining over the window
         are early-warning signals. We want the analyzer to fix things
         that are getting worse before they reach catastrophic levels.

      3. **Latest accuracy** — among categories with similar persistence and
         drift, lower absolute accuracy is worse.

      4. **Sample size** (tie-breaker) — more questions = stronger signal,
         so for ties we prefer to fix categories with bigger N.

    The score returns a tuple of floats; we sort ascending and take the head.
    Each component is negated where "more is worse" so the natural ascending
    sort puts the worst-by-each-signal first.
    """

    def score(h: CategoryHistory) -> tuple[float, float, float, int]:
        persistence = h.persistence(persistence_threshold)
        drift = h.drift()
        latest = h.latest
        # All terms encoded so that "smaller = worse" → ascending sort works:
        #   -persistence: chronic (5/5) sorts before noise (1/5)
        #   -drift:       declining (+drift) sorts before improving (-drift)
        #   accuracy:     low accuracy sorts before high
        #   -n:           bigger sample sorts before smaller
        return (-float(persistence), -drift, latest.accuracy, -latest.n)

    return sorted(histories.values(), key=score)[:top_n]


def sample_failures(
    per_question: list[dict],
    categories: list[CategoryHistory],
    per_category: int = 3,
) -> list[FailingAnswer]:
    """Pull N failing questions from each of the given categories.

    Samples come from the LATEST eval-run's `per_question` only — older
    failures were answered against earlier prompt versions and don't reflect
    what the analyzer needs to fix in the current prompt. The multi-day
    context already informs WHICH categories matter (via the ranker); the
    samples just need to show CURRENT failure shapes.
    """
    keys = {(c.layer, c.category) for c in categories}
    out: list[FailingAnswer] = []
    for q in per_question:
        if (q["layer"], q["category"]) not in keys:
            continue
        if q["verdict"]["is_correct"]:
            continue
        out.append(
            FailingAnswer(
                question_id=q["question_id"],
                layer=q["layer"],
                category=q["category"],
                question=q["question"],
                answer_text=q["answer_text"],
                judge_reasoning=q["verdict"]["reasoning"],
                false_claims=q["verdict"]["false_claims"],
            )
        )
    # Group + cap per category
    grouped: dict[tuple[int, str], list[FailingAnswer]] = defaultdict(list)
    for fa in out:
        grouped[(fa.layer, fa.category)].append(fa)
    sampled: list[FailingAnswer] = []
    for cat in categories:
        sampled.extend(grouped[(cat.layer, cat.category)][:per_category])
    return sampled


# ---------- LLM call ----------


ANALYZER_SYSTEM_PROMPT = """You are a senior production-AI engineer reviewing the daily eval of a Coveo \
Relevance Generative Answering (RGA) deployment on a Pokémon index. Your \
job is to propose a refined "Custom Prompt" (also known as the "Prompt \
instruction" or system prompt) for the RGA model when the eval shows \
accuracy regressions or stubborn failure modes.

You see a **multi-day window** of eval runs (typically the last 5 days) so \
that you can distinguish persistent failure patterns (chronic — worth \
fixing) from one-day spikes (LLM-judge variance — ignore). The user provides:

  - The current prompt text on the model
  - Overall metrics (accuracy, precision, hard_recall) across the whole \
window, in chronological order, so you can see the trend
  - Per-category breakdown for the **worst categories**, with each \
category's full trajectory across the window and two derived signals:
      • persistence (how many runs in the window had this category below \
the failing threshold — high persistence = chronic)
      • drift (decline in accuracy from the first half of the window to \
the second — positive = getting worse, negative = improving)
  - 3-5 sample failing answers from the LATEST run only (samples from \
older runs were answered against earlier prompt versions and don't \
reflect what to fix in the CURRENT prompt). Each sample includes the \
verbatim answer, the LLM judge's reasoning, and identified false_claims.

Prefer proposals that target categories with high persistence over ones \
that target single-day spikes. If the worst categories are mostly noise \
(low persistence, drift close to 0), the right answer is often "no change \
needed" — emit a no-op proposal.

You must call the `submit_proposal` tool exactly once with your \
recommendation. Do NOT respond with prose; the tool call IS the response.

Rules for the proposal:

  - `new_prompt` MUST be a complete replacement prompt — not a delta. It \
will be PUT to the Coveo API verbatim. Preserve good elements of the \
current prompt; refine what's not working.
  - The prompt should retain instruction to ground on retrieved sources, \
to refuse cleanly when sources don't cover the asked detail, and to cite \
sources. These are non-negotiable.
  - `rationale` is multi-paragraph. Explain WHICH failures motivated the \
change and HOW the new prompt addresses each. This goes into the YAML \
metadata and into the PR body / chat output for human review.
  - `expected_lift` should include per-category predictions for the \
categories you targeted, plus an overall_accuracy entry. `from` is the \
baseline (the latest run's value); `target` is your honest hypothesis \
after the change. \
**Both `from` and `target` are FRACTIONS in [0.0, 1.0], NOT percentages.** \
For example, write 0.76 (NOT 76) to represent "76% accuracy".
  - `sample_answers` is optional but helpful: 1-3 entries showing how the \
new prompt would change the answer to the worst failing questions. \
Format: list of {"question": ..., "before_answer": ..., \
"predicted_after_answer": ...}.
  - `confidence` is your self-rated confidence (0.0-1.0) that this \
change will deliver the predicted lift. Low confidence (<0.6) signals \
"experimental — review carefully." High confidence (>0.8) signals \
"I'm sure this is the right change."

If no change is warranted — accuracy is healthy AND no regressions — \
still emit a proposal where `new_prompt` equals the current prompt \
unchanged, `confidence` is high, and `rationale` explains why no change \
is needed. The skill / cron will treat this as a no-op.
"""


def build_analyzer_user_message(
    current_prompt: str,
    window: list[RunSummary],
    worst_categories: list[CategoryHistory],
    failing_samples: list[FailingAnswer],
    persistence_threshold: float = DEFAULT_PERSISTENCE_THRESHOLD,
) -> str:
    """Build the multi-day user message for the analyzer.

    `window` is the chronological list of run summaries (oldest first); the
    latest is the rightmost entry. `worst_categories` are CategoryHistory
    objects already ranked by the multi-day score function.
    """
    if not window:
        raise ValueError("window must contain at least one RunSummary")
    latest = window[-1]

    lines: list[str] = []
    lines.append("CURRENT RGA CUSTOM PROMPT:")
    lines.append('"""')
    lines.append(current_prompt)
    lines.append('"""')
    lines.append("")

    if len(window) == 1:
        lines.append(
            f"EVAL RUN ({latest.date}) — only one run available, no trend "
            "context yet:"
        )
        lines.append(
            f"  Overall:  accuracy={latest.overall_accuracy:.1%}  "
            f"precision={latest.overall_precision:.1%}  "
            f"hard_recall={latest.overall_hard_recall:.1%}"
        )
    else:
        lines.append(
            f"EVAL RUN HISTORY ({len(window)} runs, oldest first, latest "
            f"is {latest.date}):"
        )
        for r in window:
            marker = "  ← latest" if r is latest else ""
            lines.append(
                f"  {r.date}:  acc={r.overall_accuracy:.1%}  "
                f"prec={r.overall_precision:.1%}  "
                f"hr={r.overall_hard_recall:.1%}{marker}"
            )

    lines.append("")
    lines.append(
        f"WORST CATEGORIES "
        f"(ranked by persistence > drift > latest accuracy; "
        f"persistence threshold = {persistence_threshold:.0%} accuracy):"
    )
    for h in worst_categories:
        latest_cs = h.latest
        persistence = h.persistence(persistence_threshold)
        drift = h.drift()
        drift_sign = "+" if drift >= 0 else ""
        drift_label = (
            "declining"
            if drift > 0.02
            else ("improving" if drift < -0.02 else "stable")
        )
        lines.append("")
        lines.append(
            f"  L{h.layer} {h.category:35s}  "
            f"n={latest_cs.n:2d}  "
            f"latest_acc={latest_cs.accuracy:.1%}  "
            f"recall={latest_cs.hard_recall:.1%}  "
            f"gap={latest_cs.gap:+.1%}"
        )
        lines.append(
            f"    Trajectory ({h.n_runs} runs, oldest first): "
            f"{h.trajectory_str()}"
        )
        lines.append(
            f"    Persistence: {persistence}/{h.n_runs} runs below "
            f"{persistence_threshold:.0%}    "
            f"Drift: {drift_sign}{drift:.1%} ({drift_label})"
        )

    lines.append("")
    lines.append(
        "SAMPLE FAILING ANSWERS — from the LATEST run only (verbatim, read "
        "carefully):"
    )
    for i, fa in enumerate(failing_samples, 1):
        lines.append(
            f"\n--- Sample {i}: [{fa.question_id}] L{fa.layer} {fa.category} ---"
        )
        lines.append(f"Q: {fa.question}")
        lines.append(f"RGA answer: {fa.answer_text}")
        lines.append(f"Judge reasoning: {fa.judge_reasoning}")
        if fa.false_claims:
            lines.append("False claims identified:")
            for c in fa.false_claims:
                lines.append(f"  - {c}")

    lines.append(
        "\nBased on the multi-day signals above, propose a refined prompt "
        "via the submit_proposal tool. Prefer targeting categories with "
        "high persistence and/or positive drift over single-day spikes."
    )
    return "\n".join(lines)


def call_analyzer(
    current_prompt: str,
    window: list[RunSummary],
    worst_categories: list[CategoryHistory],
    failing_samples: list[FailingAnswer],
    *,
    persistence_threshold: float = DEFAULT_PERSISTENCE_THRESHOLD,
    model: str = JUDGE_MODEL,
    client: Anthropic | None = None,
) -> PromptProposal:
    """Call Sonnet with tool-use forcing; return validated PromptProposal."""
    if client is None:
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    schema = PromptProposal.model_json_schema()
    schema.pop("$defs", None)
    schema.pop("definitions", None)

    user_msg = build_analyzer_user_message(
        current_prompt,
        window,
        worst_categories,
        failing_samples,
        persistence_threshold=persistence_threshold,
    )

    response = client.messages.create(
        model=model,
        max_tokens=4096,  # the new_prompt can be long; give headroom
        system=ANALYZER_SYSTEM_PROMPT,
        tools=[
            {
                "name": "submit_proposal",
                "description": (
                    "Submit the refined RGA Custom Prompt + rationale + "
                    "expected lift + sample before/after answers + confidence."
                ),
                "input_schema": schema,
            }
        ],
        tool_choice={"type": "tool", "name": "submit_proposal"},
        messages=[{"role": "user", "content": user_msg}],
    )

    tool_blocks = [
        b for b in response.content if getattr(b, "type", "") == "tool_use"
    ]
    if not tool_blocks:
        raise RuntimeError(
            f"Sonnet didn't call submit_proposal. Response: {response.content}"
        )
    return PromptProposal.model_validate(tool_blocks[0].input)


# ---------- Pretty-printer ----------


def print_proposal(
    proposal: PromptProposal,
    current_prompt: str,
    latest: RunSummary,
) -> None:
    """Human-readable summary of the proposal to stdout."""
    print()
    print("=" * 72)
    print(" ANALYZER PROPOSAL")
    print("=" * 72)
    print(
        f"\nLatest run: {latest.date}  "
        f"accuracy={latest.overall_accuracy:.1%}  "
        f"precision={latest.overall_precision:.1%}  "
        f"hard_recall={latest.overall_hard_recall:.1%}"
    )
    print(f"Analyzer confidence: {proposal.confidence:.2f}")

    if proposal.new_prompt.strip() == current_prompt.strip():
        print("\n→ NO CHANGE PROPOSED. Current prompt is sufficient.")
    else:
        delta_chars = len(proposal.new_prompt) - len(current_prompt)
        print(
            f"\n→ CHANGE PROPOSED. "
            f"New prompt is {abs(delta_chars)} chars "
            f"{'longer' if delta_chars > 0 else 'shorter'} "
            f"({len(current_prompt)} → {len(proposal.new_prompt)})."
        )

    print("\n--- RATIONALE ---")
    print(proposal.rationale)

    if proposal.expected_lift:
        print("\n--- EXPECTED LIFT ---")
        for metric, lift in proposal.expected_lift.items():
            print(f"  {metric:40s}  {lift.from_:.1%} → {lift.target:.1%}")

    if proposal.sample_answers:
        print("\n--- SAMPLE ANSWERS (before vs predicted-after) ---")
        for i, sa in enumerate(proposal.sample_answers, 1):
            print(f"\n[Sample {i}]")
            print(f"  Q: {sa.get('question', '?')}")
            print(f"  Before:    {sa.get('before_answer', '')[:200]}…")
            print(f"  Predicted: {sa.get('predicted_after_answer', '')[:200]}…")

    if proposal.new_prompt.strip() != current_prompt.strip():
        print("\n--- NEW PROMPT (to be applied if approved) ---")
        print(proposal.new_prompt)


# ---------- Orchestrator ----------


def load_current_prompt() -> PromptVersion:
    raw = yaml.safe_load(CURRENT_PROMPT_YAML.read_text())
    return PromptVersion.model_validate(raw)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--emit",
        type=Path,
        default=None,
        help="Also write the proposal as JSON to this path (for skill consumption).",
    )
    ap.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip the LLM call. Useful for testing the data pipeline without spending API credit.",
    )
    ap.add_argument(
        "--top-categories",
        type=int,
        default=3,
        help="How many worst categories to sample failures from (default 3).",
    )
    ap.add_argument(
        "--samples-per-category",
        type=int,
        default=3,
        help="How many failing answers to sample per worst category (default 3).",
    )
    ap.add_argument(
        "--window-size",
        type=int,
        default=DEFAULT_WINDOW_SIZE,
        help=(
            f"How many recent eval-runs to consider for ranking + trend "
            f"detection (default {DEFAULT_WINDOW_SIZE}). Smaller windows "
            f"react faster to changes; larger windows filter more noise."
        ),
    )
    ap.add_argument(
        "--persistence-threshold",
        type=float,
        default=DEFAULT_PERSISTENCE_THRESHOLD,
        help=(
            f"Category accuracy below this counts as a 'failing' run for "
            f"the persistence signal (default "
            f"{DEFAULT_PERSISTENCE_THRESHOLD:.2f})."
        ),
    )
    args = ap.parse_args()

    # Load the most recent N eval-runs (or fewer if not enough exist yet).
    all_runs = list_full_runs(EVAL_RUNS_DIR)
    if not all_runs:
        print(
            "ERROR: no eval-runs/*-full.json files found. "
            "Run the evaluator first.",
            file=sys.stderr,
        )
        return 1
    window_paths = all_runs[-args.window_size :]
    print(
        f"→ Window: last {len(window_paths)} run(s) "
        f"(requested {args.window_size}, available {len(all_runs)})"
    )
    for p in window_paths:
        print(f"    {p.name}")

    # Summarize each run in the window. The latest run also yields the raw
    # per_question list so we can sample failing answers from it later.
    window: list[RunSummary] = []
    latest_perq: list[dict] = []
    for i, path in enumerate(window_paths):
        summary, perq = summarize_run(path)
        window.append(summary)
        if i == len(window_paths) - 1:
            latest_perq = perq
    latest = window[-1]

    # Build per-category histories across the window and rank by composite
    # multi-day score (persistence + drift + latest accuracy + n).
    histories = compute_category_histories(window)
    worst = rank_worst_categories(
        histories,
        top_n=args.top_categories,
        persistence_threshold=args.persistence_threshold,
    )
    print(f"\n→ Worst {len(worst)} categories (multi-day ranked):")
    for h in worst:
        latest_cs = h.latest
        persistence = h.persistence(args.persistence_threshold)
        drift = h.drift()
        drift_sign = "+" if drift >= 0 else ""
        print(
            f"  L{h.layer} {h.category:35s}  "
            f"n={latest_cs.n:2d}  "
            f"latest_acc={latest_cs.accuracy:.1%}  "
            f"persistence={persistence}/{h.n_runs}  "
            f"drift={drift_sign}{drift:.1%}"
        )

    # Sample failures from the LATEST run (older failures were against
    # earlier prompts — they'd just mislead the analyzer).
    failing = sample_failures(
        latest_perq, worst, per_category=args.samples_per_category
    )
    print(
        f"\n→ Sampled {len(failing)} failing answers from worst categories "
        f"(latest run only)."
    )

    if args.no_llm:
        print("\n--no-llm set; skipping the Sonnet call. Data pipeline OK.")
        return 0

    # Load current prompt
    current = load_current_prompt()

    # Call Sonnet
    print(f"\n→ Calling {JUDGE_MODEL} with tool-use forcing...")
    try:
        proposal = call_analyzer(
            current.prompt.strip(),
            window,
            worst,
            failing,
            persistence_threshold=args.persistence_threshold,
        )
    except Exception as e:
        print(f"ERROR: analyzer call failed: {e}", file=sys.stderr)
        return 1

    print_proposal(proposal, current.prompt.strip(), latest)

    if args.emit:
        args.emit.parent.mkdir(parents=True, exist_ok=True)
        args.emit.write_text(proposal.model_dump_json(indent=2) + "\n")
        print(f"\n→ Proposal emitted to {args.emit}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
