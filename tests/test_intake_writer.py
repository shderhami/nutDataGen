"""Write gates and record planning (intake/writer.py) — no DB required."""
import json

import pytest

from intake.model import FEDIAF_BY_ID, FEDIAF_IDS, PUFA_COMPONENT_IDS, PUFA_TOTAL_ID
from intake.spec import IntakeSpec, load_spec
from intake.writer import GateFailure, apply, check_gates, load_decisions, plan_records


@pytest.fixture()
def spec(tmp_path):
    path = tmp_path / "test_food.json"
    path.write_text(json.dumps({
        "slug": "test_food",
        "food": {
            "food_name": "test food raw", "category": "Muscle Meat",
            "base_unit": "g", "portion_qty": 100.0, "grams_per_unit": 1.0,
            "sr_legacy_fdc_id": 111111,
        },
        "sources": {},
    }))
    return load_spec(path)


def full_decisions(overrides=None):
    decisions = {}
    for nid in FEDIAF_IDS:
        decisions[nid] = {
            "value": 1.0, "source": "sr_legacy",
            "comment": "Validated 2026-08-17: test",
        }
    for nid in PUFA_COMPONENT_IDS:
        decisions[nid]["value"] = 0.1
    decisions[PUFA_TOTAL_ID]["value"] = 1.0
    for nid, d in (overrides or {}).items():
        decisions[nid] = d
    return decisions


class TestGates:
    def test_all_pass(self, spec):
        assert check_gates(spec, full_decisions()) == []

    def test_missing_nutrient(self, spec):
        decisions = full_decisions()
        del decisions[1234]
        assert any("missing nutrients" in p for p in check_gates(spec, decisions))

    def test_null_value(self, spec):
        decisions = full_decisions({1234: {"value": None, "source": None, "comment": ""}})
        assert any("no value" in p for p in check_gates(spec, decisions))

    def test_invalid_source(self, spec):
        decisions = full_decisions({1003: {"value": 1.0, "source": "vibes",
                                             "comment": "x"}})
        assert any("invalid" in p for p in check_gates(spec, decisions))

    def test_missing_comment(self, spec):
        decisions = full_decisions({1003: {"value": 1.0, "source": "sr_legacy",
                                             "comment": ""}})
        assert any("comment" in p for p in check_gates(spec, decisions))

    def test_bracket_violation(self, spec):
        decisions = full_decisions({1003: {
            "value": 1.0, "source": "sr_legacy", "comment": "x",
            "min_value": 2.0, "max_value": 3.0}})
        assert any("outside" in p for p in check_gates(spec, decisions))

    def test_one_sided_range(self, spec):
        decisions = full_decisions({1003: {
            "value": 1.0, "source": "sr_legacy", "comment": "x", "min_value": 0.5}})
        assert any("one-sided" in p for p in check_gates(spec, decisions))

    def test_pufa_invariant(self, spec):
        decisions = full_decisions()
        decisions[PUFA_TOTAL_ID]["value"] = 0.1   # < component sum 0.6
        assert any("PUFA invariant" in p for p in check_gates(spec, decisions))

    def test_apply_dry_run_refuses_on_gate_failure(self, spec):
        decisions = full_decisions()
        del decisions[1234]
        with pytest.raises(GateFailure):
            apply(spec, decisions, commit=False)


class TestPlanRecords:
    def test_records_are_complete_and_unit_converted(self, spec):
        decisions = full_decisions({1106: {
            "value": 7.0, "unit": "µg", "source": "sr_legacy",
            "comment": "vit A entered in payload µg"}})
        records = plan_records(spec, decisions, food_id=99999)
        assert len(records) == 52
        by_id = {r["nutrient_id"]: r for r in records}
        vit_a = by_id[1106]
        assert vit_a["unit"] == "IU" and vit_a["value"] == pytest.approx(23.31)
        assert "Unit normalized" in (vit_a["comment"] or "")
        for r in records:
            assert r["unit"] == FEDIAF_BY_ID[r["nutrient_id"]]["unit"]
            assert r["ai_recommendation"] is None

    def test_decisions_roundtrip(self, spec, tmp_path):
        payload = {"slug": "test_food", "decisions": [
            {"nutrient_id": nid, "verdict": "confirm",
             "decision": d} for nid, d in full_decisions().items()]}
        path = tmp_path / "decisions.json"
        path.write_text(json.dumps(payload))
        loaded = load_decisions(path)
        assert set(loaded) == set(FEDIAF_IDS)
        assert check_gates(spec, loaded) == []
