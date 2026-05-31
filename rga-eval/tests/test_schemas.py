"""Validate the golden dataset structure.

These tests load `golden/questions.json` and validate every entry against
the `GoldenQuestion` Pydantic schema. Failure here means the dataset is
authored wrong (typos in fields, bad layer numbers, missing required
keys); the actual eval runner refuses to start when this happens.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from schemas import GoldenQuestion

GOLDEN_PATH = (
    Path(__file__).resolve().parent.parent / "golden" / "questions.json"
)


@pytest.fixture(scope="session")
def questions() -> list[GoldenQuestion]:
    """Load + parse every question. Validation happens automatically when
    Pydantic constructs the GoldenQuestion model; bad entries raise here."""
    raw = json.loads(GOLDEN_PATH.read_text())
    return [GoldenQuestion.model_validate(q) for q in raw["questions"]]


def test_dataset_loads_and_validates(questions: list[GoldenQuestion]) -> None:
    """Every entry must parse cleanly against the Pydantic schema. If a
    bad edit lands (missing field, wrong type, out-of-range layer), the
    fixture above raises and this test reports the offending entry."""
    assert questions, "Golden dataset is empty"


def test_exactly_100_questions(questions: list[GoldenQuestion]) -> None:
    """The dataset is sized to 100 by design (50/35/15 split). A drift
    means we authored extra entries or lost some."""
    assert (
        len(questions) == 100
    ), f"Expected 100 questions, got {len(questions)}"


def test_layer_split_is_50_35_15(questions: list[GoldenQuestion]) -> None:
    """The split per Phase 6D plan: 50 Layer 1 / 35 Layer 2 / 15 Layer 3.
    Drift here means a Layer-1 question accidentally got a layer=2 tag,
    etc. — would skew the per-layer metrics in the dashboard."""
    by_layer = {1: 0, 2: 0, 3: 0}
    for q in questions:
        by_layer[q.layer] += 1
    assert by_layer == {
        1: 50,
        2: 35,
        3: 15,
    }, f"Layer split off: {by_layer}, expected {{1: 50, 2: 35, 3: 15}}"


def test_ids_are_unique(questions: list[GoldenQuestion]) -> None:
    """IDs are the time-series join key — must be unique."""
    ids = [q.id for q in questions]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"Duplicate question ids: {sorted(duplicates)}"


def test_layer_3_refusals_have_empty_facts(
    questions: list[GoldenQuestion],
) -> None:
    """Layer 3 questions test RGA's discipline — it should refuse to
    answer. Having expected_facts on a refusal question is a logic bug:
    we'd be asking RGA to refuse AND simultaneously checking it for
    specific content."""
    for q in questions:
        if q.layer == 3 and not q.rga_should_fire:
            assert not q.expected_facts, (
                f"Layer-3 refusal question {q.id} has expected_facts "
                f"({q.expected_facts}); should be empty"
            )


def test_citations_match_known_uri_schemes(
    questions: list[GoldenQuestion],
) -> None:
    """Every citation URI must match one of our two known schemes:
    Source A (`https://pokemondb.net/pokedex/...`) or
    Source B (`pokeapi://pokemon/...`). A URI that doesn't match either
    is a typo and would never produce a citation match at runtime."""
    bad: list[tuple[str, str]] = []
    for q in questions:
        for uri in q.expected_citations:
            ok_a = uri.startswith("https://pokemondb.net/pokedex/")
            ok_b = uri.startswith("pokeapi://pokemon/")
            if not (ok_a or ok_b):
                bad.append((q.id, uri))
    assert not bad, (
        "Citations don't match Source A or Source B URI schemes:\n  "
        + "\n  ".join(f"{qid}: {uri}" for qid, uri in bad)
    )
