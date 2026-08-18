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

    def test_blank_unit_fails_loud(self):
        # audit 2026-08-18: '' used to skip the IU factor (vit A 3.33x low)
        for bad in ("", "  ", None):
            with pytest.raises(ValueError, match="Missing unit"):
                to_fediaf(1106, 10.0, bad)  # type: ignore[arg-type]

    def test_kj_spelling_variant(self):
        assert math.isclose(to_fediaf(1008, 506.0, "KJ"), 506.0 / KJ_PER_KCAL)


class TestParseUnit:
    def test_strips_denominator(self):
        assert parse_per100g_unit("mg/100 g") == "mg"
        assert parse_per100g_unit("kJ/100g") == "kJ"
        assert parse_per100g_unit("µg/100 g") == "µg"


class TestHeaderAlignment:
    HEADER = ("Food", "Water (g)", "Chloride (mg)", "C20:5w3 (mg)")

    def test_aligned_map_passes(self):
        from intake.units import check_header_alignment
        check_header_alignment(
            self.HEADER, {1: "Water", 2: "Chloride", 3: "C20:5w3"}, "TEST")

    def test_shifted_map_fails_loud(self):
        from intake.units import check_header_alignment
        with pytest.raises(ValueError, match="no longer aligns"):
            check_header_alignment(
                self.HEADER, {1: "Chloride", 2: "Water"}, "TEST")

    def test_family_shift_is_caught(self):
        # round-2 audit: 'Vitamine K1' shifted onto a 'Vitamine E' column
        # passed the old longest-word check ('vitamine' matched both)
        from intake.units import check_header_alignment
        header = ("x", "Vitamine E (mg 100 g)", "Vitamine K1 (µg 100 g)")
        check_header_alignment(header, {2: "Vitamine K1"}, "TEST")
        with pytest.raises(ValueError, match="no longer aligns"):
            check_header_alignment(header, {1: "Vitamine K1"}, "TEST")

    def test_substring_cannot_vouch(self):
        # 'B1' must not pass on a 'Vitamine B12' cell
        from intake.units import check_header_alignment
        header = ("x", "Vitamine B12 ou Cobalamine (µg)")
        with pytest.raises(ValueError, match="no longer aligns"):
            check_header_alignment(header, {1: "B1"}, "TEST")

    def test_short_header_is_a_mismatch_not_indexerror(self):
        # round-2 audit: a shrunk dataset raised bare IndexError
        from intake.units import check_header_alignment
        with pytest.raises(ValueError, match="no longer aligns"):
            check_header_alignment(("only", "two"), {5: "Energy"}, "TEST")
