#!/usr/bin/env python3
"""Resolve CVs for the target (ingredient, nutrient) cells and write them to the
live ingredient_nutrients columns — gated behind the QA report.

  measured CV (Tiers 1-3, or a corrector's delivered spec) -> coefficient_of_variation
  category  CV (Tiers 4-6) -> category_cv
  + cv_* provenance.  Consumer = COALESCE(coefficient_of_variation, category_cv).

The live write is a single reconciling transaction (pre-image captured first, stale
/ out-of-target cells NULLed, current cells UPSERTed with each UPDATE asserted to
touch exactly one row). Coverage is structural: resolve_all JOINs every existing
ingredient_nutrients row for the constrained nutrients and resolve_cv always returns
a value, so every present target cell is written. It only commits when the QA gate
passes AND a signer is supplied.

Usage:
  python cv_assign.py                              # dry-run: resolve + gate, no write
  python cv_assign.py --food-id 10001              # resolve one ingredient (incremental)
  python cv_assign.py --commit --signed-off-by "Shahab"   # gated live write (pg_dump first)
"""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from pathlib import Path

import psycopg2.extras

import cv_config
import cv_sources
from build_nutrient_crosswalk import build_crosswalk
from db_connection import get_db, close_db
import cv_intl
from resolve_cv import load_cv_class, resolve_cv

_PIPELINE_FILES = [
    "cv_config.py", "cv_stats.py", "cv_sources.py", "build_nutrient_crosswalk.py",
    "cv_extract.py", "cv_pool.py", "resolve_cv.py", "cv_assign.py", "cv_report.py",
    "cv_intl.py",
]


def code_sha256() -> str:
    # Normalized AST (comments/docstrings/layout excluded) so cosmetic edits to a
    # pipeline file don't change the hash — mirrors cv_config.config_sha256.
    h = hashlib.sha256()
    for name in sorted(_PIPELINE_FILES):
        p = Path(__file__).parent / name
        if p.exists():
            h.update(cv_config.normalized_source(p).encode("utf-8"))
    return h.hexdigest()


def dataset_shas() -> dict:
    out = {}
    for label, p in [("sr28", cv_config.SR28_NUT_DATA),
                     ("fdc_srl", cv_config.FDC_SRL_DIR / "food_nutrient.csv"),
                     ("fdc_fdn", cv_config.FDC_FDN_DIR / "food_nutrient.csv"),
                     ("nutrient_csv", cv_config.AUTHORITATIVE_NUTRIENT_CSV),
                     ("intl_cv", cv_intl.INTL_CSV)]:
        try:
            out[label] = hashlib.sha256(Path(p).read_bytes()).hexdigest()
        except FileNotFoundError:
            out[label] = None
    return out


