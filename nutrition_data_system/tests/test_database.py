"""
Tests for database.py
"""
import sys
import os
import tempfile
from pathlib import Path
from datetime import date

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    SCHEMA_HEADERS,
    initialize_database,
    load_database,
    save_database,
    add_food_nutrients,
    get_food_by_id,
    update_nutrient,
    food_exists,
    get_all_food_ids,
    delete_food,
    create_nutrient_record,
    calculate_statistics,
)


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_records():
    """Create sample nutrient records for testing."""
    return [
        {
            "food_id": "FOOD_001",
            "food_name": "Test Food",
            "sr_legacy_fdc_id": "171116",
            "foundation_fdc_id": "746784",
            "nutrient_id": "1003",
            "fediaf_nutrient_name": "Crude Protein",
            "usda_nutrient_name": "Protein",
            "unit": "g",
            "value": "20.5",
            "source": "sr_legacy",
            "num_samples": "10",
            "min_value": "18.5",
            "max_value": "22.5",
            "median_value": "20.3",
            "year_acquired": "2019",
            "derivation_description": "Analytical",
            "estimated_se": "",
            "confidence_interval_lower": "19.5",
            "confidence_interval_upper": "21.5",
            "coefficient_of_variation": "2.44",
            "range_uncertainty": "9.76",
            "last_updated": str(date.today()),
            "comment": ""
        },
        {
            "food_id": "FOOD_001",
            "food_name": "Test Food",
            "sr_legacy_fdc_id": "171116",
            "foundation_fdc_id": "746784",
            "nutrient_id": "1004",
            "fediaf_nutrient_name": "Total Fat",
            "usda_nutrient_name": "Total lipid (fat)",
            "unit": "g",
            "value": "10.0",
            "source": "sr_legacy",
            "num_samples": "",
            "min_value": "",
            "max_value": "",
            "median_value": "",
            "year_acquired": "",
            "derivation_description": "",
            "estimated_se": "",
            "confidence_interval_lower": "",
            "confidence_interval_upper": "",
            "coefficient_of_variation": "",
            "range_uncertainty": "",
            "last_updated": str(date.today()),
            "comment": ""
        },
    ]


class TestInitializeDatabase:
    """Tests for initialize_database function."""

    def test_creates_file_with_headers(self, temp_db):
        """Test initialize_database creates file with correct headers."""
        # Remove the temp file first
        os.remove(temp_db)

        initialize_database(temp_db)

        assert os.path.exists(temp_db)
        with open(temp_db, 'r') as f:
            first_line = f.readline().strip()
        assert first_line == ','.join(SCHEMA_HEADERS)

    def test_does_not_overwrite_existing(self, temp_db, sample_records):
        """Test initialize_database doesn't overwrite existing file."""
        # Create a file with data
        save_database(sample_records, temp_db)

        # Try to initialize
        initialize_database(temp_db)

        # Data should still be there
        data = load_database(temp_db)
        assert len(data) == 2

    def test_creates_parent_directories(self, temp_db):
        """Test initialize_database creates parent directories if needed."""
        nested_path = temp_db + "_nested/subdir/db.csv"
        try:
            initialize_database(nested_path)
            assert os.path.exists(nested_path)
        finally:
            # Cleanup
            if os.path.exists(nested_path):
                os.remove(nested_path)
                os.rmdir(os.path.dirname(nested_path))
                os.rmdir(os.path.dirname(os.path.dirname(nested_path)))


class TestLoadDatabase:
    """Tests for load_database function."""

    def test_returns_empty_list_for_empty_file(self, temp_db):
        """Test load_database returns empty list for empty file."""
        initialize_database(temp_db)
        result = load_database(temp_db)
        assert result == []

    def test_returns_empty_list_for_nonexistent_file(self, temp_db):
        """Test load_database returns empty list for nonexistent file."""
        os.remove(temp_db)
        result = load_database(temp_db)
        assert result == []

    def test_loads_saved_data(self, temp_db, sample_records):
        """Test load_database loads previously saved data."""
        save_database(sample_records, temp_db)
        result = load_database(temp_db)
        assert len(result) == 2
        assert result[0]["food_id"] == "FOOD_001"


