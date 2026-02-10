"""
Comparison Engine for USDA Nutrition Data.

Compares SR Legacy and Foundation Foods data, identifies discrepancies,
and generates comparison reports.
"""
from typing import Optional

from config import DISCREPANCY_THRESHOLDS
from fediaf_nutrients import get_nutrient_by_id


def calculate_discrepancy(sr_value: float, foundation_value: float) -> dict:
    """
    Calculate percentage difference between two values.

    Uses the formula: |a - b| / ((a + b) / 2) * 100
    This gives a symmetric percentage difference.

    Args:
        sr_value: Value from SR Legacy database
        foundation_value: Value from Foundation database

    Returns:
        Dict with sr_value, foundation_value, percentage, and tier
    """
    if sr_value == 0 and foundation_value == 0:
        percentage = 0.0
    elif sr_value == 0 or foundation_value == 0:
        # If one is zero and other isn't, treat as 100% difference
        percentage = 100.0
    else:
        # Symmetric percentage difference
        avg = (sr_value + foundation_value) / 2
        percentage = abs(sr_value - foundation_value) / avg * 100

    return {
        "sr_value": sr_value,
        "foundation_value": foundation_value,
        "percentage": round(percentage, 2),
        "tier": classify_tier(percentage)
    }


def classify_tier(percentage: float) -> str:
    """
    Classify discrepancy into tier based on thresholds.

    Tiers:
        - trivial: < 5% difference
        - moderate: 5-15% difference
        - significant: 15-30% difference
        - major: > 30% difference

    Args:
        percentage: Percentage difference

    Returns:
        Tier string: "trivial", "moderate", "significant", or "major"
    """
    if percentage < DISCREPANCY_THRESHOLDS["trivial"]:
        return "trivial"
    elif percentage < DISCREPANCY_THRESHOLDS["moderate"]:
        return "moderate"
    elif percentage < DISCREPANCY_THRESHOLDS["significant"]:
        return "significant"
    else:
        return "major"


def extract_nutrient_metadata(nutrient: dict) -> dict:
    """
    Extract metadata fields from a nutrient dict.

    Args:
        nutrient: Nutrient dict from API response

    Returns:
        Dict with metadata fields for database storage
        Note: standard_error and footnote removed - USDA API does not provide these
    """
    return {
        "num_samples": nutrient.get("num_samples"),
        "min_value": nutrient.get("min_value"),
        "max_value": nutrient.get("max_value"),
        "median_value": nutrient.get("median_value"),
        "year_acquired": nutrient.get("year_acquired"),
        "derivation_description": nutrient.get("derivation_description")
    }


def compare_nutrients(sr_data: dict, foundation_data: dict) -> dict:
    """
    Compare nutrients from both sources.

    Args:
        sr_data: Dict from fetch_sr_legacy with "nutrients" key
        foundation_data: Dict from fetch_foundation with "nutrients" key

    Returns:
        Dict with categorized nutrients:
        {
            "matches": [...],           # < 5% difference
            "discrepancies": [...],     # >= 5% difference, both have values
            "sr_only": [...],           # Only in SR Legacy
            "foundation_only": [...],   # Only in Foundation
            "missing_both": [...]       # Missing from both sources
        }

        Each entry includes sr_metadata and foundation_metadata for the
        selected source's statistical data.
    """
    sr_nutrients = sr_data.get("nutrients", {})
    foundation_nutrients = foundation_data.get("nutrients", {})

    # Get all nutrient IDs from both sources
    all_ids = set(sr_nutrients.keys()) | set(foundation_nutrients.keys())

    result = {
        "matches": [],
        "discrepancies": [],
        "sr_only": [],
        "foundation_only": [],
        "missing_both": []
    }

    for nid in all_ids:
        sr_nutrient = sr_nutrients.get(nid, {})
        foundation_nutrient = foundation_nutrients.get(nid, {})

        sr_value = sr_nutrient.get("value")
        foundation_value = foundation_nutrient.get("value")

        # Get nutrient info from FEDIAF reference
        nutrient_info = get_nutrient_by_id(nid)
        nutrient_name = sr_nutrient.get("name") or foundation_nutrient.get("name") or \
                        (nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})")
        unit = sr_nutrient.get("unit") or foundation_nutrient.get("unit") or \
               (nutrient_info["unit"] if nutrient_info else "")

        # Extract metadata from both sources
        sr_metadata = extract_nutrient_metadata(sr_nutrient) if sr_nutrient else {}
        foundation_metadata = extract_nutrient_metadata(foundation_nutrient) if foundation_nutrient else {}

        entry = {
            "nutrient_id": nid,
            "nutrient_name": nutrient_name,
            "unit": unit,
            "sr_value": sr_value,
            "foundation_value": foundation_value,
            "sr_metadata": sr_metadata,
            "foundation_metadata": foundation_metadata
        }

        # Categorize based on availability
        if sr_value is None and foundation_value is None:
            result["missing_both"].append(entry)
        elif sr_value is None:
            entry["available_value"] = foundation_value
            result["foundation_only"].append(entry)
        elif foundation_value is None:
            entry["available_value"] = sr_value
            result["sr_only"].append(entry)
        else:
            # Both have values - calculate discrepancy
            discrepancy = calculate_discrepancy(sr_value, foundation_value)
            entry["discrepancy"] = discrepancy

            if discrepancy["tier"] == "trivial":
                result["matches"].append(entry)
            else:
                result["discrepancies"].append(entry)

    # Sort discrepancies by percentage (highest first)
    result["discrepancies"].sort(
        key=lambda x: x["discrepancy"]["percentage"],
        reverse=True
    )

    return result


