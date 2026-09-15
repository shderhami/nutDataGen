# Intake report: pacific cod wild raw

- generated: 2026-09-14  |  spec: `data/intake/pacific_cod.json`
- Foundation FDC: 2684444  |  SR Legacy FDC: 171955
- category: Fish & Seafood  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: price_per_unit 0.0198/g = Shahab's $8.99/lb (Safeway, Waterfront Bistro Wild Alaskan Cod, 16 oz IQF bag) / 453.592, confirmed 2026-09-14. Premium whitefish vs pollock 0.0120.
- note: FRAME-OVER-SPECIES BUILD (decided with Shahab 2026-09-14 from bag label photos): the product is PACIFIC cod - the bag's own binomial reads GADUS MACROCEPHALUS ('wild Alaskan cod', caught Alaska / processed China, IQF, two-ingredient line: cod + STP). But the species-exact SR 174191 is a TREATED retail population ('may have been previously frozen', Na 303 n=11, protein soak-diluted to 15.27) - entering it would misstate every protein-linked row ~14% low and Na 3.4x high vs the actual bag. The bag PANEL (per 100 g: protein 17.7, Na 88.5, vit D ~35 IU, kcal 75 by 4-4-9) sits on UNTREATED Atlantic SR 171955 within label rounding (protein 17.81 = 0.6% off, D 36 = 2% off). Treatment effect >> congener effect on every FEDIAF row -> primary = SR 171955. This is the treatment analog of the NZ-lamb frame flip. SR 174191 serves as per-protein cross-check only (its choline 133-nutrient panel available for per-protein transfer if a gap surfaces).
- note: PANEL TEST (pollock lesson, 2nd application, same house brand): STP declared in the ingredient line but Na 100 mg/serving << 250 avoid-threshold and protein 20 g/serving >> 14 -> LIGHT dip, untreated class - the cleanest fish bag tested (their pollock ran Na 119.5). AVOID-FRAME customer guidance transfers verbatim: avoid bags reading sodium >=250 mg/serving or protein <14 g/serving; the panel, not the ingredient line, is the frame test.
- note: FND 2684444 (Atlantic wild raw, 40 nutrients, no AAs) is paired SOLELY as the modern-population + MEASURED-IODINE carrier: iodine 113.7 ug (n=8) - the DB's SECOND measured-iodine food (pollock 185.5 was first). Its frame is the TREATED retail population (Na 298.8 n=8) -> expect row-by-row frame rejections: Na REJECT (soak artifact; SR 54 governs), P scrutiny (STP adds P; SR governs, light-dip note), protein-diluted rows reject to SR; Se/minerals corroborate per-protein. Soak direction on iodine: dilution ~10-15%, so 113.7 slightly UNDERSTATES untreated tissue - noted for the max screen; TDS arbitrates.
- note: IODINE MAX-SCREEN: 113.7 ug -> ~1512 ug/1000 kcal-of-cod; at 45% caloric inclusion ~680 vs the 1.1 mg/1000 kcal max (62%) - headroom, and lighter per calorie than pollock. DOUBLE-COUNT GUARD: iodine_db '(100328) Fish, cod, Atlantic, wild, raw' IS the FND 2684444 population (ODS echo of the same n=8 measurement) - corroboration display only, NEVER independent evidence; not listed as a source. 15192 baked = frame-off, skipped.
- note: REAL-D FISH (vs pollock's trace-honest 8 IU): SR 36 IU and the bag label ~35 IU AGREE - the first label-USDA vitamin D agreement in the fish series. MAX-SCREEN: at 45% caloric inclusion cod alone contributes ~215 IU/1000 kcal vs the 227 legal max -> cod-heavy recipes force D3 drops to ~zero (formulator max row enforces; feeds Shahab's planned editorial D advisory row). Review must still rank D by derivation code (pollock ritual); MEXT 10205 analysed D expected to corroborate ~40 IU.
- note: SPECIES MAP: EXACT G. macrocephalus = MEXT 10205 (madara, Japanese analysed), CIQUAL 26125 (Cabillaud ou morue du Pacifique, cru), iodine_db 15019 (US TDS Pacific raw). ATLANTIC congener G. morhua = SR 171955 (primary), FND 2684444, BLS T204100 (Kabeljau), FCDB 72, CoFID 16-372, CIQUAL 26043. Where Atlantic and Pacific genuinely differ (Se, D, FA), the exact-species analysed columns arbitrate. EXCLUDED: FCDB 570 'Torsk, tusk, raw' = tusk/cusk (Brosme brosme), a different fish despite the Danish name; AFCD carries NO raw gadid cod (smoked only + crocodile false-hits) - source absent; BLS T204200 deep-frozen = same population alternate frame, not listed.
- note: SR 171955 panel: 97 nutrients incl. full 12/12 AA panel, big n's (Na n=44) - only the standard four gaps (taurine, Cl, iodine, biotin). Fills: iodine = FND MEASURED with native stats (fdc_range CV expected, pollock convention); Cl + biotin = CoFID 16-372 carrier (chloride anchors: salmon 56, tilapia 61); taurine = fish-family literature estimate below. Choline present in SR natively.
- note: Fish doctrine hooks: fish-diet vitamin K rule -> pairs with K1 corrector 10065; very lean (fat ~0.7) -> tallow 10064 is the natural diluent; gadids are LOW-THIAMINASE (safer raw) and Pacific cod is moderate-low mercury (~0.1 ppm, a notch above pollock, well under concern) - customer-note material. Marine vit K ~nil expected (salmon 0.5 / tilapia 1.4 anchors).
- note: FCDB 72 (cod fillet raw): check for n's/min-max - cv_intl candidate (Danish staple fish, stats likely).

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| MEXT:10205 Fish, cod, Pacific cod, raw | Fish, cod, Pacific cod, raw (madara) - EXACT species, Japanese analysed panel; the Pacific-vs-Atlantic arbitrator for Se/D/FA; iodine datapoint expected | independent (1/44 incidental matches) |
| CIQUAL:26125 Cabillaud ou morue du Pacifique, cru | Cabillaud ou morue du Pacifique, cru - EXACT species (macrocephalus); echo screen decides | independent (2/28 incidental matches) |
| CIQUAL:26043 Cabillaud, cru | Cabillaud, cru - Atlantic congener (morhua), the fuller French aliment-moyen panel; echo screen decides | independent (2/30 incidental matches) |
| BLS:T204100 Cod raw | Cod raw (Kabeljau) - Atlantic congener; echo screen decides independence | independent (14/44 incidental matches) |
| FCDB:72 Cod, fillet, raw | Cod, fillet, raw - Atlantic congener, Danish; check for stats (cv_intl candidate) | independent (1/46 incidental matches) |
| CoFID:16-372 Cod, flesh only, raw | Cod, flesh only, raw - Atlantic congener, UK; the chloride + biotin carrier; UK-measured iodine expected as corroboration | independent (2/29 incidental matches) |
| IodineDB:NDB 15019 Fish, cod, Pacific, raw | Fish, cod, Pacific, raw - EXACT species US TDS; arbitrates the FND 113.7 measured iodine (which is Atlantic + soak-diluted); (100328) sibling row excluded as FND echo | USDA-affiliated — evidence, never independent confirmation |
| FishFamily:Gadid muscle taurine (family band: tilapia-est 84, salmon-Spitze 130, pollock-est 100) | No cod taurine measurement in any local resource; gadid muscle is taurine-substantial. Family-band mid 100 mirrors pollock 10066, SPARSE-EVIDENCE flag; prefer any measured value surfacing at review | no USDA overlap — independence not establishable |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | BLS | CIQUAL | CoFID | FCDB | FishFamily | IodineDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | 16.0688‡ | 17.81 (n=605) | 17.8† | 15.3° / 18.1° | 17.5° | 17.5135 (n=97) | — | — | 17.6 | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | BLS | CIQUAL | CoFID | FCDB | FishFamily | IodineDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 1.066? | 1.07† | — | — | 1.07849 | — | — | 1.1 | **confirm** |
| Histidine (1221) | g | — | 0.524? | 0.524† | — | — | 0.359495 | — | — | 0.44 | **confirm** |
| Isoleucine (1212) | g | — | 0.821? | 0.821† | — | — | 0.86878 | — | — | 0.69 | **confirm** |
| Leucine (1213) | g | — | 1.447? | 1.45† | — | — | 1.34811 | — | — | 1.3 | **confirm** |
| Lysine (1214) | g | — | 1.635? | 1.64† | — | — | 1.64769 | — | — | 1.5 | **confirm** |
| Methionine (1215) | g | — | 0.527? | 0.527† | — | — | 0.569201 | — | — | 0.53 | **confirm** |
| Cystine (1216) | g | — | 0.191? | 0.191† | — | — | 0.128819 | — | — | 0.19 | **confirm** |
| Phenylalanine (1217) | g | — | 0.695? | 0.695† | — | — | 0.689033 | — | — | 0.64 | **confirm** |
| Tyrosine (1218) | g | — | 0.601? | 0.601† | — | — | 0.659075 | — | — | 0.58 | **confirm** |
| Threonine (1211) | g | — | 0.781? | 0.781† | — | — | 0.748948 | — | — | 0.73 | **confirm** |
| Tryptophan (1210) | g | — | 0.199? | 0.199† | — | — | 0.17076 | — | — | 0.18 | **confirm** |
| Valine (1219) | g | — | 0.917? | 0.917† | — | — | 0.958654 | — | — | 0.78 | **confirm** |
| Taurine (1234) | mg | — | — | — | — | — | — | 100~ | — | — | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | BLS | CIQUAL | CoFID | FCDB | FishFamily | IodineDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | 0.6675 (n=8) | 0.67 (n=293) | 0.84† | 0.41° / 0.57° | 0.6° | 0.579661 (n=59) | — | — | 0.2 | **confirm** |

