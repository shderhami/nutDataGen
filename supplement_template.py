"""
Supplement Template Module.

Generates CSV templates for supplement nutrient entry and reads filled templates
back into nutrient records for database storage.

Template format:
    nutrient_id,fediaf_nutrient_name,unit,<Supplement Name>

The user fills in values in the supplement name column. Empty cells or 0 values
mean the nutrient is not present in the supplement.
"""
import csv
from pathlib import Path
from typing import Optional

from fediaf_nutrients import get_all_nutrients


TEMPLATES_DIR = Path(__file__).parent / "templates"


def generate_template(supplement_name: str) -> Path:
    """
    Generate a CSV template for a supplement.

    Creates a CSV file with all 50 FEDIAF nutrients as rows and the supplement
    name as the value column header. The user fills in nutrient values from
    the product label.

    Args:
        supplement_name: Name of the supplement (used as column header and filename).

    Returns:
        Path to the generated CSV template file.
    """
    TEMPLATES_DIR.mkdir(exist_ok=True)

    safe_name = supplement_name.lower().replace(" ", "_")
    file_path = TEMPLATES_DIR / f"{safe_name}.csv"

    nutrients = get_all_nutrients()

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nutrient_id", "fediaf_nutrient_name", "unit", supplement_name])
        for nutrient in nutrients:
            writer.writerow([
                nutrient["nutrient_id"],
                nutrient["nutrient_name"],
                nutrient["unit"],
                "",  # Empty value for user to fill
            ])

    return file_path


def read_template(file_path: str | Path) -> dict:
    """
    Read a filled supplement template CSV.

    Parses the CSV and returns the supplement name and nutrient values.
    Validates that nutrient IDs match the FEDIAF list.

    Args:
        file_path: Path to the filled CSV template.

    Returns:
        Dict with:
            "supplement_name": str (from column header),
            "nutrients": list of dicts with:
                "nutrient_id": int,
                "fediaf_nutrient_name": str,
                "unit": str,
                "value": float or None (None if cell was empty),

    Raises:
        FileNotFoundError: If the template file does not exist.
        ValueError: If the template format is invalid or nutrient IDs don't match.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {file_path}")

    expected_nutrients = get_all_nutrients()
    expected_ids = {n["nutrient_id"] for n in expected_nutrients}

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)

        if len(header) < 4:
            raise ValueError(
                f"Invalid template format: expected 4 columns, got {len(header)}. "
                "Expected: nutrient_id, fediaf_nutrient_name, unit, <Supplement Name>"
            )

        supplement_name = header[3]
        if not supplement_name.strip():
            raise ValueError("Supplement name (4th column header) is empty.")

        nutrients: list[dict] = []
        found_ids: set[int] = set()

        for row_num, row in enumerate(reader, start=2):
            if not row or all(cell.strip() == "" for cell in row):
                continue  # Skip empty rows

            if len(row) < 4:
                raise ValueError(f"Row {row_num}: expected 4 columns, got {len(row)}")

            try:
                nutrient_id = int(row[0].strip())
            except ValueError:
                raise ValueError(f"Row {row_num}: invalid nutrient_id '{row[0]}'")

            if nutrient_id not in expected_ids:
                raise ValueError(
                    f"Row {row_num}: nutrient_id {nutrient_id} is not in the FEDIAF nutrient list"
                )

            found_ids.add(nutrient_id)

            value_str = row[3].strip() if len(row) > 3 else ""
            value: Optional[float] = None
            if value_str:
                try:
                    value = float(value_str)
                except ValueError:
                    raise ValueError(
                        f"Row {row_num}: invalid value '{value_str}' for "
                        f"{row[1].strip()} (nutrient_id {nutrient_id})"
                    )

            nutrients.append({
                "nutrient_id": nutrient_id,
                "fediaf_nutrient_name": row[1].strip(),
                "unit": row[2].strip(),
                "value": value,
            })

    missing_ids = expected_ids - found_ids
    if missing_ids:
        raise ValueError(
            f"Template is missing {len(missing_ids)} nutrients. "
            f"Missing nutrient IDs: {sorted(missing_ids)}"
        )

    return {
        "supplement_name": supplement_name,
        "nutrients": nutrients,
    }


def get_nonzero_nutrients(template_data: dict) -> list[dict]:
    """
    Filter template data to only nutrients with non-zero values.

    Args:
        template_data: Parsed template data from read_template().

    Returns:
        List of nutrient dicts that have a non-None, non-zero value.
    """
    return [
        n for n in template_data["nutrients"]
        if n["value"] is not None and n["value"] != 0
    ]


def display_supplement_summary(template_data: dict) -> None:
    """
    Display a summary of the supplement template for user confirmation.

    Shows only nutrients with non-zero values in a formatted table.

    Args:
        template_data: Parsed template data from read_template().
    """
    supplement_name = template_data["supplement_name"]
    nonzero = get_nonzero_nutrients(template_data)

    print()
    print("=" * 60)
    print(f"SUPPLEMENT: {supplement_name}")
    print("=" * 60)
    print(f"  Nutrients with values: {len(nonzero)}")
    print(f"  Nutrients set to zero: {len(template_data['nutrients']) - len(nonzero)}")
    print()
    print(f"  {'Nutrient':<30} {'Value':>10} {'Unit':<6}")
    print(f"  {'-'*30} {'-'*10} {'-'*6}")
    for n in nonzero:
        print(f"  {n['fediaf_nutrient_name']:<30} {n['value']:>10.4f} {n['unit']:<6}")
    print()
