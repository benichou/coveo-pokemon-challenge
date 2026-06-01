"""Unit tests for src/apply.py — no live Coveo calls.

Strategy: use respx (httpx mock transport) to intercept HTTP calls and
assert on request shape. Tests:
  - load_prompt() validates the YAML against the Pydantic schema
  - find_model_id() filters the list response by displayName
  - patch_model_body() does the right field surgery without dropping
    unrelated config
  - make_diff() produces a stable unified diff
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx
import yaml
from apply import (
    find_model_id,
    load_prompt,
    make_diff,
    patch_model_body,
)
from pydantic import ValidationError

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def test_current_yaml_loads_and_validates() -> None:
    """The committed prompts/pokemon-rga.yaml must parse cleanly."""
    pv = load_prompt(PROMPTS_DIR / "pokemon-rga.yaml")
    assert pv.model.display_name == "pokemon-rga"
    assert pv.model.engine_id == "genqa"
    assert len(pv.prompt) > 500, "prompt suspiciously short"
    assert pv.metadata.version
    assert pv.metadata.rationale
    # The Pokemon prompt should mention the grounding instruction
    assert "ONLY" in pv.prompt
    assert "retrieved source" in pv.prompt.lower()


def test_default_history_yaml_loads() -> None:
    """The archived default-template YAML must also parse."""
    pv = load_prompt(PROMPTS_DIR / "history" / "2026-05-31-default.yaml")
    assert pv.model.display_name == "pokemon-rga"
    # The default still had the unfilled enterprise-template placeholders
    assert "[Enterprise Name]" in pv.prompt


def test_load_prompt_rejects_missing_fields(tmp_path: Path) -> None:
    """YAML missing required fields must fail Pydantic validation at load."""
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        yaml.safe_dump({"prompt": "hello"})
    )  # missing model + metadata
    with pytest.raises(ValidationError):
        load_prompt(bad)


def test_patch_model_body_preserves_unrelated_fields() -> None:
    """The PUT body must keep everything EXCEPT the prompt field unchanged."""
    current = {
        "id": "abc",
        "modelDisplayName": "pokemon-rga",
        "engineId": "genqa",
        "extraConfig": {
            "indexExport": {"sources": ["pokemondb-sitemap"]},
            "additionalAnswerInstructions": "OLD prompt",
        },
        "intervalUnit": "WEEK",
    }
    patched = patch_model_body(current, "NEW prompt")
    # Prompt field changed
    assert (
        patched["extraConfig"]["additionalAnswerInstructions"] == "NEW prompt"
    )
    # Sibling field in extraConfig preserved
    assert patched["extraConfig"]["indexExport"] == {
        "sources": ["pokemondb-sitemap"]
    }
    # Top-level fields preserved
    assert patched["id"] == "abc"
    assert patched["intervalUnit"] == "WEEK"
    # Original input not mutated (shallow-immutability sanity check)
    assert (
        current["extraConfig"]["additionalAnswerInstructions"] == "OLD prompt"
    )


def test_patch_model_body_handles_missing_extra_config() -> None:
    """If extraConfig is None or missing, patch_model_body should create it."""
    current = {"id": "abc", "modelDisplayName": "pokemon-rga"}
    patched = patch_model_body(current, "NEW")
    assert patched["extraConfig"]["additionalAnswerInstructions"] == "NEW"


def test_make_diff_empty_when_no_change() -> None:
    assert make_diff("same", "same") == ""


def test_make_diff_nonempty_when_change() -> None:
    diff = make_diff("old line\n", "new line\n")
    assert "old line" in diff
    assert "new line" in diff
    assert "+++" in diff and "---" in diff


@respx.mock
def test_find_model_id_picks_matching_display_name() -> None:
    """find_model_id must filter on modelDisplayName and ignore others."""
    respx.get(
        "https://platform.cloud.coveo.com/rest/organizations/ORG/machinelearning/models"
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "id-other",
                    "modelDisplayName": "pokemon-se",
                    "engineId": "embeddings",
                },
                {
                    "id": "id-target",
                    "modelDisplayName": "pokemon-rga",
                    "engineId": "genqa",
                },
            ],
        )
    )
    assert find_model_id("ORG", "KEY", "pokemon-rga") == "id-target"


@respx.mock
def test_find_model_id_raises_when_no_match() -> None:
    """Helpful error when no model has the target display name."""
    respx.get(
        "https://platform.cloud.coveo.com/rest/organizations/ORG/machinelearning/models"
    ).mock(return_value=httpx.Response(200, json=[]))
    with pytest.raises(RuntimeError, match="No model"):
        find_model_id("ORG", "KEY", "pokemon-rga")
