"""Pydantic models for the rga-closed-loop package.

Two data shapes live here:

  - PromptVersion       — what a prompts/*.yaml file deserializes into.
                          Validates structure on load so bad YAML fails
                          before any Coveo API call.
  - PromptProposal      — what the Layer-2 analyzer (Phase 6F.3) returns
                          when it suggests a prompt delta. Shipped here
                          ahead of 6F.3 so the schema is locked.

The YAML on disk follows the structure pinned by these models. If the
file shape ever changes, update these models AND the YAML simultaneously
so the apply script + analyzer stay in sync.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CoveoModelRef(BaseModel):
    """Identifies which Coveo ML model this prompt targets."""

    display_name: str = Field(
        description=(
            "modelDisplayName in Coveo. Stable across rebuilds — the script "
            "discovers the volatile model id by listing models and filtering "
            "on this field."
        )
    )
    engine_id: str = Field(
        description=(
            "Engine id for the model type. `genqa` = RGA. `embeddings` = "
            "Semantic Encoder. We only target genqa models."
        )
    )


class ExpectedLift(BaseModel):
    """Predicted before/after numbers for a single metric (e.g., accuracy)."""

    from_: float = Field(
        alias="from",
        ge=0.0,
        le=1.0,
        description="Baseline value measured before the prompt change.",
    )
    target: float = Field(
        ge=0.0,
        le=1.0,
        description="Hypothesis: the value after the prompt change.",
    )

    model_config = ConfigDict(populate_by_name=True)


class PromptMetadata(BaseModel):
    """Provenance + intent attached to a prompt version.

    Read by the Layer-2 analyzer to detect "this change failed to deliver"
    patterns when comparing predicted vs measured lift.
    """

    version: str = Field(
        description="Semver-ish. Bump major on breaking style changes."
    )
    applied_at: str = Field(description="ISO 8601 UTC timestamp.")
    applied_by: str
    replaces: str = Field(
        default="",
        description=(
            "Relative path to the history/ YAML this version replaces. "
            "Empty for the very first version on the model."
        ),
    )
    rationale: str = Field(description="Multi-line explanation of the change.")
    expected_lift: dict[str, ExpectedLift] = Field(
        default_factory=dict,
        description=(
            "Per-metric predicted lift. Keys are metric names like "
            "'overall_accuracy' or 'layer_1_ability_lookup'."
        ),
    )
    validated_against: str = Field(
        default="",
        description=(
            "Path to the eval-runs JSON that measured this version after "
            "it was applied. Filled in by the analyzer after the first "
            "post-change eval run; empty until then."
        ),
    )
    related_eval_run: str = Field(
        default="",
        description="Path to the pre-change eval-runs JSON that motivated this version.",
    )
    related_methodology: str = Field(
        default="",
        description="Path to the methodology doc this prompt aligns with.",
    )


class PromptVersion(BaseModel):
    """One prompts/*.yaml file deserializes into this."""

    model: CoveoModelRef
    prompt: str = Field(
        min_length=1, description="The Custom Prompt text itself."
    )
    metadata: PromptMetadata


class PromptProposal(BaseModel):
    """Layer-2 analyzer's output (Phase 6F.3 — shipped here for forward compat).

    The analyzer reads eval-runs, identifies regressed categories, samples
    failing answers, and returns this structure via Sonnet 4.6 tool-use
    forcing. The PR-opener step (6F.4) then writes it into a new YAML +
    opens a PR.
    """

    new_prompt: str = Field(
        min_length=1,
        description="The proposed replacement for prompts/pokemon-rga.yaml's `prompt` field.",
    )
    rationale: str = Field(
        description=(
            "Multi-paragraph explanation of why the analyzer is proposing "
            "this change. Goes into the PR description verbatim."
        )
    )
    expected_lift: dict[str, ExpectedLift] = Field(
        default_factory=dict,
        description="Per-metric predicted lift after this change.",
    )
    sample_answers: list[dict] = Field(
        default_factory=list,
        description=(
            "Optional. List of {question, before_answer, predicted_after_answer} "
            "showing the change in action on the worst failing categories. "
            "Renders in the PR body for human review."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Analyzer's self-rated confidence that this change will deliver "
            "the predicted lift. Low confidence = the PR description should "
            "emphasize 'experimental — review carefully'."
        ),
    )