class TestSaveDatabase:
    """Tests for save_database function."""

    def test_save_and_load_roundtrip(self, temp_db, sample_records):
        """Test save_database and load_database round-trip."""
        save_database(sample_records, temp_db)
        loaded = load_database(temp_db)

        assert len(loaded) == len(sample_records)
        for i, record in enumerate(loaded):
            for key in SCHEMA_HEADERS:
                assert record.get(key) == sample_records[i].get(key, "")

    def test_overwrites_existing_data(self, temp_db, sample_records):
        """Test save_database overwrites existing data."""
        save_database(sample_records, temp_db)
        save_database([sample_records[0]], temp_db)

        loaded = load_database(temp_db)
        assert len(loaded) == 1


class TestAddFoodNutrients:
    """Tests for add_food_nutrients function."""

    def test_adds_new_rows(self, temp_db, sample_records):
        """Test add_food_nutrients adds new rows."""
        initialize_database(temp_db)
        added = add_food_nutrients(sample_records, temp_db)

        assert added == 2
        loaded = load_database(temp_db)
        assert len(loaded) == 2

    def test_rejects_duplicates(self, temp_db, sample_records):
        """Test add_food_nutrients rejects duplicates."""
        initialize_database(temp_db)
        add_food_nutrients(sample_records, temp_db)

        # Try to add same records again
        added = add_food_nutrients(sample_records, temp_db)

        assert added == 0
        loaded = load_database(temp_db)
        assert len(loaded) == 2

    def test_adds_only_non_duplicate_rows(self, temp_db, sample_records):
        """Test add_food_nutrients adds only non-duplicate rows."""
        initialize_database(temp_db)
        add_food_nutrients([sample_records[0]], temp_db)

        # Add both records (one is duplicate)
        added = add_food_nutrients(sample_records, temp_db)

        assert added == 1  # Only second record should be added
        loaded = load_database(temp_db)
        assert len(loaded) == 2


class TestGetFoodById:
    """Tests for get_food_by_id function."""

    def test_returns_correct_rows(self, temp_db, sample_records):
        """Test get_food_by_id returns correct rows."""
        save_database(sample_records, temp_db)

        result = get_food_by_id("FOOD_001", temp_db)

        assert len(result) == 2
        assert all(r["food_id"] == "FOOD_001" for r in result)

    def test_returns_empty_list_for_unknown_food(self, temp_db, sample_records):
        """Test get_food_by_id returns empty list for unknown food."""
        save_database(sample_records, temp_db)

        result = get_food_by_id("UNKNOWN", temp_db)

        assert result == []

    def test_filters_multiple_foods(self, temp_db, sample_records):
        """Test get_food_by_id correctly filters among multiple foods."""
        # Add another food
        extra = sample_records[0].copy()
        extra["food_id"] = "FOOD_002"
        all_records = sample_records + [extra]
        save_database(all_records, temp_db)

        result = get_food_by_id("FOOD_001", temp_db)

        assert len(result) == 2
        assert all(r["food_id"] == "FOOD_001" for r in result)


class TestUpdateNutrient:
    """Tests for update_nutrient function."""

    def test_modifies_correct_row(self, temp_db, sample_records):
        """Test update_nutrient modifies correct row."""
        save_database(sample_records, temp_db)

        success = update_nutrient("FOOD_001", 1003, {"value": "25.0"}, temp_db)

        assert success
        loaded = load_database(temp_db)
        protein_row = next(r for r in loaded if r["nutrient_id"] == "1003")
        assert protein_row["value"] == "25.0"

    def test_appends_to_comment(self, temp_db, sample_records):
        """Test update_nutrient appends to comment."""
        sample_records[0]["comment"] = "Initial comment"
        save_database(sample_records, temp_db)

        update_nutrient("FOOD_001", 1003, {"comment": "New comment"}, temp_db)

        loaded = load_database(temp_db)
        protein_row = next(r for r in loaded if r["nutrient_id"] == "1003")
        assert "Initial comment" in protein_row["comment"]
        assert "New comment" in protein_row["comment"]

    def test_returns_false_for_not_found(self, temp_db, sample_records):
        """Test update_nutrient returns False for unknown record."""
        save_database(sample_records, temp_db)

        success = update_nutrient("UNKNOWN", 9999, {"value": "1.0"}, temp_db)

        assert not success

    def test_updates_last_updated(self, temp_db, sample_records):
        """Test update_nutrient updates last_updated field."""
        sample_records[0]["last_updated"] = "2020-01-01"
        save_database(sample_records, temp_db)

        update_nutrient("FOOD_001", 1003, {"value": "25.0"}, temp_db)

        loaded = load_database(temp_db)
        protein_row = next(r for r in loaded if r["nutrient_id"] == "1003")
        assert protein_row["last_updated"] == str(date.today())


