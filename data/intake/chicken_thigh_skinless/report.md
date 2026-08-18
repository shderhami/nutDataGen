# Intake report: chicken thigh boneless skinless raw

- generated: 2026-08-18  |  spec: `data/intake/chicken_thigh_skinless.json`
- Foundation FDC: 2646171  |  SR Legacy FDC: 173627
- category: Muscle Meat  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: price_per_unit is a placeholder — set the real grocery price before write --commit
- note: Fat frame spread is expected: FND 7.92 (2023 retail trim) vs SR 4.12 (1990s fully trimmed) vs MEXT 5.0 (no subcutaneous fat) vs AFCD 3.0 (lean flesh, 12% unanalysed trim) vs CoFID 2.8 (UK trim). Foundation describes the US retail cut being fed.
- note: Sibling of food 10001 (chicken thigh with skin raw, SR 172385 / FND 2727567).

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| FCDB:795 Chicken, flesh only, raw | Chicken, flesh only, raw — whole-bird skinless flesh (breast-dominant blend), nearest DK frame; no thigh-specific skinless entry | independent (0/43 incidental matches) |
| BLS:V413000 Chicken meat, without skin, raw | Chicken meat, without skin, raw — whole-bird flesh; BLS 4.0 rows here are heavily aggregated from frida/NO/USDA | independent (1/42 incidental matches) |
| MEXT:11224 Chicken, broiler, thigh, meat without skin, raw | broiler thigh, meat without skin, raw — EXACT match; trimmed 'without subcutaneous fat'; AA + FA volumes covered | independent (3/44 incidental matches) |
| CIQUAL:36024 Poulet, cuisse, viande crue | Poulet, cuisse, viande crue — whole-leg meat (thigh+drumstick), genuinely French, K2 measured | independent (1/27 incidental matches) |
| CIQUAL:36019 Poulet, haut de cuisse, viande crue | Poulet, haut de cuisse, viande crue — literal thigh match but suspected USDA copy (echo screen decides) | ECHO of USDA (23/27 values identical to <0.5%) |
| AFCD:F002806 Chicken, thigh, lean flesh, raw | Chicken, thigh, lean flesh, raw — EXACT match, Analysed (2019 composite, 8 samples, 5 states); lean-trim frame (12% separable fat unanalysed) | independent (0/31 incidental matches) |
| CoFID:18-289 Chicken, dark meat, raw | Chicken, dark meat, raw — thigh+drumstick flesh; underlying survey LGC 1994 nutrient analysis of chicken | independent (1/30 incidental matches) |
| IodineDB:NDB 05098 Chicken thigh, oven-roasted (skin removed)  | Chicken thigh, oven-roasted (skin removed), n=35 — COOKED frame; plausibility only for the raw row | USDA-affiliated — evidence, never independent confirmation |
| Spitze03:Chicken, dark meat, raw | Spitze 2003 p6, lit source b: 1690±370 mg/kg wet /10; the value food 10001 (thigh+skin) validated against; skin is taurine-poor so skinless >= skin-on | no USDA overlap — independence not establishable |
| Spitze03:Chicken, leg, raw | Spitze 2003 p6, lit source c: 337 (300-380) mg/kg wet /10 — 5x below source b's dark meat; known taurine-literature split, review must arbitrate | no USDA overlap — independence not establishable |
| NRC2006:Chicken, meat and skin, raw (whole carcass) | Table 13-7 pantothenic acid 9.20 mg/kg /10; n=1, whole-carcass meat+skin frame (20.3% fat) — context for the no-USDA B5 row | independent (0/2 incidental matches) |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | NRC2006 | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | 18.6125‡ | 19.66 (n=7) | 19.1 | 20.2† | 19.3° / 19.7≈ | 20.9° | 19.2986 (n=30) | — | 19 | — | — | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | NRC2006 | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 1.372 | — | 1.28† | — | — | 1.284 | — | 1.3 | — | — | **confirm** |
| Histidine (1221) | g | — | 0.587 | — | 0.589† | — | — | 0.5136 | — | 0.69 | — | — | **confirm** |
| Isoleucine (1212) | g | — | 0.939 | — | 1.03† | — | — | 0.9309 | — | 0.87 | — | — | **confirm** |
| Leucine (1213) | g | — | 1.675 | — | 1.5† | — | — | 1.4124 | — | 1.5 | — | — | **confirm** |
| Lysine (1214) | g | — | 1.855 | — | 1.81† | — | — | 1.7976 | — | 1.7 | — | — | **confirm** |
| Methionine (1215) | g | — | 0.562 | — | 0.553† | — | — | 0.5136 | — | 0.52 | — | — | **confirm** |
| Cystine (1216) | g | — | 0.23 | — | 0.201† | — | — | 0.1284 | — | 0.22 | — | — | **confirm** |
| Phenylalanine (1217) | g | — | 0.785 | — | 0.794† | — | — | 0.7383 | — | 0.75 | — | — | **confirm** |
| Tyrosine (1218) | g | — | 0.739 | — | 0.666† | — | — | 0.6099 | — | 0.64 | — | — | **confirm** |
| Threonine (1211) | g | — | 0.93 | — | 0.854† | — | — | 0.8025 | — | 0.85 | — | — | **confirm** |
| Tryptophan (1210) | g | — | 0.222 | 0.19 | 0.23† | — | — | 0.20865 | — | 0.24 | — | — | **confirm** |
| Valine (1219) | g | — | 0.956 | — | 1.06† | — | — | 1.0593 | — | 0.92 | — | — | **confirm** |
| Taurine (1234) | mg | — | — | — | — | — | — | — | — | — | — | 169 (n=6) / 33.7 (n=12) | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | NRC2006 | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | 7.916 (n=8) | 4.12 (n=7) | 3 | 5.6† | 4.05° / 4.12≈ | 2.8° | 5.63471 (n=34) | — | 5 | — | — | **review** |

