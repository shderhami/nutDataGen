"""Write gates and record planning (intake/writer.py) — no DB required."""
import json

import pytest

from intake.model import FEDIAF_BY_ID, FEDIAF_IDS, PUFA_COMPONENT_IDS, PUFA_TOTAL_ID
from intake.spec import load_spec
from intake.writer import GateFailure, apply, check_gates, load_decisions, plan_records

REVIEWED_META = {"slug": "test_food", "basename": "decisions.json",
                 "reviewed_by": "Shahab", "has_review_contract": False}


@pytest.fixture()
def spec(tmp_path):
    path = tmp_path / "test_food.json"
    path.write_text(json.dumps({
        "slug": "test_food",
        "food": {
            "food_name": "test food raw", "category": "Muscle Meat",
            "base_unit": "g", "portion_qty": 100.0, "grams_per_unit": 1.0,
            "sr_legacy_fdc_id": 111111, "cooking_method": None,
            "price_per_unit": 0.02, "protein_species": "chicken",
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


def problems_of(spec, decisions, meta=None):
    return check_gates(spec, decisions, meta)[0]


class TestGates:
    def test_all_pass(self, spec):
        problems, blockers = check_gates(spec, full_decisions(), REVIEWED_META)
        assert problems == [] and blockers == []

    def test_missing_nutrient(self, spec):
        decisions = full_decisions()
        del decisions[1234]
        assert any("missing nutrients" in p for p in problems_of(spec, decisions))

    def test_null_value(self, spec):
        decisions = full_decisions({1234: {"value": None, "source": None, "comment": ""}})
        assert any("no value" in p for p in problems_of(spec, decisions))

    def test_invalid_source(self, spec):
        decisions = full_decisions({1003: {"value": 1.0, "source": "vibes",
                                           "comment": "x"}})
        assert any("invalid" in p for p in problems_of(spec, decisions))

    def test_missing_comment(self, spec):
        decisions = full_decisions({1003: {"value": 1.0, "source": "sr_legacy",
                                           "comment": ""}})
        assert any("comment" in p for p in problems_of(spec, decisions))

    def test_bracket_violation(self, spec):
        decisions = full_decisions({1003: {
            "value": 1.0, "source": "sr_legacy", "comment": "x",
            "min_value": 2.0, "max_value": 3.0}})
        assert any("outside" in p for p in problems_of(spec, decisions))

    def test_one_sided_range(self, spec):
        decisions = full_decisions({1003: {
            "value": 1.0, "source": "sr_legacy", "comment": "x", "min_value": 0.5}})
        assert any("one-sided" in p for p in problems_of(spec, decisions))

    def test_pufa_invariant(self, spec):
        decisions = full_decisions()
        decisions[PUFA_TOTAL_ID]["value"] = 0.1   # < component sum 0.6
        assert any("PUFA invariant" in p for p in problems_of(spec, decisions))

    def test_censored_min_zero_rejected(self, spec):
        decisions = full_decisions({1100: {
            "value": 0.9, "source": "literature", "comment": "x",
            "num_samples": 35, "min_value": 0.0, "max_value": 9.5}})
        assert any("censored/zero minimum" in p for p in problems_of(spec, decisions))

    def test_stats_on_calculated_source_rejected(self, spec):
        decisions = full_decisions({1293: {
            "value": 1.0, "source": "calculated", "comment": "x",
            "num_samples": 4, "min_value": 0.5, "max_value": 1.5}})
        assert any("double-count" in p for p in problems_of(spec, decisions))

    def test_unconvertible_unit_fails_at_gate(self, spec):
        decisions = full_decisions({1003: {
            "value": 1.0, "unit": "IU", "source": "sr_legacy", "comment": "x"}})
        assert any("No conversion" in p for p in problems_of(spec, decisions))

    def test_string_value_is_a_problem_not_a_traceback(self, spec):
        # round-2 audit: a hand-edited "12.5" raised a bare TypeError
        decisions = full_decisions({1087: {
            "value": "12.5", "source": "sr_legacy", "comment": "x",
            "min_value": 10.0, "max_value": 14.0}})
        assert any("non-numeric" in p for p in problems_of(spec, decisions))

    def test_median_needs_range_and_bracket(self, spec):
        decisions = full_decisions({1003: {
            "value": 1.0, "source": "sr_legacy", "comment": "x",
            "median_value": 0.9}})
        assert any("median_value without" in p for p in problems_of(spec, decisions))
        decisions = full_decisions({1003: {
            "value": 1.0, "source": "sr_legacy", "comment": "x",
            "min_value": 0.5, "max_value": 1.5, "median_value": 9.0}})
        assert any("median outside" in p for p in problems_of(spec, decisions))

    def test_slug_mismatch_refused(self, spec):
        # round-2 audit: a decisions file from ANOTHER food passed every gate
        meta = dict(REVIEWED_META, slug="beef_liver")
        assert any("cross-wire" in p
                   for p in check_gates(spec, full_decisions(), meta)[0])

    def test_apply_dry_run_refuses_on_gate_failure(self, spec):
        decisions = full_decisions()
        del decisions[1234]
        with pytest.raises(GateFailure):
            apply(spec, decisions, commit=False)


class TestCommitBlockers:
    def test_food_block_problems_block_commit_not_dry_run(self, tmp_path, capsys):
        path = tmp_path / "bad_food.json"
        path.write_text(json.dumps({
            "slug": "bad_food",
            "food": {
                "food_name": "bad", "category": "Poultry",   # invalid category
                "base_unit": "g", "portion_qty": 100.0, "grams_per_unit": 1.0,
                "sr_legacy_fdc_id": 1, "price_per_unit": 0.0,  # missing price
                "bogus_field": 1,
            },
            "sources": {},
        }))
        spec = load_spec(path)
        meta = dict(REVIEWED_META, slug="bad_food")
        problems, blockers = check_gates(spec, full_decisions(), meta)
        assert problems == []
        joined = "\n".join(blockers)
        for expected in ("category", "price_per_unit", "bogus_field", "cooking_method"):
            assert expected in joined
        # dry-run previews anyway, printing the blockers (round-2 audit: the
        # shipped spec could not even preview)
        assert apply(spec, full_decisions(), commit=False, meta=meta) is None
        out = capsys.readouterr().out
        assert "COMMIT BLOCKER" in out and "Gates PASS" in out
        # commit refuses
        with pytest.raises(GateFailure, match="commit blockers"):
            apply(spec, full_decisions(), commit=True, signed_off_by="S", meta=meta)

    def test_corrector_coupling_checked_at_gate(self, tmp_path):
        path = tmp_path / "corr.json"
        path.write_text(json.dumps({
            "slug": "corr",
            "food": {
                "food_name": "corr", "category": "Muscle Meat",
                "base_unit": "g", "portion_qty": 100.0, "grams_per_unit": 1.0,
                "sr_legacy_fdc_id": 1, "cooking_method": None,
                "price_per_unit": 0.02, "protein_species": "chicken",
                "is_corrector": True,
            },
            "sources": {},
        }))
        _, blockers = check_gates(load_spec(path), full_decisions())
        assert any("is_corrector" in b for b in blockers)

    def test_supplements_out_of_scope(self, tmp_path):
        path = tmp_path / "supp.json"
        path.write_text(json.dumps({
            "slug": "supp",
            "food": {
                "food_name": "supp", "category": "Supplement",
                "base_unit": "g", "portion_qty": 100.0, "grams_per_unit": 1.0,
                "sr_legacy_fdc_id": 1, "cooking_method": None,
                "price_per_unit": 0.02,
            },
            "sources": {},
        }))
        _, blockers = check_gates(load_spec(path), full_decisions())
        assert any("out of intake scope" in b for b in blockers)

    def test_contested_verdict_needs_resolution(self, spec):
        decisions = full_decisions()
        decisions[1004]["_verdict"] = "review"
        _, blockers = check_gates(spec, decisions, REVIEWED_META)
        assert any("resolution" in b for b in blockers)
        decisions[1004]["resolution"] = "kept Foundation per trim-frame doctrine"
        _, blockers = check_gates(spec, decisions, REVIEWED_META)
        assert blockers == []


class TestReviewGates:
    def test_commit_refuses_proposed_file(self, spec):
        with pytest.raises(GateFailure, match="unreviewed output"):
            apply(spec, full_decisions(), commit=True, signed_off_by="Shahab",
                  meta={"slug": "test_food", "basename": "proposed_decisions.json",
                        "reviewed_by": "Shahab", "has_review_contract": False})

    def test_commit_refuses_lingering_review_contract_marker(self, spec):
        # round-2 audit: renaming the machine file was enough — now the
        # content marker must be removed too
        with pytest.raises(GateFailure, match="review_contract"):
            apply(spec, full_decisions(), commit=True, signed_off_by="Shahab",
                  meta={"slug": "test_food", "basename": "decisions.json",
                        "reviewed_by": "Shahab", "has_review_contract": True})

    def test_commit_requires_reviewed_by(self, spec):
        with pytest.raises(GateFailure, match="reviewed_by"):
            apply(spec, full_decisions(), commit=True, signed_off_by="Shahab",
                  meta={"slug": "test_food", "basename": "decisions.json",
                        "reviewed_by": "", "has_review_contract": False})

    def test_commit_requires_sign_off(self, spec):
        with pytest.raises(GateFailure, match="signed-off-by"):
            apply(spec, full_decisions(), commit=True, meta=REVIEWED_META)


class TestLoadDecisions:
    def test_entry_level_unit_is_honored(self, spec, tmp_path):
        # round-2 audit: a reviewed unit edit at entry level was discarded
        payload = {"slug": "test_food", "reviewed_by": "Shahab", "decisions": [
            {"nutrient_id": 1106, "unit": "µg", "verdict": "confirm",
             "decision": {"value": 7.0, "source": "sr_legacy", "comment": "x"}}]}
        path = tmp_path / "decisions.json"
        path.write_text(json.dumps(payload))
        loaded, meta = load_decisions(path)
        assert loaded[1106]["unit"] == "µg"
        records = plan_records(spec, {1106: loaded[1106]}, food_id=1)
        assert records[0]["unit"] == "IU"
        assert records[0]["value"] == pytest.approx(23.31)

    def test_decisions_roundtrip(self, spec, tmp_path):
        payload = {"slug": "test_food", "reviewed_by": "Shahab", "decisions": [
            {"nutrient_id": nid, "verdict": "confirm",
             "decision": d} for nid, d in full_decisions().items()]}
        path = tmp_path / "decisions.json"
        path.write_text(json.dumps(payload))
        loaded, meta = load_decisions(path)
        assert set(loaded) == set(FEDIAF_IDS)
        assert meta["reviewed_by"] == "Shahab"
        assert meta["basename"] == "decisions.json"
        assert meta["has_review_contract"] is False
        assert check_gates(spec, loaded, meta) == ([], [])


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
