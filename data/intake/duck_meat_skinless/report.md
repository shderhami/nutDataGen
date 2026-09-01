# Intake report: duck meat only raw

- generated: 2026-09-01  |  spec: `data/intake/duck_meat_skinless.json`
- Foundation FDC: —  |  SR Legacy FDC: 172410
- category: Muscle Meat  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: PRICE: $4.40/lb Costco whole Pekin sticker (Shahab 2026-09-01) / 453.592 = 0.0097/g as-sold, / 0.58 assumed boneless-edible yield = 0.0167/g. SAME price as the sibling (whole-bird cost allocates uniformly per edible gram since everything edible is used). Yield assumption adjustable - CONFIRM at approval.
- note: SIBLING PAIR (option A, approved 2026-09-01): this is the SKINLESS component. Sibling spec = duck_meat_skin.json (SR 172408, 'duck meat and skin raw'). DO NOT confuse: this entry is SR 172410, fat 5.95, kcal 135. Recipes blend the two (e.g., 85:15 -> Met ~2.6/1000 kcal); this entry ALONE reads Met 3.66/1000 kcal (above the 3.25 ceiling - by design, the skin sibling is the diluent).
- note: WHY TWO ENTRIES: derived-skin option was quantitatively refuted (subtraction gives negative protein/Met/B6 and >100% mass closure at all plausible skin fractions - the two SR composites are independent sample sets); MEXT's own meat/skin/composite triple proves linear blending of measured frames is exact (f=0.405, rms 0.3%). Chat analysis 2026-09-01.
- note: FRAME: whole-bird skinless flesh composite ('domesticated' USDA = White Pekin, the Costco breed). Customer: skin the whole bird; giblets/neck are NOT part of this entry (weigh separately; species-specific organ entries may come later).
- note: Panel: 92 nutrients, full 12/12 AA, vit D/E/K/A + choline native; only Cl/I/biotin/taurine gaps.
- note: POULTRY DOCTRINE expectations: vit K form_defect WILL fire (SR K1-only vs MEXT total_k; duck is dark meat, MK-4-rich - thigh precedent adopted MEXT totals 20-23); taurine cross-species from Spitze chicken dark meat 169 (duck is all-dark oxidative muscle).
- note: Internationals: 5 frame-matched adapters (no CIQUAL raw duck meat - only foie gras; verified 2026-09-01; no TDS duck in iodine_db).

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| FCDB:728 Duck, flesh only, raw | Duck, flesh only, raw - Danish; check for stats (cv_intl FOOD_MAP candidate) | ECHO of USDA (19/41 values identical to <0.5%) |
| BLS:V463000 Duck meat, without skin, raw | Duck meat, without skin, raw - German; echo screen decides (BLS poultry sometimes analytical, unlike its lamb organs) | ECHO of USDA (21/40 values identical to <0.5%) |
| MEXT:11247 Duck, domesticated, meat without skin, raw | Duck, domesticated, meat without skin, raw - Japanese analytical; total-K carrier for the menaquinone fix | independent (2/42 incidental matches) |
| CoFID:18-489 Duck, meat only, raw | Duck, meat only, raw - UK; chloride + biotin carrier; frame-exact | ECHO of USDA (10/23 values identical to <0.5%) |
| AFCD:F003632 Duck, lean flesh, raw | Duck, lean flesh, raw - Australian; check Derivation flag for borrows | independent (4/38 incidental matches) |
| Spitze03:Chicken dark meat (poultry dark-muscle proxy; no duck taurine exists locally) | No duck taurine measurement in any local resource. Duck is all-dark oxidative muscle -> Spitze chicken dark meat 169+/-37 (n=6), the same anchor validated for thighs 10001/10048. Cross-species, SPARSE-EVIDENCE flag | no USDA overlap — independence not establishable |
| PoultryFamily:Poultry muscle iodine (TDS chicken thigh/breast both ~1) | No duck iodine in TDS or any adapter. Poultry muscle family = 1 µg (10001/10048/10054 all 1, US TDS-anchored). Cross-species, SPARSE-EVIDENCE flag | no USDA overlap — independence not establishable |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | — | 18.28 (n=13) | 17.8 | 19≈ | 19.7≈ | 18.2812≈ (n=13) | 20.1 | — | — | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 1.166? | 1.163 | 1.17≈ | — | 1.17≈ | 1.3 | — | — | **confirm** |
| Histidine (1221) | g | — | 0.483? | 0.527 | 0.483≈ | — | 0.49725≈ | 0.69 | — | — | **confirm** |
| Isoleucine (1212) | g | — | 0.939? | 0.992 | 0.939≈ | — | 0.936≈ | 0.94 | — | — | **confirm** |
| Leucine (1213) | g | — | 1.544? | 1.476 | 1.54≈ | — | 1.55025≈ | 1.6 | — | — | **confirm** |
| Lysine (1214) | g | — | 1.564? | 1.465 | 1.56≈ | — | 1.55025≈ | 1.8 | — | — | **confirm** |
| Methionine (1215) | g | — | 0.494? | 0.496 | 0.494≈ | — | 0.49725≈ | 0.54 | — | — | **confirm** |
| Cystine (1216) | g | — | 0.281? | 0.222 | 0.281≈ | — | 0.2808≈ | 0.24 | — | — | **confirm** |
| Phenylalanine (1217) | g | — | 0.766? | 0.784 | 0.766≈ | — | 0.7605≈ | 0.82 | — | — | **confirm** |
| Tyrosine (1218) | g | — | 0.696? | 0.658 | 0.696≈ | — | 0.702≈ | 0.72 | — | — | **confirm** |
| Threonine (1211) | g | — | 0.781? | 0.972 | 0.781≈ | — | 0.78975≈ | 0.92 | — | — | **confirm** |
| Tryptophan (1210) | g | — | 0.254? | 0.225 | 0.253≈ | — | 0.254475≈ | 0.26 | — | — | **confirm** |
| Valine (1219) | g | — | 0.956? | 0.966 | 0.956≈ | — | 0.96525≈ | 0.99 | — | — | **confirm** |
| Taurine (1234) | mg | — | — | — | — | — | — | — | — | 169~ | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | — | 5.95 (n=13) | 5.5 | 5.1≈ | 6.5≈ | 5.115≈ (n=4) | 2.2 | — | — | **confirm** |

