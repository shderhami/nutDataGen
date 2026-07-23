#!/usr/bin/env python3
"""Readers for the pinned USDA bulk snapshots.

Two formats:
  * SR28 legacy ASCII (NUT_DATA.txt, FOOD_DES.txt, NUTR_DEF.txt): caret ('^')
    delimited, text fields wrapped in tildes ('~'), NO header row, positional.
  * FDC CSV (SR-Legacy 2018-04 and Foundation 2026-04-30): standard comma CSV
    with a header row.

The readers normalize both into plain dicts keyed on the USDA `nutrient_nbr`
(SR28 Nutr_No; for FDC, mapped from its internal nutrient_id via nutrient.csv).
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator, Optional

import cv_config

# SR28 NUT_DATA.txt positional fields (18 total).
_SR28_NDB, _SR28_NUTR, _SR28_VAL, _SR28_N, _SR28_SE = 0, 1, 2, 3, 4
_SR28_SRC, _SR28_DERIV = 5, 6
_SR28_MIN, _SR28_MAX = 10, 11
_SR28_MIN_FIELDS = 15   # tolerate a couple of missing trailing fields


def _f(s: str) -> Optional[float]:
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _i(s: str) -> Optional[int]:
    v = _f(s)
    return int(v) if v is not None else None


def _untilde(s: str) -> str:
    return s.strip().strip("~").strip()


# ── SR28 legacy ASCII ────────────────────────────────────────────────────────
def read_sr28_nut_data(path: Optional[Path] = None) -> Iterator[dict]:
    """Yield {ndb_no, nutr_no, value, n, se, min, max, src_cd, deriv_cd} per row."""
    path = path or cv_config.SR28_NUT_DATA
    with open(path, encoding="latin-1") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line:
                continue
            p = line.split("^")
            if len(p) < _SR28_MIN_FIELDS:
                raise ValueError(
                    f"{path.name}:{lineno}: expected >= {_SR28_MIN_FIELDS} "
                    f"caret fields, got {len(p)}"
                )
            ndb = _i(_untilde(p[_SR28_NDB]))
            nutr = _i(_untilde(p[_SR28_NUTR]))
            if ndb is None or nutr is None:
                continue
            yield {
                "ndb_no": ndb,
                "nutr_no": nutr,
                "value": _f(p[_SR28_VAL]),
                "n": _i(p[_SR28_N]),
                "se": _f(p[_SR28_SE]),
                "min": _f(p[_SR28_MIN]) if len(p) > _SR28_MIN else None,
                "max": _f(p[_SR28_MAX]) if len(p) > _SR28_MAX else None,
                "src_cd": _untilde(p[_SR28_SRC]) if len(p) > _SR28_SRC else "",
                "deriv_cd": _untilde(p[_SR28_DERIV]) if len(p) > _SR28_DERIV else "",
            }


def read_sr28_food_desc(path: Optional[Path] = None) -> dict[int, str]:
    """FOOD_DES.txt -> {ndb_no: long description}."""
    path = path or (cv_config.SR28_NUT_DATA.parent / "FOOD_DES.txt")
    out: dict[int, str] = {}
    with open(path, encoding="latin-1") as fh:
        for raw in fh:
            p = raw.rstrip("\n").split("^")
            if len(p) < 3:
                continue
            ndb = _i(_untilde(p[0]))
            if ndb is not None:
                out[ndb] = _untilde(p[2])   # Long_Desc
    return out


# ── FDC CSV ──────────────────────────────────────────────────────────────────
def read_fdc_nutrient_map(nutrient_csv: Path) -> dict[int, int]:
    """FDC nutrient.csv -> {nutrient_id: nutrient_nbr} (int, blanks skipped)."""
    out: dict[int, int] = {}
    with open(nutrient_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                nid = int(row["id"])
            except (ValueError, TypeError, KeyError):
                continue
            nbr_raw = (row.get("nutrient_nbr") or "").strip()
            if nbr_raw:
                try:
                    out[nid] = int(float(nbr_raw))
                except ValueError:
                    pass
    return out


def read_fdc_food(food_csv: Path) -> dict[int, str]:
    """FDC food.csv -> {fdc_id: description}."""
    out: dict[int, str] = {}
    with open(food_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                out[int(row["fdc_id"])] = (row.get("description") or "").strip()
            except (ValueError, TypeError, KeyError):
                continue
    return out


def read_sr_legacy_food(path: Path) -> dict[int, int]:
    """sr_legacy_food.csv -> {fdc_id: NDB_No (int-normalized)}."""
    out: dict[int, int] = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                fdc = int(row["fdc_id"])
            except (ValueError, TypeError, KeyError):
                continue
            ndb = _i(row.get("NDB_number") or "")
            if ndb is not None:
                out[fdc] = ndb
    return out


def read_fdc_food_nutrient(
    food_nutrient_csv: Path, nutrient_id_to_nbr: dict[int, int],
) -> Iterator[dict]:
    """FDC food_nutrient.csv -> per-row dicts keyed on nutrient_nbr.

    Yields {fdc_id, nutrient_nbr, amount, n, min, max, derivation_id}; rows whose
    nutrient_id has no nutrient_nbr in the map are skipped.
    """
    with open(food_nutrient_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                fdc = int(row["fdc_id"])
                nid = int(row["nutrient_id"])
            except (ValueError, TypeError, KeyError):
                continue
            nbr = nutrient_id_to_nbr.get(nid)
            if nbr is None:
                continue
            yield {
                "fdc_id": fdc,
                "nutrient_nbr": nbr,
                "amount": _f(row.get("amount") or ""),
                "n": _i(row.get("data_points") or ""),
                "min": _f(row.get("min") or ""),
                "max": _f(row.get("max") or ""),
                "derivation_id": (row.get("derivation_id") or "").strip(),
            }


if __name__ == "__main__":
    # Smoke test: parse each source and show counts + a sample row.
    import itertools

    print("== SR28 NUT_DATA ==")
    rows = list(itertools.islice(read_sr28_nut_data(), 200000))
    with_se = [r for r in rows if r["se"] is not None and r["n"] and r["n"] >= 3]
    print(f"  rows read (first 200k): {len(rows)}   with SE & n>=3: {len(with_se)}")
    print(f"  sample: {with_se[0] if with_se else rows[0]}")

    fdn = cv_config.FDC_FDN_DIR
    nbr_map = read_fdc_nutrient_map(fdn / "nutrient.csv")
    print(f"\n== FDC Foundation ==\n  nutrient_id->nbr entries: {len(nbr_map)}")
    fn = list(itertools.islice(read_fdc_food_nutrient(fdn / "food_nutrient.csv", nbr_map), 50000))
    with_mm = [r for r in fn if r["min"] is not None and r["max"] is not None and r["n"] and r["n"] >= 2]
    print(f"  food_nutrient rows (first 50k): {len(fn)}   with min/max & n>=2: {len(with_mm)}")
    print(f"  sample: {with_mm[0] if with_mm else (fn[0] if fn else None)}")

    srl = cv_config.FDC_SRL_DIR
    bridge = read_sr_legacy_food(srl / "sr_legacy_food.csv")
    print(f"\n== SR-Legacy bridge ==\n  fdc_id->NDB_No entries: {len(bridge)}   sample: {list(bridge.items())[:2]}")
    desc = read_sr28_food_desc()
    print(f"  SR28 FOOD_DES entries: {len(desc)}   sample: {list(desc.items())[0]}")
