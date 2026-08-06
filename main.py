#!/usr/bin/env python3
"""
USDA Nutrition Data Extraction System - Main Entry Point

Orchestrates the complete workflow for extracting, comparing, and storing
nutrition data from USDA FoodData Central databases.
"""
from typing import Optional

from config import AI_MODEL
from db_connection import close_db
from fediaf_nutrients import (
    get_all_nutrients,
    get_usda_nutrient_ids,
    get_taurine_nutrient,
    get_nutrient_by_id,
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
    food_exists_by_name,
    add_ingredient,
    add_food_nutrients,
    create_nutrient_record,
    delete_food,
)
from cv_autoassign import assign_cv_for_food
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
    detect_mass_failure,
    describe_auto_accept_disagreement,
    model_provenance,
    live_ai_calls_allowed,
    permit_live_ai_calls,
)
from supplement_template import (
    generate_template,
    read_template,
    display_supplement_summary,
    TEMPLATES_DIR,
)


def validate_nutrient_coverage(
    comparison: dict,
    missing_nutrients: list[dict]
) -> bool:
    """
    Validate that all tracked nutrients are accounted for.

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
        True if all nutrients are accounted for, False otherwise
    """
    all_nutrients = get_all_nutrients()
    expected_count = len(all_nutrients)

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
        print(f"  ✓ All {expected_count} nutrients accounted for")
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
    food_name: str,
    food_id: int,
    nutrient_id: Optional[int],
    fediaf_nutrient_name: str,
    usda_nutrient_name: Optional[str],
    unit: str,
    value: Optional[float],
    source: str,
    comment: Optional[str] = None,
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
    ai_confidence: Optional[str] = None,
    ai_model: Optional[str] = None
) -> dict:
    """
    Create single nutrient record matching database schema.

    Includes USDA metadata from the selected source for error calculation.
    Includes AI validation fields for literature cross-reference.
    """
    return create_nutrient_record(
        food_name=food_name,
        food_id=food_id,
        nutrient_id=nutrient_id,
        fediaf_nutrient_name=fediaf_nutrient_name,
        usda_nutrient_name=usda_nutrient_name,
        unit=unit,
        value=value,
        source=source,
        comment=comment,
        num_samples=num_samples,
        min_value=min_value,
        max_value=max_value,
        median_value=median_value,
        year_acquired=year_acquired,
        derivation_description=derivation_description,
        ai_recommendation=ai_recommendation,
        ai_justification=ai_justification,
        ai_source=ai_source,
        ai_confidence=ai_confidence,
        ai_model=ai_model
    )


def _cleanup_incomplete_ingredient(food_id: Optional[int]) -> None:
    """
    Remove an ingredient row created before its nutrients were saved.

    Best-effort: a failure here must not mask the error that triggered cleanup,
    and delete_food refuses when the formulator already references the row.
    """
    if food_id is None:
        return
    display_info(f"Cleaning up incomplete ingredient (ID: {food_id})...")
    try:
        delete_food(food_id)
    except Exception as exc:  # noqa: BLE001 - never mask the original failure
        display_error(
            f"Could not remove incomplete ingredient {food_id}: {exc}. "
            "Remove it manually before re-adding this food."
        )


def _api_nutrient_metadata(nutrient: dict) -> dict:
    """
    Full six-field metadata block from a fetched USDA nutrient row.

    The AI prompts render all six fields; dropping min/median/max here (as the
    single-source pseudo-comparisons once did) silently blinds the validator
    in exactly the scenario the lamb-shoulder failure exercised.
    """
    return {
        "num_samples": nutrient.get("num_samples"),
        "min_value": nutrient.get("min_value"),
        "max_value": nutrient.get("max_value"),
        "median_value": nutrient.get("median_value"),
        "year_acquired": nutrient.get("year_acquired"),
        "derivation_description": nutrient.get("derivation_description"),
    }


def report_unpopulated_zeros(dataset_label: str, data: dict) -> None:
    """
    Tell the reviewer which nutrients USDA published as an unpopulated zero.

    The zero is kept as USDA published it — an audit found such zeros are usually
    genuine, so substituting a literature value would do more harm than good. But
    USDA recorded no measurement behind them, so the reviewer is told which ones
    they are and can override any that look wrong at the prompt.
    """
    ids = data.get("unpopulated_zeros") or []
    if not ids:
        return
    names = []
    for nid in ids:
        info = get_nutrient_by_id(nid)
        names.append(info["nutrient_name"] if info else str(nid))
    display_info(
        f"{dataset_label}: {len(names)} nutrient(s) published as 0 with no data points "
        f"and no derivation (USDA never measured them) — review before accepting: "
        f"{', '.join(sorted(names))}"
    )


