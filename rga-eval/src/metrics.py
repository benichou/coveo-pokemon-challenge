"""Compute eval metrics from per-question results.

Definitions
-----------
Per question:
  hard_recall          = matched_expected_facts / total_expected_facts
                         (1.0 if no expected facts, e.g. refusal tests)
  citation_precision   = cited & expected / |cited|
                         (1.0 if no expected citations and no cited)
  is_correct           = (LLM judge) holistic "is this answer correct?"
  has_hallucination    = (LLM judge) "any false claims?"

Aggregated per layer and overall:
  accuracy             = mean(is_correct)            ∈ [0, 1]
  precision            = mean(1 - has_hallucination) ∈ [0, 1]
  hard_recall          = mean(hard_recall)           ∈ [0, 1]
  citation_precision   = mean(citation_precision)    ∈ [0, 1]
"""

from __future__ import annotations

from schemas import GoldenQuestion, LayerStats, PerQuestionResult


def compute_hard_recall(answer_text: str, expected_facts: list[str]) -> float:
    """Substring-match each expected_fact against the answer (case-insensitive)."""
    if not expected_facts:
        return 1.0
    answer_lower = answer_text.lower()
    matched = sum(1 for f in expected_facts if f.lower() in answer_lower)
    return matched / len(expected_facts)


def compute_citation_precision(cited: list[str], expected: list[str]) -> float:
    """Fraction of cited URIs that are in expected_citations."""
    if not cited:
        # No citations produced. If we expected some, that's 0; if none
        # expected, treat as 1.0 (no false-positive citations).
        return 1.0 if not expected else 0.0
    expected_set = set(expected)
    matches = sum(1 for c in cited if c in expected_set)
    return matches / len(cited)


def aggregate(per_q: list[PerQuestionResult]) -> LayerStats:
    """Aggregate metrics across a list of per-question results."""
    n = len(per_q)
    if n == 0:
        return LayerStats(
            accuracy=0.0,
            precision=0.0,
            hard_recall=0.0,
            citation_precision=0.0,
            n_questions=0,
        )
    accuracy = sum(1 for r in per_q if r.verdict.is_correct) / n
    precision = sum(1 for r in per_q if not r.verdict.has_hallucination) / n
    hard_recall = sum(r.hard_recall for r in per_q) / n
    citation_precision = sum(r.citation_precision for r in per_q) / n
    return LayerStats(
        accuracy=accuracy,
        precision=precision,
        hard_recall=hard_recall,
        citation_precision=citation_precision,
        n_questions=n,
    )


def by_layer(per_q: list[PerQuestionResult]) -> dict[str, LayerStats]:
    """Group results by layer (1/2/3) and aggregate within each."""
    buckets: dict[int, list[PerQuestionResult]] = {1: [], 2: [], 3: []}
    for r in per_q:
        if r.layer in buckets:
            buckets[r.layer].append(r)
    return {str(layer): aggregate(rs) for layer, rs in buckets.items()}


def build_per_question(
    question: GoldenQuestion,
    answer_text: str,
    rga_fired: bool,
    cited_uris: list[str],
    verdict,
) -> PerQuestionResult:
    """Construct a PerQuestionResult from raw inputs + judgment."""
    return PerQuestionResult(
        question_id=question.id,
        question=question.question,
        layer=question.layer,
        category=question.category,
        rga_fired=rga_fired,
        answer_text=answer_text,
        cited_uris=cited_uris,
        hard_recall=compute_hard_recall(answer_text, question.expected_facts),
        citation_precision=compute_citation_precision(
            cited_uris, question.expected_citations
        ),
        verdict=verdict,
    )
