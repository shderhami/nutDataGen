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
