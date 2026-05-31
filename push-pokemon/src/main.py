"""Orchestrator — the entry point you run.

End-to-end flow:

  1. Fetch the PokéAPI /pokemon list (~1,300 entries).
  2. For each entry, GET /pokemon/{name} for full detail.
  3. Filter to form variants only (filter.is_form_variant).
  4. For each form, also GET /pokemon-species/{species} so we have the
     generation. We do this once per *species*, not per form (Charizard
     has 2 forms; we fetch /pokemon-species/charizard once).
  5. Transform → Coveo Push documents.
  6. SET_STATUS REBUILD on the Push source.
  7. Push documents in batches of 50.
  8. SET_STATUS IDLE.

Idempotent: every push of the same documentId replaces, doesn't duplicate.
Re-runnable: kick it off again whenever PokéAPI grows.

Usage:
    uv run python -m main                  # full push (~277 form documents)
    uv run python -m main --dry-run        # show what would be pushed, no API calls
    uv run python -m main --limit 5        # push only the first 5 forms (smoke test)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from filter import base_species_of, is_form_variant
from pokeapi import (
    BASE_URL,
    _request_with_retry,
    fetch_pokemon_detail,
    list_all_pokemon,
)
from push import CoveoPushClient
from transform import transform

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

BATCH_SIZE = 50


def _fetch_species_cached(
    client: httpx.Client, species_slug: str, cache: dict
) -> dict | None:
    """Fetch /pokemon-species/{slug}; cache per process so each species is
    hit at most once even if it has multiple form variants."""
    if species_slug in cache:
        return cache[species_slug]
    try:
        data = _request_with_retry(
            client, f"{BASE_URL}/pokemon-species/{species_slug}"
        )
    except RuntimeError:
        data = None
    cache[species_slug] = data
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be pushed without making any Coveo API calls.",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only push the first N form variants (smoke test).",
    )
    ap.add_argument(
        "--replace",
        action="store_true",
        help="Delete every existing document in the Push source before pushing. "
        "Use after changing filter/transform logic to clean out stale docs that "
        "the new filter would no longer push.",
    )
    args = ap.parse_args()

    org_id = os.environ.get("COVEO_ORG_ID")
    source_id = os.environ.get("COVEO_PUSH_SOURCE_ID")
    api_key = os.environ.get("COVEO_PUSH_API_KEY")

    if not args.dry_run and not all([org_id, source_id, api_key]):
        print(
            "ERROR: COVEO_ORG_ID, COVEO_PUSH_SOURCE_ID, COVEO_PUSH_API_KEY "
            "must be set in .env",
            file=sys.stderr,
        )
        return 1

    print("=" * 64)
    print("pokemondb-push — pushing PokéAPI form variants to Coveo Source B")
    print("=" * 64)

    documents: list[dict] = []
    species_cache: dict[str, dict | None] = {}
    skipped_bases = 0

    with httpx.Client(timeout=30.0) as client:
        print("\n[1/4] Listing all PokéAPI Pokemon...")
        all_pokemon = list_all_pokemon(client)
        print(f"      {len(all_pokemon)} entries.")

        print("\n[2/4] Fetching detail + filtering to form variants...")
        for i, entry in enumerate(all_pokemon, 1):
            if args.limit and len(documents) >= args.limit:
                break
            name = entry["name"]
            try:
                detail = fetch_pokemon_detail(client, name)
            except RuntimeError as e:
                print(f"      [warn] {name}: {e}")
                continue

            if not is_form_variant(detail):
                skipped_bases += 1
                continue

            species_slug = base_species_of(detail)
            species_detail = _fetch_species_cached(
                client, species_slug, species_cache
            )

            doc = transform(detail, species_detail)
            documents.append(doc)

            if len(documents) % 25 == 0:
                print(
                    f"      progress: scanned {i}/{len(all_pokemon)}, "
                    f"queued {len(documents)} forms"
                )

        print(
            f"      Filtered: {len(documents)} forms kept, {skipped_bases} base species skipped."
        )

    if not documents:
        print("\nNo form variants to push. Exiting.")
        return 0

    print(f"\n[3/4] Prepared {len(documents)} documents for Source B.")
    if args.dry_run:
        print("      --dry-run set; sample of first 3 documents:")
        for d in documents[:3]:
            print(
                f"        - {d['title']:30s} types={d.get('pokemon_type')} "
                f"abilities={d.get('abilities')}"
            )
        return 0

    print("\n[4/4] Pushing to Coveo Source B...")
    push = CoveoPushClient(org_id, source_id, api_key)

    print("      → SET_STATUS REBUILD")
    push.set_status("REBUILD")

    if args.replace:
        print(
            "      → clear_source (deleting all existing docs in pokemondb-push)"
        )
        push.clear_source()

    print(f"      → pushing in batches of {BATCH_SIZE}")
    pushed = 0
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        push.push_batch(batch)
        pushed += len(batch)
        print(
            f"        batch {i // BATCH_SIZE + 1}: {pushed}/{len(documents)} pushed"
        )

    print("      → SET_STATUS IDLE")
    push.set_status("IDLE")

    print("\nDone. The Coveo index will reflect the new items within a minute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
