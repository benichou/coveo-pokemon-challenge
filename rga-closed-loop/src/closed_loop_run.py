"""Phase 6F.5 — closed-loop orchestrator for the auto-apply cron.

This is the script the GitHub Actions cron invokes. It chains:

  1. Rollback check FIRST — if the previous apply caused a big regression,
     auto-revert from prompts/history/<last replaces>.yaml and exit.
  2. Otherwise, run the analyzer (analyzer.py) on the latest eval.
  3. Evaluate guardrails (guardrails.py). If any fail, log and exit clean.
  4. Otherwise apply: archive current YAML, write new YAML, run apply.py
     against Coveo, verify via re-fetch.

What this script writes:
  - Mutates rga-closed-loop/prompts/pokemon-rga.yaml on successful apply.
  - Adds a new file to rga-closed-loop/prompts/history/ on every apply.
  - Logs every run (skip + success + rollback) to logs/closed-loop/.
  - Does NOT commit/push. That's the workflow's job — keeps the orchestrator
    git-agnostic + locally-runnable.

CLI:
  uv run python src/closed_loop_run.py                   # full cycle
  uv run python src/closed_loop_run.py --dry-run         # analyze + guard, no apply
  uv run python src/closed_loop_run.py --skip-analyzer   # skip analyzer; only do rollback-check
  uv run python src/closed_loop_run.py --no-rollback-check  # skip rollback step
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml
from analyzer import (
    JUDGE_MODEL,
    call_analyzer,
    list_full_runs,
    load_current_prompt,
    rank_worst_categories,
    sample_failures,
    summarize_run,
)
from guardrails import (
    all_passed,
    check_rollback_needed,
    evaluate_all,
    render_summary,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PACKAGE_ROOT / "prompts"
HISTORY_DIR = PROMPTS_DIR / "history"
CURRENT_YAML = PROMPTS_DIR / "pokemon-rga.yaml"
EVAL_RUNS_DIR = REPO_ROOT / "eval-runs"
LOGS_DIR = REPO_ROOT / "logs" / "closed-loop"

# Exit codes — read by the GitHub Actions workflow to decide what to commit.
EXIT_NO_CHANGE = 0  # Guard failed OR no proposal; clean exit; nothing to commit
EXIT_APPLIED = (
    10  # Successfully applied a change; YAML + history/ have new content
)
EXIT_ROLLED_BACK = (
    11  # Auto-rollback executed; YAML + history/ have new content
)
EXIT_ERROR = 1  # Hard error; abort the workflow


# ---------- Logging ----------


def log_run(payload: dict) -> Path:
    """Write a JSON log of this run to logs/closed-loop/YYYY-MM-DDTHH-MM-SS.json."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    path = LOGS_DIR / f"{ts}.json"
    # Trailing newline keeps the file POSIX-compliant and prevents the daily
    # cron's auto-commits from later failing the repo's end-of-file-fixer
    # pre-commit hook (the cron commits without running pre-commit locally).
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path


# ---------- YAML mutation ----------


def bump_minor_version(version: str) -> str:
    """1.0.0 → 1.1.0; preserve major. Reset patch to 0."""
    parts = version.split(".")
    if len(parts) != 3:
        return f"{version}+1"
    return f"{parts[0]}.{int(parts[1]) + 1}.0"


def write_new_yaml(
    proposal_dict: dict,
    history_filename: str,
    *,
    applied_by: str,
) -> None:
    """Mutate prompts/pokemon-rga.yaml in place with the proposal's content + new metadata."""
    current = yaml.safe_load(CURRENT_YAML.read_text())
    current["prompt"] = proposal_dict["new_prompt"]
    current["metadata"]["version"] = bump_minor_version(
        current["metadata"]["version"]
    )
    current["metadata"]["applied_at"] = datetime.now(UTC).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    current["metadata"]["applied_by"] = applied_by
    current["metadata"]["replaces"] = f"history/{history_filename}"
    current["metadata"]["rationale"] = proposal_dict.get("rationale", "")
    # ExpectedLift dicts shape: {"from": float, "target": float}
    new_lift = {}
    for metric, lift in proposal_dict.get("expected_lift", {}).items():
        from_v = lift.get("from") if "from" in lift else lift.get("from_")
        new_lift[metric] = {"from": from_v, "target": lift["target"]}
    current["metadata"]["expected_lift"] = new_lift
    current["metadata"]["validated_against"] = ""
    CURRENT_YAML.write_text(
        yaml.safe_dump(current, sort_keys=False, allow_unicode=True, width=120)
    )


