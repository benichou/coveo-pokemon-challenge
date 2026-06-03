"""Unit tests for src/analyzer.py — multi-day window functions.

Covers the pure data-pipeline pieces (CategoryHistory derivation,
compute_category_histories, rank_worst_categories ordering). The LLM-call
path (call_analyzer / build_analyzer_user_message) is exercised via the
data smoke-test in `analyzer.py --no-llm` and isn't unit-tested here —
that would require either live Anthropic calls or extensive mocking of
the SDK, neither of which adds value over an integration test.
"""

from __future__ import annotations

from analyzer import (
    DEFAULT_PERSISTENCE_THRESHOLD,
    CategoryHistory,
    CategoryStats,
    RunSummary,
    compute_category_histories,
    rank_worst_categories,
)

# ---------- Fixtures ----------


def make_cs(
    *,
    layer: int = 1,
    category: str = "ability_lookup",
    n: int = 10,
    accuracy: float = 0.50,
    hard_recall: float = 0.90,
) -> CategoryStats:
    return CategoryStats(
        layer=layer,
        category=category,
        n=n,
        accuracy=accuracy,
        hard_recall=hard_recall,
        gap=hard_recall - accuracy,
    )


def make_run(
    *,
    date: str = "2026-06-01",
    overall_accuracy: float = 0.70,
    overall_precision: float = 0.80,
    overall_hard_recall: float = 0.90,
    categories: dict[str, CategoryStats] | None = None,
) -> RunSummary:
    return RunSummary(
        date=date,
        overall_accuracy=overall_accuracy,
        overall_precision=overall_precision,
        overall_hard_recall=overall_hard_recall,
        by_category=categories or {},
    )


# ---------- CategoryHistory.persistence ----------


def test_persistence_all_failing():
    """5/5 runs below threshold → persistence == 5."""
    h = CategoryHistory(
        layer=1,
        category="cat",
        runs=[make_cs(accuracy=a) for a in [0.1, 0.2, 0.3, 0.4, 0.5]],
    )
    assert h.persistence(threshold=0.70) == 5


def test_persistence_none_failing():
    """All runs above threshold → persistence == 0."""
    h = CategoryHistory(
        layer=1,
        category="cat",
        runs=[make_cs(accuracy=a) for a in [0.75, 0.80, 0.85, 0.90, 0.95]],
    )
    assert h.persistence(threshold=0.70) == 0


def test_persistence_one_spike():
    """Single-day spike (1/5 below) gets low persistence — the multi-day
    window's whole point is to ignore noise like this."""
    h = CategoryHistory(
        layer=1,
        category="cat",
        runs=[make_cs(accuracy=a) for a in [0.85, 0.90, 0.40, 0.92, 0.88]],
    )
    assert h.persistence(threshold=0.70) == 1


def test_persistence_threshold_boundary():
    """At-threshold value is NOT counted as failing (strict less-than)."""
    h = CategoryHistory(layer=1, category="cat", runs=[make_cs(accuracy=0.70)])
    assert h.persistence(threshold=0.70) == 0


def test_persistence_custom_threshold():
    """A stricter threshold raises persistence; a looser one lowers it."""
    h = CategoryHistory(
        layer=1,
        category="cat",
        runs=[make_cs(accuracy=a) for a in [0.60, 0.65, 0.70, 0.75, 0.80]],
    )
    assert h.persistence(threshold=0.70) == 2  # 0.60, 0.65
    assert h.persistence(threshold=0.50) == 0
    assert h.persistence(threshold=0.90) == 5


# ---------- CategoryHistory.drift ----------


def test_drift_declining():
    """Accuracy dropping over the window → positive drift."""
    h = CategoryHistory(
        layer=1,
        category="cat",
        runs=[make_cs(accuracy=a) for a in [0.90, 0.85, 0.75, 0.65, 0.55]],
    )
    # first half (mid=2): [0.90, 0.85] avg = 0.875
    # second half:       [0.75, 0.65, 0.55] avg = 0.65
    # drift = 0.875 - 0.65 = 0.225
    assert h.drift() > 0.20
    assert h.drift() < 0.25


def test_drift_improving():
    """Accuracy rising over the window → negative drift."""
    h = CategoryHistory(
        layer=1,
        category="cat",
        runs=[make_cs(accuracy=a) for a in [0.50, 0.55, 0.70, 0.80, 0.90]],
    )
    assert h.drift() < 0


def test_drift_stable():
    """No change → drift ≈ 0."""
    h = CategoryHistory(
        layer=1,
        category="cat",
        runs=[make_cs(accuracy=0.80) for _ in range(5)],
    )
    assert abs(h.drift()) < 1e-9


def test_drift_single_run():
    """Drift is undefined with one data point; returns 0 (no trend)."""
    h = CategoryHistory(layer=1, category="cat", runs=[make_cs(accuracy=0.50)])
    assert h.drift() == 0.0


def test_drift_two_runs():
    """N=2 collapses to plain latest-vs-prior (mid=1, halves are [r0] and
    [r1]). Drift = r0.acc - r1.acc."""
    h = CategoryHistory(
        layer=1,
        category="cat",
        runs=[make_cs(accuracy=0.80), make_cs(accuracy=0.60)],
    )
    # first half [0.80] avg = 0.80; second half [0.60] avg = 0.60
    # drift = 0.80 - 0.60 = 0.20 (declining)
    assert abs(h.drift() - 0.20) < 1e-9


# ---------- compute_category_histories ----------


