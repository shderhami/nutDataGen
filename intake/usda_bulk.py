"""USDA extraction from the pinned bulk CSVs (no API, no network).

Reads `data/usda_bulk/{foundation,sr_legacy}` — the same pinned files the CV
pipeline hashes — so an extraction is reproducible for as long as the repo is.

Encodes the sweep's USDA lessons:
- derivation decode: assumed/borrowed zeros (Z, BF*) are flagged, analytical
  codes (A*) are trusted (runbook rule 2.3-3);
- retinol crosswalk: Foundation sometimes publishes retinol (1105) without
  RAE (1106) — RAE := retinol here (cats gain nothing from carotenoids);
- vitamin D crosswalk: 1114 (µg) fills 1110 (IU) at x40 when 1110 is absent;
- menaquinone note: MK-4 (1183) is surfaced on the vitamin K row so the
  K1-only blindness of SR is visible at review time.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

import cv_config
from intake.model import (
    FEDIAF_IDS,
    Q_ANALYSED,
    Q_BORROWED,
    Q_COMPUTED,
    Q_UNKNOWN,
    SourceValue,
)
from intake.units import to_fediaf

RETINOL_ID = 1105
VITA_RAE_ID = 1106
VITD_UG_ID = 1114
VITD_IU_ID = 1110
MK4_ID = 1183
VITK1_ID = 1185

_EXTRA_IDS = frozenset({RETINOL_ID, VITD_UG_ID, MK4_ID})
_WANTED_IDS = FEDIAF_IDS | _EXTRA_IDS

_DATASETS: tuple[tuple[str, Path], ...] = (
    ("FND", cv_config.FDC_FDN_DIR),
    ("SR", cv_config.FDC_SRL_DIR),
)


def _f(x: str) -> Optional[float]:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=1)
def _units_by_nutrient() -> dict[int, str]:
    """USDA storage unit per nutrient id (Foundation csv is the authority)."""
    units: dict[int, str] = {}
    for path in (cv_config.FDC_SRL_DIR / "nutrient.csv",
                 cv_config.AUTHORITATIVE_NUTRIENT_CSV):
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                units[int(row["id"])] = row["unit_name"]
    return units


@lru_cache(maxsize=1)
def _derivations() -> dict[int, tuple[str, str]]:
    path = cv_config.FDC_SRL_DIR / "food_nutrient_derivation.csv"
    out: dict[int, tuple[str, str]] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            out[int(row["id"])] = (row["code"], row["description"])
    return out


def food_names(fdc_ids: Iterable[int]) -> dict[int, str]:
    wanted = {int(i) for i in fdc_ids}
    names: dict[int, str] = {}
    for _, dirpath in _DATASETS:
        with open(dirpath / "food.csv", newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                fid = int(row["fdc_id"])
                if fid in wanted:
                    names[fid] = row["description"]
    return names


def _quality(code: str, description: str, data_points: Optional[int]) -> str:
    if code.startswith("A"):
        return Q_ANALYSED
    lowered = description.lower()
    if code == "Z" or code.startswith("BF") or "assumed" in lowered:
        return Q_BORROWED
    if "calculated" in lowered or "computed" in lowered:
        return Q_COMPUTED
    if data_points and data_points > 0:
        return Q_ANALYSED
    return Q_UNKNOWN


def extract_many(fdc_ids: Iterable[int]) -> dict[int, dict[int, SourceValue]]:
    """One pass over both bulk files; {fdc_id: {nutrient_id: SourceValue}}."""
    wanted = {int(i) for i in fdc_ids}
    names = food_names(wanted)
    units = _units_by_nutrient()
    derivations = _derivations()
    out: dict[int, dict[int, SourceValue]] = {fid: {} for fid in wanted}

    for label, dirpath in _DATASETS:
        with open(dirpath / "food_nutrient.csv", newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            col = {h: i for i, h in enumerate(header)}
            for row in reader:
                fid = int(row[col["fdc_id"]])
                if fid not in wanted:
                    continue
                nid = int(row[col["nutrient_id"]])
                if nid not in _WANTED_IDS:
                    continue
                amount = _f(row[col["amount"]])
                if amount is None:
                    continue
                dp = int(row[col["data_points"]] or 0) or None
                der_id = row[col["derivation_id"]]
                code, desc = derivations.get(int(der_id), ("", "")) if der_id else ("", "")
                vmin, vmax = _f(row[col["min"]]), _f(row[col["max"]])
                sv = SourceValue(
                    source=label,
                    source_food=f"{fid} {names.get(fid, '')}".strip(),
                    nutrient_id=nid if nid in FEDIAF_IDS else VITK1_ID,  # placeholder; fixed in _convert
                    value=amount, n=dp, vmin=vmin, vmax=vmax,
                    quality=_quality(code, desc, dp),
                    note=f"deriv {code}: {desc}" if code else "",
                    year=row[col["min_year_acquired"]] or None,
                )
                # Keyed by the RAW USDA nutrient id; crosswalk precedence is
                # resolved in _finalize after the whole food is read.
                out[fid][nid] = _convert(sv, nid, amount, vmin, vmax, units[nid])
    for fid in wanted:
        out[fid] = _finalize(out[fid])
    return out


def _convert(sv: SourceValue, nid: int, amount: float,
             vmin: Optional[float], vmax: Optional[float], unit: str) -> SourceValue:
    """Convert a raw USDA row into FEDIAF units under its FEDIAF target id."""
    target = {RETINOL_ID: VITA_RAE_ID, VITD_UG_ID: VITD_IU_ID}.get(nid, nid)
    if target not in FEDIAF_IDS:  # MK-4 kept raw; folded into the K note later
        return SourceValue(
            source=sv.source, source_food=sv.source_food, nutrient_id=VITK1_ID,
            value=amount, n=sv.n, vmin=vmin, vmax=vmax, quality=sv.quality,
            note=sv.note, year=sv.year,
        )
    scale = to_fediaf(target, 1.0, unit)
    note = sv.note
    if nid == RETINOL_ID:
        note = f"{note}; retinol (1105) as RAE — crosswalk" if note else "retinol (1105) as RAE — crosswalk"
    if nid == VITD_UG_ID:
        note = f"{note}; vit D µg (1114) x40 -> IU" if note else "vit D µg (1114) x40 -> IU"
    return SourceValue(
        source=sv.source, source_food=sv.source_food, nutrient_id=target,
        value=amount * scale, n=sv.n,
        vmin=vmin * scale if vmin is not None else None,
        vmax=vmax * scale if vmax is not None else None,
        quality=sv.quality, note=note, year=sv.year,
    )


def _finalize(rows: dict[int, SourceValue]) -> dict[int, SourceValue]:
    """Resolve crosswalk precedence and the MK-4 note; key by FEDIAF id."""
    out: dict[int, SourceValue] = {}
    for nid, sv in rows.items():
        if nid in (RETINOL_ID, VITD_UG_ID, MK4_ID):
            continue
        out[nid] = sv
    # published target beats crosswalk (a published zero included)
    if VITA_RAE_ID not in out and RETINOL_ID in rows:
        out[VITA_RAE_ID] = rows[RETINOL_ID]
    if VITD_IU_ID not in out and VITD_UG_ID in rows:
        out[VITD_IU_ID] = rows[VITD_UG_ID]
    mk4 = rows.get(MK4_ID)
    if mk4 is not None and mk4.value > 0:
        note = f"USDA MK-4 (1183) = {mk4.value:g} µg — SR/FND K row is K1 only; total-K doctrine applies"
        if VITK1_ID in out:
            out[VITK1_ID] = out[VITK1_ID].with_note(note)
        else:
            out[VITK1_ID] = SourceValue(
                source=mk4.source, source_food=mk4.source_food,
                nutrient_id=VITK1_ID, value=mk4.value, n=mk4.n,
                vmin=mk4.vmin, vmax=mk4.vmax, quality=mk4.quality,
                note=note, year=mk4.year,
            )
    return out
