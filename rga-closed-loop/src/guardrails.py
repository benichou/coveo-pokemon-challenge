"""Phase 6F.6 — guardrails for the auto-apply closed-loop cron.

Pure functions that decide whether a proposed prompt change is safe to
ship without human review. Each guard returns a GuardResult with
(passed, reason). The cron orchestrator (closed_loop_run.py) runs them
all and applies the proposal only if every guard passes.

Design principles:
  - Pure functions only. No I/O, no LLM calls. Trivially unit-testable.
  - Conservative defaults. Easier to relax later than to clean up after
    a runaway auto-apply.
  - Fail loud. Every guard returns a `reason` string that the
    orchestrator logs even on success, so the run history is auditable.

Guard menu:
  - check_confidence       — analyzer's self-rated confidence ≥ threshold
  - check_no_op            — proposal differs from current prompt
  - check_lift_threshold   — predicted overall_accuracy lift ≥ +N pts
  - check_sanity           — prompt length + required anchor phrases
  - check_rate_limit       — last apply was ≥ N days ago

Separately:
  - check_rollback_needed  — does the latest eval indicate a regression
                             from the last apply that should auto-revert?

The cron flow is:
  rollback-check → (rollback OR continue) → analyze → guard → apply
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from schemas import PromptMetadata, PromptProposal

# ---------- Result shapes ----------


@dataclass
class GuardResult:
    """One guard's verdict + audit trail."""

    name: str
    passed: bool
    reason: str

    def __str__(self) -> str:
        marker = "✓" if self.passed else "✗"
        return f"{marker} {self.name}: {self.reason}"


@dataclass
class RollbackDecision:
    """Whether the last apply needs to be auto-reverted."""

    should_rollback: bool
    reason: str
    accuracy_drop_pts: float = 0.0


# ---------- Individual guards ----------


def check_confidence(
    proposal: PromptProposal,
    *,
    min_confidence: float = 0.80,
) -> GuardResult:
    """Analyzer's self-rated confidence must clear the threshold.

    Tuning notes:
      0.80 is a reasonable default — high enough to filter out "vibes-based"
      suggestions, low enough that a well-reasoned change usually passes.
      Tighten to 0.85 if the cron is making too many marginal changes;
      relax to 0.70 if the cron is too quiet.
    """
    if proposal.confidence < min_confidence:
        return GuardResult(
            "confidence",
            False,
            f"analyzer confidence {proposal.confidence:.2f} < threshold {min_confidence:.2f}",
        )
    return GuardResult(
        "confidence",
        True,
        f"analyzer confidence {proposal.confidence:.2f} ≥ threshold {min_confidence:.2f}",
    )


def check_no_op(
    proposal: PromptProposal,
    current_prompt: str,
) -> GuardResult:
    """Skip the apply if the proposed prompt is identical to the current one.

    The analyzer is allowed to return "no change needed" (we documented this
    in its system prompt). When it does, we treat the proposal as a no-op and
    don't waste a Coveo API call.
    """
    if proposal.new_prompt.strip() == current_prompt.strip():
        return GuardResult(
            "no_op",
            False,
            "proposed prompt is identical to current — analyzer says no change needed",
        )
    return GuardResult(
        "no_op",
        True,
        "proposed prompt differs from current",
    )


def check_lift_threshold(
    proposal: PromptProposal,
    *,
    min_lift_pts: float = 0.05,
    metric: str = "overall_accuracy",
) -> GuardResult:
    """Predicted overall-accuracy lift must clear a minimum.

    Prevents tiny refinements that churn the prompt without meaningful
    expected impact. Default +5 pts is a reasonable "worth shipping" bar.
    If the analyzer predicts only +2 pts, the change is more likely noise
    than signal — wait for a stronger proposal.

    If the analyzer didn't include the named metric, the guard passes
    (no information ≠ negative information).
    """
    lift = proposal.expected_lift.get(metric)
    if lift is None:
        return GuardResult(
            "lift_threshold",
            True,
            f"no '{metric}' lift predicted by analyzer — guard skipped",
        )
    delta = lift.target - lift.from_
    if delta < min_lift_pts:
        return GuardResult(
            "lift_threshold",
            False,
            (
                f"predicted {metric} lift {delta:+.1%} below threshold "
                f"+{min_lift_pts:.1%}"
            ),
        )
    return GuardResult(
        "lift_threshold",
        True,
        f"predicted {metric} lift {delta:+.1%} ≥ threshold +{min_lift_pts:.1%}",
    )


