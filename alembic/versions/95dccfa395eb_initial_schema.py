"""initial_schema

Revision ID: 95dccfa395eb
Revises:
Create Date: 2026-02-10

Drop and recreate ingredients + ingredient_nutrients with correct column order.
Leaves every other table in the shared database untouched (as of writing:
cooking_retention_factors, nutrient_limits, standard_life_stage_map and the
recipe_* tables, all owned by the formulator repo; fediaf_requirements and
unit_conversions existed then and have since been dropped by the formulator).

WARNING: the DROP ... CASCADE below severs the formulator's FKs into
ingredients (recipe_ingredients, ingredient_prices). Never re-run this against
the shared database.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '95dccfa395eb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VALID_BASE_UNITS = "g, ml, tsp, tbsp, drop, capsule, tablet, unit"
VALID_CATEGORIES = "Muscle Meat, Organ Meat, Fish & Seafood, Egg, Dairy, Fish Oil, Plant Matter, Supplement"


def upgrade() -> None:
    """Drop and recreate ingredients, ingredient_nutrients, ingredient_prices."""
    # Drop dependent tables first (FK order)
    op.execute("DROP TABLE IF EXISTS ingredient_nutrients CASCADE")
    op.execute("DROP TABLE IF EXISTS ingredient_prices CASCADE")
    op.execute("DROP TABLE IF EXISTS ingredients CASCADE")
    op.execute("DROP SEQUENCE IF EXISTS ingredients_food_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS ingredient_nutrients_id_seq")

    # --- ingredients ---
    op.execute("CREATE SEQUENCE ingredients_food_id_seq START WITH 10001")

    op.create_table(
        "ingredients",
        sa.Column("food_id", sa.Integer(), nullable=False,
                  server_default=sa.text("nextval('ingredients_food_id_seq')")),
        sa.Column("food_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("base_unit", sa.String(20), nullable=False),
        sa.Column("portion_qty", sa.Numeric(10, 4), nullable=False),
        sa.Column("grams_per_unit", sa.Numeric(10, 4), nullable=False),
        sa.Column("me_kcal_per_unit", sa.Numeric(10, 4), nullable=True),
        sa.Column("sr_legacy_fdc_id", sa.Integer(), nullable=True),
        sa.Column("foundation_fdc_id", sa.Integer(), nullable=True),
        sa.Column("cooking_method", sa.String(20), nullable=True),
        sa.Column("price_per_unit", sa.Numeric(10, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True, server_default="USD"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("food_id"),
    )

    # Enforce valid base_unit values
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_base_unit "
        f"CHECK (base_unit IN ({', '.join(repr(u) for u in VALID_BASE_UNITS.split(', '))}))"
    )

    # Enforce valid category values
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_category "
        f"CHECK (category IN ({', '.join(repr(c) for c in VALID_CATEGORIES.split(', '))}))"
    )

    # Enforce valid cooking_method values (NULL allowed)
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_cooking_method "
        "CHECK (cooking_method IN ('raw', 'cooked'))"
    )

    op.execute("ALTER SEQUENCE ingredients_food_id_seq OWNED BY ingredients.food_id")

    # --- ingredient_nutrients ---
    op.create_table(
        "ingredient_nutrients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("food_name", sa.String(255), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("nutrient_id", sa.Integer(), nullable=False),
        sa.Column("fediaf_nutrient_name", sa.String(100), nullable=False),
        sa.Column("usda_nutrient_name", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("value", sa.Numeric(15, 6), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("num_samples", sa.Integer(), nullable=True),
        sa.Column("min_value", sa.Numeric(15, 6), nullable=True),
        sa.Column("max_value", sa.Numeric(15, 6), nullable=True),
        sa.Column("median_value", sa.Numeric(15, 6), nullable=True),
        sa.Column("year_acquired", sa.String(10), nullable=True),
        sa.Column("derivation_description", sa.String(255), nullable=True),
        sa.Column("estimated_se", sa.Numeric(15, 6), nullable=True),
        sa.Column("confidence_interval_lower", sa.Numeric(15, 6), nullable=True),
        sa.Column("confidence_interval_upper", sa.Numeric(15, 6), nullable=True),
        sa.Column("coefficient_of_variation", sa.Numeric(10, 4), nullable=True),
        sa.Column("range_uncertainty", sa.Numeric(10, 4), nullable=True),
        sa.Column("ai_recommendation", sa.String(50), nullable=True),
        sa.Column("ai_justification", sa.Text(), nullable=True),
        sa.Column("ai_source", sa.Text(), nullable=True),
        sa.Column("ai_confidence", sa.String(20), nullable=True),
        sa.Column("ai_model", sa.String(50), nullable=True),
        sa.Column("last_updated", sa.Date(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["food_id"], ["ingredients.food_id"]),
        sa.UniqueConstraint("food_id", "nutrient_id"),
    )

    op.create_index("idx_ingredient_nutrients_food_id", "ingredient_nutrients", ["food_id"])
    op.create_index("idx_ingredient_nutrients_fediaf_name", "ingredient_nutrients", ["fediaf_nutrient_name"])

    # --- ingredient_prices ---
    op.create_table(
        "ingredient_prices",
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("price_per_unit", sa.Numeric(10, 4), nullable=False),
        sa.Column("price_unit", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True, server_default="USD"),
        sa.Column("last_updated", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("ingredient_id"),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.food_id"]),
    )


def downgrade() -> None:
    """Cannot downgrade initial schema — would need the original DDL."""
    raise NotImplementedError("Cannot downgrade past initial schema")
