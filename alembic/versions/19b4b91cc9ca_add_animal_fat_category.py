"""add animal fat category

Revision ID: 19b4b91cc9ca
Revises: 8f2a41c7b6de
Create Date: 2026-09-11 12:22:44.209932

Adds 'Animal Fat' to the ingredients.category CHECK constraint and
recategorizes beef tallow (food_id 10064) out of 'Fish Oil', whose
category was triggering the formulator's fish-oil PUFA advisory on a
terrestrial rendered fat. Scope rule (Docs by convention): 'Animal Fat'
covers rendered/separated terrestrial-animal fats (tallow, lard, duck
fat, ghee); skin and other tissues stay in their meat categories, and
marine oils stay 'Fish Oil' (that category's n-3 logic is the point).

The paired app-level lists (database.VALID_CATEGORIES,
CATEGORY_TO_INGREDIENT_CLASS -> 'fat_oil', CORRECTOR_CATEGORIES) and
cv_config.SUPPLEMENT_CATEGORIES (delivered-floor CV pre-emption kept
identical for tallow; PIPELINE_VERSION cv-v8.7) change in the same
commit. The formulator repo must learn the new category separately.

Idempotent in the c2cf3be1c2cd style: constraint dropped IF EXISTS and
re-added, so it repairs a stale test database and no-ops correctly on
re-runs.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '19b4b91cc9ca'
down_revision: Union[str, Sequence[str], None] = '8f2a41c7b6de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD = ("'Muscle Meat', 'Organ Meat', 'Fish & Seafood', 'Egg', 'Dairy', "
        "'Fish Oil', 'Plant Matter', 'Supplement', 'Base'")
_NEW = _OLD + ", 'Animal Fat'"


def upgrade() -> None:
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_category")
    op.execute(
        f"ALTER TABLE ingredients ADD CONSTRAINT chk_category "
        f"CHECK (category IN ({_NEW}))"
    )
    op.execute(
        "UPDATE ingredients SET category = 'Animal Fat' "
        "WHERE food_id = 10064 AND category = 'Fish Oil'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE ingredients SET category = 'Fish Oil' "
        "WHERE food_id = 10064 AND category = 'Animal Fat'"
    )
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_category")
    op.execute(
        f"ALTER TABLE ingredients ADD CONSTRAINT chk_category "
        f"CHECK (category IN ({_OLD}))"
    )