## Fatty Acid

| nutrient | unit | FND | SR | BLS | CIQUAL | CoFID | FCDB | FishFamily | IodineDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 0.005 (n=25) | 0.0078† | 0.015° / 0.003° | 0.03° | 0.0010034 (n=4) | — | — | 0.001 | **confirm** |
| Arachidonic acid (1271) | g | — | 0.022 (n=23) | 0.023† | — | 0 tr | — | — | — | 0.004 | **review** |
| Alpha-linolenic acid (1270) | g | — | 0.001 (n=19) | 0.0034† | 0.001° / 0.001° | 0 tr | 0.00802719 (n=4) | — | — | 0 tr | **confirm** |
| EPA (1278) | g | 0.018 (n=7) | 0.064 (n=26) | 0.1† | 0.034° / 0.05° | 0.02° | 0.0697362 (n=4) | — | — | 0.024 | **confirm** |
| DHA (1272) | g | 0.054 (n=7) | 0.12 (n=26) | 0.239† | 0.096° / 0.13° | 0.05° | 0.152015 (n=4) | — | — | 0.042 | **confirm** |
| Fatty acids, total polyunsaturated (1293) | g | 0.081 (n=7) | 0.231? | 0.395‡ | — | 0.11° | 0.240063‡ | — | — | 0.07 | **confirm** |
| DPA 22:5 n-3 (1280) | g | 0.003 (n=7) | 0.01 (n=22) | 0.017† | — | 0 tr | 0.00928143 (n=4) | — | — | 0.002 | **confirm** |

