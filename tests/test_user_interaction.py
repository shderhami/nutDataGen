"""
Tests for user_interaction.py

Uses mocked input for testing interactive prompts.
"""
import sys
from pathlib import Path
from unittest.mock import patch
from io import StringIO

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from user_interaction import (
    display_comparison_report,
    display_welcome,
    prompt_food_info,
    prompt_discrepancy_decision,
    prompt_missing_nutrient,
    prompt_sr_only_nutrient,
    prompt_confirmation,
    display_final_summary,
    display_progress,
    display_error,
    display_success,
    display_info,
)


class TestDisplayFunctions:
    """Tests for display functions."""

    def test_display_comparison_report(self, capsys):
        """Test display_comparison_report outputs report."""
        report = "Test Report\nLine 2"
        display_comparison_report(report)
        captured = capsys.readouterr()
        assert "Test Report" in captured.out
        assert "Line 2" in captured.out

    def test_display_welcome(self, capsys):
        """Test display_welcome outputs welcome message."""
        display_welcome()
        captured = capsys.readouterr()
        assert "USDA" in captured.out
        assert "Nutrition" in captured.out

    def test_display_progress(self, capsys):
        """Test display_progress shows progress."""
        display_progress(5, 10, "Protein")
        captured = capsys.readouterr()
        assert "[5/10]" in captured.out
        assert "Protein" in captured.out

    def test_display_error(self, capsys):
        """Test display_error shows error."""
        display_error("Something went wrong")
        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "Something went wrong" in captured.out

    def test_display_success(self, capsys):
        """Test display_success shows success."""
        display_success("Operation completed")
        captured = capsys.readouterr()
        assert "Operation completed" in captured.out

    def test_display_info(self, capsys):
        """Test display_info shows info message."""
        display_info("Information message")
        captured = capsys.readouterr()
        assert "Information message" in captured.out


class TestPromptFoodInfo:
    """Tests for prompt_food_info function."""

    @patch('builtins.input')
    def test_returns_correct_structure(self, mock_input):
        """Test prompt_food_info returns correct structure."""
        mock_input.side_effect = [
            "FOOD_001",        # food_id
            "Test Food",       # food_name
            "171116",          # sr_fdc_id
            "746784"           # foundation_fdc_id
        ]

        result = prompt_food_info()

        assert result["food_id"] == "FOOD_001"
        assert result["food_name"] == "Test Food"
        assert result["sr_fdc_id"] == 171116
        assert result["foundation_fdc_id"] == 746784

    @patch('builtins.input')
    def test_handles_empty_foundation_id(self, mock_input):
        """Test handles empty foundation FDC ID."""
        mock_input.side_effect = [
            "FOOD_001",        # food_id
            "Test Food",       # food_name
            "171116",          # sr_fdc_id
            ""                 # foundation_fdc_id (skip)
        ]

        result = prompt_food_info()

        assert result["foundation_fdc_id"] is None

    @patch('builtins.input')
    def test_handles_invalid_sr_fdc_id_skips(self, mock_input):
        """Test handles invalid SR FDC ID by skipping (setting to None)."""
        mock_input.side_effect = [
            "FOOD_001",        # food_id
            "Test Food",       # food_name
            "invalid",         # invalid sr_fdc_id - now skipped
            ""                 # foundation_fdc_id
        ]

        result = prompt_food_info()

        assert result["sr_fdc_id"] is None

    @patch('builtins.input')
    def test_handles_empty_sr_fdc_id(self, mock_input):
        """Test handles empty SR FDC ID (skips)."""
        mock_input.side_effect = [
            "FOOD_001",        # food_id
            "Test Food",       # food_name
            "",                # sr_fdc_id (skip)
            ""                 # foundation_fdc_id (skip)
        ]

        result = prompt_food_info()

        assert result["sr_fdc_id"] is None
        assert result["foundation_fdc_id"] is None


class TestPromptDiscrepancyDecision:
    """Tests for prompt_discrepancy_decision function."""

    @pytest.fixture
    def sample_discrepancy(self):
        return {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "unit": "g",
            "sr_value": 20.0,
            "foundation_value": 25.0,
            "discrepancy": {
                "percentage": 22.2,
                "tier": "significant"
            }
        }

    @patch('builtins.input')
    def test_choice_1_keep_sr_legacy(self, mock_input, sample_discrepancy):
        """Test choosing SR Legacy value."""
        mock_input.side_effect = ["1", "Trusted source"]

        result = prompt_discrepancy_decision(sample_discrepancy)

        assert result["chosen_value"] == 20.0
        assert result["chosen_source"] == "sr_legacy"
        assert "Trusted source" in result["comment"]

    @patch('builtins.input')
    def test_choice_2_use_foundation(self, mock_input, sample_discrepancy):
        """Test choosing Foundation value."""
        mock_input.side_effect = ["2", "Better sampling"]

        result = prompt_discrepancy_decision(sample_discrepancy)

        assert result["chosen_value"] == 25.0
        assert result["chosen_source"] == "foundation"

    @patch('builtins.input')
    def test_choice_3_manual_value(self, mock_input, sample_discrepancy):
        """Test entering manual value."""
        mock_input.side_effect = ["3", "22.5", "literature", "From paper"]

        result = prompt_discrepancy_decision(sample_discrepancy)

        assert result["chosen_value"] == 22.5
        assert result["chosen_source"] == "literature"

    @patch('builtins.input')
    def test_invalid_choice_retry(self, mock_input, sample_discrepancy):
        """Test invalid choice prompts for retry."""
        mock_input.side_effect = ["invalid", "5", "4", "1", ""]

        result = prompt_discrepancy_decision(sample_discrepancy)

        assert result["chosen_source"] == "sr_legacy"