def resolve_all(food_id_filter: int | None = None) -> list[dict]:
    intl_obs = cv_intl.read_observations()
    cw = build_crosswalk()
    id_to = {nid: (v["nutrient_nbr"], v["nutrient_class"])
             for nid, v in cw.items() if v["is_target"] and v["nutrient_nbr"] is not None}
    comp_nbr = {nid: cw[spec["from_nutrient_id"]]["nutrient_nbr"]
                for nid, spec in cv_config.COMPONENT_DERIVATION.items()
                if spec["from_nutrient_id"] in cw}
    target_ids = tuple(id_to)

    db = get_db()
    lookups = load_cv_class(db)

    sr28: dict[tuple, tuple] = {}
    with db.cursor() as cur:
        cur.execute("SELECT source_food_id, nutrient_nbr, cv, n_data_points, method "
                    "FROM cv_observations WHERE source_dataset='sr28'")
        for r in cur.fetchall():
            sr28[(int(r["source_food_id"]), r["nutrient_nbr"])] = (
                float(r["cv"]), r["n_data_points"], r["method"])

    bridge = cv_sources.read_sr_legacy_food(cv_config.FDC_SRL_DIR / "sr_legacy_food.csv")

    with db.cursor() as cur:
        q = ("SELECT n.food_id, n.nutrient_id, n.value, n.min_value, n.max_value, n.num_samples, "
             "n.source, i.category, i.ingredient_class, i.sr_legacy_fdc_id, "
             "i.protein_species, i.food_name, i.is_corrector "
             "FROM ingredient_nutrients n JOIN ingredients i ON n.food_id=i.food_id "
             "WHERE n.nutrient_id IN %s")
        params: list = [target_ids]
        if food_id_filter is not None:
            q += " AND n.food_id=%s"
            params.append(food_id_filter)
        cur.execute(q, tuple(params))
        cells = [dict(r) for r in cur.fetchall()]

    def _f(x):
        return float(x) if x is not None else None

    out: list[dict] = []
    for c in cells:
        nid = c["nutrient_id"]
        nbr, nclass = id_to[nid]
        ndb = bridge.get(c["sr_legacy_fdc_id"]) if c["sr_legacy_fdc_id"] else None
        sr = sr28.get((ndb, nbr)) if ndb else None
        sr_cv, sr_n, sr_method = sr if sr else (None, None, None)
        comp_cv = comp_n = None
        if nid in comp_nbr and (c["ingredient_class"] in cv_config.ANIMAL_TISSUE_CLASSES) and ndb:
            rr = sr28.get((ndb, comp_nbr[nid]))
            if rr:
                comp_cv, comp_n = rr[0], rr[1]
        ic = c["ingredient_class"] or "other"
        # Muscle poultry/red sub-pool: prefer the curated protein_species column,
        # fall back to the ingredient name (handles species not yet in the column).
        subclass = None
        if ic == "muscle":
            subclass = (cv_config.muscle_subclass(c["protein_species"])
                        or cv_config.muscle_subclass(c["food_name"]))
        intl = intl_obs.get((c["food_id"], nid))
        res = resolve_cv(
            nutrient_id=nid, nutrient_nbr=nbr, ingredient_class=ic,
            nutrient_class=nclass, category=c["category"], value=_f(c["value"]), subclass=subclass,
            is_corrector=bool(c["is_corrector"]),
            own_min=_f(c["min_value"]), own_max=_f(c["max_value"]), own_n=c["num_samples"],
            sr28_se_cv=sr_cv, sr28_n=sr_n, sr28_method=sr_method, source=c["source"],
            component_cv=comp_cv, component_n=comp_n,
            intl_cv=(intl["cv"] if intl else None), intl_n=(intl["n"] if intl else None),
            intl_label=(intl["label"] if intl else None), lookups=lookups,
        )
        out.append({"food_id": c["food_id"], "nutrient_id": nid, "nutrient_nbr": nbr,
                    "nutrient_class": nclass, "ingredient_class": c["ingredient_class"],
                    "category": c["category"], "value": c["value"], "resolution": res})
    return out


_UPD_COLS = ["coefficient_of_variation", "category_cv", "cv_tier", "cv_method", "cv_backing_n",
             "cv_effective_n", "cv_confidence_tier", "cv_calibration_flag", "cv_class_key",
             "cv_method_inputs", "cv_config_sha256", "cv_pipeline_version"]


