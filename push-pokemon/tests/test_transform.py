"""Unit tests for `transform.transform` and `filter.is_form_variant`.

These are pure-function tests: no network, no Coveo, no PokéAPI. They run
against hand-crafted fixtures that mimic the PokéAPI response shape.
"""

from __future__ import annotations

from filter import base_species_of, is_form_variant
from transform import transform

# --- fixtures ----------------------------------------------------------------

CHARIZARD_BASE_FIXTURE = {
    "name": "charizard",
    "id": 6,
    "is_default": True,
    "species": {"name": "charizard"},
    "types": [
        {"type": {"name": "fire"}},
        {"type": {"name": "flying"}},
    ],
    "abilities": [
        {"ability": {"name": "blaze"}, "is_hidden": False},
        {"ability": {"name": "solar-power"}, "is_hidden": True},
    ],
    "stats": [
        {"stat": {"name": "hp"}, "base_stat": 78},
        {"stat": {"name": "attack"}, "base_stat": 84},
        {"stat": {"name": "defense"}, "base_stat": 78},
        {"stat": {"name": "special-attack"}, "base_stat": 109},
        {"stat": {"name": "special-defense"}, "base_stat": 85},
        {"stat": {"name": "speed"}, "base_stat": 100},
    ],
    "sprites": {
        "front_default": "https://example.com/charizard.png",
        "other": {
            "official-artwork": {
                "front_default": "https://example.com/charizard-art.png"
            }
        },
    },
}

CHARIZARD_MEGA_X_FIXTURE = {
    **CHARIZARD_BASE_FIXTURE,
    "name": "charizard-mega-x",
    "id": 10034,
    "is_default": False,
    # Mega Charizard X swaps Flying for Dragon
    "types": [
        {"type": {"name": "fire"}},
        {"type": {"name": "dragon"}},
    ],
    "abilities": [
        {"ability": {"name": "tough-claws"}, "is_hidden": False},
    ],
}

# Deoxys Normal — the canonical Deoxys, what pokemondb's /pokedex/deoxys
# already represents. PokéAPI gives it a suffixed name (deoxys-normal) but
# flags it as the default. Should NOT be treated as a form variant.
DEOXYS_NORMAL_FIXTURE = {
    **CHARIZARD_BASE_FIXTURE,
    "name": "deoxys-normal",
    "id": 386,
    "is_default": True,
    "species": {"name": "deoxys"},
}

CHARIZARD_SPECIES_FIXTURE = {
    "name": "charizard",
    "generation": {"url": "https://pokeapi.co/api/v2/generation/1/"},
}


# --- tests -------------------------------------------------------------------


def test_is_form_variant_recognizes_base_species():
    """charizard (is_default=true) is not a form variant."""
    assert is_form_variant(CHARIZARD_BASE_FIXTURE) is False


def test_is_form_variant_recognizes_mega():
    """charizard-mega-x (is_default=false) is a form variant."""
    assert is_form_variant(CHARIZARD_MEGA_X_FIXTURE) is True


def test_is_form_variant_excludes_default_form_with_suffixed_name():
    """deoxys-normal has a suffixed name but is_default=true — pokemondb's
    /pokedex/deoxys already covers it, so it must NOT be pushed to Source B.
    This is the bug the earlier 'name != species' filter had.
    """
    assert is_form_variant(DEOXYS_NORMAL_FIXTURE) is False


def test_base_species_of_returns_species_slug():
    assert base_species_of(CHARIZARD_MEGA_X_FIXTURE) == "charizard"
    assert base_species_of(CHARIZARD_BASE_FIXTURE) == "charizard"


def test_transform_basic_fields():
    doc = transform(CHARIZARD_MEGA_X_FIXTURE, CHARIZARD_SPECIES_FIXTURE)

    assert doc["documentId"] == "pokeapi://pokemon/charizard-mega-x"
    assert doc["title"] == "Charizard Mega X"
    assert doc["fileExtension"] == ".html"
    assert doc["pokemon_name"] == "Charizard Mega X"
    assert doc["dex_number"] == 10034


def test_transform_types_capitalized():
    doc = transform(CHARIZARD_MEGA_X_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    # Match casing used on pokemondb.net so cross-source facets merge cleanly.
    assert doc["pokemon_type"] == ["Fire", "Dragon"]


def test_transform_abilities_filters_hidden():
    doc = transform(CHARIZARD_BASE_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    # Solar Power is_hidden=True, should be filtered out.
    assert doc["abilities"] == ["Blaze"]


def test_transform_abilities_formats_hyphenated_slugs():
    """Tough Claws comes from PokéAPI as 'tough-claws'."""
    doc = transform(CHARIZARD_MEGA_X_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    assert doc["abilities"] == ["Tough Claws"]


def test_transform_stats_mapped_to_field_names():
    doc = transform(CHARIZARD_MEGA_X_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    assert doc["base_hp"] == 78
    assert doc["base_attack"] == 84
    assert doc["base_defense"] == 78
    assert doc["base_sp_attack"] == 109
    assert doc["base_sp_defense"] == 85
    assert doc["base_speed"] == 100


def test_transform_form_flags_set_correctly():
    mega = transform(CHARIZARD_MEGA_X_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    base = transform(CHARIZARD_BASE_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    assert mega["is_form_variant"] == "true"
    assert mega["base_species"] == "charizard"
    assert base["is_form_variant"] == "false"
    assert base["base_species"] == "charizard"


def test_transform_prefers_official_artwork():
    doc = transform(CHARIZARD_MEGA_X_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    assert doc["image_url"] == "https://example.com/charizard-art.png"


def test_transform_falls_back_to_default_sprite():
    fixture = {
        **CHARIZARD_MEGA_X_FIXTURE,
        "sprites": {"front_default": "x.png"},
    }
    doc = transform(fixture, CHARIZARD_SPECIES_FIXTURE)
    assert doc["image_url"] == "x.png"


def test_transform_generation_from_species_url():
    doc = transform(CHARIZARD_MEGA_X_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    assert doc["generation"] == "Generation 1"


def test_transform_generation_empty_when_species_missing():
    doc = transform(CHARIZARD_MEGA_X_FIXTURE, None)
    assert doc["generation"] == ""


def test_transform_body_data_includes_searchable_text():
    doc = transform(CHARIZARD_MEGA_X_FIXTURE, CHARIZARD_SPECIES_FIXTURE)
    assert "Charizard Mega X" in doc["data"]
    assert "Fire" in doc["data"]
    assert "Dragon" in doc["data"]
    assert "Tough Claws" in doc["data"]
