"""add Base category for water and other category-less ingredients

Revision ID: 3d4ab9525626
Revises: c2cf3be1c2cd
Create Date: 2026-05-22 16:51:40.690521

Adds 'Base' to the chk_category allowed list so foods that don't fit any
of the existing 8 categories (e.g. water) can be recorded.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '3d4ab9525626'
down_revision: Union[str, Sequence[str], None] = 'c2cf3be1c2cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_CATEGORIES = (
    "Muscle Meat", "Organ Meat", "Fish & Seafood", "Egg",
    "Dairy", "Fish Oil", "Plant Matter", "Supplement", "Base",
)

OLD_CATEGORIES = (
    "Muscle Meat", "Organ Meat", "Fish & Seafood", "Egg",
    "Dairy", "Fish Oil", "Plant Matter", "Supplement",
)


def _in_list(values: tuple[str, ...]) -> str:
    return ", ".join(repr(v) for v in values)


def upgrade() -> None:
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_category")
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_category "
        f"CHECK (category IN ({_in_list(NEW_CATEGORIES)}))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_category")
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_category "
        f"CHECK (category IN ({_in_list(OLD_CATEGORIES)}))"
    )
