"""
Tests for ai_validation.py
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_validation import (
    AIValidationResult,
    AIValidationError,
    build_prompt_sr_only,
    build_prompt_foundation_only,
    build_prompt_both_sources,
    build_prompt_missing,
    call_claude_api,
    call_claude_api_with_retry,
    _get_mock_response,
    _extract_json_from_response,
    parse_single_response,
    validate_nutrient_single,
    validate_nutrients_sequential,
    should_skip_validation,
    create_skipped_result,
    format_ai_suggestion,
    MOCK_MODE,
    # Async concurrent validation (Phase 2)
    _AsyncRateLimiter,
    _validate_nutrients_async,
    validate_nutrients_concurrent,
)


class TestAIValidationResult:
    """Tests for AIValidationResult dataclass."""

    def test_creates_result_with_all_fields(self):
        """Test creating an AIValidationResult with all fields."""
        result = AIValidationResult(
            nutrient_id=1003,
            nutrient_name="Protein",
            prompt_type="sr_only",
            recommendation="sr_legacy",
            recommended_value=None,
            justification="Value is consistent with literature.",
            literature_source="USDA SR Legacy",
            confidence="high"
        )

        assert result.nutrient_id == 1003
        assert result.nutrient_name == "Protein"
        assert result.prompt_type == "sr_only"
        assert result.recommendation == "sr_legacy"
        assert result.recommended_value is None
        assert result.confidence == "high"

    def test_creates_result_with_estimated_value(self):
        """Test creating an AIValidationResult with an estimated value."""
        result = AIValidationResult(
            nutrient_id=None,
            nutrient_name="Taurine",
            prompt_type="missing",
            recommendation="estimate",
            recommended_value=0.15,
            justification="Estimated from typical cat food content.",
            literature_source="Comparative analysis",
            confidence="low"
        )

        assert result.nutrient_id is None
        assert result.recommended_value == 0.15
        assert result.recommendation == "estimate"


class TestBuildPromptSrOnly:
    """Tests for build_prompt_sr_only function."""

    def test_builds_prompt_with_all_metadata(self):
        """Test building SR-only prompt with all metadata."""
        prompt = build_prompt_sr_only(
            food_name="Chicken, raw",
            nutrient_name="Protein",
            sr_value=20.5,
            unit="g",
            metadata={
                "num_samples": 10,
                "year_acquired": "2018",
                "derivation_description": "Analytical"
            }
        )

        assert "Chicken, raw" in prompt
        assert "Protein" in prompt
        assert "20.5 g" in prompt
        assert "2018" in prompt  # Sample date
        assert "SR Legacy" in prompt
        assert "cat food" in prompt.lower()  # Updated prompt mentions cat food

    def test_builds_prompt_with_missing_metadata(self):
        """Test building SR-only prompt with missing metadata."""
        prompt = build_prompt_sr_only(
            food_name="Beef, raw",
            nutrient_name="Fat",
            sr_value=15.0,
            unit="g",
            metadata={}
        )

        assert "Beef, raw" in prompt
        assert "Fat" in prompt
        assert "15.0 g" in prompt
        assert "unknown" in prompt  # Default for missing metadata


class TestBuildPromptFoundationOnly:
    """Tests for build_prompt_foundation_only function."""

    def test_builds_prompt_with_all_metadata(self):
        """Test building Foundation-only prompt with all metadata."""
        prompt = build_prompt_foundation_only(
            food_name="Chicken, raw",
            nutrient_name="Protein",
            foundation_value=20.5,
            unit="g",
            metadata={
                "num_samples": 10,
                "year_acquired": "2018",
                "derivation_description": "Analytical"
            }
        )

        assert "Chicken, raw" in prompt
        assert "Protein" in prompt
        assert "20.5 g" in prompt
        assert "2018" in prompt  # Sample date
        assert "Foundation" in prompt
        assert "cat food" in prompt.lower()

    def test_builds_prompt_with_missing_metadata(self):
        """Test building Foundation-only prompt with missing metadata."""
        prompt = build_prompt_foundation_only(
            food_name="Beef, raw",
            nutrient_name="Fat",
            foundation_value=15.0,
            unit="g",
            metadata={}
        )

        assert "Beef, raw" in prompt
        assert "Fat" in prompt
        assert "15.0 g" in prompt
        assert "unknown" in prompt  # Default for missing metadata

    def test_excludes_sr_legacy_reference(self):
        """Test that Foundation-only prompt tells AI not to search SR Legacy."""
        prompt = build_prompt_foundation_only(
            food_name="Chicken, raw",
            nutrient_name="Protein",
            foundation_value=20.5,
            unit="g",
            metadata={}
        )

        assert "Do NOT search USDA SR Legacy" in prompt

    def test_recommendation_options_are_foundation_or_literature(self):
        """Test that recommendation options are foundation or literature."""
        prompt = build_prompt_foundation_only(
            food_name="Chicken, raw",
            nutrient_name="Protein",
            foundation_value=20.5,
            unit="g",
            metadata={}
        )

        assert '"foundation" or "literature"' in prompt


class TestBuildPromptBothSources:
    """Tests for build_prompt_both_sources function."""

    def test_builds_discrepancy_prompt(self):
        """Test building prompt for discrepancy between sources."""
        prompt = build_prompt_both_sources(
            food_name="Salmon, raw",
            nutrient_name="Omega-3",
            sr_value=2.5,
            foundation_value=3.2,
            unit="g",
            discrepancy_percent=24.6,
            sr_metadata={"num_samples": 8, "year_acquired": "2017"},
            foundation_metadata={"num_samples": 15, "year_acquired": "2021"}
        )

        assert "Salmon, raw" in prompt
        assert "Omega-3" in prompt
        assert "24.6%" in prompt  # Discrepancy percentage
        assert "2.5" in prompt
        assert "3.2" in prompt
        assert "SR Legacy" in prompt
        assert "Foundation" in prompt
        assert "cat food" in prompt.lower()  # Updated prompt mentions cat food


class TestBuildPromptMissing:
    """Tests for build_prompt_missing function."""

    def test_builds_missing_nutrient_prompt(self):
        """Test building prompt for missing nutrient."""
        prompt = build_prompt_missing(
            food_name="Chicken liver, raw",
            nutrient_name="Taurine",
            unit="mg"
        )

        assert "Chicken liver, raw" in prompt
        assert "Taurine" in prompt
        assert "mg" in prompt
        assert "not available" in prompt.lower()  # "not available in either database"
        assert "cat food" in prompt.lower()  # Updated prompt mentions cat food


class TestMockResponse:
    """Tests for _get_mock_response function."""

    def test_mock_response_returns_valid_json(self):
        """Test that mock response returns valid JSON for per-nutrient prompt."""
        # Use SR-only prompt format
        prompt = build_prompt_sr_only(
            food_name="Test Food",
            nutrient_name="Protein",
            sr_value=20.0,
            unit="g",
            metadata={"year_acquired": "2020"}
        )

        response = _get_mock_response(prompt)
        parsed = json.loads(response)

        assert isinstance(parsed, dict)
        assert "recommendation" in parsed
        assert "justification" in parsed
        assert "confidence" in parsed

    def test_mock_response_sr_only(self):
        """Test mock response for SR-only prompt."""
        prompt = "SR Legacy only some nutrient"
        response = _get_mock_response(prompt)
        parsed = json.loads(response)

        assert parsed["recommendation"] == "sr_legacy"

    def test_mock_response_discrepancy(self):
        """Test mock response for discrepancy prompt."""
        # Use prompt format that matches the per-nutrient both_sources prompt
        prompt = "SR Legacy and Foundation food databases. Discrepancy: 25%"
        response = _get_mock_response(prompt)
        parsed = json.loads(response)

        assert parsed["recommendation"] in ["foundation", "literature"]


class TestFormatAiSuggestion:
    """Tests for format_ai_suggestion function."""

    def test_formats_confirmed_recommendation(self):
        """Test formatting confirmed recommendation."""
        result = AIValidationResult(
            nutrient_id=1003,
            nutrient_name="Protein",
            prompt_type="match",
            recommendation="confirmed",
            recommended_value=None,
            justification="Value is consistent with literature.",
            literature_source="USDA",
            confidence="high"
        )

        formatted = format_ai_suggestion(result)

        assert "[HIGH]" in formatted
        assert "confirms this value" in formatted

    def test_formats_foundation_recommendation(self):
        """Test formatting foundation recommendation."""
        result = AIValidationResult(
            nutrient_id=1004,
            nutrient_name="Fat",
            prompt_type="both_sources",
            recommendation="foundation",
            recommended_value=None,
            justification="Foundation data is more recent.",
            literature_source="USDA Foundation",
            confidence="medium"
        )

        formatted = format_ai_suggestion(result)

        assert "[MED]" in formatted
        assert "Foundation" in formatted

    def test_formats_literature_zero_value(self):
        """A recommended value of 0 is a real answer and must be shown.

        Zero is the expected answer whenever the unpopulated-zero rule demotes a
        nutrient that really is absent; truthiness testing hid it from reviewers.
        """
        result = AIValidationResult(
            nutrient_id=1272,
            nutrient_name="DHA",
            prompt_type="missing",
            recommendation="literature",
            recommended_value=0.0,
            justification="Land-animal fat contains no marine-origin DHA.",
            literature_source="CoFID; CIQUAL",
            confidence="high"
        )

        formatted = format_ai_suggestion(result)

        assert "(0.0)" in formatted

    def test_formats_estimate_zero_value(self):
        """The same zero-vs-missing distinction applies to estimates."""
        result = AIValidationResult(
            nutrient_id=1079,
            nutrient_name="Crude Fiber",
            prompt_type="missing",
            recommendation="estimate",
            recommended_value=0.0,
            justification="Muscle meat contains no dietary fiber.",
            literature_source="CoFID",
            confidence="high"
        )

        formatted = format_ai_suggestion(result)

        assert "(0.0)" in formatted

    def test_omits_value_when_absent(self):
        """A genuinely absent recommended value still renders without a number."""
        result = AIValidationResult(
            nutrient_id=1272,
            nutrient_name="DHA",
            prompt_type="missing",
            recommendation="literature",
            recommended_value=None,
            justification="Could not determine.",
            literature_source="",
            confidence="low"
        )

        formatted = format_ai_suggestion(result)

        assert "(" not in formatted.split(":")[1]

    def test_formats_estimate_with_value(self):
        """Test formatting estimate with recommended value."""
        result = AIValidationResult(
            nutrient_id=None,
            nutrient_name="Taurine",
            prompt_type="missing",
            recommendation="estimate",
            recommended_value=0.15,
            justification="Estimated from typical content.",
            literature_source="Comparative data",
            confidence="low"
        )

        formatted = format_ai_suggestion(result)

        assert "[LOW]" in formatted
        assert "estimate" in formatted
        assert "0.15" in formatted


class TestExtractJsonFromResponse:
    """Tests for _extract_json_from_response function."""

    def test_parses_pure_json(self):
        """Test parsing pure JSON response."""
        response = '{"recommendation": "sr_legacy", "confidence": "high"}'
        result = _extract_json_from_response(response)
        assert result["recommendation"] == "sr_legacy"
        assert result["confidence"] == "high"

    def test_parses_json_with_whitespace(self):
        """Test parsing JSON with leading/trailing whitespace."""
        response = '  \n{"recommendation": "foundation"}\n  '
        result = _extract_json_from_response(response)
        assert result["recommendation"] == "foundation"

    def test_extracts_json_from_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        response = '''Here's my analysis:

```json
{"recommendation": "literature", "confidence": "medium"}
```

This is based on scientific literature.'''
        result = _extract_json_from_response(response)
        assert result["recommendation"] == "literature"
        assert result["confidence"] == "medium"

    def test_extracts_json_from_code_block_without_language(self):
        """Test extracting JSON from code block without language specifier."""
        response = '''Analysis complete:

```
{"recommendation": "sr_legacy", "justification": "Values match literature."}
```'''
        result = _extract_json_from_response(response)
        assert result["recommendation"] == "sr_legacy"

    def test_json_embedded_in_prose_is_a_parse_failure(self):
        """The brace-slicing heuristic is gone (plan 2.3): structured outputs
        make the live response pure JSON, and slicing first-{ to last-}
        mis-parsed prose braces. Prose-wrapped JSON now fails parsing."""
        response = '''Looking at scientific literature and databases, I found:

{"recommendation": "foundation", "recommended_value": 25.5, "justification": "Foundation data is more recent.", "literature_source": "USDA Foundation", "confidence": "high"}

This recommendation is based on multiple sources.'''
        with pytest.raises(json.JSONDecodeError):
            _extract_json_from_response(response)

    def test_nested_json_in_prose_is_a_parse_failure(self):
        """Same as above for the nested-object case the heuristic covered."""
        response = 'Text before {"outer": {"inner": "value"}, "recommendation": "sr_legacy"} text after'
        with pytest.raises(json.JSONDecodeError):
            _extract_json_from_response(response)

    def test_raises_error_for_no_json(self):
        """Test raises JSONDecodeError when no JSON found."""
        response = "This is just plain text with no JSON at all."
        with pytest.raises(json.JSONDecodeError):
            _extract_json_from_response(response)

    def test_raises_error_for_malformed_json(self):
        """Test raises JSONDecodeError for malformed JSON."""
        response = '{"recommendation": "sr_legacy", invalid}'
        with pytest.raises(json.JSONDecodeError):
            _extract_json_from_response(response)


class TestCallClaudeApi:
    """Tests for call_claude_api function."""

    @patch("ai_validation.MOCK_MODE", True)
    def test_returns_mock_response_in_mock_mode(self):
        """Test that mock mode returns mock response."""
        # Patch MOCK_MODE to True for this test
        prompt = "Test prompt"
        response = call_claude_api(prompt)

        # Should return valid JSON from mock
        parsed = json.loads(response)
        assert "recommendation" in parsed

    def test_raises_error_without_api_key(self, monkeypatch):
        """Test raises error when API key is missing.

        Deliberately does NOT importlib.reload(ai_validation): a reload
        rebinds every class in the module, so exception classes imported by
        other test modules become stale and isinstance / pytest.raises stop
        matching depending on test order. Patch the module attributes instead.
        """
        import ai_validation

        monkeypatch.setattr(ai_validation, "MOCK_MODE", False)
        monkeypatch.setattr(ai_validation, "_LIVE_CALLS_GRANTED", True)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises((ValueError, RuntimeError, ImportError)):
            ai_validation.call_claude_api("Test prompt")


class TestMockModeEnvironment:
    """Tests for mock mode environment variable (AI_MOCK_MODE in config.py)."""

    def test_mock_mode_disabled_by_default(self):
        """Test that mock mode is disabled by default (real API calls)."""
        # Default value is "false" - real API calls by default
        assert MOCK_MODE is False

    def test_mock_mode_can_be_enabled(self):
        """Test that mock mode can be enabled via environment."""
        # This tests the logic - AI_MOCK_MODE="true" enables mock mode
        mock_env = os.environ.get("AI_MOCK_MODE", "false").lower() == "true"
        # Default should be false (real API)
        assert mock_env is False


# =============================================================================
# Phase 1: Per-Nutrient Validation Tests
# =============================================================================

class TestShouldSkipValidation:
    """Tests for should_skip_validation function."""

    def test_skips_when_values_match(self):
        """Test skipping when SR and Foundation values match closely."""
        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "prompt_type": "match",
            "sr_value": 20.0,
            "foundation_value": 20.5,  # < 5% difference
        }

        should_skip, reason = should_skip_validation(nutrient_data)

        assert should_skip is True
        assert "match" in reason.lower()

    def test_does_not_skip_discrepancy(self):
        """Test not skipping when there's a discrepancy."""
        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "prompt_type": "both_sources",
            "sr_value": 20.0,
            "foundation_value": 30.0,  # > 5% difference
        }

        should_skip, reason = should_skip_validation(nutrient_data)

        assert should_skip is False
        assert reason == ""

    def test_does_not_skip_sr_only(self):
        """Test not skipping SR-only nutrients."""
        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "prompt_type": "sr_only",
            "sr_value": 20.0,
        }

        should_skip, reason = should_skip_validation(nutrient_data)

        assert should_skip is False

    def test_does_not_skip_missing(self):
        """Test not skipping missing nutrients."""
        nutrient_data = {
            "nutrient_id": 1234,
            "nutrient_name": "Taurine",
            "prompt_type": "missing",
        }

        should_skip, reason = should_skip_validation(nutrient_data)

        assert should_skip is False

    def test_skips_when_both_zero(self):
        """Test skipping when both values are zero."""
        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "prompt_type": "match",
            "sr_value": 0.0,
            "foundation_value": 0.0,
        }

        should_skip, reason = should_skip_validation(nutrient_data)

        assert should_skip is True


