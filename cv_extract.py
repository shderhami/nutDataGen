#!/usr/bin/env python3
"""Extract per-source-food CVs from the pinned USDA bulk snapshots -> cv_observations.

SR28 (real SE, Tier 1) + FDC SR-Legacy/Foundation (Wan range, Tier 2). Excludes
calculated/imputed values, drops min==max, classifies each source food into an
ingredient_class, and writes a single-live-version cv_observations table.

Usage:  python cv_extract.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

import psycopg2.extras

import cv_config
import cv_sources
import cv_stats
from build_nutrient_crosswalk import build_crosswalk
from db_connection import get_db, close_db

# Composite/branded curation keep-set (LLM + keyword, see cv_curation*.py).
# {(ingredient_class, source_food_id)} of foods vetted as clean single-ingredient
# foods of their class. Loaded lazily; None = not applied (loud warning).
_CURATION_KEEP: set[tuple[str, str]] | None = None
_DROP_STATS: Counter = Counter()   # why observations were dropped (for the run report)


def load_curation_keepset() -> set[tuple[str, str]] | None:
    path = Path(__file__).parent / "data" / "cv_curation" / "merged" / "final_keep_ids.json"
    if not path.exists():
        print(f"WARNING: curation keep-set {path} not found — composite/branded "
              "curation NOT applied (run cv_curation.py + cv_curation_merge.py first).",
              file=sys.stderr)
        return None
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "keep" in data:      # versioned format
        kset_ver = data.get("pipeline_version")
        if kset_ver != cv_config.PIPELINE_VERSION:
            print(f"WARNING: curation keep-set was built under pipeline_version "
                  f"{kset_ver!r} but current is {cv_config.PIPELINE_VERSION!r}. If the "
                  "classifier changed, regenerate it (cv_curation.py + cv_curation_merge.py) "
                  "or clean foods may be orphaned by a changed (class, food_id) key.",
                  file=sys.stderr)
        data = data["keep"]
    return {(cls, str(sid)) for cls, ids in data.items() for sid in ids}

# ── source-food classifier (USDA description -> ingredient_class) ─────────────
_ORGAN = re.compile(r"\b(liver|kidney|heart|gizzard|spleen|brain|tongue|tripe|giblet|lung|sweetbread)s?\b", re.I)
_SPECIES = re.compile(r"\b(beef|chicken|pork|turkey|lamb|veal|duck|goose|bison|goat|sheep|mutton|rabbit|quail|game|venison|emu|ostrich)\b", re.I)
_FISH = re.compile(r"\b(salmon|tuna|cod|sardine|mackerel|herring|trout|tilapia|halibut|pollock|anchovy|fish|shrimp|crab|lobster|mussel|clam|oyster|scallop|squid|catfish|bass|snapper|flounder|sole|haddock|perch|carp)\b", re.I)
_DAIRY = re.compile(r"\b(milk|cheese|yogurt|yoghurt|butter|cream|dairy|whey|kefir)\b", re.I)
# fat_oil: pressed oils + rendered animal fats + pure adipose. Broadened so the pool
# is ready if a whole-food fat (poultry/beef fat, ghee, suet, separable fat) is added.
_OIL = re.compile(
    r"\b(oil|lard|tallow|suet|schmaltz|ghee|shortening|drippings"
    r"|(?:chicken|duck|goose|turkey|beef|pork|mutton|lamb|veal|bison)\s+fat"
    r"|fat,?\s*(?:chicken|duck|goose|turkey|beef|pork|mutton|lamb|veal|bison)"
    r"|separable\s+fat|fat\s+only)\b", re.I)
# 'oyster mushroom' / 'scallop squash' are plants — keep them out of the fish pool.
_FISH_PLANT_FP = re.compile(r"\b(mushrooms?|squash)\b", re.I)
_MUSCLE_CUT = re.compile(r"\b(thigh|breast|drumstick|wing|leg|meat|broiler|round|loin|chuck|rib|flank|sirloin|ground|steak|brisket|shank|tenderloin|skirt|fillet|filet|cutlet|roast|dark meat|light meat)\b", re.I)
_PLANT = re.compile(r"\b(vegetable|potato|sweet potato|carrot|peas?|beans?|lentil|chickpea|soybean|spinach|broccoli|pumpkin|squash|zucchini|kale|cabbage|lettuce|greens|rice|oats?|wheat|corn|maize|barley|quinoa|millet|apple|banana|berry|berries|fruit|tomato|cauliflower|celery|cucumber|mushroom|flaxseed|chia|seaweed|kelp)\b", re.I)


def classify_source_food(desc: str) -> str | None:
    d = desc or ""
    if _ORGAN.search(d) and _SPECIES.search(d):
        return "organ"
    if _FISH.search(d) and not _FISH_PLANT_FP.search(d):
        return "fish"
    if "egg" in d.lower() and "eggplant" not in d.lower():
        return "egg"
    # fat_oil BEFORE dairy so pure butterfat (ghee, butter oil) is a fat, not dairy;
    # plain butter/cream/cheese carry no _OIL token and still fall to dairy.
    if _OIL.search(d):
        return "fat_oil"
    if _DAIRY.search(d):
        return "dairy"
    if _SPECIES.search(d) and _MUSCLE_CUT.search(d):
        return "muscle"
    # Plant ONLY when no animal token co-occurs — drops composite meat/dairy/egg
    # dishes (soups, burritos, baby food) that carry a plant word but no cut word.
    if _PLANT.search(d) and not (
        _SPECIES.search(d) or _FISH.search(d) or _ORGAN.search(d) or _DAIRY.search(d)
        or ("egg" in d.lower() and "eggplant" not in d.lower())
    ):
        return "plant"
    return None   # unclassified -> excluded from pooling (avoids noise)


def prep_state(desc: str) -> str:
    """raw | native | cooked | canned | added_solution | preserved | dried.

    'native' = the ingredient's unprocessed form carrying no prep token (fluid
    milk, cheese, pressed oil, milled flour, fresh/frozen-raw). raw + native are
    always kept; 'dried' is kept for PLANT only (native dry form). preserved/cooked/
    canned/added_solution are dropped. preserved is checked BEFORE raw so an additive
    product tagged 'raw' (e.g. corned beef ... raw) is not rescued by the raw token."""
    d = (desc or "").lower()
    if any(kw in d for kw in cv_config.ADDED_SOLUTION_KEYWORDS):
        return "added_solution"
    if any(kw in d for kw in cv_config.CANNED_KEYWORDS):
        return "canned"
    if any(kw in d for kw in cv_config.COOKED_KEYWORDS):
        return "cooked"
    if any(kw in d for kw in cv_config.PRESERVED_KEYWORDS):
        return "preserved"
    if any(kw in d for kw in cv_config.DEHYDRATED_KEYWORDS):
        return "dried"
    if any(kw in d for kw in cv_config.RAW_KEYWORDS):
        return "raw"
    return "native"


def _calc_derivation_ids(path) -> set[str]:
    """SR-Legacy food_nutrient_derivation.csv -> ids that are NOT analytical."""
    out: set[str] = set()
    try:
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                desc = (row.get("description") or "").lower()
                if any(w in desc for w in ("calculated", "imputed", "assumed")):
                    out.add((row.get("id") or "").strip())
    except FileNotFoundError:
        pass
    return out


def _obs(dataset, version, food_id, desc, nbr, nclass, name, mean, cv, n, method, inputs, deriv, lineage):
    icls = classify_source_food(desc)
    if icls is None:
        _DROP_STATS["unclassified"] += 1
        return None
    # Prep filter: only the raw ingredient + its native unprocessed form estimate
    # the raw DB ingredient's CV; cooked/canned/enhanced/preserved are biased proxies.
    # 'dried' is the native form for PLANT (dry seeds/grains/legumes) but a processed
    # concentrate for animal products (dried egg/whey) -> kept only for plant.
    ps = prep_state(desc)
    keep_prep = ps in cv_config.PREP_KEEP_STATES or (ps == "dried" and icls == "plant")
    if not keep_prep:
        _DROP_STATS[f"prep:{ps}"] += 1
        return None
    # Composite/branded curation: food must be a vetted clean single-ingredient food.
    if _CURATION_KEEP is not None and (icls, str(food_id)) not in _CURATION_KEEP:
        _DROP_STATS["curation:composite/branded"] += 1
        return None
    cv, _ = cv_stats.clip_cv(cv, cv_config.CV_CAP)
    if cv is None or cv <= 0:
        _DROP_STATS["cv_nonpositive"] += 1
        return None
    return {
        "source_dataset": dataset, "source_dataset_version": version,
        "source_food_id": str(food_id), "source_food_desc": desc[:250],
        "prep_state": prep_state(desc), "nutrient_nbr": nbr, "nutrient_name": name,
        "mean_value": mean, "sd_value": cv * mean, "n_data_points": n, "cv": round(cv, cv_config.ROUND_DECIMALS),
        "method": method, "method_inputs": psycopg2.extras.Json(inputs), "derivation_code": deriv,
        "lineage_pair_id": str(lineage) if lineage is not None else None,
        "ingredient_class": icls, "nutrient_class": nclass,
        "pipeline_version": cv_config.PIPELINE_VERSION,
    }


def extract(apply_curation: bool = True) -> list[dict]:
    global _CURATION_KEEP
    if apply_curation:
        _CURATION_KEEP = load_curation_keepset()
        if _CURATION_KEEP is not None:
            print(f"curation keep-set: {len(_CURATION_KEEP)} clean single-ingredient foods")
    else:
        _CURATION_KEEP = None
        print("--no-curation: composite/branded keep-set NOT applied "
              "(prep + classifier filters still active) — use to re-surface candidates for scoring.")
    cw = build_crosswalk()
    target = {v["nutrient_nbr"]: (v["nutrient_class"], v["usda_name"])
              for v in cw.values() if v["nutrient_nbr"] is not None}
    obs: list[dict] = []

    # ── SR28 (Tier 1 SE, Tier 2 range) ──
    sr28_desc = cv_sources.read_sr28_food_desc()
    for r in cv_sources.read_sr28_nut_data():
        t = target.get(r["nutr_no"])
        if t is None:
            continue
        val = r["value"]
        # Keep only analytical rows (allowlist; excludes calc/imputed/label-claim/etc.).
        if val is None or val <= 0 or r.get("src_cd") not in cv_config.ANALYTICAL_SRC_CDS:
            continue
        nclass, name = t
        cv = cv_stats.cv_from_se(val, r["se"], r["n"])
        method, inputs = "se_sqrt_n", {"se": r["se"], "n": r["n"]}
        if cv is None:
            cv = cv_stats.cv_from_range(val, r["min"], r["max"], r["n"])
            method, inputs = "wan_range", {"min": r["min"], "max": r["max"], "n": r["n"]}
        if cv is None:
            continue
        o = _obs("sr28", cv_config.SR28_VERSION, r["ndb_no"], sr28_desc.get(r["ndb_no"], ""),
                 r["nutr_no"], nclass, name, val, cv, r["n"], method, inputs, r.get("deriv_cd"), r["ndb_no"])
        if o:
            obs.append(o)

    # ── FDC (Tier 2 range) ──
    def extract_fdc(dsdir, dataset, version, bridge, calc_ids):
        nbr_map = cv_sources.read_fdc_nutrient_map(dsdir / "nutrient.csv")
        food_desc = cv_sources.read_fdc_food(dsdir / "food.csv")
        for r in cv_sources.read_fdc_food_nutrient(dsdir / "food_nutrient.csv", nbr_map):
            t = target.get(r["nutrient_nbr"])
            if t is None:
                continue
            val = r["amount"]
            if val is None or val <= 0 or r["derivation_id"] in calc_ids:
                continue
            cv = cv_stats.cv_from_range(val, r["min"], r["max"], r["n"])
            if cv is None:
                continue
            nclass, name = t
            lineage = bridge.get(r["fdc_id"]) if bridge else None
            o = _obs(dataset, version, r["fdc_id"], food_desc.get(r["fdc_id"], ""),
                     r["nutrient_nbr"], nclass, name, val, cv, r["n"], "wan_range",
                     {"min": r["min"], "max": r["max"], "n": r["n"]}, r["derivation_id"], lineage)
            if o:
                obs.append(o)

    srl_bridge = cv_sources.read_sr_legacy_food(cv_config.FDC_SRL_DIR / "sr_legacy_food.csv")
    srl_calc = _calc_derivation_ids(cv_config.FDC_SRL_DIR / "food_nutrient_derivation.csv")
    extract_fdc(cv_config.FDC_SRL_DIR, "fdc_sr_legacy", cv_config.FDC_SRL_VERSION, srl_bridge, srl_calc)
    extract_fdc(cv_config.FDC_FDN_DIR, "fdc_foundation", cv_config.FDC_FDN_VERSION, {}, set())
    return obs


_COLS = ["source_dataset", "source_dataset_version", "source_food_id", "source_food_desc",
         "prep_state", "nutrient_nbr", "nutrient_name", "mean_value", "sd_value",
         "n_data_points", "cv", "method", "method_inputs", "derivation_code",
         "lineage_pair_id", "ingredient_class", "nutrient_class", "pipeline_version"]


def write(obs: list[dict]) -> int:
    db = get_db()
    with db.cursor() as cur:
        cur.execute("DELETE FROM cv_observations")
        rows = [tuple(o[c] for c in _COLS) for o in obs]
        psycopg2.extras.execute_values(
            cur,
            f"INSERT INTO cv_observations ({','.join(_COLS)}) VALUES %s "
            "ON CONFLICT (source_dataset, source_food_id, nutrient_nbr) DO NOTHING",
            rows, page_size=1000,
        )
    return len(obs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-curation", action="store_true",
                    help="skip the composite/branded keep-set (re-surface candidates for scoring)")
    args = ap.parse_args()

    obs = extract(apply_curation=not args.no_curation)
    by_ds = Counter(o["source_dataset"] for o in obs)
    by_cls = Counter(o["ingredient_class"] for o in obs)
    by_method = Counter(o["method"] for o in obs)
    by_prep = Counter(o["prep_state"] for o in obs)
    print(f"Extracted {len(obs)} observations")
    print(f"  by dataset: {dict(by_ds)}")
    print(f"  by method:  {dict(by_method)}")
    print(f"  by class:   {dict(by_cls)}")
    print(f"  by prep:    {dict(by_prep)}")
    print(f"  dropped:    {dict(_DROP_STATS)}")
    if args.dry_run:
        print("DRY RUN — cv_observations not written.")
        return
    n = write(obs)
    print(f"Wrote {n} rows to cv_observations.")
    close_db()


if __name__ == "__main__":
    main()