class TestPromptMissingNutrient:
    """Tests for prompt_missing_nutrient function."""

    @pytest.fixture
    def sample_missing(self):
        return {
            "nutrient_id": None,
            "nutrient_name": "Taurine",
            "unit": "mg",
            "notes": "Requires literature source"
        }

    @patch('builtins.input')
    def test_enter_value_with_citation(self, mock_input, sample_missing):
        """Test entering literature value with citation (required)."""
        mock_input.side_effect = ["170", "Spitze et al. 2003"]

        result = prompt_missing_nutrient(sample_missing)

        assert result["chosen_value"] == 170.0
        assert result["chosen_source"] == "literature"
        assert "Spitze" in result["comment"]

    @patch('builtins.input')
    def test_invalid_value_retry(self, mock_input, sample_missing):
        """Test invalid value prompts for retry."""
        mock_input.side_effect = ["invalid", "170", "source"]

        result = prompt_missing_nutrient(sample_missing)

        assert result["chosen_value"] == 170.0

    @patch('builtins.input')
    def test_empty_citation_retry(self, mock_input, sample_missing):
        """Test empty citation prompts for retry."""
        mock_input.side_effect = ["170", "", "Spitze et al. 2003"]

        result = prompt_missing_nutrient(sample_missing)

        assert result["chosen_value"] == 170.0
        assert "Spitze" in result["comment"]


class TestPromptSrOnlyNutrient:
    """Tests for prompt_sr_only_nutrient function."""

    @pytest.fixture
    def sample_sr_only(self):
        return {
            "nutrient_id": 1089,
            "nutrient_name": "Iron",
            "sr_value": 1.3,
            "unit": "mg"
        }

    @patch('builtins.input')
    def test_accept_sr_legacy_value(self, mock_input, sample_sr_only):
        """Test accepting SR only value with choice 1."""
        mock_input.side_effect = ["1"]

        result = prompt_sr_only_nutrient(sample_sr_only)

        assert result["chosen_value"] == 1.3
        assert result["chosen_source"] == "sr_legacy"

    @patch('builtins.input')
    def test_enter_different_value(self, mock_input, sample_sr_only):
        """Test entering different value with choice 2."""
        mock_input.side_effect = ["2", "1.5", "literature", "Value from paper"]

        result = prompt_sr_only_nutrient(sample_sr_only)

        assert result["chosen_value"] == 1.5
        assert result["chosen_source"] == "literature"
        assert "Rejected SR Legacy" in result["comment"]

    @patch('builtins.input')
    def test_invalid_choice_retry(self, mock_input, sample_sr_only):
        """Test invalid choice prompts for retry."""
        mock_input.side_effect = ["invalid", "3", "1"]

        result = prompt_sr_only_nutrient(sample_sr_only)

        assert result["chosen_value"] == 1.3
        assert result["chosen_source"] == "sr_legacy"


class TestPromptConfirmation:
    """Tests for prompt_confirmation function."""

    @patch('builtins.input')
    def test_yes_response(self, mock_input):
        """Test 'y' returns True."""
        mock_input.return_value = "y"
        assert prompt_confirmation("Confirm?") is True

    @patch('builtins.input')
    def test_yes_full_response(self, mock_input):
        """Test 'yes' returns True."""
        mock_input.return_value = "yes"
        assert prompt_confirmation("Confirm?") is True

    @patch('builtins.input')
    def test_empty_response_defaults_yes(self, mock_input):
        """Test empty response returns True."""
        mock_input.return_value = ""
        assert prompt_confirmation("Confirm?") is True

    @patch('builtins.input')
    def test_no_response(self, mock_input):
        """Test 'n' returns False."""
        mock_input.return_value = "n"
        assert prompt_confirmation("Confirm?") is False

    @patch('builtins.input')
    def test_no_full_response(self, mock_input):
        """Test 'no' returns False."""
        mock_input.return_value = "no"
        assert prompt_confirmation("Confirm?") is False

    @patch('builtins.input')
    def test_invalid_then_valid(self, mock_input):
        """Test invalid response prompts retry."""
        mock_input.side_effect = ["maybe", "y"]
        assert prompt_confirmation("Confirm?") is True


class TestDisplayFinalSummary:
    """Tests for display_final_summary function."""

    def test_displays_summary(self, capsys):
        """Test display_final_summary shows summary."""
        food_data = [
            {"fediaf_nutrient_name": "Protein", "value": "20", "unit": "g", "source": "sr_legacy"},
            {"fediaf_nutrient_name": "Fat", "value": "10", "unit": "g", "source": "foundation"},
            {"fediaf_nutrient_name": "Taurine", "value": "", "unit": "mg", "source": "skipped"},
        ]

        display_final_summary(food_data, "Test Food")

        captured = capsys.readouterr()
        assert "FINAL SUMMARY" in captured.out
        assert "Test Food" in captured.out
        assert "Total nutrients: 3" in captured.out
        assert "Protein" in captured.out
        assert "20" in captured.out
        assert "skipped" in captured.out