class TestCreateSkippedResult:
    """Tests for create_skipped_result function."""

    def test_creates_skipped_result(self):
        """Test creating a skipped result."""
        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
        }

        result = create_skipped_result(nutrient_data, "Values match within 2%")

        assert result.nutrient_id == 1003
        assert result.nutrient_name == "Protein"
        assert result.prompt_type == "skipped"
        assert result.recommendation == "foundation"
        # Not "high" (plan 4.2): this nutrient was never sent to the AI, and
        # stamping "high" made ai_confidence='high' ambiguous between "the
        # model was confident" and "we never asked".
        assert result.confidence == "skipped"
        assert "match" in result.justification.lower()


class TestParseSingleResponse:
    """Tests for parse_single_response function."""

    def test_parses_valid_json(self):
        """Test parsing valid JSON response."""
        response = json.dumps({
            "recommendation": "sr_legacy",
            "recommended_value": None,
            "justification": "Value is consistent with literature.",
            "literature_source": "MEXT Japan",
            "confidence": "high"
        })
        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "prompt_type": "sr_only"
        }

        result = parse_single_response(response, nutrient_data)

        assert result.nutrient_id == 1003
        assert result.recommendation == "sr_legacy"
        assert result.confidence == "high"

    def test_handles_invalid_json(self):
        """Test handling invalid JSON response."""
        response = "This is not JSON"
        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "prompt_type": "sr_only"
        }

        result = parse_single_response(response, nutrient_data)

        assert result.recommendation == "error"
        assert "Failed to parse" in result.justification


