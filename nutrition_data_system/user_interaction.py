"""
User Interaction Module for Nutrition Data System.

Command-line interface for user decisions and input.
"""
from typing import Optional


def display_comparison_report(report: str) -> None:
    """
    Print formatted comparison report to console.

    Args:
        report: The comparison report string to display
    """
    print(report)


def display_welcome() -> None:
    """Display welcome message."""
    print("=" * 60)
    print("USDA Nutrition Data Extraction System")
    print("=" * 60)
    print()


def prompt_food_info() -> dict:
    """
    Prompt user for food_id, food_name, sr_fdc_id, foundation_fdc_id.

    Both SR Legacy and Foundation FDC IDs are optional for ingredients
    that may not exist in USDA databases.

    Returns:
        Dict with user inputs:
        {
            "food_id": str,
            "food_name": str,
            "sr_fdc_id": int or None,
            "foundation_fdc_id": int or None
        }
    """
    print("-" * 40)
    print("Enter Food Information")
    print("-" * 40)

    food_id = input("Enter food_id: ").strip()
    while not food_id:
        print("Food ID is required.")
        food_id = input("Enter food_id: ").strip()

    food_name = input("Enter food_name: ").strip()
    while not food_name:
        print("Food name is required.")
        food_name = input("Enter food_name: ").strip()

    sr_fdc_id = None
    sr_input = input("Enter SR Legacy FDC ID (or press Enter to skip): ").strip()
    if sr_input:
        try:
            sr_fdc_id = int(sr_input)
        except ValueError:
            print("Invalid SR Legacy FDC ID, skipping.")

    foundation_fdc_id = None
    foundation_input = input("Enter Foundation FDC ID (or press Enter to skip): ").strip()
    if foundation_input:
        try:
            foundation_fdc_id = int(foundation_input)
        except ValueError:
            print("Invalid Foundation FDC ID, skipping.")

    return {
        "food_id": food_id,
        "food_name": food_name,
        "sr_fdc_id": sr_fdc_id,
        "foundation_fdc_id": foundation_fdc_id
    }


def prompt_discrepancy_decision(discrepancy: dict, ai_suggestion: Optional[str] = None) -> dict:
    """
    Display discrepancy details and prompt for decision.

    Args:
        discrepancy: Dict with nutrient discrepancy details
        ai_suggestion: Optional AI analysis suggestion to display

    Returns:
        Dict with decision:
        {
            "nutrient_id": int,
            "nutrient_name": str,
            "chosen_value": float,
            "chosen_source": str,
            "comment": str
        }
    """
    nutrient_name = discrepancy.get("nutrient_name", "Unknown")
    nutrient_id = discrepancy.get("nutrient_id")
    unit = discrepancy.get("unit", "")
    sr_value = discrepancy.get("sr_value")
    foundation_value = discrepancy.get("foundation_value")
    disc_info = discrepancy.get("discrepancy", {})
    percentage = disc_info.get("percentage", 0)
    tier = disc_info.get("tier", "unknown").upper()

    print()
    print(f"  {nutrient_name} (ID: {nutrient_id})")
    print(f"      SR Legacy:  {sr_value} {unit}")
    print(f"      Foundation: {foundation_value} {unit}")
    print(f"      Difference: {percentage}% [{tier}]")
    if ai_suggestion:
        print(f"      AI Analysis: {ai_suggestion}")
    print()
    print("  Action:")
    print(f"    [1] Keep SR Legacy ({sr_value} {unit})")
    print(f"    [2] Use Foundation ({foundation_value} {unit})")
    print("    [3] Enter manual value")
    print()

    while True:
        choice = input("  Your choice: ").strip()

        if choice == "1":
            comment = input("  Reason (optional): ").strip()
            return {
                "nutrient_id": nutrient_id,
                "nutrient_name": nutrient_name,
                "chosen_value": sr_value,
                "chosen_source": "sr_legacy",
                "comment": comment or f"Kept SR Legacy (vs Foundation: {foundation_value})"
            }
        elif choice == "2":
            comment = input("  Reason (optional): ").strip()
            return {
                "nutrient_id": nutrient_id,
                "nutrient_name": nutrient_name,
                "chosen_value": foundation_value,
                "chosen_source": "foundation",
                "comment": comment or f"Chose Foundation (vs SR Legacy: {sr_value})"
            }
        elif choice == "3":
            while True:
                try:
                    manual_value = float(input("  Enter value: ").strip())
                    break
                except ValueError:
                    print("  Please enter a valid number.")
            source = input("  Enter source (e.g., literature, manual): ").strip() or "manual"
            comment = input("  Reason (optional): ").strip()
            return {
                "nutrient_id": nutrient_id,
                "nutrient_name": nutrient_name,
                "chosen_value": manual_value,
                "chosen_source": source,
                "comment": comment or f"Manual value (SR: {sr_value}, Found: {foundation_value})"
            }
        else:
            print("  Invalid choice. Please enter 1, 2, or 3.")


