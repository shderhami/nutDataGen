"""
Tests for config.py
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    API_KEY,
    BASE_URL,
    DISCREPANCY_THRESHOLDS,
    DATA_DIR,
    DATABASE_URL,
    FOOD_ID_SEQUENCE_START,
)


def test_api_key_exists():
    """Test that API_KEY is defined (can be empty string if not set)."""
    assert API_KEY is not None
    assert isinstance(API_KEY, str)


def test_base_url_is_valid():
    """Test that BASE_URL is a valid USDA API URL."""
    assert BASE_URL is not None
    assert isinstance(BASE_URL, str)
    assert BASE_URL.startswith("https://")
    assert "usda" in BASE_URL.lower() or "nal.usda.gov" in BASE_URL


def test_discrepancy_thresholds_exist():
    """Test that all required threshold keys exist."""
    required_keys = ["trivial", "moderate", "significant"]
    for key in required_keys:
        assert key in DISCREPANCY_THRESHOLDS, f"Missing threshold key: {key}"


def test_discrepancy_thresholds_are_positive_numbers():
    """Test that all thresholds are positive numbers."""
    for key, value in DISCREPANCY_THRESHOLDS.items():
        assert isinstance(value, (int, float)), f"{key} should be a number"
        assert value > 0, f"{key} should be positive"


def test_discrepancy_thresholds_are_ordered():
    """Test that thresholds increase: trivial < moderate < significant."""
    assert DISCREPANCY_THRESHOLDS["trivial"] < DISCREPANCY_THRESHOLDS["moderate"]
    assert DISCREPANCY_THRESHOLDS["moderate"] < DISCREPANCY_THRESHOLDS["significant"]


def test_data_dir_is_path():
    """Test that DATA_DIR is a valid Path object."""
    assert isinstance(DATA_DIR, Path)


def test_database_url_is_valid():
    """Test that DATABASE_URL is a valid PostgreSQL connection string."""
    assert isinstance(DATABASE_URL, str)
    assert DATABASE_URL.startswith("postgresql://")


def test_food_id_sequence_start():
    """Test that FOOD_ID_SEQUENCE_START is a reasonable starting ID."""
    assert isinstance(FOOD_ID_SEQUENCE_START, int)
    assert FOOD_ID_SEQUENCE_START >= 1000


def test_data_dir_exists():
    """Test that data directory exists (created by config.py)."""
    assert DATA_DIR.exists(), "Data directory should be created on import"
    assert DATA_DIR.is_dir(), "DATA_DIR should be a directory"