# Anchor phrases the prompt MUST contain — protects against the analyzer
# silently dropping the grounding/citation discipline. These are case-insensitive
# substring checks; pick phrases that are very unlikely to disappear from any
# reasonable Pokemon-grounded prompt.
REQUIRED_ANCHORS = (
    "retrieved",  # must mention retrieved/retrieval — grounding discipline
    "source",  # must reference sources
)

# Length floor. The original Pokemon prompt is ~1200 chars; the analyzer-refined
# one is ~1900. A 500-char floor catches "you are a helpful assistant"-style
# collapses without being so tight it rejects legitimate refinements.
MIN_PROMPT_LENGTH = 500


def check_sanity(proposal: PromptProposal) -> GuardResult:
    """Structural checks: prompt isn't suspiciously short OR missing anchors.

    Catches catastrophic analyzer failures (e.g., model returned a default
    "You are a helpful assistant" string). NOT a semantic check — the
    analyzer's own model is responsible for semantics. This is the
    "sanity check before we ship" layer.
    """
    if len(proposal.new_prompt) < MIN_PROMPT_LENGTH:
        return GuardResult(
            "sanity",
            False,
            (
                f"prompt suspiciously short: {len(proposal.new_prompt)} chars "
                f"< floor {MIN_PROMPT_LENGTH}. Possible analyzer collapse."
            ),
        )
    lower = proposal.new_prompt.lower()
    missing = [a for a in REQUIRED_ANCHORS if a not in lower]
    if missing:
        return GuardResult(
            "sanity",
            False,
            (
                f"prompt missing required anchor phrases {missing}. "
                f"Possible grounding discipline lost."
            ),
        )
    return GuardResult(
        "sanity",
        True,
        f"length {len(proposal.new_prompt)} chars; all anchors present",
    )


def check_rate_limit(
    current_metadata: PromptMetadata,
    *,
    min_days_since_apply: int = 3,
    now: datetime | None = None,
) -> GuardResult:
    """The last apply must be at least N days old.

    Prevents the cron from churning the prompt every day, which would compound
    bad analyzer outputs and produce a noisy time-series. Three days is a
    reasonable default — gives the dashboard time to show a stable signal
    on the new prompt before another change.

    Manual applies via the /rga-closed-loop skill don't reset this clock —
    the metadata.applied_at field is what's compared, regardless of who
    applied it.
    """
    if now is None:
        now = datetime.now(UTC)
    try:
        applied = datetime.fromisoformat(
            current_metadata.applied_at.replace("Z", "+00:00")
        )
    except (ValueError, AttributeError):
        # Bad timestamp = treat as ancient (don't block on a parse error)
        return GuardResult(
            "rate_limit",
            True,
            f"could not parse applied_at={current_metadata.applied_at!r}; "
            "treating as long-ago",
        )
    age = now - applied
    threshold = timedelta(days=min_days_since_apply)
    if age < threshold:
        days_left = (threshold - age).total_seconds() / 86400
        return GuardResult(
            "rate_limit",
            False,
            (
                f"last apply was {age.days}d {age.seconds // 3600}h ago "
                f"(< {min_days_since_apply}d threshold; "
                f"{days_left:.1f}d until next eligible)"
            ),
        )
    return GuardResult(
        "rate_limit",
        True,
        f"last apply was {age.days}d {age.seconds // 3600}h ago "
        f"(≥ {min_days_since_apply}d threshold)",
    )