## Fatty Acid

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | NRC2006 | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 0.748 (n=5) | 0.43 | 1.203† | 0.62° / 0.74≈ | 0.44° | 1.20305 (n=4) | — | 0.52 | — | — | **confirm** |
| Arachidonic acid (1271) | g | — | 0.09 (n=5) | 0.02268 | — | — | 0.01° | — | — | 0.089 | — | — | **confirm** |
| Alpha-linolenic acid (1270) | g | — | 0.036 (n=5) | 0.04 | 0.218† | 0.025° / 0.03≈ | 0.07° | 0.217942 (n=4) | — | 0.018 | — | — | **confirm** |
| EPA (1278) | g | — | 0.002 (n=5) | 0 | 0.01† | 0.008° / 0.002≈ | 0° | 0.00998587 (n=4) | — | 0.002 | — | — | **confirm** |
| DHA (1272) | g | — | 0.007 (n=5) | 0.00284 | 0.031† | 0.028° / 0.007≈ | 0.01° | 0.0307066 (n=4) | — | 0.011 | — | — | **confirm** |
| Fatty acids, total polyunsaturated (1293) | g | 1.42 (n=8) | 0.94‡ | 0.52 | 1.51‡ | — | 0.6° | 1.50637‡ | — | 0.71 | — | — | **review** |
| DPA 22:5 n-3 (1280) | g | — | 0.008 (n=5) | 0.00567 | 0.021† | — | 0.01° | 0.02122 (n=4) | — | 0.01 | — | — | **confirm** |

