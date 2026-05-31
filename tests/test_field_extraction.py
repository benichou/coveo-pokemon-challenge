"""Field extraction spot-checks.

For a small set of well-known Pokemon, query Coveo and assert the indexed
field values match canonical expectations. Catches scraping-config regressions
(e.g., a CSS selector change accidentally dropping a type).
"""

from __future__ import annotations

import httpx
import pytest

SEARCH_HUB = "pokemon-search"

# (filename_slug, expected_name, expected_types, expected_dex, expected_generation)
# Chosen for diversity: single/dual type, hyphenated names, multiple generations,
# legendary, hisuian form.
POKEMON_SPOT_CHECK = [
    ("bulbasaur", "Bulbasaur", ["Grass", "Poison"], 1, "Generation 1"),
    ("pikachu", "Pikachu", ["Electric"], 25, "Generation 1"),
    ("charizard", "Charizard", ["Fire", "Flying"], 6, "Generation 1"),
    ("mewtwo", "Mewtwo", ["Psychic"], 150, "Generation 1"),
    # Note: pokemondb.net uses "Ho-oh" (lowercase second o) in their h1, not the
    # official "Ho-Oh". Our scraping faithfully captures what they render.
    ("ho-oh", "Ho-oh", ["Fire", "Flying"], 250, "Generation 2"),
    ("mr-mime", "Mr. Mime", ["Psychic", "Fairy"], 122, "Generation 1"),
    ("decidueye", "Decidueye", ["Grass", "Ghost"], 724, "Generation 7"),
    ("miraidon", "Miraidon", ["Electric", "Dragon"], 1008, "Generation 9"),
]


def _fetch_pokemon(client: httpx.Client, slug: str) -> dict:
    """Search Coveo for a specific Pokemon by URL slug and return its raw field bag."""
    body = {
        "q": "",
        "searchHub": SEARCH_HUB,
        "numberOfResults": 1,
        "aq": f'@sysuri=="https://pokemondb.net/pokedex/{slug}"',
        "fieldsToInclude": [
            "pokemon_name",
            "pokemon_type",
            "image_url",
            "dex_number",
            "generation",
            "sysuri",
        ],
    }
    r = client.post("", json=body)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    assert results, f"No result for {slug}"
    return results[0].get("raw", {})


@pytest.mark.parametrize(
    "slug,expected_name,expected_types,expected_dex,expected_gen",
    POKEMON_SPOT_CHECK,
    ids=[p[0] for p in POKEMON_SPOT_CHECK],
)
def test_pokemon_fields(
    search_client: httpx.Client,
    slug: str,
    expected_name: str,
    expected_types: list[str],
    expected_dex: int,
    expected_gen: str,
) -> None:
    raw = _fetch_pokemon(search_client, slug)

    assert (
        raw.get("pokemon_name") == expected_name
    ), f"{slug}: name mismatch — got {raw.get('pokemon_name')!r}"

    actual_types = raw.get("pokemon_type")
    # pokemon_type is multi-value: Coveo returns a list of strings
    assert (
        sorted(actual_types) == sorted(expected_types)
    ), f"{slug}: type mismatch — got {actual_types!r}, expected {expected_types!r}"

    assert (
        raw.get("dex_number") == expected_dex
    ), f"{slug}: dex_number mismatch — got {raw.get('dex_number')!r}"

    assert (
        raw.get("generation") == expected_gen
    ), f"{slug}: generation mismatch — got {raw.get('generation')!r}"

    image_url = raw.get("image_url", "")
    assert (
        image_url
        and "artwork" in image_url
        and image_url.startswith("https://")
    ), f"{slug}: image_url looks wrong — got {image_url!r}"
