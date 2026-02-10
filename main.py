#!/usr/bin/env python3
"""
USDA Nutrition Data Extraction System - Main Entry Point

Orchestrates the complete workflow for extracting, comparing, and storing
nutrition data from USDA FoodData Central databases.
"""
import sys
from typing import Optional

from config import DATABASE_FILE
from fediaf_nutrients import (
    get_all_nutrients,
    get_usda_nutrient_ids,
    get_taurine_nutrient,
    get_nutrient_by_id,
    TAURINE_NUTRIENT_ID,
)
from usda_api import (
    USDAAPIError,
    fetch_sr_legacy,
    fetch_foundation,
)
from comparison import (
    compare_nutrients,
    generate_comparison_report,
)
from database import (
    initialize_database,
    food_exists,
    add_food_nutrients,
    create_nutrient_record,
)
from user_interaction import (
    display_welcome,
    display_comparison_report,
    display_progress,
    display_error,
    display_success,
    display_info,
    display_final_summary,
    prompt_food_info,
    prompt_discrepancy_decision,
    prompt_missing_nutrient,
    prompt_sr_only_nutrient,
    prompt_confirmation,
)
from ai_validation import (
    validate_nutrients_concurrent,
    format_ai_suggestion,
    AIValidationResult,
)


def validate_nutrient_coverage(
    comparison: dict,
    missing_nutrients: list[dict]
) -> bool:
    """
    Validate that all 50 FEDIAF-required nutrients are accounted for.

    Displays a summary of nutrient coverage by category:
    - Matches (both SR and Foundation)
    - Discrepancies (both SR and Foundation, different values)
    - SR Legacy only
    - Foundation only
    - Missing from both (need literature)

    Args:
        comparison: Comparison result dict
        missing_nutrients: List of nutrients missing from USDA

    Returns:
        True if all 50 nutrients are accounted for, False otherwise
    """
    all_nutrients = get_all_nutrients()
    expected_count = len(all_nutrients)  # Should be 50

    # Count nutrients in each category
    matches_count = len(comparison.get("matches", []))
    discrepancies_count = len(comparison.get("discrepancies", []))
    sr_only_count = len(comparison.get("sr_only", []))
    foundation_only_count = len(comparison.get("foundation_only", []))
    missing_count = len(missing_nutrients)

    total_count = matches_count + discrepancies_count + sr_only_count + foundation_only_count + missing_count

    # Display validation summary
    print("\n" + "=" * 60)
    print("NUTRIENT COVERAGE VALIDATION")
    print("=" * 60)
    print(f"  Matches (SR ≈ Foundation):     {matches_count:3d}")
    print(f"  Discrepancies (SR ≠ Foundation): {discrepancies_count:3d}")
    print(f"  SR Legacy only:                 {sr_only_count:3d}")
    print(f"  Foundation only:                {foundation_only_count:3d}")
    print(f"  Missing (need literature):      {missing_count:3d}")
    print("-" * 60)
    print(f"  TOTAL ACCOUNTED:                {total_count:3d} / {expected_count}")

    if total_count == expected_count:
        print("  ✓ All 50 nutrients accounted for")
        print("=" * 60)
        return True
    else:
        print(f"  ✗ WARNING: {expected_count - total_count} nutrients unaccounted!")

        # Find which nutrients are missing
        accounted_ids = set()

        for match in comparison.get("matches", []):
            accounted_ids.add(match["nutrient_id"])
        for disc in comparison.get("discrepancies", []):
            accounted_ids.add(disc["nutrient_id"])
        for sr in comparison.get("sr_only", []):
            accounted_ids.add(sr["nutrient_id"])
        for found in comparison.get("foundation_only", []):
            accounted_ids.add(found["nutrient_id"])
        for missing in missing_nutrients:
            accounted_ids.add(missing["nutrient_id"])

        all_ids = {n["nutrient_id"] for n in all_nutrients}
        unaccounted_ids = all_ids - accounted_ids

        if unaccounted_ids:
            print("\n  Unaccounted nutrients:")
            for nid in unaccounted_ids:
                nutrient = get_nutrient_by_id(nid)
                if nutrient:
                    print(f"    - {nutrient['nutrient_name']} (ID: {nid})")

        print("=" * 60)
        return False


