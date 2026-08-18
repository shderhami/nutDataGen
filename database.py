"""
Database Operations for Nutrition Data.

PostgreSQL CRUD operations for the ingredients and ingredient_nutrients tables.
"""
import math
from datetime import date
from typing import Optional, TypedDict

from db_connection import get_db
from fediaf_nutrients import canonical_unit, fediaf_unit_factor


class NutrientRecord(TypedDict, total=False):
    """Type definition for a nutrient record ready for database insertion."""

    food_name: str
    food_id: int
    nutrient_id: Optional[int]
    fediaf_nutrient_name: str
    usda_nutrient_name: Optional[str]
    unit: str
    value: Optional[float]
    source: Optional[str]
    num_samples: Optional[int]
    min_value: Optional[float]
    max_value: Optional[float]
    median_value: Optional[float]
    year_acquired: Optional[str]
    derivation_description: Optional[str]
    estimated_se: Optional[float]
    confidence_interval_lower: Optional[float]
    confidence_interval_upper: Optional[float]
    coefficient_of_variation: Optional[float]
    range_uncertainty: Optional[float]
    ai_recommendation: Optional[str]
    ai_justification: Optional[str]
    ai_source: Optional[str]
    ai_confidence: Optional[str]
    ai_model: Optional[str]
    last_updated: Optional[str]
    comment: Optional[str]


# Columns for ingredient_nutrients INSERT
_NUTRIENT_COLUMNS = [
    "food_name", "food_id", "nutrient_id", "fediaf_nutrient_name", "usda_nutrient_name",
    "unit", "value", "source", "num_samples", "min_value", "max_value",
    "median_value", "year_acquired", "derivation_description",
    "estimated_se", "confidence_interval_lower", "confidence_interval_upper",
    "coefficient_of_variation", "range_uncertainty",
    "ai_recommendation", "ai_justification", "ai_source", "ai_confidence", "ai_model",
    "last_updated", "comment",
]


def initialize_database() -> None:
    """Verify database connection and schema are ready."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT 1 FROM ingredients LIMIT 0")
        cur.execute("SELECT 1 FROM ingredient_nutrients LIMIT 0")


def food_exists(food_id: int) -> bool:
    """Check if a food_id exists in the ingredients table."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT 1 FROM ingredients WHERE food_id = %s", (food_id,))
        return cur.fetchone() is not None


