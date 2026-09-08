"""widen chk_ingredient_protein_species to admit egg

Revision ID: d49d10b298da
Revises: 8f2a41c7b6de
Create Date: 2026-09-08

Records a constraint change applied to the shared database out-of-band by the
FORMULATOR repo (recipeFormulator), whose migration
scripts/migrate_recipe_mgmt_v17.py owns it: chk_ingredient_protein_species now
admits 'egg', so egg gets its own protein icon on The Lils instead of riding on
'chicken' (Lils envelope schema hash 09a2a9f5f645cc22 -> 6f2a9a665dd54b7d).
database.VALID_PROTEIN_SPECIES and user_interaction.VALID_PROTEIN_SPECIES carry
the matching Python copy (tests/test_constant_sync.py keeps them aligned).

Declared here so `alembic upgrade head` on a fresh or restored database never
reinstates the nine-value CHECK from c2cf3be1c2cd. Idempotent (DROP IF EXISTS,
then ADD), so it converges with the formulator's v17 in either order and is a
no-op where v17 already ran.

Note: downgrade re-asserts the nine-value CHECK, which Postgres refuses while
any row is tagged 'egg'. Retag those rows first (the formulator's
rollback_recipe_mgmt_v17.py has the same guard).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "d49d10b298da"
down_revision: Union[str, Sequence[str], None] = "8f2a41c7b6de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VALID_PROTEIN_SPECIES = "chicken, beef, fish, turkey, lamb, pork, duck, rabbit, mussel, egg"
PREVIOUS_PROTEIN_SPECIES = "chicken, beef, fish, turkey, lamb, pork, duck, rabbit, mussel"


def _in_list(values: str) -> str:
    """Render a comma-separated string as a SQL IN (...) list of literals."""
    return ", ".join(repr(v) for v in (s.strip() for s in values.split(",")))


def _assert_protein_species(values: str) -> None:
    op.execute(
        "ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_protein_species"
    )
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_ingredient_protein_species "
        "CHECK (protein_species IS NULL OR protein_species IN "
        f"({_in_list(values)}))"
    )


def upgrade() -> None:
    """(Re)assert the protein_species CHECK with egg admitted."""
    _assert_protein_species(VALID_PROTEIN_SPECIES)


def downgrade() -> None:
    """Restore the nine-value CHECK.

    Refuses with a clear message while any row is tagged 'egg' (Postgres would
    reject the ADD CONSTRAINT anyway, but with a raw CheckViolation); mirrors the
    guard in the formulator's rollback_recipe_mgmt_v17.py.
    """
    egg_rows = op.get_bind().execute(
        text("SELECT COUNT(*) FROM ingredients WHERE protein_species = 'egg'")
    ).scalar()
    if egg_rows:
        raise RuntimeError(
            f"{egg_rows} ingredient row(s) have protein_species='egg'; downgrade "
            "would violate the nine-value CHECK. Retag those rows first."
        )
    _assert_protein_species(PREVIOUS_PROTEIN_SPECIES)