## Mineral

| nutrient | unit | FND | SR | BLS | CIQUAL | CoFID | FCDB | FishFamily | IodineDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | 6.59 (n=8) | 16 (n=101) | 28† | 8° / 4.43° | 12° | 15 (n=3) | — | — | 32 | **confirm** |
| Phosphorus (1091) | mg | 224.1 (n=8) | 203 (n=75) | 169† | 281° / 163° | 169° | 200 | — | — | 230 | **confirm** |
| Potassium (1092) | mg | 245.1 (n=8) | 413 (n=49) | 340† | 235° / 357° | 322° | 338 (n=3) | — | — | 350 | **confirm** |
| Sodium (1093) | mg | 298.8 (n=8) | 54 (n=44) | 72† | 303° / 65.2° | 91° | 76 (n=3) | — | — | 110 | **confirm** |
| Chloride (1088) | mg | — | — | 165† | 110° | 165° | — | — | — | — | **adopt_foreign** |
| Magnesium (1090) | mg | 17.98 (n=8) | 32 (n=30) | 21† | 20° / 25.6° | 25° | 25 (n=3) | — | — | 24 | **confirm** |
| Iron (1089) | mg | 0.065 (n=8) | 0.38 (n=26) | 0.16† | 0.16° / 0.49° | 0.1° | 0.2 (n=4) | — | — | 0.2 | **review** |
| Copper (1098) | mg | 0.003963 (n=8) | 0.028 (n=136) | 0.028† | 0.019° / 0.1< | 0.02° | 0.019 (n=94) | — | — | 0.04 | **review** |
| Manganese (1101) | mg | 0 (n=8) | 0.015? | 0.025† | 0.012° / 0.1< | 0.01° | 0.02 (n=7) | — | — | 0.01 | **confirm** |
| Zinc (1095) | mg | 0.3051 (n=8) | 0.45 (n=188) | 0.41† | 0.31° / 0.39° | 0.3° | 0.38 (n=94) | — | — | 0.5 | **confirm** |
| Iodine (1100) | µg | 113.7 (n=8) | — | 224† | 101° | 196° | 252.844 (n=96) | — | 130.6 (n=7) | 350 | **confirm** |
| Selenium (1103) | µg | 22.79 (n=8) | 33.1 (n=11) | — | 136° | 23° | 28.65 (n=80) | — | — | 31 | **confirm** |

