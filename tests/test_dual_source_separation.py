"""Dual-source separation test — the reproducibility check for "Source A and
Source B don't overlap."

Why this exists
---------------
Source A (`pokemondb-sitemap`) indexes one document per pokemondb.net species
page (~1,028 docs). Source B (`pokemondb-push`) is meant to add *only* the
content Source A structurally cannot represent — form variants like
Mega Charizard X, Hisuian Decidueye, Galarian Zigzagoon, Deoxys Attack.

The risk: PokéAPI splits multi-form species into separate /pokemon records
(`deoxys-normal`, `deoxys-attack`, ...) and flags exactly one of them as
`is_default=true`. If Source B's filter naively accepted every PokéAPI
record whose slug differs from the species name, it would push the
`*-normal` / `*-altered` / `*-plant` / etc. default forms — which are
exactly what Source A already covers under the species's single URL.
That's silent duplication.

The fix lives in `push-pokemon/src/filter.py` (`is_form_variant` uses
PokéAPI's `is_default` flag). The test below is the *guarantee* that the
fix keeps working: for every doc Coveo has in `pokemondb-push`, fetch its
PokéAPI record and assert `is_default is False`. If anyone changes the
filter and breaks this property, this test fails on the next run.

Reproducibility for future developers
-------------------------------------
Run the whole pytest suite (`uv run pytest` from `tests/`). If THIS file's
test fails, the diagnostic output prints exactly which Push docs are
default forms (and therefore overlap with Source A), so the offending
filter change is easy to find and revert.
"""

from __future__ import annotations

import re
import time

import httpx
import pytest

POKEAPI_DETAIL_URL = "https://pokeapi.co/api/v2/pokemon/{slug}"
POKEAPI_TIMEOUT_S = 60.0
RETRY_BACKOFFS_S = (1.0, 3.0, 6.0)  # transient-failure retry schedule


def _fetch_pokeapi_detail(client: httpx.Client, slug: str) -> dict | None:
    """GET PokéAPI's /pokemon/{slug}; retry on timeout / 5xx / 429.

    Returns the JSON record, or None if non-retryable failure (4xx). PokéAPI
    is generally reliable but a 300+ call sweep can hit transient timeouts.
    """
    for backoff in (0.0, *RETRY_BACKOFFS_S):
        if backoff:
            time.sleep(backoff)
        try:
            r = client.get(
                POKEAPI_DETAIL_URL.format(slug=slug), timeout=POKEAPI_TIMEOUT_S
            )
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            continue  # retry
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            continue  # retry
        return None  # 404 etc. — won't recover
    return None


# Push doc URIs follow the shape: pokeapi://pokemon/<slug>
# (set by `transform.py`'s `documentId` construction).
PUSH_DOCID_RE = re.compile(r"^pokeapi://pokemon/([a-z0-9-]+)$")


@pytest.fixture(scope="session")
def push_uris(search_client: httpx.Client) -> set[str]:
    """All URIs currently indexed under Source B. Cached for the session."""
    uris: set[str] = set()
    page_size = 100
    first = 0
    while True:
        body = {
            "q": "",
            "searchHub": "pokemon-search",
            "numberOfResults": page_size,
            "firstResult": first,
            "aq": "@source=pokemondb-push",
            "fieldsToInclude": ["sysuri", "is_form_variant"],
        }
        r = search_client.post("", json=body)
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


def test_every_push_doc_has_pokeapi_slug_shape(push_uris: set[str]) -> None:
    """Push doc URIs must follow `pokeapi://pokemon/<slug>` — the shape
    `transform.py` produces. If a URI doesn't, either the transform was
    changed or something else pushed docs into this source."""
    violations = sorted(u for u in push_uris if not PUSH_DOCID_RE.match(u))
    assert not violations, (
        f"\n  {len(violations)} Push doc URI(s) don't match {PUSH_DOCID_RE.pattern}:\n    "
        + "\n    ".join(violations[:10])
    )


def test_every_push_doc_is_a_non_default_form(
    push_uris: set[str],
    capsys: pytest.CaptureFixture,
) -> None:
    """For every Push doc, fetch its PokéAPI record and assert
    `is_default is False`. A `True` here means the doc is the canonical
    species form that Source A already covers — that's an overlap bug.

    This is the test you'd add a Push doc URI to if you ever wanted to
    intentionally allow a default-form override; today the expectation
    is exactly zero.
    """
    if not push_uris:
        pytest.skip("Source B has no documents yet — nothing to check.")

    overlaps: list[tuple[str, str]] = []  # (slug, species)
    unreachable: list[str] = []
    with httpx.Client() as client:
        for uri in sorted(push_uris):
            m = PUSH_DOCID_RE.match(uri)
            if not m:
                continue  # shape violations are flagged by the other test
            slug = m.group(1)
            detail = _fetch_pokeapi_detail(client, slug)
            if detail is None:
                unreachable.append(slug)
                continue
            if detail.get("is_default") is True:
                species = (detail.get("species") or {}).get("name", "?")
                overlaps.append((slug, species))

    with capsys.disabled():
        print(f"\n  Source B docs checked:    {len(push_uris)}")
        print(f"  Default-form overlaps:    {len(overlaps)}")
        if unreachable:
            print(
                f"  Unreachable on PokéAPI:   {len(unreachable)} (skipped — see below)"
            )
            for slug in unreachable[:5]:
                print(f"    - {slug}")

    if overlaps:
        msg_lines = [
            f"\n  {len(overlaps)} Source B doc(s) are PokéAPI default forms",
            "  (these overlap with Source A's per-species page and should NOT be pushed):",
            "",
        ]
        for slug, species in overlaps[:20]:
            msg_lines.append(
                f"    - pokeapi://pokemon/{slug:30s}  (species: {species})"
            )
        msg_lines.append("")
        msg_lines.append("  Fix:")
        msg_lines.append(
            "    1. Verify push-pokemon/src/filter.py uses is_default==False"
        )
        msg_lines.append("    2. Re-push with cleanup:")
        msg_lines.append(
            "         cd push-pokemon && uv run python src/main.py --replace"
        )
        pytest.fail("\n".join(msg_lines))
