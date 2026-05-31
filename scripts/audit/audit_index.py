#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.27",
#     "python-dotenv>=1.0",
# ]
# ///
"""Audit the Coveo index for non-Pokemon pages that slipped through the filter.

Why this script exists
----------------------
Our URL filter (config/source/url_filter.json) is regex + substring based. It excludes
the obvious non-Pokemon pages on pokemondb.net (moves, types, abilities, etc.),
but pokemondb.net occasionally publishes new aggregate / list pages whose URL
shape we didn't anticipate. When that happens, they sneak past the filter.

The /pokedex/shiny leak (2026-05-30) is the canonical example: a list page of
shiny sprites that matched our include regex but wasn't an actual Pokemon. We
caught it by hand by cross-referencing the indexed URIs against PokéAPI's
canonical Pokemon list, then verifying suspicious slugs by fetching their HTML
and looking for the `<th>National №</th>` row that real Pokedex entries have.

This script automates that exact analysis so the next leak is caught in
seconds instead of by chance.

Three passes
------------
Pass A — URL shape regex check.
    Every indexed URI must match ^https://pokemondb\\.net/pokedex/[a-z0-9-]+$.
    Defense-in-depth; the source filter should already prevent these.

Pass B — PokéAPI cross-reference.
    PokéAPI (https://pokeapi.co) is a free, curated REST API of canonical
    Pokemon data. Every entry in their /pokemon list is a real Pokemon. We
    diff our indexed slugs against theirs to get a CANDIDATE leak set.
    PokéAPI is advisory, not authoritative: pre-release Gen 10 Pokemon
    appear on pokemondb.net before PokéAPI ingests them, and PokéAPI splits
    forms into separate entries (deoxys-normal, deoxys-attack, ...) while
    pokemondb uses one canonical slug per species. So candidates are
    "worth a second look," not "confirmed bad."

Pass C — Structural verification.
    For each candidate, fetch the page and check for a `<th>National №</th>`
    row in the vitals table. This is the authoritative signal — every real
    Pokemon page has it, no aggregate / list page does.

Output
------
Read-only. Writes audit_report.json. Exits non-zero if any leaks found, so
this can be wired into CI as a drift detector. Apply corrections with
scripts/purge_index.sh.

Usage
-----
    scripts/audit_index.py
    scripts/audit_index.py --verbose
    scripts/audit_index.py --report /tmp/leaks.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

ORG_ID = os.environ["COVEO_ORG_ID"]
SEARCH_API_KEY = os.environ["COVEO_SEARCH_API_KEY"]
SEARCH_URL = "https://platform.cloud.coveo.com/rest/search/v2"
SEARCH_HUB = "pokemon-search"

POKEAPI_LIST_URL = "https://pokeapi.co/api/v2/pokemon?limit=2000"

URL_SHAPE = re.compile(r"^https://pokemondb\.net/pokedex/[a-z0-9-]+$")
SLUG_FROM_URI = re.compile(r"^https://pokemondb\.net/pokedex/([a-z0-9-]+)$")
# Real Pokedex pages have a "<th>National №</th>" row in the vitals table.
# Aggregate / list pages (e.g. /pokedex/shiny, /pokedex/all) don't.
POKEMON_PAGE_SIGNATURE = re.compile(
    r"<th[^>]*>\s*National\s+&#8470", re.IGNORECASE
)


def enumerate_indexed_uris() -> set[str]:
    """Paginate the Search API and collect every indexed URI."""
    uris: set[str] = set()
    page_size = 100
    first = 0
    with httpx.Client(timeout=30.0) as client:
        while True:
            r = client.post(
                SEARCH_URL,
                params={"organizationId": ORG_ID},
                headers={"Authorization": f"Bearer {SEARCH_API_KEY}"},
                json={
                    "q": "",
                    "searchHub": SEARCH_HUB,
                    "numberOfResults": page_size,
                    "firstResult": first,
                    "fieldsToInclude": ["sysuri"],
                },
            )
            r.raise_for_status()
            results = r.json().get("results", [])
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


def fetch_pokeapi_slugs() -> set[str]:
    """The canonical Pokemon list from PokéAPI — advisory ground truth."""
    r = httpx.get(POKEAPI_LIST_URL, timeout=30.0)
    r.raise_for_status()
    return {entry["name"] for entry in r.json().get("results", [])}


def is_real_pokemon_page(slug: str) -> bool:
    """Authoritative check: fetch the page, look for the vitals-table row."""
    url = f"https://pokemondb.net/pokedex/{slug}"
    try:
        r = httpx.get(url, timeout=15.0, follow_redirects=True)
        if r.status_code != 200:
            return False
        return bool(POKEMON_PAGE_SIGNATURE.search(r.text))
    except httpx.HTTPError:
        return False


def slug_from_uri(uri: str) -> str | None:
    m = SLUG_FROM_URI.match(uri)
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Audit the Coveo index for non-Pokemon leaks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--report",
        default=str(REPO_ROOT / "audit_report.json"),
        help="Path to write the JSON report (default: ./audit_report.json)",
    )
    ap.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print each candidate's verification result",
    )
    args = ap.parse_args()

    print("=" * 64)
    print("Coveo index audit — finding non-Pokemon leaks")
    print("=" * 64)

    print("\n[1/4] Enumerating indexed URIs via Search API...")
    indexed = enumerate_indexed_uris()
    print(f"      {len(indexed)} URIs in the Coveo index.")

    print("\n[2/4] Pass A — URL shape regex check")
    print(f"      Pattern: {URL_SHAPE.pattern}")
    shape_violations = sorted(u for u in indexed if not URL_SHAPE.match(u))
    if shape_violations:
        print(
            f"      [FAIL] {len(shape_violations)} URI(s) violate the URL shape:"
        )
        for u in shape_violations[:10]:
            print(f"        - {u}")
    else:
        print(f"      [PASS] All {len(indexed)} URIs match the expected shape.")

    print("\n[3/4] Pass B — PokéAPI cross-reference")
    pokeapi_slugs = fetch_pokeapi_slugs()
    print(f"      PokéAPI canonical list: {len(pokeapi_slugs)} entries.")
    indexed_slugs = {slug_from_uri(u): u for u in indexed if slug_from_uri(u)}
    candidates = sorted(
        s for s in indexed_slugs if s and s not in pokeapi_slugs
    )
    print(f"      {len(candidates)} indexed slug(s) not found in PokéAPI.")
    if candidates:
        print("      Note: form variants and pre-release Pokemon legitimately")
        print("      appear here. Pass C decides which are actual leaks.")

    print(
        f"\n[4/4] Pass C — Structural verification ({len(candidates)} candidates)"
    )
    print("      Looking for `<th>National №</th>` row on each page.")
    leaks: list[dict] = []
    for slug in candidates:
        url = indexed_slugs[slug]
        ok = is_real_pokemon_page(slug)
        if args.verbose or not ok:
            marker = "      [pass]" if ok else "      [LEAK]"
            print(f"{marker} {slug:30s} {url}")
        if not ok:
            leaks.append({"slug": slug, "uri": url})

    print("\n" + "=" * 64)
    print("Audit summary")
    print("=" * 64)
    print(f"  Indexed URIs:                  {len(indexed):>4}")
    print(f"  URL-shape violations:          {len(shape_violations):>4}")
    print(f"  PokéAPI-unknown candidates:    {len(candidates):>4}")
    print(f"  Confirmed leaks (Pass C fail): {len(leaks):>4}")

    report = {
        "indexed_count": len(indexed),
        "shape_violations": shape_violations,
        "pokeapi_candidates": candidates,
        "leaks": leaks,
    }
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(f"\n  Report: {args.report}")

    if leaks or shape_violations:
        print("\n  Next step: scripts/purge_index.sh")
        return 1

    print("\n  Index is clean — no leaks detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
