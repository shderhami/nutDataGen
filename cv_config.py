"""Pinned configuration for the nutrient-CV extraction pipeline.

Single source of every versioned constant (see Docs/nutrient_cv_extraction_plan.md).
Kept as a Python module to match the repo's config.py convention (no new YAML dep).
Any change here MUST bump PIPELINE_VERSION; config_sha256() hashes this file's raw
bytes so a stored CV row can be tied to the exact config that produced it.

ALL CVs are dimensionless FRACTIONS in (0, CV_CAP].  17% CV -> 0.17, never 17.0.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

PIPELINE_VERSION = "cv-v5"   # v5: + corrector-supplement delivered-spec CV (Tier 0)
# v4: + cross-source CV>1 (SD>mean) plausibility guard
# v3: + muscle poultry/red sub-pools (v2 = prep-filter + curation)

# ── Pinned numeric parameters ────────────────────────────────────────────────
K_MIN_FOODS = 5            # min backing foods for an evidence-based class pool
N0_SHRINKAGE = 8           # fixed-weight shrinkage constant  w = n/(n+N0)
CV_CAP = 1.5               # hard upper cap on any stored CV (fraction)
CV_FLOOR = 0.02            # generic lower floor (fraction) to avoid degenerate ~0 CVs
# Cross-source plausibility guard: a CROSS-SOURCED measured CV (bulk SR28/FDC
# observation, matched by food — a different sample than the cell's value) above
# this bound means SD > mean, which is implausible as a within-ingredient BATCH CV
# and a tell that the source sample mixes distinct products (e.g. Vit-D-enriched vs
# conventional eggs). Such a candidate is REJECTED so the ladder falls to the
# same-source own-range CV or the class pool. The cell's OWN-range dispersion
# (same source as the value) is never guarded.
CROSS_SOURCE_CV_MAX = 1.0

# c4 / small-n: applies to Tier-1 sample SD only, and may only RAISE a CV.
# near-detection over-inflated CVs are separately clipped to CV_CAP (may LOWER).
NEAR_DETECTION_CLIP_TO_CAP = True
FLOOR_EXCLUSION_ROUTE_TO_PRIOR = 0.30   # >30% of a pool floor-clipped -> use the prior

# Calibration flag (SR28-SE vs FDC-range twin), per cell:
CALIB_ABS_PP = 0.05        # flag if |cv_se - cv_range| > 0.05 (5 pp)
CALIB_MIN_FLOOR = 0.03     # ...and the ratio arm only fires once both CVs >= 0.03
CALIB_RATIO_LO, CALIB_RATIO_HI = 1 / 1.5, 1.5

# The gate blocks on SYSTEMATIC divergence (median |cv_se - cv_range| over twins),
# not the per-cell flag rate: the two estimators agree ~1pp at the median, so a
# large median signals a real bug (mis-parsed field / unit error), while per-cell
# spread is expected noise. The per-cell flag is kept as informational provenance.
CALIB_MAX_MEDIAN_DIVERGENCE = 0.05

# Confidence tier thresholds
BACKING_N_HIGH = 8
W_HIGH = 0.8

# effective_n by tier (single integers)
EFFECTIVE_N_PRIOR = 1
EFFECTIVE_N_SUPPLEMENT = 2

# Delivered-supplement CV floors (fractions)
SUPPLEMENT_DELIVERED_FLOOR = 0.08
SUPPLEMENT_DELIVERED_FLOOR_LABILE = 0.15

# ── Corrector supplements (ingredients.is_corrector) — delivered SPEC CV ──────
# A corrector is a single-nutrient manufactured supplement whose whole purpose is to
# deliver a label-spec dose of one nutrient. The pooled/floor CVs above describe
# WHOLE-FOOD dispersion, which materially overstates a manufactured product: because a
# corrector delivers the bulk of the nutrient it corrects, an inflated CV dominates the
# consumer's k*sigma safety buffer and parks the corrector well above what its real
# variability justifies (e.g. Vitamin E floated to 51 IU when ~41 was warranted).
#
# So a corrector cell gets an OWN (measured-column) delivered-spec CV, which wins the
# consumer's COALESCE(coefficient_of_variation, category_cv). The category column still
# carries the delivered floor above, so NULLing the own column falls back safely.
#
# Evidence: USDA/NIH Dietary Supplement Ingredient Database (DSID) national MVM
# analysis; USP label-claim tolerances (minerals <=10% below label, iodine/selenium
# widened to +60%); vitamin-E premix stability (analytical +-~20%, 5-30% overage, ester
# ~95% retention after heat); taurine >=98.5-99% purity, RSD <10%.
#
# This mirrors the formulator repo's scripts/patch_corrector_cvs.py so a full re-run of
# this pipeline no longer reverts that patch. Keep the two in sync.
CORRECTOR_CV_STABLE = 0.03   # stable minerals, choline, taurine (delivered-floor overfill)
CORRECTOR_CV_HIGH = 0.08     # documented high variability / oxidation-labile actives
CORRECTOR_HIGH_CV_NUTRIENT_IDS = {
    1109,   # Vitamin E — oxidation losses, premix stability
    1100,   # Iodine    — USP tolerance widened to +60%
    1103,   # Selenium  — USP tolerance widened to +60%
}

# Gate thresholds
MAX_PRIOR_ONLY_FRAC = 0.60
# Twin SE-vs-range: block if ANY single same-food twin diverges more than this
# (catches a localized parse/unit error the median-divergence check would miss).
CALIB_MAX_TWIN_DIVERGENCE = 0.30

# Consumer fallback when both CV columns are NULL (never 0)
CONSUMER_NULL_FALLBACK_CV = 0.25

# Pooling / determinism
POOLING_METHOD = "median_cv"      # unweighted median of per-food CVs (percentile_disc)
ROUND_DECIMALS = 6

# ── Pinned source snapshots ──────────────────────────────────────────────────
USDA_BULK_DIR = Path(__file__).parent / "data" / "usda_bulk"
SR28_VERSION = "SR28-2015"
FDC_SRL_VERSION = "FDC-SRL-2018-04"
FDC_FDN_VERSION = "FDC-FDN-2026-04-30"
SR28_NUT_DATA = USDA_BULK_DIR / "sr28" / "NUT_DATA.txt"
FDC_SRL_DIR = USDA_BULK_DIR / "sr_legacy"
FDC_FDN_DIR = USDA_BULK_DIR / "foundation"
AUTHORITATIVE_NUTRIENT_CSV = FDC_FDN_DIR / "nutrient.csv"   # Foundation nutrient.csv = crosswalk authority

# ── Categories that pre-empt to Tier-6 (delivered supplement floor) ──────────
SUPPLEMENT_CATEGORIES = {"Supplement", "Fish Oil"}
# Zero-mean / non-nutritive: NULL CV, exempt from the Bucket-A gate
NON_NUTRITIVE_CATEGORIES = {"Base"}

# ── Nutrient class map (keyed on FDC nutrient_id, from fediaf_nutrients.py) ───
_AMINO = [1220, 1221, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1211, 1210, 1219, 1234]
_MAJOR_MIN = [1087, 1091, 1092, 1093, 1088, 1090]
_TRACE_MIN = [1089, 1098, 1101, 1095]
_SE_I = [1100, 1103]
_FAT_SOL_VIT = [1106, 1110, 1109, 1185]
_WATER_SOL_VIT = [1165, 1166, 1167, 1170, 1175, 1177, 1178, 1176]
_PROXIMATE = [1003, 1008, 1051, 1007, 1079, 1005]     # protein, energy, water, ash, fiber, carb

NUTRIENT_CLASS: dict[int, str] = {}
NUTRIENT_CLASS.update({n: "amino_acid" for n in _AMINO})
NUTRIENT_CLASS.update({n: "major_mineral" for n in _MAJOR_MIN})
NUTRIENT_CLASS.update({n: "trace_mineral" for n in _TRACE_MIN})
NUTRIENT_CLASS.update({n: "se_i" for n in _SE_I})
NUTRIENT_CLASS.update({n: "fat_sol_vit" for n in _FAT_SOL_VIT})
NUTRIENT_CLASS.update({n: "water_sol_vit" for n in _WATER_SOL_VIT})
NUTRIENT_CLASS.update({n: "low_cv_proximate" for n in _PROXIMATE})
NUTRIENT_CLASS.update({
    1004: "fat",
    1269: "n6_linoleic",
    1271: "arachidonic",
    1270: "n3_terrestrial",   # ALA (18:3) — terrestrial/plant short-chain n-3
    1278: "n3_long_chain",    # EPA
    1272: "n3_long_chain",    # DHA
    1280: "n3_long_chain",    # DPA
    1293: "fat",              # Total PUFA (has USDA data; resolves normally)
    1180: "choline",
})

# ── Tier-5 literature priors by nutrient class (FRACTIONS, biased high) ───────
# NOTE: prior_citation must be filled per class before a run may ship (§7 gate).
NUTRIENT_PRIORS: dict[str, float] = {
    "low_cv_proximate": 0.10,
    "fat": 0.30,
    "major_mineral": 0.15,
    "trace_mineral": 0.30,
    "se_i": 0.55,
    "fat_sol_vit": 0.45,
    "water_sol_vit": 0.35,
    "choline": 0.35,
    "amino_acid": 0.20,
    "n3_long_chain": 0.30,       # generic; fish/terrestrial split applied by ingredient class below
    "n3_terrestrial": 0.40,
    "n6_linoleic": 0.35,
    "arachidonic": 0.45,
}
# n-3 long-chain prior is source-conditional (fish lower than terrestrial meat):
N3_LONG_CHAIN_PRIOR_BY_INGREDIENT = {"fish": 0.25, "_default": 0.40}

# Per-nutrient prior overrides (take precedence over the nutrient-class prior).
# Taurine: no USDA dispersion and highly variable in whole foods (cooking/leaching
# losses); a conservative high prior, above the incumbent 0.25, for this Bucket-A nutrient.
PER_NUTRIENT_PRIOR = {1234: 0.30}   # taurine

# SR28 Src_Cd ANALYTICAL allowlist (verified against data/usda_bulk/sr28/SRC_CD.txt):
#   1  = Analytical or derived from analytical
#   6  = Aggregated data combining codes 1 & 12 (both analytical)
#   12 = Manufacturer's analytical; partial documentation
#   13 = Analytical data from the literature, partial documentation
# Everything else is excluded: 4 calc/imputed, 5 label-claim, 7 assumed-zero,
# 8/9 calculated, 11 non-analytical aggregate.
ANALYTICAL_SRC_CDS = {"1", "6", "12", "13"}

# Real (biased-high) provenance citation per nutrient-class prior. A prior may not
# ship carrying the sentinel; the §7 gate hard-blocks on it.
PRIOR_CITATION_SENTINEL = "citation pending"
# Each prior is a conservative biased-high engineering default; the citation names a
# REAL source establishing that class's whole-food variability magnitude. Every source
# below was found by web search and INDEPENDENTLY re-verified to exist (DOIs/PMIDs kept
# for audit); three (Volpato 2022, Dai 2022, Haug 2010) were also spot-checked by hand.
PRIOR_CITATIONS = {
    "low_cv_proximate": "Volpato et al. 2022 (Poultry Science 101(8):101926, DOI 10.1016/j.psj.2022.101926): crude-protein CV 5-7% and dry-matter CV 2-3% across food batches, well below the 15-21% CVs of fat/ash — a CV=0.10 prior sits safely above observed low-CV proximate dispersion; conservative biased-high prior.",
    "fat": "Lakshmanan et al. 2012 (Meat Science 90(1):216-225, PMID 21816544): chemical intramuscular fat across a pig population had CV=44.8%, so empirical fat dispersion far exceeds the 0.30 prior; conservative biased-high prior.",
    "major_mineral": "Pennington & Young 1990 (USDA Total Diet Study, J. Food Compos. Anal. 3(2):145-165, DOI 10.1016/0889-1575(90)90021-D): across-food CVs averaged Na 20%, K 15%, Ca 21%, P 14%, Mg 17% (~0.15-0.17); conservative biased-high prior.",
    "trace_mineral": "Pennington & Young 1990 (J. Food Compos. Anal. 3(2):166-184): Fe/Zn/Cu/Mn content across 234 US Total Diet Study foods varies substantially (element CVs ~20-30%), supporting ~0.30; conservative biased-high prior.",
    "se_i": "Carriquiry et al. 2016 (Am J Clin Nutr 104(Suppl 3):877S-887S, PMID 27534633): iodine in the same whole foods varies substantially by US region and year, too variable to represent by means alone — soil-driven high-CV class; conservative biased-high prior.",
    "fat_sol_vit": "Greenfield & Southgate 2003 (FAO, Food Composition Data, 2nd ed.): fat-soluble vitamins are among the most variable food constituents, tissue content strongly driven by animal diet, season, breed and fat level; conservative biased-high prior.",
    "water_sol_vit": "Batifoulier et al. 2006 (Eur. J. Agronomy 25(2):163-169, DOI 10.1016/j.eja.2006.04.009): across 49 wheat cultivars, thiamine spread ~2.4x and riboflavin/B6 ~2.2x — high water-soluble-vitamin variability; conservative biased-high prior.",
    "choline": "Zeisel, Mar, Howe & Holden 2003 (J Nutr 133(5):1302-1307, DOI 10.1093/jn/133.5.1302; USDA Choline Database source): total choline and betaine vary widely across whole foods and with variety/growing conditions; conservative biased-high prior.",
    "amino_acid": "Dai, Zheng & Locasale 2022 (Nature Communications 13:6683, DOI 10.1038/s41467-022-34486-0): 'Coefficient of variation > 0.2 for all amino acids' across 2,335 foods; conservative biased-high prior.",
    "n3_long_chain": "Strobel, Jahreis & Kuhnt 2012 (Lipids in Health and Disease 11:144): survey of 123 fish/fish products — EPA+DHA varies widely across species and wild-vs-farmed (per-sample CVs ~0.29-0.40); conservative biased-high prior.",
    "n3_terrestrial": "Daley et al. 2010 (Nutrition Journal 9:10, PMID 20219103, DOI 10.1186/1475-2891-9-10): grass- vs grain-fed beef ALA (C18:3 n-3) differs ~2-11x — large diet-driven n-3 variability in terrestrial tissue; conservative biased-high prior.",
    "n6_linoleic": "Pascual et al. 2006 (Food Chemistry 96:538-548, DOI 10.1016/j.foodchem.2005.02.042): linoleic acid (18:2 n-6) is the most diet/breed-driven major fatty acid in pig backfat, spanning a wide range across dietary treatments; conservative biased-high prior.",
    "arachidonic": "Haug, Olesen & Christophersen 2010 (Lipids in Health and Disease 9:37, PMID 20398309, DOI 10.1186/1476-511X-9-37): arachidonic acid in chicken thigh ranged 1.5-2.8 g/100g FA across 15 identically-fed broilers, so across-species/tissue/diet whole-food AA varies more; conservative biased-high prior.",
}

# ── Component derivation (Tier 3) ────────────────────────────────────────────
# Vitamin A (RAE, 1106) has no sampled range; derive from Retinol (1105), animal-tissue only.
# Combined-constraint CVs (Met+Cys, Phe+Tyr, EPA+DHA) are the CONSUMER's aggregation
# (nutDataGen stores each component nutrient's own CV; the formulator combines them).
COMPONENT_DERIVATION = {
    1106: {"from_nutrient_id": 1105, "gate": "animal_tissue"},   # Vit A <- Retinol
}
ANIMAL_TISSUE_CLASSES = {"muscle", "organ", "fish", "egg", "dairy"}

# ── Criticality Bucket A/B/C (by nutrient_id) ────────────────────────────────
BUCKET_A = {1234, 1165, 1180, 1106, 1110, 1098}   # taurine, thiamine, choline, Vit A, Vit D, Cu
BUCKET_C = {1004, 1269}                            # total fat, linoleic (wide window)
# labile actives (supplemented) get the higher delivered floor
LABILE_ACTIVE_NUTRIENT_IDS = {1106, 1110, 1109, 1185, 1165, 1166, 1177, 1176, 1234}

# ── prep_state keyword rules + keep policy ───────────────────────────────────
# The pooled CV must estimate the RAW DB ingredient's batch variability. A paired
# per-category test (cv_prep_test.py) showed processing is NOT CV-neutral: cooking
# COMPRESSES the CV in flesh/plant (small–medium, downward → would under-buffer)
# and INFLATES it in egg; added-solution injects manufacturing variance into Na/P
# (sodium CV 0.106 → 0.268). Canning is retort-cooking + variable pack liquid.
# So only the raw ingredient and its native unprocessed form (fluid milk, cheese,
# pressed oil, milled flour, fresh/frozen-raw) are kept; cooked/canned/enhanced are
# excluded. Dropping cooked costs ~zero coverage — raw+native already reaches the
# K>=5 pooling threshold for nearly every nutrient (see cv_prep_test feasibility).
COOKED_KEYWORDS = ["cooked", "roasted", "braised", "boiled", "grilled", "stewed",
                   "pan-fried", "fried", "baked", "broiled", "simmered", "poached",
                   "steamed", "microwaved"]
RAW_KEYWORDS = ["raw"]
ADDED_SOLUTION_KEYWORDS = ["added solution", "pre-basted", "prebasted", "enhanced"]
CANNED_KEYWORDS = ["canned", "evaporated", "condensed"]   # retort heat / concentrated
# Additive / preservation processing — injects variable salt/sugar/cure or smoke and
# is NOT the raw ingredient; dropped for ALL classes (checked BEFORE the 'raw' token,
# so "beef, cured, corned ... raw" is dropped, not rescued by the trailing 'raw').
PRESERVED_KEYWORDS = ["smoked", "salted", "sugared", "brined", "cured", "corned",
                      "pickled", "marinated", "fermented", "jerky", "lox", "kippered"]
# Dehydration/concentration. For ANIMAL classes (egg/fish/muscle/organ/dairy) this is a
# processed concentrate (dried egg powder, dried whey) -> dropped. For PLANT it is the
# ingredient's native form (dry seeds/grains/legumes/seaweed) -> kept (see cv_extract).
DEHYDRATED_KEYWORDS = ["dried", "dehydrated", "air-dried", "sun-dried", "freeze-dried",
                       "powder", "flakes"]
# prep_state values admitted into the CV pool ("native" = unlabeled native form).
# "dried" is additionally kept for PLANT only (native dry form) — handled in cv_extract.
PREP_KEEP_STATES = {"raw", "native"}

# ── Muscle subclass: poultry vs red meat ─────────────────────────────────────
# Their within-food CVs differ (cv_group_test.py: poultry more variable in major
# minerals, fatty acids, fat-sol vitamins; red meat more variable in proximates),
# and muscle DB ingredients lean heavily on the pool (turkey = 100% pooled). So a
# poultry/red sub-pool is built, with the combined 'muscle' pool as fallback.
# muscle_subclass() maps EITHER a protein_species value (DB, exact) OR a USDA food
# description (pool side, word-boundary) -> 'poultry'|'red'|None. EXTEND these lists
# for any new protein type; an unmapped species safely falls back to combined muscle.
MUSCLE_SUBCLASS = {
    "poultry": ["chicken", "turkey", "duck", "goose", "quail", "pheasant", "hen", "fowl",
                "cornish", "guinea", "squab", "partridge", "grouse", "pigeon", "dove", "capon"],
    "red": ["beef", "pork", "lamb", "veal", "bison", "goat", "mutton", "venison", "deer",
            "elk", "moose", "rabbit", "hare", "boar", "buffalo", "kangaroo", "horse"],
}
_SPECIES_TO_SUBCLASS = {sp: sub for sub, sps in MUSCLE_SUBCLASS.items() for sp in sps}


def muscle_subclass(species_or_desc: str | None) -> str | None:
    """'poultry' | 'red' | None for a protein_species value (exact) OR a food
    description (word-boundary). Unmapped -> None (uses the combined muscle pool)."""
    if not species_or_desc:
        return None
    t = species_or_desc.strip().lower()
    if t in _SPECIES_TO_SUBCLASS:            # protein_species column (exact)
        return _SPECIES_TO_SUBCLASS[t]
    for sp, sub in _SPECIES_TO_SUBCLASS.items():   # USDA description (token)
        if re.search(rf"\b{sp}\b", t):
            return sub
    return None


def nutrient_class(nutrient_id: int) -> str:
    """Nutrient class for a FDC nutrient_id (defaults to low_cv_proximate)."""
    return NUTRIENT_CLASS.get(nutrient_id, "low_cv_proximate")


def corrector_cv(nutrient_id: int) -> float:
    """Delivered-spec CV for a nutrient supplied by a corrector supplement."""
    if nutrient_id in CORRECTOR_HIGH_CV_NUTRIENT_IDS:
        return CORRECTOR_CV_HIGH
    return CORRECTOR_CV_STABLE


def bucket(nutrient_id: int) -> str:
    """Criticality bucket A/B/C for a nutrient_id."""
    if nutrient_id in BUCKET_A:
        return "A"
    if nutrient_id in BUCKET_C:
        return "C"
    return "B"


def config_sha256() -> str:
    """SHA256 over this config file's raw bytes (pins the version gate)."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
