"""PokéAPI record → Coveo Push document.

Pure functions. No I/O. The output dict matches the field shape we mapped
on the Push source (see scripts/setup/mappings.sh `push` kind and
config/fields.json). Field names line up so the Atomic UI doesn't need
source-specific logic.

Coveo Push document shape (per docs.coveo.com/en/68):
  - `documentId`     unique URI for the item (REQUIRED)
  - `title`          displayable title
  - `data`           plaintext body the index searches
  - `fileExtension`  e.g. ".html" — tells Coveo how to interpret `data`
  - <any other key>  becomes document metadata, mapped via source mappings
"""

from __future__ import annotations

from typing import Any

from filter import base_species_of, is_form_variant

# Map PokéAPI's "stat.name" to our indexed field names.
STAT_FIELD = {
    "hp": "base_hp",
    "attack": "base_attack",
    "defense": "base_defense",
    "special-attack": "base_sp_attack",
    "special-defense": "base_sp_defense",
    "speed": "base_speed",
}


def _format_name(slug: str) -> str:
    """`charizard-mega-x` → `Charizard Mega X`. Used as display title."""
    return " ".join(word.capitalize() for word in slug.split("-"))


def _format_type(slug: str) -> str:
    """`fire` → `Fire`. Match the casing pokemondb.net uses on the website
    so cross-source facets ('Fire' for both Source A and B) merge cleanly."""
    return slug.capitalize()


def _format_ability(slug: str) -> str:
    """`solar-power` → `Solar Power`. Display-friendly."""
    return " ".join(word.capitalize() for word in slug.split("-"))


def _generation_label(generation_id: int) -> str:
    """Match the format Source A uses: 'Generation 1', 'Generation 2', etc.
    Generation IDs in PokéAPI are 1-9 today (gen-1 through gen-9)."""
    return f"Generation {generation_id}"


def _generation_from_species(species_detail: dict | None) -> str:
    """species_detail is the result of GETting the /pokemon-species/{name}
    endpoint. Its `generation.url` ends in `/generation/<id>/`. Returns
    'Generation N' or '' if the data is missing."""
    if not species_detail:
        return ""
    gen_url = (species_detail.get("generation") or {}).get("url", "")
    # URL shape: https://pokeapi.co/api/v2/generation/3/
    try:
        gen_id = int(gen_url.rstrip("/").rsplit("/", 1)[-1])
    except (ValueError, IndexError):
        return ""
    return _generation_label(gen_id)


def transform(
    detail: dict,
    species_detail: dict | None = None,
) -> dict[str, Any]:
    """Convert one PokéAPI Pokemon record into a Coveo Push document.

    `detail` is the result of GET /pokemon/{name}.
    `species_detail` is the result of GET /pokemon-species/{species-name}
    — used only to look up the generation. Optional; if absent, the
    `generation` field is empty (still valid, just less useful).
    """
    name = detail["name"]
    species = base_species_of(detail)
    is_variant = is_form_variant(detail)

    types = [_format_type(t["type"]["name"]) for t in detail.get("types", [])]
    abilities = [
        _format_ability(a["ability"]["name"])
        for a in detail.get("abilities", [])
        if not a.get(
            "is_hidden"
        )  # skip hidden abilities to keep the list visible
    ]

    stats: dict[str, int] = {}
    for s in detail.get("stats", []):
        stat_name = s.get("stat", {}).get("name", "")
        field_name = STAT_FIELD.get(stat_name)
        if field_name:
            stats[field_name] = s.get("base_stat", 0)

    # PokéAPI's "official-artwork" is the high-res render that matches what
    # pokemondb.net uses. Fall back to the default sprite if missing.
    sprites = detail.get("sprites", {}) or {}
    artwork = (
        (sprites.get("other") or {})
        .get("official-artwork", {})
        .get("front_default")
    )
    image_url = artwork or sprites.get("front_default") or ""

    pokeapi_url = f"https://pokeapi.co/api/v2/pokemon/{name}"
    document_id = f"pokeapi://pokemon/{name}"
    # Link Push docs to the base species's pokemondb.net page. pokemondb
    # has one URL per species (Mega Charizard X / Y / Hisuian Decidueye /
    # etc. are sections on the base page, not standalone pages), so the
    # base-species URL is the user-meaningful click target for every form
    # variant. Source A docs already have a real pokemondb URL via their
    # sitemap-derived documentId, so this only affects Source B.
    clickable_uri = (
        f"https://pokemondb.net/pokedex/{species}"
        if species
        else pokeapi_url  # fallback for the rare entry with no species
    )

    doc: dict[str, Any] = {
        "documentId": document_id,
        "clickableUri": clickable_uri,
        "title": _format_name(name),
        "fileExtension": ".html",
        # Body: searchable plaintext describing the Pokemon. Keep it concise
        # but rich enough for RGA to ground answers on it.
        "data": (
            f"{_format_name(name)} is a Pokemon. "
            f"Type: {', '.join(types) if types else 'unknown'}. "
            f"Abilities: {', '.join(abilities) if abilities else 'none listed'}. "
            f"This is the '{name}' form of {species}."
        ),
        # Indexed metadata fields — names match the mappings on the Push source.
        "pokemon_name": _format_name(name),
        "pokemon_type": types,
        "image_url": image_url,
        "dex_number": detail.get("id", 0),
        "generation": _generation_from_species(species_detail),
        "abilities": abilities,
        "is_form_variant": "true" if is_variant else "false",
        "base_species": species,
        "pokeapi_url": pokeapi_url,
    }
    doc.update(stats)
    return doc