# ---------- Orchestration helpers ----------


def evaluate_all(
    proposal: PromptProposal,
    current_prompt: str,
    current_metadata: PromptMetadata,
    *,
    min_confidence: float = 0.80,
    min_lift_pts: float = 0.05,
    min_days_since_apply: int = 3,
    now: datetime | None = None,
) -> list[GuardResult]:
    """Run every guard. Return all results — caller decides on action."""
    return [
        check_no_op(proposal, current_prompt),
        check_confidence(proposal, min_confidence=min_confidence),
        check_lift_threshold(proposal, min_lift_pts=min_lift_pts),
        check_sanity(proposal),
        check_rate_limit(
            current_metadata,
            min_days_since_apply=min_days_since_apply,
            now=now,
        ),
    ]


def all_passed(results: list[GuardResult]) -> bool:
    return all(r.passed for r in results)


def render_summary(results: list[GuardResult]) -> str:
    """Multi-line audit string of every guard's verdict."""
    return "\n".join(str(r) for r in results)


# ---------- Auto-rollback ----------


def check_rollback_needed(
    latest_overall_accuracy: float,
    prior_overall_accuracy: float,
    current_metadata: PromptMetadata,
    *,
    max_drop_pts: float = 0.05,
    rollback_window_hours: int = 36,
    now: datetime | None = None,
) -> RollbackDecision:
    """Decide whether the last apply needs to be auto-reverted.

    Two conditions must both hold:

      1. The last apply landed within `rollback_window_hours` ago.
         Default 36h means we only rollback the CURRENT prompt — we don't
         rollback a 3-day-old prompt because today's eval looks bad
         (that bad result probably has a different cause).

      2. Overall accuracy dropped by more than `max_drop_pts` vs the
         immediately-prior eval run. Default 5pts means we tolerate
         normal LLM-judge variance (~2pts) but catch a genuine regression.

    When both conditions hold, the orchestrator should:
      - Read current_metadata.replaces (path to the previous YAML in history/)
      - Copy that file over prompts/pokemon-rga.yaml
      - Update metadata (applied_by="auto-rollback", reason=...)
      - Run apply.py --apply
      - Commit + push

    Notes:
      - This guard only LOOKS at the data. The orchestrator does the act.
      - The orchestrator should skip the analyzer step entirely on rollback
        runs (you don't want analyzer-on-analyzer compounding).
    """
    if now is None:
        now = datetime.now(UTC)

    drop = prior_overall_accuracy - latest_overall_accuracy

    # Condition 1: recent apply?
    try:
        applied = datetime.fromisoformat(
            current_metadata.applied_at.replace("Z", "+00:00")
        )
    except (ValueError, AttributeError):
        return RollbackDecision(
            False,
            f"could not parse applied_at={current_metadata.applied_at!r}; "
            "cannot decide on rollback",
            accuracy_drop_pts=drop,
        )

    age = now - applied
    if age > timedelta(hours=rollback_window_hours):
        return RollbackDecision(
            False,
            (
                f"last apply was {age.days}d {age.seconds // 3600}h ago "
                f"(> {rollback_window_hours}h rollback window). Today's "
                f"regression has a different cause; no rollback."
            ),
            accuracy_drop_pts=drop,
        )

    # Condition 2: accuracy drop?
    if drop < max_drop_pts:
        return RollbackDecision(
            False,
            (
                f"overall accuracy drop {drop:+.1%} within tolerance "
                f"(threshold > {max_drop_pts:.1%}). No rollback."
            ),
            accuracy_drop_pts=drop,
        )

    # Both conditions met
    return RollbackDecision(
        True,
        (
            f"overall accuracy dropped {drop:+.1%} (> {max_drop_pts:.1%} threshold) "
            f"after a recent apply ({age.days}d {age.seconds // 3600}h ago, "
            f"within {rollback_window_hours}h window). Rolling back to "
            f"{current_metadata.replaces!r}."
        ),
        accuracy_drop_pts=drop,
    )
