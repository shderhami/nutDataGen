"""
Tests for the Phase 5 calibration harness (plan 5.1).

The harness is the piece that turns "the confidence label is uncalibrated"
from an assertion into a number, so its scoring and pairing logic have to be
right or the numbers mislead. Pure logic is tested without the datasets; the
dataset-backed tests skip when the (gitignored) bulk CSVs are absent.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import calibration_harness as ch
import cv_config
from ai_validation import AIValidationResult

DATASETS_PRESENT = (cv_config.FDC_SRL_DIR / "food.csv").exists() and (
    cv_config.FDC_FDN_DIR / "food.csv"
).exists()
needs_datasets = pytest.mark.skipif(
    not DATASETS_PRESENT, reason="USDA bulk datasets not present (gitignored)"
)


def case(sr: float, fdn: float, nutrient_id: int = 1003) -> ch.LabeledCase:
    return ch.LabeledCase(
        fdc_id_sr=1, fdc_id_foundation=2, description="test food",
        nutrient_id=nutrient_id, sr_value=sr, foundation_value=fdn, unit="g",
    )


def result(
    recommendation: str, value=None, confidence: str = "high", nutrient_id: int = 1003
) -> AIValidationResult:
    return AIValidationResult(
        nutrient_id=nutrient_id, nutrient_name="Protein", prompt_type="sr_only",
        recommendation=recommendation, recommended_value=value,
        justification="j", literature_source="s", confidence=confidence,
    )


class TestPairingKey:
    """The ground truth is only as good as the SR<->Foundation pairing."""

    def test_punctuation_and_case_normalized(self):
        assert ch._normalize("Fish, Salmon, raw") == ch._normalize("fish salmon raw")

    def test_distinct_foods_do_not_collide(self):
        """The bug this replaced: a 2-part key collapsed every 'Fish, salmon,
        ...' onto one Foundation food and manufactured 500% disagreements."""
        smoked = "Fish, salmon, king, chinook, smoked and canned"
        brined = "Fish, salmon, king, chinook, smoked, brined (Alaska Native)"
        assert ch._normalize(smoked) != ch._normalize(brined)


class TestRelativeGap:
    def test_gap_is_relative_to_ground_truth(self):
        assert case(11.0, 10.0).relative_gap == pytest.approx(0.10)

    def test_zero_ground_truth_with_zero_prediction_is_no_gap(self):
        assert case(0.0, 0.0).relative_gap == 0.0

    def test_zero_ground_truth_with_nonzero_is_infinite_gap(self):
        assert case(5.0, 0.0).relative_gap == float("inf")


class TestPredictedValue:
    """What each recommendation would actually write to the database."""

    def test_sr_legacy_predicts_the_sr_value(self):
        assert ch._predicted_value(result("sr_legacy"), case(20.0, 18.0)) == 20.0

    def test_foundation_predicts_the_foundation_value(self):
        assert ch._predicted_value(result("foundation"), case(20.0, 18.0)) == 18.0

    def test_literature_predicts_its_own_value(self):
        assert ch._predicted_value(result("literature", 19.0), case(20.0, 18.0)) == 19.0

    def test_confirmed_zero_predicts_zero(self):
        assert ch._predicted_value(result("confirmed_zero", 0.0), case(1.0, 0.0)) == 0.0

    def test_insufficient_data_predicts_nothing(self):
        assert ch._predicted_value(result("insufficient_data"), case(20.0, 18.0)) is None


