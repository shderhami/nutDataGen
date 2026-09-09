# Intake report: chicken skin raw

- generated: 2026-09-09  |  spec: `data/intake/chicken_skin.json`
- Foundation FDC: —  |  SR Legacy FDC: 171452
- category: Muscle Meat  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: PRICE: $1.99/lb proposed by Shahab 2026-09-09 / 453.592 = 0.0044/g (scrap-market anchor - what skin/trimmings fetch at butcher counters). Two model estimators were computed and REJECTED as economically inverted (skin must price below meat): market-residual from the DB's own cut pairs gave 0.0151-0.0166 (thigh, f=0.15-0.20) and tallow-energy-parity gave 0.0137. Recorded for auditability; the scrap anchor governs.
- note: FRAME (Shahab 2026-09-09): RESERVED skin, not purchased - customers keep the skin they remove when skinning the skin-on cuts (10001 thigh / 10016 breast) for skinless recipes. Zero marginal purchase; pairs naturally with the skinless entries 10048/10054.
- note: ACCURACY PROOF (the constructive duck lesson, 2026-09-09): SR 171452 is DIRECTLY MEASURED (87 nutrients, full 12/12 AA panel, fat n=35) - no duck-style subtraction. USDA's own trio reconstructs: thigh meat+skin = meat-only + skin at 2.0% macro rms (water -0.1%, fat +0.4%, Met -1.7%); breast likewise 2.0% (AAs within +/-8.5%). The skin entry IS the skin inside our validated skin-on entries.
- note: ROLE: the SPECIES-PURE diluent for chicken recipes (dilution-family doctrine: tallow 10064 for beef/fish, duck skin-on 10061 for duck, chicken skin for chicken). Met 0.77/1000 kcal, fat 93/1000. LA HONESTY: 17.8/1000 kcal (chicken-fat profile) - unsuitable as a general LA-lean diluent (that is tallow's job); in chicken recipes it adds no new species and no new FA character.
- note: Foreign coverage is ONE entry - AFCD F002773 'Chicken, skin, composite, raw' (ANALYSED; macros corroborate SR within 9%; carries analysed Cl 32/I 2.1/biotin 1.5 = three of the five gaps). MEXT/CoFID/BLS/FCDB publish only with/without-skin frames (verified 2026-09-09). CIQUAL none.
- note: Expected LA review: SR 6.22 vs AFCD 4.18 - corn-fed n-6 precedent (6th occurrence expected); keep SR.
- note: Gaps -> AFCD adapter (Cl, I, biotin) + literature (taurine, choline). Skin is collagen-rich: taurine and per-protein AA quality differ from muscle - taurine estimated LOW with sparse flag.

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| AFCD:F002773 Chicken, skin, composite, raw | Chicken, skin, composite, raw - the ONLY foreign skin-only entry anywhere; Australian ANALYSED panel incl. chloride/iodine/biotin; corn-fed LA caveat on FA rows | independent (0/26 incidental matches) |
| PoultryFamily:Collagen-rich skin taurine (muscle 169 dark / 15.9-16 white; skin is low-taurine connective tissue) | No skin taurine measurement in any local resource. Skin is collagen-dominant (low free AA pool vs oxidative muscle); estimated well below dark-muscle 169, order-of white-meat levels. SPARSE-EVIDENCE flag - conservative low credit | no USDA overlap — independence not establishable |
| PoultryFamily:Skin choline (family: thigh meat 53-64, composite entries higher via lean) | No skin choline anywhere (SR gap, AFCD lacks choline). Membrane-lipid-bearing tissue but low lean mass; family-informed estimate 50, SPARSE-EVIDENCE flag | no USDA overlap — independence not establishable |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | AFCD | PoultryFamily | verdict |
|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | — | 13.33 (n=31) | 12.7 | — | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | AFCD | PoultryFamily | verdict |
|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 1.028? | — | — | **usda_only** |
| Histidine (1221) | g | — | 0.256? | — | — | **usda_only** |
| Isoleucine (1212) | g | — | 0.429? | — | — | **usda_only** |
| Leucine (1213) | g | — | 0.783? | — | — | **usda_only** |
| Lysine (1214) | g | — | 0.796? | — | — | **usda_only** |
| Methionine (1215) | g | — | 0.267? | — | — | **usda_only** |
| Cystine (1216) | g | — | 0.222? | — | — | **usda_only** |
| Phenylalanine (1217) | g | — | 0.45? | — | — | **usda_only** |
| Tyrosine (1218) | g | — | 0.303? | — | — | **usda_only** |
| Threonine (1211) | g | — | 0.476? | — | — | **usda_only** |
| Tryptophan (1210) | g | — | 0.107? | 0.16 | — | **review** |
| Valine (1219) | g | — | 0.561? | — | — | **usda_only** |
| Taurine (1234) | mg | — | — | — | 30~ | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | AFCD | PoultryFamily | verdict |
|---|---|---|---|---|---|---|
| Total Fat (1004) | g | — | 32.35 (n=35) | 35.1 | — | **confirm** |

## Fatty Acid

| nutrient | unit | FND | SR | AFCD | PoultryFamily | verdict |
|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 6.22 (n=33) | 4.18 | — | **review** |
| Arachidonic acid (1271) | g | — | 0.09 (n=10) | 0.06634 | — | **review** |
| Alpha-linolenic acid (1270) | g | — | 0.26 (n=27) | 0.36 | — | **review** |
| EPA (1278) | g | — | 0.02 (n=6) | 0 | — | **region_keep** |
| DHA (1272) | g | — | 0.03 (n=3) | 0 | — | **region_keep** |
| Fatty acids, total polyunsaturated (1293) | g | — | 6.81? | 4.61 | — | **review** |
| DPA 22:5 n-3 (1280) | g | — | 0.01 (n=3) | 0 | — | **confirm** |

## Mineral

| nutrient | unit | FND | SR | AFCD | PoultryFamily | verdict |
|---|---|---|---|---|---|---|
| Calcium (1087) | mg | — | 11 (n=24) | 13 | — | **confirm** |
| Phosphorus (1091) | mg | — | 100 (n=24) | 99 | — | **confirm** |
| Potassium (1092) | mg | — | 103 (n=24) | 120 | — | **confirm** |
| Sodium (1093) | mg | — | 63 (n=24) | 43 | — | **review** |
| Chloride (1088) | mg | — | — | 32 | — | **adopt_foreign** |
| Magnesium (1090) | mg | — | 13 (n=24) | 8 | — | **review** |
| Iron (1089) | mg | — | 1.08 (n=24) | 0.7 | — | **review** |
| Copper (1098) | mg | — | 0.041 (n=24) | 0.04 | — | **confirm** |
| Manganese (1101) | mg | — | 0.019 (n=24) | 0.02 | — | **confirm** |
| Zinc (1095) | mg | — | 0.93 (n=24) | 0.7 | — | **review** |
| Iodine (1100) | µg | — | — | 2.1 | — | **adopt_foreign** |
| Selenium (1103) | µg | — | 12.3 (n=3) | 0 | — | **region_keep** |

## Vitamin

| nutrient | unit | FND | SR | AFCD | PoultryFamily | verdict |
|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | — | 253.08‡ | 366.3 | — | **region_keep** |
| Vitamin D (1110) | IU | — | 24? | 276 | — | **region_keep** |
| Vitamin E (1109) | IU | — | 0? | 1.192 | — | **region_keep** |
| Vitamin K (1185) | µg | — | 2.9† | — | — | **usda_only** |
| Thiamin (1165) | mg | — | 0.033 (n=16) | 0 | — | **review** |
| Riboflavin (1166) | mg | — | 0.069 (n=16) | 0.1 | — | **review** |
| Niacin (1167) | mg | — | 3.987 (n=16) | 2 | — | **review** |
| Pantothenic acid (1170) | mg | — | 0.692 (n=1) | 0.3 | — | **review** |
| Pyridoxine (1175) | mg | — | 0.09 (n=1) | 0.11 | — | **confirm** |
| Folic acid (1177) | µg | — | 3? | 0 | — | **review** |
| Cobalamin (1178) | µg | — | 0.23? | 0.7 | — | **confirm** |
| Biotin (1176) | µg | — | — | 1.5 | — | **adopt_foreign** |
| Choline (1180) | mg | — | — | — | 50~ | **adopt_foreign** |

## Other

| nutrient | unit | FND | SR | AFCD | PoultryFamily | verdict |
|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 349‡ | 362.094‡ | — | **usda_only** |
| Water (1051) | g | — | 54.22 (n=30) | 49.4 | — | **confirm** |
| Ash (1007) | g | — | 0.41 (n=25) | 0.5 | — | **confirm** |
| Crude Fiber (1079) | g | — | 0† | 0 | — | **confirm** |
| Carbohydrate (1005) | g | — | 0† | 0 | — | **confirm** |

## Needs attention (contested rows + detection-limit context)

### Tryptophan (1210) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.107: AFCD 0.16
- suggestion: 0.107 g (source `sr_legacy`)
  - AFCD [analysed] 0.16 — Tryptophan; food-level derivation: Analysed

### Taurine (1234) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 30 mg (source `literature`)
  - PoultryFamily [estimated] 30 — No skin taurine measurement in any local resource. Skin is collagen-dominant (low free AA pool vs oxidative muscle); est

### Linoleic acid (1269) — review
- all 1 independent(s) differ >±20% from sr_legacy 6.22: AFCD 4.18
- suggestion: 6.22 g (source `sr_legacy`)
  - AFCD [analysed] 4.18 — C18:2w6; food-level derivation: Analysed

### Arachidonic acid (1271) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.09: AFCD 0.06634
- suggestion: 0.09 g (source `sr_legacy`)
  - AFCD [analysed] 0.06634 — C20:4w6; food-level derivation: Analysed

### Alpha-linolenic acid (1270) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.26: AFCD 0.36
- suggestion: 0.26 g (source `sr_legacy`)
  - AFCD [analysed] 0.36 — C18:3w3; food-level derivation: Analysed

### EPA (1278) — region_keep
- region-sensitive; foreign cluster differs: AFCD 0 — US mean kept unless defective
- suggestion: 0.02 g (source `sr_legacy`)
  - AFCD [analysed] 0 — C20:5w3; food-level derivation: Analysed

### DHA (1272) — region_keep
- region-sensitive; foreign cluster differs: AFCD 0 — US mean kept unless defective
- suggestion: 0.03 g (source `sr_legacy`)
  - AFCD [analysed] 0 — C22:6w3; food-level derivation: Analysed

### Fatty acids, total polyunsaturated (1293) — review
- all 1 independent(s) differ >±20% from sr_legacy 6.81: AFCD 4.61
- suggestion: 6.81 g (source `sr_legacy`)
  - AFCD [analysed] 4.61 — Total polyunsaturated; food-level derivation: Analysed

### Sodium (1093) — review
- all 1 independent(s) differ >±20% from sr_legacy 63: AFCD 43
- suggestion: 63 mg (source `sr_legacy`)
  - AFCD [analysed] 43 — Sodium; food-level derivation: Analysed

### Chloride (1088) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 32 mg (source `literature`)
  - AFCD [analysed] 32 — Chloride; food-level derivation: Analysed

### Magnesium (1090) — review
- all 1 independent(s) differ >±20% from sr_legacy 13: AFCD 8
- suggestion: 13 mg (source `sr_legacy`)
  - AFCD [analysed] 8 — Magnesium; food-level derivation: Analysed

### Iron (1089) — review
- all 1 independent(s) differ >±20% from sr_legacy 1.08: AFCD 0.7
- suggestion: 1.08 mg (source `sr_legacy`)
  - AFCD [analysed] 0.7 — Iron; food-level derivation: Analysed

### Zinc (1095) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.93: AFCD 0.7
- suggestion: 0.93 mg (source `sr_legacy`)
  - AFCD [analysed] 0.7 — Zinc; food-level derivation: Analysed

### Iodine (1100) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 2.1 µg (source `literature`)
  - AFCD [analysed] 2.1 — Iodine; food-level derivation: Analysed

### Selenium (1103) — region_keep
- region-sensitive; foreign cluster differs: AFCD 0 — US mean kept unless defective
- suggestion: 12.3 µg (source `sr_legacy`)
  - AFCD [analysed] 0 — Selenium; food-level derivation: Analysed

### Vitamin A (1106) — region_keep
- region-sensitive; foreign cluster differs: AFCD 366.3 — US mean kept unless defective
- suggestion: 253.08 IU (source `sr_legacy`)
  - AFCD [analysed] 366.3 — Retinol (preformed); food-level derivation: Analysed

### Vitamin D (1110) — region_keep
- region-sensitive; foreign cluster differs: AFCD 276 — US mean kept unless defective
- suggestion: 24 IU (source `sr_legacy`)
  - AFCD [analysed] 276 — Vitamin D3 equivalents; food-level derivation: Analysed

### Vitamin E (1109) — region_keep
- region-sensitive; foreign cluster differs: AFCD 1.192 — US mean kept unless defective
- suggestion: 0 IU (source `sr_legacy`)
  - AFCD [analysed] 1.192 — Alpha tocopherol; food-level derivation: Analysed

### Thiamin (1165) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.033: AFCD 0
- suggestion: 0.033 mg (source `sr_legacy`)
  - AFCD [analysed] 0 — Thiamin; food-level derivation: Analysed

### Riboflavin (1166) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.069: AFCD 0.1
- suggestion: 0.069 mg (source `sr_legacy`)
  - AFCD [analysed] 0.1 — Riboflavin; food-level derivation: Analysed

### Niacin (1167) — review
- all 1 independent(s) differ >±20% from sr_legacy 3.987: AFCD 2
- suggestion: 3.987 mg (source `sr_legacy`)
  - AFCD [analysed] 2 — Niacin (B3); food-level derivation: Analysed

### Pantothenic acid (1170) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.692: AFCD 0.3
- suggestion: 0.692 mg (source `sr_legacy`)
  - AFCD [analysed] 0.3 — Pantothenic acid; food-level derivation: Analysed

### Folic acid (1177) — review
- all 1 independent(s) differ >±20% from sr_legacy 3: AFCD 0
- suggestion: 3 µg (source `sr_legacy`)
  - AFCD [analysed] 0 — Folate, natural; food-level derivation: Analysed

### Biotin (1176) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 1.5 µg (source `literature`)
  - AFCD [analysed] 1.5 — Biotin; food-level derivation: Analysed

### Choline (1180) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 50 mg (source `literature`)
  - PoultryFamily [estimated] 50 — No skin choline anywhere (SR gap, AFCD lacks choline). Membrane-lipid-bearing tissue but low lean mass; family-informed 

## Verdict summary

- confirm: 14
- review: 14
- usda_only: 13
- region_keep: 6
- adopt_foreign: 5
