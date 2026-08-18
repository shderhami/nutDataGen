"""Unit conversion of source values into FEDIAF platform units.

Fail-loud like the platform's add-time conversion: a unit pair this module
does not know is an error, never a silent pass-through. Mirrors
`fediaf_nutrients.fediaf_unit_factor` for the IU vitamins (A: µg retinol
x3.33 — RAE := retinol in this DB; E: mg alpha-tocopherol x1.49; D: µg x40)
and adds the plain mass/energy rescales foreign tables need.
"""
from __future__ import annotations

import re

from fediaf_nutrients import canonical_unit, fediaf_unit_factor
from intake.model import FEDIAF_BY_ID

_MASS_GRAMS = {"g": 1.0, "mg": 1e-3, "µg": 1e-6}
KJ_PER_KCAL = 4.184


def to_fediaf(nutrient_id: int, value: float, unit: str) -> float:
    """Convert `value` expressed in `unit` into the nutrient's FEDIAF unit."""
    declared: str = FEDIAF_BY_ID[nutrient_id]["unit"]
    cu = canonical_unit(unit)
    if not cu:
        # fediaf_unit_factor treats a missing unit as "fall back to the
        # declared unit" (factor 1.0) — correct for DB writes, silently wrong
        # here: an adapter/spec value with no unit must never skip the IU
        # factors (audit finding 2026-08-18: '' made vit A 3.33x, vit D 40x low).
        raise ValueError(
            f"Missing unit for nutrient {nutrient_id}: a source value must "
            f"state its published unit"
        )
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


def parse_float(raw) -> "float | None":
    """Best-effort float coercion shared by the adapters ('NULL'/'' -> None)."""
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _header_token(label: str) -> str:
    """The label's most specific word, for header alignment checks."""
    words = re.sub(r"[^a-z0-9:]+", " ", label.lower()).split()
    return max(words, key=len) if words else ""


def check_header_alignment(header: "tuple | list", labels_by_index: dict[int, str],
                           source: str) -> None:
    """Tripwire for positional column maps (audit 2026-08-18): a dataset
    release that inserts/reorders a column silently shifts every index after
    it. Each mapped column's header must still contain the most specific word
    of its expected label; raise loudly otherwise."""
    problems = []
    for i, label in labels_by_index.items():
        token = _header_token(label)
        cell = re.sub(r"[^a-z0-9:]+", " ", str(header[i] if i < len(header) else "").lower())
        if token and token not in cell:
            problems.append(f"col {i}: expected '{label}' (token '{token}'), "
                            f"header says '{str(header[i])[:60]}'")
    if problems:
        raise ValueError(
            f"{source}: column map no longer aligns with the dataset header — "
            f"the file likely changed. " + "; ".join(problems))
