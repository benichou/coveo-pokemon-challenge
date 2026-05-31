"""Search query smoke tests.

Run a handful of representative queries through the Search API and assert
basic relevance properties (right Pokemon in the top result, expected
result counts when faceted, etc.). Catches regressions in the query
pipeline or index after config changes.
"""

from __future__ import annotations

import httpx

SEARCH_HUB = "pokemon-search"


def _search(client: httpx.Client, **kwargs) -> dict:
    body = {"searchHub": SEARCH_HUB, **kwargs}
    body.setdefault("q", "")
    body.setdefault("numberOfResults", 10)
    body.setdefault(
        "fieldsToInclude",
        ["pokemon_name", "pokemon_type", "generation", "sysuri"],
    )
    r = client.post("", json=body)
    r.raise_for_status()
    return r.json()


def test_search_for_charizard_returns_charizard_first(
    search_client: httpx.Client,
) -> None:
    data = _search(search_client, q="charizard", numberOfResults=3)
    results = data.get("results", [])
    assert results, "No results for query 'charizard'"
    top = results[0].get("raw", {})
    assert (
        top.get("pokemon_name") == "Charizard"
    ), f"Top result for 'charizard' was {top.get('pokemon_name')!r}, expected 'Charizard'"


def test_search_for_pikachu_returns_pikachu_first(
    search_client: httpx.Client,
) -> None:
    data = _search(search_client, q="pikachu", numberOfResults=3)
    results = data.get("results", [])
    assert results, "No results for query 'pikachu'"
    top = results[0].get("raw", {})
    assert (
        top.get("pokemon_name") == "Pikachu"
    ), f"Top result for 'pikachu' was {top.get('pokemon_name')!r}, expected 'Pikachu'"


def test_filter_by_generation_1_returns_at_least_151_results(
    search_client: httpx.Client,
) -> None:
    """Filtering by Generation 1 should return at least the canonical 151
    Pokemon (Bulbasaur through Mew). Some pokemondb.net forms may add a few."""
    data = _search(
        search_client,
        q="",
        aq='@generation=="Generation 1"',
        numberOfResults=0,
    )
    total = data.get("totalCount", 0)
    assert (
        total >= 151
    ), f"Generation 1 returned {total} results, expected >= 151"


def test_filter_by_fire_and_gen_1_includes_charizard(
    search_client: httpx.Client,
) -> None:
    """Cross-facet filter: Fire-type Gen 1 Pokemon. Should include Charizard."""
    data = _search(
        search_client,
        q="",
        aq='@pokemon_type=="Fire" @generation=="Generation 1"',
        numberOfResults=100,
        fieldsToInclude=["pokemon_name"],
    )
    names = {
        r.get("raw", {}).get("pokemon_name") for r in data.get("results", [])
    }
    assert (
        "Charizard" in names
    ), f"Charizard not found in Fire-type Gen 1 results. Got: {sorted(names)}"
    # Sanity: handful of others should also be there
    expected_subset = {
        "Charmander",
        "Charmeleon",
        "Charizard",
        "Vulpix",
        "Ninetales",
    }
    overlap = expected_subset & names
    assert (
        len(overlap) >= 4
    ), f"Expected at least 4 of {expected_subset} in results, got overlap: {overlap}"


def test_empty_query_returns_all_indexed_items(
    search_client: httpx.Client,
) -> None:
    """An empty query with no filters should return the full index count."""
    data = _search(search_client, q="", numberOfResults=0)
    total = data.get("totalCount", 0)
    assert (
        total >= 1000
    ), f"Empty query returned {total} results — index seems empty"