def food_exists_by_name(food_name: str) -> Optional[int]:
    """Check if food_name exists (case-insensitive). Return food_id if found."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT food_id FROM ingredients WHERE LOWER(food_name) = LOWER(%s)",
            (food_name,),
        )
        row = cur.fetchone()
        return row["food_id"] if row else None


VALID_BASE_UNITS = ("g", "ml", "tsp", "tbsp", "drop", "capsule", "tablet", "unit")

VALID_CATEGORIES = (
    "Muscle Meat", "Organ Meat", "Fish & Seafood", "Egg",
    "Dairy", "Fish Oil", "Plant Matter", "Supplement", "Base",
)

VALID_COOKING_METHODS = ("raw", "cooked", "boiled-drained")

VALID_SOURCES = ("grocery", "butcher", "online", "homemade", "none")

SUPPLEMENT_INFO_SOURCES = ("online", "homemade")

VALID_PROTEIN_SPECIES = (
    "chicken", "beef", "fish", "turkey",
    "lamb", "pork", "duck", "rabbit", "mussel",
)

# category -> ingredient_class, mirroring the backfill in alembic revision
# d15315a70fd8. ingredient_class drives the CV pipeline's pool lookup, so a row
# left NULL falls to 'other' (no pool) and every cell lands on the Tier-5 prior.
CATEGORY_TO_INGREDIENT_CLASS = {
    "Muscle Meat": "muscle",
    "Organ Meat": "organ",
    "Fish & Seafood": "fish",
    "Egg": "egg",
    "Dairy": "dairy",
    "Fish Oil": "fat_oil",
    "Plant Matter": "plant",
    "Supplement": "supplement",
    "Base": "base",
}

# Categories where is_corrector is meaningful — the CV ladder only consults the flag
# for these (mirrors cv_config.SUPPLEMENT_CATEGORIES; keep the two in sync). Setting it
# on any other category would be silently ignored by resolve_cv.
CORRECTOR_CATEGORIES = ("Supplement", "Fish Oil")


def ingredient_class_for(category: str) -> str:
    """CV-pipeline ingredient_class for a category."""
    return CATEGORY_TO_INGREDIENT_CLASS.get(category, "other")


def add_ingredient(
    food_name: str,
    category: str,
    base_unit: str,
    portion_qty: float,
    grams_per_unit: float,
    me_kcal_per_unit: Optional[float] = None,
    sr_legacy_fdc_id: Optional[int] = None,
    foundation_fdc_id: Optional[int] = None,
    cooking_method: Optional[str] = None,
    price_per_unit: float = 0.0,
    currency: str = "USD",
    source: str = "grocery",
    amazon_url: Optional[str] = None,
    chewy_url: Optional[str] = None,
    supplement_info: Optional[str] = None,
    protein_species: Optional[str] = None,
    display_name: Optional[str] = None,
    is_nutritional_additive: bool = False,
    is_corrector: bool = False,
) -> int:
    """Insert a new ingredient and return the auto-generated food_id.

    ingredient_class is derived from category (CV-pipeline pool key).
    is_nutritional_additive / is_corrector are read by the formulator: the former
    drives its legal-max limits, the latter selects the delivered-spec CV in
    cv_assign. They are meaningful only for CORRECTOR_CATEGORIES rows.
    """
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. "
            f"Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    if base_unit not in VALID_BASE_UNITS:
        raise ValueError(
            f"Invalid base_unit '{base_unit}'. "
            f"Must be one of: {', '.join(VALID_BASE_UNITS)}"
        )
    if cooking_method is not None and cooking_method not in VALID_COOKING_METHODS:
        raise ValueError(
            f"Invalid cooking_method '{cooking_method}'. "
            f"Must be one of: {', '.join(VALID_COOKING_METHODS)} (or None)"
        )
    if source not in VALID_SOURCES:
        raise ValueError(
            f"Invalid source '{source}'. "
            f"Must be one of: {', '.join(VALID_SOURCES)}"
        )
    if protein_species is not None and protein_species not in VALID_PROTEIN_SPECIES:
        raise ValueError(
            f"Invalid protein_species '{protein_species}'. "
            f"Must be one of: {', '.join(VALID_PROTEIN_SPECIES)} (or None)"
        )
    if supplement_info is not None and source not in SUPPLEMENT_INFO_SOURCES:
        raise ValueError(
            "supplement_info can only be set when source is one of: "
            f"{', '.join(SUPPLEMENT_INFO_SOURCES)}"
        )
    if is_corrector and category not in CORRECTOR_CATEGORIES:
        raise ValueError(
            f"is_corrector is only valid for category in "
            f"{', '.join(CORRECTOR_CATEGORIES)}, not '{category}'"
        )
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingredients
                (food_name, category, base_unit, portion_qty,
                 grams_per_unit, me_kcal_per_unit, sr_legacy_fdc_id,
                 foundation_fdc_id, cooking_method, price_per_unit, currency,
                 source, amazon_url, chewy_url, supplement_info,
                 protein_species, display_name, ingredient_class,
                 is_nutritional_additive, is_corrector)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING food_id
            """,
            (food_name, category, base_unit, portion_qty, grams_per_unit,
             me_kcal_per_unit, sr_legacy_fdc_id, foundation_fdc_id,
             cooking_method, price_per_unit, currency,
             source, amazon_url, chewy_url, supplement_info,
             protein_species, display_name, ingredient_class_for(category),
             is_nutritional_additive, is_corrector),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("Failed to insert ingredient")
        return int(row["food_id"])


def add_food_nutrients(food_nutrients: list[NutrientRecord]) -> int:
    """Insert nutrient records for a food. Returns count of rows inserted."""
    if not food_nutrients:
        return 0

    db = get_db()
    placeholders = ", ".join(["%s"] * len(_NUTRIENT_COLUMNS))
    col_names = ", ".join(_NUTRIENT_COLUMNS)
    sql = f"""
        INSERT INTO ingredient_nutrients ({col_names})
        VALUES ({placeholders})
        ON CONFLICT (food_id, nutrient_id) DO NOTHING
    """

    with db.cursor() as cur:
        rows = [
            tuple(record.get(col) for col in _NUTRIENT_COLUMNS)
            for record in food_nutrients
        ]
        cur.executemany(sql, rows)
        return len(food_nutrients)


