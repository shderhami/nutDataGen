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


def _norm_words(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9:.]+", " ", text.lower()).split()


def check_header_alignment(header: "tuple | list", labels_by_index: dict[int, str],
                           source: str) -> None:
    """Tripwire for positional column maps (audit 2026-08-18): a dataset
    release that inserts/reorders a column silently shifts every index after
    it. EVERY word of the expected label (length >= 2) must appear as an
    exact word of that column's header cell — exact-word matching so 'K1'
    cannot pass on a 'Vitamin K2' or 'B12' cell, and family words alone
    ('Vitamine', 'C18:2' on CoFID's twin columns) cannot vouch for a shifted
    neighbour. A header shorter than the map is a mismatch, not an IndexError.
    """
    problems = []
    for i, label in labels_by_index.items():
        wanted = [w for w in _norm_words(label) if len(w) >= 2]
        cell_raw = str(header[i]) if i < len(header) else ""
        cell_words = set(_norm_words(cell_raw))
        missing = [w for w in wanted if w not in cell_words]
        if missing:
            problems.append(f"col {i}: expected '{label}' (missing {missing}), "
                            f"header says '{cell_raw[:60]}'")
    if problems:
        raise ValueError(
            f"{source}: column map no longer aligns with the dataset header — "
            f"the file likely changed. " + "; ".join(problems))
