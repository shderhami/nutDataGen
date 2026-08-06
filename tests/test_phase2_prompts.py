"""
Tests for the Phase 2 items of the AI-validation plan.

2.1 provenance metadata reaches every value-bearing prompt (including via the
single-source pseudo-comparisons in main.py, which is where the narrowing
actually was), 2.2 food identity, 2.3 structured outputs, 2.4 confirmed_zero.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import ai_validation
import main
from ai_validation import (
    _RECOMMENDATION_ENUMS,
    _response_schema,
    build_prompt_both_sources,
    build_prompt_foundation_only,
    build_prompt_missing,
    build_prompt_sr_only,
    format_ai_suggestion,
    parse_single_response,
)

FULL_META = {
    "num_samples": 12,
    "min_value": 1.5,
    "max_value": 3.5,
    "median_value": 2.4,
    "year_acquired": "2018",
    "derivation_description": "Analytical",
}

# The lamb-shoulder EPA/DHA shape: a zero USDA never measured.
UNPOPULATED_META = {
    "num_samples": None,
    "min_value": None,
    "max_value": None,
    "median_value": None,
    "year_acquired": "2018",
    "derivation_description": None,
}


class TestProvenanceReachesPrompts:
    """2.1 — all six metadata fields must be visible to the model."""

    def test_sr_only_prompt_contains_all_metadata(self):
        prompt = build_prompt_sr_only("lamb shoulder", "EPA", 0.0, "g", FULL_META)
        assert "12" in prompt                      # num_samples
        assert "1.5" in prompt and "3.5" in prompt  # min / max
        assert "2.4" in prompt                      # median
        assert "Analytical" in prompt               # derivation
        assert "2018" in prompt                     # year

    def test_foundation_only_prompt_contains_all_metadata(self):
        prompt = build_prompt_foundation_only("lamb shoulder", "EPA", 0.0, "g", FULL_META)
        assert "12" in prompt
        assert "2.4" in prompt
        assert "Analytical" in prompt

    def test_both_sources_prompt_carries_both_provenance_blocks(self):
        other = dict(FULL_META, num_samples=40, median_value=9.9, derivation_description="Calculated")
        prompt = build_prompt_both_sources(
            "lamb shoulder", "EPA", 0.1, 0.2, "g", 66.7, FULL_META, other
        )
        assert "12" in prompt and "40" in prompt
        assert "2.4" in prompt and "9.9" in prompt
        assert "Analytical" in prompt and "Calculated" in prompt

    def test_unpopulated_zero_is_visibly_unmeasured(self):
        """The exact failure case: no data points, no derivation."""
        prompt = build_prompt_sr_only("lamb shoulder", "EPA", 0.0, "g", UNPOPULATED_META)
        assert "none recorded" in prompt
        assert "placeholder" in prompt.lower()

    def test_value_bearing_prompts_carry_the_provenance_rule(self):
        for prompt in (
            build_prompt_sr_only("f", "n", 1.0, "g", FULL_META),
            build_prompt_foundation_only("f", "n", 1.0, "g", FULL_META),
            build_prompt_both_sources("f", "n", 1.0, 2.0, "g", 50.0, FULL_META, FULL_META),
        ):
            assert "PROVENANCE MATTERS" in prompt

    def test_missing_prompt_has_no_usda_value(self):
        """build_prompt_missing serves nutrients absent from both sources, so
        there is no USDA value or provenance block to add."""
        prompt = build_prompt_missing("lamb shoulder", "Taurine", "mg")
        assert "PROVENANCE MATTERS" not in prompt
        assert "Data Points" not in prompt


class TestSingleSourcePseudoComparisons:
    """2.1 [audit] — the narrowing was in main.py, not ai_validation.py."""

    def test_api_metadata_helper_keeps_all_six_fields(self):
        nutrient = {
            "num_samples": 5, "min_value": 1.0, "max_value": 2.0,
            "median_value": 1.5, "year_acquired": "2019",
            "derivation_description": "Analytical",
        }
        meta = main._api_nutrient_metadata(nutrient)
        assert set(meta) == {
            "num_samples", "min_value", "max_value",
            "median_value", "year_acquired", "derivation_description",
        }
        assert meta["median_value"] == 1.5

    def test_sr_only_path_passes_full_metadata_to_validator(self, monkeypatch):
        """Acceptance: a single-source food (the lamb-shoulder shape) must
        reach the validator with min/median/max intact."""
        captured = {}

        monkeypatch.setattr(
            main, "fetch_sr_legacy",
            lambda fdc_id: {
                "nutrients": {
                    1003: {
                        "name": "Protein", "value": 20.0, "unit": "g",
                        "num_samples": 7, "min_value": 18.0, "max_value": 22.0,
                        "median_value": 19.5, "year_acquired": "2018",
                        "derivation_description": "Analytical",
                    }
                },
                "unpopulated_zeros": [],
            },
        )

        def fake_validate(**kwargs):
            captured.update(kwargs)
            return {}

        monkeypatch.setattr(main, "validate_nutrients_concurrent", fake_validate)
        monkeypatch.setattr(main, "prompt_sr_only_nutrient", lambda n, s: {
            "nutrient_name": "Protein", "chosen_value": 20.0,
            "chosen_source": "sr_legacy", "comment": "",
        })
        monkeypatch.setattr(main, "prompt_missing_nutrient", lambda n, s: {
            "nutrient_id": n.get("nutrient_id"), "chosen_value": 1.0,
            "chosen_source": "literature", "comment": "",
        })

        main.process_single_food(
            10001,
            {"food_name": "lamb shoulder", "sr_fdc_id": 174326, "foundation_fdc_id": None},
        )

        sr_only = captured["comparison_result"]["sr_only"]
        meta = sr_only[0]["sr_metadata"]
        assert meta["min_value"] == 18.0
        assert meta["median_value"] == 19.5
        assert meta["max_value"] == 22.0

    def test_food_info_threaded_to_validator(self, monkeypatch):
        """2.2 — the validator receives the food identity, not just the name."""
        captured = {}
        monkeypatch.setattr(
            main, "fetch_sr_legacy",
            lambda fdc_id: {"nutrients": {}, "unpopulated_zeros": []},
        )

        def fake_validate(**kwargs):
            captured.update(kwargs)
            return {}

        monkeypatch.setattr(main, "validate_nutrients_concurrent", fake_validate)
        monkeypatch.setattr(main, "prompt_missing_nutrient", lambda n, s: {
            "nutrient_id": n.get("nutrient_id"), "chosen_value": 1.0,
            "chosen_source": "literature", "comment": "",
        })

        food_info = {
            "food_name": "lamb shoulder", "sr_fdc_id": 174326,
            "foundation_fdc_id": None, "protein_species": "lamb",
            "cooking_method": "raw",
        }
        main.process_single_food(10001, food_info)
        assert captured["food_info"] is food_info


class TestFoodIdentity:
    """2.2 — species / cooking method / FDC IDs reach the prompt."""

    FOOD_INFO = {
        "protein_species": "lamb",
        "cooking_method": "raw",
        "category": "Meat",
        "sr_fdc_id": 174326,
    }

    def test_identity_appears_in_prompt(self):
        prompt = build_prompt_sr_only(
            "lamb shoulder", "EPA", 0.0, "g", FULL_META, food_info=self.FOOD_INFO
        )
        assert "lamb" in prompt
        assert "Meat" in prompt
        assert "174326" in prompt

    def test_missing_prompt_also_identified(self):
        prompt = build_prompt_missing(
            "lamb shoulder", "Taurine", "mg", food_info=self.FOOD_INFO
        )
        assert "lamb" in prompt
        assert "174326" in prompt

    def test_cooking_method_never_reaches_the_prompt(self):
        """Ingredients are entered raw and cooking is adjusted for downstream,
        so the stored cooking method describes later preparation, not the
        composition being validated. Passing it would describe a raw USDA
        value as cooked."""
        info = dict(self.FOOD_INFO, cooking_method="braised")
        for prompt in (
            build_prompt_sr_only("lamb shoulder", "EPA", 0.0, "g", FULL_META, info),
            build_prompt_foundation_only("lamb shoulder", "EPA", 0.0, "g", FULL_META, info),
            build_prompt_both_sources(
                "lamb shoulder", "EPA", 0.1, 0.2, "g", 66.0, FULL_META, FULL_META, info
            ),
            build_prompt_missing("lamb shoulder", "Taurine", "mg", info),
        ):
            assert "braised" not in prompt
            assert "cooking method" not in prompt.lower()

    def test_absent_food_info_degrades_to_bare_name(self):
        prompt = build_prompt_sr_only("lamb shoulder", "EPA", 0.0, "g", FULL_META)
        assert "lamb shoulder" in prompt


class TestStructuredOutputs:
    """2.3 — schema shape, and the heuristic is gone."""

    def test_schema_enumerates_legal_recommendations_per_prompt_type(self):
        assert _response_schema("sr_only")["properties"]["recommendation"]["enum"] == [
            "sr_legacy", "literature"
        ]
        assert "confirmed_zero" in _response_schema("missing")["properties"]["recommendation"]["enum"]
        # confirmed_zero is only offered where a USDA value is absent
        assert "confirmed_zero" not in _RECOMMENDATION_ENUMS["sr_only"]

    def test_schema_is_strict(self):
        schema = _response_schema("both_sources")
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == {
            "recommendation", "recommended_value", "justification",
            "literature_source", "confidence",
        }

    def test_schema_has_no_numeric_constraints(self):
        """Structured outputs reject minimum/maximum — bounds live in code."""
        schema = json.dumps(_response_schema("missing"))
        assert "minimum" not in schema and "maximum" not in schema

    def test_parse_failure_path_survives(self):
        """Truncation and mock mode still produce unparseable text."""
        result = parse_single_response(
            '{"recommendation": "literature", "recommended_v',
            {"nutrient_id": 1003, "nutrient_name": "Protein"},
        )
        assert result.recommendation == "error"

    def test_call_sites_pass_schema(self, monkeypatch):
        """The sync validator forwards a schema to the API layer."""
        seen = {}

        def fake_retry(prompt, api_key=None, schema=None):
            seen["schema"] = schema
            return json.dumps({
                "recommendation": "sr_legacy", "recommended_value": None,
                "justification": "j", "literature_source": "s", "confidence": "high",
            })

        monkeypatch.setattr(ai_validation, "call_claude_api_with_retry", fake_retry)
        ai_validation.validate_nutrient_single(
            "food",
            {"nutrient_id": 1003, "nutrient_name": "Protein", "unit": "g",
             "prompt_type": "sr_only", "sr_value": 1.0, "sr_metadata": FULL_META},
        )
        assert seen["schema"]["properties"]["recommendation"]["enum"] == [
            "sr_legacy", "literature"
        ]


class TestConfirmedZero:
    """2.4 — a genuine zero has its own home, distinct from 'unknown'."""

    def test_missing_prompt_offers_confirmed_zero(self):
        prompt = build_prompt_missing("lamb shoulder", "EPA", "g")
        assert "confirmed_zero" in prompt

    def test_confirmed_zero_without_value_becomes_zero_not_none(self):
        response = json.dumps({
            "recommendation": "confirmed_zero", "recommended_value": None,
            "justification": "not present in mammalian muscle",
            "literature_source": "lit", "confidence": "high",
        })
        result = parse_single_response(
            response, {"nutrient_id": 1278, "nutrient_name": "EPA"}
        )
        assert result.recommended_value == 0.0

    def test_confirmed_zero_renders_distinctly(self):
        result = ai_validation.AIValidationResult(
            nutrient_id=1278, nutrient_name="EPA", prompt_type="missing",
            recommendation="confirmed_zero", recommended_value=0.0,
            justification="genuinely absent", literature_source="lit",
            confidence="high",
        )
        formatted = format_ai_suggestion(result)
        assert "confirmed zero" in formatted.lower()
        assert "insufficient" not in formatted.lower()

    def test_sibling_repo_column_is_free_text(self):
        """2.4 [audit] cross-repo check: ai_recommendation is VARCHAR(50) with
        no CHECK constraint and the formulator never filters on its value, so a
        new enum member is additive. Pinned here so a future constraint or
        consumer breaks this test rather than production."""
        assert len("confirmed_zero") <= 50
