"""
Tests for comparison.py
"""
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from comparison import (
    calculate_discrepancy,
    classify_tier,
    compare_nutrients,
    generate_comparison_report,
    get_discrepancy_summary,
    extract_nutrient_metadata,
)


class TestCalculateDiscrepancy:
    """Tests for calculate_discrepancy function."""

    def test_identical_values_zero_percent(self):
        """Test calculate_discrepancy with identical values (0%)."""
        result = calculate_discrepancy(10.0, 10.0)
        assert result["percentage"] == 0.0
        assert result["tier"] == "trivial"

    def test_10_percent_difference(self):
        """Test calculate_discrepancy with ~10% difference."""
        # 10 vs 11 gives about 9.5% difference
        result = calculate_discrepancy(10.0, 11.0)
        assert 9 <= result["percentage"] <= 10
        assert result["tier"] == "moderate"

    def test_50_percent_difference(self):
        """Test calculate_discrepancy with 50% difference."""
        # 1 vs 2 gives 66.7% difference ((2-1)/1.5*100)
        result = calculate_discrepancy(1.0, 2.0)
        assert result["percentage"] > 50
        assert result["tier"] == "major"

    def test_both_zero_returns_zero(self):
        """Test that both values being zero returns 0%."""
        result = calculate_discrepancy(0.0, 0.0)
        assert result["percentage"] == 0.0
        assert result["tier"] == "trivial"

    def test_one_zero_returns_100_percent(self):
        """Test that one value being zero returns 100%."""
        result = calculate_discrepancy(10.0, 0.0)
        assert result["percentage"] == 100.0
        assert result["tier"] == "major"

    def test_returns_correct_structure(self):
        """Test that return dict has correct structure."""
        result = calculate_discrepancy(10.0, 12.0)
        assert "sr_value" in result
        assert "foundation_value" in result
        assert "percentage" in result
        assert "tier" in result
        assert result["sr_value"] == 10.0
        assert result["foundation_value"] == 12.0


class TestClassifyTier:
    """Tests for classify_tier function."""

    def test_trivial_tier(self):
        """Test classify_tier returns trivial for < 5%."""
        assert classify_tier(0) == "trivial"
        assert classify_tier(4.9) == "trivial"

    def test_moderate_tier(self):
        """Test classify_tier returns moderate for 5-15%."""
        assert classify_tier(5) == "moderate"
        assert classify_tier(10) == "moderate"
        assert classify_tier(14.9) == "moderate"

    def test_significant_tier(self):
        """Test classify_tier returns significant for 15-30%."""
        assert classify_tier(15) == "significant"
        assert classify_tier(25) == "significant"
        assert classify_tier(29.9) == "significant"

    def test_major_tier(self):
        """Test classify_tier returns major for > 30%."""
        assert classify_tier(30) == "major"
        assert classify_tier(50) == "major"
        assert classify_tier(100) == "major"

    def test_boundary_values(self):
        """Test exact boundary values."""
        assert classify_tier(4.99) == "trivial"
        assert classify_tier(5.0) == "moderate"
        assert classify_tier(14.99) == "moderate"
        assert classify_tier(15.0) == "significant"
        assert classify_tier(29.99) == "significant"
        assert classify_tier(30.0) == "major"


