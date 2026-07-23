#!/usr/bin/env python3
"""Two-group CV comparisons, stratified by nutrient family:
  * ORGAN : liver vs heart
  * MUSCLE: poultry vs red meat

Unit = within-food CV (SR28 real-SE, method='se_sqrt_n', 0<cv<1.5) from the cleaned
cv_observations (raw+native, curated). Per (comparison × nutrient family):
  * Welch's t-test on log(CV)   — the requested test, on the modeling scale
  * Mann-Whitney U on CV        — distribution-free median check
  * Cliff's delta               — nonparametric effect size (sign = A>B)
  * BH-FDR across families within each comparison
n is reported at BOTH the observation and distinct-food level (obs within a family
are pseudo-replicated — several nutrients per food — so a per-food robustness t-test
on mean-CV-per-food is also run). "DIFFERENT" = FDR-significant AND |Δmedian|>0.03.

Usage:  python cv_group_test.py
"""
from __future__ import annotations

import os
import re
from collections import defaultdict

import numpy as np
import psycopg2
from scipy import stats

from cv_prep_test import FAMILY, FAM_ORDER, cliffs_delta, bh_fdr, interp_delta

EPS = 0.03

COMPARISONS = [
    {"name": "ORGAN — liver vs heart", "class": "organ",
     "A": ("liver", re.compile(r"\bliver\b", re.I)),
     "B": ("heart", re.compile(r"\bheart\b", re.I))},
    {"name": "MUSCLE — poultry vs red meat", "class": "muscle",
     "A": ("poultry", re.compile(r"\b(chicken|turkey|duck|goose|quail|pheasant|cornish|guinea|squab|hen|fowl)\b", re.I)),
     "B": ("red meat", re.compile(r"\b(beef|pork|lamb|veal|bison|goat|mutton|venison|elk|moose|rabbit|boar|buffalo)\b", re.I))},
]


def run(cur, comp) -> None:
    A_lab, A_re = comp["A"]; B_lab, B_re = comp["B"]
    cur.execute("""SELECT source_food_desc, nutrient_class, cv, source_food_id
                   FROM cv_observations
                   WHERE ingredient_class=%s AND method='se_sqrt_n' AND cv>0 AND cv<1.5""",
                (comp["class"],))
    # cv[fam][grp]=[cv] ; foodcv[fam][grp][food]=[cv]
    cvs = defaultdict(lambda: defaultdict(list))
    foodcv = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for desc, nc, cv, sid in cur.fetchall():
        fam = FAMILY.get(nc)
        if fam is None:
            continue
        a, b = bool(A_re.search(desc or "")), bool(B_re.search(desc or ""))
        grp = A_lab if (a and not b) else B_lab if (b and not a) else None
        if grp is None:
            continue
        cvs[fam][grp].append(float(cv))
        foodcv[fam][grp][sid].append(float(cv))

    rows = []
    for fam in FAM_ORDER:
        A = np.array(cvs[fam][A_lab]); B = np.array(cvs[fam][B_lab])
        if len(A) < 8 or len(B) < 8:
            continue
        welch_p = stats.ttest_ind(np.log(A), np.log(B), equal_var=False).pvalue
        mwu_p = stats.mannwhitneyu(A, B, alternative="two-sided").pvalue
        # per-food robustness: one mean-CV per distinct food, then Welch t on log
        fa = np.array([np.mean(v) for v in foodcv[fam][A_lab].values()])
        fb = np.array([np.mean(v) for v in foodcv[fam][B_lab].values()])
        food_p = (stats.ttest_ind(np.log(fa), np.log(fb), equal_var=False).pvalue
                  if len(fa) >= 3 and len(fb) >= 3 else float("nan"))
        rows.append({
            "fam": fam, "nA": len(A), "nB": len(B), "fA": len(fa), "fB": len(fb),
            "mA": float(np.median(A)), "mB": float(np.median(B)),
            "dmed": float(np.median(A) - np.median(B)),
            "delta": cliffs_delta(A, B), "welch_p": welch_p, "mwu_p": mwu_p, "food_p": food_p,
        })
    # BH-FDR on BOTH the observation-level (pseudo-replicated, descriptive only) and
    # the per-food independent-unit test. The VERDICT gates on the per-food q so it is
    # not a pseudo-replication artifact (many nutrient CVs per food inflate obs-level n).
    for x, q in zip(rows, bh_fdr([r["welch_p"] for r in rows] or [1.0])):
        x["q"] = q
    food_ps = [(r["food_p"] if r["food_p"] == r["food_p"] else 1.0) for r in rows]  # nan -> 1
    for x, fq in zip(rows, bh_fdr(food_ps or [1.0])):
        x["food_q"] = fq

    print("\n" + "=" * 116)
    print(f"{comp['name']}   (A = {A_lab}, B = {B_lab})   Welch t on log-CV; VERDICT gates on per-food q; Cliff δ sign: +→{A_lab} higher")
    print("=" * 116)
    h = (f"{'nutrient family':16s} {A_lab[:8]:>18s} {B_lab[:8]:>18s} {'Δmed':>7s} "
         f"{'Cliffδ':>8s} {'obs q':>8s} {'FOOD q':>8s}  verdict")
    print(h); print("-" * len(h))
    ndiff = 0
    for x in rows:
        sig = x["food_q"] < 0.05                    # primary: independent-unit (per-food) test
        rel = sig and abs(x["dmed"]) > EPS
        ndiff += rel
        verdict = ("DIFFERENT" if rel
                   else "obs-only(pseudo-rep)" if x["q"] < 0.05      # obs-sig but not per-food
                   else "equivalent")
        ca = f"{x['mA']:.3f} [{x['nA']:3d}/{x['fA']:2d}f]"
        cb = f"{x['mB']:.3f} [{x['nB']:3d}/{x['fB']:2d}f]"
        print(f"{x['fam']:16s} {ca:>18s} {cb:>18s} {x['dmed']:+7.3f} {x['delta']:+8.3f} "
              f"{x['q']:8.4g} {x['food_q']:8.4g}  {verdict} ({interp_delta(x['delta'])})")
    print(f"  -> {ndiff}/{len(rows)} families DIFFERENT by the per-food test (FOOD q<0.05 AND |Δmed|>{EPS})")


def main() -> None:
    c = psycopg2.connect(host=os.environ["DATABASE_HOST"], port=os.environ["DATABASE_PORT"],
                         dbname=os.environ["DATABASE_NAME"], user=os.environ["DATABASE_USER"],
                         password=os.environ["DATABASE_PASSWORD"])
    cur = c.cursor()
    for comp in COMPARISONS:
        run(cur, comp)
    c.close()


if __name__ == "__main__":
    main()
