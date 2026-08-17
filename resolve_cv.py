#!/usr/bin/env python3
"""The shared CV precedence ladder.

Used by cv_assign (the batch/`--food-id` incremental pass). NOTE: it is NOT
auto-wired into create_nutrient_record — a newly inserted ingredient carries NULL
CVs (consumer falls back to the flat 0.25) until `cv_assign.py --food-id <id>
--commit` (gate + sign-off) is run for it. That incremental run IS the per-insert
mechanism; the DB is never left with the wrong (legacy percent) CV.

resolve_cv() returns a dict of the two CV columns + provenance:
  measured_cv  -> ingredient_nutrients.coefficient_of_variation (own measured CV, Tiers 1-3,
                  or a corrector's delivered-spec CV, or None)
  category_cv  -> ingredient_nutrients.category_cv (pooled/prior/supplement, Tiers 4-6)
plus cv_tier / cv_method / cv_backing_n / cv_effective_n / cv_confidence_tier /
cv_class_key / cv_method_inputs / cv_calibration_flag.

cv_tier vocabulary: none | corrector | supplement | literature_range | sr28_se |
fdc_range | component | class_pool | nutrient_prior.

All CVs are FRACTIONS in (0, CV_CAP].  Consumer = COALESCE(measured, category).
"""
from __future__ import annotations

import math
from typing import Optional

import cv_config
import cv_stats

PRIOR_SENTINEL_CLASS = "_prior"
COARSE = -1


def load_cv_class(db) -> dict:
    """Build O(1) lookups from cv_class: fine (ic,nbr), coarse (ic,nclass), prior (nclass)."""
    fine, coarse, prior = {}, {}, {}
    with db.cursor() as cur:
        cur.execute("SELECT ingredient_class, nutrient_nbr, nutrient_class, pooled_cv, "
                    "n_foods, is_literature_prior FROM cv_class")
        for r in cur.fetchall():
            r = dict(r)
            if r["is_literature_prior"]:
                prior[r["nutrient_class"]] = r
            elif r["nutrient_nbr"] == COARSE:
                coarse[(r["ingredient_class"], r["nutrient_class"])] = r
            else:
                fine[(r["ingredient_class"], r["nutrient_nbr"])] = r
    return {"fine": fine, "coarse": coarse, "prior": prior}


def _key(r: dict) -> dict:
    return {"ingredient_class": r["ingredient_class"], "nutrient_nbr": r["nutrient_nbr"],
            "nutrient_class": r["nutrient_class"]}


def _calib_flag(cv_se: float, cv_range: float) -> bool:
    """True if a cell's SE-derived and range-derived CVs disagree materially."""
    if abs(cv_se - cv_range) > cv_config.CALIB_ABS_PP:
        return True
    if cv_se >= cv_config.CALIB_MIN_FLOOR and cv_range >= cv_config.CALIB_MIN_FLOOR:
        ratio = cv_se / cv_range if cv_range > 0 else float("inf")
        if ratio < cv_config.CALIB_RATIO_LO or ratio > cv_config.CALIB_RATIO_HI:
            return True
    return False


def _pool_class_keys(ingredient_class: str, subclass: Optional[str]) -> list[str]:
    """Ordered pool lookup keys, most-specific first. A muscle ingredient with a
    known subclass tries its poultry/red sub-pool, then the combined muscle pool."""
    if ingredient_class == "muscle" and subclass in ("poultry", "red"):
        return [f"muscle::{subclass}", "muscle"]
    return [ingredient_class]


def _class_prior(nutrient_id: int, ingredient_class: str, nutrient_class: str, lk: dict) -> float:
    """Biased-high Tier-5 prior (per-nutrient override > n-3 conditional > class prior)."""
    override = cv_config.PER_NUTRIENT_PRIOR.get(nutrient_id)
    if override is not None:
        return override
    if nutrient_class == "n3_long_chain":
        return cv_config.N3_LONG_CHAIN_PRIOR_BY_INGREDIENT.get(
            ingredient_class, cv_config.N3_LONG_CHAIN_PRIOR_BY_INGREDIENT["_default"])
    p = lk["prior"].get(nutrient_class)
    return float(p["pooled_cv"]) if p else 0.30


