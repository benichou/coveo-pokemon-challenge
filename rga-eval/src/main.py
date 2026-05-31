"""RGA Skill Evaluator — orchestrator.

End-to-end flow:
  1. Load golden/questions.json (validated by Pydantic at load time).
  2. Discover the Coveo RGA answer config ID (or read from env).
  3. For each question:
       a. Stream the RGA answer (Coveo /answer/v1/generate SSE)
       b. Compute deterministic metrics (hard_recall, citation_precision)
       c. Send to Sonnet 4.6 with tool-use forcing → JudgeVerdict
       d. Combine into PerQuestionResult
  4. Aggregate to LayerStats (per layer + overall).
  5. Write eval-runs/YYYY-MM-DD-<mode>.json via publish.write_run().

Output files are tagged by run mode so diagnostic runs never clobber the
canonical daily full run:
  full run            -> eval-runs/YYYY-MM-DD-full.json
  --limit N (smoke)   -> eval-runs/YYYY-MM-DD-smoke.json
  --layer N           -> eval-runs/YYYY-MM-DD-layer{N}.json

Usage:
  uv run python src/main.py                       # full 100-question run
  uv run python src/main.py --limit 5             # smoke test
  uv run python src/main.py --layer 3             # only Layer-3 (refusal) questions
  uv run python src/main.py --dry-run             # no API calls; just validate dataset
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from anthropic import Anthropic
from coveo_rga import (
    get_config_id_from_env_or_discover,
    stream_answer_with_retry,
)
from dotenv import load_dotenv
from llm_judge import DEFAULT_MODEL, judge_one
from metrics import aggregate, build_per_question, by_layer
from publish import write_run
from schemas import EvalRun, GoldenQuestion, JudgeVerdict, PerQuestionResult

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

GOLDEN_PATH = (
    Path(__file__).resolve().parent.parent / "golden" / "questions.json"
)


def load_questions() -> list[GoldenQuestion]:
    raw = json.loads(GOLDEN_PATH.read_text())
    return [GoldenQuestion.model_validate(q) for q in raw["questions"]]


def run_one(
    question: GoldenQuestion,
    *,
    org_id: str,
    config_id: str,
    coveo_key: str,
    anthropic_client: Anthropic,
    judge_model: str,
    verbose: bool,
) -> PerQuestionResult:
    """Run one full question — RGA + judge."""
    # 1. Stream answer
    try:
        rga = stream_answer_with_retry(
            org_id, config_id, coveo_key, question.question
        )
        rga_fired = rga.fired
        answer_text = rga.answer_text
        cited_uris = rga.cited_uris
    except Exception as e:
        # RGA failure — record as not-fired with error in text
        if verbose:
            print(f"  ⚠ RGA failed for {question.id}: {e}")
        rga_fired = False
        answer_text = ""
        cited_uris = []

    # 2. Judge
    try:
        verdict = judge_one(
            question, answer_text, model=judge_model, client=anthropic_client
        )
    except Exception as e:
        if verbose:
            print(f"  ⚠ Judge failed for {question.id}: {e}")
        verdict = JudgeVerdict(
            is_correct=False,
            has_hallucination=False,
            false_claims=[],
            reasoning=f"Judge call failed: {e}",
        )

    return build_per_question(
        question=question,
        answer_text=answer_text,
        rga_fired=rga_fired,
        cited_uris=cited_uris,
        verdict=verdict,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only evaluate the first N questions (smoke test).",
    )
    ap.add_argument(
        "--layer",
        type=int,
        choices=[1, 2, 3],
        default=0,
        help="Only evaluate questions from this layer.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip API calls; just load + validate the dataset.",
    )
    ap.add_argument(
        "--judge-model",
        default=os.environ.get("JUDGE_MODEL", DEFAULT_MODEL),
        help=f"Anthropic model id (default: {DEFAULT_MODEL}).",
    )
    args = ap.parse_args()

    print("=" * 64)
    print("RGA Skill Evaluator")
    print("=" * 64)

    # Load + filter questions
    questions = load_questions()
    if args.layer:
        questions = [q for q in questions if q.layer == args.layer]
    if args.limit:
        questions = questions[: args.limit]

    # Output-file mode tag. A limited run is a smoke test regardless of layer;
    # a layer-scoped (but unlimited) run is tagged by layer; otherwise it's the
    # canonical full run. See publish.write_run().
    if args.limit:
        mode = "smoke"
    elif args.layer:
        mode = f"layer{args.layer}"
    else:
        mode = "full"

    print(f"\nQuestions to evaluate: {len(questions)}  (mode: {mode})")

    if args.dry_run:
        print("--dry-run set; not calling any APIs. Dataset is valid.")
        return 0

    # Env checks. Two distinct Coveo keys:
    #   - COVEO_RGA_JUDGE_API_KEY (Knowledge.Answer Manager:Edit) — for
    #     discovering / managing answer configs. Used once at startup.
    #   - COVEO_SEARCH_API_KEY (Anonymous Search template) — for the actual
    #     generate streaming calls. The search key has both Execute Query
    #     AND Answer Manager:Use, which the generate endpoint requires.
    org_id = os.environ.get("COVEO_ORG_ID")
    judge_key = os.environ.get("COVEO_RGA_JUDGE_API_KEY")
    search_key = os.environ.get("COVEO_SEARCH_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    missing = [
        name
        for name, val in [
            ("COVEO_ORG_ID", org_id),
            ("COVEO_RGA_JUDGE_API_KEY", judge_key),
            ("COVEO_SEARCH_API_KEY", search_key),
            ("ANTHROPIC_API_KEY", anthropic_key),
        ]
        if not val
    ]
    if missing:
        print(f"ERROR: missing env vars: {missing}", file=sys.stderr)
        print("See docs/rga-eval.md for setup instructions.", file=sys.stderr)
        return 1

    # Discover config ID (use judge key — search key can't list configs)
    print("\nDiscovering Coveo RGA answer config...")
    try:
        config_id = get_config_id_from_env_or_discover(org_id, judge_key)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"  Using config: {config_id}")

    # Anthropic client (reused across questions)
    anthropic_client = Anthropic(api_key=anthropic_key)

    print(f"\nJudge model: {args.judge_model}")
    print("\nRunning evaluation...")

    per_q: list[PerQuestionResult] = []
    started = time.time()
    for i, q in enumerate(questions, 1):
        print(f"  [{i:3d}/{len(questions)}] {q.id:40s} ", end="", flush=True)
        result = run_one(
            q,
            org_id=org_id,
            config_id=config_id,
            coveo_key=search_key,  # generation uses search key (has Execute Query)
            anthropic_client=anthropic_client,
            judge_model=args.judge_model,
            verbose=False,
        )
        marker = "✓" if result.verdict.is_correct else "✗"
        print(f"{marker} (recall={result.hard_recall:.2f})")
        per_q.append(result)

    elapsed = time.time() - started
    print(f"\nCompleted {len(per_q)} questions in {elapsed:.1f}s")

    # Aggregate
    overall = aggregate(per_q)
    layer_stats = by_layer(per_q)

    print("\nResults:")
    print(
        f"  Overall:  accuracy={overall.accuracy:.1%} precision={overall.precision:.1%} hard_recall={overall.hard_recall:.1%}"
    )
    for layer_key, stats in layer_stats.items():
        if stats.n_questions:
            print(
                f"  Layer {layer_key} (n={stats.n_questions}):"
                f" accuracy={stats.accuracy:.1%}"
                f" precision={stats.precision:.1%}"
                f" hard_recall={stats.hard_recall:.1%}"
            )

    # Write output
    run = EvalRun(
        timestamp=datetime.now(UTC).isoformat(),
        coveo_org_id=org_id,
        judge_model=args.judge_model,
        overall=overall,
        by_layer=layer_stats,
        per_question=per_q,
    )
    out_path = write_run(run, mode=mode)
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