def prompt_missing_nutrient(nutrient: dict, ai_suggestion: Optional[str] = None) -> dict:
    """
    Prompt user for value of nutrient missing from USDA.

    All nutrients must have a value - this function requires the user to enter
    a value from literature or other sources.

    Args:
        nutrient: Dict with nutrient info
        ai_suggestion: Optional AI analysis suggestion to display

    Returns:
        Decision dict:
        {
            "nutrient_id": int or None,
            "nutrient_name": str,
            "chosen_value": float,
            "chosen_source": str,
            "comment": str
        }
    """
    nutrient_name = nutrient.get("nutrient_name", "Unknown")
    nutrient_id = nutrient.get("nutrient_id")
    unit = nutrient.get("unit", "")
    notes = nutrient.get("notes", "")

    print()
    print(f"  {nutrient_name}")
    print(f"      Not available in USDA databases - value required from literature.")
    if notes:
        print(f"      Note: {notes}")
    if ai_suggestion:
        print(f"      AI Analysis: {ai_suggestion}")
    print()

    while True:
        try:
            value = float(input(f"  Enter value ({unit}): ").strip())
            break
        except ValueError:
            print("  Please enter a valid number.")

    citation = input("  Enter citation (e.g., Spitze et al. 2003): ").strip()
    while not citation:
        print("  Citation is required for literature values.")
        citation = input("  Enter citation: ").strip()

    return {
        "nutrient_id": nutrient_id,
        "nutrient_name": nutrient_name,
        "chosen_value": value,
        "chosen_source": "literature",
        "comment": f"Source: {citation}"
    }


def prompt_sr_only_nutrient(nutrient: dict, ai_suggestion: Optional[str] = None) -> dict:
    """
    Prompt user for nutrient only available in SR Legacy.

    Args:
        nutrient: Dict with nutrient info
        ai_suggestion: Optional AI analysis suggestion to display

    Returns:
        Decision dict
    """
    nutrient_name = nutrient.get("nutrient_name", "Unknown")
    nutrient_id = nutrient.get("nutrient_id")
    value = nutrient.get("sr_value") or nutrient.get("available_value")
    unit = nutrient.get("unit", "")

    print()
    print(f"  {nutrient_name}: {value} {unit} (SR Legacy only)")
    if ai_suggestion:
        print(f"  AI Analysis: {ai_suggestion}")
    print()
    print("  Action:")
    print(f"    [1] Accept SR Legacy value ({value} {unit})")
    print("    [2] Enter different value")
    print()

    while True:
        choice = input("  Your choice: ").strip()

        if choice == "1":
            return {
                "nutrient_id": nutrient_id,
                "nutrient_name": nutrient_name,
                "chosen_value": value,
                "chosen_source": "sr_legacy",
                "comment": "SR Legacy (only source)"
            }
        elif choice == "2":
            while True:
                try:
                    manual_value = float(input(f"  Enter value ({unit}): ").strip())
                    break
                except ValueError:
                    print("  Please enter a valid number.")
            source = input("  Enter source (e.g., literature, manual): ").strip() or "manual"
            reason = input("  Reason for rejecting SR Legacy value: ").strip()
            return {
                "nutrient_id": nutrient_id,
                "nutrient_name": nutrient_name,
                "chosen_value": manual_value,
                "chosen_source": source,
                "comment": f"Rejected SR Legacy ({value}): {reason}" if reason else f"Rejected SR Legacy ({value})"
            }
        else:
            print("  Invalid choice. Please enter 1 or 2.")


def prompt_confirmation(message: str) -> bool:
    """
    Generic yes/no confirmation prompt.

    Args:
        message: The confirmation message to display

    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input(f"{message} [Y/n]: ").strip().lower()
        if response in ("", "y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("Please enter Y or N.")


def display_final_summary(food_data: list[dict], food_name: str) -> None:
    """
    Display final nutrient table before saving.

    Args:
        food_data: List of nutrient records
        food_name: Name of the food
    """
    print()
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Food: {food_name}")
    print()

    # Count by source
    source_counts = {}
    for record in food_data:
        source = record.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1

    print(f"Total nutrients: {len(food_data)}")
    for source, count in sorted(source_counts.items()):
        print(f"  - From {source}: {count}")
    print()

    # List nutrients
    print("Nutrients:")
    for record in food_data:
        value = record.get("value", "")
        unit = record.get("unit", "")
        # Try fediaf_nutrient_name first (new schema), fall back to nutrient_name for backward compatibility
        name = record.get("fediaf_nutrient_name") or record.get("nutrient_name", "Unknown")
        source = record.get("source", "")

        if value:
            print(f"  - {name}: {value} {unit} [{source}]")
        else:
            print(f"  - {name}: (skipped) [{source}]")

    print()


def display_progress(current: int, total: int, item_name: str) -> None:
    """
    Display progress indicator.

    Args:
        current: Current item number
        total: Total number of items
        item_name: Name of current item
    """
    print(f"\n[{current}/{total}] {item_name}")


def display_error(message: str) -> None:
    """Display error message."""
    print(f"\nERROR: {message}\n")


def display_success(message: str) -> None:
    """Display success message."""
    print(f"\n✓ {message}\n")


def display_info(message: str) -> None:
    """Display info message."""
    print(f"\n{message}\n")