## Fatty Acid

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 0.67 (n=1) | 0.63 | 0.599≈ | — | 0.598598≈ (n=4) | 0.3 | — | — | **confirm** |
| Arachidonic acid (1271) | g | — | 0? | 0.07798 | — | — | — | 0.074 | — | — | **review** |
| Alpha-linolenic acid (1270) | g | — | 0.08 (n=1) | 0.03 | 0.105≈ | — | 0.104564≈ (n=4) | 0.015 | — | — | **review** |
| EPA (1278) | g | — | 0? | 0 | 0.004≈ | — | 0.00423337≈ (n=4) | 0.002 | — | — | **confirm** |
| DHA (1272) | g | — | 0? | 0.0052 | 0.018≈ | — | 0.0182035≈ (n=4) | 0.003 | — | — | **confirm** |
| Fatty acids, total polyunsaturated (1293) | g | — | 0.75? | 0.76 | 0.775≈ | 1≈ | 0.877789≈ | 0.44 | — | — | **confirm** |
| DPA 22:5 n-3 (1280) | g | — | 0? | 0 | 0.016≈ | — | 0.0158751≈ (n=4) | 0.007 | — | — | **confirm** |

## Mineral

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | — | 11 (n=2) | 7 | 12≈ | 12≈ | 11≈ (n=2) | 5 | — | — | **review** |
| Phosphorus (1091) | mg | — | 203 (n=2) | 170 | 202≈ | 200≈ | 203≈ (n=2) | 230 | — | — | **confirm** |
| Potassium (1092) | mg | — | 271 (n=3) | 270 | 286≈ | 290≈ | 297≈ (n=3) | 360 | — | — | **confirm** |
| Sodium (1093) | mg | — | 74 (n=5) | 91 | 90≈ | 110≈ | 86≈ (n=3) | 84 | — | — | **confirm** |
| Chloride (1088) | mg | — | — | 60 | 98≈ | 98≈ | — | — | — | — | **adopt_foreign** |
| Magnesium (1090) | mg | — | 19 (n=1) | 19 | 20≈ | 19≈ | 22≈ (n=3) | 26 | — | — | **confirm** |
| Iron (1089) | mg | — | 2.4 (n=1) | 1.8 | 2≈ | 2.4≈ | 1.2≈ (n=2) | 2.4 | — | — | **confirm** |
| Copper (1098) | mg | — | 0.253 (n=282) | 0.25 | 0.24≈ | 0.34≈ | 0.14≈ (n=5) | 0.31 | — | — | **confirm** |
| Manganese (1101) | mg | — | 0.019? | 0 | 0.019≈ | 0≈ | 0.019≈ | 0.02 | — | — | **confirm** |
| Zinc (1095) | mg | — | 1.9 (n=1) | 2 | 1.7≈ | 1.9≈ | 1.35≈ (n=5) | 2.3 | — | — | **confirm** |
| Iodine (1100) | µg | — | — | 0 | 1.2≈ | — | 1.2≈ (n=3) | 11 | 1~ | — | **adopt_foreign** |
| Selenium (1103) | µg | — | 13.9† | 25 | — | 22≈ | 24≈ (n=5) | 21 | — | — | **region_keep** |

