"""PokéAPI client — paginated list + per-Pokemon detail fetch.

PokéAPI (https://pokeapi.co) is a free, no-auth REST API. It rate-limits to
~100 req/sec which is plenty for our ~1,300 form fetches. We still backoff
on 429s and 5xxs because being a good citizen costs nothing.

Two endpoints we use:
  - GET /pokemon?limit=N&offset=O — paginated list of {name, url}
  - GET /pokemon/{name-or-id}    — full per-Pokemon record (types, stats,
                                    abilities, sprites, species link)
"""

from __future__ import annotations

import time
from collections.abc import Iterator

import httpx

BASE_URL = "https://pokeapi.co/api/v2"
PAGE_SIZE = 200  # PokéAPI accepts up to 100,000 but 200 is a reasonable batch
RETRY_BACKOFFS = (1.0, 2.0, 5.0)  # seconds


def _request_with_retry(client: httpx.Client, url: str) -> dict:
    """GET `url`; retry on 429/5xx up to len(RETRY_BACKOFFS) times."""
    last_status = None
    for backoff in (0.0, *RETRY_BACKOFFS):
        if backoff:
            time.sleep(backoff)
        r = client.get(url, timeout=30.0)
        if r.status_code == 200:
            return r.json()
        last_status = r.status_code
        if r.status_code not in (429, 500, 502, 503, 504):
            break  # non-retryable error
    raise RuntimeError(
        f"PokéAPI request failed after retries: {url} → HTTP {last_status}"
    )


def list_all_pokemon(client: httpx.Client) -> list[dict]:
    """Fetch the full /pokemon list. Returns [{name, url}, ...]."""
    out: list[dict] = []
    offset = 0
    while True:
        page = _request_with_retry(
            client, f"{BASE_URL}/pokemon?limit={PAGE_SIZE}&offset={offset}"
        )
        results = page.get("results", [])
        out.extend(results)
        if not page.get("next"):
            break
        offset += PAGE_SIZE
    return out


def fetch_pokemon_detail(client: httpx.Client, name_or_id: str) -> dict:
    """Fetch the full record for one Pokemon (or form). Includes stats,
    types, abilities, sprites, species link."""
    return _request_with_retry(client, f"{BASE_URL}/pokemon/{name_or_id}")


def iter_pokemon_details(
    client: httpx.Client, names: list[str]
) -> Iterator[dict]:
    """Yield detail records for each name in order. Use this when you want
    streaming without holding ~1300 records in memory at once."""
    for name in names:
        yield fetch_pokemon_detail(client, name)
