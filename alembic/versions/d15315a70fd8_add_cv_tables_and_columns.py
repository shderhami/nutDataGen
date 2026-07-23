"""add cv tables and columns

Nutrient-CV extraction pipeline (see Docs/nutrient_cv_extraction_plan.md).

Re-purposes ingredient_nutrients.coefficient_of_variation from the legacy
percent relative-SE to the cell's own MEASURED population CV (a fraction),
adds category_cv (the pooled/prior/supplement fallback, also a fraction) plus
cv_* provenance, adds ingredients.ingredient_class, and creates the audit
tables (cv_observations, cv_class, cv_pipeline_run, cv_cv_preimage).

Revision ID: d15315a70fd8
Revises: 22cd8e233ca8
Create Date: 2026-07-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d15315a70fd8"
down_revision: Union[str, Sequence[str], None] = "22cd8e233ca8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# cv_* provenance columns added to ingredient_nutrients (name, type)
_CV_COLUMNS = [
    ("category_cv", sa.Numeric(10, 6)),          # pooled/prior/supplement CV (fraction), every cell
    ("cv_tier", sa.String(30)),                  # sr28_se|fdc_range|component|class_pool|nutrient_prior|supplement
    ("cv_method", sa.String(30)),
    ("cv_backing_n", sa.Integer()),
    ("cv_effective_n", sa.Integer()),
    ("cv_confidence_tier", sa.String(10)),       # high|medium|low
    ("cv_calibration_flag", sa.Boolean()),       # NULL unless a twinned single-source cell
    ("cv_class_key", postgresql.JSONB()),        # (ingredient_class, nutrient_nbr, nutrient_class) of the pool used
    ("cv_method_inputs", postgresql.JSONB()),    # exact numbers used
    ("cv_config_sha256", sa.String(64)),
    ("cv_pipeline_version", sa.String(20)),
]


def upgrade() -> None:
    # 1. Re-purpose coefficient_of_variation: widen precision for small fractions.
    #    (Existing legacy percent-RSE values are left in place; cv_assign captures a
    #    pre-image and overwrites them with the measured population CV, a fraction.)
    op.alter_column(
        "ingredient_nutrients", "coefficient_of_variation",
        type_=sa.Numeric(10, 6), existing_type=sa.Numeric(10, 4), existing_nullable=True,
    )

    # 2. category_cv + cv_* provenance on ingredient_nutrients
    for name, coltype in _CV_COLUMNS:
        op.add_column("ingredient_nutrients", sa.Column(name, coltype, nullable=True))

    # 3. ingredients.ingredient_class + coarse backfill from the existing category
    op.add_column("ingredients", sa.Column("ingredient_class", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE ingredients SET ingredient_class = CASE category
            WHEN 'Muscle Meat'    THEN 'muscle'
            WHEN 'Organ Meat'     THEN 'organ'
            WHEN 'Fish & Seafood' THEN 'fish'
            WHEN 'Egg'            THEN 'egg'
            WHEN 'Dairy'          THEN 'dairy'
            WHEN 'Fish Oil'       THEN 'fat_oil'
            WHEN 'Plant Matter'   THEN 'plant'
            WHEN 'Supplement'     THEN 'supplement'
            WHEN 'Base'           THEN 'base'
            ELSE 'other'
        END
        """
    )

    # 4. cv_pipeline_run — per-run provenance + gate/sign-off
    op.create_table(
        "cv_pipeline_run",
        sa.Column("pipeline_version", sa.String(20), primary_key=True),
        sa.Column("config_sha256", sa.String(64), nullable=False),
        sa.Column("code_sha256", sa.String(64), nullable=False),
        sa.Column("dataset_shas", postgresql.JSONB(), nullable=False),
        sa.Column("gate_passed", sa.Boolean(), nullable=True),
        sa.Column("signed_off_by", sa.Text(), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("run_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # 5. cv_cv_preimage — targeted pre-image for a precise single-column revert
    op.create_table(
        "cv_cv_preimage",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("pipeline_version", sa.String(20), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("nutrient_id", sa.Integer(), nullable=False),
        sa.Column("old_coefficient_of_variation", sa.Numeric(15, 6), nullable=True),
        sa.Column("old_category_cv", sa.Numeric(15, 6), nullable=True),
        sa.Column("old_cv_json", postgresql.JSONB(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_cv_preimage_version", "cv_cv_preimage", ["pipeline_version"])

    # 6. cv_observations — raw per-source-food dispersion (immutable per run)
    op.create_table(
        "cv_observations",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("source_dataset", sa.String(20), nullable=False),
        sa.Column("source_dataset_version", sa.String(30), nullable=False),
        sa.Column("source_food_id", sa.String(20), nullable=False),
        sa.Column("source_food_desc", sa.Text(), nullable=True),
        sa.Column("prep_state", sa.String(12), nullable=True),
        sa.Column("nutrient_nbr", sa.Integer(), nullable=False),
        sa.Column("nutrient_name", sa.String(100), nullable=True),
        sa.Column("mean_value", sa.Numeric(15, 6), nullable=True),
        sa.Column("sd_value", sa.Numeric(15, 6), nullable=True),
        sa.Column("n_data_points", sa.Integer(), nullable=True),
        sa.Column("cv", sa.Numeric(10, 6), nullable=True),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("method_inputs", postgresql.JSONB(), nullable=True),
        sa.Column("derivation_code", sa.String(10), nullable=True),
        sa.Column("lineage_pair_id", sa.String(20), nullable=True),
        sa.Column("ingredient_class", sa.String(40), nullable=True),
        sa.Column("nutrient_class", sa.String(40), nullable=True),
        sa.Column("pipeline_version", sa.String(20), nullable=False),
        sa.Column("extracted_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("source_dataset", "source_food_id", "nutrient_nbr", name="uq_cv_obs_natural"),
    )
    op.create_index("idx_cv_obs_class_nut", "cv_observations", ["ingredient_class", "nutrient_nbr"])

    # 7. cv_class — pooled class CVs (nutrient_class NOT NULL so coarse rows can't collide on NULL)
    op.create_table(
        "cv_class",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("ingredient_class", sa.String(40), nullable=False),
        sa.Column("nutrient_nbr", sa.Integer(), nullable=False, server_default=sa.text("-1")),
        sa.Column("nutrient_class", sa.String(40), nullable=False),
        sa.Column("pooled_cv", sa.Numeric(10, 6), nullable=False),
        sa.Column("n_foods", sa.Integer(), nullable=False),
        sa.Column("pooling_method", sa.String(30), nullable=False),
        sa.Column("cv_p25", sa.Numeric(10, 6), nullable=True),
        sa.Column("cv_p75", sa.Numeric(10, 6), nullable=True),
        sa.Column("source_mix", postgresql.JSONB(), nullable=True),
        sa.Column("method_mix", postgresql.JSONB(), nullable=True),
        sa.Column("floor_clipped_frac", sa.Numeric(5, 4), nullable=True),
        sa.Column("is_literature_prior", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("prior_citation", sa.Text(), nullable=True),
        sa.Column("pipeline_version", sa.String(20), nullable=False),
        sa.Column("built_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(
        "uq_cv_class_key", "cv_class",
        ["ingredient_class", "nutrient_nbr", "nutrient_class"], unique=True,
    )
    # A real nutrient_nbr (> 0) maps to exactly one pool; coarse -1 rows legitimately vary nutrient_class.
    op.create_index(
        "uq_cv_class_fine", "cv_class",
        ["ingredient_class", "nutrient_nbr"], unique=True,
        postgresql_where=sa.text("nutrient_nbr <> -1"),
    )


def downgrade() -> None:
    op.drop_index("uq_cv_class_fine", table_name="cv_class")
    op.drop_index("uq_cv_class_key", table_name="cv_class")
    op.drop_table("cv_class")
    op.drop_index("idx_cv_obs_class_nut", table_name="cv_observations")
    op.drop_table("cv_observations")
    op.drop_index("idx_cv_preimage_version", table_name="cv_cv_preimage")
    op.drop_table("cv_cv_preimage")
    op.drop_table("cv_pipeline_run")
    op.drop_column("ingredients", "ingredient_class")
    for name, _ in reversed(_CV_COLUMNS):
        op.drop_column("ingredient_nutrients", name)
    op.alter_column(
        "ingredient_nutrients", "coefficient_of_variation",
        type_=sa.Numeric(10, 4), existing_type=sa.Numeric(10, 6), existing_nullable=True,
    )