class TestScoring:
    def test_correct_within_tolerance(self):
        scored = ch.score_cases([case(10.5, 10.0)], {1003: result("sr_legacy")})
        assert len(scored) == 1 and scored[0].correct

    def test_incorrect_outside_tolerance(self):
        scored = ch.score_cases([case(15.0, 10.0)], {1003: result("sr_legacy")})
        assert not scored[0].correct
        assert scored[0].relative_error == pytest.approx(0.5)

    def test_choosing_foundation_is_always_correct(self):
        """Foundation is the ground truth, so this is a sanity check on the
        scorer, not a claim about the model."""
        scored = ch.score_cases([case(50.0, 10.0)], {1003: result("foundation")})
        assert scored[0].correct

    def test_error_results_are_not_scored(self):
        assert ch.score_cases([case(10.0, 10.0)], {1003: result("error")}) == []

    def test_missing_results_are_not_scored(self):
        assert ch.score_cases([case(10.0, 10.0)], {}) == []

    def test_abstentions_are_not_scored(self):
        """insufficient_data writes nothing, so it can be neither right nor
        wrong — counting it either way would bias the accuracy number."""
        scored = ch.score_cases([case(10.0, 10.0)], {1003: result("insufficient_data")})
        assert scored == []


class TestSummary:
    def _scored(self, confidence: str, correct: bool, n: int) -> list[ch.ScoredCase]:
        return [
            ch.ScoredCase(
                nutrient_id=1003, description="d", sr_value=10.0,
                foundation_value=10.0 if correct else 20.0,
                predicted_value=10.0, recommendation="sr_legacy",
                confidence=confidence, correct=correct,
                relative_error=0.0 if correct else 0.5,
            )
            for _ in range(n)
        ]

    def test_empty_summary_is_safe(self):
        summary = ch.summarize([])
        assert summary["total_scored"] == 0
        assert summary["overall_accuracy"] is None

    def test_accuracy_per_confidence_level(self):
        scored = self._scored("high", True, 8) + self._scored("low", False, 8)
        summary = ch.summarize(scored)
        assert summary["by_confidence"]["high"]["accuracy"] == 1.0
        assert summary["by_confidence"]["low"]["accuracy"] == 0.0

    def test_detects_a_calibrated_validator(self):
        scored = (
            self._scored("high", True, 10)
            + self._scored("low", True, 5) + self._scored("low", False, 5)
        )
        assert ch.summarize(scored)["confidence_is_calibrated"] is True

    def test_detects_an_uncalibrated_validator(self):
        """The failure the plan asserts but never measured: 'high' no better
        than 'low'."""
        scored = (
            self._scored("high", False, 10)
            + self._scored("low", True, 10)
        )
        assert ch.summarize(scored)["confidence_is_calibrated"] is False

    def test_thin_levels_do_not_decide_calibration(self):
        scored = self._scored("high", False, 2) + self._scored("low", True, 2)
        assert ch.summarize(scored)["confidence_is_calibrated"] is None

    def test_summary_records_prompt_provenance(self):
        summary = ch.summarize(self._scored("high", True, 5))
        assert "+p:" in summary["provenance"]


class TestRunWithoutDatasets:
    def test_absent_datasets_report_cleanly(self, monkeypatch):
        monkeypatch.setattr(ch, "build_labeled_set", lambda *a, **k: [])
        out = ch.run(limit=1)
        assert "error" in out and "gitignored" in out["error"]


@needs_datasets
class TestAgainstRealDatasets:
    def test_builds_informative_cases_only(self):
        from fediaf_nutrients import get_usda_nutrient_ids

        cases = ch.build_labeled_set(get_usda_nutrient_ids(), limit=30)
        assert cases
        for c in cases:
            assert c.relative_gap >= ch.MIN_INFORMATIVE_DISCREPANCY

    def test_limit_is_respected(self):
        from fediaf_nutrients import get_usda_nutrient_ids

        assert len(ch.build_labeled_set(get_usda_nutrient_ids(), limit=7)) == 7

    def test_end_to_end_in_mock_mode(self):
        """The harness runs and produces a summary without live API calls
        (conftest forces mock mode for the whole suite)."""
        summary = ch.run(limit=6)
        assert summary["total_scored"] >= 0
        assert "by_confidence" in summary
        assert summary["tolerance"] == ch.ACCURACY_TOLERANCE
