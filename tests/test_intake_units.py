"""Unit conversion contract of the intake pipeline (intake/units.py)."""
import math

import pytest

from intake.units import KJ_PER_KCAL, parse_per100g_unit, to_fediaf


class TestToFediaf:
    def test_identity_when_units_match(self):
        assert to_fediaf(1003, 19.66, "g") == 19.66      # protein g -> g
        assert to_fediaf(1103, 22.9, "µg") == 22.9        # selenium µg -> µg

    def test_vitamin_a_retinol_ug_to_iu(self):
        assert math.isclose(to_fediaf(1106, 7.0, "µg"), 23.31)

    def test_vitamin_e_mg_to_iu(self):
        assert math.isclose(to_fediaf(1109, 0.18, "mg"), 0.2682)

    def test_vitamin_d_ug_to_iu(self):
        assert math.isclose(to_fediaf(1110, 0.2, "µg"), 8.0)

    def test_mass_rescale_mg_to_g(self):
        # amino acids arrive as mg/100 g from MEXT/AFCD/FCDB
        assert math.isclose(to_fediaf(1213, 1500.0, "mg"), 1.5)

    def test_mass_rescale_ug_to_mg(self):
        # BLS stores B6/Cu/Mn in µg; platform stores mg
        assert math.isclose(to_fediaf(1175, 420.0, "µg"), 0.42)

    def test_spelling_variants(self):
        assert math.isclose(to_fediaf(1100, 6.0, "ug"), 6.0)
        assert math.isclose(to_fediaf(1087, 11.0, "MG"), 11.0)

    def test_kj_to_kcal(self):
        assert math.isclose(to_fediaf(1008, 506.0, "kJ"), 506.0 / KJ_PER_KCAL)

    def test_unknown_pair_fails_loud(self):
        with pytest.raises(ValueError):
            to_fediaf(1003, 1.0, "IU")   # protein in IU is nonsense
        with pytest.raises(ValueError):
            to_fediaf(1106, 1.0, "g")    # no g->IU route for vitamin A


class TestParseUnit:
    def test_strips_denominator(self):
        assert parse_per100g_unit("mg/100 g") == "mg"
        assert parse_per100g_unit("kJ/100g") == "kJ"
        assert parse_per100g_unit("µg/100 g") == "µg"
