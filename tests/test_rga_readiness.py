"""RGA readiness test.

What this asserts
-----------------
The Relevance Generative Answering (RGA) pipeline is wired and accepting
queries. Specifically:

  1. The `pokemon-rga` model exists in the org and is in the ONLINE state.
  2. The `pokemon-se` (Semantic Encoder) companion model also exists and
     is ONLINE — RGA's answer quality depends on SE feeding it better
     retrieval chunks (see docs/ml-models.md for why both are needed).
  3. Both models are associated with the default query pipeline.
  4. A natural-language question sent through the `pokemon-search` hub
     with `mlGenerativeQuestionAnswering` enabled returns a HTTP 200
     with a valid `searchUid` (the handle the streaming-answer endpoint
     would use to deliver the generated text).

What this does NOT assert
-------------------------
The actual generated answer text. Coveo's `/answer/v1/configs/{id}/generate`
streaming endpoint requires the `Knowledge.Answer Manager` privilege to
call directly, which our project API keys deliberately don't carry (least
privilege). Answer quality is verified manually by typing questions like
`what type is charizard` into the running UI and watching the streamed
answer + citations appear above the result list — that's a judgment call
a human is better at making than a test.

If the model status flips OFFLINE, the association is removed, or the
search hub stops accepting RGA-tagged queries, this test catches it.
That's the "is RGA configured and reachable?" guarantee.
"""

from __future__ import annotations

import os

import httpx

ORG_ID = os.environ["COVEO_ORG_ID"]
PLATFORM = "https://platform.cloud.coveo.com"
RGA_MODEL_NAME = "pokemon-rga"
SE_MODEL_NAME = "pokemon-se"


def _list_models(admin_client: httpx.Client) -> list[dict]:
    r = admin_client.get("/machinelearning/models")
    r.raise_for_status()
    return r.json()


def _default_pipeline_id(admin_client: httpx.Client) -> str:
    r = admin_client.get(
        f"{PLATFORM}/rest/search/v1/admin/pipelines",
        params={"organizationId": ORG_ID},
    )
    r.raise_for_status()
    default = next((p for p in r.json() if p.get("isDefault")), None)
    assert default, "No default query pipeline found on the org"
    return default["id"]


def _pipeline_associations(
    admin_client: httpx.Client, pipeline_id: str
) -> list[dict]:
    r = admin_client.get(
        f"{PLATFORM}/rest/search/v2/admin/pipelines/{pipeline_id}/ml/model/associations",
        params={"organizationId": ORG_ID},
    )
    r.raise_for_status()
    return r.json().get("rules", [])


def test_rga_model_is_online(admin_client: httpx.Client) -> None:
    """The pokemon-rga model must exist and be ONLINE.

    If this fails: check the Console under AI & ML → Models → pokemon-rga.
    Status should be `Active` (green). If the model is still BUILDING
    long after creation, trigger a rebuild via the Console or wait — RGA
    build can take 10–60 minutes for a small index.
    """
    models = _list_models(admin_client)
    rga = next(
        (m for m in models if m.get("modelDisplayName") == RGA_MODEL_NAME),
        None,
    )
    assert (
        rga
    ), f"Model '{RGA_MODEL_NAME}' not found — was it deleted from the Console?"
    assert rga.get("status") == "ONLINE", (
        f"Model '{RGA_MODEL_NAME}' is in state {rga.get('status')!r}, expected ONLINE. "
        "See AI & ML → Models in the Console; trigger a rebuild if it's stuck."
    )
    assert rga.get("modelActivenessState") == "ACTIVE", (
        f"Model '{RGA_MODEL_NAME}' is not ACTIVE (state: "
        f"{rga.get('modelActivenessState')!r})."
    )


def test_semantic_encoder_is_online(admin_client: httpx.Client) -> None:
    """The pokemon-se model — the retrieval companion that improves RGA's
    answer grounding — must also be ONLINE. Tests RGA + SE together
    because Coveo's own guidance is they should be associated together."""
    models = _list_models(admin_client)
    se = next(
        (m for m in models if m.get("modelDisplayName") == SE_MODEL_NAME),
        None,
    )
    assert se, f"Model '{SE_MODEL_NAME}' not found"
    assert (
        se.get("status") == "ONLINE"
    ), f"Model '{SE_MODEL_NAME}' is in state {se.get('status')!r}, expected ONLINE."


def test_both_models_associated_with_default_pipeline(
    admin_client: httpx.Client,
) -> None:
    """The two models must be wired into the default query pipeline.

    If this fails: run `scripts/ml/associate_models.sh` from the repo
    root. The script is idempotent and will (re)create whichever
    associations are missing. See docs/ml-models.md for the API surface
    it uses.
    """
    pipeline_id = _default_pipeline_id(admin_client)
    rules = _pipeline_associations(admin_client, pipeline_id)
    associated_names = {r.get("modelDisplayName") for r in rules}

    missing = {RGA_MODEL_NAME, SE_MODEL_NAME} - associated_names
    assert not missing, (
        f"Default pipeline is missing associations for: {sorted(missing)}. "
        f"Currently associated: {sorted(associated_names)}. "
        "Fix: run scripts/ml/associate_models.sh"
    )


def test_search_hub_accepts_rga_query(search_client: httpx.Client) -> None:
    """Submit a natural-language question through the `pokemon-search`
    hub with the mlGenerativeQuestionAnswering pipeline parameter set
    — the same shape Atomic sends in the browser. The org must accept
    it (HTTP 200) and return a searchUid (the handle a downstream
    streaming-answer endpoint would use to deliver the generated text).

    This catches regressions where the search hub gets misconfigured,
    the RGA association gets dropped, or the org-level RGA feature
    flag flips off.
    """
    body = {
        "q": "what type is charizard",
        "searchHub": "pokemon-search",
        "numberOfResults": 1,
        "pipelineRuleParameters": {
            "mlGenerativeQuestionAnswering": {
                "responseFormat": {
                    "contentFormat": ["text/markdown", "text/plain"],
                },
            },
        },
    }
    r = search_client.post("", json=body)
    assert r.status_code == 200, (
        f"Search API rejected RGA-tagged query (HTTP {r.status_code}): "
        f"{r.text[:300]}"
    )
    data = r.json()
    assert data.get("searchUid"), (
        "Response missing searchUid — RGA streaming endpoint needs this "
        "as the request handle. Got keys: " + ", ".join(sorted(data.keys()))
    )
    assert data.get("pipeline") == "default", (
        f"Search routed through pipeline {data.get('pipeline')!r}; "
        "expected 'default' (where our RGA + SE associations live)."
    )
