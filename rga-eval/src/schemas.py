"""Pydantic models for the RGA Skill Evaluator.

Four data shapes live here, each pinning the structure of one stage of
the eval pipeline:

  - GoldenQuestion       — one entry in the curated dataset
  - JudgeVerdict         — what Sonnet 4.6 returns via tool-use forcing
  - PerQuestionResult    — one evaluated question (the joined record)
  - EvalRun              — the full daily output (written to eval-runs/)

Pydantic enforces these at every boundary:
  - Loading questions.json validates against GoldenQuestion (catches bad
    dataset edits at startup, before any API calls).
  - Anthropic's tool-use feature is given JudgeVerdict.model_json_schema()
    so the model is *forced* to return a structurally-valid judgment.
  - Writing eval-runs/YYYY-MM-DD-<mode>.json serializes through EvalRun, so the
    dashboard always reads well-formed JSON.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GoldenQuestion(BaseModel):
    """One entry in golden/questions.json.

    Authored by hand. Each question is a contract: "if RGA is healthy,
    its answer to `question` should mention every string in
    `expected_facts` (substring match) and cite every URI in
    `expected_citations`. If the question's `rga_should_fire` is False,
    RGA should NOT confidently answer it."
    """

    id: str = Field(
        description=(
            "Stable slug for this question; used as the key in time-series "
            "comparison so we can see 'q-charizard-type accuracy dropped from "
            "100% to 0% on date X'. Use kebab-case."
        )
    )
    layer: int = Field(
        ge=1,
        le=3,
        description=(
            "1 = single-fact (RGA should answer easily, ~95% expected). "
            "2 = multi-doc synthesis (the SE-aided sweet spot, ~70-85% expected). "
            "3 = edge case / refusal test (RGA should NOT fire or should refuse)."
        ),
    )
    category: str = Field(
        description=(
            "Sub-grouping within a layer (e.g. 'type-lookup', "
            "'form-comparison', 'out-of-domain-refusal'). Lets the dashboard "
            "drill down: 'all type-lookup questions degraded yesterday'."
        )
    )
    question: str = Field(description="The exact query text submitted to RGA.")
    expected_facts: list[str] = Field(
        default_factory=list,
        description=(
            "Strings the generated answer should contain (case-insensitive "
            "substring match). Used to compute Hard Recall deterministically, "
            "no LLM required. For Layer 3 refusal questions, leave empty."
        ),
    )
    expected_citations: list[str] = Field(
        default_factory=list,
        description=(
            "Document URIs RGA should cite. Match the format of our index: "
            "'https://pokemondb.net/pokedex/<name>' for Source A, "
            "'pokeapi://pokemon/<slug>' for Source B."
        ),
    )
    rga_should_fire: bool = Field(
        default=True,
        description=(
            "False for Layer 3 refusal tests. If RGA fires anyway with a "
            "confident answer, the LLM judge marks it as a hallucination."
        ),
    )
    notes: str = Field(
        default="",
        description="Author intent for future readers; not used by metrics.",
    )


class JudgeVerdict(BaseModel):
    """What the LLM judge (Sonnet 4.6) returns per question.

    Sonnet is invoked with tool-use forcing — the API guarantees the
    returned arguments validate against this schema. We get reliable
    structured output without parsing free-form JSON.
    """

    is_correct: bool = Field(
        description=(
            "Does the answer correctly address the question? Considers both "
            "whether the expected key facts are present AND whether the "
            "overall response is factually accurate. For Layer 3 questions, "
            "a graceful refusal (admitting lack of knowledge) is correct."
        )
    )
    has_hallucination: bool = Field(
        description=(
            "True if the answer contains any factual claim that contradicts "
            "known Pokemon canon. Empty/refusal answers are NOT hallucinations."
        )
    )
    false_claims: list[str] = Field(
        default_factory=list,
        description=(
            "Each false claim found, with a brief explanation. Empty list "
            "if no hallucinations."
        ),
    )
    reasoning: str = Field(
        description="1-2 sentence explanation of the judgment."
    )


class PerQuestionResult(BaseModel):
    """One evaluated question. The joined record of (golden, RGA, judge)."""

    question_id: str
    question: str
    layer: int
    category: str
    rga_fired: bool = Field(
        description=(
            "Did RGA produce a non-empty answer? False means the answer "
            "stream was empty (RGA declined to ground)."
        )
    )
    answer_text: str = Field(
        description="Concatenated text deltas from RGA's stream."
    )
    cited_uris: list[str] = Field(default_factory=list)
    hard_recall: float = Field(
        ge=0.0,
        le=1.0,
        description="Deterministic substring match on expected_facts.",
    )
    citation_precision: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Fraction of cited URIs that are in expected_citations. 0.0 if "
            "RGA cited nothing or if expected_citations was empty."
        ),
    )
    verdict: JudgeVerdict


class LayerStats(BaseModel):
    """Aggregated metrics for one layer (or 'overall')."""

    accuracy: float = Field(ge=0.0, le=1.0)
    precision: float = Field(
        ge=0.0,
        le=1.0,
        description="1 - (fraction of questions with any hallucination).",
    )
    hard_recall: float = Field(ge=0.0, le=1.0)
    citation_precision: float = Field(ge=0.0, le=1.0)
    n_questions: int


class EvalRun(BaseModel):
    """One run's output. Written to eval-runs/YYYY-MM-DD-<mode>.json.

    Commit history of this file IS the time-series database. The
    dashboard reads all eval-runs/*.json at build time and renders the
    Δ-over-time charts.
    """

    timestamp: str = Field(description="ISO 8601 UTC at run start.")
    coveo_org_id: str
    judge_model: str = Field(
        description=(
            "Pinned Anthropic snapshot, e.g. 'claude-sonnet-4-6-20250805'. "
            "Eval results across runs are comparable iff this string is the "
            "same; a snapshot change is itself a metric input we record."
        )
    )
    overall: LayerStats
    by_layer: dict[str, LayerStats] = Field(description="Keys: '1', '2', '3'.")
    per_question: list[PerQuestionResult]
