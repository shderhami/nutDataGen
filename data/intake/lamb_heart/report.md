# Intake report: lamb heart raw

- generated: 2026-08-31  |  spec: `data/intake/lamb_heart.json`
- Foundation FDC: —  |  SR Legacy FDC: 174444
- category: Organ Meat  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: price_per_unit 0.0176/g ($7.99/lb) CONFIRMED by Shahab 2026-08-31 at approval.
- note: FRAME DECISION (Shahab 2026-08-31): supply is NZ/AU imported -> PRIMARY = SR 174444 'Lamb, New Zealand, imported, heart, raw' (grass-fed frame: fat 3.68, Se 10.9 NZ low-Se soils, vit A 5 µg and vit D 1 µg MEASURED natively - no false-zero fight). US domestic 172527 (grain-fed: fat 5.68 n=12, Se 32) carried as USDA-LINEAGE literature contrast rows so the frame choice gets explicit resolutions.
- note: 4th cardiac species - the validated heart family anchors cross-species rows: chicken 10007 (taurine 231, vit K MK-4 50, Zn 2.3), turkey 10029, beef 10050 (taurine 65 scaled, vit K 5 MEXT total, choline 229, chloride 44 CoFID ox, iodine 1.8 FCDB, biotin 2 CoFID).
- note: SR-only food (Foundation has only ground lamb). BOTH SR lamb hearts carry FULL 12/12 AA panels - unlike beef heart, no foreign AA adoption needed.
- note: THIN INTERNATIONALS: only BLS V515100 + CoFID 18-396 exist (no FCDB/MEXT/CIQUAL/AFCD lamb heart - verified 2026-08-31) -> no cv_intl mapping candidate; review leans on the cardiac-family physiology cross-checks. NZ n=1 on most rows -> expect class_pool CVs.
- note: Zn sanity pre-check PASSED: NZ 1.65 / US 1.87 sit in the validated cardiac band (~1.8-2.3; the chicken-heart 3x Zn defect pattern is absent).
- note: BLS also has mutton V516100 and sheep V514100 hearts - lamb V515100 used; the others are age-class brackets only (not included as sources).
- note: Watch EPA 0.059/DHA 0.021 (NZ n=1): grass-fed ruminant n-3 - plausible for pasture; PUFA total 0.646 vs component sum to be gate-checked as usual.

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| BLS:V515100 Lamb heart, raw | Lamb heart, raw - German table; expect SFK/frida borrows flagged; mutton/sheep siblings bracket for context | ECHO of USDA (17/39 values identical to <0.5%) |
| CoFID:18-396 Heart, lamb, raw | Heart, lamb, raw - UK McCance/LGC organ heritage; the chloride + biotin carrier (ox heart 18-398 supplied beef heart's 44/2); cite underlying refs | independent (0/26 incidental matches) |
| SR-US:Lamb, variety meats, heart, raw (FDC 172527) - US domestic grain-fed | US domestic frame CONTRAST (grain-fed, n=12): fed population is NZ/AU grass-fed per Shahab - kept as lineage corroboration that cardiac fat runs 3.7-5.7 across systems; never independent | USDA-affiliated — evidence, never independent confirmation |
| SR-US:Lamb, variety meats, heart, raw (FDC 172527) | US grain-fed Se (Se-rich feed) - frame contrast only; the fed population follows NZ low-Se soils (primary 10.9). Region-sensitive row: resolution must document the NZ choice | USDA-affiliated — evidence, never independent confirmation |
| CardiacFamily:Cross-species cardiac scaling (validated hearts 10007/10029/10050) | No lamb-heart taurine measurement in any local resource. Ruminant cardiac convention = beef heart 10050's validated 65 (muscle 36-43 x cardiac ratio ~1.5); ovine muscle taurine sits in the same band as bovine. SPARSE-EVIDENCE flag - same convention, same caveat as 10050 | no USDA overlap — independence not establishable |
| CardiacFamily:Ruminant cardiac total-K convention (MEXT beef heart 11091) | No lamb vit K row anywhere; ruminant cardiac MK-4 convention = beef heart's 5 (MEXT total-K; ruminant MK-4 << poultry's 50). Cross-species, flag in comment | no USDA overlap — independence not establishable |
| CardiacFamily:Cardiac choline family (chicken 227 FDC-2023, beef 229 FDC-2023-via-FCDB) | No lamb choline row anywhere; mammalian/avian cardiac choline is tightly clustered 227-229 - cross-species estimate at the family midpoint, sparse-evidence flag | no USDA overlap — independence not establishable |
| CardiacFamily:Cardiac iodine family (beef 1.8 FCDB n=1 + CIQUAL 1.9) | No lamb iodine row; ruminant cardiac iodine ~1.8-1.9 per the beef heart adoption. If CoFID 18-396 carries a measured lamb value, prefer it at review | no USDA overlap — independence not establishable |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | BLS | CardiacFamily | CoFID | SR-US | verdict |
|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | — | 18.09 (n=1) | 17.6≈ | — | 17.1° | — | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | BLS | CardiacFamily | CoFID | SR-US | verdict |
|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 1.218 | 1.22≈ | — | — | — | **usda_only** |
| Histidine (1221) | g | — | 0.383 | 0.383≈ | — | — | — | **usda_only** |
| Isoleucine (1212) | g | — | 0.81 | 0.81≈ | — | — | — | **usda_only** |
| Leucine (1213) | g | — | 1.397 | 1.4≈ | — | — | — | **usda_only** |
| Lysine (1214) | g | — | 1.58 | 1.58≈ | — | — | — | **usda_only** |
| Methionine (1215) | g | — | 0.59 | 0.59≈ | — | — | — | **usda_only** |
| Cystine (1216) | g | — | 0.237 | 0.237≈ | — | — | — | **usda_only** |
| Phenylalanine (1217) | g | — | 0.712 | 0.712≈ | — | — | — | **usda_only** |
| Tyrosine (1218) | g | — | 0.627 | 0.627≈ | — | — | — | **usda_only** |
| Threonine (1211) | g | — | 0.863 | 0.863≈ | — | — | — | **usda_only** |
| Tryptophan (1210) | g | — | 0.2 | 0.2≈ | — | — | — | **usda_only** |
| Valine (1219) | g | — | 0.921 | 0.921≈ | — | — | — | **usda_only** |
| Taurine (1234) | mg | — | — | — | 65~ | — | — | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | BLS | CardiacFamily | CoFID | SR-US | verdict |
|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | — | 3.68 (n=1) | 6.8≈ | — | 6.8° | 5.68 (n=12) | **review** |

