"""Facet sanity tests.

Queries the @generation facet **scoped to Source A** (the sitemap source)
and asserts canonical Pokemon counts per generation. pokemondb.net may have
a few separately-URL'd alternate forms that add to canonical totals (Mega
forms, regional variants), so we use "at least N" assertions with a small
tolerance ceiling for sanity.

The Source A scope matters: Source B (pokemondb-push) deliberately adds
~325 form variants per PokéAPI's coverage, which would inflate the
generation facet counts well past the canonical numbers if we didn't
filter. The dual-source separation guarantee is enforced by
`test_dual_source_separation.py`; this test focuses on Source A's
fidelity to the canonical species list.
"""

from __future__ import annotations

import httpx

SEARCH_HUB = "pokemon-search"

# Canonical counts as of Gen 9 release.
# https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number
# Tolerance: pokemondb.net may add separately-URL'd forms (Zacian-Crowned,
# Hisuian Decidueye, etc.). We assert minimum >= canonical, max not too far above.
CANONICAL_GEN_COUNTS = {
    "Generation 1": 151,
    "Generation 2": 100,
    "Generation 3": 135,
    "Generation 4": 107,
    "Generation 5": 156,
    "Generation 6": 72,
    "Generation 7": 88,
    "Generation 8": 96,
    "Generation 9": 120,
}
# Allow generous slack for variant forms with their own pages
MAX_OVER_CANONICAL = 30


def _fetch_generation_facet(client: httpx.Client) -> dict[str, int]:
    """Return {generation_label: count} from the @generation facet,
    scoped to Source A only (see module docstring for why)."""
    body = {
        "q": "",
        "searchHub": SEARCH_HUB,
        "aq": "@source=pokemondb-sitemap",
        "numberOfResults": 0,  # we only want the facet, not results
        "facets": [
            {
                "facetId": "generation",
                "field": "generation",
                "type": "specific",
                "numberOfValues": 50,
            }
        ],
    }
    r = client.post("", json=body)
    r.raise_for_status()
    data = r.json()

    counts: dict[str, int] = {}
    for facet in data.get("facets", []):
        if facet.get("field") == "generation":
            for v in facet.get("values", []):
                counts[v["value"]] = v["numberOfResults"]
    return counts


def test_facet_returns_all_expected_generations(
    search_client: httpx.Client,
) -> None:
    counts = _fetch_generation_facet(search_client)
    missing = [g for g in CANONICAL_GEN_COUNTS if g not in counts]
    assert (
        not missing
    ), f"Generation facet missing {missing}. Got: {sorted(counts.keys())}"


def test_per_generation_counts_meet_canonical_minimum(
    search_client: httpx.Client,
) -> None:
    counts = _fetch_generation_facet(search_client)

    failures = []
    for gen, canonical in CANONICAL_GEN_COUNTS.items():
        actual = counts.get(gen, 0)
        if actual < canonical:
            failures.append(
                f"{gen}: indexed {actual} < canonical {canonical} (missing Pokemon?)"
            )
        elif actual > canonical + MAX_OVER_CANONICAL:
            failures.append(
                f"{gen}: indexed {actual} much higher than canonical {canonical} "
                f"(more than +{MAX_OVER_CANONICAL} — unexpected scope creep?)"
            )

    if failures:
        raise AssertionError("\n  ".join([""] + failures))