def commit(resolutions: list[dict], signer: str, full: bool, record_run: bool = True) -> None:
    """Reconcile + write in ONE transaction. Gate is re-verified and CV bounds are
    asserted here so no write can occur without a fresh PASS. `full`=True runs the
    orphan-NULL reconcile pass. `record_run`=False skips the cv_pipeline_run upsert —
    used by the per-ingredient auto-assign path so an incremental add does not move the
    version's sign-off/timestamp (the deliberate full commit owns the run record)."""
    pv = cv_config.PIPELINE_VERSION
    csha, code = cv_config.config_sha256(), code_sha256()
    dshas = dataset_shas()
    if any(v is None for v in dshas.values()):
        raise SystemExit(f"Missing pinned dataset file(s) — cannot commit: {dshas}")

    from cv_report import evaluate_gate      # structurally couple gate -> write
    gate_ok, gate_fail = evaluate_gate(resolutions)
    if not gate_ok:
        raise SystemExit("Gate BLOCKED at commit: " + "; ".join(gate_fail))

    conn = get_db().get_connection()
    cur = conn.cursor()
    try:
        # Refuse-to-run: one (config, code, datasets) per pipeline_version.
        cur.execute("SELECT config_sha256, code_sha256, dataset_shas "
                    "FROM cv_pipeline_run WHERE pipeline_version=%s", (pv,))
        prev = cur.fetchone()
        if prev and (prev[0] != csha or prev[1] != code or prev[2] != dshas):
            raise RuntimeError(
                f"config/code/dataset changed under pipeline_version '{pv}' — bump PIPELINE_VERSION.")

        # Pre-image: capture ONCE per version (never clobber the original legacy
        # values on a re-commit), all cv_* columns for a full revert.
        cur.execute("SELECT 1 FROM cv_cv_preimage WHERE pipeline_version=%s LIMIT 1", (pv,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO cv_cv_preimage (pipeline_version, food_id, nutrient_id, "
                "old_coefficient_of_variation, old_category_cv, old_cv_json) "
                "SELECT %s, food_id, nutrient_id, coefficient_of_variation, category_cv, "
                "jsonb_build_object("
                "'coefficient_of_variation', coefficient_of_variation, 'category_cv', category_cv, "
                "'cv_tier', cv_tier, 'cv_method', cv_method, 'cv_backing_n', cv_backing_n, "
                "'cv_effective_n', cv_effective_n, 'cv_confidence_tier', cv_confidence_tier, "
                "'cv_calibration_flag', cv_calibration_flag, 'cv_class_key', cv_class_key, "
                "'cv_method_inputs', cv_method_inputs, 'cv_config_sha256', cv_config_sha256, "
                "'cv_pipeline_version', cv_pipeline_version) "
                "FROM ingredient_nutrients", (pv,),
            )

        if full:
            cur.execute("UPDATE ingredient_nutrients SET " + ", ".join(f"{c}=NULL" for c in _UPD_COLS))

        for r in resolutions:
            res = r["resolution"]
            for col in ("measured_cv", "category_cv"):
                v = res[col]
                if v is not None and not (0.0 < float(v) <= cv_config.CV_CAP):
                    raise RuntimeError(
                        f"CV out of bounds ({col}={v}) for food_id={r['food_id']} "
                        f"nutrient_id={r['nutrient_id']}")
            vals = [
                res["measured_cv"], res["category_cv"], res["cv_tier"], res["cv_method"],
                res["cv_backing_n"], res["cv_effective_n"], res["cv_confidence_tier"],
                res["cv_calibration_flag"],
                psycopg2.extras.Json(res["cv_class_key"]) if res["cv_class_key"] else None,
                psycopg2.extras.Json(res["cv_method_inputs"]) if res["cv_method_inputs"] else None,
                csha, pv,
            ]
            cur.execute(
                "UPDATE ingredient_nutrients SET " + ", ".join(f"{c}=%s" for c in _UPD_COLS)
                + " WHERE food_id=%s AND nutrient_id=%s",
                vals + [r["food_id"], r["nutrient_id"]],
            )
            if cur.rowcount != 1:
                raise RuntimeError(
                    f"expected exactly 1 row for food_id={r['food_id']} "
                    f"nutrient_id={r['nutrient_id']}, got {cur.rowcount}")

        if record_run:
            cur.execute(
                "INSERT INTO cv_pipeline_run (pipeline_version, config_sha256, code_sha256, "
                "dataset_shas, gate_passed, signed_off_by, signed_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,now()) "
                "ON CONFLICT (pipeline_version) DO UPDATE SET config_sha256=EXCLUDED.config_sha256, "
                "code_sha256=EXCLUDED.code_sha256, dataset_shas=EXCLUDED.dataset_shas, "
                "gate_passed=EXCLUDED.gate_passed, signed_off_by=EXCLUDED.signed_off_by, signed_at=now()",
                (pv, csha, code, psycopg2.extras.Json(dshas), gate_ok, signer),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _summary(resolutions: list[dict]) -> None:
    tiers = Counter(r["resolution"]["cv_tier"] for r in resolutions)
    conf = Counter(r["resolution"]["cv_confidence_tier"] for r in resolutions)
    measured = sum(1 for r in resolutions if r["resolution"]["measured_cv"] is not None)
    print(f"Resolved {len(resolutions)} cells: {measured} measured (coefficient_of_variation), "
          f"{len(resolutions) - measured} category-only")
    print(f"  by tier:       {dict(tiers)}")
    print(f"  by confidence: {dict(conf)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="write to the live columns (gated)")
    ap.add_argument("--signed-off-by", type=str, help="signer name (required for --commit)")
    ap.add_argument("--food-id", type=int, help="resolve a single ingredient (incremental)")
    ap.add_argument("--skip-backup", action="store_true")
    args = ap.parse_args()

    resolutions = resolve_all(args.food_id)
    _summary(resolutions)

    from cv_report import evaluate_gate   # lazy import (avoids cycle)
    passed, failures = evaluate_gate(resolutions)
    print(f"\nQA gate: {'PASS' if passed else 'BLOCK'}")
    for f in failures:
        print(f"  - {f}")

    if not args.commit:
        print("\nDRY RUN — nothing written. Use --commit --signed-off-by NAME to apply.")
        return

    if not passed:
        raise SystemExit("Gate BLOCKED — refusing to write. Resolve the failures above.")
    if not args.signed_off_by:
        raise SystemExit("--commit requires --signed-off-by NAME.")

    if not args.skip_backup:
        try:
            from backfill_nutrients import backup_database
            backup_database(Path("backups"))
        except Exception as e:  # noqa: BLE001
            raise SystemExit(f"Backup failed ({e}). Use --skip-backup to override.")

    commit(resolutions, args.signed_off_by, full=(args.food_id is None))
    print(f"\nCommitted {len(resolutions)} cells (signed off by {args.signed_off_by}).")
    close_db()


if __name__ == "__main__":
    main()
