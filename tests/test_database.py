"""
Tests for database.py

Tests PostgreSQL database operations and pure computation functions.
"""
import sys
from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    initialize_database,
    food_exists,
    food_exists_by_name,
    add_ingredient,
    add_food_nutrients,
    get_food_by_id,
    get_ingredient,
    get_all_food_ids,
    delete_food,
    update_nutrient,
    validate_nutrient_completeness,
    create_nutrient_record,
    calculate_statistics,
)


@pytest.fixture
def mock_db():
    """Create a mock database connection for testing."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("database.get_db") as mock_get_db:
        mock_db_instance = MagicMock()
        mock_db_instance.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_db_instance.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_db.return_value = mock_db_instance
        yield mock_cursor


class TestInitializeDatabase:
    """Tests for initialize_database function."""

    def test_verifies_tables_exist(self, mock_db):
        """Test initialize_database verifies table access."""
        initialize_database()
        assert mock_db.execute.call_count == 2


class TestFoodExists:
    """Tests for food_exists function."""

    def test_returns_true_when_found(self, mock_db):
        """Test food_exists returns True when food_id exists."""
        mock_db.fetchone.return_value = {"food_id": 1001}
        assert food_exists(1001) is True

    def test_returns_false_when_not_found(self, mock_db):
        """Test food_exists returns False when food_id not found."""
        mock_db.fetchone.return_value = None
        assert food_exists(9999) is False


class TestFoodExistsByName:
    """Tests for food_exists_by_name function."""

    def test_returns_food_id_when_found(self, mock_db):
        """Test returns food_id for existing food name."""
        mock_db.fetchone.return_value = {"food_id": 1001}
        result = food_exists_by_name("Chicken thigh")
        assert result == 1001

    def test_returns_none_when_not_found(self, mock_db):
        """Test returns None for nonexistent food name."""
        mock_db.fetchone.return_value = None
        result = food_exists_by_name("Unknown food")
        assert result is None


class TestAddIngredient:
    """Tests for add_ingredient function."""

    def test_returns_food_id(self, mock_db):
        """Test add_ingredient returns auto-generated food_id."""
        mock_db.fetchone.return_value = {"food_id": 10001}
        result = add_ingredient(
            "Chicken thigh", category="Muscle Meat", base_unit="g",
            portion_qty=100.0, grams_per_unit=1.0, sr_legacy_fdc_id=171116,
        )
        assert result == 10001

    def test_raises_on_failure(self, mock_db):
        """Test add_ingredient raises RuntimeError on failure."""
        mock_db.fetchone.return_value = None
        with pytest.raises(RuntimeError):
            add_ingredient(
                "Chicken thigh", category="Muscle Meat", base_unit="g",
                portion_qty=100.0, grams_per_unit=1.0,
            )

    def test_rejects_invalid_base_unit(self, mock_db):
        """Test add_ingredient rejects invalid base_unit."""
        with pytest.raises(ValueError, match="Invalid base_unit"):
            add_ingredient(
                "Chicken thigh", category="Muscle Meat", base_unit="kg",
                portion_qty=100.0, grams_per_unit=1000.0,
            )

    def test_rejects_invalid_category(self, mock_db):
        """Test add_ingredient rejects invalid category."""
        with pytest.raises(ValueError, match="Invalid category"):
            add_ingredient(
                "Chicken thigh", category="Invalid", base_unit="g",
                portion_qty=100.0, grams_per_unit=1.0,
            )


class TestAddFoodNutrients:
    """Tests for add_food_nutrients function."""

    def test_returns_count(self, mock_db):
        """Test add_food_nutrients returns count of inserted rows."""
        records = [
            {"food_id": 1001, "nutrient_id": 1003, "fediaf_nutrient_name": "Protein",
             "unit": "g", "value": 20.0, "source": "sr_legacy"},
            {"food_id": 1001, "nutrient_id": 1004, "fediaf_nutrient_name": "Fat",
             "unit": "g", "value": 10.0, "source": "sr_legacy"},
        ]
        result = add_food_nutrients(records)
        assert result == 2

    def test_returns_zero_for_empty_list(self):
        """Test add_food_nutrients returns 0 for empty list."""
        result = add_food_nutrients([])
        assert result == 0


class TestGetFoodById:
    """Tests for get_food_by_id function."""

    def test_returns_nutrient_rows(self, mock_db):
        """Test get_food_by_id returns nutrient rows as dicts."""
        mock_db.fetchall.return_value = [
            {"food_id": 1001, "nutrient_id": 1003, "value": 20.0},
            {"food_id": 1001, "nutrient_id": 1004, "value": 10.0},
        ]
        result = get_food_by_id(1001)
        assert len(result) == 2
        assert result[0]["nutrient_id"] == 1003


class TestGetIngredient:
    """Tests for get_ingredient function."""

    def test_returns_ingredient_dict(self, mock_db):
        """Test get_ingredient returns ingredient details."""
        mock_db.fetchone.return_value = {"food_id": 1001, "food_name": "Chicken"}
        result = get_ingredient(1001)
        assert result["food_name"] == "Chicken"

    def test_returns_none_when_not_found(self, mock_db):
        """Test get_ingredient returns None for unknown food_id."""
        mock_db.fetchone.return_value = None
        result = get_ingredient(9999)
        assert result is None


class TestGetAllFoodIds:
    """Tests for get_all_food_ids function."""

    def test_returns_sorted_ids(self, mock_db):
        """Test get_all_food_ids returns sorted list of IDs."""
        mock_db.fetchall.return_value = [
            {"food_id": 1001},
            {"food_id": 1002},
            {"food_id": 1003},
        ]
        result = get_all_food_ids()
        assert result == [1001, 1002, 1003]

    def test_returns_empty_for_no_data(self, mock_db):
        """Test get_all_food_ids returns empty list when no data."""
        mock_db.fetchall.return_value = []
        result = get_all_food_ids()
        assert result == []


class TestDeleteFood:
    """Tests for delete_food function."""

    def test_returns_nutrient_count(self, mock_db):
        """Test delete_food returns count of deleted nutrient rows."""
        mock_db.rowcount = 5
        result = delete_food(1001)
        assert result == 5


class TestUpdateNutrient:
    """Tests for update_nutrient function."""

    def test_returns_false_for_empty_updates(self):
        """Test update_nutrient returns False for empty updates."""
        result = update_nutrient(1001, 1003, {})
        assert result is False

    def test_handles_comment_append(self, mock_db):
        """Test update_nutrient appends to comment field."""
        mock_db.rowcount = 1
        result = update_nutrient(1001, 1003, {"comment": "New note"})
        assert result is True
        # Verify SQL was executed for comment update
        assert mock_db.execute.called

    def test_handles_field_updates(self, mock_db):
        """Test update_nutrient updates fields."""
        mock_db.rowcount = 1
        result = update_nutrient(1001, 1003, {"value": 25.0})
        assert result is True


class TestValidateNutrientCompleteness:
    """Tests for validate_nutrient_completeness function."""

    def test_returns_true_when_complete(self, mock_db):
        """Test returns True when count matches expected."""
        mock_db.fetchone.return_value = {"cnt": 50}
        assert validate_nutrient_completeness(1001) is True

    def test_returns_false_when_incomplete(self, mock_db):
        """Test returns False when count doesn't match expected."""
        mock_db.fetchone.return_value = {"cnt": 45}
        assert validate_nutrient_completeness(1001) is False


