"""Add-time FEDIAF unit conversion (fediaf_nutrients.fediaf_unit_factor +
database.create_nutrient_record).

USDA payloads deliver vitamin A as µg RAE and vitamin E as mg alpha-tocopherol;
the platform stores FEDIAF units (IU for vitamins A/D/E). These tests pin the
conversion factors (retinol basis for A — RAE := retinol in this DB), the
spelling normalization, the fail-loud contract for unknown pairs, and that a
converted record's stats columns stay unit-consistent with its value.
"""
import math

import pytest

from database import calculate_statistics, create_nutrient_record
from fediaf_nutrients import canonical_unit, fediaf_unit_factor


class TestCanonicalUnit:
    def test_spelling_variants_collapse(self):
        assert canonical_unit("µg") == "µg"
        assert canonical_unit("UG") == "µg"
        assert canonical_unit("ug") == "µg"
        assert canonical_unit("mcg") == "µg"
        assert canonical_unit("MG") == "mg"
        assert canonical_unit("iu") == "IU"
        assert canonical_unit(" G ") == "g"
        assert canonical_unit("KCAL") == "kcal"

    def test_unknown_unit_passes_through_stripped(self):
        assert canonical_unit(" kJ ") == "kJ"

    def test_none_stays_none(self):
        assert canonical_unit(None) is None


class TestFediafUnitFactor:
    def test_vitamin_a_ug_to_iu(self):
        assert fediaf_unit_factor(1106, "µg") == ("IU", 3.33)

    def test_vitamin_a_spelling_variants(self):
        assert fediaf_unit_factor(1106, "UG") == ("IU", 3.33)
        assert fediaf_unit_factor(1106, "mcg") == ("IU", 3.33)

    def test_vitamin_e_mg_to_iu(self):
        assert fediaf_unit_factor(1109, "mg") == ("IU", 1.49)

    def test_vitamin_d_ug_to_iu_defensive(self):
        # Pipeline fetches USDA 1110 (already IU); the µg factor is defensive.
        assert fediaf_unit_factor(1110, "µg") == ("IU", 40.0)

    def test_noop_when_already_fediaf_unit(self):
        assert fediaf_unit_factor(1106, "IU") == ("IU", 1.0)
        assert fediaf_unit_factor(1103, "µg") == ("µg", 1.0)  # selenium
        assert fediaf_unit_factor(1003, "g") == ("g", 1.0)    # protein

    def test_matching_spelling_variant_normalized_without_factor(self):
        assert fediaf_unit_factor(1100, "UG") == ("µg", 1.0)  # iodine
        assert fediaf_unit_factor(1087, "MG") == ("mg", 1.0)  # calcium

    def test_missing_unit_falls_back_to_declared(self):
        assert fediaf_unit_factor(1106, None) == ("IU", 1.0)
        assert fediaf_unit_factor(1106, "") == ("IU", 1.0)

    def test_untracked_nutrient_passes_through(self):
        assert fediaf_unit_factor(9999, "mg") == ("mg", 1.0)
        assert fediaf_unit_factor(None, "mg") == ("mg", 1.0)

    def test_unknown_pair_fails_loud(self):
        with pytest.raises(ValueError, match="No conversion"):
            fediaf_unit_factor(1008, "kJ")     # energy must arrive as kcal
        with pytest.raises(ValueError, match="No conversion"):
            fediaf_unit_factor(1106, "mg")     # no mg->IU factor for vit A


def _record(nutrient_id, unit, value, **kwargs):
    return create_nutrient_record(
        food_name="test food",
        food_id=99999,
        nutrient_id=nutrient_id,
        fediaf_nutrient_name="Test",
        usda_nutrient_name="Test",
        unit=unit,
        value=value,
        source="sr_legacy",
        **kwargs,
    )


class TestCreateRecordConversion:
    def test_vitamin_a_payload_converted_to_iu(self):
        rec = _record(1106, "µg", 23.0)
        assert rec["unit"] == "IU"
        assert rec["value"] == pytest.approx(76.59)
        assert rec["comment"] == (
            "Unit normalized: 23 µg -> 76.59 IU (x3.33, FEDIAF platform unit)"
        )

    def test_existing_comment_preserved(self):
        rec = _record(1106, "µg", 23.0, comment="SR Legacy (only source)")
        assert rec["comment"].startswith("SR Legacy (only source); Unit normalized: ")

    def test_vitamin_e_payload_converted_to_iu(self):
        rec = _record(1109, "mg", 0.7)
        assert rec["unit"] == "IU"
        assert rec["value"] == pytest.approx(1.043)

    def test_stats_scale_with_value(self):
        raw = _record(1109, "IU", 100.0, num_samples=8, min_value=50.0, max_value=150.0)
        conv = _record(1109, "mg", 100.0, num_samples=8, min_value=50.0, max_value=150.0)
        assert conv["min_value"] == pytest.approx(74.5)
        assert conv["max_value"] == pytest.approx(223.5)
        # SE/CI are derived AFTER conversion, so they scale by the same factor
        # (up to calculate_statistics's own 4-decimal rounding).
        assert conv["estimated_se"] == pytest.approx(raw["estimated_se"] * 1.49, abs=1e-3)
        assert conv["confidence_interval_lower"] == pytest.approx(
            raw["confidence_interval_lower"] * 1.49, abs=1e-3)
        assert conv["confidence_interval_upper"] == pytest.approx(
            raw["confidence_interval_upper"] * 1.49, abs=1e-3)
        # Bracket invariant holds in the converted record.
        assert conv["min_value"] <= conv["value"] <= conv["max_value"]
        assert (conv["confidence_interval_lower"] <= conv["value"]
                <= conv["confidence_interval_upper"])
        # range_uncertainty is a ratio — identical whichever unit came in.
        assert conv["range_uncertainty"] == pytest.approx(raw["range_uncertainty"])

    def test_stats_match_fresh_computation_on_converted_inputs(self):
        conv = _record(1106, "µg", 2.2, num_samples=8, min_value=1.09, max_value=3.0)
        expected = calculate_statistics(
            value=round(2.2 * 3.33, 6), standard_error=None, num_samples=8,
            min_value=round(1.09 * 3.33, 6), max_value=round(3.0 * 3.33, 6))
        assert conv["estimated_se"] == pytest.approx(expected["estimated_se"])
        assert conv["confidence_interval_lower"] == pytest.approx(
            expected["confidence_interval_lower"])
        assert conv["confidence_interval_upper"] == pytest.approx(
            expected["confidence_interval_upper"])
        assert conv["estimated_se"] == pytest.approx(
            (3.0 - 1.09) * 3.33 / 4.0 / math.sqrt(8), abs=1e-3)

    def test_zero_value_converts_cleanly(self):
        rec = _record(1106, "µg", 0.0)
        assert rec["unit"] == "IU"
        assert rec["value"] == 0.0
        assert "Unit normalized: 0 µg -> 0 IU" in rec["comment"]

    def test_iu_payload_untouched_no_breadcrumb(self):
        rec = _record(1106, "IU", 20.0, comment="AI estimate")
        assert rec["unit"] == "IU"
        assert rec["value"] == 20.0
        assert rec["comment"] == "AI estimate"

    def test_none_value_gets_declared_unit_without_note(self):
        rec = _record(1106, "µg", None)
        assert rec["unit"] == "IU"
        assert rec["value"] is None
        assert rec["comment"] is None
