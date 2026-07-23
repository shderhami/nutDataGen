#!/usr/bin/env python3
"""Pool cv_observations -> cv_class (fine + coarse rungs + Tier-5 priors).

Lineage dedup (SR28 + FDC-SR-Legacy are the same food -> count once, prefer the
SR28 SE row; FDC Foundation kept as independent) then an unweighted median
(percentile_disc) of the per-food CVs per (ingredient_class x nutrient).

Usage:  python cv_pool.py [--dry-run]
"""
from __future__ import annotations

import argparse
import math
from collections import Counter, defaultdict

import psycopg2.extras

import cv_config
from db_connection import get_db, close_db

PRIOR_SENTINEL_CLASS = "_prior"
COARSE = -1


def _pd(vals_sorted: list[float], p: float) -> float:
    """percentile_disc: first value whose cumulative fraction >= p."""
    n = len(vals_sorted)
    idx = min(max(math.ceil(p * n) - 1, 0), n - 1)
    return vals_sorted[idx]


def _dedup(rows: list[dict]) -> list[dict]:
    """Collapse SR28<->FDC-SRL twins by (lineage_pair_id, nutrient_nbr), prefer SR28.
    Foundation rows (lineage_pair_id NULL) are independent and all kept."""
    best: dict[tuple, dict] = {}
    kept_null: list[dict] = []
    for r in rows:
        lp = r["lineage_pair_id"]
        if lp is None:
            kept_null.append(r)
            continue
        k = (lp, r["nutrient_nbr"])
        cur = best.get(k)
        if cur is None or (r["source_dataset"] == "sr28" and cur["source_dataset"] != "sr28"):
            best[k] = r
    return list(best.values()) + kept_null


def _pool_row(ic: str, nbr: int, nclass: str, rows: list[dict]) -> dict | None:
    deduped = _dedup(rows)
    cvs = sorted(float(r["cv"]) for r in deduped)
    if not cvs:
        return None
    clipped = sum(1 for c in cvs if c >= cv_config.CV_CAP)
    return {
        "ingredient_class": ic, "nutrient_nbr": nbr, "nutrient_class": nclass,
        "pooled_cv": round(_pd(cvs, 0.5), cv_config.ROUND_DECIMALS),
        "n_foods": len(cvs),
        "pooling_method": cv_config.POOLING_METHOD,
        "cv_p25": round(_pd(cvs, 0.25), cv_config.ROUND_DECIMALS),
        "cv_p75": round(_pd(cvs, 0.75), cv_config.ROUND_DECIMALS),
        "source_mix": psycopg2.extras.Json(dict(Counter(r["source_dataset"] for r in deduped))),
        "method_mix": psycopg2.extras.Json(dict(Counter(r["method"] for r in deduped))),
        "floor_clipped_frac": round(clipped / len(cvs), 4),
        "is_literature_prior": False, "prior_citation": None,
        "pipeline_version": cv_config.PIPELINE_VERSION,
    }


def build_pools() -> list[dict]:
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT ingredient_class, nutrient_nbr, nutrient_class, source_dataset, "
            "method, lineage_pair_id, cv, source_food_desc FROM cv_observations "
            "ORDER BY source_dataset, source_food_id"      # deterministic
        )
        obs = [dict(r) for r in cur.fetchall()]

    fine: dict[tuple, list] = defaultdict(list)      # (ic, nbr) -> rows
    coarse: dict[tuple, list] = defaultdict(list)    # (ic, nclass) -> rows
    for r in obs:
        ic, nbr, nclass = r["ingredient_class"], r["nutrient_nbr"], r["nutrient_class"]
        fine[(ic, nbr)].append(r)
        coarse[(ic, nclass)].append(r)
        # Muscle sub-pools (poultry/red) in addition to the combined muscle pool,
        # keyed as pseudo-classes 'muscle::poultry' / 'muscle::red'. resolve_cv tries
        # the sub-pool first and falls back to the combined 'muscle' pool.
        if ic == "muscle":
            sub = cv_config.muscle_subclass(r["source_food_desc"])
            if sub:
                sk = f"muscle::{sub}"
                fine[(sk, nbr)].append(r)
                coarse[(sk, nclass)].append(r)

    pools: list[dict] = []
    for (ic, nbr), rows in fine.items():
        row = _pool_row(ic, nbr, rows[0]["nutrient_class"], rows)
        if row:
            pools.append(row)
    for (ic, nclass), rows in coarse.items():
        row = _pool_row(ic, COARSE, nclass, rows)
        if row:
            pools.append(row)

    # Tier-5 literature priors (universal, keyed on nutrient_class).
    for nclass, prior in cv_config.NUTRIENT_PRIORS.items():
        pools.append({
            "ingredient_class": PRIOR_SENTINEL_CLASS, "nutrient_nbr": COARSE,
            "nutrient_class": nclass, "pooled_cv": round(prior, cv_config.ROUND_DECIMALS),
            "n_foods": 0, "pooling_method": "literature_prior",
            "cv_p25": None, "cv_p75": None, "source_mix": psycopg2.extras.Json({}),
            "method_mix": psycopg2.extras.Json({}), "floor_clipped_frac": None,
            "is_literature_prior": True,
            "prior_citation": cv_config.PRIOR_CITATIONS.get(
                nclass, cv_config.PRIOR_CITATION_SENTINEL),
            "pipeline_version": cv_config.PIPELINE_VERSION,
        })
    return pools


_COLS = ["ingredient_class", "nutrient_nbr", "nutrient_class", "pooled_cv", "n_foods",
         "pooling_method", "cv_p25", "cv_p75", "source_mix", "method_mix",
         "floor_clipped_frac", "is_literature_prior", "prior_citation", "pipeline_version"]


def write(pools: list[dict]) -> int:
    db = get_db()
    with db.cursor() as cur:
        cur.execute("DELETE FROM cv_class")
        rows = [tuple(p[c] for c in _COLS) for p in pools]
        psycopg2.extras.execute_values(
            cur, f"INSERT INTO cv_class ({','.join(_COLS)}) VALUES %s", rows, page_size=500,
        )
    return len(pools)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pools = build_pools()
    fine = [p for p in pools if p["nutrient_nbr"] != COARSE]
    coarse = [p for p in pools if p["nutrient_nbr"] == COARSE and not p["is_literature_prior"]]
    priors = [p for p in pools if p["is_literature_prior"]]
    thin = [p for p in fine if p["n_foods"] < cv_config.K_MIN_FOODS]
    print(f"Pools: {len(fine)} fine + {len(coarse)} coarse + {len(priors)} priors")
    print(f"  fine pools below k={cv_config.K_MIN_FOODS}: {len(thin)}")
    if args.dry_run:
        print("DRY RUN — cv_class not written.")
        return
    print(f"Wrote {write(pools)} rows to cv_class.")
    close_db()


if __name__ == "__main__":
    main()
