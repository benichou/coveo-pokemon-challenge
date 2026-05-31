"""Shared pytest fixtures for the Coveo Pokemon Challenge test suite.

Loads `.env` from the repo root and exposes:
  - search_client: httpx client pre-configured for the Search API (uses COVEO_SEARCH_API_KEY)
  - admin_client:  httpx client pre-configured for the platform/admin API (uses COVEO_ADMIN_API_KEY)
  - url_filter_config: parsed contents of config/source/url_filter.json
  - indexed_uris: set of all URIs currently in the index (session-scoped, fetched once)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

# Repo root is one level up from tests/
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

ORG_ID = os.environ["COVEO_ORG_ID"]
SEARCH_API_KEY = os.environ["COVEO_SEARCH_API_KEY"]
ADMIN_API_KEY = os.environ["COVEO_ADMIN_API_KEY"]
SOURCE_ID = os.environ["COVEO_SITEMAP_SOURCE_ID"]
SEARCH_HUB = "pokemon-search"
SEARCH_URL = "https://platform.cloud.coveo.com/rest/search/v2"
PLATFORM_URL = f"https://platform.cloud.coveo.com/rest/organizations/{ORG_ID}"


@pytest.fixture(scope="session")
def search_client() -> httpx.Client:
    """Search API client, scoped to one session (reused across tests)."""
    with httpx.Client(
        base_url=SEARCH_URL,
        headers={"Authorization": f"Bearer {SEARCH_API_KEY}"},
        params={"organizationId": ORG_ID},
        timeout=30.0,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def admin_client() -> httpx.Client:
    """Admin (platform) API client, scoped to one session."""
    with httpx.Client(
        base_url=PLATFORM_URL,
        headers={"Authorization": f"Bearer {ADMIN_API_KEY}"},
        timeout=30.0,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def url_filter_config() -> dict:
    """Parsed contents of config/source/url_filter.json — the single source of truth
    shared between scripts/source/widen.sh and these tests."""
    with open(REPO_ROOT / "config" / "source" / "url_filter.json") as f:
        return json.load(f)


def _paginate_uris(
    client: httpx.Client, source_filter: str | None = None
) -> set[str]:
    """Enumerate all URIs in the index (optionally filtered by source).

    `source_filter` is a value for the Coveo `@source` field
    (e.g., 'pokemondb-sitemap' or 'pokemondb-push'). If None, returns the
    union of both sources.
    """
    uris: set[str] = set()
    page_size = 1000  # Coveo Search API's max numberOfResults per request
    first = 0
    while True:
        body = {
            "q": "",
            "searchHub": SEARCH_HUB,
            "numberOfResults": page_size,
            "firstResult": first,
            "fieldsToInclude": ["sysuri"],
            # Sort by @date (indexedDate) ascending so pagination is stable.
            # Without an explicit sort, Coveo defaults to relevancy; on an
            # empty query with many ties, relevancy ordering shuffles
            # between page calls — items get dropped, others duplicated.
            # @date is set on every indexed item and is stable within a run.
            "sortCriteria": "date ascending",
        }
        if source_filter:
            body["aq"] = f"@source={source_filter}"
        r = client.post("", json=body)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            break
        for res in results:
            uri = res.get("raw", {}).get("sysuri") or res.get("uri")
            if uri:
                uris.add(uri)
        if len(results) < page_size:
            break
        first += page_size
    return uris


@pytest.fixture(scope="session")
def indexed_uris(search_client: httpx.Client) -> set[str]:
    """All URIs indexed under Source A (`pokemondb-sitemap`).

    Note: scoped to Source A even though Source B (`pokemondb-push`) exists.
    Most tests in this directory pre-date Source B and assume "indexed URIs"
    means the sitemap-derived set. New tests that want Source B coverage
    should use the explicit `indexed_uris_push` or `indexed_uris_all`
    fixtures below.
    """
    return _paginate_uris(search_client, source_filter="pokemondb-sitemap")


@pytest.fixture(scope="session")
def indexed_uris_push(search_client: httpx.Client) -> set[str]:
    """All URIs indexed under Source B (`pokemondb-push`)."""
    return _paginate_uris(search_client, source_filter="pokemondb-push")


@pytest.fixture(scope="session")
def indexed_uris_all(search_client: httpx.Client) -> set[str]:
    """Union of all indexed URIs across both sources."""
    return _paginate_uris(search_client, source_filter=None)