def _category(nutrient_id: int, class_keys: list[str], nutrient_nbr: int,
              nutrient_class: str, lk: dict):
    """Return (cv, tier, backing_n, class_key). Always resolves (prior is universal).

    class_keys is the ordered pool preference (sub-pool first, combined class last).
    A fine (same-nutrient) pool with >= k foods is used as-is (evidence-based, even if
    low). Otherwise the value is a coarse TRANSPLANT or the class prior, and for a
    Bucket-A critical nutrient it is FLOORED to the biased-high prior — so a pool built
    from *other* nutrients (e.g. taurine, which has zero observations, riding on the
    amino-acid coarse pool) can never ship a dangerously low buffer.
    """
    base_class = class_keys[-1]
    for ck in class_keys:                      # fine same-nutrient pool, sub-pool first
        fine = lk["fine"].get((ck, nutrient_nbr))
        if fine and fine["n_foods"] >= cv_config.K_MIN_FOODS:
            return float(fine["pooled_cv"]), "class_pool", fine["n_foods"], _key(fine)

    cv = tier = n = key = None
    for ck in class_keys:                      # coarse transplant, sub-pool first
        coarse = lk["coarse"].get((ck, nutrient_class))
        if coarse and coarse["n_foods"] >= cv_config.K_MIN_FOODS:
            cv, tier, n, key = float(coarse["pooled_cv"]), "class_pool", coarse["n_foods"], _key(coarse)
            break
    if cv is None:
        cv = _class_prior(nutrient_id, base_class, nutrient_class, lk)
        tier, n, key = "nutrient_prior", cv_config.EFFECTIVE_N_PRIOR, {"prior_class": nutrient_class}

    # Floor override (taurine) + Bucket-A biased-high floor — transplants/priors only.
    floor = cv_config.PER_NUTRIENT_PRIOR.get(nutrient_id) or 0.0
    if cv_config.bucket(nutrient_id) == "A":
        floor = max(floor, _class_prior(nutrient_id, base_class, nutrient_class, lk))
    if floor > cv:
        return floor, "nutrient_prior", cv_config.EFFECTIVE_N_PRIOR, {
            "prior_nutrient": nutrient_id, "floored_from": round(cv, 4)}
    return cv, tier, n, key


def _shrink_target(class_keys: list[str], nutrient_nbr: int, nutrient_class: str, lk: dict):
    """Measured cells shrink toward the measured pool (sub-pool + fine preferred).

    Only pools meeting K_MIN_FOODS are valid shrink targets — mirrors _category.
    Shrinking a measured CV toward a sub-threshold (n<k) pool is statistically
    unreliable and, since the pool CV can be lower, risks pulling the buffer DOWN."""
    for ck in class_keys:
        fine = lk["fine"].get((ck, nutrient_nbr))
        if fine and fine["n_foods"] >= cv_config.K_MIN_FOODS:
            return float(fine["pooled_cv"])
    for ck in class_keys:
        coarse = lk["coarse"].get((ck, nutrient_class))
        if coarse and coarse["n_foods"] >= cv_config.K_MIN_FOODS:
            return float(coarse["pooled_cv"])
    return None


