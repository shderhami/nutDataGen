#!/usr/bin/env python3
"""Build + validate the nutrient_nbr <-> nutrient_id crosswalk (fail-loud).

Layers 1-2 of the CV pipeline key on USDA `nutrient_nbr` (SR28 Nutr_No); Layer 3
and ingredient_nutrients key on the FDC internal `nutrient_id`. The only bridge is
FDC nutrient.csv. This module materializes and VALIDATES that bridge for the target
nutrient set (fediaf_nutrients + component sources) and aborts loudly on any
ambiguity, so a wrong join can never silently transplant the wrong nutrient's CV.

Usage:  python build_nutrient_crosswalk.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import cv_config
from fediaf_nutrients import get_all_nutrients


class CrosswalkError(RuntimeError):
    """Raised when the crosswalk cannot be validated (fail-loud)."""


def _load_nutrient_csv(path: Path) -> dict[int, dict]:
    """FDC nutrient.csv -> {nutrient_id: {name, unit, nutrient_nbr|None}}."""
    out: dict[int, dict] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                nid = int(row["id"])
            except (ValueError, TypeError, KeyError):
                continue
            nbr_raw = (row.get("nutrient_nbr") or "").strip()
            nbr = None
            if nbr_raw:
                try:
                    nbr = int(float(nbr_raw))
                except ValueError:
                    nbr = None
            out[nid] = {
                "name": (row.get("name") or "").strip(),
                "unit": (row.get("unit_name") or "").strip(),
                "nutrient_nbr": nbr,
            }
    return out


def build_crosswalk() -> dict[int, dict]:
    """Return {nutrient_id: {nutrient_nbr, usda_name, unit, nutrient_class,
    disposition, is_target}} or raise CrosswalkError."""
    fdn = _load_nutrient_csv(cv_config.AUTHORITATIVE_NUTRIENT_CSV)     # authoritative
    srl = _load_nutrient_csv(cv_config.FDC_SRL_DIR / "nutrient.csv")   # cross-check

    targets = get_all_nutrients()
    target_ids = {n["nutrient_id"] for n in targets if n["nutrient_id"] is not None}
    # component-source nutrient_ids (e.g. Retinol 1105 feeding Vit A) are needed too
    for spec in cv_config.COMPONENT_DERIVATION.values():
        target_ids.add(spec["from_nutrient_id"])
    meta_by_id = {n["nutrient_id"]: n for n in targets}

    errors: list[str] = []
    seen_nbr: dict[int, int] = {}
    crosswalk: dict[int, dict] = {}

    for nid in sorted(target_ids):
        f = fdn.get(nid)
        s = srl.get(nid)
        nbr = (f or {}).get("nutrient_nbr")
        if nbr is None and s:
            nbr = s.get("nutrient_nbr")

        # Cross-check the two datasets agree where both have a value.
        if (f and s and f.get("nutrient_nbr") is not None
                and s.get("nutrient_nbr") is not None
                and f["nutrient_nbr"] != s["nutrient_nbr"]):
            errors.append(
                f"nutrient_id {nid}: Foundation nbr {f['nutrient_nbr']} "
                f"!= SR-Legacy nbr {s['nutrient_nbr']}"
            )

        if nbr is not None:
            if nbr <= 0:
                errors.append(f"nutrient_id {nid}: non-positive nutrient_nbr {nbr}")
            prev = seen_nbr.get(nbr)
            if prev is not None and prev != nid:
                errors.append(
                    f"duplicate nutrient_nbr {nbr}: nutrient_id {prev} and {nid}"
                )
            seen_nbr[nbr] = nid

        meta = meta_by_id.get(nid, {})
        crosswalk[nid] = {
            "nutrient_nbr": nbr,
            # has_nbr -> reachable at Tiers 1-3; no_nbr -> route to Tier 4/5 by class
            "disposition": "has_nbr" if nbr is not None else "no_nbr",
            "usda_name": (f or s or {}).get("name") or meta.get("usda_name"),
            "unit": meta.get("unit"),
            "nutrient_class": cv_config.nutrient_class(nid),
            "is_target": nid in {n["nutrient_id"] for n in targets},
        }

    if errors:
        raise CrosswalkError(
            "Crosswalk validation FAILED:\n  - " + "\n  - ".join(errors)
        )
    return crosswalk


def main() -> None:
    cw = build_crosswalk()
    has = sum(1 for v in cw.values() if v["disposition"] == "has_nbr")
    non = sum(1 for v in cw.values() if v["disposition"] == "no_nbr")
    print(f"Crosswalk OK: {len(cw)} nutrients "
          f"({has} with nutrient_nbr, {non} no-nbr -> Tier 4/5 by class)")
    for nid, v in sorted(cw.items()):
        flag = "" if v["disposition"] == "has_nbr" else "   <-- no nbr (Tier 4/5)"
        tgt = "" if v["is_target"] else " (component source)"
        print(f"  id={nid:5d}  nbr={str(v['nutrient_nbr']):>5s}  "
              f"{str(v['usda_name'])[:38]:38s} [{v['nutrient_class']}]{tgt}{flag}")


if __name__ == "__main__":
    try:
        main()
    except CrosswalkError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
