"""URL set parity — the most important test.

Fetches pokemondb.net's sitemap, applies our filter (regex + exclusions read
from `config/source/url_filter.json`), and asserts the resulting set is identical
to the set of URIs Coveo has indexed.

If this passes, the crawl picked up exactly what our intent said it should —
no more, no less. If it fails, the diagnostic output shows which URLs
disagree.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import httpx
import pytest

POKEMONDB_SITEMAP = "https://pokemondb.net/static/sitemaps/pokemondb.xml"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _fetch_sitemap_urls() -> list[str]:
    r = httpx.get(POKEMONDB_SITEMAP, timeout=30.0)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    return [loc.text for loc in root.findall(".//sm:loc", SITEMAP_NS)]


def _apply_filter(
    urls: list[str],
    include_regex: str,
    exclusion_substrings: list[str],
) -> set[str]:
    pattern = re.compile(include_regex)
    out: set[str] = set()
    for u in urls:
        if not pattern.match(u):
            continue
        if any(sub in u for sub in exclusion_substrings):
            continue
        out.add(u)
    return out


def test_indexed_uris_match_filtered_sitemap(
    indexed_uris: set[str],
    url_filter_config: dict,
) -> None:
    """Coveo's indexed URI set should exactly equal the sitemap URLs that
    pass our `all`-mode include + exclude filters.

    Both sides apply the same logic from `config/source/url_filter.json` — one via
    the Coveo crawler (in production), one via Python (here, in the test).
    Drift between them means the crawler didn't do what we asked.
    """
    cfg = url_filter_config["modes"]["all"]
    sitemap_urls = _fetch_sitemap_urls()
    expected = _apply_filter(
        sitemap_urls,
        cfg["include_regex"],
        cfg["exclusions_contains"],
    )

    only_in_expected = expected - indexed_uris
    only_in_actual = indexed_uris - expected

    if only_in_expected or only_in_actual:
        lines = [
            "",
            f"  Sitemap entries:          {len(sitemap_urls)}",
            f"  Expected (filter-passed): {len(expected)}",
            f"  Actually indexed:         {len(indexed_uris)}",
        ]
        if only_in_expected:
            sample = sorted(only_in_expected)[:10]
            lines.append(f"  Missing from index ({len(only_in_expected)}):")
            for u in sample:
                lines.append(f"    - {u}")
            if len(only_in_expected) > len(sample):
                lines.append(
                    f"    ... and {len(only_in_expected) - len(sample)} more"
                )
        if only_in_actual:
            sample = sorted(only_in_actual)[:10]
            lines.append(f"  Extra in index ({len(only_in_actual)}):")
            for u in sample:
                lines.append(f"    + {u}")
            if len(only_in_actual) > len(sample):
                lines.append(
                    f"    ... and {len(only_in_actual) - len(sample)} more"
                )
        raise AssertionError("\n".join(lines))


def test_index_count_is_in_reasonable_range(indexed_uris: set[str]) -> None:
    """Sanity check on absolute counts — the canonical Pokemon count through
    Gen 9 is 1,025; pokemondb.net adds a handful of separately-URL'd forms
    (Zacian-Crowned etc.) and pre-released Gen 10 placeholders. Anything
    in the 1,000-1,100 band is reasonable; outside that suggests the crawl
    is broken or the filter has drifted."""
    n = len(indexed_uris)
    assert 1000 <= n <= 1100, (
        f"Indexed count {n} outside expected range 1000-1100. "
        "Either the crawl is incomplete, the filter is wrong, or pokemondb.net "
        "has grown/shrunk significantly."
    )


def test_filter_funnel_pokemon_only(
    indexed_uris: set[str],
    url_filter_config: dict,
    capsys: pytest.CaptureFixture,
) -> None:
    """Explicit filter funnel: walks through each filter stage and asserts the
    counts at each step. Confirms our Coveo filter excludes non-Pokemon pages
    (moves, types, abilities, items, locations, aggregate pages) correctly.

    Prints a breakdown like:
        Total sitemap URLs:                12,915
        URLs in /pokedex/* (any):           6,458
        After include regex:                1,032
        After exclusion rules:              1,029
        Coveo indexed:                      1,029
    """
    sitemap_urls = _fetch_sitemap_urls()
    cfg = url_filter_config["modes"]["all"]
    include_regex = cfg["include_regex"]
    exclusions = cfg["exclusions_contains"]

    pokedex_section = [u for u in sitemap_urls if "/pokedex/" in u]
    pattern = re.compile(include_regex)
    after_include = [u for u in sitemap_urls if pattern.match(u)]
    after_exclude = [
        u for u in after_include if not any(sub in u for sub in exclusions)
    ]

    # Make these visible in the test output (use -s flag or check captured)
    with capsys.disabled():
        print()
        print(f"  Total sitemap URLs:              {len(sitemap_urls):>6,}")
        print(f"  URLs in /pokedex/* (any):        {len(pokedex_section):>6,}")
        print(f"  After include regex:             {len(after_include):>6,}")
        print(f"  After exclusion rules:           {len(after_exclude):>6,}")
        print(f"  Coveo indexed:                   {len(indexed_uris):>6,}")

    # Assertions
    assert (
        len(sitemap_urls) > 10_000
    ), f"Sitemap has only {len(sitemap_urls)} URLs — pokemondb.net structure may have changed"
    assert (
        len(pokedex_section) > len(after_include)
    ), "Include regex should narrow /pokedex/* — moves/types/etc. shouldn't all match it"
    # Coveo indexed count must equal the post-exclusion sitemap-filtered count
    assert len(after_exclude) == len(indexed_uris), (
        f"Filter funnel produced {len(after_exclude)} URLs but Coveo indexed {len(indexed_uris)}. "
        "The two should be equal — see test_indexed_uris_match_filtered_sitemap for the URL diff."
    )


# Non-Pokemon URLs that SHOULD have been excluded by our filter.
# If any of these are in the index, our exclusion rules are broken.
NON_POKEMON_URLS_SHOULD_NOT_BE_INDEXED = [
    # Move pages
    "https://pokemondb.net/move/tackle",
    "https://pokemondb.net/move/thunderbolt",
    # Type pages
    "https://pokemondb.net/type/fire",
    "https://pokemondb.net/type/water",
    # Ability pages
    "https://pokemondb.net/ability/overgrow",
    # Item pages
    "https://pokemondb.net/item/potion",
    # Aggregate /pokedex/* pages
    "https://pokemondb.net/pokedex/all",
    "https://pokemondb.net/pokedex/national",
    "https://pokemondb.net/pokedex/shiny",
    # Game listing pages
    "https://pokemondb.net/pokedex/game/red-blue",
    # Stats aggregate
    "https://pokemondb.net/pokedex/stats/height-weight",
]


def test_non_pokemon_urls_are_excluded(indexed_uris: set[str]) -> None:
    """Explicitly verify that known non-Pokemon URLs are NOT in the index.
    If any of these slipped through, our exclusion rules have a hole."""
    leaks = [
        u for u in NON_POKEMON_URLS_SHOULD_NOT_BE_INDEXED if u in indexed_uris
    ]
    assert not leaks, (
        "\n  These non-Pokemon URLs should be excluded but are indexed:\n    "
        + "\n    ".join(leaks)
    )
