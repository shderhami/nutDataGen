"""Corrector-supplement delivered-spec CV (resolve_cv).

A corrector (ingredients.is_corrector) is a single-nutrient manufactured supplement.
The whole-food supplement floor overstates its variability, and because a corrector
delivers the bulk of the nutrient it corrects, that inflated CV dominates the
consumer's k*sigma buffer. So a corrector cell gets an OWN delivered-spec CV, which
wins the consumer's COALESCE(coefficient_of_variation, category_cv).

Regression for the formulator's scripts/patch_corrector_cvs.py being reverted by a
full cv_assign re-run: this pipeline must now reproduce that patch itself.
"""
from __future__ import annotations

import cv_config
from resolve_cv import resolve_cv


_EMPTY_LOOKUPS: dict = {"fine": {}, "coarse": {}, "prior": {}}

# Taurine (1234) — Bucket-A, labile, stable-CV corrector nutrient.
_TAURINE = dict(nutrient_id=1234, nutrient_nbr=529, ingredient_class="supplement",
                nutrient_class="amino_acid", category="Supplement", value=1000.0)
# Vitamin E (1109) — high-CV corrector nutrient (oxidation / premix stability).
_VIT_E = dict(nutrient_id=1109, nutrient_nbr=323, ingredient_class="supplement",
              nutrient_class="fat_sol_vit", category="Supplement", value=14.9)


def test_non_corrector_supplement_keeps_delivered_floor() -> None:
    r = resolve_cv(**_TAURINE, is_corrector=False, lookups=_EMPTY_LOOKUPS)
    assert r["measured_cv"] is None                       # no own CV
    assert r["category_cv"] == cv_config.SUPPLEMENT_DELIVERED_FLOOR_LABILE
    assert r["cv_tier"] == "supplement"


def test_corrector_gets_stable_spec_cv() -> None:
    r = resolve_cv(**_TAURINE, is_corrector=True, lookups=_EMPTY_LOOKUPS)
    assert r["measured_cv"] == cv_config.CORRECTOR_CV_STABLE
    assert r["cv_tier"] == "corrector"
    assert r["cv_method"] == "delivered_spec"


def test_corrector_high_cv_nutrient_gets_higher_spec_cv() -> None:
    r = resolve_cv(**_VIT_E, is_corrector=True, lookups=_EMPTY_LOOKUPS)
    assert r["measured_cv"] == cv_config.CORRECTOR_CV_HIGH
    assert r["cv_tier"] == "corrector"


def test_corrector_retains_category_floor_as_fallback() -> None:
    """The delivered floor stays in category_cv, so NULLing the own column is safe."""
    r = resolve_cv(**_VIT_E, is_corrector=True, lookups=_EMPTY_LOOKUPS)
    assert r["category_cv"] == cv_config.SUPPLEMENT_DELIVERED_FLOOR_LABILE
    assert r["measured_cv"] < r["category_cv"]


def test_corrector_spec_cv_wins_the_consumer_coalesce() -> None:
    r = resolve_cv(**_TAURINE, is_corrector=True, lookups=_EMPTY_LOOKUPS)
    effective = r["measured_cv"] if r["measured_cv"] is not None else r["category_cv"]
    assert effective == cv_config.CORRECTOR_CV_STABLE


def test_corrector_records_provenance() -> None:
    r = resolve_cv(**_TAURINE, is_corrector=True, lookups=_EMPTY_LOOKUPS)
    assert r["cv_method_inputs"] == {
        "cv_spec": cv_config.CORRECTOR_CV_STABLE,
        "category_floor": cv_config.SUPPLEMENT_DELIVERED_FLOOR_LABILE,
    }


def test_corrector_zero_value_still_carved_out() -> None:
    """A corrector row that delivers nothing gets NULL CVs, like any zero-mean cell.

    Mirrors the formulator patch's `WHERE n.value > 0`.
    """
    r = resolve_cv(**{**_TAURINE, "value": 0.0}, is_corrector=True, lookups=_EMPTY_LOOKUPS)
    assert r["measured_cv"] is None and r["category_cv"] is None
    assert r["cv_tier"] == "none"


def test_corrector_spec_cvs_are_valid_fractions() -> None:
    for cv in (cv_config.CORRECTOR_CV_STABLE, cv_config.CORRECTOR_CV_HIGH):
        assert 0.0 < cv <= cv_config.CV_CAP


def test_corrector_flag_ignored_for_non_supplement_category() -> None:
    """Only the supplement pre-emption consults is_corrector; whole foods are unaffected.

    (database.add_ingredient rejects the combination, but the ladder must not
    mis-resolve a legacy row that carries it.)
    """
    r = resolve_cv(nutrient_id=1234, nutrient_nbr=529, ingredient_class="muscle",
                   nutrient_class="amino_acid", category="Muscle Meat", value=100.0,
                   is_corrector=True, lookups=_EMPTY_LOOKUPS)
    assert r["cv_tier"] != "corrector"
