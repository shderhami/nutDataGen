"""add boiled-drained to cooking_method

Revision ID: 46134add8717
Revises: 95dccfa395eb
Create Date: 2026-05-05 14:20:43.974706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46134add8717'
down_revision: Union[str, Sequence[str], None] = '95dccfa395eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT chk_cooking_method")
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_cooking_method "
        "CHECK (cooking_method IN ('raw', 'cooked', 'boiled-drained'))"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT chk_cooking_method")
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_cooking_method "
        "CHECK (cooking_method IN ('raw', 'cooked'))"
    )
