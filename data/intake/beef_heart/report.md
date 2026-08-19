# Intake report: beef heart raw

- generated: 2026-08-19  |  spec: `data/intake/beef_heart.json`
- Foundation FDC: —  |  SR Legacy FDC: 168625
- category: Organ Meat  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: FRAME: trimmed heart muscle (cap/vessels off) — confirmed by Shahab 2026-08-18; every dataset is trimmed-frame (fat cluster 2.95-3.94; MEXT 7.6 is semi-trimmed JP convention). Wegmans sells trimmed; price 0.0099/g as sold.
- note: SR-only food: no Foundation entry exists for beef heart.
- note: Cardiac siblings for cross-species anchors: chicken heart 10007 (validated: vit K MK-4 50, taurine 231), turkey heart 10029.
- note: Seong 2014 B1/B2/B6 columns NOT curated (PDF column ambiguity: B2 0.07 vs cardiac family ~0.9) — consult the PDF visually if those rows contest.

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| FCDB:641 Heart, beef, raw | Heart, beef, raw — Danish analytical; stats n=4-6 on Ca/Mg/P/folate (cv-v8 FOOD_MAP candidate) | independent (4/27 incidental matches) |
| MEXT:11091 Beef, offal and by-products, heart, raw | beef heart raw — SEMI-TRIMMED frame (fat 7.6 vs cluster ~3.5): expect fat and fat-tracking rows to read high; minerals/water-solubles comparable | independent (0/26 incidental matches) |
| CIQUAL:40052 Coeur, boeuf, cru | Coeur, boeuf, cru — echo suspect (chicken heart's CIQUAL entry was a USDA copy; screener decides) | independent (10/26 incidental matches) |
| CoFID:18-398 Heart, ox, raw | Heart, ox, raw — UK; cite underlying survey from refs | independent (0/23 incidental matches) |
| SR-NZ:Beef, New Zealand imported, heart, raw (FDC 174723) | USDA NZ-imported entry — grass-fed frame corroboration for trimmed fat; USDA lineage, never independent | USDA-affiliated — evidence, never independent confirmation |
| Seong14:Hanwoo beef heart | Seong 2014 vitamin table: niacin 7.46±1.06 mg/100 g, hanwoo cattle heart | independent (0/2 incidental matches) |
| Biel19:Beef heart | Biel 2019 prose: beef hearts Mn 0.29 mg/100 g (veal 0.35) | independent (0/1 incidental matches) |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | Biel19 | CIQUAL | CoFID | FCDB | MEXT | SR-NZ | Seong14 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | — | 17.72 (n=1) | — | 18.5° | 18.2° | 17.7188† (n=1) | 16.5 | — | — | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | Biel19 | CIQUAL | CoFID | FCDB | MEXT | SR-NZ | Seong14 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | — | — | — | — | 1.10565? | 1 | — | — | **adopt_foreign** |
| Histidine (1221) | g | — | — | — | — | — | 0.48195? | 0.43 | — | — | **adopt_foreign** |
| Isoleucine (1212) | g | — | — | — | — | — | 0.8505? | 0.73 | — | — | **adopt_foreign** |
| Leucine (1213) | g | — | — | — | — | — | 1.61595? | 1.4 | — | — | **adopt_foreign** |
| Lysine (1214) | g | — | — | — | — | — | 1.6443? | 1.3 | — | — | **adopt_foreign** |
| Methionine (1215) | g | — | — | — | — | — | 0.4536? | 0.41 | — | — | **adopt_foreign** |
| Cystine (1216) | g | — | — | — | — | — | 0.184275? | 0.22 | — | — | **adopt_foreign** |
| Phenylalanine (1217) | g | — | — | — | — | — | 0.82215? | 0.7 | — | — | **adopt_foreign** |
| Tyrosine (1218) | g | — | — | — | — | — | 0.65205? | 0.53 | — | — | **adopt_foreign** |
| Threonine (1211) | g | — | — | — | — | — | 0.82215? | 0.69 | — | — | **adopt_foreign** |
| Tryptophan (1210) | g | — | — | — | — | — | 1.95615? | 0.21 | — | — | **adopt_foreign** |
| Valine (1219) | g | — | — | — | — | — | 0.06804? | 0.85 | — | — | **adopt_foreign** |
| Taurine (1234) | mg | — | — | — | — | — | — | — | — | — | **no_evidence** |

## Fat

| nutrient | unit | FND | SR | Biel19 | CIQUAL | CoFID | FCDB | MEXT | SR-NZ | Seong14 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | — | 3.94 (n=1) | — | 2.95° | 3.5° | 3.08 (n=3) | 7.6 | 3.4 | — | **confirm** |

## Fatty Acid

| nutrient | unit | FND | SR | Biel19 | CIQUAL | CoFID | FCDB | MEXT | SR-NZ | Seong14 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 0.395 (n=1) | — | 0.27° | — | 0.346305 (n=3) | 0.29 | — | — | **confirm** |
| Arachidonic acid (1271) | g | — | 0.128 (n=1) | — | — | — | — | 0.02 | — | — | **review** |
| Alpha-linolenic acid (1270) | g | — | 0.016? | — | 0.026° | — | 0.0300048 (n=3) | 0.002 | — | — | **confirm** |
| EPA (1278) | g | — | 0† | — | 0° | — | 0.0212534 (n=3) | 0 | — | — | **confirm** |
| DHA (1272) | g | — | 0† | — | 0° | — | 0.0043757 (n=3) | 0 | — | — | **confirm** |
| Fatty acids, total polyunsaturated (1293) | g | — | 0.546 (n=1) | — | — | 0.1° | 0.58353‡ | 0.33 | — | — | **review** |
| DPA 22:5 n-3 (1280) | g | — | 0† | — | — | — | 0.0196906 (n=3) | 0 | — | — | **confirm** |

## Mineral

| nutrient | unit | FND | SR | Biel19 | CIQUAL | CoFID | FCDB | MEXT | SR-NZ | Seong14 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | — | 7 (n=1) | — | 7° | 5° | 3.95 (n=6) | 5 | — | — | **confirm** |
| Phosphorus (1091) | mg | — | 212 (n=1) | — | 212° | 210° | 214 (n=6) | 170 | — | — | **confirm** |
| Potassium (1092) | mg | — | 287 (n=1) | — | 287° | 290° | 240 (n=1) | 260 | — | — | **confirm** |
| Sodium (1093) | mg | — | 98 (n=1) | — | 81.7° | 88° | 95 (n=1) | 70 | — | — | **confirm** |
| Chloride (1088) | mg | — | — | — | — | 44° | — | — | — | — | **adopt_foreign** |
| Magnesium (1090) | mg | — | 21 (n=1) | — | 21° | 22° | 17 (n=4) | 23 | — | — | **confirm** |
| Iron (1089) | mg | — | 4.31 (n=1) | — | 5.14° | 5° | 4.2 (n=1) | 3.3 | — | 5.888 | **confirm** |
| Copper (1098) | mg | — | 0.396 (n=1) | — | 0.4° | 0.37° | 0.31 (n=1) | 0.42 | — | — | **confirm** |
| Manganese (1101) | mg | — | 0.035 (n=1) | 0.29 | 0.035° | 0.04° | 0.032? (n=3) | — | — | — | **confirm** |
| Zinc (1095) | mg | — | 1.7 (n=1) | — | 1.49° | 1.8° | 1.4 (n=1) | 2.1 | — | — | **confirm** |
| Iodine (1100) | µg | — | — | — | 1.9° | — | 1.8 (n=1) | — | — | — | **adopt_foreign** |
| Selenium (1103) | µg | — | 21.8 (n=1) | — | 23.5° | 3° | 14? (n=2) | — | — | — | **confirm** |

## Vitamin

| nutrient | unit | FND | SR | Biel19 | CIQUAL | CoFID | FCDB | MEXT | SR-NZ | Seong14 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | — | 0? | — | 0° | 0 tr | 0† (n=1) | 29.97 | — | 41.5917 | **confirm** |
| Vitamin D (1110) | IU | — | — | — | 37.2° | — | 40‡ | 0 | — | — | **adopt_foreign** |
| Vitamin E (1109) | IU | — | 0.3278 (n=2) | — | 0.3278° | 0.6705° | 0.298‡ (n=1) | 0.894 | — | — | **confirm** |
| Vitamin K (1185) | µg | — | 0 (n=2) | — | 0° | — | 0‡ | 5 | — | — | **form_defect** |
| Thiamin (1165) | mg | — | 0.238 (n=1) | — | 0.24° | 0.45° | 0.335 (n=1) | 0.37254 | — | — | **confirm** |
| Riboflavin (1166) | mg | — | 0.906 (n=1) | — | 0.91° | 0.8° | 0.75 (n=1) | 0.9 | — | — | **confirm** |
| Niacin (1167) | mg | — | 7.53 (n=1) | — | 6.78° | 6.3° | 7.5 (n=1) | 5.8 | — | 7.46 | **confirm** |
| Pantothenic acid (1170) | mg | — | 1.79 (n=1) | — | 1.79° | 2.4° | 2.5 | 2.16 | — | — | **confirm** |
| Pyridoxine (1175) | mg | — | 0.279 (n=1) | — | 0.11° | 0.23° | 0.26 (n=2) | 0.29 | — | — | **confirm** |
| Folic acid (1177) | µg | — | 3 (n=2) | — | 3° | 4° | 20 (n=6) | 16 | — | — | **confirm** |
| Cobalamin (1178) | µg | — | 8.55 (n=1) | — | 8.44° | 13° | 10 (n=2) | 12.1 | — | — | **confirm** |
| Biotin (1176) | µg | — | — | — | — | 2° | 2† | — | — | — | **adopt_foreign** |
| Choline (1180) | mg | — | — | — | — | — | 229† (n=1) | — | — | — | **review** |

## Other

| nutrient | unit | FND | SR | Biel19 | CIQUAL | CoFID | FCDB | MEXT | SR-NZ | Seong14 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 112‡ | — | 103‡ | 104° | 102.56‡ | 142‡ | — | — | **confirm** |
| Water (1051) | g | — | 77.11 (n=1) | — | 79° | 76.4° | 77.11† (n=1) | 74.8 | — | — | **confirm** |
| Ash (1007) | g | — | 1.1 (n=1) | — | 1.1° | — | 1.1† (n=1) | 1 | — | — | **confirm** |
| Crude Fiber (1079) | g | — | 0† | — | 0° | — | 0† | 0~ | — | — | **confirm** |
| Carbohydrate (1005) | g | — | 0.14‡ | — | 0.6° | — | 0.99125‡ | 0.1 | — | — | **review** |

## Needs attention (contested rows + detection-limit context)

### Arginine (1220) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 1 g (source `literature`)
  - FCDB [unknown] 1.10565 — Arginine
  - MEXT [analysed] 1 — ARG (AA volume, per 100 g EP)

### Histidine (1221) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.43 g (source `literature`)
  - FCDB [unknown] 0.48195 — Histidine
  - MEXT [analysed] 0.43 — HIS (AA volume, per 100 g EP)

### Isoleucine (1212) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.73 g (source `literature`)
  - FCDB [unknown] 0.8505 — Isoleucine
  - MEXT [analysed] 0.73 — ILE (AA volume, per 100 g EP)

### Leucine (1213) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 1.4 g (source `literature`)
  - FCDB [unknown] 1.61595 — Leucine
  - MEXT [analysed] 1.4 — LEU (AA volume, per 100 g EP)

### Lysine (1214) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 1.3 g (source `literature`)
  - FCDB [unknown] 1.6443 — Lysine
  - MEXT [analysed] 1.3 — LYS (AA volume, per 100 g EP)

### Methionine (1215) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.41 g (source `literature`)
  - FCDB [unknown] 0.4536 — Methionine
  - MEXT [analysed] 0.41 — MET (AA volume, per 100 g EP)

### Cystine (1216) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.22 g (source `literature`)
  - FCDB [unknown] 0.184275 — Cystine
  - MEXT [analysed] 0.22 — CYS (AA volume, per 100 g EP)

### Phenylalanine (1217) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.7 g (source `literature`)
  - FCDB [unknown] 0.82215 — Phenylalanine
  - MEXT [analysed] 0.7 — PHE (AA volume, per 100 g EP)

### Tyrosine (1218) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.53 g (source `literature`)
  - FCDB [unknown] 0.65205 — Tyrosine
  - MEXT [analysed] 0.53 — TYR (AA volume, per 100 g EP)

### Threonine (1211) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.69 g (source `literature`)
  - FCDB [unknown] 0.82215 — Threonine
  - MEXT [analysed] 0.69 — THR (AA volume, per 100 g EP)

### Tryptophan (1210) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.21 g (source `literature`)
  - FCDB [unknown] 1.95615 — Tryptophan
  - MEXT [analysed] 0.21 — TRP (AA volume, per 100 g EP)

### Valine (1219) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.85 g (source `literature`)
  - FCDB [unknown] 0.06804 — Valine
  - MEXT [analysed] 0.85 — VAL (AA volume, per 100 g EP)

### Taurine (1234) — no_evidence
- no measurement in any local resource — operator/literature call

### Arachidonic acid (1271) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.128: MEXT 0.02
- suggestion: 0.128 g (source `sr_legacy`)
  - MEXT [analysed] 0.02 — F20D4N6 (FA volume, per 100 g EP)

### Fatty acids, total polyunsaturated (1293) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.546: MEXT 0.33, CoFID 0.1
- suggestion: 0.546 g (source `sr_legacy`)
  - FCDB [computed] 0.58353 — Sum polyunsaturated fatty acids; src [1003] Value calculated by converting various analytical data
  - MEXT [analysed] 0.33 — FAPU (FA volume, per 100 g EP)
  - CoFID [compiled] 0.1 — Poly FA /100g food; refs: LGC, Carcase meat and offal survey, 1982-1983

### Chloride (1088) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 44 mg (source `literature`)
  - CoFID [compiled] 44 — Chloride; refs: LGC, Carcase meat and offal survey, 1982-1983

### Iodine (1100) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 1.8 µg (source `literature`)
  - FCDB [analysed] 1.8 — Iodine; src [1055] The iodine content of Danish food (1982)
  - CIQUAL [compiled] 1.9 — Iode

### Vitamin A (1106) — confirm
- 1/3 independent(s) within ±20%: CIQUAL 0
- detection-limit info: CoFID trace
- suggestion: 0 IU (source `sr_legacy`)
  - FCDB [borrowed] 0 — Retinol; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - MEXT [analysed] 29.97 — RETOL (main volume)
  - CIQUAL [compiled] 0 — Rétinol
  - CoFID [trace] 0 — Retinol; refs: LGC, Carcase meat and offal survey, 1982-1983
  - Seong14 [analysed] 41.5917 — Seong 2014 vitamin table: vitamin A 12.49±2.69 µg/100 g (retinol basis), hanwoo cattle heart

### Vitamin D (1110) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0 IU (source `literature`)
  - FCDB [computed] 40 — Vitamin D; src [1003] Value calculated by converting various analytical data
  - MEXT [analysed] 0 — VITD (main volume)
  - CIQUAL [compiled] 37.2 — Vitamine D

### Vitamin K (1185) — form_defect
- USDA K row is K1-only (0 µg); menaquinone-inclusive tables read ~5 µg
- suggestion: 5 µg (source `literature`)
  - FCDB [computed] 0 — Vitamin K; src [1003] Value calculated by converting various analytical data
  - MEXT [analysed] 5 — VITK (main volume); menaquinone-inclusive total K
  - CIQUAL [compiled] 0 — Vitamine K1 only; K2 n/a

### Biotin (1176) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 2 µg (source `literature`)
  - FCDB [borrowed] 2 — Biotin; src [1344] McCance and Widdowson's: The Composition of Foods, 4th revised and extended edition (1978)
  - CoFID [compiled] 2 — Biotin; refs: LGC, Carcase meat and offal survey, 1982-1983

### Choline (1180) — review
- no USDA value and no measured foreign value (only borrowed) — operator/literature call
  - FCDB [borrowed] 229 — Choline; src [2187] FoodData Central (2023)

### Carbohydrate (1005) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.14: MEXT 0.1, CIQUAL 0.6
- suggestion: 0.14 g (source `sr_legacy`)
  - FCDB [computed] 0.99125 — Carbohydrate by difference; src [1003] Value calculated by converting various analytical data
  - MEXT [analysed] 0.1 — Carbohydrate, total (main volume)
  - CIQUAL [compiled] 0.6 — Glucides

## Verdict summary

- confirm: 30
- adopt_foreign: 16
- review: 4
- no_evidence: 1
- form_defect: 1
