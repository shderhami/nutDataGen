"""Guard: every nutrient_id is stored in exactly one unit across
ingredient_nutrients, and that unit is the FEDIAF-declared one.

Vitamins A (1106) and E (1109) historically mixed USDA payload units (µg/mg)
with FEDIAF IU; the 2026-08-17 normalization converted them (x3.33 retinol
basis / x1.49) and create_nutrient_record now converts payload units at add
time. This test fails if a payload-unit row ever reappears.

DB-optional: skips when the database is unreachable (same convention as
test_pipeline_version_integrity).
"""
import pytest

from fediaf_nutrients import get_nutrient_by_id


def _units_by_nutrient() -> dict[int, list[str]]:
    try:
        from db_connection import get_db
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT nutrient_id, array_agg(DISTINCT unit) AS units "
                "FROM ingredient_nutrients GROUP BY nutrient_id"
            )
            rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001 - any connection failure means skip
        pytest.skip(f"DB unavailable — nothing to guard: {exc}")
    if not rows:
        pytest.skip("ingredient_nutrients is empty — nothing to guard")
    return {int(r["nutrient_id"]): sorted(r["units"]) for r in rows}


def test_one_distinct_unit_per_nutrient_id():
    mixed = {
        nid: units
        for nid, units in _units_by_nutrient().items()
        if len(units) != 1
    }
    assert not mixed, (
        "Mixed units per nutrient_id in ingredient_nutrients (the add pipeline "
        f"must convert to FEDIAF units at create time): {mixed}"
    )


def test_stored_unit_is_the_fediaf_declared_unit():
    wrong = {}
    for nid, units in _units_by_nutrient().items():
        info = get_nutrient_by_id(nid)
        if info is None:
            continue  # untracked nutrient rows are outside this contract
        if units != [info["unit"]]:
            wrong[nid] = {"stored": units, "declared": info["unit"]}
    assert not wrong, (
        f"Stored units diverge from FEDIAF declared units: {wrong}"
    )
