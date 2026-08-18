"""Spec loading, including the curated literature-evidence channel (plan §5)."""
import json

import pytest

from intake.extract import literature_values
from intake.model import Q_ANALYSED, Q_COMPILED
from intake.spec import load_spec


def _write_spec(tmp_path, **extra):
    payload = {
        "slug": "test_food",
        "food": {
            "food_name": "test food raw", "category": "Muscle Meat",
            "base_unit": "g", "portion_qty": 100.0, "grams_per_unit": 1.0,
            "sr_legacy_fdc_id": 111111,
        },
        "sources": {},
        **extra,
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(payload))
    return path


class TestLiteratureBlock:
    def test_entries_parse_and_convert(self, tmp_path):
        spec = load_spec(_write_spec(tmp_path, literature=[
            {"source": "Spitze03", "item": "chicken dark meat",
             "nutrient_id": 1234, "value": 169, "unit": "mg", "n": 6,
             "note": "p6; mg/kg wet /10"},
            {"source": "NRC2006", "item": "chicken meat+skin",
             "nutrient_id": 1103, "value": 14, "unit": "µg",
             "quality": "compiled"},
            {"source": "Lit", "item": "retinol in µg",
             "nutrient_id": 1106, "value": 10, "unit": "µg"},
        ]))
        values = literature_values(spec)
        assert [sv.source for sv in values] == ["Spitze03", "NRC2006", "Lit"]
        taurine = values[0]
        assert taurine.value == 169 and taurine.n == 6
        assert taurine.quality == Q_ANALYSED and taurine.unit == "mg"
        assert values[1].quality == Q_COMPILED
        assert values[2].value == pytest.approx(33.3)   # µg -> IU x3.33
        assert values[2].unit == "IU"

    def test_range_converts_with_value(self, tmp_path):
        spec = load_spec(_write_spec(tmp_path, literature=[
            {"source": "Spitze03", "nutrient_id": 1234, "value": 33.7,
             "unit": "mg", "n": 12, "min": 30, "max": 38},
        ]))
        sv = literature_values(spec)[0]
        assert (sv.vmin, sv.vmax) == (30.0, 38.0)

    def test_missing_field_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="literature\\[0\\] missing"):
            load_spec(_write_spec(tmp_path, literature=[
                {"source": "X", "nutrient_id": 1234, "value": 1}]))

    def test_unknown_nutrient_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="unknown nutrient_id"):
            load_spec(_write_spec(tmp_path, literature=[
                {"source": "X", "nutrient_id": 9999, "value": 1, "unit": "mg"}]))

    def test_empty_block_is_fine(self, tmp_path):
        spec = load_spec(_write_spec(tmp_path))
        assert spec.literature == [] and literature_values(spec) == []

    def test_literature_lineage_declares_usda_derived_numbers(self, tmp_path):
        spec = load_spec(_write_spec(tmp_path, literature=[
            {"source": "SomeReview", "nutrient_id": 1234, "value": 50,
             "unit": "mg", "usda_lineage": True,
             "note": "review table reprints USDA figures"}]))
        assert literature_values(spec)[0].usda_lineage is True


class TestFdcIdCoercion:
    def test_quoted_ids_are_coerced_to_int(self, tmp_path):
        payload = {
            "slug": "t",
            "food": {
                "food_name": "t", "category": "Muscle Meat", "base_unit": "g",
                "portion_qty": 100.0, "grams_per_unit": 1.0,
                "sr_legacy_fdc_id": "173627", "foundation_fdc_id": "2646171",
            },
            "sources": {},
        }
        path = tmp_path / "coerce.json"
        path.write_text(json.dumps(payload))
        spec = load_spec(path)
        assert spec.sr_fdc_id == 173627 and spec.foundation_fdc_id == 2646171
