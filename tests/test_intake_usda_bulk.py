"""Golden pins for the USDA bulk extractor (pinned data/usda_bulk files)."""
import math

import pytest

from intake.model import Q_ANALYSED, Q_BORROWED, Q_COMPUTED
from intake.usda_bulk import extract_many


@pytest.fixture(scope="module")
def thigh_pair():
    return extract_many([2646171, 173627])


class TestFoundation:
    def test_fat_analytical_with_range(self, thigh_pair):
        sv = thigh_pair[2646171][1004]
        assert math.isclose(sv.value, 7.916, rel_tol=1e-3)
        assert sv.n == 8 and sv.vmin == 6.31 and sv.vmax == 9.92
        assert sv.quality == Q_ANALYSED

    def test_protein_flagged_nitrogen_calculated(self, thigh_pair):
        sv = thigh_pair[2646171][1003]
        assert math.isclose(sv.value, 18.6125, rel_tol=1e-4)
        assert sv.quality == Q_COMPUTED and "NC" in sv.note


class TestCrosswalks:
    """The maiden pair exercises neither crosswalk (SR publishes both sides),
    so these pins cover the fill/precedence/MK-4 layer explicitly."""

    @pytest.fixture(scope="class")
    def foods(self):
        # salmon FND: retinol 1105 only; pollock FND: vit D 1114 only;
        # fortified cheese: BOTH 1114 and published 1110; feta: MK-4 only
        return extract_many([2684441, 2768206, 325198, 2684242])

    def test_retinol_fills_rae_with_iu_conversion(self, foods):
        sv = foods[2684441][1106]
        assert math.isclose(sv.value, 2.151 * 3.33, rel_tol=1e-3)
        assert sv.n == 8 and "crosswalk" in sv.note

    def test_vitd_ug_fills_iu_slot(self, foods):
        sv = foods[2768206][1110]
        assert sv.value == 0.0 and "x40" in sv.note

    def test_published_target_beats_crosswalk(self, foods):
        sv = foods[325198][1110]
        assert sv.value == 301.0 and "crosswalk" not in sv.note

    def test_mk4_only_food_gets_mk4_form_not_k1_label(self, foods):
        from intake.model import FORM_MK4_ONLY
        sv = foods[2684242][1185]
        assert sv.value == 4.5 and sv.form == FORM_MK4_ONLY
        assert "MK-4" in sv.note and "K1 only" not in sv.note


class TestSRLegacy:
    def test_vitamin_a_converted_to_iu(self, thigh_pair):
        sv = thigh_pair[173627][1106]
        assert math.isclose(sv.value, 7 * 3.33)
        assert sv.n == 1

    def test_vitamin_e_converted_to_iu(self, thigh_pair):
        assert math.isclose(thigh_pair[173627][1109].value, 0.18 * 1.49)

    def test_vitamin_d_already_iu(self, thigh_pair):
        assert thigh_pair[173627][1110].value == 1.0

    def test_borrowed_vitamin_k_flagged(self, thigh_pair):
        sv = thigh_pair[173627][1185]
        assert sv.quality == Q_BORROWED and "BFYN" in sv.note

    def test_measured_lc_pufas(self, thigh_pair):
        sv = thigh_pair[173627][1278]
        assert sv.value == 0.002 and sv.n == 5 and sv.quality == Q_ANALYSED

    def test_selenium_with_range(self, thigh_pair):
        sv = thigh_pair[173627][1103]
        assert (sv.value, sv.n, sv.vmin, sv.vmax) == (22.9, 5, 15.8, 27.2)