def test_compute_histories_preserves_chronological_order():
    """Histories list runs in the same order as the input runs list."""
    runs = [
        make_run(
            date=d,
            categories={
                "L1:cat": make_cs(accuracy=acc),
            },
        )
        for d, acc in [("d1", 0.50), ("d2", 0.60), ("d3", 0.70)]
    ]
    histories = compute_category_histories(runs)
    assert "L1:cat" in histories
    accuracies = [cs.accuracy for cs in histories["L1:cat"].runs]
    assert accuracies == [0.50, 0.60, 0.70]


def test_compute_histories_handles_missing_categories():
    """A category that only appears in some runs has a shorter history;
    we do NOT pad with synthetic zeros (which would be ambiguous with
    'category had 0% accuracy')."""
    r1 = make_run(
        date="d1",
        categories={
            "L1:a": make_cs(category="a"),
            "L1:b": make_cs(category="b"),
        },
    )
    r2 = make_run(date="d2", categories={"L1:a": make_cs(category="a")})
    histories = compute_category_histories([r1, r2])
    assert histories["L1:a"].n_runs == 2
    assert histories["L1:b"].n_runs == 1


def test_compute_histories_empty_input():
    """Zero runs in → zero histories out."""
    assert compute_category_histories([]) == {}


# ---------- rank_worst_categories ----------


def _hist(*accs: float, key: str = "cat", layer: int = 1, n: int = 10):
    """Convenience: build a CategoryHistory from a list of accuracy values."""
    return CategoryHistory(
        layer=layer,
        category=key,
        runs=[
            make_cs(layer=layer, category=key, accuracy=a, n=n) for a in accs
        ],
    )


def test_rank_chronic_beats_noise():
    """A category failing 5/5 days beats one failing only 1/5 days even
    if today's accuracy looks similar."""
    chronic = _hist(0.20, 0.25, 0.20, 0.30, 0.25, key="chronic")
    one_day_spike = _hist(0.90, 0.92, 0.30, 0.91, 0.93, key="spike")
    histories = {h.key: h for h in [chronic, one_day_spike]}
    ranked = rank_worst_categories(
        histories, top_n=2, persistence_threshold=0.70
    )
    assert ranked[0].category == "chronic"
    assert ranked[1].category == "spike"


def test_rank_persistence_beats_drift():
    """Among categories with similar latest accuracy, higher persistence
    wins over higher drift — chronic failure is the primary signal."""
    chronic_no_drift = _hist(
        0.30, 0.30, 0.30, 0.30, 0.30, key="chronic_no_drift"
    )
    drifting = _hist(0.85, 0.80, 0.65, 0.55, 0.50, key="drifting")
    # chronic_no_drift: persistence 5/5, drift = 0
    # drifting:         persistence 3/5 (last 3 below 0.70), drift > 0
    histories = {h.key: h for h in [chronic_no_drift, drifting]}
    ranked = rank_worst_categories(
        histories, top_n=2, persistence_threshold=0.70
    )
    assert ranked[0].category == "chronic_no_drift"
    assert ranked[1].category == "drifting"


def test_rank_drift_breaks_persistence_tie():
    """Among categories with equal persistence, the one declining faster
    (higher drift) ranks worse."""
    declining = _hist(
        0.85, 0.80, 0.60, 0.55, 0.50, key="declining"
    )  # persistence 3/5, drift positive
    stable_low = _hist(
        0.65, 0.65, 0.65, 0.65, 0.65, key="stable_low"
    )  # persistence 5/5, drift 0
    # Different persistence, so stable_low wins because chronic > drift.
    # We want declining to RANK SECOND. To test drift-breaks-tie we need
    # equal persistence.
    drift_a = _hist(
        0.60, 0.55, 0.50, 0.45, 0.40, key="drift_a"
    )  # persistence 5/5, declining
    drift_b = _hist(
        0.40, 0.45, 0.50, 0.55, 0.60, key="drift_b"
    )  # persistence 5/5, improving
    histories = {h.key: h for h in [drift_a, drift_b, stable_low, declining]}
    ranked = rank_worst_categories(
        histories, top_n=4, persistence_threshold=0.70
    )
    # All four are below 0.70 latest, but only drift_a + drift_b + stable_low
    # have full 5/5 persistence. Among them, drift_a (declining) beats stable_low
    # (no drift) beats drift_b (improving).
    keys_in_order = [r.category for r in ranked]
    assert keys_in_order.index("drift_a") < keys_in_order.index("stable_low")
    assert keys_in_order.index("stable_low") < keys_in_order.index("drift_b")


def test_rank_respects_top_n_cap():
    """top_n=2 returns exactly 2 even if more histories exist."""
    histories = {
        f"L1:{k}": _hist(0.5, 0.5, 0.5, key=k) for k in ["a", "b", "c", "d"]
    }
    ranked = rank_worst_categories(histories, top_n=2)
    assert len(ranked) == 2


def test_rank_handles_single_run_history():
    """A category with only one data point in the window has drift=0 and
    persistence in {0,1}; should still be rankable."""
    histories = {"L1:cat": _hist(0.30, key="cat")}
    ranked = rank_worst_categories(histories, top_n=1)
    assert len(ranked) == 1
    assert ranked[0].drift() == 0.0


# ---------- trajectory_str (cosmetic, but easy to lock down) ----------


def test_trajectory_str_format():
    """Trajectory renders as percent values separated by single spaces."""
    h = _hist(0.10, 0.20, 0.30)
    assert h.trajectory_str() == "10% 20% 30%"


# ---------- Default threshold sanity ----------


def test_default_threshold_value():
    """Locking 0.70 as the package default — bumping it should be a
    deliberate change with a doc update + memory update."""
    assert DEFAULT_PERSISTENCE_THRESHOLD == 0.70