def process_single_food(food_id: int, food_info: dict) -> list[dict]:
    """
    Process one food item through complete workflow.

    Args:
        food_id: Auto-generated food_id from the database
        food_info: Dict with food_name, sr_fdc_id, foundation_fdc_id

    Returns:
        List of nutrient records ready for saving
    """
    food_name = food_info["food_name"]
    sr_fdc_id = food_info.get("sr_fdc_id")
    foundation_fdc_id = food_info.get("foundation_fdc_id")

    records = []
    sr_data = None
    foundation_data = None

    # Fetch SR Legacy data if provided
    if sr_fdc_id:
        display_info(f"Fetching SR Legacy data for FDC ID {sr_fdc_id}...")
        try:
            sr_data = fetch_sr_legacy(sr_fdc_id)
            sr_nutrient_count = sum(1 for n in sr_data["nutrients"].values() if n["value"] is not None)
            display_success(f"Retrieved {sr_nutrient_count} of {len(get_usda_nutrient_ids())} FEDIAF-required nutrients")
            report_unpopulated_zeros("SR Legacy", sr_data)
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
            report_unpopulated_zeros("Foundation", foundation_data)
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
        for entry in comparison.get("missing_both", []):
            nutrient_info = get_nutrient_by_id(entry["nutrient_id"])
            if nutrient_info:
                missing_nutrients.append(nutrient_info)

        # Always add Taurine (USDA ID 1234, no data in USDA datasets)
        taurine = get_taurine_nutrient()
        if taurine and taurine["nutrient_id"] not in [n["nutrient_id"] for n in missing_nutrients]:
            missing_nutrients.append(taurine)

        # Validate all nutrients are accounted for
        validate_nutrient_coverage(comparison, missing_nutrients)

        # Run AI validation on all nutrients
        display_info("Running AI literature validation...")
        ai_results = validate_nutrients_concurrent(
            food_name=food_name,
            comparison_result=comparison,
            sr_data=sr_data,
            foundation_data=foundation_data,
            missing_nutrients=missing_nutrients,
            verbose=True,
            food_info=food_info
        )
        display_success(f"AI validation complete for {len(ai_results)} nutrients")

        # Mass-failure gate: a wholesale validation failure (credits, outage)
        # must abort the food, not walk the operator through a review loop
        # whose every suggestion is an error message.
        mass_failure = detect_mass_failure(ai_results)
        if mass_failure:
            display_error(f"AI validation mass failure — aborting this food: {mass_failure}")
            return []

        # Helper to get AI result for a nutrient
        def get_ai_fields(nid):
            """Get AI validation fields for a nutrient."""
            ai_result = ai_results.get(nid)
            if ai_result:
                return {
                    "ai_recommendation": ai_result.recommendation,
                    "ai_justification": ai_result.justification,
                    "ai_source": ai_result.literature_source,
                    "ai_confidence": ai_result.confidence,
                    # Model ID + prompt version hash, so a stored justification
                    # can be traced to the prompt that produced it.
                    "ai_model": model_provenance(),
                }
            return {}

        # Process matches (auto-accept Foundation for trivial differences < 5%)
        for match in comparison["matches"]:
            nid = match["nutrient_id"]
            nutrient_info = get_nutrient_by_id(nid)
            value = match["foundation_value"]
            foundation_meta = match.get("foundation_metadata", {})
            ai_fields = get_ai_fields(nid)
            # This path never prompts, so an AI/DB contradiction would
            # otherwise be stored with no review trail.
            comment = f"Auto-accepted (< 5% difference with SR Legacy: {match['sr_value']})"
            disagreement = describe_auto_accept_disagreement(
                ai_results.get(nid), "foundation"
            )
            if disagreement:
                comment = f"{comment}. {disagreement}"
            records.append(build_nutrient_record(
                food_name=food_name,
                food_id=food_id,
                nutrient_id=nid,
                fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                usda_nutrient_name=match["nutrient_name"],
                unit=match.get("unit", nutrient_info["unit"] if nutrient_info else ""),
                value=value,
                source="foundation",
                comment=comment,
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
                ai_confidence=ai_fields.get("ai_confidence"),
                ai_model=ai_fields.get("ai_model")
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
                    food_name=food_name,
                    food_id=food_id,
                    nutrient_id=nid,
                    fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                    usda_nutrient_name=decision["nutrient_name"],
                    unit=disc.get("unit", nutrient_info["unit"] if nutrient_info else ""),
                    value=decision["chosen_value"],
                    source=decision["chosen_source"],
                    comment=decision["comment"],
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
                    ai_confidence=ai_fields.get("ai_confidence"),
                    ai_model=ai_fields.get("ai_model")
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
                    food_name=food_name,
                    food_id=food_id,
                    nutrient_id=nid,
                    fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                    usda_nutrient_name=decision["nutrient_name"],
                    unit=nutrient.get("unit", nutrient_info["unit"] if nutrient_info else ""),
                    value=decision["chosen_value"],
                    source=decision["chosen_source"],
                    comment=decision["comment"],
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
                    ai_confidence=ai_fields.get("ai_confidence"),
                    ai_model=ai_fields.get("ai_model")
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

                # Written without prompting: record any AI disagreement rather
                # than leaving the contradiction implicit in the columns.
                comment = "Foundation only (not in SR Legacy)"
                disagreement = describe_auto_accept_disagreement(ai_result, "foundation")
                if disagreement:
                    comment = f"{comment}. {disagreement}"

                records.append(build_nutrient_record(
                    food_name=food_name,
                    food_id=food_id,
                    nutrient_id=nid,
                    fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                    usda_nutrient_name=nutrient["nutrient_name"],
                    unit=nutrient.get("unit", nutrient_info["unit"] if nutrient_info else ""),
                    value=value,
                    source="foundation",
                    comment=comment,
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
                    ai_confidence=ai_fields.get("ai_confidence"),
                    ai_model=ai_fields.get("ai_model")
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

        # Always add Taurine (USDA ID 1234, no data in USDA datasets)
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
                    "sr_metadata": _api_nutrient_metadata(nutrient)
                }
                for nid, nutrient in sr_data["nutrients"].items()
                if nutrient["value"] is not None
            ],
            "foundation_only": [],
            "missing_both": list(missing_from_sr)
        }

        # Validate all nutrients are accounted for
        validate_nutrient_coverage(sr_only_comparison, missing_nutrients)

        # Run AI validation
        display_info("Running AI literature validation...")
        ai_results = validate_nutrients_concurrent(
            food_name=food_name,
            comparison_result=sr_only_comparison,
            sr_data=sr_data,
            foundation_data=None,
            missing_nutrients=missing_nutrients,
            verbose=True,
            food_info=food_info
        )
        display_success(f"AI validation complete for {len(ai_results)} nutrients")

        # Mass-failure gate: a wholesale validation failure (credits, outage)
        # must abort the food, not walk the operator through a review loop
        # whose every suggestion is an error message.
        mass_failure = detect_mass_failure(ai_results)
        if mass_failure:
            display_error(f"AI validation mass failure — aborting this food: {mass_failure}")
            return []

        # Helper to get AI result for a nutrient
        def get_ai_fields(nid):
            """Get AI validation fields for a nutrient."""
            ai_result = ai_results.get(nid)
            if ai_result:
                return {
                    "ai_recommendation": ai_result.recommendation,
                    "ai_justification": ai_result.justification,
                    "ai_source": ai_result.literature_source,
                    "ai_confidence": ai_result.confidence,
                    # Model ID + prompt version hash, so a stored justification
                    # can be traced to the prompt that produced it.
                    "ai_model": model_provenance(),
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
                "sr_metadata": _api_nutrient_metadata(nutrient)
            }

            # Prompt user to accept or provide different value
            decision = prompt_sr_only_nutrient(sr_only_nutrient, ai_suggestion)

            ai_fields = get_ai_fields(nid)

            # Use SR metadata if user accepted SR value, otherwise no metadata for manual entries
            if decision["chosen_source"] == "sr_legacy":
                meta = _api_nutrient_metadata(nutrient)
            else:
                meta = {}

            records.append(build_nutrient_record(
                food_name=food_name,
                food_id=food_id,
                nutrient_id=nid,
                fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                usda_nutrient_name=decision["nutrient_name"],
                unit=nutrient["unit"] or (nutrient_info["unit"] if nutrient_info else ""),
                value=decision["chosen_value"],
                source=decision["chosen_source"],
                comment=decision["comment"],
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
                ai_confidence=ai_fields.get("ai_confidence"),
                ai_model=ai_fields.get("ai_model")
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

        # Always add Taurine (USDA ID 1234, no data in USDA datasets)
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
                    "foundation_metadata": _api_nutrient_metadata(nutrient)
                }
                for nid, nutrient in foundation_data["nutrients"].items()
                if nutrient["value"] is not None
            ],
            "missing_both": list(missing_from_foundation)
        }

        # Validate all nutrients are accounted for
        validate_nutrient_coverage(foundation_only_comparison, missing_nutrients)

        # Run AI validation
        display_info("Running AI literature validation...")
        ai_results = validate_nutrients_concurrent(
            food_name=food_name,
            comparison_result=foundation_only_comparison,
            sr_data={"nutrients": {}},  # Empty SR data
            foundation_data=foundation_data,
            missing_nutrients=missing_nutrients,
            verbose=True,
            food_info=food_info
        )
        display_success(f"AI validation complete for {len(ai_results)} nutrients")

        # Mass-failure gate: a wholesale validation failure (credits, outage)
        # must abort the food, not walk the operator through a review loop
        # whose every suggestion is an error message.
        mass_failure = detect_mass_failure(ai_results)
        if mass_failure:
            display_error(f"AI validation mass failure — aborting this food: {mass_failure}")
            return []

        # Helper to get AI result for a nutrient
        def get_ai_fields(nid):
            """Get AI validation fields for a nutrient."""
            ai_result = ai_results.get(nid)
            if ai_result:
                return {
                    "ai_recommendation": ai_result.recommendation,
                    "ai_justification": ai_result.justification,
                    "ai_source": ai_result.literature_source,
                    "ai_confidence": ai_result.confidence,
                    # Model ID + prompt version hash, so a stored justification
                    # can be traced to the prompt that produced it.
                    "ai_model": model_provenance(),
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
            foundation_meta = _api_nutrient_metadata(nutrient)
            ai_fields = get_ai_fields(nid)

            # Auto-accepted without prompting — record any AI disagreement.
            comment = "Foundation only (SR Legacy not available)"
            disagreement = describe_auto_accept_disagreement(
                ai_results.get(nid), "foundation"
            )
            if disagreement:
                comment = f"{comment}. {disagreement}"

            records.append(build_nutrient_record(
                food_name=food_name,
                food_id=food_id,
                nutrient_id=nid,
                fediaf_nutrient_name=nutrient_info["nutrient_name"] if nutrient_info else f"Unknown ({nid})",
                usda_nutrient_name=nutrient["name"],
                unit=nutrient["unit"] or (nutrient_info["unit"] if nutrient_info else ""),
                value=value,
                source="foundation",
                comment=comment,
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
                ai_confidence=ai_fields.get("ai_confidence"),
                ai_model=ai_fields.get("ai_model")
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

        # Validate all nutrients are accounted for
        validate_nutrient_coverage(empty_comparison, missing_nutrients)

        # Run AI validation to get literature suggestions
        display_info("Running AI literature validation for all nutrients...")
        ai_results = validate_nutrients_concurrent(
            food_name=food_name,
            comparison_result=empty_comparison,
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=missing_nutrients,
            verbose=True,
            food_info=food_info
        )
        display_success(f"AI validation complete for {len(ai_results)} nutrients")

        # Mass-failure gate: a wholesale validation failure (credits, outage)
        # must abort the food, not walk the operator through a review loop
        # whose every suggestion is an error message.
        mass_failure = detect_mass_failure(ai_results)
        if mass_failure:
            display_error(f"AI validation mass failure — aborting this food: {mass_failure}")
            return []

    # Handle nutrients missing from USDA
    if missing_nutrients:
        print("\n" + "-" * 60)
        print("NUTRIENTS MISSING FROM USDA")
        print("-" * 60)

        for i, nutrient in enumerate(missing_nutrients, 1):
            display_progress(i, len(missing_nutrients), nutrient["nutrient_name"])

            # Get AI suggestion for missing nutrient. Results are keyed by
            # nutrient_id only — the validator drops no-ID results loudly.
            nutrient_id = nutrient.get("nutrient_id")
            ai_result = ai_results.get(nutrient_id) if nutrient_id is not None else None
            ai_suggestion = format_ai_suggestion(ai_result) if ai_result else None

            decision = prompt_missing_nutrient(nutrient, ai_suggestion)

            # Get AI fields
            ai_fields = {}
            if ai_result:
                ai_fields = {
                    "ai_recommendation": ai_result.recommendation,
                    "ai_justification": ai_result.justification,
                    "ai_source": ai_result.literature_source,
                    "ai_confidence": ai_result.confidence,
                    "ai_model": model_provenance(),
                }

            records.append(build_nutrient_record(
                food_name=food_name,
                food_id=food_id,
                nutrient_id=decision["nutrient_id"],
                fediaf_nutrient_name=nutrient["nutrient_name"],
                usda_nutrient_name=nutrient.get("usda_name", nutrient["nutrient_name"]),
                unit=nutrient["unit"],
                value=decision["chosen_value"],
                source=decision["chosen_source"],
                comment=decision["comment"],
                # AI validation fields
                ai_recommendation=ai_fields.get("ai_recommendation"),
                ai_justification=ai_fields.get("ai_justification"),
                ai_source=ai_fields.get("ai_source"),
                ai_confidence=ai_fields.get("ai_confidence"),
                ai_model=ai_fields.get("ai_model")
            ))

    return records


def process_supplement(food_id: int, food_name: str) -> list[dict]:
    """
    Process a supplement using a pre-filled CSV template.

    Bypasses USDA fetch, comparison, and AI validation. Reads nutrient values
    from a CSV template file, shows non-zero nutrients for confirmation, and
    creates records with source="product_label" for entered values and
    value=0/source="not_in_supplement" for the rest.

    Args:
        food_id: Auto-generated food_id from the database.
        food_name: Name of the supplement.

    Returns:
        List of nutrient records ready for saving, or empty list on failure.
    """
    # Auto-detect template from food name
    default_path = TEMPLATES_DIR / f"{food_name.lower().replace(' ', '_')}.csv"
    if default_path.exists():
        file_path = input(f"Enter template CSV path [{default_path}]: ").strip()
        if not file_path:
            file_path = str(default_path)
    else:
        file_path = input("Enter path to filled supplement template CSV: ").strip()
        if not file_path:
            display_error("No file path provided.")
            return []

    try:
        template_data = read_template(file_path)
    except FileNotFoundError as e:
        display_error(str(e))
        return []
    except ValueError as e:
        display_error(f"Invalid template: {e}")
        return []

    display_supplement_summary(template_data)

    if not prompt_confirmation("Accept these values?"):
        display_info("Supplement entry cancelled.")
        return []

    records: list[dict] = []
    for nutrient in template_data["nutrients"]:
        has_value = nutrient["value"] is not None and nutrient["value"] != 0
        fediaf_info = get_nutrient_by_id(nutrient["nutrient_id"])
        usda_name = fediaf_info["usda_name"] if fediaf_info else nutrient["fediaf_nutrient_name"]

        records.append(create_nutrient_record(
            food_name=food_name,
            food_id=food_id,
            nutrient_id=nutrient["nutrient_id"],
            fediaf_nutrient_name=nutrient["fediaf_nutrient_name"],
            usda_nutrient_name=usda_name,
            unit=nutrient["unit"],
            value=nutrient["value"] if has_value else 0.0,
            source="product_label" if has_value else "not_in_supplement",
            comment="From supplement template" if has_value else "Zero - not in supplement",
        ))

    return records


def main():
    """Main entry point."""
    display_welcome()

    from config import AI_MOCK_MODE
    if AI_MOCK_MODE:
        print("[MOCK MODE] AI validation is using mock responses (AI_MOCK_MODE=true)\n")
    elif not live_ai_calls_allowed():
        # Billed calls are blocked by default. Ask once per run rather than
        # letting the pipeline spend money on the operator's behalf.
        nutrient_count = len(get_all_nutrients())
        display_info(
            f"AI validation calls the Anthropic API — about {nutrient_count} billed "
            f"requests per ingredient, using model {AI_MODEL}."
        )
        if prompt_confirmation("Allow billed AI validation calls for this run?"):
            permit_live_ai_calls("operator confirmed at startup")
        else:
            # Don't proceed into an ingredient add that cannot complete: the
            # validators raise LiveAPICallBlocked, which would abort mid-run and
            # leave the ingredient row created before validation orphaned.
            display_info(
                "Billed calls declined. AI validation cannot run, so the ingredient "
                "add would fail partway through."
            )
            display_info("Re-run with AI_MOCK_MODE=true for an offline dry run.")
            close_db()
            return

    # Bound before the try: the exception handlers below reference food_id, so a
    # failure ahead of the first loop iteration (e.g. initialize_database) must
    # not hit UnboundLocalError inside the handler.
    food_id: Optional[int] = None

    try:
        # Initialize database connection
        initialize_database()

        while True:
            food_id = None

            # Get food info from user (no food_id — auto-generated)
            food_info = prompt_food_info()
            food_name = food_info["food_name"]

            # Check if food already exists by name
            existing_id = food_exists_by_name(food_name)
            if existing_id:
                if not prompt_confirmation(
                    f"Food '{food_name}' already exists (ID: {existing_id}). Add as new entry?"
                ):
                    display_info("Skipping this food.")
                    if prompt_confirmation("Process another food?"):
                        continue
                    else:
                        break

            # Create ingredient record — auto-generates food_id
            food_id = add_ingredient(
                food_name=food_name,
                category=food_info["category"],
                base_unit=food_info["base_unit"],
                portion_qty=food_info["portion_qty"],
                grams_per_unit=food_info["grams_per_unit"],
                me_kcal_per_unit=food_info.get("me_kcal_per_unit"),
                sr_legacy_fdc_id=food_info.get("sr_fdc_id"),
                foundation_fdc_id=food_info.get("foundation_fdc_id"),
                cooking_method=food_info.get("cooking_method"),
                price_per_unit=food_info["price_per_unit"],
                currency=food_info.get("currency", "USD"),
                source=food_info.get("source", "grocery"),
                amazon_url=food_info.get("amazon_url"),
                chewy_url=food_info.get("chewy_url"),
                supplement_info=food_info.get("supplement_info"),
                protein_species=food_info.get("protein_species"),
                display_name=food_info.get("display_name"),
                is_nutritional_additive=food_info.get("is_nutritional_additive", False),
                is_corrector=food_info.get("is_corrector", False),
            )
            display_success(f"Created ingredient '{food_name}' with ID {food_id}")

            # Process the food - supplements use CSV template, others use USDA pipeline
            if food_info["category"] == "Supplement":
                records = process_supplement(food_id, food_name)
            else:
                records = process_single_food(food_id, food_info)

            if not records:
                display_error("No records were created.")
                # Clean up the orphaned ingredient row
                delete_food(food_id)
                food_id = None
                if prompt_confirmation("Process another food?"):
                    continue
                else:
                    break

            # Validate completeness — all nutrients must be present
            expected_count = len(get_all_nutrients())
            if len(records) != expected_count:
                display_error(
                    f"Expected {expected_count} nutrients but got {len(records)}. "
                    "Cannot save incomplete data."
                )
                delete_food(food_id)
                food_id = None
                if prompt_confirmation("Process another food?"):
                    continue
                else:
                    break

            # Display final summary
            display_final_summary(records, food_name)

            # Confirm save
            if prompt_confirmation("Save to database?"):
                added = add_food_nutrients(records)
                # The row is committed from here on: stop tracking it for cleanup,
                # or a failure in anything below (CV assignment, prompts) would
                # hand a fully-saved ingredient to delete_food.
                saved_food_id = food_id
                food_id = None
                display_success(f"Saved {added} nutrient records for '{food_name}' (ID: {saved_food_id})")
                # Auto-assign CVs so the new ingredient isn't left at NULL (best-effort:
                # a gate block / missing datasets warns but never undoes the save).
                cv_ok, cv_msg = assign_cv_for_food(saved_food_id)
                if cv_ok:
                    display_success(f"CVs assigned: {cv_msg}")
                else:
                    display_error(f"CVs NOT assigned ({cv_msg}).")
                    display_info(
                        f"Run when ready: python cv_assign.py --food-id {saved_food_id} "
                        "--commit --signed-off-by NAME"
                    )
            else:
                display_info("Not saved. Removing ingredient entry.")
                delete_food(food_id)
                food_id = None

            # Ask to continue
            print("-" * 60)
            if not prompt_confirmation("Process another food?"):
                break

        print("\nThank you for using the USDA Nutrition Data Extraction System!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        _cleanup_incomplete_ingredient(food_id)
    except Exception as exc:
        # add_ingredient runs before nutrient processing, so any failure between
        # the two leaves a row with zero nutrients. Previously only Ctrl-C was
        # handled, so an API error, a DB blip, or a permission refusal each left
        # an orphan behind. Clean up, then re-raise — the error is still real.
        display_error(f"Unexpected error: {exc}")
        _cleanup_incomplete_ingredient(food_id)
        raise
    finally:
        close_db()


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3 and sys.argv[1] == "--generate-template":
        supplement_name = " ".join(sys.argv[2:])
        path = generate_template(supplement_name)
        print(f"Template generated: {path}")
        print(f"Fill in the '{supplement_name}' column with nutrient values, then run the program.")
    else:
        main()
