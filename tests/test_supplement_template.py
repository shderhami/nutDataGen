"""
Tests for supplement_template.py

Tests CSV template generation, reading, validation, and supplement processing.
"""
import csv
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supplement_template import (
    generate_template,
    read_template,
    get_nonzero_nutrients,
    display_supplement_summary,
    TEMPLATES_DIR,
)


@pytest.fixture
def tmp_template(tmp_path):
    """Create a filled template CSV in a temp directory for testing."""
    def _make(supplement_name="Test Supplement", values=None):
        from fediaf_nutrients import get_all_nutrients
        nutrients = get_all_nutrients()

        file_path = tmp_path / "test_supplement.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["nutrient_id", "fediaf_nutrient_name", "unit", supplement_name])
            for nutrient in nutrients:
                nid = nutrient["nutrient_id"]
                val = ""
                if values and nid in values:
                    val = values[nid]
                writer.writerow([
                    nid,
                    nutrient["nutrient_name"],
                    nutrient["unit"],
                    val,
                ])
        return file_path
    return _make


class TestGenerateTemplate:
    """Tests for generate_template function."""

    def test_creates_file(self, tmp_path):
        """Test template file is created."""
        with patch("supplement_template.TEMPLATES_DIR", tmp_path):
            path = generate_template("Taurine Powder")
            assert path.exists()

    def test_filename_format(self, tmp_path):
        """Test filename is lowercased with underscores."""
        with patch("supplement_template.TEMPLATES_DIR", tmp_path):
            path = generate_template("Taurine Powder")
            assert path.name == "taurine_powder.csv"

    def test_header_contains_supplement_name(self, tmp_path):
        """Test CSV header has supplement name as 4th column."""
        with patch("supplement_template.TEMPLATES_DIR", tmp_path):
            path = generate_template("Taurine Powder")
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                assert header == ["nutrient_id", "fediaf_nutrient_name", "unit", "Taurine Powder"]

    def test_has_52_nutrient_rows(self, tmp_path):
        """Test template has 52 nutrient rows."""
        with patch("supplement_template.TEMPLATES_DIR", tmp_path):
            path = generate_template("Test Supplement")
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                rows = list(reader)
                assert len(rows) == 52

    def test_value_column_empty(self, tmp_path):
        """Test value column is empty in template."""
        with patch("supplement_template.TEMPLATES_DIR", tmp_path):
            path = generate_template("Test Supplement")
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                for row in reader:
                    assert row[3] == "", f"Value should be empty but got '{row[3]}'"

    def test_creates_templates_dir(self, tmp_path):
        """Test creates templates directory if it doesn't exist."""
        new_dir = tmp_path / "new_templates"
        with patch("supplement_template.TEMPLATES_DIR", new_dir):
            generate_template("Test")
            assert new_dir.exists()