## Vitamin

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | — | 79.92‡ | 59.94 | 79.92≈ | 79.92≈ | 79.92≈ | 29.97 | — | — | **region_keep** |
| Vitamin D (1110) | IU | — | 3† | 37.6† | 22≈ | — | 22≈ (n=1) | 16 | — | — | **region_keep** |
| Vitamin E (1109) | IU | — | 1.043? | 0.596 | 0.596≈ | 0.0298≈ | 0≈ | 0.596 | — | — | **confirm** |
| Vitamin K (1185) | µg | — | 2.8† | — | 5.5≈ | — | 0≈ | 22 | — | — | **form_defect** |
| Thiamin (1165) | mg | — | 0.36 (n=1) | 0.32 | 0.36≈ | 0.36≈ | 0.36≈ (n=1) | 0.40802 | — | — | **confirm** |
| Riboflavin (1166) | mg | — | 0.45 (n=1) | 0.2 | 0.45≈ | 0.45≈ | 0.45≈ (n=1) | 0.41 | — | — | **confirm** |
| Niacin (1167) | mg | — | 5.3 (n=1) | 4.5 | 5.3≈ | 5.3≈ | 5.3≈ (n=1) | 7.9 | — | — | **confirm** |
| Pantothenic acid (1170) | mg | — | 1.6 (n=1) | 1.4 | 1.6≈ | 1.6≈ | 1.6≈ (n=1) | 1.83 | — | — | **confirm** |
| Pyridoxine (1175) | mg | — | 0.34 (n=1) | 0.1 | 0.34≈ | 0.34≈ | 0.34≈ (n=1) | 0.54 | — | — | **review** |
| Folic acid (1177) | µg | — | 25 (n=1) | 0† | 33≈ | 25≈ | 48≈ (n=6) | 14 | — | — | **review** |
| Cobalamin (1178) | µg | — | 0.4 (n=1) | 0.7 | 2≈ | 3≈ | 0.4≈ (n=1) | 3 | — | — | **confirm** |
| Biotin (1176) | µg | — | — | 2.9 | 6≈ | 6≈ | — | 5.6 | — | — | **adopt_foreign** |
| Choline (1180) | mg | — | 53.6† | — | — | — | 53.6≈ (n=1) | — | — | — | **usda_only** |

## Other

| nutrient | unit | FND | SR | AFCD | BLS | CoFID | FCDB | MEXT | PoultryFamily | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 135‡ | 120.937‡ | 122≈ | 137≈ | 126.255≈ | 106‡ | — | — | **usda_only** |
| Water (1051) | g | — | 73.77 (n=13) | 75.1 | 74.3≈ | 74.8≈ | 73.77≈ (n=13) | 77.2 | — | — | **confirm** |
| Ash (1007) | g | — | 1.06 (n=13) | 0.9 | 1.06≈ | — | 1.06≈ (n=13) | 1.1 | — | — | **confirm** |
| Crude Fiber (1079) | g | — | 0† | 0 | 0≈ | 0≈ | 0≈ | 0~ | — | — | **confirm** |
| Carbohydrate (1005) | g | — | 0.94‡ | 0 | 0≈ | — | 1.77375≈ | 0.2 | — | — | **review** |

## Needs attention (contested rows + detection-limit context)