## Mineral

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | NRC2006 | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | 5.65 (n=8) | 7 (n=6) | 6 | 11† | 10.3° / 7≈ | 7° | 11 (n=4) | — | 5 | — | — | **confirm** |
| Phosphorus (1091) | mg | 178.3 (n=8) | 185 (n=6) | 180 | 188† | 173° / 185≈ | 110° | 173† (n=24) | — | 190 | — | — | **confirm** |
| Potassium (1092) | mg | 271.8 (n=8) | 242 (n=6) | 320 | 280† | 229° / 242≈ | 390° | 281? (n=4) | — | 320 | — | — | **confirm** |
| Sodium (1093) | mg | 62.33 (n=8) | 95 (n=6) | 64 | 79† | 92° / 95≈ | 90° | 76? (n=4) | — | 69 | — | — | **confirm** |
| Chloride (1088) | mg | — | — | 69 | 85† | — | 110° | — | — | — | — | — | **adopt_foreign** |
| Magnesium (1090) | mg | 21.8 (n=8) | 23 (n=6) | 24 | 25† | 22.3° / 23≈ | 24° | 24.2174 (n=46) | — | 24 | — | — | **confirm** |
| Iron (1089) | mg | 0.6018 (n=8) | 0.81 (n=6) | 0.56 | 0.7† | 0.99° / 0.81≈ | 0.8° | 0.578261 (n=46) | — | 0.6 | — | — | **confirm** |
| Copper (1098) | mg | 0.04235 (n=8) | 0.062 (n=6) | 0.042 | 0.04† | 0.061° / 0.062≈ | 0.02° | 0.036 (n=25) | — | 0.04 | — | — | **confirm** |
| Manganese (1101) | mg | 0 (n=8) | 0.013 (n=6) | 0.011 | 0.016† | 0.019° / 0.013≈ | 0.01° | 0.014 (n=4) | — | 0.01 | — | — | **confirm** |
| Zinc (1095) | mg | 1.348 (n=8) | 1.58 (n=6) | 1.4 | 1.26† | 1.8° / 1.58≈ | 1.7° | 0.97087 (n=46) | — | 1.8 | — | — | **confirm** |
| Iodine (1100) | µg | — | — | 0 | 1† | 2° | 6° | 0.4 (n=5) | 0.9 (n=35) | 0 | — | — | **adopt_foreign** |
| Selenium (1103) | µg | — | 22.9 (n=5) | 21 | — | — | 14° | 12.4 (n=28) | — | 19 | 14° | — | **confirm** |

## Vitamin

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | NRC2006 | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | — | 23.31 (n=1) | 43.29 | 53.28† | 55.611° / 23.31≈ | 66.6° | 53.28† | — | 53.28 | — | — | **region_keep** |
| Vitamin D (1110) | IU | — | 1 (n=1) | 52.4† | 4‡ | 0° / 0≈ | 4° | 8‡ | — | 8 | — | — | **confirm** |
| Vitamin E (1109) | IU | — | 0.2682 (n=1) | 2.086 | 0.894† | 0.298° / 0.2682≈ | 0.2533° | 0.4321 (n=23) | — | 0.894 | — | — | **confirm** |
| Vitamin K (1185) | µg | — | 2.9† | — | 5.83‡ | 36.83° / 2.9≈ | 0.05° | 0‡ | — | 23 | — | — | **form_defect** |
| Thiamin (1165) | mg | — | 0.088 (n=5) | 0.12 | 0.12† | 0.079° / 0.088≈ | 0.14° | 0.096 (n=20) | — | 0.10644 | — | — | **confirm** |
| Riboflavin (1166) | mg | — | 0.196 (n=5) | 0.12 | 0.15† | 0.18° / 0.2≈ | 0.22° | 0.158 (n=20) | — | 0.19 | — | — | **confirm** |
| Niacin (1167) | mg | — | 5.557 (n=5) | 5 | 7.8† | 5.9° / 5.56≈ | 5.6° | 8.239† (n=16) | — | 5.5 | — | — | **confirm** |
| Pantothenic acid (1170) | mg | — | — | 0.95 | 1.06† | 1.2° / 1.23≈ | 1.09° | 1.058† | — | 1.06 | 0.92° | — | **adopt_foreign** |
| Pyridoxine (1175) | mg | — | 0.451 (n=5) | 0.24 | 0.42† | 0.35° / 0.45≈ | 0.28° | 0.39 (n=20) | — | 0.31 | — | — | **confirm** |
| Folic acid (1177) | µg | — | 4† | 32 | 11† | 7.67° / 4≈ | 9° | 21.1667 (n=24) | — | 10 | 6° | — | **review** |
| Cobalamin (1178) | µg | — | 0.61 (n=5) | 0.4 | 0.3† | 0.42° / 0.61≈ | 1° | 0.42 (n=20) | — | 0.3 | — | — | **confirm** |
| Biotin (1176) | µg | — | — | 3.7 | 0.84† | — | 3° | 2† | — | 3.6 | — | — | **adopt_foreign** |
| Choline (1180) | mg | — | 53.6? | — | — | — | — | 65.7† (n=1) | — | — | — | — | **usda_only** |

