"""add none to ingredient source for category-less ingredients

Revision ID: 22cd8e233ca8
Revises: 3d4ab9525626
Create Date: 2026-05-22 17:01:09.395694

Adds 'none' to chk_ingredient_source so ingredients without a meaningful
purchase channel (e.g. water) can have source explicitly set to 'none'
(the column is NOT NULL).

chk_ingredient_supplement_url is unaffected: it still requires
source IN ('online','homemade') for supplement_info to be set, so 'none'
implicitly disallows supplement_info, which is the desired behavior.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '22cd8e233ca8'
down_revision: Union[str, Sequence[str], None] = '3d4ab9525626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_SOURCES = ("grocery", "butcher", "online", "homemade", "none")
OLD_SOURCES = ("grocery", "butcher", "online", "homemade")


def _in_list(values: tuple[str, ...]) -> str:
    return ", ".join(repr(v) for v in values)


def upgrade() -> None:
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_source")
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_ingredient_source "
        f"CHECK (source IN ({_in_list(NEW_SOURCES)}))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_source")
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_ingredient_source "
        f"CHECK (source IN ({_in_list(OLD_SOURCES)}))"
    )
