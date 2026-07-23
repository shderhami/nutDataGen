#!/usr/bin/env python3
"""QA gate + review report for the resolved CVs.

evaluate_gate() is the machine-checkable ship/block gate (imported by cv_assign
before it commits). main() prints the full review report for human sign-off.

Usage:  python cv_report.py
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict

import cv_config
from resolve_cv import resolve_cv  # noqa: F401  (kept for symmetry / future use)


def evaluate_gate(resolutions: list[dict]) -> tuple[bool, list[str]]:
    """Return (passed, failures). Hard blocks only; warnings live in the report."""
    failures: list[str] = []
    n = len(resolutions) or 1

    prior_only = [r for r in resolutions if r["resolution"]["cv_tier"] == "nutrient_prior"]

    # 1. No Bucket-A / critical nutrient may ship below 0.25 via a bare prior OR a
    #    coarse (transplanted) class pool. Fine same-nutrient pools are exempt (they
    #    are the intended evidence-based outputs).
    for r in resolutions:
        res = r["resolution"]
        if cv_config.bucket(r["nutrient_id"]) != "A":
            continue
        eff = res["measured_cv"] if res["measured_cv"] is not None else res["category_cv"]
        if eff is None:
            continue   # zero-mean / Base carve-out
        key = res["cv_class_key"] or {}
        is_transplant = res["cv_tier"] == "nutrient_prior" or (
            res["cv_tier"] == "class_pool" and key.get("nutrient_nbr") == -1)
        if is_transplant and float(eff) < cv_config.CONSUMER_NULL_FALLBACK_CV:
            failures.append(
                f"Bucket-A nutrient {r['nutrient_id']} (food {r['food_id']}) ships {eff} "
                f"< {cv_config.CONSUMER_NULL_FALLBACK_CV} via {res['cv_tier']} transplant")

    # 2. Too many cells falling to the literature prior.
    frac = len(prior_only) / n
    if frac > cv_config.MAX_PRIOR_ONLY_FRAC:
        failures.append(f"prior-only fraction {frac:.2f} > {cv_config.MAX_PRIOR_ONLY_FRAC}")

    # 3. Vitamin A retinol proxy must never fire on non-animal tissue.
    for r in resolutions:
        if (r["resolution"]["cv_method"] == "retinol"
                and r["ingredient_class"] not in cv_config.ANIMAL_TISSUE_CLASSES):
            failures.append(f"Vit A via retinol on non-animal food {r['food_id']}")

    # 4. Twin SE-vs-range calibration: block on SYSTEMATIC (median) divergence, not
    #    per-cell noise (the two estimators agree ~1pp at the median empirically).
    diffs = [mi["calib_abs_diff"] for r in resolutions
             if (mi := r["resolution"]["cv_method_inputs"]) and "calib_abs_diff" in mi]
    if diffs:
        med = statistics.median(diffs)
        if med > cv_config.CALIB_MAX_MEDIAN_DIVERGENCE:
            failures.append(
                f"calibration median |cv_se-cv_range| {med:.3f} > "
                f"{cv_config.CALIB_MAX_MEDIAN_DIVERGENCE} — systematic SE-vs-range "
                f"divergence over {len(diffs)} same-food twins (possible parse/unit bug)")
        worst = max(diffs)
        if worst > cv_config.CALIB_MAX_TWIN_DIVERGENCE:
            failures.append(
                f"calibration worst twin |cv_se-cv_range| {worst:.3f} > "
                f"{cv_config.CALIB_MAX_TWIN_DIVERGENCE} — localized SE/range error")

    # 5. No literature prior may ship uncited (sentinel/null citation).
    uncited = set()
    for r in resolutions:
        if r["resolution"]["cv_tier"] == "nutrient_prior":
            cit = cv_config.PRIOR_CITATIONS.get(r["nutrient_class"])
            if not cit or cv_config.PRIOR_CITATION_SENTINEL in cit:
                uncited.add(r["nutrient_class"])
    for nc in sorted(uncited):
        failures.append(f"literature prior for nutrient_class '{nc}' is uncited")

    return (len(failures) == 0, failures)


def build_report(resolutions: list[dict]) -> str:
    n = len(resolutions)
    tiers = Counter(r["resolution"]["cv_tier"] for r in resolutions)
    conf = Counter(r["resolution"]["cv_confidence_tier"] for r in resolutions)
    measured = [r for r in resolutions if r["resolution"]["measured_cv"] is not None]

    lines = ["=" * 64, "CV PIPELINE — REVIEW REPORT", "=" * 64,
             f"cells: {n}   measured (coefficient_of_variation): {len(measured)} "
             f"({100 * len(measured) // (n or 1)}%)   category-only: {n - len(measured)}",
             f"tiers:       {dict(tiers)}",
             f"confidence:  {dict(conf)}"]

    twin_diffs = [mi["calib_abs_diff"] for r in resolutions
                  if (mi := r["resolution"]["cv_method_inputs"]) and "calib_abs_diff" in mi]
    if twin_diffs:
        lines.append(f"calibration: {len(twin_diffs)} same-food SE-vs-range twins, "
                     f"median |diff| {statistics.median(twin_diffs):.3f}, worst {max(twin_diffs):.3f}")
    else:
        lines.append("calibration: 0 same-food twins (abstain — no SR-Legacy-sourced measured cells)")

    # Diff vs the incumbent flat 25%
    deltas = []
    for r in resolutions:
        res = r["resolution"]
        eff = res["measured_cv"] if res["measured_cv"] is not None else res["category_cv"]
        if eff is not None:
            deltas.append(float(eff) - 0.25)
    if deltas:
        below = sum(1 for d in deltas if d < 0)
        lines.append(f"vs flat 0.25:  {below}/{len(deltas)} cells BELOW 0.25 "
                     f"(mean effective CV {sum(float(r['resolution']['measured_cv'] or r['resolution']['category_cv'] or 0) for r in resolutions)/(n or 1):.3f})")

    # Per-ingredient measured coverage
    by_food = defaultdict(lambda: [0, 0])
    for r in resolutions:
        by_food[r["food_id"]][0 if r["resolution"]["measured_cv"] is not None else 1] += 1
    lines.append(f"\nper-ingredient (measured / category-only), {len(by_food)} ingredients:")
    for fid in sorted(by_food):
        m, c = by_food[fid]
        lines.append(f"  food {fid}: measured={m:2d}  category-only={c:2d}")

    # Prior-cell status (non-blocking): warn only on genuinely UNCITED priors.
    prior_cells = [r for r in resolutions if r["resolution"]["cv_tier"] == "nutrient_prior"]
    if prior_cells:
        def _uncited(nc: str) -> bool:
            cit = cv_config.PRIOR_CITATIONS.get(nc)
            return not cit or cv_config.PRIOR_CITATION_SENTINEL in cit
        uncited = sum(1 for r in prior_cells if _uncited(r["nutrient_class"]))
        if uncited:
            lines.append(f"\nWARN: {uncited} of {len(prior_cells)} literature-prior cells are "
                         "UNCITED (sentinel/missing) — fill before final ship.")
        else:
            lines.append(f"\nNOTE: {len(prior_cells)} cells on literature prior — every class prior "
                         "carries a verified citation (see cv_config.PRIOR_CITATIONS).")

    passed, failures = evaluate_gate(resolutions)
    lines.append("\n" + "-" * 64)
    lines.append(f"GATE: {'PASS' if passed else 'BLOCK'}")
    for f in failures:
        lines.append(f"  BLOCK: {f}")
    lines.append("-" * 64)
    return "\n".join(lines)


def main() -> None:
    from cv_assign import resolve_all
    print(build_report(resolve_all()))


if __name__ == "__main__":
    main()
