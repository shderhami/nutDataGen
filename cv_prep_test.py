#!/usr/bin/env python3
"""Statistical test: does COOKING shift the within-food batch CV vs RAW, within
each ingredient category and nutrient group?  (added-solution excluded.)

Design
------
Unit = one analytical within-food CV (SR28 real Std_Error: cv = SE*sqrt(n)/c4/mean),
kept only where method='se_sqrt_n' and 0 < cv < 1.5.  prep derived from description.

Two complementary tests per (ingredient_class x nutrient_family):
  * UNPAIRED  — Mann-Whitney U (median, distribution-free) + Welch t on log(cv).
                Effect size = Cliff's delta.
  * PAIRED    — same base food (prep tokens stripped) x nutrient measured BOTH raw
                and cooked; Wilcoxon signed-rank on (cooked-raw) + paired t on the
                log-ratio.  Removes the food-identity confound.

Because n is large, statistical significance is cheap; we therefore also report the
EFFECT SIZE and a practical-equivalence margin (EPS = 0.03 CV, i.e. 3 percentage
points).  A difference "matters" only if it is BOTH significant (BH-FDR q<0.05) AND
|median delta| > EPS.  Benjamini-Hochberg controls the false-discovery rate across
the family of unpaired tests.

Usage:  python cv_prep_test.py
"""
from __future__ import annotations

import os
import re
from collections import defaultdict

import numpy as np
import psycopg2
from scipy import stats

EPS = 0.03  # practical-equivalence margin, in CV units (3 percentage points)

FAMILY = {
    "amino_acid": "amino_acids",
    "major_mineral": "minerals_major",
    "trace_mineral": "minerals_trace", "se_i": "minerals_trace",
    "water_sol_vit": "vitamins_water", "choline": "vitamins_water",
    "fat_sol_vit": "vitamins_fat",
    "n3_long_chain": "fatty_acids", "n6_linoleic": "fatty_acids",
    "n3_terrestrial": "fatty_acids", "arachidonic": "fatty_acids",
    "fat": "proximates_fat", "low_cv_proximate": "proximates_fat",
}
FAM_ORDER = ["amino_acids", "minerals_major", "minerals_trace", "vitamins_water",
             "vitamins_fat", "fatty_acids", "proximates_fat"]
CLS_ORDER = ["muscle", "organ", "fish", "egg", "dairy", "fat_oil", "plant"]

RAW = re.compile(r"\braw\b", re.I)
SOL = re.compile(r"added solution|pre-basted|enhanced", re.I)
COOK = re.compile(r"\b(cooked|roasted|braised|boiled|grilled|stewed|pan-?fried|fried|"
                  r"baked|broiled|simmered|poached|steamed|microwaved)\b", re.I)
STRIP = re.compile(r"\b(raw|cooked|roasted|braised|boiled|grilled|stewed|pan-?fried|fried|"
                   r"baked|broiled|simmered|poached|steamed|microwaved|drained|"
                   r"with salt|without salt|solids?|liquids?)\b", re.I)


def prep(d: str) -> str:
    d = d or ""
    if SOL.search(d):
        return "added_solution"
    if RAW.search(d):
        return "raw"
    if COOK.search(d):
        return "cooked"
    return "other"


def stem(d: str) -> str:
    return re.sub(r"[ ,()]+", " ", STRIP.sub("", d or "")).strip().lower()


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """P(x>y) - P(x<y); robust nonparametric effect size."""
    ys = np.sort(y)
    gt = np.searchsorted(ys, x, side="left").sum()        # y strictly < x
    lt = (len(y) - np.searchsorted(ys, x, side="right")).sum()  # y strictly > x
    return (gt - lt) / (len(x) * len(y))


def bh_fdr(pvals: list[float]) -> list[float]:
    p = np.asarray(pvals, float)
    n = len(p)
    order = np.argsort(p)
    q = np.empty(n)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        idx = order[i]
        prev = min(prev, p[idx] * n / (i + 1))
        q[idx] = prev
    return q.tolist()


def interp_delta(d: float) -> str:
    a = abs(d)
    return ("negligible" if a < 0.147 else "small" if a < 0.33
            else "medium" if a < 0.474 else "large")


