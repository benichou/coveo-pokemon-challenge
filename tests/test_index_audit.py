"""Index audit — every indexed URI is independently verified as a real Pokemon.

This complements `test_url_set_parity.py`. Parity says "the indexed set matches
what our filter intends to allow" — but the filter itself could be wrong
(e.g., it admits `/pokedex/shiny` because that URL shape was never anticipated).
This file asserts "every indexed item is, in fact, a real Pokemon page" using
two external sources of truth that don't depend on our filter:

  1. PokéAPI (https://pokeapi.co) — advisory; narrows the candidate set.
  2. The pokemondb.net page HTML — authoritative; real Pokedex entries have
     a `<th>National №</th>` row in their vitals table that aggregate / list
     pages (like /pokedex/shiny or /pokedex/all) don't.

Mirrors the analysis done by `scripts/audit/audit_index.py`. The script is for
ad-hoc and CI use without pytest; this file catches drift on every test run.
"""

from __future__ import annotations

import re

import httpx
import pytest

URL_SHAPE = re.compile(r"^https://pokemondb\.net/pokedex/[a-z0-9-]+$")
SLUG_FROM_URI = re.compile(r"^https://pokemondb\.net/pokedex/([a-z0-9-]+)$")
# pokemondb HTML-encodes the № character — match the encoded form so the
# signature check is robust against future page redesigns.
POKEMON_PAGE_SIGNATURE = re.compile(
    r"<th[^>]*>\s*National\s+&#8470", re.IGNORECASE
)
POKEAPI_LIST_URL = "https://pokeapi.co/api/v2/pokemon?limit=2000"


def test_every_indexed_uri_has_pokemon_url_shape(
    indexed_uris: set[str],
) -> None:
    """Defense-in-depth: every indexed URI must match the include regex.

    Failing this means the URL filter on the Coveo source was bypassed —
    typically because someone edited it in the Admin Console UI without
    going through `source/widen.sh`. The fix is to re-apply the filter
    from `config/source/url_filter.json`.
    """
    violations = sorted(u for u in indexed_uris if not URL_SHAPE.match(u))
    assert not violations, (
        f"\n  {len(violations)} indexed URI(s) don't match {URL_SHAPE.pattern}:\n    "
        + "\n    ".join(violations[:20])
    )


def test_every_indexed_item_is_a_real_pokemon(
    indexed_uris: set[str],
    capsys: pytest.CaptureFixture,
) -> None:
    """Catches the `/pokedex/shiny` class of leak: aggregate pages whose URL
    shape passes the filter but whose content is not a Pokemon.

    Two passes:
      - PokéAPI cross-reference narrows the index to candidates (slugs we
        don't recognize as canonical Pokemon). Pre-release Gen 10 Pokemon
        and form variants legitimately end up in this set — that's why
        PokéAPI is advisory, not authoritative.
      - For each candidate, fetch pokemondb.net's page and look for the
        `<th>National №</th>` row. Every real Pokedex entry has it.
        Anything that doesn't is a confirmed leak.
    """
    r = httpx.get(POKEAPI_LIST_URL, timeout=30.0)
    r.raise_for_status()
    pokeapi_slugs = {entry["name"] for entry in r.json().get("results", [])}

    indexed_slugs: dict[str, str] = {}
    for uri in indexed_uris:
        m = SLUG_FROM_URI.match(uri)
        if m:
            indexed_slugs[m.group(1)] = uri

    candidates = sorted(s for s in indexed_slugs if s not in pokeapi_slugs)

    leaks: list[str] = []
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for slug in candidates:
            try:
                resp = client.get(f"https://pokemondb.net/pokedex/{slug}")
                if resp.status_code != 200 or not POKEMON_PAGE_SIGNATURE.search(
                    resp.text
                ):
                    leaks.append(indexed_slugs[slug])
            except httpx.HTTPError:
                leaks.append(indexed_slugs[slug])

    with capsys.disabled():
        print()
        print(f"  Indexed URIs:                  {len(indexed_uris):>4}")
        print(f"  PokéAPI canonical list:        {len(pokeapi_slugs):>4}")
        print(f"  PokéAPI-unknown candidates:    {len(candidates):>4}")
        print(f"  Confirmed leaks (Pass C fail): {len(leaks):>4}")

    assert not leaks, (
        f"\n  {len(leaks)} indexed URI(s) are NOT real Pokemon pages:\n    "
        + "\n    ".join(leaks)
        + "\n\n  Fix:"
        + "\n    1. scripts/audit/audit_index.py    # confirms the leaks + writes audit_report.json"
        + "\n    2. scripts/audit/purge_index.sh    # updates config/source/url_filter.json + rebuilds"
    )