## Fatty Acid

| nutrient | unit | FND | SR | BLS | CardiacFamily | CoFID | SR-US | verdict |
|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 0.34? | 0.31≈ | — | 0.31° | — | **confirm** |
| Arachidonic acid (1271) | g | — | 0.091? | 0.05≈ | — | 0.05° | — | **review** |
| Alpha-linolenic acid (1270) | g | — | 0.096? | 0.09≈ | — | 0.09° | — | **confirm** |
| EPA (1278) | g | — | 0.059 (n=1) | 0.04≈ | — | 0.04° | — | **region_keep** |
| DHA (1272) | g | — | 0.021 (n=1) | 0≈ | — | 0° | — | **region_keep** |
| Fatty acids, total polyunsaturated (1293) | g | — | 0.646‡ | 0.49≈ | — | 0.5° | — | **review** |
| DPA 22:5 n-3 (1280) | g | — | 0.032 (n=1) | 0≈ | — | 0° | — | **region_keep** |

## Mineral

| nutrient | unit | FND | SR | BLS | CardiacFamily | CoFID | SR-US | verdict |
|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | — | 5 (n=1) | 6≈ | — | 7° | — | **review** |
| Phosphorus (1091) | mg | — | 204 (n=1) | 207≈ | — | 210° | — | **confirm** |
| Potassium (1092) | mg | — | 277 (n=1) | 278≈ | — | 280° | — | **confirm** |
| Sodium (1093) | mg | — | 94 (n=1) | 117≈ | — | 140° | — | **review** |
| Chloride (1088) | mg | — | — | 140≈ | — | 140° | — | **adopt_foreign** |
| Magnesium (1090) | mg | — | 20 (n=1) | 20≈ | — | 21° | — | **confirm** |
| Iron (1089) | mg | — | 3.29 (n=1) | 3.4≈ | — | 3.6° | — | **confirm** |
| Copper (1098) | mg | — | 0.412 (n=1) | 0.47≈ | — | 0.52° | — | **review** |
| Manganese (1101) | mg | — | 0.022 (n=1) | 0.02≈ | — | 0.02° | — | **confirm** |
| Zinc (1095) | mg | — | 1.65 (n=1) | 2≈ | — | 2° | — | **confirm** |
| Iodine (1100) | µg | — | — | 1.1≈ | 1.8~ | — | — | **adopt_foreign** |
| Selenium (1103) | µg | — | 10.9 (n=1) | — | — | 2° | 32 (n=3) | **region_keep** |

