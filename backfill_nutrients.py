#!/usr/bin/env python3
"""
Backfill script: Add 2 new secondary constraint nutrients to existing ingredients.

Nutrients added:
  - 1293: Fatty acids, total polyunsaturated (g)
  - 1280: DPA 22:5 n-3 (g)

For real foods (with FDC IDs): fetch from USDA API + AI validation, auto-accept.
For supplements (no FDC IDs): interactive prompt (default=0 on Enter).

Usage:
  python backfill_nutrients.py                     # Full backfill with backup
  python backfill_nutrients.py --dry-run            # Preview only
  python backfill_nutrients.py --food-id 10001      # Single food
  python backfill_nutrients.py --skip-backup        # Skip pg_dump (not recommended)
"""
import argparse
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from config import AI_MODEL, DATABASE_NAME, DATABASE_PASSWORD
from db_connection import get_db, close_db
from database import (
    get_all_food_ids,
    get_ingredient,
    add_food_nutrients,
    create_nutrient_record,
)
from fediaf_nutrients import get_secondary_nutrients, get_nutrient_by_id
from usda_api import fetch_food_data, extract_nutrients, USDAAPIError
from ai_validation import (
    validate_nutrient_single,
    AIValidationResult,
)


BACKFILL_NUTRIENT_IDS = [1293, 1280]


def backup_database(backup_dir: Path) -> Path:
    """Create a pg_dump backup before modifying data."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{DATABASE_NAME}_{timestamp}.sql"

    # Use libpq's pg_dump to match server version
    pg_dump_bin = "/opt/homebrew/Cellar/libpq/17.6/bin/pg_dump"
    cmd = [
        pg_dump_bin,
        "-h", "localhost",
        "-p", "5432",
        "-U", "postgres",
        "-d", DATABASE_NAME,
        "-f", str(backup_path),
    ]

    env = dict(subprocess.os.environ, PGPASSWORD=DATABASE_PASSWORD)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"  WARNING: pg_dump failed: {result.stderr}")
        raise RuntimeError(f"Database backup failed: {result.stderr}")

    print(f"  Database backup created: {backup_path}")
    return backup_path


def get_existing_nutrient_ids(food_id: int) -> set[int]:
    """Get set of nutrient_ids already in DB for a food_id."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT nutrient_id FROM ingredient_nutrients WHERE food_id = %s",
            (food_id,),
        )
        return {int(row["nutrient_id"]) for row in cur.fetchall()}


def backfill_supplement(
    food_id: int, food_name: str, nutrients_to_add: list[dict]
) -> list[dict]:
    """Interactively prompt for supplement nutrient values (default=0)."""
    records = []
    print(f"\n  Enter values for {food_name} (press Enter for 0):")

    for nutrient in nutrients_to_add:
        nid = nutrient["nutrient_id"]
        name = nutrient["nutrient_name"]
        unit = nutrient["unit"]

        while True:
            raw = input(f"    {name} ({unit}) [{nid}]: ").strip()
            if raw == "":
                value = 0.0
                break
            try:
                value = float(raw)
                break
            except ValueError:
                print("      Invalid number, try again.")

        source = "product_label" if value != 0 else "not_in_supplement"
        records.append(create_nutrient_record(
            food_name=food_name,
            food_id=food_id,
            nutrient_id=nid,
            fediaf_nutrient_name=name,
            usda_nutrient_name=nutrient["usda_name"],
            unit=unit,
            value=value,
            source=source,
            comment="Backfill: secondary constraint nutrient",
        ))

    return records


