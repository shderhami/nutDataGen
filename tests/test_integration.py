"""
Integration tests for main.py

Tests complete workflow with mocked API and user input.
"""
import sys
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import (
    build_nutrient_record,
    process_single_food,
)
from database import NutrientRecord
from fediaf_nutrients import get_all_nutrients, get_usda_nutrient_ids


# Mock API responses
MOCK_SR_RESPONSE = {
    "fdcId": 171116,
    "description": "Chicken, broiler or fryers, thigh, meat only, raw",
    "dataType": "SR Legacy",
    "foodNutrients": [
        {"nutrient": {"id": 1003, "name": "Protein", "unitName": "g"}, "amount": 19.6},
        {"nutrient": {"id": 1004, "name": "Total lipid (fat)", "unitName": "g"}, "amount": 6.99},
        {"nutrient": {"id": 1008, "name": "Energy", "unitName": "kcal"}, "amount": 142},
        {"nutrient": {"id": 1087, "name": "Calcium, Ca", "unitName": "mg"}, "amount": 8},
        {"nutrient": {"id": 1089, "name": "Iron, Fe", "unitName": "mg"}, "amount": 1.3},
        {"nutrient": {"id": 1215, "name": "Methionine", "unitName": "g"}, "amount": 0.44},
        {"nutrient": {"id": 1216, "name": "Cystine", "unitName": "g"}, "amount": 0.24},
        {"nutrient": {"id": 1217, "name": "Phenylalanine", "unitName": "g"}, "amount": 0.65},
        {"nutrient": {"id": 1218, "name": "Tyrosine", "unitName": "g"}, "amount": 0.58},
    ]
}

MOCK_FOUNDATION_RESPONSE = {
    "fdcId": 746784,
    "description": "Chicken, broiler, thigh, meat only, raw",
    "dataType": "Foundation",
    "foodNutrients": [
        {"nutrient": {"id": 1003, "name": "Protein", "unitName": "g"}, "amount": 20.1},
        {"nutrient": {"id": 1004, "name": "Total lipid (fat)", "unitName": "g"}, "amount": 7.5},
        {"nutrient": {"id": 1008, "name": "Energy", "unitName": "kcal"}, "amount": 150},
        {"nutrient": {"id": 1087, "name": "Calcium, Ca", "unitName": "mg"}, "amount": 9},
        {"nutrient": {"id": 1089, "name": "Iron, Fe", "unitName": "mg"}, "amount": 0.89},  # Significant diff
    ]
}


class TestBuildNutrientRecord:
    """Tests for build_nutrient_record function."""

    def test_creates_valid_record(self):
        """Test creates valid record matching database schema."""
        record = build_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.5,
            source="sr_legacy",
            comment="Test comment"
        )

        assert record["food_id"] == 1001
        assert record["fediaf_nutrient_name"] == "Crude Protein"
        assert record["usda_nutrient_name"] == "Protein"
        assert record["value"] == 20.5
        assert record["source"] == "sr_legacy"

    def test_handles_none_values(self):
        """Test handles None values correctly."""
        record = build_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=None,
            fediaf_nutrient_name="Taurine",
            usda_nutrient_name=None,
            unit="mg",
            value=None,
            source="skipped"
        )

        assert record["nutrient_id"] is None
        assert record["usda_nutrient_name"] is None
        assert record["value"] is None

    def test_includes_usda_metadata(self):
        """Test includes USDA metadata fields."""
        record = build_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.5,
            source="sr_legacy",
            num_samples=10,
            min_value=18.5,
            max_value=22.5,
            median_value=20.3,
            year_acquired="2019",
            derivation_description="Analytical"
        )

        assert record["num_samples"] == 10
        assert record["min_value"] == 18.5
        assert record["max_value"] == 22.5
        assert record["median_value"] == 20.3
        assert record["year_acquired"] == "2019"
        assert record["derivation_description"] == "Analytical"
        # SE is estimated from range
        assert record["estimated_se"] is not None

    def test_calculates_statistics(self):
        """Test calculates statistical fields from range estimation."""
        record = build_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.0,
            source="sr_legacy",
            num_samples=50,
            min_value=18.0,
            max_value=22.0
        )

        # Should have calculated statistics (native floats, not strings)
        assert record["confidence_interval_lower"] is not None
        assert record["confidence_interval_upper"] is not None
        assert record["coefficient_of_variation"] is not None
        assert record["range_uncertainty"] is not None


