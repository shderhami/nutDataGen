"""catch up ingredients is_nutritional_additive and is_corrector flags

Revision ID: 8f2a41c7b6de
Revises: d15315a70fd8
Create Date: 2026-08-05

Records two ingredients columns that were applied to the shared database
out-of-band by the FORMULATOR repo (recipeFormulator), whose migrations
scripts/migrate_recipe_mgmt_v12.py and v14.py own them:

  is_nutritional_additive  BOOLEAN NOT NULL DEFAULT false  (v12)
      Drives the formulator's legal-max (nutritional additive) limits.
  is_corrector             BOOLEAN NOT NULL DEFAULT false  (v14)
      Marks a single-nutrient corrector supplement. Read by this repo's CV
      pipeline (cv_assign -> resolve_cv) to assign the delivered-spec CV.

Declared here so `alembic upgrade head` on a fresh database reproduces the live
schema — without them, database.add_ingredient's INSERT and cv_assign's JOIN
both fail with UndefinedColumn. The formulator remains the semantic owner and
backfills existing rows; this migration only guarantees the columns exist.

Idempotent (ADD COLUMN IF NOT EXISTS), so it is a no-op on the live and test
databases, where both columns are already present.

Note: downgrade drops both columns, which would break the formulator. Only
downgrade a database this repo owns exclusively.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8f2a41c7b6de"
down_revision: Union[str, Sequence[str], None] = "d15315a70fd8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS "
        "is_nutritional_additive BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS "
        "is_corrector BOOLEAN NOT NULL DEFAULT false"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS is_corrector")
    op.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS is_nutritional_additive")
