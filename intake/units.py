"""Unit conversion of source values into FEDIAF platform units.

Fail-loud like the platform's add-time conversion: a unit pair this module
does not know is an error, never a silent pass-through. Mirrors
`fediaf_nutrients.fediaf_unit_factor` for the IU vitamins (A: µg retinol
x3.33 — RAE := retinol in this DB; E: mg alpha-tocopherol x1.49; D: µg x40)
and adds the plain mass/energy rescales foreign tables need.
"""
from __future__ import annotations

from fediaf_nutrients import canonical_unit, fediaf_unit_factor
from intake.model import FEDIAF_BY_ID

_MASS_GRAMS = {"g": 1.0, "mg": 1e-3, "µg": 1e-6}
KJ_PER_KCAL = 4.184


def to_fediaf(nutrient_id: int, value: float, unit: str) -> float:
    """Convert `value` expressed in `unit` into the nutrient's FEDIAF unit."""
    declared: str = FEDIAF_BY_ID[nutrient_id]["unit"]
    cu = canonical_unit(unit)
    if cu == declared:
        return value
    if cu in _MASS_GRAMS and declared in _MASS_GRAMS:
        return value * _MASS_GRAMS[cu] / _MASS_GRAMS[declared]
    if declared == "IU":
        # fediaf_unit_factor knows the vitamin A/D/E payload conversions and
        # raises for anything it does not — exactly the contract we want.
        _, factor = fediaf_unit_factor(nutrient_id, cu)
        return value * factor
    if declared == "kcal" and cu == "kJ":
        return value / KJ_PER_KCAL
    raise ValueError(
        f"No conversion from '{unit}' to FEDIAF unit '{declared}' "
        f"for nutrient {nutrient_id}"
    )


def parse_per100g_unit(header_unit: str) -> str:
    """Strip a per-100g denominator: 'mg/100 g' -> 'mg', 'kJ/100g' -> 'kJ'."""
    return header_unit.split("/")[0].strip()