def get_food_by_id(food_id: int) -> list[dict]:
    """Get all nutrient rows for a specific food."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT * FROM ingredient_nutrients WHERE food_id = %s",
            (food_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_ingredient(food_id: int) -> Optional[dict]:
    """Get ingredient details by food_id."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM ingredients WHERE food_id = %s", (food_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_food_ids() -> list[int]:
    """Get all food_ids from ingredients table, sorted."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT food_id FROM ingredients ORDER BY food_id")
        return [int(row["food_id"]) for row in cur.fetchall()]


class IngredientInUseError(RuntimeError):
    """Raised when an ingredient cannot be deleted because a recipe references it."""


def delete_food(food_id: int) -> int:
    """Delete an ingredient and all its nutrients. Returns nutrient rows deleted.

    The formulator's recipe_ingredients / ingredient_prices tables FK into
    ingredients, so a referenced food cannot be removed. Check first and raise a
    named error rather than letting the FK violation surface as a raw psycopg2
    error mid-transaction.
    """
    db = get_db()
    with db.cursor() as cur:
        # recipe_ingredients is formulator-owned and absent from a nutDataGen-only
        # database, so probe before referencing it (a missing table would otherwise
        # abort the statement at plan time).
        refs = []
        for table, column in (("recipe_ingredients", "food_id"),
                              ("ingredient_prices", "ingredient_id")):
            cur.execute("SELECT to_regclass(%s) AS t", (table,))
            row = cur.fetchone()
            if row is None or row["t"] is None:
                continue
            cur.execute(f"SELECT count(*) AS n FROM {table} WHERE {column} = %s", (food_id,))
            row = cur.fetchone()
            if row and int(row["n"]):
                refs.append(f"{row['n']} {table} row(s)")
        if refs:
            raise IngredientInUseError(
                f"Cannot delete food_id={food_id}: referenced by {', '.join(refs)}. "
                "Remove those references first."
            )
        cur.execute(
            "DELETE FROM ingredient_nutrients WHERE food_id = %s", (food_id,)
        )
        nutrient_count: int = cur.rowcount
        cur.execute("DELETE FROM ingredients WHERE food_id = %s", (food_id,))
        return nutrient_count


def update_nutrient(
    food_id: int, nutrient_id: int, updates: dict
) -> bool:
    """Update specific nutrient fields for a food. Appends to comment field."""
    if not updates:
        return False

    db = get_db()
    updates = dict(updates)  # avoid mutating caller's dict
    today = str(date.today())

    with db.cursor() as cur:
        # Handle comment appending specially
        if "comment" in updates:
            comment_val = updates.pop("comment")
            cur.execute(
                """UPDATE ingredient_nutrients
                   SET comment = CASE
                       WHEN comment IS NOT NULL AND comment != ''
                       THEN comment || '; ' || %s
                       ELSE %s
                   END,
                   last_updated = %s
                   WHERE food_id = %s AND nutrient_id = %s""",
                (comment_val, comment_val, today, food_id, nutrient_id),
            )

        if updates:
            set_clauses = ", ".join(f"{k} = %s" for k in updates)
            values = list(updates.values()) + [today, food_id, nutrient_id]
            cur.execute(
                f"""UPDATE ingredient_nutrients
                    SET {set_clauses}, last_updated = %s
                    WHERE food_id = %s AND nutrient_id = %s""",
                values,
            )
            return cur.rowcount > 0

    return True


def validate_nutrient_completeness(food_id: int, expected_count: int = 52) -> bool:
    """Validate that all required nutrients exist for a food in the database."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) as cnt FROM ingredient_nutrients WHERE food_id = %s",
            (food_id,),
        )
        row = cur.fetchone()
        return row is not None and int(row["cnt"]) == expected_count


# =============================================================================
# Statistics Calculation (pure computation, unchanged from CSV version)
# =============================================================================


