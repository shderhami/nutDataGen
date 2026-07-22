"""catch up ingredients source, urls, supplement, protein, display_name columns and constraints

Revision ID: c2cf3be1c2cd
Revises: 46134add8717
Create Date: 2026-05-14 12:57:45.573012

Records schema that was applied to the live database out-of-band: the
source / amazon_url / chewy_url / supplement_info / protein_species /
display_name columns on ingredients, plus the three check constraints
governing them (the protein_species list includes 'mussel').

Written to be idempotent so it is a no-op on the live database (already
applied), repairs the test database (which carries stale constraint
values), and builds the correct table on a fresh database:
  - columns use ADD COLUMN IF NOT EXISTS
  - constraints are dropped IF EXISTS then re-added, so a stale definition
    is replaced with the current one.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c2cf3be1c2cd'
down_revision: Union[str, Sequence[str], None] = '46134add8717'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VALID_SOURCES = "grocery, butcher, online, homemade"
SUPPLEMENT_INFO_SOURCES = "online, homemade"
VALID_PROTEIN_SPECIES = "chicken, beef, fish, turkey, lamb, pork, duck, rabbit, mussel"


def _in_list(values: str) -> str:
    """Render a comma-separated string as a SQL IN (...) list of literals."""
    return ", ".join(repr(v) for v in (s.strip() for s in values.split(",")))


def upgrade() -> None:
    """Add ingredients columns and (re)assert their check constraints."""
    op.execute(
        "ALTER TABLE ingredients "
        "ADD COLUMN IF NOT EXISTS source VARCHAR(20) NOT NULL DEFAULT 'grocery'"
    )
    op.execute(
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS amazon_url VARCHAR(2000)"
    )
    op.execute(
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS chewy_url VARCHAR(2000)"
    )
    op.execute(
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS supplement_info TEXT"
    )
    op.execute(
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS protein_species VARCHAR(20)"
    )
    op.execute(
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS display_name VARCHAR(200)"
    )

    op.execute("ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_source")
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_ingredient_source "
        f"CHECK (source IN ({_in_list(VALID_SOURCES)}))"
    )

    op.execute(
        "ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_supplement_url"
    )
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_ingredient_supplement_url "
        f"CHECK (source IN ({_in_list(SUPPLEMENT_INFO_SOURCES)}) OR supplement_info IS NULL)"
    )

    op.execute(
        "ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_protein_species"
    )
    op.execute(
        "ALTER TABLE ingredients ADD CONSTRAINT chk_ingredient_protein_species "
        "CHECK (protein_species IS NULL OR protein_species IN "
        f"({_in_list(VALID_PROTEIN_SPECIES)}))"
    )


def downgrade() -> None:
    """Drop the columns and constraints added by this migration."""
    op.execute(
        "ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_protein_species"
    )
    op.execute(
        "ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_supplement_url"
    )
    op.execute("ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS chk_ingredient_source")

    op.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS display_name")
    op.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS protein_species")
    op.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS supplement_info")
    op.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS chewy_url")
    op.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS amazon_url")
    op.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS source")