## Other

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | NRC2006 | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 121‡ | 104.207‡ | 131‡ | 114‡ / 116≈ | 109° | 127.907‡ | — | 127‡ | — | — | **confirm** |
| Water (1051) | g | 72.92 (n=8) | 76.22 (n=7) | 77.2 | 75† | 76° / 76.2≈ | 75.8° | 74.0667 (n=30) | — | 76.1 | — | — | **confirm** |
| Ash (1007) | g | 0.9575 (n=8) | 0.95 (n=7) | 1 | 1† | 0.98° / 0.95≈ | — | 1 (n=30) | — | 1 | — | — | **confirm** |
| Crude Fiber (1079) | g | — | 0† | 0 | 0‡ | 0° / 0≈ | 0° | 0† | — | 0~ | — | — | **confirm** |
| Carbohydrate (1005) | g | 0‡ | 0† | 0 | 0‡ | 0° / 0≈ | 0° | 0‡ | — | 0 | — | — | **confirm** |

## Needs attention (everything not confirm/usda_only)

### Taurine (1234) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 33.7 mg (source `literature`)
  - Spitze03 [analysed] 169 — Spitze 2003 p6, lit source b: 1690±370 mg/kg wet /10; the value food 10001 (thigh+skin) validated against; skin is tauri
  - Spitze03 [analysed] 33.7 — Spitze 2003 p6, lit source c: 337 (300-380) mg/kg wet /10 — 5x below source b's dark meat; known taurine-literature spli

### Total Fat (1004) — review
- all 5 independent(s) differ >±20% from foundation 7.916: FCDB 5.63471 (n=34), MEXT 5, CIQUAL 4.05, AFCD 3, CoFID 2.8
- suggestion: 7.916 g (source `foundation`)
  - FCDB [analysed] 5.63471 — Fat; src [1818, 2089, 1840] Determination of fat and fatty acid distribution (1992) | Nutrients in whole chickens (2012)
  - BLS [borrowed] 5.6 — FAT [Nährstoffdatenbank] National Food Institute; Food data (frida.fooddata.dk), version 4.2; 2022
  - MEXT [analysed] 5 — Lipid (main volume)
  - CIQUAL [compiled] 4.05 — Lipides
  - CIQUAL [echo] 4.12 — Lipides; was compiled
  - AFCD [analysed] 3 — Fat, total; food-level derivation: Analysed
  - CoFID [compiled] 2.8 — Fat; refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolton-Smith et al Br

### Fatty acids, total polyunsaturated (1293) — review
- all 3 independent(s) differ >±20% from foundation 1.42: MEXT 0.71, AFCD 0.52, CoFID 0.6
- suggestion: 1.42 g (source `foundation`)
  - FCDB [computed] 1.50637 — Sum polyunsaturated fatty acids; src [1003] Value calculated by converting various analytical data
  - BLS [computed] 1.51 — FAPU [Formelberechnung] -
  - MEXT [analysed] 0.71 — FAPU (FA volume, per 100 g EP)
  - AFCD [analysed] 0.52 — Total PUFA, equated; food-level derivation: Analysed
  - CoFID [compiled] 0.6 — Poly FA /100g food; refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolton

### Chloride (1088) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 69 mg (source `literature`)
  - BLS [borrowed] 85 — CLD [Übernommener Wert] -
  - AFCD [analysed] 69 — Chloride; food-level derivation: Analysed
  - CoFID [compiled] 110 — Chloride; refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolton-Smith et 

### Iodine (1100) — adopt_foreign
- no USDA value; 6 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 0.9 µg (source `literature`)
  - FCDB [analysed] 0.4 — Iodine; src [1055] The iodine content of Danish food (1982)
  - BLS [borrowed] 1 — ID [Aggregation] National Food Institute; Food data (frida.fooddata.dk), version 4.2; 2022#Norweg
  - MEXT [analysed] 0 — ID (main volume)
  - CIQUAL [compiled] 2 — Iode
  - AFCD [analysed] 0 — Iodine; food-level derivation: Analysed
  - CoFID [compiled] 6 — Iodine; refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolton-Smith et al
  - IodineDB [analysed] 0.9 — Iodine DB R4; SD=1.8

### Vitamin A (1106) — region_keep
- region-sensitive; foreign cluster differs: MEXT 53.28, CIQUAL 55.611, AFCD 43.29, CoFID 66.6 — US mean kept unless defective
- suggestion: 23.31 IU (source `sr_legacy`)
  - FCDB [borrowed] 53.28 — Retinol; src [1342] USDA Table for Standard Reference (1976)
  - BLS [borrowed] 53.28 — RETOL [Nährstoffdatenbank] National Food Institute, Food data (frida.fooddata.dk), version 5.2, May 2024
  - MEXT [analysed] 53.28 — RETOL (main volume)
  - CIQUAL [compiled] 55.611 — Rétinol
  - CIQUAL [echo] 23.31 — Rétinol; was compiled
  - AFCD [analysed] 43.29 — Retinol (preformed); food-level derivation: Analysed
  - CoFID [compiled] 66.6 — Retinol; refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolton-Smith et a

