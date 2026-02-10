"""
Database Operations for Nutrition Data.

CSV read/write operations for persistent storage of nutrition data.
"""
import csv
from datetime import date
from pathlib import Path
from typing import Optional

from config import DATABASE_FILE

# CSV schema column headers
# Note: standard_error and footnote removed - USDA API does not provide these fields
SCHEMA_HEADERS = [
    "food_id",
    "food_name",
    "portion_size",
    "sr_legacy_fdc_id",
    "foundation_fdc_id",
    "nutrient_id",
    "fediaf_nutrient_name",
    "usda_nutrient_name",
    "unit",
    "value",
    "source",
    # USDA metadata fields (available from API)
    "num_samples",
    "min_value",
    "max_value",
    "median_value",
    "year_acquired",
    "derivation_description",
    # Calculated statistical fields (computed from min/max/num_samples)
    "estimated_se",
    "confidence_interval_lower",
    "confidence_interval_upper",
    "coefficient_of_variation",
    "range_uncertainty",
    # AI validation fields
    "ai_recommendation",
    "ai_justification",
    "ai_source",
    "ai_confidence",
    # Record metadata
    "last_updated",
    "comment"
]


def initialize_database(filepath: Optional[str] = None) -> None:
    """
    Create empty database file with headers if not exists.

    Args:
        filepath: Path to database file (uses config default if not provided)
    """
    path = Path(filepath) if filepath else DATABASE_FILE

    # Create parent directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Only create if file doesn't exist
    if not path.exists():
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=SCHEMA_HEADERS)
            writer.writeheader()


def load_database(filepath: Optional[str] = None) -> list[dict]:
    """
    Load database from CSV file.

    Args:
        filepath: Path to database file (uses config default if not provided)

    Returns:
        List of row dictionaries
    """
    path = Path(filepath) if filepath else DATABASE_FILE

    if not path.exists():
        return []

    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_database(data: list[dict], filepath: Optional[str] = None) -> None:
    """
    Save complete database to CSV file.

    Args:
        data: List of row dictionaries
        filepath: Path to database file (uses config default if not provided)
    """
    path = Path(filepath) if filepath else DATABASE_FILE

    # Create parent directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA_HEADERS)
        writer.writeheader()
        writer.writerows(data)


def add_food_nutrients(food_nutrients: list[dict], filepath: Optional[str] = None) -> int:
    """
    Add new food nutrient rows to database.
    Checks for duplicates (food_id + nutrient_id).

    Args:
        food_nutrients: List of nutrient records to add
        filepath: Path to database file (uses config default if not provided)

    Returns:
        Number of rows added (excludes duplicates)
    """
    path = Path(filepath) if filepath else DATABASE_FILE

    # Load existing data
    existing = load_database(str(path))

    # Build set of existing (food_id, nutrient_id) pairs
    existing_keys = set()
    for row in existing:
        key = (row.get("food_id"), row.get("nutrient_id"))
        existing_keys.add(key)

    # Filter out duplicates
    new_rows = []
    for row in food_nutrients:
        key = (row.get("food_id"), str(row.get("nutrient_id")))
        if key not in existing_keys:
            new_rows.append(row)
            existing_keys.add(key)

    # Append new rows
    if new_rows:
        file_exists = path.exists() and path.stat().st_size > 0
        with open(path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=SCHEMA_HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_rows)

    return len(new_rows)


def get_food_by_id(food_id: str, filepath: Optional[str] = None) -> list[dict]:
    """
    Get all nutrient rows for a specific food.

    Args:
        food_id: The food identifier
        filepath: Path to database file (uses config default if not provided)

    Returns:
        List of nutrient records for the food
    """
    data = load_database(filepath)
    return [row for row in data if row.get("food_id") == food_id]


def update_nutrient(food_id: str, nutrient_id: int,
                    updates: dict, filepath: Optional[str] = None) -> bool:
    """
    Update specific nutrient for a food.
    Appends to comment field rather than replacing.

    Args:
        food_id: The food identifier
        nutrient_id: The nutrient ID to update
        updates: Dictionary of fields to update
        filepath: Path to database file (uses config default if not provided)

    Returns:
        True if update was successful, False if record not found
    """
    data = load_database(filepath)
    nutrient_id_str = str(nutrient_id)
    updated = False

    for row in data:
        if row.get("food_id") == food_id and row.get("nutrient_id") == nutrient_id_str:
            # Handle comment appending
            if "comment" in updates:
                existing_comment = row.get("comment", "") or ""
                new_comment = updates["comment"]
                if existing_comment:
                    row["comment"] = f"{existing_comment}; {new_comment}"
                else:
                    row["comment"] = new_comment
                updates = {k: v for k, v in updates.items() if k != "comment"}

            # Update other fields
            row.update(updates)

            # Update last_updated
            row["last_updated"] = str(date.today())
            updated = True
            break

    if updated:
        save_database(data, filepath)

    return updated


