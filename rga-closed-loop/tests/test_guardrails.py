"""Unit tests for src/guardrails.py — pure functions, zero I/O.

Covers each guard's pass + fail cases plus the auto-rollback decision.
"""

from __future__ import annotations

from datetime import UTC, datetime

from guardrails import (
    MIN_PROMPT_LENGTH,
    REQUIRED_ANCHORS,
    all_passed,
    check_confidence,
    check_lift_threshold,
    check_no_op,
    check_rate_limit,
    check_rollback_needed,
    check_sanity,
    evaluate_all,
)
from schemas import ExpectedLift, PromptMetadata, PromptProposal

# ---------- Fixtures ----------


def make_proposal(
    *,
    new_prompt: str = "A" * 600 + " retrieved source content",
    confidence: float = 0.85,
    overall_lift: tuple[float, float] | None = (0.62, 0.78),
) -> PromptProposal:
    expected_lift: dict[str, ExpectedLift] = {}
    if overall_lift is not None:
        # Note: pydantic accepts the `from_` alias internally
        expected_lift["overall_accuracy"] = ExpectedLift(
            from_=overall_lift[0], target=overall_lift[1]
        )
    return PromptProposal(
        new_prompt=new_prompt,
        rationale="test rationale",
        expected_lift=expected_lift,
        sample_answers=[],
        confidence=confidence,
    )


def make_metadata(
    *,
    applied_at: str = "2026-05-01T00:00:00Z",  # ancient by default
    replaces: str = "history/2026-04-30-old.yaml",
) -> PromptMetadata:
    return PromptMetadata(
        version="1.0.0",
        applied_at=applied_at,
        applied_by="test",
        replaces=replaces,
        rationale="test",
        expected_lift={},
        validated_against="",
        related_eval_run="",
        related_methodology="",
    )


# ---------- check_confidence ----------


def test_confidence_passes_above_threshold() -> None:
    r = check_confidence(make_proposal(confidence=0.85))
    assert r.passed
    assert "0.85" in r.reason


def test_confidence_fails_below_threshold() -> None:
    r = check_confidence(make_proposal(confidence=0.60))
    assert not r.passed
    assert "0.60" in r.reason


def test_confidence_boundary_at_threshold() -> None:
    # Exactly 0.80 should pass (>=).
    r = check_confidence(make_proposal(confidence=0.80))
    assert r.passed


def test_confidence_custom_threshold() -> None:
    r = check_confidence(make_proposal(confidence=0.85), min_confidence=0.90)
    assert not r.passed


# ---------- check_no_op ----------


def test_no_op_fails_when_proposal_matches_current() -> None:
    p = make_proposal(new_prompt="A" * 600 + " retrieved source")
    r = check_no_op(p, current_prompt="A" * 600 + " retrieved source")
    assert not r.passed
    assert "identical" in r.reason


def test_no_op_passes_when_proposal_differs() -> None:
    p = make_proposal(new_prompt="A" * 600 + " retrieved source NEW")
    r = check_no_op(p, current_prompt="A" * 600 + " retrieved source")
    assert r.passed


def test_no_op_ignores_leading_trailing_whitespace() -> None:
    p = make_proposal(new_prompt="  hello  retrieved source  ")
    r = check_no_op(p, current_prompt="hello  retrieved source")
    assert not r.passed


# ---------- check_lift_threshold ----------


def test_lift_passes_above_threshold() -> None:
    # +16pts predicted lift
    r = check_lift_threshold(make_proposal(overall_lift=(0.62, 0.78)))
    assert r.passed


def test_lift_fails_below_threshold() -> None:
    # +2pts predicted lift
    r = check_lift_threshold(make_proposal(overall_lift=(0.62, 0.64)))
    assert not r.passed


def test_lift_passes_when_metric_absent() -> None:
    # No information ≠ negative information
    r = check_lift_threshold(make_proposal(overall_lift=None))
    assert r.passed
    assert "skipped" in r.reason.lower()


def test_lift_custom_threshold_and_metric() -> None:
    p = make_proposal(overall_lift=None)
    p.expected_lift["ability_lookup"] = ExpectedLift(from_=0.10, target=0.30)
    r = check_lift_threshold(p, min_lift_pts=0.10, metric="ability_lookup")
    assert r.passed  # +20pts ≥ +10pts


# ---------- check_sanity ----------


def test_sanity_fails_when_too_short() -> None:
    r = check_sanity(make_proposal(new_prompt="too short retrieved source"))
    assert not r.passed
    assert "short" in r.reason.lower()


def test_sanity_fails_when_anchor_missing() -> None:
    # Long enough but no "source" anchor
    r = check_sanity(make_proposal(new_prompt="X" * 700 + " retrieved"))
    assert not r.passed
    assert "anchor" in r.reason.lower()


def test_sanity_passes_when_long_and_has_anchors() -> None:
    r = check_sanity(make_proposal())  # default has both anchors and is long
    assert r.passed


def test_sanity_anchors_are_case_insensitive() -> None:
    r = check_sanity(make_proposal(new_prompt="A" * 600 + " RETRIEVED SOURCE"))
    assert r.passed


