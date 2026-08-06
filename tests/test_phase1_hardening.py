"""
Tests for the Phase 1 hardening items of the AI-validation plan.

Covers: the mass-failure gate (1.1), the derived skip threshold (1.2), numeric
coercion of recommended_value (1.3), format_ai_suggestion branch coverage
(1.4), and ID-only result keying (1.5). DERIVATION_CODES (1.6) is pinned in
test_usda_api.py; import identity (1.7) is exercised implicitly by every test
run since the root __init__.py was removed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import ai_validation
import config
import main
from ai_validation import (
    AIValidationResult,
    _coerce_recommended_value,
    detect_mass_failure,
    format_ai_suggestion,
    validate_nutrients_concurrent,
)


def make_result(
    recommendation: str = "sr_legacy",
    prompt_type: str = "sr_only",
    nutrient_id: int = 1003,
    confidence: str = "high",
    justification: str = "why",
) -> AIValidationResult:
    return AIValidationResult(
        nutrient_id=nutrient_id,
        nutrient_name="Protein",
        prompt_type=prompt_type,
        recommendation=recommendation,
        recommended_value=None,
        justification=justification,
        literature_source="src",
        confidence=confidence,
    )


class TestCoerceRecommendedValue:
    """1.3 — recommended_value must be numeric or None, never a string."""

    def test_none_passes_through(self):
        assert _coerce_recommended_value(None) == (None, True)

    def test_numbers_coerce_to_float(self):
        assert _coerce_recommended_value(50) == (50.0, True)
        assert _coerce_recommended_value(0.05) == (0.05, True)
        assert _coerce_recommended_value(0) == (0.0, True)

    def test_numeric_string_coerces(self):
        assert _coerce_recommended_value("50.5") == (50.5, True)
        assert _coerce_recommended_value(" 12 ") == (12.0, True)

    def test_unit_bearing_string_rejected(self):
        assert _coerce_recommended_value("50 mg") == (None, False)

    def test_trace_rejected(self):
        assert _coerce_recommended_value("trace") == (None, False)

    def test_bool_rejected(self):
        assert _coerce_recommended_value(True) == (None, False)

    def test_nan_and_inf_rejected(self):
        assert _coerce_recommended_value("nan") == (None, False)
        assert _coerce_recommended_value("inf") == (None, False)
        assert _coerce_recommended_value(float("nan")) == (None, False)

    def test_parse_downgrades_confidence_on_bad_value(self):
        response = (
            '{"recommendation": "literature", "recommended_value": "trace", '
            '"justification": "j", "literature_source": "s", "confidence": "high"}'
        )
        result = ai_validation.parse_single_response(
            response, {"nutrient_id": 1003, "nutrient_name": "Protein"}
        )
        assert result.recommended_value is None
        assert result.confidence == "low"
        assert "discarded" in result.justification

    def test_parse_keeps_numeric_value_and_confidence(self):
        response = (
            '{"recommendation": "literature", "recommended_value": 42.5, '
            '"justification": "j", "literature_source": "s", "confidence": "high"}'
        )
        result = ai_validation.parse_single_response(
            response, {"nutrient_id": 1003, "nutrient_name": "Protein"}
        )
        assert result.recommended_value == 42.5
        assert result.confidence == "high"


class TestFormatBranchCoverage:
    """1.4 — every recommendation value renders distinguishably."""

    def test_error_is_visually_distinct(self):
        formatted = format_ai_suggestion(
            make_result(recommendation="error", justification="billing failed")
        )
        assert "ERROR" in formatted
        assert "billing failed" in formatted
        # Must not look like "no recommendation"
        assert "No recommendation" not in formatted

    def test_insufficient_data_has_own_branch(self):
        formatted = format_ai_suggestion(make_result(recommendation="insufficient_data"))
        assert "insufficient data" in formatted.lower()
        assert "No recommendation" not in formatted

    def test_all_known_values_render_distinctly(self):
        values = ["sr_legacy", "foundation", "literature", "insufficient_data", "error"]
        rendered = {v: format_ai_suggestion(make_result(recommendation=v)) for v in values}
        assert len(set(rendered.values())) == len(values)


class TestResultKeying:
    """1.5 — results are keyed by nutrient_id only; no-ID results drop loudly."""

    def test_no_id_result_dropped_with_warning(self, capsys):
        results = validate_nutrients_concurrent(
            food_name="test food",
            comparison_result={
                "matches": [], "discrepancies": [], "sr_only": [], "foundation_only": []
            },
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=[
                {"nutrient_id": None, "nutrient_name": "Mystery", "unit": "mg"}
            ],
        )
        assert results == {}
        assert "dropping AI result" in capsys.readouterr().out

    def test_id_results_keyed_by_int(self):
        results = validate_nutrients_concurrent(
            food_name="test food",
            comparison_result={
                "matches": [], "discrepancies": [], "sr_only": [], "foundation_only": []
            },
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=[
                {"nutrient_id": 1234, "nutrient_name": "Taurine", "unit": "mg"}
            ],
        )
        assert set(results.keys()) == {1234}

    def test_no_name_keyed_lookup_left_in_main(self):
        """Acceptance: the main.py name-keyed fallback is gone."""
        source = Path(main.__file__).read_text()
        assert "ai_results.get(nutrient_name)" not in source


class TestMassFailureGate:
    """1.1 — wholesale failure aborts instead of entering the review loop."""

    def test_no_results_no_failure(self):
        assert detect_mass_failure({}) is None

    def test_all_errors_trips(self):
        results = {i: make_result("error", "sr_only", i) for i in range(5)}
        assert detect_mass_failure(results) is not None

    def test_no_errors_no_failure(self):
        results = {i: make_result("sr_legacy", "sr_only", i) for i in range(5)}
        assert detect_mass_failure(results) is None

    def test_fraction_below_threshold_passes(self):
        results = {i: make_result("sr_legacy", "sr_only", i) for i in range(9)}
        results[99] = make_result("error", "sr_only", 99)  # 10% errors
        assert detect_mass_failure(results) is None

    def test_skipped_results_excluded_from_denominator(self):
        """40 skipped matches + 12 failed billed calls must trip the gate,
        even though it is only 23% of the total."""
        results = {i: make_result("foundation", "skipped", i) for i in range(40)}
        for i in range(100, 112):
            results[i] = make_result("error", "sr_only", i)
        failure = detect_mass_failure(results)
        assert failure is not None
        assert "12 of 12" in failure

    def test_process_single_food_aborts_on_mass_failure(self, monkeypatch):
        """Acceptance: an all-error validation returns [] (main deletes the row)."""
        monkeypatch.setattr(
            main, "fetch_sr_legacy",
            lambda fdc_id: {
                "nutrients": {
                    1003: {
                        "name": "Protein", "value": 20.0, "unit": "g",
                        "num_samples": 4, "min_value": None, "max_value": None,
                        "median_value": None, "year_acquired": "2018",
                        "derivation_description": "Analytical",
                    }
                },
                "unpopulated_zeros": [],
            },
        )
        monkeypatch.setattr(
            main, "validate_nutrients_concurrent",
            lambda **kwargs: {1003: make_result("error", "sr_only", 1003)},
        )

        records = main.process_single_food(
            10001,
            {"food_name": "test food", "sr_fdc_id": 111, "foundation_fdc_id": None},
        )
        assert records == []


class TestImportIdentity:
    """1.7 — exception classes must stay identity-stable across the suite.

    Two things broke this historically: the project root carrying an
    __init__.py (so modules loaded as both `ai_validation` and
    `nutDataGen.ai_validation`), and an importlib.reload() in a test, which
    rebinds every class so previously-imported ones go stale. Either makes
    isinstance / pytest.raises fail depending on test order.
    """

    def test_no_root_package_init(self):
        root = Path(main.__file__).parent
        assert not (root / "__init__.py").exists(), (
            "a root __init__.py lets modules load under two identities"
        )

    def test_no_module_reloads_in_tests(self):
        offenders = []
        for path in (Path(__file__).parent).glob("test_*.py"):
            text = path.read_text()
            if "importlib.reload(" in text and "Deliberately does NOT" not in text:
                offenders.append(path.name)
        assert not offenders, (
            f"importlib.reload() rebinds classes and breaks isinstance: {offenders}"
        )

    def test_exception_classes_are_identity_stable(self):
        import ai_validation as first
        import ai_validation as second

        assert first.LiveAPICallBlocked is second.LiveAPICallBlocked
        assert first.NonRetryableAPIError is second.NonRetryableAPIError
        assert isinstance(
            first.NonRetryableAPIError("x"), second.NonRetryableAPIError
        )


class TestThresholdCoupling:
    """1.2 — the skip threshold is derived from the match threshold."""

    def test_skip_threshold_derived_from_trivial(self):
        assert config.SKIP_VALIDATION_THRESHOLD == float(
            config.DISCREPANCY_THRESHOLDS["trivial"]
        )