def calculate_statistics(
    value: Optional[float],
    standard_error: Optional[float],
    num_samples: Optional[int],
    min_value: Optional[float],
    max_value: Optional[float],
) -> dict[str, Optional[float]]:
    """
    Calculate statistical measures for error estimation.

    When standard_error is not provided by the API (common for USDA data),
    it is estimated from the range using: SD ~ Range/4, SE = SD/sqrt(n).
    """
    result: dict[str, Optional[float]] = {
        "confidence_interval_lower": None,
        "confidence_interval_upper": None,
        "coefficient_of_variation": None,
        "range_uncertainty": None,
        "estimated_se": None,
    }

    if value is None:
        return result

    se_to_use = standard_error

    if (
        se_to_use is None
        and min_value is not None
        and max_value is not None
        and max_value > min_value
    ):
        range_val = max_value - min_value
        estimated_sd = range_val / 4.0

        if num_samples and num_samples > 1:
            se_to_use = estimated_sd / math.sqrt(num_samples)
            result["estimated_se"] = round(se_to_use, 4)
        elif num_samples == 1:
            se_to_use = estimated_sd
            result["estimated_se"] = round(se_to_use, 4)

    if se_to_use is not None and se_to_use > 0:
        if num_samples and num_samples > 1:
            t_value = 2.0 if num_samples < 30 else 1.96
        else:
            t_value = 1.96

        margin = t_value * se_to_use
        result["confidence_interval_lower"] = round(value - margin, 4)
        result["confidence_interval_upper"] = round(value + margin, 4)

        # coefficient_of_variation is NO LONGER written here. It was a relative
        # standard error (SE/value*100, a percent) — the wrong quantity. The CV
        # pipeline (resolve_cv / cv_assign) now owns this column and writes the
        # correct POPULATION CV as a fraction. Left as None (see result init).

    if min_value is not None and max_value is not None and max_value > min_value:
        range_val = max_value - min_value
        if value != 0:
            range_uncertainty = (range_val / (2 * value)) * 100
            result["range_uncertainty"] = round(range_uncertainty, 2)

    return result


# =============================================================================
# Record Creation
# =============================================================================


def _format_number(v: float) -> str:
    """Trailing-zero-trimmed decimal rendering for unit-conversion comments."""
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s or "0"


def create_nutrient_record(
    food_name: str,
    food_id: int,
    nutrient_id: Optional[int],
    fediaf_nutrient_name: str,
    usda_nutrient_name: Optional[str],
    unit: str,
    value: Optional[float],
    source: str,
    comment: Optional[str] = None,
    # USDA metadata
    num_samples: Optional[int] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    median_value: Optional[float] = None,
    year_acquired: Optional[str] = None,
    derivation_description: Optional[str] = None,
    # AI validation
    ai_recommendation: Optional[str] = None,
    ai_justification: Optional[str] = None,
    ai_source: Optional[str] = None,
    ai_confidence: Optional[str] = None,
    ai_model: Optional[str] = None,
) -> NutrientRecord:
    """Create a nutrient record dict ready for database insertion.

    The record is stored in the nutrient's FEDIAF unit: a payload unit that
    differs (USDA vitamin A µg RAE, vitamin E mg alpha-tocopherol) is converted
    here, before statistics are derived, so value and every stats column share
    one unit (min/max bracket rule) and each nutrient_id keeps a single unit
    across ingredient_nutrients.
    """
    target_unit, factor = fediaf_unit_factor(nutrient_id, unit)
    if factor != 1.0:
        if value is not None:
            converted = round(value * factor, 6)
            note = (
                f"Unit normalized: {_format_number(value)} {canonical_unit(unit)} -> "
                f"{_format_number(converted)} {target_unit} "
                f"(x{factor:g}, FEDIAF platform unit)"
            )
            comment = f"{comment}; {note}" if comment else note
            value = converted
        min_value = round(min_value * factor, 6) if min_value is not None else None
        max_value = round(max_value * factor, 6) if max_value is not None else None
        median_value = round(median_value * factor, 6) if median_value is not None else None
    unit = target_unit

    stats = calculate_statistics(
        value=value,
        standard_error=None,
        num_samples=num_samples,
        min_value=min_value,
        max_value=max_value,
    )

    return NutrientRecord(
        food_name=food_name,
        food_id=food_id,
        nutrient_id=nutrient_id,
        fediaf_nutrient_name=fediaf_nutrient_name,
        usda_nutrient_name=usda_nutrient_name,
        unit=unit,
        value=value,
        source=source,
        num_samples=num_samples,
        min_value=min_value,
        max_value=max_value,
        median_value=median_value,
        year_acquired=year_acquired,
        derivation_description=derivation_description,
        estimated_se=stats["estimated_se"],
        confidence_interval_lower=stats["confidence_interval_lower"],
        confidence_interval_upper=stats["confidence_interval_upper"],
        coefficient_of_variation=stats["coefficient_of_variation"],
        range_uncertainty=stats["range_uncertainty"],
        ai_recommendation=ai_recommendation,
        ai_justification=ai_justification,
        ai_source=ai_source,
        ai_confidence=ai_confidence,
        ai_model=ai_model,
        last_updated=str(date.today()),
        comment=comment,
    )