class TestCompareNutrients:
    """Tests for compare_nutrients function."""

    def test_correctly_categorizes_matching_nutrients(self):
        """Test compare_nutrients correctly categorizes matching nutrients."""
        sr_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 20.0, "unit": "g"},
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 20.5, "unit": "g"},  # < 5% diff
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        assert len(result["matches"]) == 1
        assert result["matches"][0]["nutrient_id"] == 1003

    def test_correctly_identifies_discrepancies(self):
        """Test compare_nutrients correctly identifies discrepancies."""
        sr_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 20.0, "unit": "g"},
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 25.0, "unit": "g"},  # > 5% diff
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        assert len(result["discrepancies"]) == 1
        assert result["discrepancies"][0]["nutrient_id"] == 1003
        assert "discrepancy" in result["discrepancies"][0]

    def test_handles_sr_only_nutrients(self):
        """Test compare_nutrients handles sr_only nutrients."""
        sr_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 20.0, "unit": "g"},
                1004: {"name": "Fat", "value": 10.0, "unit": "g"},
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": None, "unit": "g"},
                1004: {"name": "Fat", "value": 10.0, "unit": "g"},
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        assert len(result["sr_only"]) == 1
        assert result["sr_only"][0]["nutrient_id"] == 1003

    def test_handles_foundation_only_nutrients(self):
        """Test compare_nutrients handles foundation_only nutrients."""
        sr_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": None, "unit": "g"},
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 20.0, "unit": "g"},
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        assert len(result["foundation_only"]) == 1

    def test_handles_missing_both_nutrients(self):
        """Test compare_nutrients handles missing_both nutrients."""
        sr_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": None, "unit": "g"},
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": None, "unit": "g"},
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        assert len(result["missing_both"]) == 1

    def test_returns_correct_structure(self):
        """Test compare_nutrients returns correct structure."""
        sr_data = {"nutrients": {}}
        foundation_data = {"nutrients": {}}

        result = compare_nutrients(sr_data, foundation_data)

        assert "matches" in result
        assert "discrepancies" in result
        assert "sr_only" in result
        assert "foundation_only" in result
        assert "missing_both" in result

    def test_discrepancies_sorted_by_percentage(self):
        """Test that discrepancies are sorted by percentage (highest first)."""
        sr_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 10.0, "unit": "g"},
                1004: {"name": "Fat", "value": 10.0, "unit": "g"},
                1008: {"name": "Energy", "value": 100.0, "unit": "kcal"},
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 12.0, "unit": "g"},    # ~18%
                1004: {"name": "Fat", "value": 20.0, "unit": "g"},        # ~67%
                1008: {"name": "Energy", "value": 110.0, "unit": "kcal"}, # ~10%
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        # Should be sorted: Fat (67%) > Protein (18%) > Energy (10%)
        percentages = [d["discrepancy"]["percentage"] for d in result["discrepancies"]]
        assert percentages == sorted(percentages, reverse=True)


