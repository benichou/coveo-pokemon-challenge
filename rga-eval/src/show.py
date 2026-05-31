"""Pretty-print the latest (or a specific) eval-runs JSON for a terminal.

Used by the `/rga-eval` Claude Code skill and as a standalone CLI:

    uv run python src/show.py                  # latest full run
    uv run python src/show.py 2026-05-31       # that date's full run
    uv run python src/show.py 2026-05-31-smoke # a specific dated mode file
    uv run python src/show.py --failures       # latest full run, only failing questions
    uv run python src/show.py --hallu          # latest full run, only hallucinated questions

Runs are stored as eval-runs/YYYY-MM-DD-<mode>.json (mode = full / smoke /
layer{N}). "Latest" and a bare date both prefer the canonical full run; smoke
and layer runs are diagnostic and only surface when named explicitly.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_RUNS_DIR = REPO_ROOT / "eval-runs"


def _prefer_full(files: list[Path]) -> Path | None:
    """Given a sorted list of run files, pick the canonical one.

    Prefer the latest `*-full.json` (the canonical 100-question run); fall
    back to the latest of whatever is present (diagnostic smoke/layer runs, or
    legacy unsuffixed files written before mode tagging).
    """
    if not files:
        return None
    full = [f for f in files if f.stem.endswith("-full")]
    return (full or files)[-1]


def latest_run_path() -> Path | None:
    """Return the latest run, preferring the canonical full run for the day."""
    if not EVAL_RUNS_DIR.exists():
        return None
    return _prefer_full(sorted(EVAL_RUNS_DIR.glob("*.json")))


def resolve_date_path(date: str) -> Path | None:
    """Resolve a date (or dated-mode stem) argument to a run file.

    - "2026-05-31-smoke" / "2026-05-31-full" -> that exact file.
    - "2026-05-31" -> that day's full run, else any run for the day, else the
      legacy unsuffixed 2026-05-31.json.
    """
    exact = EVAL_RUNS_DIR / f"{date}.json"
    if exact.exists():
        return exact
    return _prefer_full(sorted(EVAL_RUNS_DIR.glob(f"{date}-*.json")))


def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def print_summary(run: dict) -> None:
    print("=" * 66)
    print(f"RGA Eval — {run['timestamp']}")
    print(f"Judge model: {run['judge_model']}")
    print("=" * 66)
    overall = run["overall"]
    print("\nOverall")
    print(f"  Accuracy:           {fmt_pct(overall['accuracy'])}")
    print(f"  Precision:          {fmt_pct(overall['precision'])}")
    print(f"  Hard recall:        {fmt_pct(overall['hard_recall'])}")
    print(f"  Citation precision: {fmt_pct(overall['citation_precision'])}")
    print(f"  Total questions:    {overall['n_questions']}")

    print("\nBy layer")
    layer_labels = {
        "1": "Layer 1 — single fact",
        "2": "Layer 2 — multi-doc synthesis",
        "3": "Layer 3 — edge cases",
    }
    for key in ["1", "2", "3"]:
        stats = run["by_layer"].get(key)
        if not stats or stats["n_questions"] == 0:
            continue
        print(
            f"  {layer_labels[key]:32s} "
            f"(n={stats['n_questions']:3d})  "
            f"acc={fmt_pct(stats['accuracy'])}  "
            f"prec={fmt_pct(stats['precision'])}  "
            f"recall={fmt_pct(stats['hard_recall'])}"
        )


def print_category_breakdown(run: dict) -> None:
    """Group failures + hallucinations by category."""
    per_q = run["per_question"]
    failed = [r for r in per_q if not r["verdict"]["is_correct"]]
    hallu = [r for r in per_q if r["verdict"]["has_hallucination"]]

    print(f"\nFailures by category ({len(failed)} / {len(per_q)} total)")
    by_cat: Counter[str] = Counter()
    for r in failed:
        by_cat[f"L{r['layer']} {r['category']}"] += 1
    for cat, n in by_cat.most_common():
        print(f"  {n:2d}  {cat}")

    print(f"\nHallucinations by category ({len(hallu)} / {len(per_q)})")
    by_cat = Counter()
    for r in hallu:
        by_cat[f"L{r['layer']} {r['category']}"] += 1
    for cat, n in by_cat.most_common():
        print(f"  {n:2d}  {cat}")


def print_failures_detail(run: dict, hallu_only: bool = False) -> None:
    """Print each failing (or hallucinated) question with its judge reasoning."""
    per_q = run["per_question"]
    if hallu_only:
        rows = [r for r in per_q if r["verdict"]["has_hallucination"]]
        header = "Hallucinated questions"
    else:
        rows = [r for r in per_q if not r["verdict"]["is_correct"]]
        header = "Failing questions"

    print(f"\n{header} ({len(rows)} total)")
    print("-" * 66)
    for r in rows:
        marker = "💥" if r["verdict"]["has_hallucination"] else "✗"
        print(
            f"\n{marker}  [{r['question_id']}] (L{r['layer']} {r['category']})"
        )
        print(f"    Q: {r['question']}")
        if r["answer_text"]:
            preview = r["answer_text"][:200].replace("\n", " ")
            print(
                f"    A: {preview}{'...' if len(r['answer_text']) > 200 else ''}"
            )
        else:
            print("    A: (no answer produced)")
        print(
            f"    recall={r['hard_recall']:.2f}  "
            f"is_correct={r['verdict']['is_correct']}  "
            f"hallu={r['verdict']['has_hallucination']}"
        )
        print(f"    Judge: {r['verdict']['reasoning']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "date",
        nargs="?",
        default=None,
        help="Date prefix YYYY-MM-DD (default: latest)",
    )
    ap.add_argument(
        "--failures",
        action="store_true",
        help="Show details of every failing question",
    )
    ap.add_argument(
        "--hallu",
        action="store_true",
        help="Show details of every hallucinated question",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Just the summary header + numbers, no category/failure breakdown",
    )
    args = ap.parse_args()

    path = resolve_date_path(args.date) if args.date else latest_run_path()

    if not path or not path.exists():
        print(
            "No eval runs found in eval-runs/. Run an eval first:",
            file=sys.stderr,
        )
        print("  cd rga-eval && uv run python src/main.py", file=sys.stderr)
        return 1

    run = json.loads(path.read_text())

    print_summary(run)
    if not args.quiet:
        print_category_breakdown(run)

    if args.failures:
        print_failures_detail(run, hallu_only=False)
    elif args.hallu:
        print_failures_detail(run, hallu_only=True)

    print(f"\nSource: {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
