"""Phase 6F Layer 2 — LLM-assisted analyzer for RGA prompt-tuning.

What it does:
  1. Loads the latest and previous eval-runs/*-full.json.
  2. Computes per-category metrics; identifies the worst-degraded
     categories (largest gap between hard_recall and accuracy is the
     "RGA elaborates wrongly" signal).
  3. Samples failing answers verbatim from those categories — the
     LLM analyzer can't pattern-match without reading the data.
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
  uv run python src/analyzer.py                          # latest vs previous, stdout
  uv run python src/analyzer.py --emit PATH              # also write JSON to PATH
  uv run python src/analyzer.py --no-llm                 # skip the LLM call (data-pipeline test)
  uv run python src/analyzer.py --top-categories 5       # how many worst categories to sample from (default 3)
  uv run python src/analyzer.py --samples-per-category 3 # how many failing answers per category (default 3)
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
    summary: RunSummary,
    prior: RunSummary | None,
    top_n: int = 3,
) -> list[CategoryStats]:
    """Pick the categories most worth fixing.

    Ranking heuristic: prefer (1) categories that regressed vs prior (negative
    delta), then (2) categories with the largest hard_recall ↔ accuracy gap
    (the "elaborates wrongly" signal — RGA mentions the right fact but
    fabricates around it), then (3) lowest absolute accuracy. Tie-break on n
    (more questions = stronger signal).
    """

    def score(cat: CategoryStats) -> tuple[float, float, float, int]:
        delta = 0.0
        if prior is not None:
            prior_cat = prior.by_category.get(cat.key)
            if prior_cat:
                delta = cat.accuracy - prior_cat.accuracy
        # Lower scores are worse; we'll sort ascending and take the head.
        return (delta, -cat.gap, cat.accuracy, -cat.n)

    return sorted(summary.by_category.values(), key=score)[:top_n]


def sample_failures(
    per_question: list[dict],
    categories: list[CategoryStats],
    per_category: int = 3,
) -> list[FailingAnswer]:
    """Pull N failing questions from each of the given categories."""
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

You evaluate one (current prompt, latest eval, prior eval, failing answers) \
bundle at a time. The user provides:

  - The current prompt text on the model
  - Overall metrics (accuracy, precision, hard_recall) for the latest run
  - Per-category breakdown of the latest run + the prior run (so you can \
spot regressions)
  - 3-5 sample failing answers from the worst categories, verbatim, with \
the LLM judge's reasoning and identified false_claims

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
after the change.
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
    latest: RunSummary,
    prior: RunSummary | None,
    worst_categories: list[CategoryStats],
    failing_samples: list[FailingAnswer],
) -> str:
    lines: list[str] = []
    lines.append("CURRENT RGA CUSTOM PROMPT:")
    lines.append('"""')
    lines.append(current_prompt)
    lines.append('"""')
    lines.append("")
    lines.append(f"LATEST EVAL RUN ({latest.date}):")
    lines.append(
        f"  Overall:  accuracy={latest.overall_accuracy:.1%}  "
        f"precision={latest.overall_precision:.1%}  "
        f"hard_recall={latest.overall_hard_recall:.1%}"
    )
    if prior is not None:
        lines.append(f"\nPRIOR EVAL RUN ({prior.date}) — for trend context:")
        lines.append(
            f"  Overall:  accuracy={prior.overall_accuracy:.1%}  "
            f"precision={prior.overall_precision:.1%}  "
            f"hard_recall={prior.overall_hard_recall:.1%}"
        )
    else:
        lines.append(
            "\n(No prior run available — this is the first full eval. "
            "Analyze the latest run on its own merits.)"
        )

    lines.append(
        "\nWORST CATEGORIES (latest run, ranked by regression > gap > accuracy):"
    )
    for c in worst_categories:
        prior_acc = ""
        if prior:
            pc = prior.by_category.get(c.key)
            if pc:
                delta = c.accuracy - pc.accuracy
                sign = "+" if delta >= 0 else ""
                prior_acc = f" (prior: {pc.accuracy:.1%}, Δ={sign}{delta:.1%})"
        lines.append(
            f"  L{c.layer} {c.category:35s}  n={c.n:2d}  "
            f"acc={c.accuracy:.1%}  recall={c.hard_recall:.1%}  "
            f"gap={c.gap:+.1%}{prior_acc}"
        )

    lines.append("\nSAMPLE FAILING ANSWERS (verbatim — read these carefully):")
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
        "\nBased on the above, propose a refined prompt via the submit_proposal tool."
    )
    return "\n".join(lines)


def call_analyzer(
    current_prompt: str,
    latest: RunSummary,
    prior: RunSummary | None,
    worst_categories: list[CategoryStats],
    failing_samples: list[FailingAnswer],
    *,
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
        current_prompt, latest, prior, worst_categories, failing_samples
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
    args = ap.parse_args()

    # Find eval-runs
    runs = list_full_runs(EVAL_RUNS_DIR)
    if not runs:
        print(
            "ERROR: no eval-runs/*-full.json files found. "
            "Run the evaluator first.",
            file=sys.stderr,
        )
        return 1
    latest_path = runs[-1]
    prior_path = runs[-2] if len(runs) >= 2 else None
    print(f"→ Latest run: {latest_path.name}")
    print(f"→ Prior run:  {prior_path.name if prior_path else '(none)'}")

    # Summarize
    latest, latest_perq = summarize_run(latest_path)
    prior = summarize_run(prior_path)[0] if prior_path else None

    # Pick worst categories
    worst = rank_worst_categories(latest, prior, top_n=args.top_categories)
    print(f"\n→ Worst {len(worst)} categories (ranked):")
    for c in worst:
        prior_part = ""
        if prior:
            pc = prior.by_category.get(c.key)
            if pc:
                delta = c.accuracy - pc.accuracy
                sign = "+" if delta >= 0 else ""
                prior_part = f"  (Δ vs prior: {sign}{delta:.1%})"
        print(
            f"  L{c.layer} {c.category:35s}  n={c.n:2d}  "
            f"acc={c.accuracy:.1%}  recall={c.hard_recall:.1%}  "
            f"gap={c.gap:+.1%}{prior_part}"
        )

    # Sample failures
    failing = sample_failures(
        latest_perq, worst, per_category=args.samples_per_category
    )
    print(f"\n→ Sampled {len(failing)} failing answers from worst categories.")

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
            latest,
            prior,
            worst,
            failing,
        )
    except Exception as e:
        print(f"ERROR: analyzer call failed: {e}", file=sys.stderr)
        return 1

    print_proposal(proposal, current.prompt.strip(), latest)

    if args.emit:
        args.emit.parent.mkdir(parents=True, exist_ok=True)
        args.emit.write_text(proposal.model_dump_json(indent=2))
        print(f"\n→ Proposal emitted to {args.emit}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
