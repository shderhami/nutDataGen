"""
Tests for the Phase 4 items of the AI-validation plan.

4.1 self-consistency sampling, 4.2 confidence semantics, 4.3 typed
retry/exception handling, 4.4 the auto-accept disagreement trail, and
4.5 prompt provenance.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import ai_validation
import config
import main
from ai_validation import (
    AIValidationResult,
    NonRetryableAPIError,
    create_skipped_result,
    describe_auto_accept_disagreement,
    model_provenance,
    prompt_version_hash,
    reconcile_samples,
)


def sample(
    recommendation: str = "literature",
    value=None,
    confidence: str = "high",
    prompt_type: str = "missing",
) -> AIValidationResult:
    return AIValidationResult(
        nutrient_id=1234,
        nutrient_name="Taurine",
        prompt_type=prompt_type,
        recommendation=recommendation,
        recommended_value=value,
        justification="because",
        literature_source="lit",
        confidence=confidence,
    )


class TestSelfConsistency:
    """4.1 — a measured confidence replaces the self-reported one."""

    def test_disabled_by_default(self):
        assert config.AI_SELF_CONSISTENCY_SAMPLES == 1

    def test_single_sample_passes_through_unchanged(self):
        one = sample(value=50.0)
        assert reconcile_samples([one]) is one

    def test_empty_samples_rejected(self):
        with pytest.raises(ValueError):
            reconcile_samples([])

    def test_median_of_agreeing_values(self):
        results = [sample(value=v) for v in (40.0, 50.0, 55.0)]
        assert reconcile_samples(results).recommended_value == 50.0

    def test_tight_agreement_keeps_confidence(self):
        results = [sample(value=v, confidence="high") for v in (50.0, 51.0, 52.0)]
        merged = reconcile_samples(results)
        assert merged.confidence == "high"
        assert "samples agreed" in merged.justification

    def test_wide_spread_forces_low_confidence(self):
        results = [sample(value=v, confidence="high") for v in (10.0, 50.0, 90.0)]
        merged = reconcile_samples(results)
        assert merged.confidence == "low"
        assert "spread" in merged.justification

    def test_recommendation_disagreement_forces_low_confidence(self):
        results = [
            sample("literature", 50.0, "high"),
            sample("literature", 52.0, "high"),
            sample("insufficient_data", None, "high"),
        ]
        merged = reconcile_samples(results)
        assert merged.recommendation == "literature"
        assert merged.confidence == "low"
        assert "disagreed" in merged.justification

    def test_partial_abstention_forces_low_confidence(self):
        """A sample returning no value disagrees about whether the value is
        knowable, even when the recommendation label matches."""
        results = [
            sample("literature", None, "high"),
            sample("literature", 50.0, "high"),
            sample("literature", 52.0, "high"),
        ]
        merged = reconcile_samples(results)
        assert merged.recommended_value == 51.0
        assert merged.confidence == "low"
        assert "no value" in merged.justification

    def test_all_zero_samples_stay_confident(self):
        """confirmed_zero agreement must not be treated as infinite spread."""
        results = [sample("confirmed_zero", 0.0, "high") for _ in range(3)]
        merged = reconcile_samples(results)
        assert merged.recommended_value == 0.0
        assert merged.confidence == "high"

    def test_zero_with_outlier_forces_low_confidence(self):
        results = [
            sample("confirmed_zero", 0.0, "high"),
            sample("confirmed_zero", 0.0, "high"),
            sample("confirmed_zero", 1.0, "high"),
        ]
        assert reconcile_samples(results).confidence == "low"

    def test_confidence_is_never_raised(self):
        """Agreement across samples is not proof of correctness."""
        results = [sample(value=v, confidence="low") for v in (50.0, 50.0, 50.0)]
        assert reconcile_samples(results).confidence == "low"

    def test_error_samples_ignored_when_others_usable(self):
        results = [
            sample("error", None, "low"),
            sample("literature", 50.0, "medium"),
            sample("literature", 50.0, "medium"),
        ]
        merged = reconcile_samples(results)
        assert merged.recommendation == "literature"
        assert merged.recommended_value == 50.0

    def test_all_error_samples_return_an_error(self):
        results = [sample("error", None, "low") for _ in range(3)]
        assert reconcile_samples(results).recommendation == "error"

    def test_reduction_is_deterministic(self):
        results = [
            sample("literature", 50.0, "high"),
            sample("insufficient_data", None, "high"),
        ]
        first = reconcile_samples(results)
        second = reconcile_samples(results)
        assert (first.recommendation, first.recommended_value) == (
            second.recommendation, second.recommended_value
        )


class TestSkippedConfidence:
    """4.2 — 'we never asked' is distinct from 'the model was confident'."""

    def test_skipped_result_is_not_high(self):
        result = create_skipped_result({"nutrient_id": 1003}, "values match")
        assert result.confidence == "skipped"

    def test_skipped_renders_distinctly(self):
        result = create_skipped_result({"nutrient_id": 1003}, "values match")
        assert "[SKIPPED]" in ai_validation.format_ai_suggestion(result)

    def test_skipped_excluded_from_mass_failure_denominator(self):
        results = {1: create_skipped_result({"nutrient_id": 1}, "match")}
        assert ai_validation.detect_mass_failure(results) is None


class TestTypedExceptionHandling:
    """4.3 — typed classification instead of substring matching."""

    def test_bad_request_is_non_retryable(self):
        import anthropic

        exc = anthropic.BadRequestError.__new__(anthropic.BadRequestError)
        Exception.__init__(exc, "bad schema")
        classified = ai_validation._classify_api_exception(exc)
        assert isinstance(classified, NonRetryableAPIError)

    def test_unknown_error_is_retryable_runtime_error(self):
        classified = ai_validation._classify_api_exception(RuntimeError("overloaded"))
        assert isinstance(classified, RuntimeError)
        assert not isinstance(classified, NonRetryableAPIError)

    def test_sync_retry_stops_on_non_retryable(self, monkeypatch):
        calls = []

        def boom(prompt, api_key=None, schema=None):
            calls.append(1)
            raise NonRetryableAPIError("BadRequestError: nope")

        monkeypatch.setattr(ai_validation, "MOCK_MODE", False)
        monkeypatch.setattr(ai_validation, "call_claude_api", boom)

        with pytest.raises(NonRetryableAPIError):
            ai_validation.call_claude_api_with_retry("prompt")
        assert len(calls) == 1, f"non-retryable error retried {len(calls)} times"

    def test_sync_retry_still_retries_transient(self, monkeypatch):
        calls = []

        def flaky(prompt, api_key=None, schema=None):
            calls.append(1)
            raise RuntimeError("Claude API error: overloaded")

        monkeypatch.setattr(ai_validation, "MOCK_MODE", False)
        monkeypatch.setattr(ai_validation, "call_claude_api", flaky)
        monkeypatch.setattr(ai_validation.time, "sleep", lambda s: None)

        with pytest.raises(ai_validation.AIValidationError):
            ai_validation.call_claude_api_with_retry("prompt")
        assert len(calls) == config.AI_MAX_RETRIES

    def test_sdk_retries_disabled(self, monkeypatch):
        """The SDK's own retries would stack on ours (~15 requests/nutrient)."""
        captured = {}

        class FakeMessages:
            def create(self, **kwargs):
                return SimpleNamespace(
                    stop_reason="end_turn",
                    content=[SimpleNamespace(type="text", text="{}")],
                )

        import anthropic

        def fake_client(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(messages=FakeMessages())

        monkeypatch.setattr(ai_validation, "MOCK_MODE", False)
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", True)
        monkeypatch.setattr(anthropic, "Anthropic", fake_client)

        ai_validation.call_claude_api("prompt", api_key="k")
        assert captured["max_retries"] == 0


class TestDisagreementTrail:
    """4.4 — auto-accepted paths record the contradiction they create."""

    def test_agreement_records_nothing(self):
        result = sample("foundation", None, "high", prompt_type="match")
        assert describe_auto_accept_disagreement(result, "foundation") is None

    def test_disagreement_is_described(self):
        result = sample("literature", 12.5, "high", prompt_type="foundation_only")
        note = describe_auto_accept_disagreement(result, "foundation")
        assert note is not None
        assert "literature" in note and "12.5" in note and "high" in note

    def test_error_result_records_nothing(self):
        result = sample("error", None, "low")
        assert describe_auto_accept_disagreement(result, "foundation") is None

    def test_skipped_result_records_nothing(self):
        result = create_skipped_result({"nutrient_id": 1003}, "match")
        assert describe_auto_accept_disagreement(result, "foundation") is None

    def test_absent_result_records_nothing(self):
        assert describe_auto_accept_disagreement(None, "foundation") is None

    def test_foundation_only_record_carries_the_trail(self, monkeypatch):
        """Acceptance: the contradiction reaches the stored row's comment."""
        monkeypatch.setattr(
            main, "fetch_foundation",
            lambda fdc_id: {
                "nutrients": {
                    1003: {
                        "name": "Protein", "value": 20.0, "unit": "g",
                        "num_samples": 4, "min_value": None, "max_value": None,
                        "median_value": None, "year_acquired": "2020",
                        "derivation_description": "Analytical",
                    }
                },
                "unpopulated_zeros": [],
            },
        )
        monkeypatch.setattr(
            main, "validate_nutrients_concurrent",
            lambda **kwargs: {
                1003: AIValidationResult(
                    nutrient_id=1003, nutrient_name="Protein",
                    prompt_type="foundation_only", recommendation="literature",
                    recommended_value=18.0, justification="lit disagrees",
                    literature_source="J Food Comp Anal", confidence="high",
                )
            },
        )
        monkeypatch.setattr(main, "prompt_missing_nutrient", lambda n, s: {
            "nutrient_id": n.get("nutrient_id"), "chosen_value": 1.0,
            "chosen_source": "literature", "comment": "",
        })

        records = main.process_single_food(
            10001,
            {"food_name": "test food", "sr_fdc_id": None, "foundation_fdc_id": 222},
        )
        protein = [r for r in records if r.get("nutrient_id") == 1003][0]
        assert "AI disagreed" in protein["comment"]
        assert "literature" in protein["comment"]


class TestPromptProvenance:
    """4.5 — a stored justification is traceable to its prompt."""

    def test_hash_is_stable_within_a_run(self):
        assert prompt_version_hash() == prompt_version_hash()

    def test_hash_is_not_unknown(self):
        """cv_config.normalized_source must be reachable."""
        assert prompt_version_hash() != "unknown"

    def test_provenance_contains_model_and_hash(self):
        provenance = model_provenance()
        assert provenance.startswith(config.AI_MODEL)
        assert prompt_version_hash() in provenance

    def test_provenance_fits_the_column(self):
        """ingredient_nutrients.ai_model is VARCHAR(50)."""
        assert len(model_provenance()) <= 50

    def test_main_stores_provenance_not_bare_model(self):
        source = Path(main.__file__).read_text()
        assert '"ai_model": AI_MODEL' not in source
        assert '"ai_model": model_provenance()' in source
