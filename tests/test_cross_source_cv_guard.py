"""Cross-source plausibility guard (resolve_cv).

A CROSS-SOURCED measured CV — a bulk SR28/FDC observation matched by food, a different
sample than the cell's value — above CROSS_SOURCE_CV_MAX (=1.0, i.e. SD > mean) is
rejected so the ladder falls to the same-source own-range CV or the class pool. The
SAME-SOURCE own-range CV (from the value's own min/max) is NEVER guarded.

Regression for the whole-egg Vitamin D 127% CV: value 98.4 IU from Foundation (no
dispersion), CV cross-sourced from an SR28 sample (mean 82, 39-368 IU spread).
"""
from __future__ import annotations

import cv_config
from resolve_cv import resolve_cv


def _lookups(pool_cv: float = 0.47, n_foods: int = 6) -> dict:
    """Minimal cv_class lookups with one fine egg/fat-sol-vit pool (Vit D, nbr 324)."""
    row = {"ingredient_class": "egg", "nutrient_nbr": 324, "nutrient_class": "fat_sol_vit",
           "pooled_cv": pool_cv, "n_foods": n_foods, "is_literature_prior": False}
    return {"fine": {("egg", 324): row}, "coarse": {}, "prior": {}}


_COMMON = dict(nutrient_id=1110, nutrient_nbr=324, ingredient_class="egg",
               nutrient_class="fat_sol_vit", category="Egg", value=98.4)


def test_cross_sourced_cv_over_1_demoted_to_pool() -> None:
    # The whole-egg Vit D case: cross-sourced SR28 CV 1.27 (>1) → rejected → pool.
    r = resolve_cv(**_COMMON, sr28_se_cv=1.27, sr28_n=10, sr28_method="se_sqrt_n",
                   source="foundation", lookups=_lookups())
    assert r["measured_cv"] is None                       # cross-sourced 1.27 rejected
    assert r["category_cv"] is not None                   # fell to the class pool
    # Demotion recorded in the JSON method_inputs; the boolean twin flag is untouched.
    assert r["cv_method_inputs"] == {"cross_source_demoted_cv": 1.27}
    assert r["cv_calibration_flag"] in (None, False)


def test_cross_sourced_cv_at_or_below_1_is_kept() -> None:
    r = resolve_cv(**_COMMON, sr28_se_cv=0.30, sr28_n=10, sr28_method="se_sqrt_n",
                   source="foundation", lookups=_lookups())
    assert r["measured_cv"] is not None                   # plausible → kept
    assert r["cv_tier"] == "sr28_se"
    assert "cross_source_demoted_cv" not in (r["cv_method_inputs"] or {})


def test_boundary_exactly_1_is_kept() -> None:
    # Guard is strictly ">"; CV == cap is still a (barely) plausible measurement.
    r = resolve_cv(**_COMMON, sr28_se_cv=cv_config.CROSS_SOURCE_CV_MAX, sr28_n=10,
                   sr28_method="se_sqrt_n", source="foundation", lookups=_lookups())
    assert r["measured_cv"] is not None and r["cv_tier"] == "sr28_se"


def test_same_source_own_range_over_1_is_not_guarded() -> None:
    # Cross-source SR28 CV 1.27 is dropped, but the SAME-SOURCE own-range CV (from the
    # value's own min/max, ~1.97 here) is kept — the guard only touches cross-sourced CVs.
    r = resolve_cv(**_COMMON, sr28_se_cv=1.27, sr28_n=10, sr28_method="se_sqrt_n",
                   own_min=1.0, own_max=600.0, own_n=10,
                   source="sr_legacy", lookups=_lookups())
    assert r["measured_cv"] is not None                   # same-source range kept
    assert r["cv_tier"] == "fdc_range"
    assert r["cv_method_inputs"]["cross_source_demoted_cv"] == 1.27   # noted for audit
