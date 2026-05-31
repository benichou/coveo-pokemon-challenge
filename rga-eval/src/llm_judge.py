"""Sonnet 4.6 as LLM judge for RGA answer quality.

Why structured output via tool-use forcing
-------------------------------------------
Free-form JSON output from LLMs is fragile — Sonnet sometimes adds
prose before/after, sometimes returns markdown fences, sometimes
forgets a key. Tool-use forcing eliminates that: we register a
"submit_judgment" tool whose input schema is JudgeVerdict's JSON
schema, then set `tool_choice` to force that tool. Anthropic
guarantees the returned arguments validate against the schema.

The JudgeVerdict Pydantic model parses the tool input, giving us a
type-safe object. If Anthropic ever drifts and returns a malformed
structure, Pydantic raises and we record the failure rather than
silently corrupting metrics.

Cost
----
Sonnet 4.6: ~$3/M input, ~$15/M output. Each judgment is ~1K input
tokens + ~200 output tokens = ~$0.006 per question. 100 questions
per run = ~$0.60/run. Daily for a month = ~$18, well under our
$5-credit-then-pay budget.
"""

from __future__ import annotations

import os

from anthropic import Anthropic
from schemas import GoldenQuestion, JudgeVerdict

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
JUDGE_SYSTEM_PROMPT = """You are an expert Pokemon-knowledge evaluator. Your \
job is to judge whether AI-generated answers to Pokemon questions are \
factually correct.

You evaluate one (question, answer) pair at a time. The user provides:
  - The original question that was asked
  - A list of expected key facts that a correct answer would mention
    (empty list if the question is out-of-domain or a refusal test)
  - Whether the AI was supposed to refuse the question (rga_should_fire=false)
  - The actual answer the AI produced

You must call the `submit_judgment` tool exactly once with your evaluation.
Do NOT respond with prose; the tool call IS the response.

Evaluation rules:
  - `is_correct`: True if the answer adequately addresses the question.
    For a normal question, this means the expected facts are present
    AND there are no factual errors. For a refusal test (rga_should_fire
    =false), this means the AI either declined to answer OR gave a
    nuanced response that doesn't claim a false answer.
  - `has_hallucination`: True if the answer makes any factual claim
    that contradicts canonical Pokemon facts. An empty / refusal answer
    is NOT a hallucination.
  - `false_claims`: List each hallucination with a brief reason, or
    empty list if none.
  - `reasoning`: 1-2 sentences explaining the judgment.

Use canonical Pokemon facts as the source of truth. The expected_facts
list is a starting point but not exhaustive; an answer can contain
correct facts beyond the expected list and still be is_correct=True."""


def build_judge_prompt(
    question: GoldenQuestion,
    answer_text: str,
) -> str:
    """Construct the per-question user message for Sonnet."""
    expected = (
        "\n".join(f"  - {f}" for f in question.expected_facts)
        if question.expected_facts
        else "  (none — this is a refusal test or has no specific facts)"
    )
    answer = (
        answer_text.strip()
        if answer_text.strip()
        else "(empty / no answer produced)"
    )
    return f"""QUESTION ASKED:
{question.question}

EXPECTED KEY FACTS (a correct answer should mention these):
{expected}

RGA SHOULD FIRE: {question.rga_should_fire}
(If false, the AI was supposed to refuse or stay silent.)

AI-GENERATED ANSWER UNDER EVALUATION:
\"\"\"
{answer}
\"\"\"

Evaluate the answer and call the submit_judgment tool."""


def judge_one(
    question: GoldenQuestion,
    answer_text: str,
    *,
    model: str = DEFAULT_MODEL,
    client: Anthropic | None = None,
) -> JudgeVerdict:
    """Run one judgment. Returns a validated JudgeVerdict."""
    if client is None:
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    schema = JudgeVerdict.model_json_schema()
    # Anthropic's tool input_schema expects a JSON Schema object. Pydantic
    # produces one with `$defs` and `definitions` keys that some validators
    # reject; strip them and inline if present. For our flat model
    # there's nothing nested so this is usually a no-op.
    schema.pop("$defs", None)
    schema.pop("definitions", None)

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=JUDGE_SYSTEM_PROMPT,
        tools=[
            {
                "name": "submit_judgment",
                "description": (
                    "Submit your evaluation of the Pokemon answer's "
                    "correctness and factual accuracy."
                ),
                "input_schema": schema,
            }
        ],
        tool_choice={"type": "tool", "name": "submit_judgment"},
        messages=[
            {
                "role": "user",
                "content": build_judge_prompt(question, answer_text),
            }
        ],
    )

    # Find the tool_use block in the response
    tool_blocks = [
        b for b in response.content if getattr(b, "type", "") == "tool_use"
    ]
    if not tool_blocks:
        raise RuntimeError(
            "Sonnet didn't call the submit_judgment tool. Response: "
            f"{response.content}"
        )
    return JudgeVerdict.model_validate(tool_blocks[0].input)