### Taurine (1234) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 169 mg (source `literature`)
  - Spitze03 [estimated] 169 — No duck taurine measurement in any local resource. Duck is all-dark oxidative muscle -> Spitze chicken dark meat 169+/-3

### Arachidonic acid (1271) — review
- all 2 independent(s) differ >±20% from sr_legacy 0: MEXT 0.074, AFCD 0.07798
- suggestion: 0 g (source `sr_legacy`)
  - MEXT [analysed] 0.074 — F20D4N6 (FA volume, per 100 g EP)
  - AFCD [analysed] 0.07798 — C20:4w6; food-level derivation: Analysed

### Alpha-linolenic acid (1270) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.08: MEXT 0.015, AFCD 0.03
- suggestion: 0.08 g (source `sr_legacy`)
  - FCDB [echo] 0.104564 — C18:3,n-3; src [1818] Determination of fat and fatty acid distribution (1992); was analysed
  - BLS [echo] 0.105 — F18:3CN3 [Nährstoffdatenbank] National Food Institute; Food data (frida.fooddata.dk), version 4.2; 2022; was borrowed
  - MEXT [analysed] 0.015 — F18D3N3 (FA volume, per 100 g EP)
  - AFCD [analysed] 0.03 — C18:3w3; food-level derivation: Analysed

### Calcium (1087) — review
- all 2 independent(s) differ >±20% from sr_legacy 11: MEXT 5, AFCD 7
- suggestion: 11 mg (source `sr_legacy`)
  - FCDB [echo] 11 — Calcium; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007); was borrowed
  - BLS [echo] 12 — CA [Aggregation] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - MEXT [analysed] 5 — CA (main volume)
  - CoFID [echo] 12 — Calcium; refs: Reviewed 2013. LGC, Poultry and game surveys, 1983-1984; and RHM, Fatty acids in foods, 1993. Selenium fr
  - AFCD [analysed] 7 — Calcium; food-level derivation: Analysed

### Chloride (1088) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 60 mg (source `literature`)
  - BLS [echo] 98 — CLD [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - CoFID [echo] 98 — Chloride; refs: Reviewed 2013. LGC, Poultry and game surveys, 1983-1984; and RHM, Fatty acids in foods, 1993. Selenium f
  - AFCD [analysed] 60 — Chloride; food-level derivation: Analysed

### Iodine (1100) — adopt_foreign
- no USDA value; 3 measured source(s) available
- suggestion: 1 µg (source `literature`)
  - FCDB [echo] 1.2 — Iodine; src [1055] The iodine content of Danish food (1982); was analysed
  - BLS [echo] 1.2 — ID [Nährstoffdatenbank] National Food Institute; Food data (frida.fooddata.dk), version 4.2; 2022; was borrowed
  - MEXT [analysed] 11 — ID (main volume)
  - AFCD [analysed] 0 — Iodine; food-level derivation: Analysed
  - PoultryFamily [estimated] 1 — No duck iodine in TDS or any adapter. Poultry muscle family = 1 µg (10001/10048/10054 all 1, US TDS-anchored). Cross-spe

### Selenium (1103) — region_keep
- region-sensitive; foreign cluster differs: MEXT 21, AFCD 25 — US mean kept unless defective
- suggestion: 13.9 µg (source `sr_legacy`)
  - FCDB [echo] 24 — Selenium; src [1102] Trace Elements in Meat and Organs from Danish Slaughtered Animals, 1972-82 (1986); was analysed
  - MEXT [analysed] 21 — SE (main volume)
  - CoFID [echo] 22 — Selenium; refs: Reviewed 2013. LGC, Poultry and game surveys, 1983-1984; and RHM, Fatty acids in foods, 1993. Selenium f
  - AFCD [analysed] 25 — Selenium; food-level derivation: Analysed

### Vitamin A (1106) — region_keep
- region-sensitive; foreign cluster differs: MEXT 29.97, AFCD 59.94 — US mean kept unless defective
- suggestion: 79.92 IU (source `sr_legacy`)
  - FCDB [echo] 79.92 — Retinol; src [1342] USDA Table for Standard Reference (1976); was borrowed
  - BLS [echo] 79.92 — RETOL [Aggregation] National Food Institute, Food data (frida.fooddata.dk), version 5.2, May 2024#Co; was borrowed
  - MEXT [analysed] 29.97 — RETOL (main volume)
  - CoFID [echo] 79.92 — Retinol; refs: Reviewed 2013. LGC, Poultry and game surveys, 1983-1984; and RHM, Fatty acids in foods, 1993. Selenium fr
  - AFCD [analysed] 59.94 — Retinol (preformed); food-level derivation: Analysed

### Vitamin D (1110) — region_keep
- region-sensitive; foreign cluster differs: MEXT 16 — US mean kept unless defective
- suggestion: 3 IU (source `sr_legacy`)
  - FCDB [echo] 22 — Vitamin D; src [2137] Ciqual French food composition table (2017); was borrowed
  - BLS [echo] 22 — VITD [Formelberechnung] -; was computed
  - MEXT [analysed] 16 — VITD (main volume)
  - AFCD [borrowed] 37.6 — Vitamin D3 equivalents; food-level derivation: Analysed; sampling: Vitamin D, folate, I and trans fat were imputed from 

### Vitamin K (1185) — form_defect
- USDA K row is K1-only (2.8 µg); menaquinone-inclusive tables read ~22 µg
- suggestion: 22 µg (source `literature`)
  - FCDB [echo] 0 — Vitamin K; src [1003] Value calculated by converting various analytical data; was computed
  - BLS [echo] 5.5 — VITK [Formelberechnung] -; VITK1=1.9µg, VITK2=3.6µg; was computed
  - MEXT [analysed] 22 — VITK (main volume); menaquinone-inclusive total K

### Pyridoxine (1175) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.34: MEXT 0.54, AFCD 0.1
- suggestion: 0.34 mg (source `sr_legacy`)
  - FCDB [echo] 0.34 — Vitamin B6; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007); was borrowed
  - BLS [echo] 0.34 — VITB6 [Aggregation] US Department of Agriculture, Agricultural Research Service; USDA National Nutri; was borrowed
  - MEXT [analysed] 0.54 — VITB6A (main volume)
  - CoFID [echo] 0.34 — Vitamin B6; refs: Reviewed 2013. LGC, Poultry and game surveys, 1983-1984; and RHM, Fatty acids in foods, 1993. Selenium
  - AFCD [analysed] 0.1 — Pyridoxine B6; food-level derivation: Analysed