## Vitamin

| nutrient | unit | FND | SR | BLS | CIQUAL | CoFID | FCDB | FishFamily | IodineDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | 3.07492 (n=8) | 39.96‡ | 6.66† | 6.66° / 6.66< | 6.66° | 7.659† (n=1) | — | — | 33.3 | **region_keep** |
| Vitamin D (1110) | IU | — | 36 (n=1) | 0‡ | 20° | 0 tr | 40‡ | — | — | 40 | **confirm** |
| Vitamin E (1109) | IU | — | 0.9536 (n=2) | 0.4768† | 0.8046° / 0.6556° | 0.9834° | 0.6705‡ (n=3) | — | — | 1.192 | **confirm** |
| Vitamin K (1185) | µg | — | 0.1 (n=1) | 10.28‡ | 0° / 0.1° | 0.01° | 6.82978‡ | — | — | 0~ | **confirm** |
| Thiamin (1165) | mg | — | 0.076 (n=40) | 0.055† | 0.033° / 0.04< | 0.06° | 0.05 (n=12) | — | — | 0.0887 | **confirm** |
| Riboflavin (1166) | mg | — | 0.065 (n=68) | 0.046† | 0.045° / 0.049° | 0.08° | 0.04 (n=8) | — | — | 0.1 | **confirm** |
| Niacin (1167) | mg | — | 2.063 (n=69) | 2.3† | 1.1° / 2.18° | 2.3° | 2 (n=8) | — | — | 1.4 | **confirm** |
| Pantothenic acid (1170) | mg | — | 0.153 (n=45) | 0.25† | 0.29° / 0.14° | 0.25° | 0.14 | — | — | 0.44 | **confirm** |
| Pyridoxine (1175) | mg | — | 0.245 (n=4) | 0.2† | 0.12° / 0.16° | 0.14° | 0.221 (n=4) | — | — | 0.07 | **confirm** |
| Folic acid (1177) | µg | — | 7? | 5.6† | 7° / 21.2° | 7° | 16 (n=4) | — | — | 5 | **confirm** |
| Cobalamin (1178) | µg | 1.248 (n=8) | 0.91 (n=55) | 1.155† | 1.98° / 1.32° | 1.5° | 1.10849 (n=53) | — | — | 1.3 | **confirm** |
| Biotin (1176) | µg | — | — | 1.3† | — | 1.3° | 1.1 (n=4) | — | — | 2.5 | **adopt_foreign** |
| Choline (1180) | mg | — | 65.2† | — | — | — | 65.2† (n=1) | — | — | — | **usda_only** |

