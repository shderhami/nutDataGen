# Intake report: duck meat and skin raw

- generated: 2026-09-01  |  spec: `data/intake/duck_meat_skin.json`
- Foundation FDC: —  |  SR Legacy FDC: 172408
- category: Muscle Meat  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: PRICE: $4.40/lb Costco whole Pekin sticker (Shahab 2026-09-01) / 453.592 = 0.0097/g as-sold, / 0.58 assumed boneless-edible yield = 0.0167/g. SAME price as the sibling (whole-bird cost allocates uniformly per edible gram). Yield assumption adjustable - CONFIRM at approval.
- note: SIBLING PAIR (option A, approved 2026-09-01): this is the SKIN-ON composite - the recipe's FAT DILUENT. Sibling spec = duck_meat_skinless.json (SR 172410, 'duck meat only raw'). DO NOT confuse: this entry is SR 172408, fat 39.34, kcal 404, Met 0.72/1000 kcal, fat 97/1000 kcal - NEVER feasible standalone; recipes use it at ~10-25% alongside the skinless sibling.
- note: WHY TWO ENTRIES: see sibling spec - derived skin refuted, measured-composite blending exact (MEXT triple f=0.405, rms 0.3%).
- note: FRAME: whole-bird flesh + ALL skin and separable fat (USDA composite incl. fat depots - hence 39.3% fat vs MEXT JP composite's 19.8%; the frames differ, expect fat-tracking rows to read high vs internationals and resolve on frame grounds, cv_intl-EXCLUDES-style reasoning in comments). 'Domesticated' = White Pekin, the Costco breed. Giblets/neck NOT part of this entry.
- note: Panel: 91 nutrients, full 12/12 AA, vit D/E/K/A + choline native; only Cl/I/biotin/taurine gaps.
- note: POULTRY DOCTRINE expectations: vit K form_defect WILL fire (SR K1-only vs MEXT total_k; skin-on dark poultry - thigh skin-on 10001 adopted MEXT total 20); taurine lean-scaled from the dark-meat anchor (169 x protein ratio 11.49/18.28 = 106).
- note: Internationals: 5 frame-matched adapters (FCDB 101 flesh+skin, BLS V464100, MEXT 11206, CoFID 18-371 'meat, fat and skin', AFCD F003634 'lean flesh, skin & fat').

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| FCDB:101 Duck, flesh and skin, raw | Duck, flesh and skin, raw - Danish; leaner EU composite expected vs US all-fat-depot frame; frame note on fat rows | ECHO of USDA (19/40 values identical to <0.5%) |
| BLS:V464100 Duck meat, with skin, raw | Duck meat, with skin, raw - German; frame likely leaner than US composite | independent (1/40 incidental matches) |
| MEXT:11206 Duck, domesticated, meat with skin, raw | Duck, domesticated, meat with skin, raw - JP composite is 19.8% fat vs our 39.3 (fat-depot inclusion differs); minerals/water-solubles comparable, fat-tracking rows resolve on frame; total-K carrier | independent (0/41 incidental matches) |
| CoFID:18-371 Duck, raw, meat, fat and skin | Duck, raw, meat, fat and skin - UK; the closest foreign frame (explicitly includes fat); chloride + biotin carrier | independent (1/21 incidental matches) |
| AFCD:F003634 Duck, lean flesh, skin & fat, raw | Duck, lean flesh, skin & fat, raw - Australian; frame-close; check Derivation flag | independent (0/27 incidental matches) |
| Spitze03:Chicken dark meat, lean-scaled to this composite (no duck taurine exists locally) | Spitze chicken dark meat 169 (thigh-validated anchor) x lean-mass ratio 11.49/18.28 (this composite's protein vs the skinless sibling's) = 106. Skin carries ~no taurine; lean-scaling convention per 10035->10055 discussions. Cross-species, SPARSE-EVIDENCE flag | no USDA overlap — independence not establishable |
| PoultryFamily:Poultry muscle iodine (TDS chicken family ~1), skin-diluted | No duck iodine anywhere. Poultry family = 1 µg; skin dilution is within the anchor's own uncertainty, kept at 1. Cross-species, SPARSE-EVIDENCE flag | no USDA overlap — independence not establishable |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | — | 11.49? | 13‡ | 18.1† | 13.1° | 11.46≈ | 14.9 | — | — | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 0.77? | — | 1.1† | — | 0.77196≈ | 1.1 | — | — | **review** |
| Histidine (1221) | g | — | 0.283? | — | 0.41† | — | 0.2757≈ | 0.48 | — | — | **review** |
| Isoleucine (1212) | g | — | 0.537? | — | 0.94† | — | 0.53302≈ | 0.66 | — | — | **confirm** |
| Leucine (1213) | g | — | 0.9? | — | 1.4† | — | 0.90062≈ | 1.2 | — | — | **review** |
| Lysine (1214) | g | — | 0.912? | — | 1.56† | — | 0.919≈ | 1.2 | — | — | **review** |
| Methionine (1215) | g | — | 0.291? | — | 0.45† | — | 0.29408≈ | 0.38 | — | — | **review** |
| Cystine (1216) | g | — | 0.18? | — | 0.281‡ | — | 0.180124≈ | 0.17 | — | — | **confirm** |
| Phenylalanine (1217) | g | — | 0.459? | — | 0.71† | — | 0.4595≈ | 0.6 | — | — | **review** |
| Tyrosine (1218) | g | — | 0.395? | — | 0.677‡ | — | 0.38598≈ | 0.51 | — | — | **review** |
| Threonine (1211) | g | — | 0.471? | — | 0.79† | — | 0.47788≈ | 0.66 | — | — | **review** |
| Tryptophan (1210) | g | — | 0.144? | 0.164‡ | 0.246‡ | — | 0.143364≈ | 0.17 | — | — | **confirm** |
| Valine (1219) | g | — | 0.573? | — | 0.87† | — | 0.56978≈ | 0.72 | — | — | **review** |
| Taurine (1234) | mg | — | — | — | — | — | — | — | — | 106~ | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | — | 39.34? | 36.9‡ | 17.2† | 37.3° | 39.34≈ | 19.8 | — | — | **confirm** |

## Fatty Acid

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 4.69? | 4.09‡ | 2.05† | — | 4.72165≈ | 4.1 | — | — | **confirm** |
| Arachidonic acid (1271) | g | — | 0? | 0.13051‡ | — | — | 0≈ | 0.12 | — | — | **review** |
| Alpha-linolenic acid (1270) | g | — | 0.39? | 0.24‡ | 0.171† | — | 0.391797≈ | 0.28 | — | — | **review** |
| EPA (1278) | g | — | 0? | 0‡ | — | — | 0≈ | 0.001 | — | — | **confirm** |
| DHA (1272) | g | — | 0? | 0.00216‡ | — | — | 0≈ | 0.002 | — | — | **confirm** |
| Fatty acids, total polyunsaturated (1293) | g | — | 5.08? | 4.47‡ | 2.221‡ | 5.6° | 5.11345≈ | 4.67 | — | — | **confirm** |
| DPA 22:5 n-3 (1280) | g | — | 0? | 0‡ | — | — | 0≈ | 0.019 | — | — | **region_keep** |

## Mineral

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | — | 11? | 5‡ | 14.6† | 8° | 11≈ | 5 | — | — | **review** |
| Phosphorus (1091) | mg | — | 139? | 94‡ | 198.7† | 120° | 139≈ | 160 | — | — | **confirm** |
| Potassium (1092) | mg | — | 209? | 153‡ | 265† | 190° | 297≈ (n=3) | 250 | — | — | **confirm** |
| Sodium (1093) | mg | — | 63? | 58‡ | 38† | 73° | 86≈ (n=3) | 67 | — | — | **confirm** |
| Chloride (1088) | mg | — | — | 78‡ | 85† | 62° | — | — | — | — | **adopt_foreign** |
| Magnesium (1090) | mg | — | 15? | 10‡ | 21.7† | 14° | 22≈ (n=3) | 17 | — | — | **confirm** |
| Iron (1089) | mg | — | 2.4? | 1.01‡ | 2.73† | 1.3° | 1.2≈ (n=2) | 1.6 | — | — | **review** |
| Copper (1098) | mg | — | 0.236? | 0.127‡ | 0.242† | 0.18° | 0.14≈ (n=5) | 0.2 | — | — | **confirm** |
| Manganese (1101) | mg | — | 0.017? | 0‡ | 0.05† | 0 tr | 0.017≈ | 0.01 | — | — | **confirm** |
| Zinc (1095) | mg | — | 1.36? | 1.09‡ | 1.84† | 1.3° | 1.35≈ (n=5) | 1.6 | — | — | **confirm** |
| Iodine (1100) | µg | — | — | 0.2‡ | — | — | 1.2≈ (n=3) | 7 | 1~ | — | **adopt_foreign** |
| Selenium (1103) | µg | — | 12.4? | 15.1‡ | — | — | 24≈ (n=5) | 16 | — | — | **region_keep** |

## Vitamin

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | — | 166.5‡ | 199.8‡ | 86.58† | 169.83° | 169.83≈ (n=20) | 206.46 | — | — | **confirm** |
| Vitamin D (1110) | IU | — | 26† | 176.8‡ | 12‡ | — | 40≈ | 32 | — | — | **confirm** |
| Vitamin E (1109) | IU | — | 1.043? | 0.447‡ | 1.27321† | — | 0≈ | 0.745 | — | — | **confirm** |
| Vitamin K (1185) | µg | — | 5.5† | — | 5.5‡ | — | 0≈ | 41 | — | — | **form_defect** |
| Thiamin (1165) | mg | — | 0.197 (n=20) | 0.156‡ | 0.3† | 0.14° | 0.197≈ (n=20) | 0.2661 | — | — | **review** |
| Riboflavin (1166) | mg | — | 0.21 (n=20) | 0.112‡ | 0.2† | 0.51° | 0.21≈ (n=20) | 0.26 | — | — | **confirm** |
| Niacin (1167) | mg | — | 3.934? | 2.51‡ | 3.5† | 3.5° | 3.934≈ | 5.3 | — | — | **confirm** |
| Pantothenic acid (1170) | mg | — | 0.951? | 0.79‡ | 0.701† | 0.95° | 0.951≈ | 1.2 | — | — | **confirm** |
| Pyridoxine (1175) | mg | — | 0.19 (n=20) | 0.05‡ | 0.53† | 0.33° | 0.19≈ (n=20) | 0.34 | — | — | **review** |
| Folic acid (1177) | µg | — | 13? | 0‡ | 21† | 7° | 48≈ (n=6) | 10 | — | — | **review** |
| Cobalamin (1178) | µg | — | 0.25? | 0.5‡ | 0.65† | 2° | 0.25≈ | 2.1 | — | — | **review** |
| Biotin (1176) | µg | — | — | 2‡ | 0.84† | — | 6≈ | 4 | — | — | **adopt_foreign** |
| Choline (1180) | mg | — | 31† | — | — | — | 31≈ (n=1) | — | — | — | **usda_only** |

## Other

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 404‡ | 378.824‡ | 227‡ | 388° | 399.9≈ | 250‡ | — | — | **confirm** |
| Water (1051) | g | — | 48.5? | 47.8‡ | 63.7† | 49.7° | 48.5≈ | 62.7 | — | — | **confirm** |
| Ash (1007) | g | — | 0.68? | 0.5‡ | 0.94† | — | 0.7≈ | 0.8 | — | — | **confirm** |
| Crude Fiber (1079) | g | — | 0† | 0‡ | 0‡ | — | 0≈ | 0~ | — | — | **confirm** |
| Carbohydrate (1005) | g | — | 0† | 0‡ | 0‡ | — | 0≈ | 0.1 | — | — | **replace_suggest** |

## Needs attention (contested rows + detection-limit context)

### Arginine (1220) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.77: MEXT 1.1
- suggestion: 0.77 g (source `sr_legacy`)
  - FCDB [echo] 0.77196 — Arginine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 1.1 — ARG [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 1.1 — ARG (AA volume, per 100 g EP)

### Histidine (1221) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.283: MEXT 0.48
- suggestion: 0.283 g (source `sr_legacy`)
  - FCDB [echo] 0.2757 — Histidine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 0.41 — HIS [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.48 — HIS (AA volume, per 100 g EP)

### Leucine (1213) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.9: MEXT 1.2
- suggestion: 0.9 g (source `sr_legacy`)
  - FCDB [echo] 0.90062 — Leucine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 1.4 — LEU [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 1.2 — LEU (AA volume, per 100 g EP)

### Lysine (1214) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.912: MEXT 1.2
- suggestion: 0.912 g (source `sr_legacy`)
  - FCDB [echo] 0.919 — Lysine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 1.56 — LYS [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 1.2 — LYS (AA volume, per 100 g EP)

### Methionine (1215) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.291: MEXT 0.38
- suggestion: 0.291 g (source `sr_legacy`)
  - FCDB [echo] 0.29408 — Methionine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 0.45 — MET [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.38 — MET (AA volume, per 100 g EP)

### Phenylalanine (1217) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.459: MEXT 0.6
- suggestion: 0.459 g (source `sr_legacy`)
  - FCDB [echo] 0.4595 — Phenylalanine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 0.71 — PHE [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.6 — PHE (AA volume, per 100 g EP)

### Tyrosine (1218) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.395: MEXT 0.51
- suggestion: 0.395 g (source `sr_legacy`)
  - FCDB [echo] 0.38598 — Tyrosine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [computed] 0.677 — TYR [Musterberechnung] -
  - MEXT [analysed] 0.51 — TYR (AA volume, per 100 g EP)

### Threonine (1211) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.471: MEXT 0.66
- suggestion: 0.471 g (source `sr_legacy`)
  - FCDB [echo] 0.47788 — Threonine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 0.79 — THR [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.66 — THR (AA volume, per 100 g EP)

### Valine (1219) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.573: MEXT 0.72
- suggestion: 0.573 g (source `sr_legacy`)
  - FCDB [echo] 0.56978 — Valine; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 0.87 — VAL [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.72 — VAL (AA volume, per 100 g EP)

### Taurine (1234) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 106 mg (source `literature`)
  - Spitze03 [estimated] 106 — Spitze chicken dark meat 169 (thigh-validated anchor) x lean-mass ratio 11.49/18.28 (this composite's protein vs the ski

### Arachidonic acid (1271) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: MEXT 0.12
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [echo] 0 — C20:4,n-6; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - MEXT [analysed] 0.12 — F20D4N6 (FA volume, per 100 g EP)
  - AFCD [computed] 0.13051 — C20:4w6; food-level derivation: Recipe

### Alpha-linolenic acid (1270) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.39: MEXT 0.28
- suggestion: 0.39 g (source `sr_legacy`)
  - FCDB [echo] 0.391797 — C18:3,n-3; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [borrowed] 0.171 — F18:3CN3 [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.28 — F18D3N3 (FA volume, per 100 g EP)
  - AFCD [computed] 0.24 — C18:3w3; food-level derivation: Recipe

### DPA 22:5 n-3 (1280) — region_keep
- region-sensitive; foreign cluster differs: MEXT 0.019 — US mean kept unless defective
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [echo] 0 — C22:5,n-3; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - MEXT [analysed] 0.019 — F22D5N3 (FA volume, per 100 g EP)
  - AFCD [computed] 0 — C22:5w3; food-level derivation: Recipe

### Calcium (1087) — review
- all 2 independent(s) differ >±20% from sr_legacy 11: MEXT 5, CoFID 8
- suggestion: 11 mg (source `sr_legacy`)
  - FCDB [echo] 11 — Calcium; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007); was borrowed
  - BLS [borrowed] 14.6 — CA [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 5 — CA (main volume)
  - CoFID [compiled] 8 — Calcium; refs: As Meat, Poultry and Game Supplement, 1995; and LGC, Poultry and game surveys, 1983-1984. Additional fatt
  - AFCD [computed] 5 — Calcium; food-level derivation: Recipe

### Chloride (1088) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 62 mg (source `literature`)
  - BLS [borrowed] 85 — CLD [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - CoFID [compiled] 62 — Chloride; refs: As Meat, Poultry and Game Supplement, 1995; and LGC, Poultry and game surveys, 1983-1984. Additional fat
  - AFCD [computed] 78 — Chloride; food-level derivation: Recipe

### Iron (1089) — review
- all 2 independent(s) differ >±20% from sr_legacy 2.4: MEXT 1.6, CoFID 1.3
- suggestion: 2.4 mg (source `sr_legacy`)
  - FCDB [echo] 1.2 — Iron; src [1043] The iron content of Danish foods (1978); was analysed
  - BLS [borrowed] 2.73 — FE [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 1.6 — FE (main volume)
  - CoFID [compiled] 1.3 — Iron; refs: As Meat, Poultry and Game Supplement, 1995; and LGC, Poultry and game surveys, 1983-1984. Additional fatty a
  - AFCD [computed] 1.01 — Iron; food-level derivation: Recipe

### Manganese (1101) — confirm
- 1/1 independent(s) within ±20%: MEXT 0.01
- detection-limit info: CoFID trace
- suggestion: 0.017 mg (source `sr_legacy`)
  - FCDB [echo] 0.017 — Manganese; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007); was borrowed
  - BLS [borrowed] 0.05 — MN [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.01 — MN (main volume)
  - CoFID [trace] 0 — Manganese; refs: As Meat, Poultry and Game Supplement, 1995; and LGC, Poultry and game surveys, 1983-1984. Additional fa
  - AFCD [computed] 0 — Manganese; food-level derivation: Recipe

### Iodine (1100) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 7 µg (source `literature`)
  - FCDB [echo] 1.2 — Iodine; src [1055] The iodine content of Danish food (1982); was analysed
  - MEXT [analysed] 7 — ID (main volume)
  - AFCD [computed] 0.2 — Iodine; food-level derivation: Recipe
  - PoultryFamily [estimated] 1 — No duck iodine anywhere. Poultry family = 1 µg; skin dilution is within the anchor's own uncertainty, kept at 1. Cross-s

### Selenium (1103) — region_keep
- region-sensitive; foreign cluster differs: MEXT 16 — US mean kept unless defective
- suggestion: 12.4 µg (source `sr_legacy`)
  - FCDB [echo] 24 — Selenium; src [1102] Trace Elements in Meat and Organs from Danish Slaughtered Animals, 1972-82 (1986); was analysed
  - MEXT [analysed] 16 — SE (main volume)
  - AFCD [computed] 15.1 — Selenium; food-level derivation: Recipe

### Vitamin K (1185) — form_defect
- USDA K row is K1-only (5.5 µg); menaquinone-inclusive tables read ~41 µg
- suggestion: 41 µg (source `literature`)
  - FCDB [echo] 0 — Vitamin K; src [1003] Value calculated by converting various analytical data; was computed
  - BLS [computed] 5.5 — VITK [Formelberechnung] -; VITK1=1.9µg, VITK2=3.6µg
  - MEXT [analysed] 41 — VITK (main volume); menaquinone-inclusive total K

### Thiamin (1165) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.197: MEXT 0.2661, CoFID 0.14
- suggestion: 0.197 mg (source `sr_legacy`)
  - FCDB [echo] 0.197 — Thiamin (Vitamin B1); src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007); was borrowed
  - BLS [borrowed] 0.3 — THIA [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.2661 — THIAHCL 0.3 x0.887 (HCl->thiamin base)
  - CoFID [compiled] 0.14 — Thiamin; refs: As Meat, Poultry and Game Supplement, 1995; and LGC, Poultry and game surveys, 1983-1984. Additional fatt
  - AFCD [computed] 0.156 — Thiamin; food-level derivation: Recipe

### Pyridoxine (1175) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.19: MEXT 0.34, CoFID 0.33
- suggestion: 0.19 mg (source `sr_legacy`)
  - FCDB [echo] 0.19 — Vitamin B6; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007); was borrowed
  - BLS [borrowed] 0.53 — VITB6 [Übernommener Wert] -
  - MEXT [analysed] 0.34 — VITB6A (main volume)
  - CoFID [compiled] 0.33 — Vitamin B6; refs: As Meat, Poultry and Game Supplement, 1995; and LGC, Poultry and game surveys, 1983-1984. Additional f
  - AFCD [computed] 0.05 — Pyridoxine B6; food-level derivation: Recipe

### Folic acid (1177) — review
- all 2 independent(s) differ >±20% from sr_legacy 13: MEXT 10, CoFID 7
- suggestion: 13 µg (source `sr_legacy`)
  - FCDB [echo] 48 — Folate; src [1803] Folacin content in foods (1993); was analysed
  - BLS [borrowed] 21 — FOLFD [Übernommener Wert] -
  - MEXT [analysed] 10 — FOL (main volume)
  - CoFID [compiled] 7 — Folate; refs: As Meat, Poultry and Game Supplement, 1995; and LGC, Poultry and game surveys, 1983-1984. Additional fatty
  - AFCD [computed] 0 — Folate, natural; food-level derivation: Recipe

### Cobalamin (1178) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.25: MEXT 2.1, CoFID 2
- suggestion: 0.25 µg (source `sr_legacy`)
  - FCDB [echo] 0.25 — Vitamin B12; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007); was borrowed
  - BLS [borrowed] 0.65 — VITB12 [Übernommener Wert] -
  - MEXT [analysed] 2.1 — VITB12 (main volume)
  - CoFID [compiled] 2 — Vitamin B12; refs: As Meat, Poultry and Game Supplement, 1995; and LGC, Poultry and game surveys, 1983-1984. Additional 
  - AFCD [computed] 0.5 — Cobalamin B12; food-level derivation: Recipe

### Biotin (1176) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 4 µg (source `literature`)
  - FCDB [echo] 6 — Biotin; src [1344] McCance and Widdowson's: The Composition of Foods, 4th revised and extended edition (1978); was borro
  - BLS [borrowed] 0.84 — BIOT [Übernommener Wert] -
  - MEXT [analysed] 4 — BIOT (main volume)
  - AFCD [computed] 2 — Biotin; food-level derivation: Recipe

### Carbohydrate (1005) — replace_suggest
- USDA zero is assumed/borrowed (deriv Z: Assumed zero (Insignificant amount or not naturally) but 1 independent(s) measure nonzero
- suggestion: 0.1 g (source `literature`)
  - FCDB [echo] 0 — Carbohydrate by difference; src [1003] Value calculated by converting various analytical data; was computed
  - BLS [computed] 0 — CHO [Formelberechnung] -
  - MEXT [analysed] 0.1 — Carbohydrate, total (main volume)
  - AFCD [computed] 0 — Available carbohydrate w/o sugar alcohols; food-level derivation: Recipe

## Verdict summary

- confirm: 26
- review: 17
- adopt_foreign: 4
- region_keep: 2
- form_defect: 1
- usda_only: 1
- replace_suggest: 1