class TestFoodExists:
    """Tests for food_exists function."""

    def test_returns_true_for_existing_food(self, temp_db, sample_records):
        """Test food_exists returns True for existing food."""
        save_database(sample_records, temp_db)

        assert food_exists("FOOD_001", temp_db)

    def test_returns_false_for_nonexistent_food(self, temp_db, sample_records):
        """Test food_exists returns False for nonexistent food."""
        save_database(sample_records, temp_db)

        assert not food_exists("UNKNOWN", temp_db)

    def test_returns_false_for_empty_database(self, temp_db):
        """Test food_exists returns False for empty database."""
        initialize_database(temp_db)

        assert not food_exists("ANY", temp_db)


class TestGetAllFoodIds:
    """Tests for get_all_food_ids function."""

    def test_returns_unique_ids(self, temp_db, sample_records):
        """Test get_all_food_ids returns unique IDs."""
        save_database(sample_records, temp_db)

        result = get_all_food_ids(temp_db)

        assert result == ["FOOD_001"]

    def test_returns_sorted_ids(self, temp_db, sample_records):
        """Test get_all_food_ids returns sorted IDs."""
        extra = sample_records[0].copy()
        extra["food_id"] = "FOOD_002"
        extra2 = sample_records[0].copy()
        extra2["food_id"] = "AAA_FOOD"
        all_records = sample_records + [extra, extra2]
        save_database(all_records, temp_db)

        result = get_all_food_ids(temp_db)

        assert result == ["AAA_FOOD", "FOOD_001", "FOOD_002"]

    def test_returns_empty_for_empty_database(self, temp_db):
        """Test get_all_food_ids returns empty list for empty database."""
        initialize_database(temp_db)

        result = get_all_food_ids(temp_db)

        assert result == []


class TestDeleteFood:
    """Tests for delete_food function."""

    def test_deletes_all_records_for_food(self, temp_db, sample_records):
        """Test delete_food removes all records for a food."""
        save_database(sample_records, temp_db)

        deleted = delete_food("FOOD_001", temp_db)

        assert deleted == 2
        loaded = load_database(temp_db)
        assert len(loaded) == 0

    def test_returns_zero_for_nonexistent_food(self, temp_db, sample_records):
        """Test delete_food returns 0 for nonexistent food."""
        save_database(sample_records, temp_db)

        deleted = delete_food("UNKNOWN", temp_db)

        assert deleted == 0