class TestGenerateComparisonReport:
    """Tests for generate_comparison_report function."""

    def test_produces_readable_output(self):
        """Test generate_comparison_report produces readable output."""
        comparison = {
            "matches": [{"nutrient_id": 1003, "nutrient_name": "Protein"}],
            "discrepancies": [{
                "nutrient_id": 1004,
                "nutrient_name": "Fat",
                "unit": "g",
                "sr_value": 10.0,
                "foundation_value": 15.0,
                "discrepancy": {"percentage": 40.0, "tier": "major"}
            }],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        report = generate_comparison_report(
            "Test Food",
            171116,
            746784,
            comparison
        )

        assert "COMPARISON REPORT" in report
        assert "Test Food" in report
        assert "171116" in report
        assert "746784" in report
        assert "Fat" in report
        assert "MAJOR" in report

    def test_includes_summary_section(self):
        """Test report includes summary section."""
        comparison = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        report = generate_comparison_report("Food", 123, 456, comparison)

        assert "Summary:" in report
        assert "Matching" in report
        assert "Discrepancies" in report

    def test_handles_no_foundation_id(self):
        """Test report handles None foundation ID."""
        comparison = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        report = generate_comparison_report("Food", 123, None, comparison)

        assert "Not provided" in report

    def test_includes_all_sections(self):
        """Test report includes all relevant sections."""
        comparison = {
            "matches": [{"nutrient_id": 1}],
            "discrepancies": [{
                "nutrient_id": 2,
                "nutrient_name": "Test",
                "unit": "g",
                "sr_value": 1.0,
                "foundation_value": 2.0,
                "discrepancy": {"percentage": 50.0, "tier": "major"}
            }],
            "sr_only": [{"nutrient_name": "SR Only", "sr_value": 1, "unit": "g"}],
            "foundation_only": [{"nutrient_name": "Found Only", "foundation_value": 1, "unit": "g"}],
            "missing_both": [{"nutrient_name": "Missing"}]
        }

        report = generate_comparison_report("Food", 123, 456, comparison)

        assert "DISCREPANCIES REQUIRING REVIEW" in report
        assert "NUTRIENTS ONLY IN SR LEGACY" in report
        assert "NUTRIENTS ONLY IN FOUNDATION" in report
        assert "NUTRIENTS MISSING FROM BOTH" in report


class TestGetDiscrepancySummary:
    """Tests for get_discrepancy_summary function."""

    def test_counts_tiers_correctly(self):
        """Test get_discrepancy_summary counts tiers correctly."""
        comparison = {
            "matches": [1, 2, 3],  # 3 trivial from matches
            "discrepancies": [
                {"discrepancy": {"tier": "moderate"}},
                {"discrepancy": {"tier": "moderate"}},
                {"discrepancy": {"tier": "significant"}},
                {"discrepancy": {"tier": "major"}},
            ],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        summary = get_discrepancy_summary(comparison)

        assert summary["trivial"] == 3
        assert summary["moderate"] == 2
        assert summary["significant"] == 1
        assert summary["major"] == 1

    def test_empty_comparison(self):
        """Test summary with empty comparison."""
        comparison = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": []
        }

        summary = get_discrepancy_summary(comparison)

        assert summary["trivial"] == 0
        assert summary["moderate"] == 0
        assert summary["significant"] == 0
        assert summary["major"] == 0


class TestExtractNutrientMetadata:
    """Tests for extract_nutrient_metadata function."""

    def test_extracts_all_fields(self):
        """Test extracts all metadata fields."""
        nutrient = {
            "name": "Protein",
            "value": 20.0,
            "unit": "g",
            "num_samples": 10,
            "min_value": 18.0,
            "max_value": 22.0,
            "median_value": 20.0,
            "year_acquired": "2019",
            "derivation_description": "Analytical"
        }

        result = extract_nutrient_metadata(nutrient)

        assert result["num_samples"] == 10
        assert result["min_value"] == 18.0
        assert result["max_value"] == 22.0
        assert result["median_value"] == 20.0
        assert result["year_acquired"] == "2019"
        assert result["derivation_description"] == "Analytical"
        # Note: standard_error and footnote removed - USDA API does not provide these

    def test_handles_missing_fields(self):
        """Test handles missing metadata fields gracefully."""
        nutrient = {
            "name": "Protein",
            "value": 20.0,
            "unit": "g"
        }

        result = extract_nutrient_metadata(nutrient)

        assert result["num_samples"] is None
        assert result["min_value"] is None

    def test_handles_empty_dict(self):
        """Test handles empty dict."""
        result = extract_nutrient_metadata({})

        assert result["num_samples"] is None
        assert result["min_value"] is None


class TestCompareNutrientsMetadata:
    """Tests for compare_nutrients with metadata pass-through."""

    def test_includes_sr_metadata_in_results(self):
        """Test compare_nutrients includes sr_metadata in results."""
        sr_data = {
            "nutrients": {
                1003: {
                    "name": "Protein", "value": 20.0, "unit": "g",
                    "num_samples": 10, "min_value": 18.0, "max_value": 22.0
                },
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 20.5, "unit": "g"},
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        assert "sr_metadata" in result["matches"][0]
        assert result["matches"][0]["sr_metadata"]["num_samples"] == 10
        assert result["matches"][0]["sr_metadata"]["min_value"] == 18.0

    def test_includes_foundation_metadata_in_results(self):
        """Test compare_nutrients includes foundation_metadata in results."""
        sr_data = {
            "nutrients": {
                1003: {"name": "Protein", "value": 20.0, "unit": "g"},
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {
                    "name": "Protein", "value": 20.5, "unit": "g",
                    "num_samples": 15, "min_value": 18.5, "max_value": 22.5
                },
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        assert "foundation_metadata" in result["matches"][0]
        assert result["matches"][0]["foundation_metadata"]["num_samples"] == 15
        assert result["matches"][0]["foundation_metadata"]["min_value"] == 18.5

    def test_discrepancies_include_both_metadata(self):
        """Test discrepancies include metadata from both sources."""
        sr_data = {
            "nutrients": {
                1003: {
                    "name": "Protein", "value": 20.0, "unit": "g",
                    "num_samples": 10, "derivation_description": "Analytical"
                },
            }
        }
        foundation_data = {
            "nutrients": {
                1003: {
                    "name": "Protein", "value": 30.0, "unit": "g",
                    "num_samples": 15, "derivation_description": "Calculated"
                },
            }
        }

        result = compare_nutrients(sr_data, foundation_data)

        disc = result["discrepancies"][0]
        assert disc["sr_metadata"]["num_samples"] == 10
        assert disc["sr_metadata"]["derivation_description"] == "Analytical"
        assert disc["foundation_metadata"]["num_samples"] == 15
        assert disc["foundation_metadata"]["derivation_description"] == "Calculated"
