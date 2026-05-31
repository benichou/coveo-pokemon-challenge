"""Decide which PokéAPI entries are *form variants* (Source B's scope).

The goal of Source B is to index Pokemon that Source A (pokemondb-sitemap)
can't represent — pokemondb has one URL per species, so it can't show
Mega Charizard X having different types from base Charizard.

A "form variant" for our purposes is a PokéAPI entry that represents
*additional* content over what Source A already indexes. Examples:

  - `charizard-mega-x`   ← form variant ✓ (Mega X — pokemondb doesn't URL it)
  - `decidueye-hisui`    ← form variant ✓ (Hisuian — regional variant)
  - `pikachu-gmax`       ← form variant ✓ (Gigantamax)
  - `deoxys-attack`      ← form variant ✓ (alt forme)
  - `charizard`          ← base species ✗ (Source A already has it)
  - `deoxys-normal`      ← **default form ✗** (this IS what /pokedex/deoxys
                                              already represents on pokemondb)

The detection rule is **PokéAPI's `is_default` flag**, not name comparison.
PokéAPI splits multi-form species into separate /pokemon records, but flags
the canonical form (the one a normal user thinks of as "Deoxys" or
"Shaymin") as `is_default=true`. That default record overlaps with
pokemondb's single-URL representation. We want only `is_default=false`
entries — those are the *extra* content.

The earlier rule `name != species` was wrong because it caught entries
like `deoxys-normal` (where the name has a form suffix but it's still the
default form for the species). The `is_default` flag is authoritative.
"""

from __future__ import annotations


def is_form_variant(detail: dict) -> bool:
    """`detail` is a record from PokéAPI's /pokemon/{name} endpoint.

    Returns True iff this is a non-default form (one that pokemondb's
    single-URL-per-species sitemap can't represent). Uses PokéAPI's
    `is_default` flag as the authoritative signal.
    """
    return detail.get("is_default") is False


def base_species_of(detail: dict) -> str:
    """Return the species slug — the base species name regardless of form.
    For `charizard-mega-x` this returns `charizard`."""
    return (detail.get("species") or {}).get("name", "")
