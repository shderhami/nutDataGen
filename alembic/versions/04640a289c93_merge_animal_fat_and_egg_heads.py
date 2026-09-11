"""merge animal fat and egg heads

Revision ID: 04640a289c93
Revises: 19b4b91cc9ca, d49d10b298da
Create Date: 2026-09-11 12:30:14.428904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04640a289c93'
down_revision: Union[str, Sequence[str], None] = ('19b4b91cc9ca', 'd49d10b298da')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