class TestValidateNutrientSingle:
    """Tests for validate_nutrient_single function."""

    def test_validates_sr_only_nutrient(self):
        """Test validating an SR-only nutrient."""
        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "unit": "g",
            "prompt_type": "sr_only",
            "sr_value": 20.0,
            "sr_metadata": {"year_acquired": "2018"}
        }

        result = validate_nutrient_single("Chicken, raw", nutrient_data)

        # Check result has expected attributes (avoid isinstance issues)
        assert result.nutrient_id == 1003
        assert result.nutrient_name == "Protein"
        assert result.recommendation in ["sr_legacy", "literature", "foundation"]
        assert result.confidence in ["high", "medium", "low"]

    def test_validates_both_sources_nutrient(self):
        """Test validating a nutrient with both sources."""
        nutrient_data = {
            "nutrient_id": 1004,
            "nutrient_name": "Fat",
            "unit": "g",
            "prompt_type": "both_sources",
            "sr_value": 10.0,
            "foundation_value": 12.0,
            "discrepancy_percent": 18.2,
            "sr_metadata": {},
            "foundation_metadata": {}
        }

        result = validate_nutrient_single("Chicken, raw", nutrient_data)

        assert result.nutrient_id == 1004
        assert result.nutrient_name == "Fat"
        assert hasattr(result, "recommendation")

    def test_validates_missing_nutrient(self):
        """Test validating a missing nutrient."""
        nutrient_data = {
            "nutrient_id": 1234,
            "nutrient_name": "Taurine",
            "unit": "mg",
            "prompt_type": "missing"
        }

        result = validate_nutrient_single("Chicken liver, raw", nutrient_data)

        assert result.nutrient_id == 1234
        assert result.nutrient_name == "Taurine"
        assert result.recommendation in ["literature", "estimate", "insufficient_data"]

    def test_raises_error_for_unknown_prompt_type(self):
        """Test raising error for unknown prompt type."""
        import ai_validation

        nutrient_data = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "unit": "g",
            "prompt_type": "unknown_type"
        }

        with pytest.raises(ai_validation.AIValidationError):
            validate_nutrient_single("Chicken, raw", nutrient_data)


