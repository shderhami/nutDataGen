"""USDA extraction from the pinned bulk CSVs (no API, no network).

Reads `data/usda_bulk/{foundation,sr_legacy}` — the same pinned files the CV
pipeline hashes — so an extraction is reproducible for as long as the repo is.

Encodes the sweep's USDA lessons:
- derivation decode: assumed/borrowed zeros (Z, BF*) are flagged, analytical
  codes (A*) are trusted (runbook rule 2.3-3);
- crosswalks (one table, `_CROSSWALK`): retinol 1105 fills RAE 1106 (RAE :=
  retinol here — cats gain nothing from carotenoids) and vitamin D µg 1114
  fills IU 1110, with a published target (a zero included) always winning;
  mirrors usda_api._retinol_fallback on the API path — keep the two in sync;
- menaquinone: MK-4 (1183) is surfaced on the vitamin K row, and USDA K rows
  carry form=k1_only so the rule engine knows SR's blindness structurally.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

import cv_config
from intake.model import (
    FEDIAF_IDS,
    FORM_K1_ONLY,
    FORM_MK4_ONLY,
    Q_ANALYSED,
    Q_BORROWED,
    Q_COMPUTED,
    Q_UNKNOWN,
    SourceValue,
)
from intake.units import parse_float, to_fediaf

RETINOL_ID = 1105
VITA_RAE_ID = 1106
VITD_UG_ID = 1114
VITD_IU_ID = 1110
MK4_ID = 1183
VITK1_ID = 1185

# raw USDA nutrient id -> the FEDIAF id it may fill when that id is absent
_CROSSWALK: dict[int, int] = {RETINOL_ID: VITA_RAE_ID, VITD_UG_ID: VITD_IU_ID}
_CROSSWALK_NOTES: dict[int, str] = {
    RETINOL_ID: "retinol (1105) as RAE — crosswalk",
    VITD_UG_ID: "vit D µg (1114) x40 -> IU — crosswalk",
}
_EXTRA_IDS = frozenset(_CROSSWALK) | {MK4_ID}
_WANTED_IDS = FEDIAF_IDS | _EXTRA_IDS

_DATASETS: tuple[tuple[str, Path], ...] = (
    ("FND", cv_config.FDC_FDN_DIR),
    ("SR", cv_config.FDC_SRL_DIR),
)

_f = parse_float


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


# the Foundation bulk holds 469 real foods and ~87,500 sub-sample /
# acquisition rows — a mistyped id is ~187x more likely to land on a
# non-food that "extracts" a plausible 1-nutrient table (corpus sweep
# 2026-08-18). Only real food rows resolve.
_REAL_FOOD_TYPES = frozenset({"foundation_food", "sr_legacy_food"})


def food_names(fdc_ids: Iterable[int]) -> dict[int, str]:
    wanted = {int(i) for i in fdc_ids}
    names: dict[int, str] = {}
    for _, dirpath in _DATASETS:
        with open(dirpath / "food.csv", newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                fid = int(row["fdc_id"])
                if fid in wanted and row["data_type"] in _REAL_FOOD_TYPES:
                    names[fid] = row["description"]
    return names


def _quality(code: str, description: str, data_points: Optional[int]) -> str:
    lowered = description.lower()
    if code == "Z" or code.startswith("BF") or "assumed" in lowered:
        return Q_BORROWED
    # A-prefix codes are NOT uniformly analytical: AS is "Summed" and AR is
    # regression-derived — the CV pipeline (cv_extract._calc_derivation_ids)
    # excludes those same rows from dispersion pooling, so classifying them
    # `analysed` here would let the two pipelines contradict each other on
    # the same cell (audit 2026-08-18).
    if any(m in lowered for m in ("summed", "regression", "calculated",
                                  "computed", "imputed", "recipe")):
        return Q_COMPUTED
    if code.startswith("A"):
        return Q_ANALYSED
    if data_points and data_points > 0:
        return Q_ANALYSED
    return Q_UNKNOWN


def _make_value(label: str, food: str, nid: int, target: int, amount: float,
                dp: Optional[int], vmin: Optional[float], vmax: Optional[float],
                code: str, desc: str, year: Optional[str]) -> SourceValue:
    """One converted SourceValue under its FEDIAF target id."""
    scale = to_fediaf(target, 1.0, _units_by_nutrient()[nid]) if target in FEDIAF_IDS else 1.0
    note = f"deriv {code}: {desc}" if code else ""
    if nid == 1005 and amount < 0:
        # USDA carbohydrate-by-difference on lean meats can compute slightly
        # negative (10 foods in the pinned Foundation bulk, -0.15..-0.71 g) —
        # an arithmetic artifact meaning zero (corpus sweep 2026-08-18)
        note = (f"{note}; by-difference {amount:g} clamped to 0" if note
                else f"by-difference {amount:g} clamped to 0")
        amount, vmin, vmax = 0.0, None, None
    if nid in _CROSSWALK_NOTES:
        note = f"{note}; {_CROSSWALK_NOTES[nid]}" if note else _CROSSWALK_NOTES[nid]
    return SourceValue(
        source=label, source_food=food, nutrient_id=target,
        value=amount * scale, n=dp,
        vmin=vmin * scale if vmin is not None else None,
        vmax=vmax * scale if vmax is not None else None,
        quality=_quality(code, desc, dp), note=note, year=year,
        form=FORM_K1_ONLY if target == VITK1_ID else "",
    )


def extract_many(fdc_ids: Iterable[int]) -> dict[int, dict[int, SourceValue]]:
    """One pass over both bulk files; {fdc_id: {nutrient_id: SourceValue}}.

    Ids that do not resolve to a REAL food row (foundation_food /
    sr_legacy_food) return empty tables, which extract.run fails loud on.
    """
    wanted = {int(i) for i in fdc_ids}
    names = food_names(wanted)
    wanted &= set(names)   # sub-sample/acquisition ids never extract
    derivations = _derivations()
    # raw rows keyed by the RAW USDA nutrient id; crosswalk precedence and the
    # MK-4 note are resolved in _finalize once the whole food is read.
    raw: dict[int, dict[int, SourceValue]] = {int(i): {} for i in fdc_ids}

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
                raw[fid][nid] = _make_value(
                    label=label, food=f"{fid} {names.get(fid, '')}".strip(),
                    nid=nid, target=_CROSSWALK.get(nid, nid), amount=amount,
                    dp=dp, vmin=_f(row[col["min"]]), vmax=_f(row[col["max"]]),
                    code=code, desc=desc,
                    year=row[col["min_year_acquired"]] or None,
                )
    return {fid: _finalize(rows) for fid, rows in raw.items()}


def _finalize(rows: dict[int, SourceValue]) -> dict[int, SourceValue]:
    """Resolve crosswalk precedence and the MK-4 note; key by FEDIAF id."""
    out: dict[int, SourceValue] = {
        nid: sv for nid, sv in rows.items() if nid not in _EXTRA_IDS
    }
    # a published target beats its crosswalk source (a published zero included)
    for source_id, target_id in _CROSSWALK.items():
        if target_id not in out and source_id in rows:
            out[target_id] = rows[source_id]
    mk4 = rows.get(MK4_ID)
    if mk4 is not None and mk4.value > 0:
        if VITK1_ID in out:
            out[VITK1_ID] = out[VITK1_ID].with_note(
                f"USDA MK-4 (1183) = {mk4.value:g} µg — this K row is K1 only; "
                f"total-K doctrine applies")
        else:
            # no K1 row at all: surface the MK-4 measurement honestly as an
            # MK-4-only value (74 Foundation foods) — never labeled K1-only
            out[VITK1_ID] = SourceValue(
                source=mk4.source, source_food=mk4.source_food,
                nutrient_id=VITK1_ID, value=mk4.value, n=mk4.n,
                vmin=mk4.vmin, vmax=mk4.vmax, quality=mk4.quality,
                note=(f"USDA publishes MK-4 (1183) only for this food — no K1 "
                      f"row; value is menaquinone-4 alone"),
                year=mk4.year, form=FORM_MK4_ONLY,
            )
    return out