def build_nutrient_record(
    food_id: str,
    food_name: str,
    sr_fdc_id: Optional[int],
    foundation_fdc_id: Optional[int],
    nutrient_id: Optional[int],
    fediaf_nutrient_name: str,
    usda_nutrient_name: Optional[str],
    unit: str,
    value: Optional[float],
    source: str,
    comment: Optional[str] = None,
    portion_size: str = "100g",
    # USDA metadata fields (from selected source)
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
    Create single nutrient record matching schema.

    Includes USDA metadata from the selected source for error calculation.
    Includes AI validation fields for literature cross-reference.
    Note: standard_error and footnote removed - USDA API does not provide these.
    """
    return create_nutrient_record(
        food_id=food_id,
        food_name=food_name,
        sr_legacy_fdc_id=sr_fdc_id,
        foundation_fdc_id=foundation_fdc_id,
        nutrient_id=nutrient_id,
        fediaf_nutrient_name=fediaf_nutrient_name,
        usda_nutrient_name=usda_nutrient_name,
        unit=unit,
        value=value,
        source=source,
        comment=comment,
        portion_size=portion_size,
        num_samples=num_samples,
        min_value=min_value,
        max_value=max_value,
        median_value=median_value,
        year_acquired=year_acquired,
        derivation_description=derivation_description,
        ai_recommendation=ai_recommendation,
        ai_justification=ai_justification,
        ai_source=ai_source,
        ai_confidence=ai_confidence
    )


def process_single_food(food_info: dict) -> list[dict]:
    """
    Process one food item through complete workflow.

    Args:
        food_info: Dict with food_id, food_name, sr_fdc_id, foundation_fdc_id

    Returns:
        List of nutrient records ready for saving
    """
    food_id = food_info["food_id"]
    food_name = food_info["food_name"]
    sr_fdc_id = food_info.get("sr_fdc_id")
    foundation_fdc_id = food_info.get("foundation_fdc_id")

    records = []
    sr_data = None
    foundation_data = None
    portion_size = "100g"

    # Fetch SR Legacy data if provided
    if sr_fdc_id:
        display_info(f"Fetching SR Legacy data for FDC ID {sr_fdc_id}...")
        try:
            sr_data = fetch_sr_legacy(sr_fdc_id)
            sr_nutrient_count = sum(1 for n in sr_data["nutrients"].values() if n["value"] is not None)
            display_success(f"Retrieved {sr_nutrient_count} of {len(get_usda_nutrient_ids())} FEDIAF-required nutrients")
            # Get portion size from API response (USDA data is always per 100g)
            portion_size = sr_data.get("portion_size", "100g")
        except USDAAPIError as e:
            display_error(f"Failed to fetch SR Legacy data: {e}")
            display_info("Continuing without SR Legacy data...")

    # Fetch Foundation data if provided
    if foundation_fdc_id:
        display_info(f"Fetching Foundation data for FDC ID {foundation_fdc_id}...")
        try:
            foundation_data = fetch_foundation(foundation_fdc_id)
            found_nutrient_count = sum(1 for n in foundation_data["nutrients"].values() if n["value"] is not None)
            display_success(f"Retrieved {found_nutrient_count} of {len(get_usda_nutrient_ids())} FEDIAF-required nutrients")
        except USDAAPIError as e:
            display_error(f"Failed to fetch Foundation data: {e}")
            display_info("Continuing with SR Legacy data only...")

    # Handle different scenarios based on available data
    # Scenario 1: Both SR and Foundation available
    if sr_data and foundation_data:
        comparison = compare_nutrients(sr_data, foundation_data)
        report = generate_comparison_report(food_name, sr_fdc_id, foundation_fdc_id, comparison)
        display_comparison_report(report)

        # Calculate missing nutrients dynamically from comparison results
        # Includes nutrients missing from both databases + Taurine (always missing)
        missing_nutrients = []
        for nid in comparison.get("missing_both", []):
            nutrient_info = get_nutrient_by_id(nid)
            if nutrient_info:
                missing_nutrients.append(nutrient_info)

        # Always add Taurine (custom ID 9001, never in USDA)
        taurine = get_taurine_nutrient()
        if taurine and taurine["nutrient_id"] not in [n["nutrient_id"] for n in missing_nutrients]:
            missing_nutrients.append(taurine)

        # Validate all 50 nutrients are accounted for
        validate_nutrient_coverage(comparison, missing_nutrients)

        # Run AI validation on all nutrients
        display_info("Running AI literature validation...")
        ai_results = validate_nutrients_concurrent(
            food_name=food_name,
            comparison_result=comparison,
            sr_data=sr_data,
            foundation_data=foundation_data,
            missing_nutrients=missing_nutrients,
            verbose=True
        )
        display_success(f"AI validation complete for {len(ai_results)} nutrients")

        # Helper to get AI result for a nutrient
        def get_ai_fields(nid):
            """Get AI validation fields for a nutrient."""
            ai_result = ai_results.get(nid)
            if ai_result:
                return {
                    "ai_recommendation": ai_result.recommendation,
                    "ai_justification": ai_result.justification,
                    "ai_source": ai_result.literature_source,
                    "ai_confidence": ai_result.confidence
                }
            return {}

        # Process matches (auto-accept Foundation for trivial differences < 5%)
        for match in comparison["matches"]:
            nid = match["nutrient_id"]
            nutrient_info = get_nutrient_by_id(nid)
            value = match["foundation_value"]
            foundation_meta = match.get("foundation_metadata", {})
            ai_fields = get_ai_fields(nid)
            records.append(build_nutrient_record(
                food_id=food_id,
                food_name=food_name,
                sr_fdc_id=sr_fdc_id,
                foundation_fdc_id=foundation_fdc_id,
                nutrient_id=nid,
                fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                usda_nutrient_name=match["nutrient_name"],
                unit=match.get("unit", nutrient_info["unit"] if nutrient_info else ""),
                value=value,
                source="foundation",
                comment=f"Auto-accepted (< 5% difference with SR Legacy: {match['sr_value']})",
                portion_size=portion_size,
                # USDA metadata from Foundation (selected source)
                num_samples=foundation_meta.get("num_samples"),
                min_value=foundation_meta.get("min_value"),
                max_value=foundation_meta.get("max_value"),
                median_value=foundation_meta.get("median_value"),
                year_acquired=foundation_meta.get("year_acquired"),
                derivation_description=foundation_meta.get("derivation_description"),
                # AI validation fields
                ai_recommendation=ai_fields.get("ai_recommendation"),
                ai_justification=ai_fields.get("ai_justification"),
                ai_source=ai_fields.get("ai_source"),
                ai_confidence=ai_fields.get("ai_confidence")
            ))

        # Process discrepancies - require user decision
        if comparison["discrepancies"]:
            print("\n" + "-" * 60)
            print("DISCREPANCIES REQUIRING REVIEW")
            print("-" * 60)

            for i, disc in enumerate(comparison["discrepancies"], 1):
                display_progress(i, len(comparison["discrepancies"]), disc["nutrient_name"])

                # Get AI suggestion for this nutrient
                nid = disc["nutrient_id"]
                ai_result = ai_results.get(nid)
                ai_suggestion = format_ai_suggestion(ai_result) if ai_result else None

                decision = prompt_discrepancy_decision(disc, ai_suggestion)

                nutrient_info = get_nutrient_by_id(nid)
                ai_fields = get_ai_fields(nid)

                # Use metadata from the chosen source
                chosen_source = decision["chosen_source"]
                if chosen_source == "sr_legacy":
                    meta = disc.get("sr_metadata", {})
                elif chosen_source == "foundation":
                    meta = disc.get("foundation_metadata", {})
                else:
                    meta = {}  # For literature or skipped, no USDA metadata

                records.append(build_nutrient_record(
                    food_id=food_id,
                    food_name=food_name,
                    sr_fdc_id=sr_fdc_id,
                    foundation_fdc_id=foundation_fdc_id,
                    nutrient_id=nid,
                    fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                    usda_nutrient_name=decision["nutrient_name"],
                    unit=disc.get("unit", nutrient_info["unit"] if nutrient_info else ""),
                    value=decision["chosen_value"],
                    source=decision["chosen_source"],
                    comment=decision["comment"],
                    portion_size=portion_size,
                    # USDA metadata from selected source
                    num_samples=meta.get("num_samples"),
                    min_value=meta.get("min_value"),
                    max_value=meta.get("max_value"),
                    median_value=meta.get("median_value"),
                    year_acquired=meta.get("year_acquired"),
                    derivation_description=meta.get("derivation_description"),
                    # AI validation fields
                    ai_recommendation=ai_fields.get("ai_recommendation"),
                    ai_justification=ai_fields.get("ai_justification"),
                    ai_source=ai_fields.get("ai_source"),
                    ai_confidence=ai_fields.get("ai_confidence")
                ))

        # Process SR-only nutrients
        if comparison["sr_only"]:
            print("\n" + "-" * 60)
            print("NUTRIENTS ONLY IN SR LEGACY")
            print("-" * 60)

            for nutrient in comparison["sr_only"]:
                nid = nutrient["nutrient_id"]

                # Get AI suggestion for this nutrient
                ai_result = ai_results.get(nid)
                ai_suggestion = format_ai_suggestion(ai_result) if ai_result else None

                decision = prompt_sr_only_nutrient(nutrient, ai_suggestion)
                nutrient_info = get_nutrient_by_id(nid)
                sr_meta = nutrient.get("sr_metadata", {})
                ai_fields = get_ai_fields(nid)

                records.append(build_nutrient_record(
                    food_id=food_id,
                    food_name=food_name,
                    sr_fdc_id=sr_fdc_id,
                    foundation_fdc_id=foundation_fdc_id,
                    nutrient_id=nid,
                    fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                    usda_nutrient_name=decision["nutrient_name"],
                    unit=nutrient.get("unit", nutrient_info["unit"] if nutrient_info else ""),
                    value=decision["chosen_value"],
                    source=decision["chosen_source"],
                    comment=decision["comment"],
                    portion_size=portion_size,
                    # USDA metadata from SR Legacy
                    num_samples=sr_meta.get("num_samples"),
                    min_value=sr_meta.get("min_value"),
                    max_value=sr_meta.get("max_value"),
                    median_value=sr_meta.get("median_value"),
                    year_acquired=sr_meta.get("year_acquired"),
                    derivation_description=sr_meta.get("derivation_description"),
                    # AI validation fields
                    ai_recommendation=ai_fields.get("ai_recommendation"),
                    ai_justification=ai_fields.get("ai_justification"),
                    ai_source=ai_fields.get("ai_source"),
                    ai_confidence=ai_fields.get("ai_confidence")
                ))

        # Process Foundation-only nutrients
        if comparison["foundation_only"]:
            print("\n" + "-" * 60)
            print("NUTRIENTS ONLY IN FOUNDATION")
            print("-" * 60)

            for nutrient in comparison["foundation_only"]:
                nid = nutrient["nutrient_id"]
                nutrient_info = get_nutrient_by_id(nid)
                value = nutrient["foundation_value"]
                foundation_meta = nutrient.get("foundation_metadata", {})
                ai_fields = get_ai_fields(nid)

                # Get AI suggestion for this nutrient
                ai_result = ai_results.get(nid)
                ai_suggestion = format_ai_suggestion(ai_result) if ai_result else None

                print(f"  {nutrient['nutrient_name']}: {value} {nutrient.get('unit', '')} (Foundation only)")
                if ai_suggestion:
                    print(f"    AI Analysis: {ai_suggestion}")

                records.append(build_nutrient_record(
                    food_id=food_id,
                    food_name=food_name,
                    sr_fdc_id=sr_fdc_id,
                    foundation_fdc_id=foundation_fdc_id,
                    nutrient_id=nid,
                    fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                    usda_nutrient_name=nutrient["nutrient_name"],
                    unit=nutrient.get("unit", nutrient_info["unit"] if nutrient_info else ""),
                    value=value,
                    source="foundation",
                    comment="Foundation only (not in SR Legacy)",
                    portion_size=portion_size,
                    # USDA metadata from Foundation
                    num_samples=foundation_meta.get("num_samples"),
                    min_value=foundation_meta.get("min_value"),
                    max_value=foundation_meta.get("max_value"),
                    median_value=foundation_meta.get("median_value"),
                    year_acquired=foundation_meta.get("year_acquired"),
                    derivation_description=foundation_meta.get("derivation_description"),
                    # AI validation fields
                    ai_recommendation=ai_fields.get("ai_recommendation"),
                    ai_justification=ai_fields.get("ai_justification"),
                    ai_source=ai_fields.get("ai_source"),
                    ai_confidence=ai_fields.get("ai_confidence")
                ))

    # Scenario 2: Only SR Legacy data available
    elif sr_data:
        print("\n" + "-" * 60)
        print("SR LEGACY DATA (Foundation not available)")
        print("-" * 60)

        # Calculate missing nutrients: nutrients not in SR Legacy + Taurine
        # Get all required nutrient IDs
        all_nutrient_ids = set(get_usda_nutrient_ids())
        sr_nutrient_ids = set(
            nid for nid, nutrient in sr_data["nutrients"].items()
            if nutrient["value"] is not None
        )
        missing_from_sr = all_nutrient_ids - sr_nutrient_ids

        missing_nutrients = []
        for nid in missing_from_sr:
            nutrient_info = get_nutrient_by_id(nid)
            if nutrient_info:
                missing_nutrients.append(nutrient_info)

        # Always add Taurine (custom ID 9001, never in USDA)
        taurine = get_taurine_nutrient()
        if taurine and taurine["nutrient_id"] not in [n["nutrient_id"] for n in missing_nutrients]:
            missing_nutrients.append(taurine)

        # Build a pseudo-comparison for AI validation (all SR-only)
        sr_only_comparison = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [
                {
                    "nutrient_id": nid,
                    "nutrient_name": nutrient["name"],
                    "sr_value": nutrient["value"],
                    "unit": nutrient["unit"],
                    "sr_metadata": {
                        "num_samples": nutrient.get("num_samples"),
                        "year_acquired": nutrient.get("year_acquired"),
                        "derivation_description": nutrient.get("derivation_description"),
                    }
                }
                for nid, nutrient in sr_data["nutrients"].items()
                if nutrient["value"] is not None
            ],
            "foundation_only": [],
            "missing_both": list(missing_from_sr)
        }

        # Validate all 50 nutrients are accounted for
        validate_nutrient_coverage(sr_only_comparison, missing_nutrients)

        # Run AI validation
        display_info("Running AI literature validation...")
        ai_results = validate_nutrients_concurrent(
            food_name=food_name,
            comparison_result=sr_only_comparison,
            sr_data=sr_data,
            foundation_data=None,
            missing_nutrients=missing_nutrients,
            verbose=True
        )
        display_success(f"AI validation complete for {len(ai_results)} nutrients")

        # Helper to get AI result for a nutrient
        def get_ai_fields(nid):
            """Get AI validation fields for a nutrient."""
            ai_result = ai_results.get(nid)
            if ai_result:
                return {
                    "ai_recommendation": ai_result.recommendation,
                    "ai_justification": ai_result.justification,
                    "ai_source": ai_result.literature_source,
                    "ai_confidence": ai_result.confidence
                }
            return {}

        # Process each SR Legacy nutrient - prompt user for each
        sr_nutrients_with_values = [
            (nid, nutrient) for nid, nutrient in sr_data["nutrients"].items()
            if nutrient["value"] is not None
        ]

        print(f"\nReviewing {len(sr_nutrients_with_values)} nutrients from SR Legacy...")

        for i, (nid, nutrient) in enumerate(sr_nutrients_with_values, 1):
            nutrient_info = get_nutrient_by_id(nid)
            value = nutrient["value"]

            display_progress(i, len(sr_nutrients_with_values), nutrient["name"])

            # Get AI suggestion for this nutrient
            ai_result = ai_results.get(nid)
            ai_suggestion = format_ai_suggestion(ai_result) if ai_result else None

            # Build nutrient data for prompt
            sr_only_nutrient = {
                "nutrient_id": nid,
                "nutrient_name": nutrient["name"],
                "sr_value": value,
                "unit": nutrient["unit"],
                "sr_metadata": {
                    "num_samples": nutrient.get("num_samples"),
                    "year_acquired": nutrient.get("year_acquired"),
                    "derivation_description": nutrient.get("derivation_description"),
                }
            }

            # Prompt user to accept or provide different value
            decision = prompt_sr_only_nutrient(sr_only_nutrient, ai_suggestion)

            ai_fields = get_ai_fields(nid)

            # Use SR metadata if user accepted SR value, otherwise no metadata for manual entries
            if decision["chosen_source"] == "sr_legacy":
                meta = {
                    "num_samples": nutrient.get("num_samples"),
                    "min_value": nutrient.get("min_value"),
                    "max_value": nutrient.get("max_value"),
                    "median_value": nutrient.get("median_value"),
                    "year_acquired": nutrient.get("year_acquired"),
                    "derivation_description": nutrient.get("derivation_description"),
                }
            else:
                meta = {}

            records.append(build_nutrient_record(
                food_id=food_id,
                food_name=food_name,
                sr_fdc_id=sr_fdc_id,
                foundation_fdc_id=foundation_fdc_id,
                nutrient_id=nid,
                fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                usda_nutrient_name=decision["nutrient_name"],
                unit=nutrient["unit"] or (nutrient_info["unit"] if nutrient_info else ""),
                value=decision["chosen_value"],
                source=decision["chosen_source"],
                comment=decision["comment"],
                portion_size=portion_size,
                # USDA metadata (only if SR Legacy was accepted)
                num_samples=meta.get("num_samples"),
                min_value=meta.get("min_value"),
                max_value=meta.get("max_value"),
                median_value=meta.get("median_value"),
                year_acquired=meta.get("year_acquired"),
                derivation_description=meta.get("derivation_description"),
                # AI validation fields
                ai_recommendation=ai_fields.get("ai_recommendation"),
                ai_justification=ai_fields.get("ai_justification"),
                ai_source=ai_fields.get("ai_source"),
                ai_confidence=ai_fields.get("ai_confidence")
            ))

    # Scenario 3: Only Foundation data available (no SR Legacy)
    elif foundation_data:
        print("\n" + "-" * 60)
        print("FOUNDATION DATA (SR Legacy not available)")
        print("-" * 60)

        # Calculate missing nutrients: nutrients not in Foundation + Taurine
        all_nutrient_ids = set(get_usda_nutrient_ids())
        foundation_nutrient_ids = set(
            nid for nid, nutrient in foundation_data["nutrients"].items()
            if nutrient["value"] is not None
        )
        missing_from_foundation = all_nutrient_ids - foundation_nutrient_ids

        missing_nutrients = []
        for nid in missing_from_foundation:
            nutrient_info = get_nutrient_by_id(nid)
            if nutrient_info:
                missing_nutrients.append(nutrient_info)

        # Always add Taurine (custom ID 9001, never in USDA)
        taurine = get_taurine_nutrient()
        if taurine and taurine["nutrient_id"] not in [n["nutrient_id"] for n in missing_nutrients]:
            missing_nutrients.append(taurine)

        # Build a pseudo-comparison for AI validation (all Foundation-only)
        foundation_only_comparison = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [
                {
                    "nutrient_id": nid,
                    "nutrient_name": nutrient["name"],
                    "foundation_value": nutrient["value"],
                    "unit": nutrient["unit"],
                    "foundation_metadata": {
                        "num_samples": nutrient.get("num_samples"),
                        "year_acquired": nutrient.get("year_acquired"),
                        "derivation_description": nutrient.get("derivation_description"),
                    }
                }
                for nid, nutrient in foundation_data["nutrients"].items()
                if nutrient["value"] is not None
            ],
            "missing_both": list(missing_from_foundation)
        }

        # Validate all 50 nutrients are accounted for
        validate_nutrient_coverage(foundation_only_comparison, missing_nutrients)

        # Run AI validation
        display_info("Running AI literature validation...")
        ai_results = validate_nutrients_concurrent(
            food_name=food_name,
            comparison_result=foundation_only_comparison,
            sr_data={"nutrients": {}},  # Empty SR data
            foundation_data=foundation_data,
            missing_nutrients=missing_nutrients,
            verbose=True
        )
        display_success(f"AI validation complete for {len(ai_results)} nutrients")

        # Helper to get AI result for a nutrient
        def get_ai_fields(nid):
            """Get AI validation fields for a nutrient."""
            ai_result = ai_results.get(nid)
            if ai_result:
                return {
                    "ai_recommendation": ai_result.recommendation,
                    "ai_justification": ai_result.justification,
                    "ai_source": ai_result.literature_source,
                    "ai_confidence": ai_result.confidence
                }
            return {}

        # Process each Foundation nutrient - auto-accept
        foundation_nutrients_with_values = [
            (nid, nutrient) for nid, nutrient in foundation_data["nutrients"].items()
            if nutrient["value"] is not None
        ]

        print(f"\nProcessing {len(foundation_nutrients_with_values)} nutrients from Foundation...")

        for nid, nutrient in foundation_nutrients_with_values:
            nutrient_info = get_nutrient_by_id(nid)
            value = nutrient["value"]
            foundation_meta = {
                "num_samples": nutrient.get("num_samples"),
                "min_value": nutrient.get("min_value"),
                "max_value": nutrient.get("max_value"),
                "median_value": nutrient.get("median_value"),
                "year_acquired": nutrient.get("year_acquired"),
                "derivation_description": nutrient.get("derivation_description"),
            }
            ai_fields = get_ai_fields(nid)

            records.append(build_nutrient_record(
                food_id=food_id,
                food_name=food_name,
                sr_fdc_id=sr_fdc_id,
                foundation_fdc_id=foundation_fdc_id,
                nutrient_id=nid,
                fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                usda_nutrient_name=nutrient["name"],
                unit=nutrient["unit"] or (nutrient_info["unit"] if nutrient_info else ""),
                value=value,
                source="foundation",
                comment="Foundation only (SR Legacy not available)",
                portion_size=portion_size,
                # USDA metadata from Foundation
                num_samples=foundation_meta.get("num_samples"),
                min_value=foundation_meta.get("min_value"),
                max_value=foundation_meta.get("max_value"),
                median_value=foundation_meta.get("median_value"),
                year_acquired=foundation_meta.get("year_acquired"),
                derivation_description=foundation_meta.get("derivation_description"),
                # AI validation fields
                ai_recommendation=ai_fields.get("ai_recommendation"),
                ai_justification=ai_fields.get("ai_justification"),
                ai_source=ai_fields.get("ai_source"),
                ai_confidence=ai_fields.get("ai_confidence")
            ))

    # Scenario 4: Neither SR Legacy nor Foundation available
    else:
        print("\n" + "-" * 60)
        print("NO USDA DATA AVAILABLE")
        print("-" * 60)
        display_info("All nutrients will need to be entered from literature sources.")

        # All nutrients are missing - need literature values
        missing_nutrients = get_all_nutrients()

        # Build empty comparison for AI validation
        empty_comparison = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [],
            "foundation_only": [],
            "missing_both": [n["nutrient_id"] for n in missing_nutrients if n["nutrient_id"]]
        }

        # Validate all 50 nutrients are accounted for
        validate_nutrient_coverage(empty_comparison, missing_nutrients)

        # Run AI validation to get literature suggestions
        display_info("Running AI literature validation for all nutrients...")
        ai_results = validate_nutrients_concurrent(
            food_name=food_name,
            comparison_result=empty_comparison,
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=missing_nutrients,
            verbose=True
        )
        display_success(f"AI validation complete for {len(ai_results)} nutrients")

    # Handle nutrients missing from USDA
    if missing_nutrients:
        print("\n" + "-" * 60)
        print("NUTRIENTS MISSING FROM USDA")
        print("-" * 60)

        for i, nutrient in enumerate(missing_nutrients, 1):
            display_progress(i, len(missing_nutrients), nutrient["nutrient_name"])

            # Get AI suggestion for missing nutrient
            # Try nutrient_id first, then fall back to nutrient_name as key
            nutrient_id = nutrient.get("nutrient_id")
            nutrient_name = nutrient["nutrient_name"]
            ai_result = ai_results.get(nutrient_id) if nutrient_id else ai_results.get(nutrient_name)
            ai_suggestion = format_ai_suggestion(ai_result) if ai_result else None

            decision = prompt_missing_nutrient(nutrient, ai_suggestion)

            # Get AI fields
            ai_fields = {}
            if ai_result:
                ai_fields = {
                    "ai_recommendation": ai_result.recommendation,
                    "ai_justification": ai_result.justification,
                    "ai_source": ai_result.literature_source,
                    "ai_confidence": ai_result.confidence
                }

            records.append(build_nutrient_record(
                food_id=food_id,
                food_name=food_name,
                sr_fdc_id=sr_fdc_id,
                foundation_fdc_id=foundation_fdc_id,
                nutrient_id=decision["nutrient_id"],
                fediaf_nutrient_name=nutrient["nutrient_name"],
                usda_nutrient_name=None,  # Not available in USDA
                unit=nutrient["unit"],
                value=decision["chosen_value"],
                source=decision["chosen_source"],
                comment=decision["comment"],
                portion_size=portion_size,
                # AI validation fields
                ai_recommendation=ai_fields.get("ai_recommendation"),
                ai_justification=ai_fields.get("ai_justification"),
                ai_source=ai_fields.get("ai_source"),
                ai_confidence=ai_fields.get("ai_confidence")
            ))

    return records


def main():
    """Main entry point."""
    display_welcome()

    # Initialize database
    initialize_database()

    while True:
        # Get food info from user
        food_info = prompt_food_info()

        # Check if food already exists
        if food_exists(food_info["food_id"]):
            if not prompt_confirmation(f"Food '{food_info['food_id']}' already exists. Overwrite?"):
                display_info("Skipping this food.")
                if prompt_confirmation("Process another food?"):
                    continue
                else:
                    break

        # Process the food
        records = process_single_food(food_info)

        if not records:
            display_error("No records were created.")
            if prompt_confirmation("Process another food?"):
                continue
            else:
                break

        # Display final summary
        display_final_summary(records, food_info["food_name"])

        # Confirm save
        if prompt_confirmation("Save to database?"):
            added = add_food_nutrients(records, str(DATABASE_FILE))
            display_success(f"Saved {added} nutrient records to {DATABASE_FILE}")
        else:
            display_info("Not saved.")

        # Ask to continue
        print("-" * 60)
        if not prompt_confirmation("Process another food?"):
            break

    print("\nThank you for using the USDA Nutrition Data Extraction System!")


if __name__ == "__main__":
    main()