def main() -> None:
    c = psycopg2.connect(host=os.environ["DATABASE_HOST"], port=os.environ["DATABASE_PORT"],
                         dbname=os.environ["DATABASE_NAME"], user=os.environ["DATABASE_USER"],
                         password=os.environ["DATABASE_PASSWORD"])
    cur = c.cursor()
    cur.execute("""SELECT ingredient_class, nutrient_class, nutrient_name, source_food_desc, cv
                   FROM cv_observations
                   WHERE method='se_sqrt_n' AND cv IS NOT NULL AND cv>0 AND cv<1.5""")
    # cells[(cls,fam)][prep] = [cv...] ;  pairs[(cls,fam,stem,nutrient)][prep]=[cv...]
    cells: dict = defaultdict(lambda: defaultdict(list))
    pairs: dict = defaultdict(lambda: defaultdict(list))
    for ic, nc, nn, desc, cv in cur.fetchall():
        fam = FAMILY.get(nc)
        if fam is None:
            continue
        p = prep(desc)
        if p not in ("raw", "cooked"):   # added_solution & other excluded
            continue
        cv = float(cv)
        cells[(ic, fam)][p].append(cv)
        pairs[(ic, fam, stem(desc), nn)][p].append(cv)
    c.close()

    # ---- unpaired tests per (class, family) ----
    rows = []
    for ic in CLS_ORDER:
        for fam in FAM_ORDER:
            d = cells.get((ic, fam))
            if not d:
                continue
            r = np.array(d["raw"]); k = np.array(d["cooked"])
            if len(r) < 8 or len(k) < 8:
                continue
            mwu_p = stats.mannwhitneyu(k, r, alternative="two-sided").pvalue
            t_p = stats.ttest_ind(np.log(k), np.log(r), equal_var=False).pvalue
            rows.append({
                "cls": ic, "fam": fam, "nr": len(r), "nk": len(k),
                "med_r": float(np.median(r)), "med_k": float(np.median(k)),
                "dmed": float(np.median(k) - np.median(r)),
                "delta": cliffs_delta(k, r), "mwu_p": mwu_p, "t_p": t_p,
            })
    qs = bh_fdr([x["mwu_p"] for x in rows])
    for x, q in zip(rows, qs):
        x["q"] = q

    print("=" * 108)
    print("COOKED vs RAW within-food CV — UNPAIRED (Mann-Whitney U on CV, Welch t on log-CV)")
    print(f"significant = BH-FDR q<0.05 ; practically-relevant = |Δmedian| > {EPS}")
    print("=" * 108)
    hdr = (f"{'class':8s} {'nutrient family':16s} {'n_raw':>6s} {'n_cook':>6s} "
           f"{'medRAW':>7s} {'medCOOK':>7s} {'Δmed':>7s} {'Cliffδ':>8s} {'q(FDR)':>8s}  verdict")
    print(hdr); print("-" * len(hdr))
    n_relevant = 0
    for x in sorted(rows, key=lambda z: (CLS_ORDER.index(z["cls"]), FAM_ORDER.index(z["fam"]))):
        sig = x["q"] < 0.05
        relevant = sig and abs(x["dmed"]) > EPS
        n_relevant += relevant
        verdict = ("DIFFERENT" if relevant else
                   ("sig-but-tiny" if sig else "equivalent"))
        print(f"{x['cls']:8s} {x['fam']:16s} {x['nr']:6d} {x['nk']:6d} "
              f"{x['med_r']:7.3f} {x['med_k']:7.3f} {x['dmed']:+7.3f} "
              f"{x['delta']:+8.3f} {x['q']:8.4f}  {verdict} ({interp_delta(x['delta'])})")

    # ---- paired tests per family (pooled across classes) ----
    print("\n" + "=" * 108)
    print("COOKED vs RAW — PAIRED (same base food × nutrient, both forms present) — Wilcoxon signed-rank")
    print("=" * 108)
    fam_pairs: dict = defaultdict(list)   # fam -> [(raw_mean, cook_mean)]
    allpairs = []
    for (ic, fam, st, nn), d in pairs.items():
        if d["raw"] and d["cooked"]:
            pr, pk = float(np.mean(d["raw"])), float(np.mean(d["cooked"]))
            fam_pairs[fam].append((pr, pk)); allpairs.append((pr, pk))
    ph = f"{'nutrient family':16s} {'#pairs':>7s} {'medΔ(k-r)':>10s} {'medRatio':>9s} {'%cook>raw':>10s} {'Wilcoxon p':>11s}"
    print(ph); print("-" * len(ph))
    for fam in FAM_ORDER:
        pl = fam_pairs.get(fam, [])
        if len(pl) < 8:
            continue
        rr = np.array([a for a, _ in pl]); kk = np.array([b for _, b in pl])
        diff = kk - rr
        p = stats.wilcoxon(kk, rr).pvalue if np.any(diff != 0) else 1.0
        pct = 100 * np.mean(kk > rr)
        print(f"{fam:16s} {len(pl):7d} {np.median(diff):+10.3f} {np.median(kk/rr):9.3f} "
              f"{pct:9.0f}% {p:11.4g}")
    rr = np.array([a for a, _ in allpairs]); kk = np.array([b for _, b in allpairs])
    diff = kk - rr
    wp = stats.wilcoxon(kk, rr).pvalue
    tp = stats.ttest_rel(np.log(kk), np.log(rr)).pvalue
    print("-" * len(ph))
    print(f"{'ALL POOLED':16s} {len(allpairs):7d} {np.median(diff):+10.3f} {np.median(kk/rr):9.3f} "
          f"{100*np.mean(kk>rr):9.0f}% {wp:11.4g}")
    print(f"\nOverall paired: {len(allpairs)} food×nutrient pairs | median Δ(cook-raw)={np.median(diff):+.4f} "
          f"| median ratio={np.median(kk/rr):.3f} | Wilcoxon p={wp:.4g} | paired-t(logratio) p={tp:.4g}")

    print("\n" + "=" * 108)
    print(f"SUMMARY: {n_relevant} / {len(rows)} class×family cells are BOTH significant AND "
          f"practically different (|Δmed|>{EPS}).")
    print("=" * 108)


if __name__ == "__main__":
    main()