class TestCreateNutrientRecord:
    """Tests for create_nutrient_record function."""

    def test_creates_valid_record(self):
        """Test create_nutrient_record creates valid record with native types."""
        record = create_nutrient_record(
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
        assert record["nutrient_id"] == 1003
        assert record["fediaf_nutrient_name"] == "Crude Protein"
        assert record["usda_nutrient_name"] == "Protein"
        assert record["value"] == 20.5
        assert record["last_updated"] == str(date.today())

    def test_handles_none_nutrient_id(self):
        """Test create_nutrient_record handles None nutrient_id."""
        record = create_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=None,
            fediaf_nutrient_name="Taurine",
            usda_nutrient_name=None,
            unit="mg",
            value=170.0,
            source="literature"
        )

        assert record["nutrient_id"] is None
        assert record["usda_nutrient_name"] is None

    def test_handles_none_value(self):
        """Test create_nutrient_record handles None value."""
        record = create_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=None,
            source="sr_legacy"
        )

        assert record["value"] is None

    def test_includes_usda_metadata(self):
        """Test create_nutrient_record includes USDA metadata fields."""
        record = create_nutrient_record(
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

    def test_calculates_confidence_interval(self):
        """Test create_nutrient_record calculates confidence interval from range."""
        record = create_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.0,
            source="sr_legacy",
            min_value=16.0,
            max_value=24.0,
            num_samples=50
        )

        assert record["confidence_interval_lower"] is not None
        assert record["confidence_interval_upper"] is not None
        assert record["confidence_interval_lower"] < 20.0
        assert record["confidence_interval_upper"] > 20.0

    def test_calculates_coefficient_of_variation(self):
        """Test create_nutrient_record calculates coefficient of variation."""
        record = create_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.0,
            source="sr_legacy",
            min_value=16.0,
            max_value=24.0,
            num_samples=16
        )

        assert record["coefficient_of_variation"] is not None
        assert record["coefficient_of_variation"] > 0

    def test_calculates_range_uncertainty(self):
        """Test create_nutrient_record calculates range-based uncertainty."""
        record = create_nutrient_record(
            food_name="Test Food",
            food_id=1001,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.0,
            source="sr_legacy",
            min_value=18.0,
            max_value=22.0
        )

        # Range uncertainty = (max - min) / (2 * value) * 100 = 4 / 40 * 100 = 10.0
        assert record["range_uncertainty"] == 10.0