## Other

| nutrient | unit | FND | SR | BLS | CIQUAL | CoFID | FCDB | FishFamily | IodineDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 82‡ | 79‡ | 64.8‡ / 77.4‡ | 75° | 75.271‡ | — | — | 77‡ | **confirm** |
| Water (1051) | g | 82.86 (n=8) | 81.22 (n=537) | 80.45† | 84° / 79.8° | 81.6° | 80.699 (n=99) | — | — | 80.9 | **confirm** |
| Ash (1007) | g | 1.478 (n=8) | 1.16 (n=165) | 1.2† | 1.46° / 1.1° | — | 1.20784 (n=97) | — | — | 1.2 | **confirm** |
| Crude Fiber (1079) | g | — | 0† | 0‡ | 0° / 0.2< | 0° | 0 | — | — | 0~ | **confirm** |
| Carbohydrate (1005) | g | 0‡ | 0† | 0‡ | 0° / 0 tr | — | 0‡ | — | — | 0.1 | **confirm** |

## Needs attention (contested rows + detection-limit context)

### Taurine (1234) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 100 mg (source `literature`)
  - FishFamily [estimated] 100 — No cod taurine measurement in any local resource; gadid muscle is taurine-substantial. Family-band mid 100 mirrors pollo

### Arachidonic acid (1271) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.022: MEXT 0.004
- detection-limit info: CoFID trace
- suggestion: 0.022 g (source `sr_legacy`)
  - MEXT [analysed] 0.004 — F20D4N6 (FA volume, per 100 g EP)
  - BLS [borrowed] 0.023 — F20:4CN6 [Nährstoffdatenbank] Leibniz-Institut für Lebensmittel-Systembiologie; SFK Online Version; 2016
  - CoFID [trace] 0 — cis n-6 C20:4; refs: DH, Nutrient analysis of fish and fish products, 2013

### Alpha-linolenic acid (1270) — confirm
- 3/3 independent(s) within ±20%: CIQUAL 0.001, CIQUAL 0.001, FCDB 0.00802719 (n=4)
- detection-limit info: MEXT trace, CoFID trace
- suggestion: 0.001 g (source `sr_legacy`)
  - MEXT [trace] 0 — F18D3N3 (FA volume, per 100 g EP)
  - CIQUAL [compiled] 0.001 — AG 18:3
  - CIQUAL [compiled] 0.001 — AG 18:3
  - BLS [borrowed] 0.0034 — F18:3CN3 [Nährstoffdatenbank] Leibniz-Institut für Lebensmittel-Systembiologie; SFK Online Version; 2016
  - FCDB [analysed] 0.00802719 — C18:3,n-3; src [1818] Determination of fat and fatty acid distribution (1992)
  - CoFID [trace] 0 — cis n-3 C18:3; refs: DH, Nutrient analysis of fish and fish products, 2013

