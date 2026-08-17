"""cv-v8 international same-food CV pooling (resolve_cv).

A matched foreign observation is credited at the DISCOUNTED effective
n_eff = 1/(1/n + 2*sigma^2), never its raw n: sigma^2 is the measured
between-population wobble of ln(CV), so foreign credit saturates near
1/(2*sigma^2) samples no matter how large the foreign study is.
"""
from __future__ import annotations

import math

import cv_config
from resolve_cv import resolve_cv

_EMPTY_LOOKUPS: dict = {"fine": {}, "coarse": {}, "prior": {}}

_CELL = dict(nutrient_id=1103, nutrient_nbr=317, ingredient_class="organ",
             nutrient_class="se_i", category="Organ Meat", value=40.0)
_INTL = dict(intl_cv=0.30, intl_n=14, intl_label='FCDB 6.1 742 "Liver, ox, raw" Selenium')


def _expected(us_cv, us_n, intl_cv, intl_n):
    n_eff = 1.0 / (1.0 / intl_n + 2.0 * cv_config.INTL_CV_SIGMA2)
    w = us_n / (us_n + n_eff)
    return math.exp(w * math.log(us_cv) + (1 - w) * math.log(intl_cv)), n_eff


def test_pooling_blends_at_discounted_weight() -> None:
    r = resolve_cv(**_CELL, sr28_se_cv=0.15, sr28_n=4, sr28_method="se_sqrt_n",
                   **_INTL, lookups=_EMPTY_LOOKUPS)
    exp, n_eff = _expected(0.15, 4, 0.30, 14)
    assert r["cv_method"] == "se_sqrt_n+intl"
    assert abs(r["measured_cv"] - round(max(exp, cv_config.CV_FLOOR), 6)) < 1e-6
    assert r["cv_backing_n"] == 4 + max(1, round(n_eff))   # honest decomposition
    intl = r["cv_method_inputs"]["intl"]
    assert intl["n"] == 14 and intl["source"].startswith("FCDB")
    assert 0 < intl["n_eff"] < 3   # saturating credit, never the raw n


def test_ceiling_saturates_regardless_of_foreign_n() -> None:
    _, n_small = _expected(0.15, 4, 0.30, 8)
    _, n_big = _expected(0.15, 4, 0.30, 85)
    assert n_big < 1 / (2 * cv_config.INTL_CV_SIGMA2) + 0.01
    assert n_big - n_small < 1.0   # tenfold more foreign samples adds <1 credit


def test_no_intl_leaves_resolution_unchanged() -> None:
    a = resolve_cv(**_CELL, sr28_se_cv=0.15, sr28_n=4, sr28_method="se_sqrt_n",
                   lookups=_EMPTY_LOOKUPS)
    assert a["cv_method"] == "se_sqrt_n"
    assert "intl" not in (a["cv_method_inputs"] or {})


def test_literature_range_cells_do_not_double_count() -> None:
    """A literature_range cell's own stats are often the same foreign dataset."""
    r = resolve_cv(**_CELL, source="literature", own_min=20.0, own_max=60.0, own_n=14,
                   **_INTL, lookups=_EMPTY_LOOKUPS)
    assert r["cv_tier"] == "literature_range"
    assert "+intl" not in r["cv_method"]
    assert "intl" not in (r["cv_method_inputs"] or {})
