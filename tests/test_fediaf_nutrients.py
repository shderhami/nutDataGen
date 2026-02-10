"""
Tests for fediaf_nutrients.py
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fediaf_nutrients import (
    FEDIAF_NUTRIENTS,
    TAURINE_NUTRIENT_ID,
    get_all_nutrients,
    get_usda_nutrient_ids,
    get_nutrient_by_id,
    get_nutrient_by_name,
    get_taurine_nutrient,
    get_nutrients_by_category,
)


class TestFediafNutrientsData:
    """Tests for the FEDIAF_NUTRIENTS data structure."""

    def test_fediaf_nutrients_contains_50_entries(self):
        """Test that FEDIAF_NUTRIENTS contains exactly 50 entries."""
        assert len(FEDIAF_NUTRIENTS) == 50, f"Expected 50 nutrients, got {len(FEDIAF_NUTRIENTS)}"

    def test_all_required_fields_present(self):
        """Test that all required fields are present in each entry."""
        required_fields = [
            "nutrient_id",
            "nutrient_name",
            "unit",
            "fediaf_required",
            "category",
            "notes"
        ]
        for i, nutrient in enumerate(FEDIAF_NUTRIENTS):
            for field in required_fields:
                assert field in nutrient, f"Missing field '{field}' in nutrient {i}: {nutrient.get('nutrient_name', 'Unknown')}"

    def test_nutrient_id_types(self):
        """Test that nutrient_id is int or None."""
        for nutrient in FEDIAF_NUTRIENTS:
            assert nutrient["nutrient_id"] is None or isinstance(nutrient["nutrient_id"], int), \
                f"Invalid nutrient_id type for {nutrient['nutrient_name']}"

    def test_fediaf_required_is_true(self):
        """Test that all nutrients have fediaf_required=True."""
        for nutrient in FEDIAF_NUTRIENTS:
            assert nutrient["fediaf_required"] is True, \
                f"fediaf_required should be True for {nutrient['nutrient_name']}"

    def test_valid_categories(self):
        """Test that all categories are valid."""
        valid_categories = {"Protein", "Amino Acid", "Fat", "Fatty Acid", "Mineral", "Vitamin", "Other"}
        for nutrient in FEDIAF_NUTRIENTS:
            assert nutrient["category"] in valid_categories, \
                f"Invalid category '{nutrient['category']}' for {nutrient['nutrient_name']}"

class TestGetAllNutrients:
    """Tests for get_all_nutrients function."""

    def test_returns_list(self):
        """Test that get_all_nutrients returns a list."""
        result = get_all_nutrients()
        assert isinstance(result, list)

    def test_returns_copy(self):
        """Test that get_all_nutrients returns a copy, not the original."""
        result = get_all_nutrients()
        result.append({"test": "data"})
        assert len(FEDIAF_NUTRIENTS) == 50

    def test_returns_all_50(self):
        """Test that get_all_nutrients returns all 50 nutrients."""
        result = get_all_nutrients()
        assert len(result) == 50


class TestGetUsdaNutrientIds:
    """Tests for get_usda_nutrient_ids function."""

    def test_returns_only_non_none_ids(self):
        """Test that get_usda_nutrient_ids returns only non-None IDs."""
        result = get_usda_nutrient_ids()
        assert None not in result
        assert all(isinstance(id, int) for id in result)

    def test_returns_list_of_ints(self):
        """Test that all returned IDs are integers."""
        result = get_usda_nutrient_ids()
        for id in result:
            assert isinstance(id, int)

    def test_count_matches_usda_available(self):
        """Test that count matches nutrients with usda_available=True and non-None ID."""
        result = get_usda_nutrient_ids()
        expected_count = sum(
            1 for n in FEDIAF_NUTRIENTS
            if n["nutrient_id"] is not None
        )
        assert len(result) == expected_count


class TestGetNutrientById:
    """Tests for get_nutrient_by_id function."""

    def test_returns_correct_nutrient(self):
        """Test get_nutrient_by_id returns correct nutrient."""
        result = get_nutrient_by_id(1003)
        assert result is not None
        assert result["nutrient_name"] == "Crude Protein"

    def test_returns_none_for_invalid_id(self):
        """Test get_nutrient_by_id returns None for invalid ID."""
        result = get_nutrient_by_id(99999)
        assert result is None

    def test_returns_copy(self):
        """Test that get_nutrient_by_id returns a copy."""
        result = get_nutrient_by_id(1003)
        result["nutrient_name"] = "Modified"
        original = get_nutrient_by_id(1003)
        assert original["nutrient_name"] == "Crude Protein"

    def test_various_nutrient_ids(self):
        """Test various known nutrient IDs."""
        test_cases = [
            (1003, "Crude Protein"),
            (1004, "Total Fat"),
            (1087, "Calcium"),
            (1008, "Energy"),
        ]
        for id, expected_name in test_cases:
            result = get_nutrient_by_id(id)
            assert result is not None
            assert result["nutrient_name"] == expected_name


class TestGetNutrientByName:
    """Tests for get_nutrient_by_name function."""

    def test_returns_correct_nutrient(self):
        """Test get_nutrient_by_name returns correct nutrient."""
        result = get_nutrient_by_name("Crude Protein")
        assert result is not None
        assert result["nutrient_id"] == 1003

    def test_case_insensitive(self):
        """Test that search is case-insensitive."""
        result = get_nutrient_by_name("crude protein")
        assert result is not None
        assert result["nutrient_id"] == 1003

    def test_returns_none_for_unknown_name(self):
        """Test returns None for unknown name."""
        result = get_nutrient_by_name("Unknown Nutrient XYZ")
        assert result is None


class TestGetTaurineNutrient:
    """Tests for get_taurine_nutrient function."""

    def test_returns_taurine(self):
        """Test get_taurine_nutrient returns Taurine."""
        result = get_taurine_nutrient()
        assert result is not None
        assert result["nutrient_name"] == "Taurine"

    def test_taurine_has_custom_id(self):
        """Test Taurine has custom nutrient ID 9001."""
        result = get_taurine_nutrient()
        assert result["nutrient_id"] == TAURINE_NUTRIENT_ID
        assert result["nutrient_id"] == 9001

    def test_taurine_unit_is_mg(self):
        """Test Taurine unit is mg."""
        result = get_taurine_nutrient()
        assert result["unit"] == "mg"


class TestGetNutrientsByCategory:
    """Tests for get_nutrients_by_category function."""

    def test_protein_category(self):
        """Test getting Protein category."""
        result = get_nutrients_by_category("Protein")
        assert len(result) >= 1
        assert all(n["category"] == "Protein" for n in result)

    def test_mineral_category(self):
        """Test getting Mineral category."""
        result = get_nutrients_by_category("Mineral")
        assert len(result) == 12
        names = [n["nutrient_name"] for n in result]
        assert "Calcium" in names
        assert "Iron" in names

    def test_case_insensitive(self):
        """Test category search is case-insensitive."""
        result1 = get_nutrients_by_category("vitamin")
        result2 = get_nutrients_by_category("VITAMIN")
        assert len(result1) == len(result2)

    def test_empty_for_invalid_category(self):
        """Test returns empty list for invalid category."""
        result = get_nutrients_by_category("Invalid Category")
        assert result == []