## Vitamin

| nutrient | unit | FND | SR | BLS | CardiacFamily | CoFID | SR-US | verdict |
|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | — | 16.65? | 16.65≈ | — | 0 tr | — | **usda_only** |
| Vitamin D (1110) | IU | — | 1 (n=1) | 0≈ | — | — | — | **usda_only** |
| Vitamin E (1109) | IU | — | 0.9685 (n=1) | 0.9685≈ | — | 0.5513° | — | **confirm** |
| Vitamin K (1185) | µg | — | — | — | 5~ | — | — | **adopt_foreign** |
| Thiamin (1165) | mg | — | 0.52 (n=1) | 0.5≈ | — | 0.48° | — | **confirm** |
| Riboflavin (1166) | mg | — | 0.537 (n=1) | 0.7≈ | — | 0.9° | — | **review** |
| Niacin (1167) | mg | — | 5.757 (n=1) | 6.3≈ | — | 6.9° | — | **confirm** |
| Pantothenic acid (1170) | mg | — | 2.244 (n=1) | 2.4≈ | — | 2.5° | — | **confirm** |
| Pyridoxine (1175) | mg | — | 0.144 (n=1) | 0.22≈ | — | 0.29° | — | **review** |
| Folic acid (1177) | µg | — | — | 2≈ | — | 2° | 2 (n=2) | **adopt_foreign** |
| Cobalamin (1178) | µg | — | 8.4 (n=1) | 8≈ | — | 8° | — | **confirm** |
| Biotin (1176) | µg | — | — | 4≈ | — | 4° | — | **adopt_foreign** |
| Choline (1180) | mg | — | — | — | 228~ | — | — | **adopt_foreign** |

## Other

| nutrient | unit | FND | SR | BLS | CardiacFamily | CoFID | SR-US | verdict |
|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 105‡ | 132≈ | — | 129° | — | **confirm** |
| Water (1051) | g | — | 77.84 (n=1) | 76.7≈ | — | 75.6° | — | **confirm** |
| Ash (1007) | g | — | 1.13 (n=1) | 1.13≈ | — | — | — | **usda_only** |
| Crude Fiber (1079) | g | — | 0† | 0≈ | — | — | — | **usda_only** |
| Carbohydrate (1005) | g | — | 0‡ | 0≈ | — | — | — | **usda_only** |

## Needs attention (contested rows + detection-limit context)

### Taurine (1234) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 65 mg (source `literature`)
  - CardiacFamily [estimated] 65 — No lamb-heart taurine measurement in any local resource. Ruminant cardiac convention = beef heart 10050's validated 65 (

