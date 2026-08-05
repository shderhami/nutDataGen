"""Guards against drift between the repo's deliberately-mirrored constant copies.

The DB CHECK constraints are mirrored in database.py (write-side validation) and
user_interaction.py (prompt vocabulary), and the corrector-category set is mirrored
again in cv_config.py (the CV ladder). These duplicates exist to keep the modules
decoupled; these tests make a one-sided edit fail loudly.
"""
from __future__ import annotations

import cv_config
import database
import user_interaction


def test_base_units_match() -> None:
    assert database.VALID_BASE_UNITS == user_interaction.VALID_BASE_UNITS


def test_categories_match() -> None:
    assert database.VALID_CATEGORIES == user_interaction.VALID_CATEGORIES


def test_cooking_methods_match() -> None:
    assert database.VALID_COOKING_METHODS == user_interaction.VALID_COOKING_METHODS


def test_sources_match() -> None:
    assert database.VALID_SOURCES == user_interaction.VALID_SOURCES
    assert database.SUPPLEMENT_INFO_SOURCES == user_interaction.SUPPLEMENT_INFO_SOURCES


def test_protein_species_match() -> None:
    assert database.VALID_PROTEIN_SPECIES == user_interaction.VALID_PROTEIN_SPECIES


def test_corrector_categories_match() -> None:
    assert database.CORRECTOR_CATEGORIES == user_interaction.CORRECTOR_CATEGORIES


def test_corrector_categories_match_the_cv_ladder() -> None:
    """resolve_cv only consults is_corrector inside SUPPLEMENT_CATEGORIES, so the
    write-side validation must permit exactly that set — no wider, no narrower."""
    assert set(database.CORRECTOR_CATEGORIES) == cv_config.SUPPLEMENT_CATEGORIES


def test_every_ingredient_class_category_is_a_valid_category() -> None:
    assert set(database.CATEGORY_TO_INGREDIENT_CLASS) == set(database.VALID_CATEGORIES)