### DPA 22:5 n-3 (1280) — confirm
- 2/2 independent(s) within ±20%: MEXT 0.002, FCDB 0.00928143 (n=4)
- detection-limit info: CoFID trace
- suggestion: 0.003 g (source `foundation`)
  - MEXT [analysed] 0.002 — F22D5N3 (FA volume, per 100 g EP)
  - BLS [borrowed] 0.017 — F22:5CN3 [Nährstoffdatenbank] Leibniz-Institut für Lebensmittel-Systembiologie; SFK Online Version; 2016
  - FCDB [analysed] 0.00928143 — C22:5,n-3; src [1818] Determination of fat and fatty acid distribution (1992)
  - CoFID [trace] 0 — cis n-3 C22:5; refs: DH, Nutrient analysis of fish and fish products, 2013

### Chloride (1088) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 110 mg (source `literature`)
  - CIQUAL [compiled] 110 — Chlorure
  - BLS [borrowed] 165 — CLD [Literatur] Health, D. o; Nutrient analysis of fish and fish products; 2013
  - CoFID [compiled] 165 — Chloride; refs: DH, Nutrient analysis of fish and fish products, 2013

### Iron (1089) — review
- all 5 independent(s) differ >±20% from foundation 0.065: MEXT 0.2, CIQUAL 0.16, CIQUAL 0.49, FCDB 0.2 (n=4), CoFID 0.1
- suggestion: 0.065 mg (source `foundation`)
  - MEXT [analysed] 0.2 — FE (main volume)
  - CIQUAL [compiled] 0.16 — Fer
  - CIQUAL [compiled] 0.49 — Fer
  - BLS [borrowed] 0.16 — FE [Literatur] Koivistoinen P; Mineral element composition of Finnish foods. N, K, Ca, Mg, P, S
  - FCDB [analysed] 0.2 — Iron; src [1043] The iron content of Danish foods (1978)
  - CoFID [compiled] 0.1 — Iron; refs: DH, Nutrient analysis of fish and fish products, 2013

### Copper (1098) — review
- all 4 independent(s) differ >±20% from foundation 0.003963: MEXT 0.04, CIQUAL 0.019, FCDB 0.019 (n=94), CoFID 0.02
- detection-limit info: CIQUAL <= 0.1
- suggestion: 0.003963 mg (source `foundation`)
  - MEXT [analysed] 0.04 — CU (main volume)
  - CIQUAL [compiled] 0.019 — Cuivre
  - CIQUAL [censored] 0.1 — Cuivre
  - BLS [borrowed] 0.028 — CU [Aggregation] Koivistoinen P; Mineral element composition of Finnish foods. N, K, Ca, Mg, P, S
  - FCDB [analysed] 0.019 — Copper; src [1534] Inorganic contaminants in consumer fish from Danish main waters (1987)
  - CoFID [compiled] 0.02 — Copper; refs: DH, Nutrient analysis of fish and fish products, 2013

### Manganese (1101) — confirm
- 2/4 independent(s) within ±20%: MEXT 0.01, CoFID 0.01
- detection-limit info: CIQUAL <= 0.1
- suggestion: 0 mg (source `foundation`)
  - MEXT [analysed] 0.01 — MN (main volume)
  - CIQUAL [compiled] 0.012 — Manganèse
  - CIQUAL [censored] 0.1 — Manganèse
  - BLS [borrowed] 0.025 — MN [Literatur] Koivistoinen P; Mineral element composition of Finnish foods. N, K, Ca, Mg, P, S
  - FCDB [analysed] 0.02 — Manganese; src [1368] Composition of the Edible Portion of Raw (Fresh or Frozen) Crustaceans, Finfish and Mollusks. III 
  - CoFID [compiled] 0.01 — Manganese; refs: DH, Nutrient analysis of fish and fish products, 2013