### Total Fat (1004) — review
- all 1 independent(s) differ >±20% from sr_legacy 3.68: CoFID 6.8
- suggestion: 3.68 g (source `sr_legacy`)
  - BLS [echo] 6.8 — FAT [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - CoFID [compiled] 6.8 — Fat; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty Acid 
  - SR-US [analysed] 5.68 — US domestic frame CONTRAST (grain-fed, n=12): fed population is NZ/AU grass-fed per Shahab - kept as lineage corroborati

### Arachidonic acid (1271) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.091: CoFID 0.05
- suggestion: 0.091 g (source `sr_legacy`)
  - BLS [echo] 0.05 — F20:4CN6 [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borr
  - CoFID [compiled] 0.05 — cis n-6 C20:4; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from F

### EPA (1278) — region_keep
- region-sensitive; foreign cluster differs: CoFID 0.04 — US mean kept unless defective
- suggestion: 0.059 g (source `sr_legacy`)
  - BLS [echo] 0.04 — F20:5CN3 [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borr
  - CoFID [compiled] 0.04 — cis n-3 C20:5; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from F

### DHA (1272) — region_keep
- region-sensitive; foreign cluster differs: CoFID 0 — US mean kept unless defective
- suggestion: 0.021 g (source `sr_legacy`)
  - BLS [echo] 0 — F22:6CN3 [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borr
  - CoFID [compiled] 0 — cis n-3 C22:6; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from F

### Fatty acids, total polyunsaturated (1293) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.646: CoFID 0.5
- suggestion: 0.646 g (source `sr_legacy`)
  - BLS [echo] 0.49 — FAPU [Formelberechnung] -; was computed
  - CoFID [compiled] 0.5 — Poly FA /100g food; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids f

### DPA 22:5 n-3 (1280) — region_keep
- region-sensitive; foreign cluster differs: CoFID 0 — US mean kept unless defective
- suggestion: 0.032 g (source `sr_legacy`)
  - BLS [echo] 0 — F22:5CN3 [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borr
  - CoFID [compiled] 0 — cis n-3 C22:5; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from F

### Calcium (1087) — review
- all 1 independent(s) differ >±20% from sr_legacy 5: CoFID 7
- suggestion: 5 mg (source `sr_legacy`)
  - BLS [echo] 6 — CA [Aggregation] US Department of Agriculture, Agricultural Research Service; USDA National Nutri; was borrowed
  - CoFID [compiled] 7 — Calcium; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty A

### Sodium (1093) — review
- all 1 independent(s) differ >±20% from sr_legacy 94: CoFID 140
- suggestion: 94 mg (source `sr_legacy`)
  - BLS [echo] 117 — NA [Aggregation] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - CoFID [compiled] 140 — Sodium; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty Ac

### Chloride (1088) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 140 mg (source `literature`)
  - BLS [echo] 140 — CLD [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - CoFID [compiled] 140 — Chloride; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty 

### Copper (1098) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.412: CoFID 0.52
- suggestion: 0.412 mg (source `sr_legacy`)
  - BLS [echo] 0.47 — CU [Aggregation] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - CoFID [compiled] 0.52 — Copper; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty Ac

### Iodine (1100) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 1.8 µg (source `literature`)
  - BLS [echo] 1.1 — ID [Übernommener Wert] -; was borrowed
  - CardiacFamily [estimated] 1.8 — No lamb iodine row; ruminant cardiac iodine ~1.8-1.9 per the beef heart adoption. If CoFID 18-396 carries a measured lam

### Selenium (1103) — region_keep
- region-sensitive; foreign cluster differs: CoFID 2 — US mean kept unless defective
- suggestion: 10.9 µg (source `sr_legacy`)
  - CoFID [compiled] 2 — Selenium; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty 
  - SR-US [analysed] 32 — US grain-fed Se (Se-rich feed) - frame contrast only; the fed population follows NZ low-Se soils (primary 10.9). Region-

### Vitamin A (1106) — usda_only
- no independent foreign value
- detection-limit info: CoFID trace
- suggestion: 16.65 IU (source `sr_legacy`)
  - BLS [echo] 16.65 — RETOL [Nährstoffdatenbank] Converted value from: US Department of Agriculture, Agricultural Research Servic; was borrowe
  - CoFID [trace] 0 — Retinol; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty A

### Vitamin K (1185) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 5 µg (source `literature`)
  - CardiacFamily [estimated] 5 — No lamb vit K row anywhere; ruminant cardiac MK-4 convention = beef heart's 5 (MEXT total-K; ruminant MK-4 << poultry's 

### Riboflavin (1166) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.537: CoFID 0.9
- suggestion: 0.537 mg (source `sr_legacy`)
  - BLS [echo] 0.7 — RIBF [Aggregation] US Department of Agriculture, Agricultural Research Service; USDA National Nutri; was borrowed
  - CoFID [compiled] 0.9 — Riboflavin; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatt

### Pyridoxine (1175) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.144: CoFID 0.29
- suggestion: 0.144 mg (source `sr_legacy`)
  - BLS [echo] 0.22 — VITB6 [Aggregation] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - CoFID [compiled] 0.29 — Vitamin B6; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatt

### Folic acid (1177) — adopt_foreign
- no USDA value; 2 measured source(s) available
- suggestion: 2 µg (source `literature`)
  - BLS [echo] 2 — FOLFD [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowe
  - CoFID [compiled] 2 — Folate; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty Ac
  - SR-US [analysed] 2 — Folate missing from the NZ entry; US domestic measured 2 (n=2) - cardiac folate is uniformly low (beef heart 3, CIQUAL b

### Biotin (1176) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 4 µg (source `literature`)
  - BLS [echo] 4 — BIOT [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - CoFID [compiled] 4 — Biotin; refs: MW4, 1978. Values reviewed for Meat, Poultry and Game Supplement, 1995. Fats and fatty acids from Fatty Ac

### Choline (1180) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 228 mg (source `literature`)
  - CardiacFamily [estimated] 228 — No lamb choline row anywhere; mammalian/avian cardiac choline is tightly clustered 227-229 - cross-species estimate at t

## Verdict summary

- usda_only: 17
- confirm: 16
- review: 8
- adopt_foreign: 7
- region_keep: 4