class TestProcessSingleFood:
    """Tests for process_single_food function with mocked dependencies."""

    @pytest.fixture
    def food_info(self):
        return {
            "food_name": "Chicken thigh, meat only, raw",
            "sr_fdc_id": 171116,
            "foundation_fdc_id": 746784
        }

    @pytest.fixture
    def food_info_sr_only(self):
        return {
            "food_name": "Chicken thigh, meat only, raw",
            "sr_fdc_id": 171116,
            "foundation_fdc_id": None
        }

    @patch('main.fetch_foundation')
    @patch('main.fetch_sr_legacy')
    @patch('main.prompt_discrepancy_decision')
    @patch('main.prompt_sr_only_nutrient')
    @patch('main.prompt_missing_nutrient')
    def test_processes_food_with_both_sources(
        self, mock_missing, mock_sr_only, mock_disc, mock_fetch_found, mock_fetch_sr, food_info
    ):
        """Test processing food with both SR Legacy and Foundation data."""
        # Setup mocks with full metadata
        mock_fetch_sr.return_value = {
            "fdc_id": 171116,
            "description": "Chicken thigh",
            "data_type": "SR Legacy",
            "nutrients": {
                1003: {"name": "Protein", "value": 19.6, "unit": "g",
                       "num_samples": 10, "min_value": 18.0, "max_value": 21.0,
                       "median_value": 19.5,
                       "year_acquired": "2018", "derivation_description": "Analytical"},
                1004: {"name": "Fat", "value": 6.99, "unit": "g",
                       "num_samples": None, "min_value": None, "max_value": None,
                       "median_value": None,
                       "year_acquired": None, "derivation_description": "Calculated"},
                1089: {"name": "Iron", "value": 1.3, "unit": "mg",
                       "num_samples": 5, "min_value": 1.1, "max_value": 1.5,
                       "median_value": 1.3,
                       "year_acquired": "2019", "derivation_description": "Analytical"},
                1223: {"name": "Methionine", "value": 0.44, "unit": "g",
                       "num_samples": None, "min_value": None, "max_value": None,
                       "median_value": None,
                       "year_acquired": None, "derivation_description": None},
                1213: {"name": "Cystine", "value": 0.24, "unit": "g",
                       "num_samples": None, "min_value": None, "max_value": None,
                       "median_value": None,
                       "year_acquired": None, "derivation_description": None},
            }
        }

        mock_fetch_found.return_value = {
            "fdc_id": 746784,
            "description": "Chicken thigh",
            "data_type": "Foundation",
            "nutrients": {
                1003: {"name": "Protein", "value": 20.0, "unit": "g",
                       "num_samples": 15, "min_value": 18.5, "max_value": 21.5,
                       "median_value": 20.0,
                       "year_acquired": "2020", "derivation_description": "Analytical"},
                1004: {"name": "Fat", "value": 7.0, "unit": "g",
                       "num_samples": 15, "min_value": 6.0, "max_value": 8.0,
                       "median_value": 7.0,
                       "year_acquired": "2020", "derivation_description": "Analytical"},
                1089: {"name": "Iron", "value": 0.89, "unit": "mg",
                       "num_samples": 12, "min_value": 0.7, "max_value": 1.1,
                       "median_value": 0.88,
                       "year_acquired": "2020", "derivation_description": "Analytical"},
            }
        }

        # Mock user decisions
        mock_disc.return_value = {
            "nutrient_id": 1089,
            "nutrient_name": "Iron",
            "chosen_value": 0.89,
            "chosen_source": "foundation",
            "comment": "Better sampling"
        }

        mock_sr_only.return_value = {
            "nutrient_id": 1223,
            "nutrient_name": "Methionine",
            "chosen_value": 0.44,
            "chosen_source": "sr_legacy",
            "comment": "SR Legacy only"
        }

        mock_missing.return_value = {
            "nutrient_id": 1234,
            "nutrient_name": "Taurine",
            "chosen_value": 170.0,
            "chosen_source": "literature",
            "comment": "Source: Spitze et al. 2003"
        }

        # Process with food_id as first arg
        records = process_single_food(1001, food_info)

        # Verify
        assert len(records) > 0
        assert mock_fetch_sr.called
        assert mock_fetch_found.called

    @patch('main.fetch_sr_legacy')
    @patch('main.prompt_missing_nutrient')
    @patch('main.prompt_sr_only_nutrient')
    def test_processes_sr_only(self, mock_sr_only, mock_missing, mock_fetch_sr, food_info_sr_only):
        """Test processing food with SR Legacy only."""
        mock_fetch_sr.return_value = {
            "fdc_id": 171116,
            "description": "Chicken thigh",
            "data_type": "SR Legacy",
            "nutrients": {
                1003: {"name": "Protein", "value": 19.6, "unit": "g",
                       "num_samples": 10, "min_value": 18.0, "max_value": 21.0,
                       "median_value": 19.5,
                       "year_acquired": "2018", "derivation_description": "Analytical"},
            }
        }

        # Mock SR-only nutrient prompt to accept SR Legacy value
        mock_sr_only.return_value = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "chosen_value": 19.6,
            "chosen_source": "sr_legacy",
            "comment": "SR Legacy (only source)"
        }

        # Mock missing nutrient prompt (now requires a value)
        mock_missing.return_value = {
            "nutrient_id": 1234,
            "nutrient_name": "Taurine",
            "chosen_value": 170.0,
            "chosen_source": "literature",
            "comment": "Source: Spitze et al. 2003"
        }

        records = process_single_food(1001, food_info_sr_only)

        assert len(records) > 0
        assert mock_fetch_sr.called
        assert mock_sr_only.called

    @patch('main.prompt_missing_nutrient')
    @patch('main.fetch_sr_legacy')
    def test_handles_api_error(self, mock_fetch_sr, mock_missing, food_info_sr_only):
        """Test handles API error gracefully by continuing with missing nutrients."""
        from usda_api import USDAAPIError
        mock_fetch_sr.side_effect = USDAAPIError("API Error")

        # Mock missing nutrient prompts to provide values (all nutrients will be missing)
        mock_missing.return_value = {
            "nutrient_id": 1003,
            "nutrient_name": "Protein",
            "chosen_value": 20.0,
            "chosen_source": "literature",
            "comment": "Source: Test literature"
        }

        records = process_single_food(1001, food_info_sr_only)

        # Should still produce records (all from literature)
        assert len(records) > 0
        # All records should be from literature source
        for record in records:
            assert record.get("source") == "literature"


class TestFediafNutrientsCoverage:
    """Tests to verify all tracked nutrients are handled."""

    def test_all_nutrients_defined(self):
        """Test that exactly 52 nutrients are defined (50 FEDIAF + 2 secondary)."""
        all_nutrients = get_all_nutrients()
        assert len(all_nutrients) == 52

    def test_usda_ids_extracted(self):
        """Test that USDA IDs are properly extracted."""
        usda_ids = get_usda_nutrient_ids()
        # Should have IDs for nutrients available in USDA
        assert len(usda_ids) > 40  # Most should be available


class TestSchemaCompliance:
    """Tests to verify output matches expected database schema."""

    def test_record_has_all_required_fields(self):
        """Test that records have all required NutrientRecord fields."""
        from database import _NUTRIENT_COLUMNS

        record = build_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.0,
            source="sr_legacy"
        )

        for field in _NUTRIENT_COLUMNS:
            assert field in record, f"Missing field: {field}"