### Vitamin A (1106) — region_keep
- region-sensitive; foreign cluster differs: MEXT 33.3, CIQUAL 6.66, CoFID 6.66 — US mean kept unless defective
- detection-limit info: CIQUAL <= 6.66
- suggestion: 3.07492 IU (source `foundation`)
  - MEXT [analysed] 33.3 — RETOL (main volume)
  - CIQUAL [compiled] 6.66 — Rétinol
  - CIQUAL [censored] 6.66 — Rétinol
  - BLS [borrowed] 6.66 — RETOL [Literatur] Health, D. o; Nutrient analysis of fish and fish products; 2013
  - FCDB [borrowed] 7.659 — Retinol; src [2284] The Swedish Food Composition Database, Version 2025-06-09 (2025)
  - CoFID [compiled] 6.66 — Retinol; refs: DH, Nutrient analysis of fish and fish products, 2013

### Vitamin D (1110) — confirm
- 1/2 independent(s) within ±20%: MEXT 40
- detection-limit info: CoFID trace
- suggestion: 36 IU (source `sr_legacy`)
  - MEXT [analysed] 40 — VITD (main volume)
  - CIQUAL [compiled] 20 — Vitamine D
  - BLS [computed] 0 — VITD [Formelberechnung] -
  - FCDB [computed] 40 — Vitamin D; src [1003] Value calculated by converting various analytical data
  - CoFID [trace] 0 — Vitamin D; refs: DH, Nutrient analysis of fish and fish products, 2013

### Thiamin (1165) — confirm
- 1/4 independent(s) within ±20%: MEXT 0.0887
- detection-limit info: CIQUAL <= 0.04
- suggestion: 0.076 mg (source `sr_legacy`)
  - MEXT [analysed] 0.0887 — THIAHCL 0.1 x0.887 (HCl->thiamin base)
  - CIQUAL [compiled] 0.033 — B1
  - CIQUAL [censored] 0.04 — B1
  - BLS [borrowed] 0.055 — THIA [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - FCDB [analysed] 0.05 — Thiamin (Vitamin B1); src [1019] Studies of the vitamin B1 content in Danish foods by The Danish Vitamin Laboratory (195
  - CoFID [compiled] 0.06 — Thiamin; refs: DH, Nutrient analysis of fish and fish products, 2013

### Biotin (1176) — adopt_foreign
- no USDA value; 3 measured source(s) available
- suggestion: 1.3 µg (source `literature`)
  - MEXT [analysed] 2.5 — BIOT (main volume)
  - BLS [borrowed] 1.3 — BIOT [Literatur] Health, D. o; Nutrient analysis of fish and fish products; 2013
  - FCDB [analysed] 1.1 — Biotin; src [1071] Folacin and Biotin in Foods (1988)
  - CoFID [compiled] 1.3 — Biotin; refs: DH, Nutrient analysis of fish and fish products, 2013

### Crude Fiber (1079) — confirm
- 4/4 independent(s) within ±20%: MEXT 0, CIQUAL 0, FCDB 0, CoFID 0
- detection-limit info: CIQUAL <= 0.2
- suggestion: 0 g (source `sr_legacy`)
  - MEXT [estimated] 0 — FIBTG (main volume)
  - CIQUAL [compiled] 0 — Fibres
  - CIQUAL [censored] 0.2 — Fibres
  - BLS [computed] 0 — FIBT [Logische Null] -
  - FCDB [analysed] 0 — Dietary fibre; src [1655] Natural zero value for content. Not analyzed
  - CoFID [compiled] 0 — AOAC fibre; refs: DH, Nutrient analysis of fish and fish products, 2013

### Carbohydrate (1005) — confirm
- 1/2 independent(s) within ±20%: CIQUAL 0
- detection-limit info: CIQUAL trace
- suggestion: 0 g (source `foundation`)
  - MEXT [analysed] 0.1 — Carbohydrate, total (main volume)
  - CIQUAL [compiled] 0 — Glucides
  - CIQUAL [trace] 0 — Glucides
  - BLS [computed] 0 — CHO [Formelberechnung] -
  - FCDB [computed] 0 — Carbohydrate by difference; src [1003] Value calculated by converting various analytical data

## Verdict summary

- confirm: 44
- adopt_foreign: 3
- review: 3
- region_keep: 1
- usda_only: 1
