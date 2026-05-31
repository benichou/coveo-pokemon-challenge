"""Coveo RGA streaming client.

What this does
--------------
For each evaluator question, POST to Coveo's RGA generate endpoint and
collect the streamed answer + citations:

    POST /rest/organizations/{orgId}/answer/v1/configs/{configId}/generate
    Accept: text/event-stream
    Content-Type: application/json
    Body: {"q": "...", "pipeline": "default", "searchHub": "pokemon-search"}

The response is a Server-Sent Events stream. Each event has a name (e.g.,
`textDelta`, `citations`, `done`) and a JSON `data:` payload. We
accumulate `textDelta` events into the final answer string and capture
`citations` into a list of source URIs.

Discovering the configId
------------------------
Each RGA model has a corresponding "answer config" (Coveo's wrapper).
The configId is NOT the model ID; it's a separate identifier. We list
configs at startup (`GET /rest/organizations/{orgId}/answer/v1/configs`)
and pick the one whose name matches our model. Future runs cache the
discovered ID in COVEO_RGA_CONFIG_ID so the lookup runs once.

Required env
------------
- COVEO_ORG_ID
- COVEO_RGA_JUDGE_API_KEY    (Knowledge.Answer Manager → Edit)
- COVEO_RGA_CONFIG_ID        (optional; auto-discovered if absent)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

import httpx

PLATFORM = "https://platform.cloud.coveo.com"
DEFAULT_RGA_MODEL_NAME = "pokemon-rga"


@dataclass
class RgaAnswer:
    """What we capture from one RGA generation."""

    fired: bool
    answer_text: str
    cited_uris: list[str] = field(default_factory=list)
    raw_events: list[dict] = field(default_factory=list)


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def discover_config_id(org_id: str, api_key: str) -> str:
    """Find the answer config that references our RGA model.

    If only one config exists, return it. If multiple exist, prefer the
    one whose name contains `pokemon-rga`. Raises if no match.
    """
    r = httpx.get(
        f"{PLATFORM}/rest/organizations/{org_id}/answer/v1/configs",
        headers=_auth_headers(api_key),
        timeout=15.0,
    )
    r.raise_for_status()
    data = r.json()
    # Coveo wraps the list under `items` (paginated shape).
    # Older docs called it `configs`; handle both for forward-compat.
    if isinstance(data, list):
        configs = data
    else:
        configs = data.get("items") or data.get("configs") or []

    if not configs:
        raise RuntimeError(
            "Coveo returned no answer configs. Either the RGA model "
            "wasn't created yet, or the API key lacks "
            "Knowledge.Answer Manager privilege."
        )

    # Single config — easy case
    if len(configs) == 1:
        return configs[0]["id"]

    # Multiple — find by name
    for cfg in configs:
        name = (cfg.get("name") or "").lower()
        if DEFAULT_RGA_MODEL_NAME in name:
            return cfg["id"]

    # Fallback: take the first one
    return configs[0]["id"]


def stream_answer(
    org_id: str,
    config_id: str,
    api_key: str,
    question: str,
    search_hub: str = "pokemon-search",
    pipeline: str = "default",
    timeout: float = 60.0,
) -> RgaAnswer:
    """POST one question, consume the SSE stream, return the assembled
    answer + citations."""
    url = (
        f"{PLATFORM}/rest/organizations/{org_id}/answer/v1/"
        f"configs/{config_id}/generate"
    )
    body = {
        "q": question,
        "pipeline": pipeline,
        "searchHub": search_hub,
    }

    answer_chunks: list[str] = []
    cited_uris: list[str] = []
    raw_events: list[dict] = []
    current_event: str = ""
    current_data: list[str] = []

    def flush_event() -> None:
        """Coveo RGA SSE shape (verified 2026-05-31):

            event: message
            data: {"payloadType":"genqa.messageType",
                   "payload":"{\\"textDelta\\":\\"...\\"}",
                   "finishReason":null,"errorMessage":null,"statusCode":null}

        Every event is just `message`. The discriminator is `payloadType`
        inside the data JSON. The `payload` field is itself a JSON string
        we must parse a second time. Known payload types:

          genqa.headerMessageType    — answer style / format metadata
          genqa.messageType          — { textDelta, padding } (text chunk)
          genqa.citationsType        — { citations: [...] }
          genqa.endOfStreamType      — { answerGenerated: bool }
        """
        nonlocal current_event, current_data
        if not current_data:
            current_event = ""
            current_data = []
            return
        outer_raw = "".join(current_data)
        try:
            outer = json.loads(outer_raw) if outer_raw.strip() else {}
        except json.JSONDecodeError:
            outer = {"_raw": outer_raw}
        raw_events.append({"event": current_event, "data": outer})

        # Unwrap the nested JSON string in `payload`
        payload_type = outer.get("payloadType", "")
        payload_str = outer.get("payload", "")
        try:
            payload = (
                json.loads(payload_str)
                if isinstance(payload_str, str) and payload_str.strip()
                else {}
            )
        except json.JSONDecodeError:
            payload = {}

        if payload_type == "genqa.messageType":
            delta = payload.get("textDelta", "")
            if delta:
                answer_chunks.append(delta)
        elif payload_type == "genqa.citationsType":
            for c in payload.get("citations", []) or []:
                uri = c.get("uri") or c.get("clickUri") or c.get("sourceUri")
                if uri:
                    cited_uris.append(uri)

        current_event = ""
        current_data = []

    with (
        httpx.Client(timeout=timeout) as client,
        client.stream(
            "POST",
            url,
            headers={
                **_auth_headers(api_key),
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            },
            json=body,
        ) as response,
    ):
        if response.status_code != 200:
            # Drain body for error reporting
            response.read()
            raise RuntimeError(
                f"RGA generate failed (HTTP {response.status_code}): "
                f"{response.text[:300]}"
            )
        for line in response.iter_lines():
            if line == "":
                # blank line terminates an SSE event
                flush_event()
                continue
            if line.startswith(":"):
                # SSE comment — ignore
                continue
            if line.startswith("event:"):
                current_event = line[len("event:") :].strip()
            elif line.startswith("data:"):
                current_data.append(line[len("data:") :].lstrip())
        # End of stream — flush any partial event
        flush_event()

    answer_text = "".join(answer_chunks).strip()
    return RgaAnswer(
        fired=bool(answer_text),
        answer_text=answer_text,
        cited_uris=cited_uris,
        raw_events=raw_events,
    )


def stream_answer_with_retry(
    org_id: str,
    config_id: str,
    api_key: str,
    question: str,
    max_attempts: int = 3,
) -> RgaAnswer:
    """Wrap stream_answer with retry on transient failures."""
    backoffs = (1.0, 3.0, 8.0)
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return stream_answer(org_id, config_id, api_key, question)
        except (httpx.HTTPError, RuntimeError) as e:
            last_err = e
            if attempt < max_attempts - 1:
                time.sleep(backoffs[attempt])
    raise RuntimeError(
        f"RGA stream failed after {max_attempts} attempts: {last_err}"
    )


def get_config_id_from_env_or_discover(org_id: str, api_key: str) -> str:
    """Return COVEO_RGA_CONFIG_ID from env if set, else discover via API."""
    cfg_id = os.environ.get("COVEO_RGA_CONFIG_ID")
    if cfg_id:
        return cfg_id
    return discover_config_id(org_id, api_key)
