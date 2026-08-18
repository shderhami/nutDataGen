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
    so these pins cover the fill/precedence/MK-4 layer explicitly. Real-food
    pins where the pinned bulk has one; the MK-4/vit-D branches only occur on
    sub-sample rows (now filtered out), so those use synthetic rows through
    _finalize directly."""

    @pytest.fixture(scope="class")
    def foods(self):
        # salmon FND: retinol 1105 only; fortified cheese: BOTH 1114 and 1110
        return extract_many([2684441, 325198])

    def test_retinol_fills_rae_with_iu_conversion(self, foods):
        sv = foods[2684441][1106]
        assert math.isclose(sv.value, 2.151 * 3.33, rel_tol=1e-3)
        assert sv.n == 8 and "crosswalk" in sv.note

    def test_published_target_beats_crosswalk(self, foods):
        sv = foods[325198][1110]
        assert sv.value == 301.0 and "crosswalk" not in sv.note

    def test_vitd_ug_fills_iu_slot_synthetic(self):
        from intake.model import SourceValue
        from intake.usda_bulk import VITD_IU_ID, VITD_UG_ID, _finalize
        row = SourceValue(source="FND", source_food="synthetic",
                          nutrient_id=VITD_IU_ID, value=44.0, quality=Q_ANALYSED,
                          note="vit D µg (1114) x40 -> IU — crosswalk")
        out = _finalize({VITD_UG_ID: row})
        assert out[VITD_IU_ID].value == 44.0 and "x40" in out[VITD_IU_ID].note

    def test_mk4_only_food_gets_mk4_form_not_k1_label(self):
        from intake.model import FORM_MK4_ONLY, SourceValue
        from intake.usda_bulk import MK4_ID, VITK1_ID, _finalize
        mk4 = SourceValue(source="FND", source_food="synthetic",
                          nutrient_id=MK4_ID, value=4.5, quality=Q_ANALYSED)
        out = _finalize({MK4_ID: mk4})
        sv = out[VITK1_ID]
        assert sv.value == 4.5 and sv.form == FORM_MK4_ONLY
        assert "MK-4" in sv.note and "K1 only" not in sv.note

    def test_sub_sample_ids_do_not_resolve(self):
        # corpus sweep: a typo'd id landing on a sub_sample row must yield an
        # empty table (extract.run fails loud), not a plausible 1-row "food"
        res = extract_many([2684242, 2768206])   # feta + pollock sub-samples
        assert res[2684242] == {} and res[2768206] == {}

    def test_negative_carb_by_difference_clamped(self):
        # 2727567 (thigh meat+skin FND) publishes 1005 = -0.17 (NC artifact)
        sv = extract_many([2727567])[2727567][1005]
        assert sv.value == 0.0 and "clamped" in sv.note


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