def resolve_cv(*, nutrient_id: int, nutrient_nbr: Optional[int], ingredient_class: str,
               nutrient_class: str, category: str, value: Optional[float],
               subclass: Optional[str] = None, is_corrector: bool = False,
               own_min: Optional[float] = None, own_max: Optional[float] = None,
               own_n: Optional[int] = None,
               sr28_se_cv: Optional[float] = None, sr28_n: Optional[int] = None,
               sr28_method: Optional[str] = None, source: Optional[str] = None,
               component_cv: Optional[float] = None, component_n: Optional[int] = None,
               intl_cv: Optional[float] = None, intl_n: Optional[int] = None,
               intl_label: Optional[str] = None,
               lookups: dict) -> dict:
    base = {"measured_cv": None, "category_cv": None, "cv_tier": None, "cv_method": None,
            "cv_backing_n": None, "cv_effective_n": None, "cv_confidence_tier": None,
            "cv_class_key": None, "cv_method_inputs": None, "cv_calibration_flag": None}

    # 0. Non-nutritive / zero-mean carve-out -> both columns NULL, gate-exempt.
    if category in cv_config.NON_NUTRITIVE_CATEGORIES or value in (None, 0):
        return {**base, "cv_tier": "none"}

    # 1. Supplement / Fish-Oil pre-emption -> Tier-6 delivered floor (category column).
    #    A CORRECTOR additionally gets an own delivered-SPEC CV in the measured column:
    #    the whole-food floor overstates a manufactured single-nutrient product and would
    #    inflate the consumer's buffer (see cv_config.CORRECTOR_CV_*). The floor stays in
    #    category_cv so NULLing the own column falls back to the old behaviour.
    if category in cv_config.SUPPLEMENT_CATEGORIES:
        floor = (cv_config.SUPPLEMENT_DELIVERED_FLOOR_LABILE
                 if nutrient_id in cv_config.LABILE_ACTIVE_NUTRIENT_IDS
                 else cv_config.SUPPLEMENT_DELIVERED_FLOOR)
        out = {**base, "category_cv": round(floor, cv_config.ROUND_DECIMALS),
               "cv_tier": "supplement", "cv_method": "delivered_floor",
               "cv_effective_n": cv_config.EFFECTIVE_N_SUPPLEMENT, "cv_confidence_tier": "medium"}
        if is_corrector:
            spec = cv_config.corrector_cv(nutrient_id)
            out.update({
                "measured_cv": round(spec, cv_config.ROUND_DECIMALS),
                "cv_tier": "corrector", "cv_method": "delivered_spec",
                "cv_method_inputs": {"cv_spec": spec, "category_floor": floor},
            })
        return out

    # 2. Measured candidates (Tiers 1-3), best first. Method-aware: an SR28 row may
    #    be SE-derived (se_sqrt_n) OR range-derived (wan_range); only the former is
    #    Tier-1 'sr28_se'. The row's own min/max/n gives an independent range CV
    #    used both as a fallback measured candidate and for twin calibration.
    own_range_cv = cv_stats.cv_from_range(value, own_min, own_max, own_n)
    # Cross-source plausibility guard. sr28_se_cv is a BULK observation CV (matched by
    # food from cv_observations) — a DIFFERENT sample than the value, whose own-record
    # dispersion is the separate own_range_cv. A cross-sourced CV > 1.0 means SD > mean:
    # implausible as a within-ingredient BATCH CV and a tell the source sample mixes
    # distinct products (e.g. Vit-D-enriched vs conventional eggs). Reject it so the
    # ladder falls to the same-source own-range CV (if any) or the class pool. The
    # same-source own_range_cv is never guarded, so this fires only on cross-sourced CVs.
    cross_source_demoted = None
    if sr28_se_cv is not None and sr28_se_cv > cv_config.CROSS_SOURCE_CV_MAX:
        cross_source_demoted = round(sr28_se_cv, 6)
        sr28_se_cv = sr28_n = None
    measured_cv = measured_n = measured_tier = measured_method = m_inputs = None
    calib_flag = None
    # 2a. Literature-sourced value with its own coherent {min, max, n}: the row's
    #     stats ARE the same-source evidence (the validation workflow stores value
    #     and stats from one citation together), while sr28/component candidates
    #     describe the superseded USDA estimate of a different sample. Bracket
    #     guard: a mean always lies within its own range, so stats that fail it
    #     are stale leftovers from an overridden value and must not drive a CV.
    if (source == "literature" and own_range_cv is not None
            and own_min is not None and own_max is not None
            and own_min <= value <= own_max):
        measured_cv, measured_n = own_range_cv, own_n
        measured_tier, measured_method = "literature_range", "wan_range"
        m_inputs = {"min": own_min, "max": own_max, "n": own_n}
        if sr28_se_cv is not None:
            m_inputs["superseded_bulk_cv"] = round(sr28_se_cv, 6)
        if component_cv is not None:
            m_inputs["superseded_component_cv"] = round(component_cv, 6)
    elif sr28_se_cv is not None:
        is_se = (sr28_method == "se_sqrt_n")
        measured_cv, measured_n = sr28_se_cv, sr28_n
        measured_tier = "sr28_se" if is_se else "fdc_range"
        measured_method = "se_sqrt_n" if is_se else "wan_range"
        m_inputs = ({"cv_se": round(sr28_se_cv, 6), "n": sr28_n} if is_se
                    else {"cv_range": round(sr28_se_cv, 6), "n": sr28_n})
        # Twin SE-vs-range calibration — only a valid twin when the row's own range
        # is the SAME food as the SR28 SE (i.e. the value came from SR-Legacy); a
        # Foundation-sourced row is a different food. Clip both arms to CV_CAP.
        if is_se and own_range_cv is not None and source == "sr_legacy":
            own_clip, _ = cv_stats.clip_cv(own_range_cv, cv_config.CV_CAP)
            calib_flag = _calib_flag(sr28_se_cv, own_clip)
            m_inputs["calib_abs_diff"] = round(abs(sr28_se_cv - own_clip), 6)
    elif component_cv is not None:
        measured_cv, measured_n, measured_tier, measured_method = component_cv, component_n, "component", "retinol"
        m_inputs = {"cv_component": round(component_cv, 6), "n": component_n}
    elif own_range_cv is not None:
        measured_cv, measured_n, measured_tier, measured_method = own_range_cv, own_n, "fdc_range", "wan_range"
        m_inputs = {"min": own_min, "max": own_max, "n": own_n}
        if cross_source_demoted is not None:   # kept the same-source range; noted for audit
            m_inputs["cross_source_demoted_cv"] = cross_source_demoted

    # 2b. International same-food pooling (cv-v8): blend the measured CV with a
    #     matched foreign observation at its DISCOUNTED effective n
    #     (n_eff = 1/(1/n + 2*sigma^2); sigma^2 is measured — cv_config.INTL_CV_SIGMA2).
    #     literature_range cells are skipped: their own stats are often the very
    #     same foreign source, and pooling would double-count one dataset.
    if (intl_cv is not None and intl_n and measured_cv is not None and measured_cv > 0
            and intl_cv > 0 and measured_tier in ("sr28_se", "fdc_range", "component")):
        n_eff = 1.0 / (1.0 / intl_n + 2.0 * cv_config.INTL_CV_SIGMA2)
        base_n = measured_n or 1
        w_us = base_n / (base_n + n_eff)
        pooled = math.exp(w_us * math.log(measured_cv) + (1.0 - w_us) * math.log(intl_cv))
        m_inputs = dict(m_inputs or {})
        m_inputs["intl"] = {"us_cv": round(measured_cv, 6), "cv": round(intl_cv, 6),
                            "n": intl_n, "n_eff": round(n_eff, 2),
                            "w_us": round(w_us, 3), "source": intl_label}
        measured_cv = pooled
        measured_n = base_n + max(1, round(n_eff))
        measured_method = f"{measured_method}+intl"

    # 3. Category (Tiers 4-5) — always resolves. class_keys puts a muscle poultry/red
    #    sub-pool ahead of the combined muscle pool.
    class_keys = _pool_class_keys(ingredient_class, subclass)
    cat_cv, cat_tier, cat_n, cat_key = _category(nutrient_id, class_keys, nutrient_nbr, nutrient_class, lookups)
    cat_cv = max(cat_cv, cv_config.CV_FLOOR)
    cat_cv, _ = cv_stats.clip_cv(cat_cv, cv_config.CV_CAP)
    base["category_cv"] = round(cat_cv, cv_config.ROUND_DECIMALS)

    if measured_cv is None:
        # No measurement: consumer will use category. Confidence from the category tier.
        if cat_tier == "class_pool" and cat_n >= cv_config.K_MIN_FOODS:
            conf, eff = "medium", cat_n
        else:
            conf, eff = "low", cv_config.EFFECTIVE_N_PRIOR
        return {**base, "cv_tier": cat_tier, "cv_method": "pool" if cat_tier == "class_pool" else "prior",
                "cv_backing_n": cat_n, "cv_effective_n": eff, "cv_confidence_tier": conf,
                "cv_class_key": cat_key,
                # Provenance: a cross-sourced measured CV was rejected (SD>mean) and this
                # cell fell to the pool — recorded in cv_method_inputs (cv_calibration_flag
                # is a boolean column, owned by the SE-vs-range twin flag; leave it None).
                "cv_method_inputs": ({"cross_source_demoted_cv": cross_source_demoted}
                                     if cross_source_demoted else None)}

    # 4. Shrink the measured cell toward the measured pool (log scale); skip downward for Bucket-A.
    class_cv = _shrink_target(class_keys, nutrient_nbr, nutrient_class, lookups)
    w = 1.0
    if class_cv is not None and measured_cv > 0 and class_cv > 0 and measured_n:
        w = measured_n / (measured_n + cv_config.N0_SHRINKAGE)
        if cv_config.bucket(nutrient_id) == "A" and class_cv < measured_cv:
            w = 1.0                                       # keep the higher measured CV
        else:
            measured_cv = math.exp(w * math.log(measured_cv) + (1 - w) * math.log(class_cv))
    measured_cv = max(measured_cv, cv_config.CV_FLOOR)
    measured_cv, _ = cv_stats.clip_cv(measured_cv, cv_config.CV_CAP)

    backing = measured_n or 0
    # 'high' only for genuine SE-derived, well-sampled, barely-shrunk cells.
    high = (measured_tier == "sr28_se" and backing >= cv_config.BACKING_N_HIGH
            and w >= cv_config.W_HIGH)
    eff = backing + (cv_config.N0_SHRINKAGE if w < 1.0 else 0)
    return {**base, "measured_cv": round(measured_cv, cv_config.ROUND_DECIMALS),
            "cv_tier": measured_tier, "cv_method": measured_method, "cv_backing_n": backing,
            "cv_effective_n": eff, "cv_confidence_tier": "high" if high else "medium",
            # A measured cell's provenance is the measurement (+ shrink); do NOT attach
            # the category fallback key (which may be a floored-prior dict for Bucket-A).
            "cv_class_key": None, "cv_method_inputs": {**(m_inputs or {}), "shrink_w": round(w, 3)},
            "cv_calibration_flag": calib_flag}


