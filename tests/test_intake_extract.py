"""Extraction orchestration fail-loud paths and central lineage tagging
(intake/extract.py) — round-2 audit regression tests."""
import json

import pytest

from intake import extract
from intake.model import SourceValue
from intake.spec import load_spec


def _spec(tmp_path, **food_overrides):
    food = {
        "food_name": "test food raw", "category": "Muscle Meat",
        "base_unit": "g", "portion_qty": 100.0, "grams_per_unit": 1.0,
        "sr_legacy_fdc_id": 173627, "cooking_method": None,
        "price_per_unit": 0.02, "protein_species": "chicken",
    }
    food.update(food_overrides)
    path = tmp_path / "spec.json"
    path.write_text(json.dumps({"slug": "t", "food": food, "sources": {}}))
    return load_spec(path)


class TestFailLoud:
    def test_string_fdc_id_is_coerced(self, tmp_path):
        spec = _spec(tmp_path, sr_legacy_fdc_id="173627")
        assert spec.sr_fdc_id == 173627
        extraction = extract.run(spec)
        assert extraction.sr   # would have been silently empty pre-fix

    def test_unknown_fdc_id_raises(self, tmp_path):
        spec = _spec(tmp_path, sr_legacy_fdc_id=999999999)
        with pytest.raises(KeyError, match="matched no rows"):
            extract.run(spec)

    def test_empty_adapter_result_raises(self, tmp_path, monkeypatch):
        spec = _spec(tmp_path)
        spec.sources = {"fcdb": [type("R", (), {"key": 795, "note": ""})()]}
        import intake.sources.fcdb as fcdb
        monkeypatch.setattr(fcdb, "extract", lambda key, note="": [])
        with pytest.raises(KeyError, match="produced no values"):
            extract.run(spec)


class TestCentralLineage:
    def test_adapter_level_declaration_tags_every_row(self, tmp_path, monkeypatch):
        # round-2 audit: lineage was a per-row flag one adapter had to
        # remember; the module attribute is applied centrally now
        spec = _spec(tmp_path)
        spec.sources = {"iodine_db": [type("R", (), {"key": "05098", "note": ""})()]}
        import intake.sources.iodine_db as iodine_db
        monkeypatch.setattr(
            iodine_db, "extract",
            lambda key, note="": [SourceValue(
                source="IodineDB", source_food="x", nutrient_id=1100,
                value=1.0)])   # note: adapter "forgot" the per-row flag
        extraction = extract.run(spec)
        iodine_rows = [sv for sv in extraction.foreign if sv.source == "IodineDB"]
        assert iodine_rows and all(sv.usda_lineage for sv in iodine_rows)