def backfill_real_food(
    food_id: int, food_name: str, ingredient: dict,
    nutrients_to_add: list[dict]
) -> list[dict]:
    """Fetch 2 nutrients from USDA API, run AI validation, build records."""
    sr_fdc_id = ingredient.get("sr_legacy_fdc_id")
    foundation_fdc_id = ingredient.get("foundation_fdc_id")
    nutrient_ids = [n["nutrient_id"] for n in nutrients_to_add]

    # Fetch from USDA
    sr_nutrients: Optional[dict] = None
    foundation_nutrients: Optional[dict] = None

    if sr_fdc_id:
        try:
            raw = fetch_food_data(sr_fdc_id)
            sr_nutrients = extract_nutrients(raw, nutrient_ids)
            sr_count = sum(1 for v in sr_nutrients.values() if v["value"] is not None)
            print(f"    SR Legacy ({sr_fdc_id}): {sr_count}/{len(nutrient_ids)} nutrients found")
        except USDAAPIError as e:
            print(f"    SR Legacy fetch failed: {e}")

    if foundation_fdc_id:
        try:
            raw = fetch_food_data(foundation_fdc_id)
            foundation_nutrients = extract_nutrients(raw, nutrient_ids)
            f_count = sum(1 for v in foundation_nutrients.values() if v["value"] is not None)
            print(f"    Foundation ({foundation_fdc_id}): {f_count}/{len(nutrient_ids)} nutrients found")
        except USDAAPIError as e:
            print(f"    Foundation fetch failed: {e}")

    records = []
    for nutrient in nutrients_to_add:
        nid = nutrient["nutrient_id"]
        name = nutrient["nutrient_name"]
        unit = nutrient["unit"]
        usda_name = nutrient["usda_name"]

        sr_val = sr_nutrients[nid]["value"] if sr_nutrients and nid in sr_nutrients else None
        f_val = foundation_nutrients[nid]["value"] if foundation_nutrients and nid in foundation_nutrients else None
        sr_meta = sr_nutrients[nid] if sr_nutrients and nid in sr_nutrients else {}
        f_meta = foundation_nutrients[nid] if foundation_nutrients and nid in foundation_nutrients else {}

        # Determine prompt type and run AI validation
        ai_result = _validate_nutrient(food_name, nid, name, unit, sr_val, f_val, sr_meta, f_meta)

        # Choose value based on AI recommendation
        chosen_value, chosen_source, chosen_meta = _choose_value(
            ai_result, sr_val, f_val, sr_meta, f_meta
        )

        print(f"    {name}: {chosen_value} {unit} (source: {chosen_source}, "
              f"AI: {ai_result.confidence})")

        records.append(create_nutrient_record(
            food_name=food_name,
            food_id=food_id,
            nutrient_id=nid,
            fediaf_nutrient_name=name,
            usda_nutrient_name=usda_name,
            unit=unit,
            value=chosen_value,
            source=chosen_source,
            num_samples=chosen_meta.get("num_samples"),
            min_value=chosen_meta.get("min_value"),
            max_value=chosen_meta.get("max_value"),
            median_value=chosen_meta.get("median_value"),
            year_acquired=chosen_meta.get("year_acquired"),
            derivation_description=chosen_meta.get("derivation_description"),
            ai_recommendation=ai_result.recommendation,
            ai_justification=ai_result.justification,
            ai_source=ai_result.literature_source,
            ai_confidence=ai_result.confidence,
            ai_model=AI_MODEL,
            comment="Backfill: secondary constraint nutrient",
        ))

    return records


def _validate_nutrient(
    food_name: str, nid: int, name: str, unit: str,
    sr_val: Optional[float], f_val: Optional[float],
    sr_meta: dict, f_meta: dict,
) -> AIValidationResult:
    """Run AI validation for a single nutrient based on available data."""
    if sr_val is not None and f_val is not None:
        # Both sources available
        avg = (sr_val + f_val) / 2 if (sr_val + f_val) != 0 else 1
        disc = abs(sr_val - f_val) / avg * 100 if avg != 0 else 0
        prompt_type = "both_sources"
        nutrient_data = {
            "nutrient_id": nid, "nutrient_name": name, "unit": unit,
            "prompt_type": prompt_type,
            "sr_value": sr_val, "foundation_value": f_val,
            "discrepancy_percent": disc,
            "sr_metadata": sr_meta, "foundation_metadata": f_meta,
        }
    elif sr_val is not None:
        prompt_type = "sr_only"
        nutrient_data = {
            "nutrient_id": nid, "nutrient_name": name, "unit": unit,
            "prompt_type": prompt_type,
            "sr_value": sr_val, "sr_metadata": sr_meta,
        }
    elif f_val is not None:
        prompt_type = "foundation_only"
        nutrient_data = {
            "nutrient_id": nid, "nutrient_name": name, "unit": unit,
            "prompt_type": prompt_type,
            "foundation_value": f_val, "foundation_metadata": f_meta,
        }
    else:
        prompt_type = "missing"
        nutrient_data = {
            "nutrient_id": nid, "nutrient_name": name, "unit": unit,
            "prompt_type": prompt_type,
        }

    return validate_nutrient_single(food_name, nutrient_data)