if __name__ == "__main__":
    from db_connection import get_db
    lk = load_cv_class(get_db())
    demos = [
        dict(nutrient_id=1098, nutrient_nbr=312, ingredient_class="organ", nutrient_class="trace_mineral",
             category="Organ Meat", value=5.0, sr28_se_cv=0.30, sr28_n=8),        # measured Cu, Bucket-B
        dict(nutrient_id=1103, nutrient_nbr=317, ingredient_class="muscle", nutrient_class="se_i",
             category="Muscle Meat", value=20.0, own_min=3.0, own_max=47.0, own_n=11),  # own-range Se
        dict(nutrient_id=1234, nutrient_nbr=529, ingredient_class="supplement", nutrient_class="amino_acid",
             category="Supplement", value=1000.0),                                 # taurine supplement (labile)
        dict(nutrient_id=1234, nutrient_nbr=529, ingredient_class="supplement", nutrient_class="amino_acid",
             category="Supplement", value=1000.0, is_corrector=True),              # taurine CORRECTOR
        dict(nutrient_id=1109, nutrient_nbr=323, ingredient_class="supplement", nutrient_class="fat_sol_vit",
             category="Supplement", value=14.9, is_corrector=True),                # Vit E corrector (high-CV)
        dict(nutrient_id=1106, nutrient_nbr=320, ingredient_class="plant", nutrient_class="fat_sol_vit",
             category="Plant Matter", value=10.0),                                 # Vit A, no measurement -> category
        dict(nutrient_id=1051, nutrient_nbr=255, ingredient_class="base", nutrient_class="low_cv_proximate",
             category="Base", value=0.0),                                          # water zero-mean carve-out
    ]
    for d in demos:
        r = resolve_cv(lookups=lk, **d)
        print(f"nid={d['nutrient_id']:5d} {d['ingredient_class']:10s} -> "
              f"measured={r['measured_cv']} category={r['category_cv']} "
              f"tier={r['cv_tier']} conf={r['cv_confidence_tier']} eff_n={r['cv_effective_n']}")