### Folic acid (1177) — review
- all 1 independent(s) differ >±20% from sr_legacy 25: MEXT 14
- suggestion: 25 µg (source `sr_legacy`)
  - FCDB [echo] 48 — Folate; src [1803] Folacin content in foods (1993); was analysed
  - BLS [echo] 33 — FOLFD [Aggregation] National Food Institute; Food data (frida.fooddata.dk), version 4.2; 2022#Public; was borrowed
  - MEXT [analysed] 14 — FOL (main volume)
  - CoFID [echo] 25 — Folate; refs: Reviewed 2013. LGC, Poultry and game surveys, 1983-1984; and RHM, Fatty acids in foods, 1993. Selenium fro
  - AFCD [borrowed] 0 — Folate, natural; food-level derivation: Analysed; sampling: Vitamin D, folate, I and trans fat were imputed from chicken

### Biotin (1176) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 2.9 µg (source `literature`)
  - BLS [echo] 6 — BIOT [Nährstoffdatenbank] Public Health England; McCance and Widdowson's The Composition of Foods Integrat; was borrowed
  - MEXT [analysed] 5.6 — BIOT (main volume)
  - CoFID [echo] 6 — Biotin; refs: Reviewed 2013. LGC, Poultry and game surveys, 1983-1984; and RHM, Fatty acids in foods, 1993. Selenium fro
  - AFCD [analysed] 2.9 — Biotin; food-level derivation: Analysed

### Carbohydrate (1005) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.94: MEXT 0.2, AFCD 0
- suggestion: 0.94 g (source `sr_legacy`)
  - FCDB [echo] 1.77375 — Carbohydrate by difference; src [1003] Value calculated by converting various analytical data; was computed
  - BLS [echo] 0 — CHO [Formelberechnung] -; was computed
  - MEXT [analysed] 0.2 — Carbohydrate, total (main volume)
  - AFCD [analysed] 0 — Available carbohydrate w/o sugar alcohols; food-level derivation: Analysed

## Verdict summary

- confirm: 36
- review: 6
- adopt_foreign: 4
- region_keep: 3
- usda_only: 2
- form_defect: 1