class TestReadTemplate:
    """Tests for read_template function."""

    def test_reads_filled_template(self, tmp_template):
        """Test reading a template with some filled values."""
        path = tmp_template(
            supplement_name="Taurine Powder",
            values={1234: 1000, 1003: 0.5}  # Taurine=1000mg, Protein=0.5g
        )
        result = read_template(path)

        assert result["supplement_name"] == "Taurine Powder"
        assert len(result["nutrients"]) == 52

        # Check taurine value
        taurine = next(n for n in result["nutrients"] if n["nutrient_id"] == 1234)
        assert taurine["value"] == 1000.0

        # Check protein value
        protein = next(n for n in result["nutrients"] if n["nutrient_id"] == 1003)
        assert protein["value"] == 0.5

    def test_empty_values_are_none(self, tmp_template):
        """Test empty value cells are parsed as None."""
        path = tmp_template(values={1234: 500})  # Only taurine filled
        result = read_template(path)

        # Non-filled nutrients should be None
        protein = next(n for n in result["nutrients"] if n["nutrient_id"] == 1003)
        assert protein["value"] is None

    def test_file_not_found(self):
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            read_template("/nonexistent/path/template.csv")

    def test_invalid_nutrient_id(self, tmp_path):
        """Test ValueError for invalid nutrient ID."""
        file_path = tmp_path / "bad.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nutrient_id", "fediaf_nutrient_name", "unit", "Test"])
            writer.writerow(["abc", "Protein", "g", "10"])
        with pytest.raises(ValueError, match="invalid nutrient_id"):
            read_template(file_path)

    def test_unknown_nutrient_id(self, tmp_path):
        """Test ValueError for nutrient ID not in FEDIAF list."""
        file_path = tmp_path / "bad.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nutrient_id", "fediaf_nutrient_name", "unit", "Test"])
            writer.writerow(["99999", "Unknown Nutrient", "g", "10"])
        with pytest.raises(ValueError, match="not in the FEDIAF"):
            read_template(file_path)

    def test_invalid_value(self, tmp_template, tmp_path):
        """Test ValueError for non-numeric value."""
        file_path = tmp_path / "bad_value.csv"
        from fediaf_nutrients import get_all_nutrients
        nutrients = get_all_nutrients()

        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nutrient_id", "fediaf_nutrient_name", "unit", "Test"])
            for n in nutrients:
                val = "abc" if n["nutrient_id"] == 1003 else ""
                writer.writerow([n["nutrient_id"], n["nutrient_name"], n["unit"], val])

        with pytest.raises(ValueError, match="invalid value"):
            read_template(file_path)

    def test_missing_nutrients(self, tmp_path):
        """Test ValueError when template has fewer than 52 nutrients."""
        file_path = tmp_path / "incomplete.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nutrient_id", "fediaf_nutrient_name", "unit", "Test"])
            writer.writerow(["1003", "Crude Protein", "g", "10"])
        with pytest.raises(ValueError, match="missing"):
            read_template(file_path)

    def test_too_few_columns(self, tmp_path):
        """Test ValueError when header has fewer than 4 columns."""
        file_path = tmp_path / "short.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nutrient_id", "fediaf_nutrient_name", "unit"])
        with pytest.raises(ValueError, match="expected 4 columns"):
            read_template(file_path)

    def test_empty_supplement_name(self, tmp_path):
        """Test ValueError when supplement name column header is empty."""
        file_path = tmp_path / "noname.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nutrient_id", "fediaf_nutrient_name", "unit", ""])
        with pytest.raises(ValueError, match="Supplement name"):
            read_template(file_path)


class TestGetNonzeroNutrients:
    """Tests for get_nonzero_nutrients function."""

    def test_filters_none_values(self):
        """Test None values are excluded."""
        data = {
            "supplement_name": "Test",
            "nutrients": [
                {"nutrient_id": 1003, "fediaf_nutrient_name": "Protein", "unit": "g", "value": 10.0},
                {"nutrient_id": 1004, "fediaf_nutrient_name": "Fat", "unit": "g", "value": None},
            ]
        }
        result = get_nonzero_nutrients(data)
        assert len(result) == 1
        assert result[0]["nutrient_id"] == 1003

    def test_filters_zero_values(self):
        """Test zero values are excluded."""
        data = {
            "supplement_name": "Test",
            "nutrients": [
                {"nutrient_id": 1003, "fediaf_nutrient_name": "Protein", "unit": "g", "value": 10.0},
                {"nutrient_id": 1004, "fediaf_nutrient_name": "Fat", "unit": "g", "value": 0.0},
            ]
        }
        result = get_nonzero_nutrients(data)
        assert len(result) == 1
        assert result[0]["nutrient_id"] == 1003

    def test_keeps_nonzero_values(self):
        """Test non-zero values are kept."""
        data = {
            "supplement_name": "Test",
            "nutrients": [
                {"nutrient_id": 1234, "fediaf_nutrient_name": "Taurine", "unit": "mg", "value": 1000.0},
                {"nutrient_id": 1087, "fediaf_nutrient_name": "Calcium", "unit": "mg", "value": 500.0},
            ]
        }
        result = get_nonzero_nutrients(data)
        assert len(result) == 2

    def test_empty_nutrients(self):
        """Test empty nutrient list returns empty."""
        data = {"supplement_name": "Test", "nutrients": []}
        result = get_nonzero_nutrients(data)
        assert result == []


