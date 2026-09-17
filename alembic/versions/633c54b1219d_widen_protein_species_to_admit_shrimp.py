"""widen chk_ingredient_protein_species to admit shrimp

Revision ID: 633c54b1219d
Revises: 04640a289c93
Create Date: 2026-09-17

Adds 'shrimp' to the protein_species CHECK for the shrimp add (food
'whiteleg shrimp farmed raw'). The mussel precedent already gives one
shellfish its own species; shrimp-as-'fish' would wrongly couple it to the
formulator's fish rotation/advisory logic (Shahab approved the new species
2026-09-17). Unlike d49d10b298da (egg), this constraint change originates in
THIS repo - the FORMULATOR repo must still learn 'shrimp' (icon + any
species logic) on its side.

database.VALID_PROTEIN_SPECIES and user_interaction.VALID_PROTEIN_SPECIES
carry the matching Python copies (tests/test_constant_sync.py keeps them
aligned). Idempotent (DROP IF EXISTS, then ADD), converging with any
out-of-band assertion in either order.

Note: downgrade re-asserts the ten-value CHECK, which Postgres refuses while
any row is tagged 'shrimp'. Retag those rows first (same guard style as the
egg migration).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "633c54b1219d"
down_revision: Union[str, Sequence[str], None] = "04640a289c93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VALID_PROTEIN_SPECIES = (
    "chicken, beef, fish, turkey, lamb, pork, duck, rabbit, mussel, egg, shrimp"
)
PREVIOUS_PROTEIN_SPECIES = (
    "chicken, beef, fish, turkey, lamb, pork, duck, rabbit, mussel, egg"
)


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
    """(Re)assert the protein_species CHECK with shrimp admitted."""
    _assert_protein_species(VALID_PROTEIN_SPECIES)


def downgrade() -> None:
    """Restore the ten-value CHECK.

    Refuses with a clear message while any row is tagged 'shrimp' (Postgres
    would reject the ADD CONSTRAINT anyway, but with a raw CheckViolation).
    """
    shrimp_rows = op.get_bind().execute(
        text("SELECT COUNT(*) FROM ingredients WHERE protein_species = 'shrimp'")
    ).scalar()
    if shrimp_rows:
        raise RuntimeError(
            f"{shrimp_rows} ingredient row(s) have protein_species='shrimp'; "
            "downgrade would violate the ten-value CHECK. Retag those rows first."
        )
    _assert_protein_species(PREVIOUS_PROTEIN_SPECIES)