### Vitamin K (1185) — form_defect
- USDA K row is K1-only (2.9 µg); menaquinone-inclusive tables read ~29.915 µg
- anchor tie-broken — review must arbitrate
- suggestion: 23 µg (source `literature`)
  - FCDB [computed] 0 — Vitamin K; src [1003] Value calculated by converting various analytical data
  - BLS [computed] 5.83 — VITK [Formelberechnung] -; VITK1=0µg, VITK2=5.83µg
  - MEXT [analysed] 23 — VITK (main volume); menaquinone-inclusive total K
  - CIQUAL [compiled] 36.83 — Vitamine K1+K2 total-K; K1=2.53, K2=34.3
  - CIQUAL [echo] 2.9 — Vitamine K1+K2 total-K; K1=2.9, K2 n/a; was compiled
  - CoFID [compiled] 0.05 — Vitamin K1 (K1 only); refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolt

### Pantothenic acid (1170) — adopt_foreign
- no USDA value; 5 measured source(s) available
- suggestion: 1.06 mg (source `literature`)
  - FCDB [borrowed] 1.058 — Pantothenic acid; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - BLS [borrowed] 1.06 — PANTAC [Nährstoffdatenbank] US Department of Agriculture, Agricultural Research Service; USDA National Nutri
  - MEXT [analysed] 1.06 — PANTAC (main volume)
  - CIQUAL [compiled] 1.2 — B5
  - CIQUAL [echo] 1.23 — B5; was compiled
  - AFCD [analysed] 0.95 — Pantothenic acid; food-level derivation: Analysed
  - CoFID [compiled] 1.09 — Pantothenate; refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolton-Smith
  - NRC2006 [compiled] 0.92 — Table 13-7 pantothenic acid 9.20 mg/kg /10; n=1, whole-carcass meat+skin frame (20.3% fat) — context for the no-USDA B5 

### Folic acid (1177) — review
- all 6 independent(s) differ >±20% from sr_legacy 4: FCDB 21.1667 (n=24), MEXT 10, CIQUAL 7.67, AFCD 32, CoFID 9, NRC2006 6
- suggestion: 4 µg (source `sr_legacy`)
  - FCDB [analysed] 21.1667 — Folate; src [1840, 1845] Food Monitoring System for Nutrients. Meat, Second Cycle (1994) | Folacin content in foods (199
  - BLS [borrowed] 11 — FOLFD [Aggregation] Norwegian Food Safety Authority; Norwegian Food Composition Database; 2021#Natio
  - MEXT [analysed] 10 — FOL (main volume)
  - CIQUAL [compiled] 7.67 — Folates totaux
  - CIQUAL [echo] 4 — Folates totaux; was compiled
  - AFCD [analysed] 32 — Folate, natural; food-level derivation: Analysed
  - CoFID [compiled] 9 — Folate; refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolton-Smith et al
  - NRC2006 [compiled] 6 — Table 13-7 folate 0.06 mg/kg /10; n=1 meat+skin frame — supports the low side of the folate spread

### Biotin (1176) — adopt_foreign
- no USDA value; 3 measured source(s) available
- suggestion: 3.6 µg (source `literature`)
  - FCDB [borrowed] 2 — Biotin; src [1344] McCance and Widdowson's: The Composition of Foods, 4th revised and extended edition (1978)
  - BLS [borrowed] 0.84 — BIOT [Übernommener Wert] -
  - MEXT [analysed] 3.6 — BIOT (main volume)
  - AFCD [analysed] 3.7 — Biotin; food-level derivation: Analysed
  - CoFID [compiled] 3 — Biotin; refs: Reviewed 2013. LGC, Nutrient analysis of chicken and turkey, 1994-1995; vitamin K1 from Bolton-Smith et al

## Verdict summary

- confirm: 41
- adopt_foreign: 5
- review: 3
- region_keep: 1
- form_defect: 1
- usda_only: 1