class TestDisplaySupplementSummary:
    """Tests for display_supplement_summary function."""

    def test_displays_summary(self, capsys):
        """Test summary output format."""
        data = {
            "supplement_name": "Taurine Powder",
            "nutrients": [
                {"nutrient_id": 1234, "fediaf_nutrient_name": "Taurine", "unit": "mg", "value": 1000.0},
                {"nutrient_id": 1003, "fediaf_nutrient_name": "Protein", "unit": "g", "value": None},
                {"nutrient_id": 1004, "fediaf_nutrient_name": "Fat", "unit": "g", "value": 0.0},
            ]
        }
        display_supplement_summary(data)
        captured = capsys.readouterr()

        assert "Taurine Powder" in captured.out
        assert "Nutrients with values: 1" in captured.out
        assert "Nutrients set to zero: 2" in captured.out
        assert "Taurine" in captured.out
        assert "1000" in captured.out


class TestProcessSupplement:
    """Tests for process_supplement function in main.py."""

    def test_creates_52_records(self, tmp_template):
        """Test supplement processing creates exactly 52 nutrient records."""
        from main import process_supplement

        path = tmp_template(
            supplement_name="Taurine Powder",
            values={1234: 1000}
        )

        with patch("builtins.input", side_effect=[str(path), "y"]):
            with patch("main.create_nutrient_record") as mock_create:
                mock_create.side_effect = lambda **kwargs: kwargs
                records = process_supplement(food_id=10005, food_name="Taurine Powder")

        assert len(records) == 52

    def test_nonzero_source_is_product_label(self, tmp_template):
        """Test non-zero nutrient source is 'product_label'."""
        from main import process_supplement

        path = tmp_template(
            supplement_name="Taurine Powder",
            values={1234: 1000}
        )

        with patch("builtins.input", side_effect=[str(path), "y"]):
            with patch("main.create_nutrient_record") as mock_create:
                mock_create.side_effect = lambda **kwargs: kwargs
                records = process_supplement(food_id=10005, food_name="Taurine Powder")

        taurine = next(r for r in records if r["nutrient_id"] == 1234)
        assert taurine["source"] == "product_label"
        assert taurine["value"] == 1000.0

    def test_empty_source_is_not_in_supplement(self, tmp_template):
        """Test empty nutrient source is 'not_in_supplement' with value 0."""
        from main import process_supplement

        path = tmp_template(
            supplement_name="Taurine Powder",
            values={1234: 1000}
        )

        with patch("builtins.input", side_effect=[str(path), "y"]):
            with patch("main.create_nutrient_record") as mock_create:
                mock_create.side_effect = lambda **kwargs: kwargs
                records = process_supplement(food_id=10005, food_name="Taurine Powder")

        protein = next(r for r in records if r["nutrient_id"] == 1003)
        assert protein["source"] == "not_in_supplement"
        assert protein["value"] == 0.0

    def test_user_cancels(self, tmp_template):
        """Test cancellation returns empty list."""
        from main import process_supplement

        path = tmp_template(values={1234: 1000})

        with patch("builtins.input", side_effect=[str(path), "n"]):
            records = process_supplement(food_id=10005, food_name="Test")

        assert records == []

    def test_empty_path_returns_empty(self):
        """Test empty path returns empty list."""
        from main import process_supplement

        with patch("builtins.input", return_value=""):
            records = process_supplement(food_id=10005, food_name="Test")

        assert records == []

    def test_missing_file_returns_empty(self):
        """Test missing file returns empty list."""
        from main import process_supplement

        with patch("builtins.input", return_value="/nonexistent/file.csv"):
            records = process_supplement(food_id=10005, food_name="Test")

        assert records == []