class TestCalculateStatistics:
    """Tests for calculate_statistics function."""

    def test_returns_none_for_none_value(self):
        """Test returns None values when value is None."""
        result = calculate_statistics(None, 1.0, 10, 18.0, 22.0)

        assert result["confidence_interval_lower"] is None
        assert result["confidence_interval_upper"] is None
        assert result["coefficient_of_variation"] is None
        assert result["range_uncertainty"] is None

    def test_handles_zero_value(self):
        """Test zero value calculates CI but skips CV and range_uncertainty."""
        result = calculate_statistics(0, 1.0, 10, 18.0, 22.0)

        # CI should be calculated (0 +/- 2.0 * 1.0)
        assert result["confidence_interval_lower"] == -2.0
        assert result["confidence_interval_upper"] == 2.0
        # CV and range_uncertainty skip division by zero
        assert result["coefficient_of_variation"] is None
        assert result["range_uncertainty"] is None

    def test_calculates_ci_with_large_samples(self):
        """Test calculates 95% CI with t=1.96 for large samples."""
        result = calculate_statistics(20.0, 1.0, 50, None, None)

        # CI = 20 +/- 1.96 * 1.0
        assert abs(result["confidence_interval_lower"] - 18.04) < 0.01
        assert abs(result["confidence_interval_upper"] - 21.96) < 0.01

    def test_calculates_ci_with_small_samples(self):
        """Test calculates 95% CI with t=2.0 for small samples."""
        result = calculate_statistics(20.0, 1.0, 10, None, None)

        # CI = 20 +/- 2.0 * 1.0
        assert result["confidence_interval_lower"] == 18.0
        assert result["confidence_interval_upper"] == 22.0

    def test_calculates_cv(self):
        """Test calculates coefficient of variation."""
        result = calculate_statistics(20.0, 2.0, 10, None, None)

        # CV = 2.0 / 20.0 * 100 = 10.0
        assert result["coefficient_of_variation"] == 10.0

    def test_calculates_range_uncertainty(self):
        """Test calculates range-based uncertainty."""
        result = calculate_statistics(20.0, None, None, 16.0, 24.0)

        # Range uncertainty = (24 - 16) / (2 * 20) * 100 = 8 / 40 * 100 = 20.0
        assert result["range_uncertainty"] == 20.0

    def test_estimates_se_from_range_when_not_provided(self):
        """Test SE is estimated from range when standard_error is not provided."""
        # value=20, range=24-16=8, estimated_sd=8/4=2, estimated_se=2/sqrt(10)=0.632
        result = calculate_statistics(20.0, None, 10, 16.0, 24.0)

        # Should have estimated SE
        assert result["estimated_se"] is not None
        assert result["estimated_se"] == pytest.approx(0.6325, rel=0.01)
        # CI should be calculated from estimated SE
        assert result["confidence_interval_lower"] is not None
        assert result["confidence_interval_upper"] is not None
        # CV should also be calculated
        assert result["coefficient_of_variation"] is not None
        # Range uncertainty should still be calculated
        assert result["range_uncertainty"] is not None

    def test_no_estimation_without_samples(self):
        """Test SE not estimated without num_samples."""
        result = calculate_statistics(20.0, None, None, 16.0, 24.0)

        # Without num_samples, can't estimate SE
        assert result["estimated_se"] is None
        assert result["confidence_interval_lower"] is None
        assert result["confidence_interval_upper"] is None
        # But range uncertainty should still work
        assert result["range_uncertainty"] is not None

    def test_no_range_uncertainty_when_max_equals_min(self):
        """Test range uncertainty not calculated when max equals min."""
        result = calculate_statistics(20.0, None, None, 20.0, 20.0)

        assert result["range_uncertainty"] is None