class TestCreateNutrientRecord:
    """Tests for create_nutrient_record function."""

    def test_creates_valid_record(self):
        """Test create_nutrient_record creates valid record."""
        record = create_nutrient_record(
            food_id="TEST_001",
            food_name="Test Food",
            sr_legacy_fdc_id=171116,
            foundation_fdc_id=746784,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.5,
            source="sr_legacy",
            comment="Test comment"
        )

        assert record["food_id"] == "TEST_001"
        assert record["nutrient_id"] == "1003"
        assert record["fediaf_nutrient_name"] == "Crude Protein"
        assert record["usda_nutrient_name"] == "Protein"
        assert record["value"] == "20.5"
        assert record["last_updated"] == str(date.today())

    def test_handles_none_foundation_id(self):
        """Test create_nutrient_record handles None foundation_fdc_id."""
        record = create_nutrient_record(
            food_id="TEST_001",
            food_name="Test Food",
            sr_legacy_fdc_id=171116,
            foundation_fdc_id=None,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=20.5,
            source="sr_legacy"
        )

        assert record["foundation_fdc_id"] == ""

    def test_handles_none_nutrient_id(self):
        """Test create_nutrient_record handles None nutrient_id."""
        record = create_nutrient_record(
            food_id="TEST_001",
            food_name="Test Food",
            sr_legacy_fdc_id=171116,
            foundation_fdc_id=None,
            nutrient_id=None,
            fediaf_nutrient_name="Taurine",
            usda_nutrient_name=None,
            unit="mg",
            value=170.0,
            source="literature"
        )

        assert record["nutrient_id"] == ""
        assert record["usda_nutrient_name"] == ""

    def test_handles_none_value(self):
        """Test create_nutrient_record handles None value."""
        record = create_nutrient_record(
            food_id="TEST_001",
            food_name="Test Food",
            sr_legacy_fdc_id=171116,
            foundation_fdc_id=None,
            nutrient_id=1003,
            fediaf_nutrient_name="Crude Protein",
            usda_nutrient_name="Protein",
            unit="g",
            value=None,
            source="sr_legacy"
        )

        assert record["value"] == ""

    def test_includes_usda_metadata(self):
        """Test create_nutrient_record includes USDA metadata fields."""
        record = create_nutrient_record(
            food_id="TEST_001",
            food_name="Test Food",
            sr_legacy_fdc_id=171116,
            foundation_fdc_id=746784,
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

        assert record["num_samples"] == "10"
        assert record["min_value"] == "18.5"
        assert record["max_value"] == "22.5"
        assert record["median_value"] == "20.3"
        assert record["year_acquired"] == "2019"
        assert record["derivation_description"] == "Analytical"
        # SE is now estimated from range since USDA API doesn't provide it
        assert record["estimated_se"] != ""

    def test_calculates_confidence_interval(self):
        """Test create_nutrient_record calculates confidence interval from range."""
        record = create_nutrient_record(
            food_id="TEST_001",
            food_name="Test Food",
            sr_legacy_fdc_id=171116,
            foundation_fdc_id=None,
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

        # CI is estimated from range when SE not provided
        assert record["confidence_interval_lower"] != ""
        assert record["confidence_interval_upper"] != ""
        assert float(record["confidence_interval_lower"]) < 20.0
        assert float(record["confidence_interval_upper"]) > 20.0

    def test_calculates_coefficient_of_variation(self):
        """Test create_nutrient_record calculates coefficient of variation from estimated SE."""
        record = create_nutrient_record(
            food_id="TEST_001",
            food_name="Test Food",
            sr_legacy_fdc_id=171116,
            foundation_fdc_id=None,
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

        # CV is calculated from estimated SE
        assert record["coefficient_of_variation"] != ""
        assert float(record["coefficient_of_variation"]) > 0

    def test_calculates_range_uncertainty(self):
        """Test create_nutrient_record calculates range-based uncertainty."""
        record = create_nutrient_record(
            food_id="TEST_001",
            food_name="Test Food",
            sr_legacy_fdc_id=171116,
            foundation_fdc_id=None,
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
        assert record["range_uncertainty"] == "10.0"


class TestCalculateStatistics:
    """Tests for calculate_statistics function."""

    def test_returns_none_for_none_value(self):
        """Test returns None values when value is None."""
        result = calculate_statistics(None, 1.0, 10, 18.0, 22.0)

        assert result["confidence_interval_lower"] is None
        assert result["confidence_interval_upper"] is None
        assert result["coefficient_of_variation"] is None
        assert result["range_uncertainty"] is None

    def test_returns_none_for_zero_value(self):
        """Test returns None values when value is zero."""
        result = calculate_statistics(0, 1.0, 10, 18.0, 22.0)

        assert result["confidence_interval_lower"] is None
        assert result["confidence_interval_upper"] is None

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