def test_sanity_floor_value_matches_constant() -> None:
    # Sanity check on the test itself: MIN_PROMPT_LENGTH is what we expect
    assert MIN_PROMPT_LENGTH == 500


def test_sanity_anchors_include_expected() -> None:
    # Don't fragment the test if someone tightens the list
    assert "retrieved" in REQUIRED_ANCHORS
    assert "source" in REQUIRED_ANCHORS


# ---------- check_rate_limit ----------


def test_rate_limit_passes_when_apply_is_old() -> None:
    md = make_metadata(applied_at="2026-05-01T00:00:00Z")
    now = datetime(2026, 6, 1, tzinfo=UTC)  # 31 days later
    r = check_rate_limit(md, now=now)
    assert r.passed


def test_rate_limit_fails_when_apply_is_recent() -> None:
    md = make_metadata(applied_at="2026-06-01T00:00:00Z")
    now = datetime(2026, 6, 1, 12, tzinfo=UTC)  # 12 hours later
    r = check_rate_limit(md, now=now)
    assert not r.passed
    assert "until next eligible" in r.reason


def test_rate_limit_boundary_at_threshold() -> None:
    # Exactly 3 days later → passes (>=)
    md = make_metadata(applied_at="2026-05-29T00:00:00Z")
    now = datetime(2026, 6, 1, tzinfo=UTC)
    r = check_rate_limit(md, now=now, min_days_since_apply=3)
    assert r.passed


def test_rate_limit_handles_bad_timestamp() -> None:
    md = make_metadata(applied_at="not-a-timestamp")
    r = check_rate_limit(md, now=datetime(2026, 6, 1, tzinfo=UTC))
    assert r.passed  # treats as ancient — don't block on parse error
    assert "could not parse" in r.reason


# ---------- evaluate_all ----------


def test_evaluate_all_returns_one_result_per_guard() -> None:
    p = make_proposal()
    md = make_metadata()
    results = evaluate_all(p, "current prompt", md)
    assert len(results) == 5
    names = {r.name for r in results}
    assert names == {
        "no_op",
        "confidence",
        "lift_threshold",
        "sanity",
        "rate_limit",
    }


def test_all_passed_aggregator() -> None:
    p = make_proposal()
    md = make_metadata()
    results = evaluate_all(p, "different current prompt", md)
    assert all_passed(results)


def test_all_passed_returns_false_if_any_fails() -> None:
    p = make_proposal(confidence=0.10)  # confidence guard will fail
    md = make_metadata()
    results = evaluate_all(p, "different current prompt", md)
    assert not all_passed(results)


# ---------- check_rollback_needed ----------


def test_rollback_triggered_when_recent_apply_and_big_drop() -> None:
    md = make_metadata(applied_at="2026-06-01T00:00:00Z")
    now = datetime(2026, 6, 2, tzinfo=UTC)  # 1 day later, well within window
    decision = check_rollback_needed(
        latest_overall_accuracy=0.55,  # dropped 7pts
        prior_overall_accuracy=0.62,
        current_metadata=md,
        now=now,
    )
    assert decision.should_rollback
    assert decision.accuracy_drop_pts > 0.05


def test_no_rollback_when_drop_is_small() -> None:
    md = make_metadata(applied_at="2026-06-01T00:00:00Z")
    now = datetime(2026, 6, 2, tzinfo=UTC)
    decision = check_rollback_needed(
        latest_overall_accuracy=0.60,  # only -2pts (judge variance)
        prior_overall_accuracy=0.62,
        current_metadata=md,
        now=now,
    )
    assert not decision.should_rollback
    assert "tolerance" in decision.reason


def test_no_rollback_when_apply_is_old() -> None:
    # Big drop, but the apply was a week ago — not caused by it
    md = make_metadata(applied_at="2026-05-20T00:00:00Z")
    now = datetime(2026, 6, 1, tzinfo=UTC)
    decision = check_rollback_needed(
        latest_overall_accuracy=0.50,  # -12pts
        prior_overall_accuracy=0.62,
        current_metadata=md,
        now=now,
    )
    assert not decision.should_rollback
    assert "different cause" in decision.reason


def test_no_rollback_when_accuracy_improved() -> None:
    # Accuracy went UP — definitely no rollback
    md = make_metadata(applied_at="2026-06-01T00:00:00Z")
    now = datetime(2026, 6, 2, tzinfo=UTC)
    decision = check_rollback_needed(
        latest_overall_accuracy=0.78,
        prior_overall_accuracy=0.62,
        current_metadata=md,
        now=now,
    )
    assert not decision.should_rollback
    assert decision.accuracy_drop_pts < 0


def test_rollback_handles_bad_timestamp_gracefully() -> None:
    md = make_metadata(applied_at="garbage")
    decision = check_rollback_needed(
        latest_overall_accuracy=0.40,
        prior_overall_accuracy=0.80,
        current_metadata=md,
        now=datetime(2026, 6, 1, tzinfo=UTC),
    )
    assert not decision.should_rollback  # don't auto-rollback if we can't parse
    assert "could not parse" in decision.reason