def archive_current_yaml(slug: str) -> str:
    """Copy current YAML to history/YYYY-MM-DD-<slug>.yaml. Returns the new filename."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    filename = f"{today}-{slug}.yaml"
    # Avoid clobbering an existing same-day archive
    n = 2
    while (HISTORY_DIR / filename).exists():
        filename = f"{today}-{slug}-v{n}.yaml"
        n += 1
    shutil.copy(CURRENT_YAML, HISTORY_DIR / filename)
    return filename


def run_apply_py(force: bool = False) -> int:
    """Invoke apply.py as a subprocess. Returns exit code."""
    args = ["uv", "run", "python", "src/apply.py", "--apply"]
    if force:
        args.append("--force")
    result = subprocess.run(
        args,
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


# ---------- Rollback ----------


def do_rollback(current_md, log_payload: dict) -> int:
    """Restore the YAML pointed to by current_md.replaces. Returns an exit code."""
    if not current_md.replaces:
        log_payload["rollback_skipped"] = (
            "current metadata has no `replaces` pointer"
        )
        return EXIT_NO_CHANGE

    target = PACKAGE_ROOT / current_md.replaces
    if not target.exists():
        log_payload["rollback_failed"] = f"history file not found: {target}"
        return EXIT_ERROR

    # Archive the (bad) current YAML to history/ before overwriting
    bad_archive = archive_current_yaml("rollback-from")

    # Read the target (the good previous version) and reset its metadata
    # to mark it as the new live state under a rollback identity
    prev = yaml.safe_load(target.read_text())
    prev["metadata"]["version"] = bump_minor_version(
        prev["metadata"]["version"]
    )
    prev["metadata"]["applied_at"] = datetime.now(UTC).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    prev["metadata"]["applied_by"] = "auto-rollback (closed-loop cron)"
    prev["metadata"]["replaces"] = f"history/{bad_archive}"
    prev["metadata"]["rationale"] = (
        "Automatic rollback. The previous apply was followed by a >5pt "
        "drop in overall_accuracy on the next-day eval. Restoring the prior "
        "version. The version this rollback returns to is preserved; the "
        "rolled-back-from YAML is archived as " + bad_archive + "."
    )
    prev["metadata"]["expected_lift"] = {}
    prev["metadata"]["validated_against"] = ""
    CURRENT_YAML.write_text(
        yaml.safe_dump(prev, sort_keys=False, allow_unicode=True, width=120)
    )
    log_payload["rollback_yaml_target"] = current_md.replaces
    log_payload["rollback_archive_bad_as"] = bad_archive

    # Apply (force, because we want to PUT even though the body just changed)
    rc = run_apply_py(force=False)
    log_payload["rollback_apply_returncode"] = rc
    if rc != 0:
        return EXIT_ERROR
    return EXIT_ROLLED_BACK


# ---------- Main orchestrator ----------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Run analyzer + guards but skip the apply step.",
    )
    ap.add_argument(
        "--skip-analyzer",
        action="store_true",
        help="Only check rollback. Useful for a low-cost daily safety check.",
    )
    ap.add_argument(
        "--no-rollback-check",
        action="store_true",
        help="Skip the rollback safety check. Reserved for the first-ever cron run.",
    )
    args = ap.parse_args()

    log_payload: dict = {
        "started_at": datetime.now(UTC).isoformat(),
        "args": vars(args),
        "exit_code": None,
    }

    # ---------- Setup ----------
    runs = list_full_runs(EVAL_RUNS_DIR)
    if not runs:
        print(
            "ERROR: no eval-runs/*-full.json files. Run the eval first.",
            file=sys.stderr,
        )
        log_payload["error"] = "no eval-runs"
        log_run(log_payload)
        return EXIT_ERROR

    latest_path = runs[-1]
    prior_path = runs[-2] if len(runs) >= 2 else None

    latest_summary, latest_perq = summarize_run(latest_path)
    prior_summary = summarize_run(prior_path)[0] if prior_path else None

    log_payload["latest_run"] = latest_path.name
    log_payload["prior_run"] = prior_path.name if prior_path else None
    log_payload["latest_overall_accuracy"] = latest_summary.overall_accuracy

    current_pv = load_current_prompt()
    current_md = current_pv.metadata
    log_payload["current_yaml_version"] = current_md.version

    # ---------- Step 1: rollback check ----------
    if args.no_rollback_check:
        print("→ Skipping rollback check (--no-rollback-check).")
    elif prior_summary is None:
        print(
            "→ No prior eval run — skipping rollback check (nothing to compare against)."
        )
    else:
        print("→ Checking auto-rollback decision...")
        decision = check_rollback_needed(
            latest_overall_accuracy=latest_summary.overall_accuracy,
            prior_overall_accuracy=prior_summary.overall_accuracy,
            current_metadata=current_md,
        )
        log_payload["rollback_decision"] = {
            "should_rollback": decision.should_rollback,
            "reason": decision.reason,
            "accuracy_drop_pts": decision.accuracy_drop_pts,
        }
        print(f"  {decision.reason}")

        if decision.should_rollback:
            if args.dry_run:
                print("\n[dry-run] Rollback WOULD execute. Skipping.")
                log_payload["exit_code"] = EXIT_NO_CHANGE
                log_run(log_payload)
                return EXIT_NO_CHANGE
            print("\n→ Executing auto-rollback...")
            rc = do_rollback(current_md, log_payload)
            log_payload["exit_code"] = rc
            log_run(log_payload)
            return rc

    # ---------- Step 2: analyzer (skip if --skip-analyzer or proposed for rollback) ----------
    if args.skip_analyzer:
        print(
            "→ --skip-analyzer set; exiting (rollback check was the only goal)."
        )
        log_payload["exit_code"] = EXIT_NO_CHANGE
        log_run(log_payload)
        return EXIT_NO_CHANGE

    print("\n→ Running analyzer (LLM call — Sonnet 4.6)...")
    worst = rank_worst_categories(latest_summary, prior_summary, top_n=3)
    failing = sample_failures(latest_perq, worst, per_category=3)
    try:
        proposal = call_analyzer(
            current_pv.prompt.strip(),
            latest_summary,
            prior_summary,
            worst,
            failing,
            model=JUDGE_MODEL,
        )
    except Exception as e:
        print(f"ERROR: analyzer call failed: {e}", file=sys.stderr)
        log_payload["error"] = f"analyzer failed: {e}"
        log_payload["exit_code"] = EXIT_ERROR
        log_run(log_payload)
        return EXIT_ERROR

    log_payload["proposal_confidence"] = proposal.confidence
    log_payload["proposal_new_prompt_chars"] = len(proposal.new_prompt)
    log_payload["proposal_rationale_first200"] = proposal.rationale[:200]

    # ---------- Step 3: guardrails ----------
    print("\n→ Evaluating guardrails...")
    results = evaluate_all(
        proposal,
        current_prompt=current_pv.prompt.strip(),
        current_metadata=current_md,
    )
    print(render_summary(results))
    log_payload["guardrails"] = [
        {"name": r.name, "passed": r.passed, "reason": r.reason}
        for r in results
    ]

    if not all_passed(results):
        print("\n→ One or more guards failed. Skipping apply.")
        log_payload["exit_code"] = EXIT_NO_CHANGE
        log_run(log_payload)
        return EXIT_NO_CHANGE

    if args.dry_run:
        print(
            "\n[dry-run] All guards passed but --dry-run set. Skipping apply."
        )
        log_payload["exit_code"] = EXIT_NO_CHANGE
        log_run(log_payload)
        return EXIT_NO_CHANGE

    # ---------- Step 4: apply ----------
    print(
        "\n→ All guards passed. Archiving current YAML + writing new prompt..."
    )
    slug = f"pre-cron-v{current_md.version}"
    history_filename = archive_current_yaml(slug)
    log_payload["archived_to"] = history_filename

    write_new_yaml(
        proposal.model_dump(),
        history_filename=history_filename,
        applied_by=(
            f"closed-loop cron (analyzer Sonnet 4.6, "
            f"confidence={proposal.confidence:.2f})"
        ),
    )
    log_payload["new_yaml_version"] = yaml.safe_load(CURRENT_YAML.read_text())[
        "metadata"
    ]["version"]

    print("\n→ Running apply.py --apply against Coveo...")
    rc = run_apply_py()
    log_payload["apply_returncode"] = rc

    if rc != 0:
        print(
            "\n✗ apply.py failed. Working tree has the new YAML but live Coveo is NOT updated.",
            file=sys.stderr,
        )
        log_payload["exit_code"] = EXIT_ERROR
        log_run(log_payload)
        return EXIT_ERROR

    print("\n✓ Closed-loop cycle complete: analyzer → guard → apply → verify.")
    log_payload["exit_code"] = EXIT_APPLIED
    log_run(log_payload)
    return EXIT_APPLIED


if __name__ == "__main__":
    sys.exit(main())