def _choose_value(
    ai_result: AIValidationResult,
    sr_val: Optional[float], f_val: Optional[float],
    sr_meta: dict, f_meta: dict,
) -> tuple[float, str, dict]:
    """Choose final value based on AI recommendation. Returns (value, source, metadata)."""
    rec = ai_result.recommendation

    if rec == "foundation" and f_val is not None:
        return f_val, "foundation", f_meta
    elif rec == "sr_legacy" and sr_val is not None:
        return sr_val, "sr_legacy", sr_meta
    elif rec == "literature" and ai_result.recommended_value is not None:
        return ai_result.recommended_value, "literature", {}
    elif f_val is not None:
        return f_val, "foundation", f_meta
    elif sr_val is not None:
        return sr_val, "sr_legacy", sr_meta
    elif ai_result.recommended_value is not None:
        return ai_result.recommended_value, "literature", {}
    else:
        return 0.0, "literature", {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill 2 secondary constraint nutrients for existing ingredients"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing to DB")
    parser.add_argument("--food-id", type=int,
                        help="Process only a specific food_id")
    parser.add_argument("--skip-backup", action="store_true",
                        help="Skip database backup (not recommended)")
    args = parser.parse_args()

    print("=" * 60)
    print("BACKFILL: Secondary Constraint Nutrients")
    print("  Nutrients: 1293 (Total PUFA), 1280 (DPA 22:5 n-3)")
    print("=" * 60)

    # Step 1: Backup
    if not args.skip_backup and not args.dry_run:
        print("\nStep 1: Database backup")
        try:
            backup_database(Path("backups"))
        except RuntimeError:
            print("  Backup failed. Use --skip-backup to proceed anyway.")
            sys.exit(1)
    else:
        print("\nStep 1: Backup skipped")

    # Step 2: Get nutrients to backfill
    secondary_nutrients = get_secondary_nutrients()
    print(f"\nStep 2: {len(secondary_nutrients)} nutrients to backfill")
    for n in secondary_nutrients:
        print(f"  - {n['nutrient_id']}: {n['nutrient_name']} ({n['unit']})")

    # Step 3: Get food_ids
    if args.food_id:
        food_ids = [args.food_id]
    else:
        food_ids = get_all_food_ids()

    print(f"\nStep 3: Processing {len(food_ids)} food(s)")
    print("-" * 60)

    total_added = 0
    for food_id in food_ids:
        ingredient = get_ingredient(food_id)
        if not ingredient:
            print(f"\n  [{food_id}] NOT FOUND - skipping")
            continue

        food_name = ingredient["food_name"]
        category = ingredient.get("category", "")

        # Check which nutrients already exist
        existing_ids = get_existing_nutrient_ids(food_id)
        nutrients_to_add = [
            n for n in secondary_nutrients
            if n["nutrient_id"] not in existing_ids
        ]

        if not nutrients_to_add:
            print(f"\n  [{food_id}] {food_name}: already has all nutrients, skipping")
            continue

        is_supplement = category == "Supplement"
        print(f"\n  [{food_id}] {food_name} ({category})"
              f" - {'SUPPLEMENT' if is_supplement else 'REAL FOOD'}")

        if is_supplement:
            if args.dry_run:
                print("    [DRY RUN] Would prompt for supplement values")
                records = []
                for n in nutrients_to_add:
                    records.append({"fediaf_nutrient_name": n["nutrient_name"],
                                    "value": 0.0, "unit": n["unit"]})
            else:
                records = backfill_supplement(food_id, food_name, nutrients_to_add)
        else:
            records = backfill_real_food(food_id, food_name, ingredient, nutrients_to_add)

        if args.dry_run:
            for r in records:
                name = r.get("fediaf_nutrient_name", "?")
                val = r.get("value", 0)
                unit = r.get("unit", "")
                print(f"    [DRY RUN] {name} = {val} {unit}")
        else:
            added = add_food_nutrients(records)
            total_added += added
            print(f"    Inserted {added} nutrient(s)")

    print("\n" + "=" * 60)
    if args.dry_run:
        print("DRY RUN complete. No changes made.")
    else:
        print(f"Backfill complete. {total_added} nutrient records added.")
    print("=" * 60)

    close_db()


if __name__ == "__main__":
    main()
