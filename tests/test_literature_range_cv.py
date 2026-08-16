"""literature_range measured tier (resolve_cv, cv-v7).

A validated (literature-sourced) row stores value + {min, max, n} from ONE
citation (e.g. chicken liver vitamin A from FCDB 712: 9400, 5100-14200, n=42).
Its CV must come from that same-source range, not from USDA sr28/component
candidates that describe the superseded estimate of a different sample.

The bracket guard (min <= value <= max) keeps the tier away from stale USDA
stats left behind by an override: egg-yolk niacin 10031/1167 stores value 0.07
against leftover stats {0.022..0.030, n=4} of the rejected SR value.
"""
from __future__ import annotations

import cv_config
import cv_stats
from resolve_cv import resolve_cv

_EMPTY_LOOKUPS: dict = {"fine": {}, "coarse": {}, "prior": {}}

# Chicken liver vitamin A (10002/1106) as validated on 2026-08-16.
_VIT_A = dict(nutrient_id=1106, nutrient_nbr=320, ingredient_class="organ",
              nutrient_class="fat_sol_vit", category="Organ Meat", value=9400.0)
_FCDB_STATS = dict(own_min=5100.0, own_max=14200.0, own_n=42)


def _expected_unshrunk_cv() -> float:
    cv = cv_stats.cv_from_range(9400.0, 5100.0, 14200.0, 42)
    assert cv is not None
    cv = max(cv, cv_config.CV_FLOOR)
    cv, _ = cv_stats.clip_cv(cv, cv_config.CV_CAP)
    return round(cv, cv_config.ROUND_DECIMALS)


def test_literature_row_with_stats_resolves_literature_range() -> None:
    r = resolve_cv(**_VIT_A, **_FCDB_STATS, source="literature",
                   component_cv=0.2591, component_n=4, lookups=_EMPTY_LOOKUPS)
    assert r["cv_tier"] == "literature_range"
    assert r["cv_method"] == "wan_range"
    assert r["cv_backing_n"] == 42
    assert r["measured_cv"] == _expected_unshrunk_cv()
    assert r["cv_confidence_tier"] == "medium"
    # The preempted USDA candidate is kept for audit.
    assert r["cv_method_inputs"]["superseded_component_cv"] == 0.2591


def test_literature_without_stats_falls_back_to_component() -> None:
    r = resolve_cv(**_VIT_A, source="literature",
                   component_cv=0.2591, component_n=4, lookups=_EMPTY_LOOKUPS)
    assert r["cv_tier"] == "component"
    assert r["cv_method"] == "retinol"


def test_sr_legacy_row_keeps_existing_ladder() -> None:
    """A USDA-sourced row with own stats must NOT enter the literature tier."""
    r = resolve_cv(**_VIT_A, **_FCDB_STATS, source="sr_legacy",
                   sr28_se_cv=0.30, sr28_n=10, sr28_method="se_sqrt_n",
                   lookups=_EMPTY_LOOKUPS)
    assert r["cv_tier"] == "sr28_se"


def test_incoherent_stats_bracket_guard() -> None:
    """Egg-yolk-niacin shape: stale stats of a rejected value do not drive a CV."""
    r = resolve_cv(nutrient_id=1167, nutrient_nbr=406, ingredient_class="egg",
                   nutrient_class="b_vitamin", category="Egg", value=0.07,
                   own_min=0.022, own_max=0.030, own_n=4, source="literature",
                   sr28_se_cv=0.17, sr28_n=6, sr28_method="se_sqrt_n",
                   lookups=_EMPTY_LOOKUPS)
    assert r["cv_tier"] != "literature_range"
    assert r["cv_tier"] == "sr28_se"