def food_exists(food_id: str, filepath: Optional[str] = None) -> bool:
    """
    Check if food_id already exists in database.

    Args:
        food_id: The food identifier to check
        filepath: Path to database file (uses config default if not provided)

    Returns:
        True if food exists, False otherwise
    """
    data = load_database(filepath)
    return any(row.get("food_id") == food_id for row in data)


def get_all_food_ids(filepath: Optional[str] = None) -> list[str]:
    """
    Get list of all unique food_ids in database.

    Args:
        filepath: Path to database file (uses config default if not provided)

    Returns:
        List of unique food IDs
    """
    data = load_database(filepath)
    food_ids = set()
    for row in data:
        fid = row.get("food_id")
        if fid:
            food_ids.add(fid)
    return sorted(list(food_ids))


def delete_food(food_id: str, filepath: Optional[str] = None) -> int:
    """
    Delete all records for a specific food.

    Args:
        food_id: The food identifier to delete
        filepath: Path to database file (uses config default if not provided)

    Returns:
        Number of rows deleted
    """
    data = load_database(filepath)
    original_count = len(data)
    data = [row for row in data if row.get("food_id") != food_id]
    deleted_count = original_count - len(data)

    if deleted_count > 0:
        save_database(data, filepath)

    return deleted_count


def calculate_statistics(
    value: Optional[float],
    standard_error: Optional[float],
    num_samples: Optional[int],
    min_value: Optional[float],
    max_value: Optional[float]
) -> dict[str, Optional[float]]:
    """
    Calculate statistical measures for error estimation.

    When standard_error is not provided by the API (common for USDA data),
    it is estimated from the range using: SD ≈ Range/4, SE = SD/sqrt(n).

    Args:
        value: The nutrient value (mean)
        standard_error: Standard error from USDA (often None)
        num_samples: Number of samples
        min_value: Minimum value
        max_value: Maximum value

    Returns:
        Dict with confidence_interval_lower, confidence_interval_upper,
        coefficient_of_variation, range_uncertainty, and estimated_se
    """
    import math

    result: dict[str, Optional[float]] = {
        "confidence_interval_lower": None,
        "confidence_interval_upper": None,
        "coefficient_of_variation": None,
        "range_uncertainty": None,
        "estimated_se": None
    }

    if value is None or value == 0:
        return result

    # Use provided standard_error, or estimate from range if available
    se_to_use = standard_error

    if se_to_use is None and min_value is not None and max_value is not None and max_value > min_value:
        # Estimate SD from range: SD ≈ Range / 4 (normal distribution approximation)
        range_val = max_value - min_value
        estimated_sd = range_val / 4.0

        # Estimate SE from SD: SE = SD / sqrt(n)
        if num_samples and num_samples > 1:
            se_to_use = estimated_sd / math.sqrt(num_samples)
            result["estimated_se"] = round(se_to_use, 4)
        elif num_samples == 1:
            # With only 1 sample, use SD directly as uncertainty estimate
            se_to_use = estimated_sd
            result["estimated_se"] = round(se_to_use, 4)

    # Calculate 95% Confidence Interval (using t-distribution approximation)
    # CI = mean +/- t * SE, where t ≈ 1.96 for large samples (95% CI)
    if se_to_use is not None and se_to_use > 0:
        # Use t-value based on sample size if available
        if num_samples and num_samples > 1:
            # For small samples, use approximation: t ≈ 2 for n < 30
            t_value = 2.0 if num_samples < 30 else 1.96
        else:
            t_value = 1.96  # Default for large/unknown samples

        margin = t_value * se_to_use
        result["confidence_interval_lower"] = round(value - margin, 4)
        result["confidence_interval_upper"] = round(value + margin, 4)

        # Calculate Coefficient of Variation (CV = SE / mean * 100)
        # Note: CV is typically calculated from SD, but SE can be used as proxy
        # SE = SD / sqrt(n), so this gives a normalized measure of variability
        cv = (se_to_use / value) * 100
        result["coefficient_of_variation"] = round(cv, 2)

    # Calculate Range-based Uncertainty
    # Range uncertainty = (max - min) / (2 * mean) * 100
    if min_value is not None and max_value is not None:
        if max_value > min_value:
            range_val = max_value - min_value
            range_uncertainty = (range_val / (2 * value)) * 100
            result["range_uncertainty"] = round(range_uncertainty, 2)

    return result