class TestValidateNutrientsSequential:
    """Tests for validate_nutrients_sequential function."""

    def test_validates_multiple_nutrients(self):
        """Test validating multiple nutrients sequentially."""
        comparison_result = {
            "matches": [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "sr_value": 20.0,
                    "foundation_value": 20.2,
                    "unit": "g",
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "discrepancies": [
                {
                    "nutrient_id": 1004,
                    "nutrient_name": "Fat",
                    "sr_value": 10.0,
                    "foundation_value": 15.0,
                    "unit": "g",
                    "discrepancy": {"percentage": 40.0},
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        sr_data = {"nutrients": {}}
        foundation_data = {"nutrients": {}}

        results = validate_nutrients_sequential(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data=sr_data,
            foundation_data=foundation_data,
            missing_nutrients=[]
        )

        assert 1003 in results
        assert 1004 in results

    def test_skips_matching_nutrients(self):
        """Test that matching nutrients are skipped."""
        comparison_result = {
            "matches": [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "sr_value": 20.0,
                    "foundation_value": 20.1,  # < 5% difference
                    "unit": "g",
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        results = validate_nutrients_sequential(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data={"nutrients": {}},
            missing_nutrients=[]
        )

        assert 1003 in results
        # Skipped nutrients have prompt_type "skipped"
        assert results[1003].prompt_type == "skipped"
        assert results[1003].recommendation == "foundation"

    def test_validates_missing_nutrients(self):
        """Test validating missing nutrients."""
        comparison_result = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        missing_nutrients = [
            {"nutrient_id": 1234, "nutrient_name": "Taurine", "unit": "mg"}
        ]

        results = validate_nutrients_sequential(
            food_name="Chicken, raw",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=missing_nutrients
        )

        assert 1234 in results

    def test_returns_empty_for_no_nutrients(self):
        """Test returns empty dict when no nutrients."""
        comparison_result = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        results = validate_nutrients_sequential(
            food_name="Empty Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=[]
        )

        assert results == {}

    def test_verbose_mode(self, capsys):
        """Test verbose mode prints progress."""
        comparison_result = {
            "matches": [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "sr_value": 20.0,
                    "foundation_value": 20.1,
                    "unit": "g",
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        results = validate_nutrients_sequential(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data={"nutrients": {}},
            missing_nutrients=[],
            verbose=True
        )

        captured = capsys.readouterr()
        assert "Validating" in captured.out
        assert "Protein" in captured.out


class TestCallClaudeApiWithRetry:
    """Tests for call_claude_api_with_retry function."""

    @patch("ai_validation.MOCK_MODE", True)
    def test_returns_response_on_success(self):
        """Test returning response on successful call."""
        response = call_claude_api_with_retry("Test prompt")

        # In mock mode, should return valid JSON
        parsed = json.loads(response)
        assert "recommendation" in parsed

    @patch("ai_validation.MOCK_MODE", True)
    def test_uses_mock_mode(self):
        """Test that mock mode is used when enabled."""
        response = call_claude_api_with_retry("Test prompt")
        assert response is not None


# =============================================================================
# Phase 2: Async Concurrent Validation Tests
# =============================================================================

class TestAsyncRateLimiter:
    """Tests for _AsyncRateLimiter class."""

    def test_allows_immediate_first_request(self):
        """Test that first request is not delayed."""
        async def run_test():
            limiter = _AsyncRateLimiter(min_interval=1.0)
            import time
            start = time.time()
            await limiter.acquire()
            elapsed = time.time() - start
            # First request should be immediate (< 0.1s)
            assert elapsed < 0.1

        asyncio.run(run_test())

    def test_enforces_minimum_interval(self):
        """Test that rate limiter enforces minimum interval."""
        async def run_test():
            limiter = _AsyncRateLimiter(min_interval=0.1)
            import time

            # First request
            await limiter.acquire()

            # Second request should wait
            start = time.time()
            await limiter.acquire()
            elapsed = time.time() - start

            # Should have waited approximately 0.1s
            assert elapsed >= 0.08  # Allow small tolerance

        asyncio.run(run_test())


class TestValidateNutrientsConcurrent:
    """Tests for validate_nutrients_concurrent sync wrapper."""

    def test_validates_multiple_nutrients(self):
        """Test validating multiple nutrients concurrently."""
        comparison_result = {
            "matches": [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "sr_value": 20.0,
                    "foundation_value": 20.2,
                    "unit": "g",
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "discrepancies": [
                {
                    "nutrient_id": 1004,
                    "nutrient_name": "Fat",
                    "sr_value": 10.0,
                    "foundation_value": 15.0,
                    "unit": "g",
                    "discrepancy": {"percentage": 40.0},
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        sr_data = {"nutrients": {}}
        foundation_data = {"nutrients": {}}

        results = validate_nutrients_concurrent(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data=sr_data,
            foundation_data=foundation_data,
            missing_nutrients=[]
        )

        assert 1003 in results
        assert 1004 in results

    def test_skips_matching_nutrients(self):
        """Test that matching nutrients are skipped (not sent to API)."""
        comparison_result = {
            "matches": [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "sr_value": 20.0,
                    "foundation_value": 20.1,  # < 5% difference
                    "unit": "g",
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        results = validate_nutrients_concurrent(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data={"nutrients": {}},
            missing_nutrients=[]
        )

        assert 1003 in results
        # Skipped nutrients have prompt_type "skipped"
        assert results[1003].prompt_type == "skipped"
        assert results[1003].recommendation == "foundation"

    def test_validates_missing_nutrients(self):
        """Test validating missing nutrients."""
        comparison_result = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        missing_nutrients = [
            {"nutrient_id": 1234, "nutrient_name": "Taurine", "unit": "mg"}
        ]

        results = validate_nutrients_concurrent(
            food_name="Chicken, raw",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=missing_nutrients
        )

        assert 1234 in results

    def test_returns_empty_for_no_nutrients(self):
        """Test returns empty dict when no nutrients."""
        comparison_result = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        results = validate_nutrients_concurrent(
            food_name="Empty Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=[]
        )

        assert results == {}

    def test_returns_same_type_as_sequential(self):
        """Test return type matches sequential function."""
        comparison_result = {
            "matches": [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "sr_value": 20.0,
                    "foundation_value": 20.1,
                    "unit": "g",
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        concurrent_results = validate_nutrients_concurrent(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data={"nutrients": {}},
            missing_nutrients=[]
        )

        sequential_results = validate_nutrients_sequential(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data={"nutrients": {}},
            missing_nutrients=[]
        )

        # Both should return dict with same keys
        assert set(concurrent_results.keys()) == set(sequential_results.keys())

        # Both should return AIValidationResult objects
        for key in concurrent_results:
            assert hasattr(concurrent_results[key], 'nutrient_id')
            assert hasattr(concurrent_results[key], 'recommendation')
            assert hasattr(concurrent_results[key], 'confidence')

    def test_concurrent_limit_capped(self):
        """Test concurrent limit is capped at max."""
        # This should not raise an error even with high limit
        comparison_result = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        # Limit is capped internally
        results = validate_nutrients_concurrent(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=[],
            concurrent_limit=100  # Will be capped to AI_MAX_CONCURRENT_LIMIT
        )

        assert results == {}

    def test_verbose_mode(self, capsys):
        """Test verbose mode prints progress."""
        comparison_result = {
            "matches": [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "sr_value": 20.0,
                    "foundation_value": 20.1,
                    "unit": "g",
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        results = validate_nutrients_concurrent(
            food_name="Test Food",
            comparison_result=comparison_result,
            sr_data={"nutrients": {}},
            foundation_data={"nutrients": {}},
            missing_nutrients=[],
            verbose=True
        )

        captured = capsys.readouterr()
        assert "Validating" in captured.out
        assert "concurrent" in captured.out


class TestValidateNutrientsAsync:
    """Tests for _validate_nutrients_async internal function."""

    def test_validates_multiple_nutrients_concurrently(self):
        """Test concurrent validation of multiple nutrients."""
        async def run_test():
            nutrients_data = [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "unit": "g",
                    "prompt_type": "sr_only",
                    "sr_value": 20.0,
                    "sr_metadata": {}
                },
                {
                    "nutrient_id": 1004,
                    "nutrient_name": "Fat",
                    "unit": "g",
                    "prompt_type": "sr_only",
                    "sr_value": 10.0,
                    "sr_metadata": {}
                }
            ]

            results = await _validate_nutrients_async(
                food_name="Test Food",
                nutrients_data=nutrients_data
            )

            assert 1003 in results
            assert 1004 in results

        asyncio.run(run_test())

    def test_handles_empty_list(self):
        """Test handling empty nutrients list."""
        async def run_test():
            results = await _validate_nutrients_async(
                food_name="Test Food",
                nutrients_data=[]
            )
            assert results == {}

        asyncio.run(run_test())

    def test_skips_matching_nutrients(self):
        """Test that match nutrients are skipped."""
        async def run_test():
            nutrients_data = [
                {
                    "nutrient_id": 1003,
                    "nutrient_name": "Protein",
                    "unit": "g",
                    "prompt_type": "match",
                    "sr_value": 20.0,
                    "foundation_value": 20.1,  # < 5% difference
                    "sr_metadata": {},
                    "foundation_metadata": {}
                }
            ]

            results = await _validate_nutrients_async(
                food_name="Test Food",
                nutrients_data=nutrients_data
            )

            assert 1003 in results
            assert results[1003].prompt_type == "skipped"

        asyncio.run(run_test())