def generate_comparison_report(food_name: str, sr_fdc_id: int,
                                foundation_fdc_id: Optional[int],
                                comparison: dict) -> str:
    """
    Generate human-readable comparison report.

    Args:
        food_name: Name of the food being compared
        sr_fdc_id: SR Legacy FDC ID
        foundation_fdc_id: Foundation FDC ID (can be None)
        comparison: Result from compare_nutrients()

    Returns:
        Formatted report string
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("COMPARISON REPORT")
    lines.append("=" * 60)
    lines.append(f"Food: {food_name}")
    lines.append(f"SR Legacy FDC: {sr_fdc_id}")
    if foundation_fdc_id:
        lines.append(f"Foundation FDC: {foundation_fdc_id}")
    else:
        lines.append("Foundation FDC: Not provided")
    lines.append("")

    # Summary
    lines.append("Summary:")
    lines.append(f"  - Matching (< 5% difference): {len(comparison['matches'])} nutrients")
    lines.append(f"  - Discrepancies (≥ 5%): {len(comparison['discrepancies'])} nutrients")
    lines.append(f"  - SR Legacy only: {len(comparison['sr_only'])} nutrients")
    lines.append(f"  - Foundation only: {len(comparison['foundation_only'])} nutrients")
    lines.append(f"  - Missing from both: {len(comparison['missing_both'])} nutrients")
    lines.append("")

    # Discrepancies section
    if comparison["discrepancies"]:
        lines.append("-" * 60)
        lines.append("DISCREPANCIES REQUIRING REVIEW")
        lines.append("-" * 60)
        lines.append("")

        for i, disc in enumerate(comparison["discrepancies"], 1):
            tier = disc["discrepancy"]["tier"].upper()
            lines.append(f"[{i}/{len(comparison['discrepancies'])}] {disc['nutrient_name']} (ID: {disc['nutrient_id']})")
            lines.append(f"      SR Legacy:  {disc['sr_value']} {disc['unit']}")
            lines.append(f"      Foundation: {disc['foundation_value']} {disc['unit']}")
            lines.append(f"      Difference: {disc['discrepancy']['percentage']}% [{tier}]")
            lines.append("")

    # SR Only section
    if comparison["sr_only"]:
        lines.append("-" * 60)
        lines.append("NUTRIENTS ONLY IN SR LEGACY")
        lines.append("-" * 60)
        for nutrient in comparison["sr_only"]:
            lines.append(f"  - {nutrient['nutrient_name']}: {nutrient['sr_value']} {nutrient['unit']}")
        lines.append("")

    # Foundation Only section
    if comparison["foundation_only"]:
        lines.append("-" * 60)
        lines.append("NUTRIENTS ONLY IN FOUNDATION")
        lines.append("-" * 60)
        for nutrient in comparison["foundation_only"]:
            lines.append(f"  - {nutrient['nutrient_name']}: {nutrient['foundation_value']} {nutrient['unit']}")
        lines.append("")

    # Missing from both section
    if comparison["missing_both"]:
        lines.append("-" * 60)
        lines.append("NUTRIENTS MISSING FROM BOTH SOURCES")
        lines.append("-" * 60)
        for nutrient in comparison["missing_both"]:
            lines.append(f"  - {nutrient['nutrient_name']}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def get_discrepancy_summary(comparison: dict) -> dict:
    """
    Get a summary of discrepancies by tier.

    Args:
        comparison: Result from compare_nutrients()

    Returns:
        Dict with counts by tier
    """
    summary = {
        "trivial": 0,
        "moderate": 0,
        "significant": 0,
        "major": 0
    }

    for disc in comparison["discrepancies"]:
        tier = disc["discrepancy"]["tier"]
        summary[tier] += 1

    # Matches are trivial
    summary["trivial"] += len(comparison["matches"])

    return summary