def create_nutrient_record(
    food_id: str,
    food_name: str,
    sr_legacy_fdc_id: Optional[int],
    foundation_fdc_id: Optional[int],
    nutrient_id: Optional[int],
    fediaf_nutrient_name: str,
    usda_nutrient_name: Optional[str],
    unit: str,
    value: Optional[float],
    source: str,
    comment: Optional[str] = None,
    portion_size: str = "100g",
    # USDA metadata fields
    num_samples: Optional[int] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    median_value: Optional[float] = None,
    year_acquired: Optional[str] = None,
    derivation_description: Optional[str] = None,
    # AI validation fields
    ai_recommendation: Optional[str] = None,
    ai_justification: Optional[str] = None,
    ai_source: Optional[str] = None,
    ai_confidence: Optional[str] = None
) -> dict:
    """
    Create a single nutrient record matching the schema.

    Args:
        food_id: Unique identifier for the food
        food_name: Human-readable food name
        sr_legacy_fdc_id: USDA SR Legacy FDC ID
        foundation_fdc_id: USDA Foundation FDC ID (optional)
        nutrient_id: USDA nutrient ID (or custom ID like 9001 for Taurine)
        fediaf_nutrient_name: Nutrient name as defined in FEDIAF guidelines
        usda_nutrient_name: Nutrient name from USDA API response
        unit: Measurement unit
        value: Nutrient value
        source: Data source (sr_legacy, foundation, literature)
        comment: User comments from discrepancy resolution
        portion_size: Portion size for nutrient values (default "100g")
        num_samples: Number of data points/samples from USDA
        min_value: Minimum value from USDA
        max_value: Maximum value from USDA
        median_value: Median value from USDA
        year_acquired: Year data was acquired by USDA
        derivation_description: Full derivation description (Analytical, Calculated, etc.)

    Returns:
        Dictionary matching CSV schema
    """
    # Calculate statistical measures (SE is estimated from range since USDA API doesn't provide it)
    stats = calculate_statistics(
        value=value,
        standard_error=None,  # USDA API doesn't provide standard_error
        num_samples=num_samples,
        min_value=min_value,
        max_value=max_value
    )

    return {
        "food_id": food_id,
        "food_name": food_name,
        "portion_size": portion_size,
        "sr_legacy_fdc_id": str(sr_legacy_fdc_id),
        "foundation_fdc_id": str(foundation_fdc_id) if foundation_fdc_id else "",
        "nutrient_id": str(nutrient_id) if nutrient_id else "",
        "fediaf_nutrient_name": fediaf_nutrient_name,
        "usda_nutrient_name": usda_nutrient_name or "",
        "unit": unit,
        "value": str(value) if value is not None else "",
        "source": source,
        # USDA metadata fields
        "num_samples": str(num_samples) if num_samples is not None else "",
        "min_value": str(min_value) if min_value is not None else "",
        "max_value": str(max_value) if max_value is not None else "",
        "median_value": str(median_value) if median_value is not None else "",
        "year_acquired": year_acquired or "",
        "derivation_description": derivation_description or "",
        # Calculated statistical fields
        "estimated_se": str(stats["estimated_se"]) if stats["estimated_se"] is not None else "",
        "confidence_interval_lower": str(stats["confidence_interval_lower"]) if stats["confidence_interval_lower"] is not None else "",
        "confidence_interval_upper": str(stats["confidence_interval_upper"]) if stats["confidence_interval_upper"] is not None else "",
        "coefficient_of_variation": str(stats["coefficient_of_variation"]) if stats["coefficient_of_variation"] is not None else "",
        "range_uncertainty": str(stats["range_uncertainty"]) if stats["range_uncertainty"] is not None else "",
        # AI validation fields
        "ai_recommendation": ai_recommendation or "",
        "ai_justification": ai_justification or "",
        "ai_source": ai_source or "",
        "ai_confidence": ai_confidence or "",
        # Record metadata
        "last_updated": str(date.today()),
        "comment": comment or ""
    }
