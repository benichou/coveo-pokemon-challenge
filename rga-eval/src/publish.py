"""Write an EvalRun JSON file to eval-runs/ at the repo root.

One file per (day, mode): `eval-runs/YYYY-MM-DD-<mode>.json`. The mode tag
(`full` / `smoke` / `layer{N}`) keeps diagnostic runs from clobbering the
canonical daily full run. The dashboard reads `eval-runs/*.json` at build
time; commit history of this directory IS the time-series database.
"""

from __future__ import annotations

import json
from pathlib import Path

from schemas import EvalRun

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_RUNS_DIR = REPO_ROOT / "eval-runs"


def write_run(run: EvalRun, mode: str = "full") -> Path:
    """Pydantic-serialize the EvalRun and write to eval-runs/YYYY-MM-DD-<mode>.json.

    `mode` is the run kind (`full` / `smoke` / `layer{N}`) and becomes a
    filename suffix so that, e.g., a smoke test does not overwrite the day's
    full run. Returns the output path. If a file for today's date AND mode
    already exists, we overwrite it (a re-run of the same kind on the same day
    replaces the previous output rather than accumulating multiple files).
    """
    EVAL_RUNS_DIR.mkdir(exist_ok=True)
    # ISO 8601 prefix sorts correctly and is a natural filename
    date_prefix = run.timestamp[:10]  # "2026-05-31"
    path = EVAL_RUNS_DIR / f"{date_prefix}-{mode}.json"

    path.write_text(
        json.dumps(run.model_dump(), indent=2, ensure_ascii=False) + "\n"
    )
    return path
