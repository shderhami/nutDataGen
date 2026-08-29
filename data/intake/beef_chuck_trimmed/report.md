# Intake report: beef chuck under blade trimmed raw

- generated: 2026-08-29  |  spec: `data/intake/beef_chuck_trimmed.json`
- Foundation FDC: —  |  SR Legacy FDC: 170814
- category: Muscle Meat  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: price_per_unit 0.0245/g confirmed by Shahab 2026-08-29 (trimmed-mass basis: Wegmans Choice chuck roast $9.99/lb with ~8-12% external-trim discard -> $0.0242-0.0250/g band).
- note: FRAME: SR 170814 'under blade pot roast or steak, boneless, separable lean and fat, trimmed to 0" fat, choice' = a boneless chuck roast with ALL EXTERNAL fat removed, seam fat and marbling left in (13.93 g fat/100 g). Customer instruction: buy boneless chuck roast, trim off all external/surface fat, do NOT dissect seam fat. Chosen 2026-08-29 with Shahab as the mid-fat beef for raw recipes: Met 2.69 g/1000 kcal (ceiling 3.25), fat 69 g/1000 kcal.
- note: WARNING from the cut survey: fully-trimmed chuck frames ('separable lean only' <9% fat, incl. 'chuck for stew' at Met 4.9-5.2/1000 kcal) violate the methionine ceiling - do not swap to a leaner frame without redoing that math.
- note: SR-only food: the only Foundation chuck aggregate (2646174, 17.8% fat as-sold retail) frame-mismatches this trimmed cut; no lean-chuck Foundation entry exists. Precedent: beef heart 10050 was SR-only.
- note: Evidence tier: SR 170814 is from the 2011-2013 national chuck study - 107 nutrients, fat n=24, full FA panel, vitamin D and choline measured (richer than sibling 10035's handbook-era 168672, n=0). Grade 'choice' matches Wegmans stock.
- note: Siblings for anchors: 10035 chuck roast untrimmed (validated 2026-08-17 - vit K 1.6, vit D 12 IU, iodine 2.8, chloride 52, biotin 2.8, taurine 40), 10021 top round, 10050 beef heart. Expect this cut's values to sit between 10035 and lean cuts on fat-tracking rows.
- note: iodine_db adapter has NO beef entries (verified 2026-08-29: TDS R4 subset lacks plain beef cuts) - iodine anchor carried as a literature row citing the same FDA TDS chuck-roast datum the 10035 review used.
- note: MEXT frame note: 'without subcutaneous fat' = external fat removed, seam fat in - the same frame concept as our 0" trim lean+fat. Imported-beef class is the US/AU-origin population (policy precedent: 10021/10035 vit D reviews).

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| FCDB:1019 Beef, chuck, raw | Beef, chuck, raw - Danish analytical; leaner Danish trim was a frame MISMATCH vs untrimmed 10035 (cv_intl EXCLUDES) but sits closer to this trimmed frame; compare engine decides row by row | independent (1/41 incidental matches) |
| BLS:U231100 Beef neck/chuck, raw | Beef neck/chuck (Hals/Kamm), raw - German chuck-roll/neck region, adjacent to under blade; frame unstated, expect compilation quality | independent (0/39 incidental matches) |
| MEXT:11065 Beef, imported beef, chuck roll, without subcutaneous fat, raw  | Beef, imported beef, chuck roll, without subcutaneous fat, raw - BEST frame match: US/AU-origin population, chuck-roll complex (contains the under blade), external fat off | independent (1/43 incidental matches) |
| CIQUAL:6270 Boeuf, paleron cru | Boeuf, paleron cru - French chuck/blade braising cut; 10035's paleron row was judged independent (gave K1 1.5); echo screen decides again here | independent (2/28 incidental matches) |
| CoFID:18-007 Beef, braising steak, raw, lean and fat | Beef, braising steak, raw, lean and fat - UK chuck-and-blade retail frame (~13% fat, closest CoFID frame to ours); underlying LGC carcase surveys per refs; lean-only twin is 18-006 | independent (1/22 incidental matches) |
| AFCD:F000527 Beef, casserole meat, boneless, chuck, untrimmed, raw | Beef, casserole meat, boneless, chuck, untrimmed, raw - Australian retail chuck; 'untrimmed' AU convention is leaner than US untrimmed, roughly bracketing our frame; check Derivation flag for borrows | independent (0/31 incidental matches) |
| Spitze03:Beef muscle band (ground <30% fat; b-grade whole cuts) | Spitze 2003 beef muscle band 31-43 mg/100 g: ground <30% fat 36.4 (n=6, 33.4-38.5), b-grade whole 43+/-8 (n=5). Under blade is oxidative shoulder muscle -> high end, matching sibling 10035's validated 40. Lean-mass scaling from 10035's frame (82->86% lean) would give ~42; no under-blade-specific measurement exists, so no stats attached (sibling-consistency convention). | no USDA overlap — independence not establishable |
| FDA-TDS:Beef chuck roast, oven-roasted (TDS; not in local iodine_db subset) | FDA Total Diet Study chuck roast oven-roasted 3.8 µg/100 g (n=8, SD 2.2), back-adjusted ~x0.75 for cooking moisture loss -> ~2.8-2.9 raw. Same datum and adjustment the 10035 review stored (2.8). COOKED-frame caveat as with the 10054 iodine anchor. | no USDA overlap — independence not establishable |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | FDA-TDS | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | — | 19.15‡ (n=24) | 21.7‡ | 19.25† | 21.2° | 20.7° | 18.8333 (n=6) | — | 18 | — | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | FDA-TDS | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 1.261‡ | — | 1.33† | — | — | 1.15317 | — | 1.2~ | — | **confirm** |
| Histidine (1221) | g | — | 0.621‡ | — | 0.73† | — | — | 0.6545 | — | 0.69~ | — | **confirm** |
| Isoleucine (1212) | g | — | 0.815‡ | — | 1.11† | — | — | 0.935 | — | 0.79~ | — | **confirm** |
| Leucine (1213) | g | — | 1.541‡ | — | 1.8† | — | — | 1.46483 | — | 1.4~ | — | **confirm** |
| Lysine (1214) | g | — | 1.675‡ | — | 1.86† | — | — | 1.62067 | — | 1.6~ | — | **confirm** |
| Methionine (1215) | g | — | 0.544‡ | — | 0.55† | — | — | 0.4675 | — | 0.46~ | — | **confirm** |
| Cystine (1216) | g | — | 0.201‡ | — | 0.26† | — | — | 0.14025 | — | 0.2~ | — | **confirm** |
| Phenylalanine (1217) | g | — | 0.729‡ | — | 0.91† | — | — | 0.748 | — | 0.72~ | — | **confirm** |
| Tyrosine (1218) | g | — | 0.66‡ | — | 0.73† | — | — | 0.623333 | — | 0.61~ | — | **confirm** |
| Threonine (1211) | g | — | 0.843‡ | — | 1† | — | — | 0.810333 | — | 0.79~ | — | **confirm** |
| Tryptophan (1210) | g | — | 0.216‡ | 0.175‡ | 0.25† | — | — | 0.221283 | — | 0.22~ | — | **confirm** |
| Valine (1219) | g | — | 0.866‡ | — | 1.21† | — | — | 0.997333 | — | 0.85~ | — | **confirm** |
| Taurine (1234) | mg | — | — | — | — | — | — | — | — | — | 40 | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | FDA-TDS | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | — | 13.93‡ (n=24) | 10.4‡ | 8.05† | 6.54° | 8.6° | 13.1167 (n=6) | — | 17.1 | — | **confirm** |

## Fatty Acid

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | FDA-TDS | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 0.515? | 0.27‡ | 0.17† | 0.13° | — | 0.177334 (n=8) | — | 0.32~ | — | **review** |
| Arachidonic acid (1271) | g | — | 0.045‡ (n=4) | 0.06845‡ | — | — | — | 0 (n=8) | — | 0.023~ | — | **review** |
| Alpha-linolenic acid (1270) | g | — | 0.021? | 0.09‡ | 0.1† | 0.031° | — | 0.0360805 (n=8) | — | 0.071~ | — | **confirm** |
| EPA (1278) | g | — | 0.001‡ (n=4) | 0.04512‡ | — | 0° | — | — | — | 0.005~ | — | **confirm** |
| DHA (1272) | g | — | 0‡ (n=4) | 0.00837‡ | — | 0° | — | 0 (n=8) | — | 0~ | — | **confirm** |
| Fatty acids, total polyunsaturated (1293) | g | — | 0.588‡ | 0.58‡ | 0.27‡ | — | 0.4° | 0.213415‡ | — | 0.47~ | — | **review** |
| DPA 22:5 n-3 (1280) | g | — | 0.003‡ (n=4) | 0.0534‡ | — | — | — | — | — | 0.025~ | — | **region_keep** |

## Mineral

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | FDA-TDS | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | — | 12‡ (n=4) | 4‡ | 6.48† | 11° | 5° | 5.27 (n=6) | — | 4 | — | **confirm** |
| Phosphorus (1091) | mg | — | 181‡ (n=4) | 177‡ | 155† | 223° | 180° | 175 (n=6) | — | 150 | — | **confirm** |
| Potassium (1092) | mg | — | 329‡ (n=4) | 336‡ | 292.174† | 343° | 300° | 310‡ | — | 300 | — | **confirm** |
| Sodium (1093) | mg | — | 76‡ (n=4) | 58‡ | 43† | 49° | 60° | 62‡ | — | 49 | — | **review** |
| Chloride (1088) | mg | — | — | — | — | — | 51° | — | — | — | — | **adopt_foreign** |
| Magnesium (1090) | mg | — | 19‡ (n=4) | 20‡ | 17.522† | 25° | 19° | 21‡ | — | 18 | — | **confirm** |
| Iron (1089) | mg | — | 2.13‡ (n=4) | 1.74‡ | 2.035† | 2.5° | 1.4° | 2.2 (n=3) | — | 1.2 | — | **confirm** |
| Copper (1098) | mg | — | 0.073‡ (n=4) | 0.167‡ | 0.064† | 0.087° | 0 tr | 0.07‡ | — | 0.07 | — | **confirm** |
| Manganese (1101) | mg | — | 0.011‡ (n=4) | 0‡ | 0.012† | 0.012° | 0 tr | 0.011 (n=32) | — | 0.01 | — | **confirm** |
| Zinc (1095) | mg | — | 6.99‡ (n=4) | 5.91‡ | 5.678† | 5.51° | 5.6° | 4.4‡ | — | 5.8 | — | **confirm** |
| Iodine (1100) | µg | — | — | 1.3‡ | 2† | — | 16° | 1‡ | 2.8 | — | — | **adopt_foreign** |
| Selenium (1103) | µg | — | 21.7‡ (n=4) | 17.6‡ | — | 10.2° | 7° | 6.5 (n=85) | — | — | — | **region_keep** |

## Vitamin

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | FDA-TDS | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | — | 13.32? | 16.65‡ | 9.99† | 9.99° | 0 tr | 43.29‡ | — | 33.3 | — | **region_keep** |
| Vitamin D (1110) | IU | — | 5‡ (n=4) | 138.4‡ | 16‡ | 4° | 20° | 24‡ | — | 16 | — | **confirm** |
| Vitamin E (1109) | IU | — | 0.2384‡ (n=4) | 0.745‡ | 0.447† | 0.298° | 0.1341° | 0.6407‡ | — | 1.043 | — | **confirm** |
| Vitamin K (1185) | µg | — | 1.5 (n=12) | — | — | 1.5° | — | 0‡ | — | 5 | — | **form_defect** |
| Thiamin (1165) | mg | — | 0.079‡ (n=1) | 0.053‡ | 0.09† | 0.08° | 0.07° | 0.04 (n=3) | — | 0.06209 | — | **confirm** |
| Riboflavin (1166) | mg | — | 0.167‡ (n=4) | 0.182‡ | 0.19† | 0.21° | 0.27° | 0.185 (n=3) | — | 0.2 | — | **confirm** |
| Niacin (1167) | mg | — | 3.983‡ (n=4) | 2.88‡ | 5.2† | 3.67° | 3.9° | 5.7‡ | — | 3.5 | — | **confirm** |
| Pantothenic acid (1170) | mg | — | 0.63‡ (n=1) | 0.45‡ | 0.9† | 0.86° | 0.59° | 0.75‡ | — | 1 | — | **confirm** |
| Pyridoxine (1175) | mg | — | 0.38‡ (n=4) | 0.11‡ | 0.3† | 0.27° | 0.42° | 0.46‡ | — | 0.25 | — | **confirm** |
| Folic acid (1177) | µg | — | 3† | 20‡ | 4.1† | 3° | 53° | 6‡ | — | 8 | — | **confirm** |
| Cobalamin (1178) | µg | — | 2.94‡ (n=4) | 1.8‡ | 3.67† | 2.77° | 2° | 1.4 | — | 1.8 | — | **confirm** |
| Biotin (1176) | µg | — | — | — | 0† | — | 1° | 0† | — | — | — | **adopt_foreign** |
| Choline (1180) | mg | — | 64.5‡ (n=1) | — | — | — | — | 63.5† (n=1) | — | — | — | **usda_only** |

## Other

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | FDA-TDS | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 202‡ | 180.449‡ | 149‡ | 144‡ | 160° | 193.383‡ | — | 237‡ | — | **review** |
| Water (1051) | g | — | 66‡ (n=24) | 68.2‡ | 76.1† | 72.3° | 69.4° | 67.1733 (n=6) | — | 64 | — | **confirm** |
| Ash (1007) | g | — | 0.98‡ (n=24) | 1.2‡ | 1† | 1.19° | — | 0.876667 (n=6) | — | 0.8 | — | **confirm** |
| Crude Fiber (1079) | g | — | 0† | 0‡ | 0‡ | 0° | — | 0 | — | 0~ | — | **confirm** |
| Carbohydrate (1005) | g | — | 0‡ | 0‡ | 0‡ | 0° | — | 0‡ | — | 0.1 | — | **confirm** |

## Needs attention (contested rows + detection-limit context)

### Taurine (1234) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 40 mg (source `literature`)
  - Spitze03 [analysed] 40 — Spitze 2003 beef muscle band 31-43 mg/100 g: ground <30% fat 36.4 (n=6, 33.4-38.5), b-grade whole 43+/-8 (n=5). Under bl

### Linoleic acid (1269) — review
- all 3 independent(s) differ >±20% from sr_legacy 0.515: FCDB 0.177334 (n=8), MEXT 0.32, CIQUAL 0.13
- suggestion: 0.515 g (source `sr_legacy`)
  - FCDB [analysed] 0.177334 — C18:2,n-6; src [1862] Fatty acid distribution in frying oil, beef, veal and lamb (1997)
  - BLS [borrowed] 0.17 — F18:2CN6 [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [estimated] 0.32 — F18D2N6 (FA volume, per 100 g EP)
  - CIQUAL [compiled] 0.13 — AG 18:2
  - AFCD [computed] 0.27 — C18:2w6; food-level derivation: Recipe

### Arachidonic acid (1271) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.045: FCDB 0 (n=8), MEXT 0.023
- suggestion: 0.045 g (source `sr_legacy`)
  - FCDB [analysed] 0 — C20:4,n-6; src [1862] Fatty acid distribution in frying oil, beef, veal and lamb (1997)
  - MEXT [estimated] 0.023 — F20D4N6 (FA volume, per 100 g EP)
  - AFCD [computed] 0.06845 — C20:4w6; food-level derivation: Recipe

### Fatty acids, total polyunsaturated (1293) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.588: MEXT 0.47, CoFID 0.4
- suggestion: 0.588 g (source `sr_legacy`)
  - FCDB [computed] 0.213415 — Sum polyunsaturated fatty acids; src [1003] Value calculated by converting various analytical data
  - BLS [computed] 0.27 — FAPU [Formelberechnung] -
  - MEXT [estimated] 0.47 — FAPU (FA volume, per 100 g EP)
  - CoFID [compiled] 0.4 — Poly FA /100g food; refs: LGC, Nutrient analysis of carcase beef, 1992-1993
  - AFCD [computed] 0.58 — Total polyunsaturated; food-level derivation: Recipe

### DPA 22:5 n-3 (1280) — region_keep
- region-sensitive; foreign cluster differs: MEXT 0.025 — US mean kept unless defective
- suggestion: 0.003 g (source `sr_legacy`)
  - MEXT [estimated] 0.025 — F22D5N3 (FA volume, per 100 g EP)
  - AFCD [computed] 0.0534 — C22:5w3; food-level derivation: Recipe

### Sodium (1093) — review
- all 3 independent(s) differ >±20% from sr_legacy 76: MEXT 49, CIQUAL 49, CoFID 60
- suggestion: 76 mg (source `sr_legacy`)
  - FCDB [computed] 62 — Sodium; src [1003] Value calculated by converting various analytical data
  - BLS [borrowed] 43 — NA [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 49 — NA (main volume)
  - CIQUAL [compiled] 49 — Sodium
  - CoFID [compiled] 60 — Sodium; refs: LGC, Nutrient analysis of carcase beef, 1992-1993
  - AFCD [computed] 58 — Sodium; food-level derivation: Recipe

### Chloride (1088) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 51 mg (source `literature`)
  - CoFID [compiled] 51 — Chloride; refs: LGC, Nutrient analysis of carcase beef, 1992-1993

### Copper (1098) — confirm
- 2/2 independent(s) within ±20%: MEXT 0.07, CIQUAL 0.087
- detection-limit info: CoFID trace
- suggestion: 0.073 mg (source `sr_legacy`)
  - FCDB [computed] 0.07 — Copper; src [1003] Value calculated by converting various analytical data
  - BLS [borrowed] 0.064 — CU [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.07 — CU (main volume)
  - CIQUAL [compiled] 0.087 — Cuivre
  - CoFID [trace] 0 — Copper; refs: LGC, Nutrient analysis of carcase beef, 1992-1993
  - AFCD [computed] 0.167 — Copper; food-level derivation: Recipe

### Manganese (1101) — confirm
- 3/3 independent(s) within ±20%: FCDB 0.011 (n=32), MEXT 0.01, CIQUAL 0.012
- detection-limit info: CoFID trace
- suggestion: 0.011 mg (source `sr_legacy`)
  - FCDB [analysed] 0.011 — Manganese; src [1348] Mineral Element Composition of Finnish Foods: N, K, Ca, Mg, P, S, Fe, Cu, Mn, Zn, Mo, Co, Ni, Cr, 
  - BLS [borrowed] 0.012 — MN [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.01 — MN (main volume)
  - CIQUAL [compiled] 0.012 — Manganèse
  - CoFID [trace] 0 — Manganese; refs: LGC, Nutrient analysis of carcase beef, 1992-1993
  - AFCD [computed] 0 — Manganese; food-level derivation: Recipe

### Iodine (1100) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 2.8 µg (source `literature`)
  - FCDB [computed] 1 — Iodine; src [1003] Value calculated by converting various analytical data
  - BLS [borrowed] 2 — ID [Übernommener Wert] -
  - CoFID [compiled] 16 — Iodine; refs: LGC, Nutrient analysis of carcase beef, 1992-1993
  - AFCD [computed] 1.3 — Iodine; food-level derivation: Recipe
  - FDA-TDS [analysed] 2.8 — FDA Total Diet Study chuck roast oven-roasted 3.8 µg/100 g (n=8, SD 2.2), back-adjusted ~x0.75 for cooking moisture loss

### Selenium (1103) — region_keep
- region-sensitive; foreign cluster differs: FCDB 6.5 (n=85), CIQUAL 10.2, CoFID 7 — US mean kept unless defective
- suggestion: 21.7 µg (source `sr_legacy`)
  - FCDB [analysed] 6.5 — Selenium; src [1532] Monitoring program for trace elements in foodstuffs, 1983-1987. 1986: Cd, Pb, Hg, Ni, Cr, As and Se
  - CIQUAL [compiled] 10.2 — Sélénium
  - CoFID [compiled] 7 — Selenium; refs: LGC, Nutrient analysis of carcase beef, 1992-1993
  - AFCD [computed] 17.6 — Selenium; food-level derivation: Recipe

### Vitamin A (1106) — region_keep
- region-sensitive; foreign cluster differs: MEXT 33.3, CIQUAL 9.99 — US mean kept unless defective
- detection-limit info: CoFID trace
- suggestion: 13.32 IU (source `sr_legacy`)
  - FCDB [computed] 43.29 — Retinol; src [1003] Value calculated by converting various analytical data
  - BLS [borrowed] 9.99 — RETOL [Nährstoffdatenbank] Converted value from: Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzu
  - MEXT [analysed] 33.3 — RETOL (main volume)
  - CIQUAL [compiled] 9.99 — Rétinol
  - CoFID [trace] 0 — Retinol; refs: LGC, Nutrient analysis of carcase beef, 1992-1993
  - AFCD [computed] 16.65 — Retinol (preformed); food-level derivation: Recipe

### Vitamin K (1185) — form_defect
- USDA K row is K1-only (1.5 µg); menaquinone-inclusive tables read ~5 µg
- suggestion: 5 µg (source `literature`)
  - FCDB [computed] 0 — Vitamin K; src [1003] Value calculated by converting various analytical data
  - MEXT [analysed] 5 — VITK (main volume); menaquinone-inclusive total K
  - CIQUAL [compiled] 1.5 — Vitamine K1 only; K2 n/a

### Biotin (1176) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 1 µg (source `literature`)
  - FCDB [borrowed] 0 — Biotin; src [1344] McCance and Widdowson's: The Composition of Foods, 4th revised and extended edition (1978)
  - BLS [borrowed] 0 — BIOT [Nährstoffdatenbank] National Food Institute, Food data (frida.fooddata.dk), version 5.2, May 2024
  - CoFID [compiled] 1 — Biotin; refs: LGC, Nutrient analysis of carcase beef, 1992-1993

### Energy (1008) — review
- all 1 independent(s) differ >±20% from sr_legacy 202: CoFID 160
- suggestion: 202 kcal (source `sr_legacy`)
  - FCDB [computed] 193.383 — Energy (kcal); src [1003] Value calculated by converting various analytical data
  - BLS [computed] 149 — ENERCC [Formelberechnung] -
  - MEXT [computed] 237 — ENERC_KCAL (main volume); energy is always calculated
  - CIQUAL [computed] 144 — Energie Jones
  - CoFID [compiled] 160 — Energy; refs: LGC, Nutrient analysis of carcase beef, 1992-1993
  - AFCD [computed] 180.449 — Energy without fibre, equated; food-level derivation: Recipe

## Verdict summary

- confirm: 38
- review: 5
- adopt_foreign: 4
- region_keep: 3
- form_defect: 1
- usda_only: 1
