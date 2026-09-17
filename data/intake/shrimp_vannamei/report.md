# Intake report: whiteleg shrimp farmed raw

- generated: 2026-09-17  |  spec: `data/intake/shrimp_vannamei.json`
- Foundation FDC: 2684443  |  SR Legacy FDC: 174210
- category: Fish & Seafood  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: price_per_unit 0.022/g confirmed by Shahab 2026-09-17 - tail-off, peeled, needle-deveined retail bag. Priciest seafood-group item (cod 0.0198, pollock 0.0120).
- note: RETAIL-CLASS TREATED FRAME (Shahab-directed 2026-09-17: 'the data should be for a type of shrimp that is available in most of the retails in the usa'): that product is farm-raised whiteleg (Litopenaeus vannamei), ~80-90% of US retail, frozen raw peeled IQF - and typically STP-SOAKED. This build deliberately INVERTS the fish builds: primary SR 174210 'mixed species raw (may contain additives to retain moisture)' IS the treated retail class (protein 13.61 n=4, Na 566 n=4 range 508-642, K 113 leached, 134 nutrients, AA 12/12, analytical vitamins). ERROR-DIRECTION argument: an untreated-bag buyer feeds MORE protein/K/B1 than credited (safe for mins); storing untreated would overstate nutrition ~30% for the majority of buyers (unsafe). SR 175179 legacy untreated (protein 20.1, Na 119, K 264, n=3, 67 rows no AAs/vitamins) = the untreated REFERENCE, documented in comments, not adopted.
- note: FND 2684443 (2024, n=8 farm-raised peeled retail composites) is FRAME-MIXED - its own ranges prove it: Na 113-783 (mean 475), protein 12.06-21.25, K 33.8-331. Its means average treated+untreated bags and match NEITHER frame -> proximate/electrolyte rows REJECT to SR-pure-treated; its population-quality rows (iodine, retinol, B12, trace minerals) stand as modern measurements. Expect the machine to anchor foundation on shared rows - overrides to SR planned.
- note: MEASURED IODINE, THIRD FOOD: FND 13.64 ug (n=8, range 4.07-36.9); TDS 15149 raw corroborates (n=17, mean 14.2, range 4.1-38.5, vintages 2008/2016/2023 - the 2023 tranche likely INCLUDES the FND samples: partial-overlap corroboration, never independent; '(100327)' annotation is the ODS link). Shrimp is LOW-iodine (vs pollock 185.5 / cod 113.7) - zero max concern; also NOT the iodine vehicle.
- note: VIT A DEFECT PRE-REGISTERED: SR 180 IU / retinol 54 ug is BORROWED ('taken from another source'); FND MEASURED retinol 0.6478 ug (n=8, range 0-3.0) -> adopt ~2.2 IU (x3.33). Crustaceans store astaxanthin, not retinol; cats cannot convert carotenoids - species-correct honest near-zero (cod-3-IU pattern). Override any machine keep of 180.
- note: SR 174210 FA BRACKET INCOHERENCE PRE-REGISTERED: the FA means sit ~2x ABOVE their own n=4 ranges (EPA 0.068 vs 0.024-0.039; DHA 0.07 vs 0.025-0.039; ARA 0.034 vs 0.013-0.017; LA 0.095 vs 0.019-0.063) - mean-outside-range would trip the v7 bracket guard. DO NOT store those ranges; store FA values stat-less (or resolve provenance at review). PUFA total 0.295 calculated - check component-sum invariant at review (values, not ranges, must cohere).
- note: THIAMIN TRIPLE THREAT -> MANDATORY-COOK GUIDANCE (potato precedent, 2nd member): (1) crustaceans carry thiaminase (gadids do not) - COOK before serving; (2) avoid SULFITE bags entirely - sodium bisulfite/metabisulfite on the ingredient line destroys thiamin (the AU sulfite-pet-meat deficiency outbreaks); (3) shrimp is naturally B1-poor (treated SR 0.02 n=4). DOSING BASIS: RAW grams - weigh raw, then cook. COOK GENTLY (steam/light saute), never boil-and-drain: Spitze shows boiled shrimp taurine 11 vs raw 31-39 (solubles leach into discarded water; K/B-vits likewise).
- note: TAURINE: Spitze measured SHRIMP DIRECTLY (a first - no family estimate needed): raw freshwater de-shelled 31 mg/100g wet (n=2), medium 39 (n=1), cooked small 11 (boil leach); /10 wet-basis convention applied. Adopt ~35 raw. MYTH CHECK recorded: shrimp is NOT a taurine star - scallop 827/mussel 655/clam 520/squid 356 are; shrimp sits BELOW fish muscle (salmon 130, pollock-est 100). Role is palatability/variety, not taurine.
- note: SOAK CHEMISTRY of the stored frame: Na 566 (dip salt), K 113 (drip leach; untreated 264 - understatement is the SAFE direction for the binding K min), P 244 (STP is a phosphate; untreated 214 - stored HIGH = conservative for Ca:P, asymmetric doctrine aligned). Vit D 2 IU analytical n=5 range 0-6 = trace-honest (pollock pattern; marine invertebrate). Vit K 0.3 n=4 (fish-K rule pairs with K1 corrector in seafood-only recipes). Cholesterol 126 (cat-irrelevant, noted for label coherence checks).
- note: SPECIES MAP: EXACT L. vannamei = MEXT 10415 whiteleg raw (Japanese analysed - THE arbiter). Penaeid siblings: MEXT 10321 kuruma / 10329 giant tiger (cultured raw), FCDB 1548 tiger prawn aquaculture raw frozen (check for Danish stats), AFCD wild penaeids (F007433 generic 'Prawn, flesh, raw (green)' = Cl/I/biotin carrier candidate; F007422 banana / F007424 brown tiger / F007454 Western king wild raw), CoFID 16-387 'Prawns, king, raw' (UK warm-water farmed class, DH-2013 Cl/biotin carrier). BLS T753100 = Crangon crangon (DIFFERENT FAMILY Crangonidae, North Sea brown shrimp) - family-level caveat on any adoption. CIQUAL 10021 'Crevette, crue' + 10038 'surgelee, crue' generic species-unstated - PRESUMED USDA-COPY until the echo screen clears them (CIQUAL 26125 lesson).
- note: PROTEIN_SPECIES 'shrimp' (Shahab approved 2026-09-17, my recommendation accepted): new species added via egg-style migration 633c54b1219d (tuple + CHECK + user_interaction mirror; constant-sync tests). Mussel precedent - shellfish get their own species; 'fish' would have wrongly coupled shrimp to fish rotation/advisory logic. FORMULATOR PENDING (Shahab-side): learn 'shrimp' (icon + species logic), like the Animal Fat category.
- note: AA panel: SR 174210 carries 12/12 at protein 13.61 (internally coherent - AAs and protein share the treated frame). Gaps: taurine (Spitze literature above), Cl + biotin (CoFID/AFCD carriers), iodine (FND measured), choline 80.9 borrowed (expect usda_only keep).
- note: cv_intl: FCDB 1548 is species-sibling (monodon, not vannamei) -> expect NO FOOD_MAP entry (pollock-saithe precedent); still check its stats at review.

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| MEXT:10415 Crustacean, whiteleg shrimp, raw | Crustacean, whiteleg shrimp, raw - EXACT species (L. vannamei), Japanese analysed; the Pacific-white arbiter for every contested row; iodine/vitamin datapoints expected | independent (0/44 incidental matches) |
| CIQUAL:10021 Crevette, crue | Crevette, crue - generic raw; species unstated; PRESUMED-COPY until echo screen (26125 lesson) | independent (2/26 incidental matches) |
| CIQUAL:10038 Crevette, surgelée, crue | Crevette, surgelee, crue - frozen raw, closest to the IQF product; same presumed-copy caution | independent (0/11 incidental matches) |
| CoFID:16-387 Prawns, king, raw | Prawns, king, raw - UK warm-water farmed class (vannamei/monodon), DH-2013 program; the chloride + biotin carrier | independent (0/27 incidental matches) |
| AFCD:F007433 Prawn, flesh, raw (green) | Prawn, flesh, raw (green) - generic analysed AU composite; second Cl/I/biotin carrier; wild penaeids (banana/tiger/king) as family bracket | independent (3/32 incidental matches) |
| FCDB:1548 Tiger prawn, aquaculture, raw, frozen | Tiger prawn, aquaculture, raw, frozen - penaeid sibling (P. monodon), Danish; check for stats; sibling caveat on any adoption | independent (3/25 incidental matches) |
| BLS:T753100 Common shrimp raw | Common shrimp raw - Crangon crangon, DIFFERENT FAMILY (North Sea brown shrimp); family-level caveat; echo screen decides | independent (1/44 incidental matches) |
| IodineDB:NDB 15149 (100327) Crustaceans, shrimp, mixed species, raw | Crustaceans, shrimp, mixed species, raw - US TDS n=17 mean 14.2 (2008/2016/2023 vintages; 2023 tranche likely overlaps the FND samples - partial-overlap corroboration, never independent) | USDA-affiliated — evidence, never independent confirmation |
| Spitze03:Shrimp, freshwater de-shelled raw 310 mg/kg (n=2) + shrimp medium 390 mg/kg (n=1); cooked small 110 mg/kg shows boil leach | Direct Spitze same-item measurements (/10 wet-basis convention): raw pool 31-39 -> 35 adopted. First shellfish taurine from the canonical source, not a family estimate. Cooked-serving losses noted in guidance (steam, do not boil-and-drain) | no USDA overlap — independence not establishable |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | 15.5687‡ | 13.61 (n=4) | 20.7‡ | 18.6† | 19.7° / 23.4° | 17.6° | 15.6975 (n=12) | — | 19.6 | — | **confirm** |

## Amino Acid

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 1.342 | — | 1.74† | — | — | — | — | 1.8 | — | **review** |
| Histidine (1221) | g | — | 0.3 | — | 0.41† | — | — | — | — | 0.39 | — | **review** |
| Isoleucine (1212) | g | — | 0.627 | — | 1† | — | — | — | — | 0.77 | — | **confirm** |
| Leucine (1213) | g | — | 1.165 | — | 1.97† | — | — | — | — | 1.4 | — | **confirm** |
| Lysine (1214) | g | — | 1.297 | — | 2.02† | — | — | — | — | 1.6 | — | **confirm** |
| Methionine (1215) | g | — | 0.397 | — | 0.67† | — | — | — | — | 0.51 | — | **review** |
| Cystine (1216) | g | — | 0.162 | — | 0.31† | — | — | — | — | 0.22 | — | **review** |
| Phenylalanine (1217) | g | — | 0.593 | — | 0.88† | — | — | — | — | 0.76 | — | **review** |
| Tyrosine (1218) | g | — | 0.515 | — | 0.65† | — | — | — | — | 0.66 | — | **review** |
| Threonine (1211) | g | — | 0.54 | — | 0.85† | — | — | — | — | 0.71 | — | **review** |
| Tryptophan (1210) | g | — | 0.155 | 0.156‡ | 0.21† | — | — | — | — | 0.19 | — | **confirm** |
| Valine (1219) | g | — | 0.637 | — | 0.99† | — | — | — | — | 0.81 | — | **review** |
| Taurine (1234) | mg | — | — | — | — | — | — | — | — | — | 35 | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | 0.8013 (n=8) | 1.01 (n=4) | 0.8‡ | 1.44† | 0.84° / 0.9° | 0.7° | 0.6 (n=9) | — | 0.6 | — | **confirm** |

## Fatty Acid

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 0.095 (n=4) | 0.01‡ | 0.062417† | — | 0.06° | — | — | 0.047 | — | **review** |
| Arachidonic acid (1271) | g | — | 0.034 (n=4) | 0.04947‡ | 0.0675† | — | 0.02° | — | — | 0.013 | — | **review** |
| Alpha-linolenic acid (1270) | g | — | 0.006 (n=4) | 0‡ | 0.00771† | 0.0059° | 0 tr | — | — | 0.003 | — | **confirm** |
| EPA (1278) | g | — | 0.068 (n=4) | 0.06803‡ | 0.205933† | — | 0.06° | — | — | 0.036 | — | **confirm** |
| DHA (1272) | g | — | 0.07 (n=4) | 0.06085‡ | 0.159533† | — | 0.05° | — | — | 0.04 | — | **region_keep** |
| Fatty acids, total polyunsaturated (1293) | g | — | 0.295‡ | 0.21‡ | 0.5227‡ | — | 0.22° | 0.239 (n=1) | — | 0.15 | — | **confirm** |
| DPA 22:5 n-3 (1280) | g | — | 0.006 (n=4) | 0.00854‡ | 0.019617† | — | 0 tr | — | — | 0.002 | — | **confirm** |

## Mineral

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | 64.63 (n=8) | 54 (n=4) | 72‡ | 92† | 84.8° | 44° | 71.55 (n=2) | — | 68 | — | **confirm** |
| Phosphorus (1091) | mg | 190.6 (n=8) | 244 (n=4) | 317‡ | 224† | 195° | 155° | 199 (n=2) | — | 220 | — | **confirm** |
| Potassium (1092) | mg | 145.9 (n=8) | 113 (n=4) | 314‡ | 230† | 278° | 126° | 103.5 (n=2) | — | 270 | — | **confirm** |
| Sodium (1093) | mg | 474.9 (n=8) | 566 (n=4) | 345‡ | 146† | 182° / 240° | 215° | 412 (n=2) | — | 140 | — | **confirm** |
| Chloride (1088) | mg | — | — | 330‡ | 61† | — | 260° | 433.5 (n=2) | — | — | — | **adopt_foreign** |
| Magnesium (1090) | mg | 22.53 (n=8) | 22 (n=4) | 45‡ | 22.5† | 49.8° | 28° | 29.75 (n=2) | — | 37 | — | **confirm** |
| Iron (1089) | mg | 0.5223 (n=8) | 0.21 (n=4) | 0.16‡ | 0.605† | 3.21° | 0.7° | 0.575 (n=2) | — | 1.4 | — | **confirm** |
| Copper (1098) | mg | 0.2084 (n=8) | 0.182 (n=4) | 0.416‡ | 0.169† | 0.72° | 0.21° | 0.2185 (n=2) | — | 0.33 | — | **confirm** |
| Manganese (1101) | mg | 0.02866 (n=8) | 0.029 (n=4) | 0.013‡ | 0.03† | 0.17° | 0.04° | 0.0675 (n=2) | — | 0.1 | — | **review** |
| Zinc (1095) | mg | 0.9368 (n=8) | 0.97 (n=4) | 1.43‡ | 0.91† | 2.81° / 0.9° | 1.2° | 0.97 (n=2) | — | 1.2 | — | **confirm** |
| Iodine (1100) | µg | 13.64 (n=8) | — | 57.2‡ | 90.5† | 120° | 5° | 26.5 (n=2) | 14.2 (n=17) | 10 | — | **region_keep** |
| Selenium (1103) | µg | 19.48 (n=8) | 29.6 (n=4) | 43.7‡ | — | 34° | 34° | 29.5 (n=2) | — | 27 | — | **region_keep** |

## Vitamin

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | 2.15717 (n=8) | 179.82‡ | 3.33‡ | 7.659† | 6.66° | 0 tr | 0 (n=2) | — | 0 | — | **region_keep** |
| Vitamin D (1110) | IU | — | 2 (n=5) | 0.4‡ | — | 8< | 0 tr | 0‡ | — | 0 | — | **region_keep** |
| Vitamin E (1109) | IU | — | 1.9668 (n=4) | 2.384‡ | 2.1903† | — | 2.682° | 1.70605 (n=2) | — | 2.533 | — | **confirm** |
| Vitamin K (1185) | µg | — | 0.3 (n=4) | — | 0.1‡ | — | — | — | — | 0~ | — | **confirm** |
| Thiamin (1165) | mg | — | 0.02 (n=4) | 0‡ | 0.051† | 0.035° | 0 tr | 0.03 (n=2) | — | 0.02661 | — | **confirm** |
| Riboflavin (1166) | mg | — | 0.015 (n=4) | 0.06‡ | 0.034† | 0.03° / 0.02° | 0.05° | 0.025 (n=2) | — | 0.04 | — | **confirm** |
| Niacin (1167) | mg | — | 1.778 (n=4) | 2.8‡ | 2.43† | 3.2° | 0.1° | 1.55 (n=2) | — | 3.6 | — | **confirm** |
| Pantothenic acid (1170) | mg | — | 0.31 (n=2) | 0.37‡ | 0.08† | 0.37° | 0.16° | 0.22 (n=2) | — | 0.23 | — | **confirm** |
| Pyridoxine (1175) | mg | — | 0.161 (n=4) | 0.34‡ | 0.13† | 0.15° / 0.07° | 0.11° | 0.0865 (n=2) | — | 0.14 | — | **confirm** |
| Folic acid (1177) | µg | — | 19 (n=4) | 16‡ | 11.988† | 19° / 13° | 11° | — | — | 38 | — | **confirm** |
| Cobalamin (1178) | µg | 0.9963 (n=8) | 1.11 (n=4) | 1‡ | 1.71† | 1° | 1.3° | 1.395 (n=2) | — | 1.2 | — | **confirm** |
| Biotin (1176) | µg | — | — | — | 1† | — | 3.9° | 1.055 (n=2) | — | 1.9 | — | **adopt_foreign** |
| Choline (1180) | mg | — | 80.9? | — | — | — | — | 80.9† (n=1) | — | — | — | **usda_only** |

## Other

| nutrient | unit | FND | SR | AFCD | BLS | CIQUAL | CoFID | FCDB | IodineDB | MEXT | Spitze03 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 71‡ | 91.0612‡ | 87‡ | 99‡ / 105‡ | 77° | 68.19‡ | — | 91‡ | — | **confirm** |
| Water (1051) | g | 81.28 (n=8) | 83.01 (n=4) | 76.8‡ | 78.4† | 74.3° | 81.9° | 81.9417 (n=12) | — | 78.6 | — | **confirm** |
| Ash (1007) | g | 1.865 (n=8) | 1.86 (n=4) | 2‡ | 1.38† | 1.99° / 1.84° | — | 1.76083 (n=12) | — | 1.3 | — | **confirm** |
| Crude Fiber (1079) | g | — | 0† | 0‡ | 0‡ | 0° / 0.5< | 0° | 0 | — | 0~ | — | **confirm** |
| Carbohydrate (1005) | g | 0.48495‡ | 0.91‡ | 0‡ | 0‡ | 3.21° / 0.74° | — | 0‡ | — | 0.7 | — | **review** |

## Needs attention (contested rows + detection-limit context)

### Arginine (1220) — review
- all 1 independent(s) differ >±20% from sr_legacy 1.342: MEXT 1.8
- suggestion: 1.342 g (source `sr_legacy`)
  - MEXT [analysed] 1.8 — ARG (AA volume, per 100 g EP)
  - BLS [borrowed] 1.74 — ARG [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Histidine (1221) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.3: MEXT 0.39
- suggestion: 0.3 g (source `sr_legacy`)
  - MEXT [analysed] 0.39 — HIS (AA volume, per 100 g EP)
  - BLS [borrowed] 0.41 — HIS [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Methionine (1215) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.397: MEXT 0.51
- suggestion: 0.397 g (source `sr_legacy`)
  - MEXT [analysed] 0.51 — MET (AA volume, per 100 g EP)
  - BLS [borrowed] 0.67 — MET [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Cystine (1216) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.162: MEXT 0.22
- suggestion: 0.162 g (source `sr_legacy`)
  - MEXT [analysed] 0.22 — CYS (AA volume, per 100 g EP)
  - BLS [borrowed] 0.31 — CYSTE [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Phenylalanine (1217) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.593: MEXT 0.76
- suggestion: 0.593 g (source `sr_legacy`)
  - MEXT [analysed] 0.76 — PHE (AA volume, per 100 g EP)
  - BLS [borrowed] 0.88 — PHE [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Tyrosine (1218) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.515: MEXT 0.66
- suggestion: 0.515 g (source `sr_legacy`)
  - MEXT [analysed] 0.66 — TYR (AA volume, per 100 g EP)
  - BLS [borrowed] 0.65 — TYR [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Threonine (1211) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.54: MEXT 0.71
- suggestion: 0.54 g (source `sr_legacy`)
  - MEXT [analysed] 0.71 — THR (AA volume, per 100 g EP)
  - BLS [borrowed] 0.85 — THR [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Valine (1219) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.637: MEXT 0.81
- suggestion: 0.637 g (source `sr_legacy`)
  - MEXT [analysed] 0.81 — VAL (AA volume, per 100 g EP)
  - BLS [borrowed] 0.99 — VAL [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Taurine (1234) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 35 mg (source `literature`)
  - Spitze03 [analysed] 35 — Direct Spitze same-item measurements (/10 wet-basis convention): raw pool 31-39 -> 35 adopted. First shellfish taurine f

### Linoleic acid (1269) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.095: MEXT 0.047, CoFID 0.06
- suggestion: 0.095 g (source `sr_legacy`)
  - MEXT [analysed] 0.047 — F18D2N6 (FA volume, per 100 g EP)
  - CoFID [compiled] 0.06 — cis n-6 C18:2; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0.01 — C18:2w6; food-level derivation: Recipe
  - BLS [borrowed] 0.062417 — F18:2CN6 [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Arachidonic acid (1271) — review
- all 2 independent(s) differ >±20% from sr_legacy 0.034: MEXT 0.013, CoFID 0.02
- suggestion: 0.034 g (source `sr_legacy`)
  - MEXT [analysed] 0.013 — F20D4N6 (FA volume, per 100 g EP)
  - CoFID [compiled] 0.02 — cis n-6 C20:4; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0.04947 — C20:4w6; food-level derivation: Recipe
  - BLS [borrowed] 0.0675 — F20:4CN6 [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Alpha-linolenic acid (1270) — confirm
- 2/2 independent(s) within ±20%: MEXT 0.003, CIQUAL 0.0059
- detection-limit info: CoFID trace
- suggestion: 0.006 g (source `sr_legacy`)
  - MEXT [analysed] 0.003 — F18D3N3 (FA volume, per 100 g EP)
  - CIQUAL [compiled] 0.0059 — AG 18:3
  - CoFID [trace] 0 — cis n-3 C18:3; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0 — C18:3w3; food-level derivation: Recipe
  - BLS [borrowed] 0.00771 — F18:3CN3 [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### DHA (1272) — region_keep
- region-sensitive; foreign cluster differs: MEXT 0.04, CoFID 0.05 — US mean kept unless defective
- suggestion: 0.07 g (source `sr_legacy`)
  - MEXT [analysed] 0.04 — F22D6N3 (FA volume, per 100 g EP)
  - CoFID [compiled] 0.05 — cis n-3 C22:6; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0.06085 — C22:6w3; food-level derivation: Recipe
  - BLS [borrowed] 0.159533 — F22:6CN3 [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### DPA 22:5 n-3 (1280) — confirm
- 1/1 independent(s) within ±20%: MEXT 0.002
- detection-limit info: CoFID trace
- suggestion: 0.006 g (source `sr_legacy`)
  - MEXT [analysed] 0.002 — F22D5N3 (FA volume, per 100 g EP)
  - CoFID [trace] 0 — cis n-3 C22:5; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0.00854 — C22:5w3; food-level derivation: Recipe
  - BLS [borrowed] 0.019617 — F22:5CN3 [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Chloride (1088) — adopt_foreign
- no USDA value; 2 measured source(s) available
- anchor is a tie-break between split sources — review must arbitrate
- suggestion: 433.5 mg (source `literature`)
  - CoFID [compiled] 260 — Chloride; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 330 — Chloride; food-level derivation: Recipe
  - FCDB [analysed] 433.5 — Chloride; src [2068] Fish and fish products - Determination of nutrient content (2015)
  - BLS [borrowed] 61 — CLD [Übernommener Wert] -

### Manganese (1101) — review
- all 4 independent(s) differ >±20% from foundation 0.02866: MEXT 0.1, CIQUAL 0.17, CoFID 0.04, FCDB 0.0675 (n=2)
- suggestion: 0.02866 mg (source `foundation`)
  - MEXT [analysed] 0.1 — MN (main volume)
  - CIQUAL [compiled] 0.17 — Manganèse
  - CoFID [compiled] 0.04 — Manganese; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0.013 — Manganese; food-level derivation: Recipe
  - FCDB [analysed] 0.0675 — Manganese; src [2068] Fish and fish products - Determination of nutrient content (2015)
  - BLS [borrowed] 0.03 — MN [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Iodine (1100) — region_keep
- region-sensitive; foreign cluster differs: MEXT 10, CIQUAL 120, CoFID 5, FCDB 26.5 (n=2) — US mean kept unless defective
- suggestion: 13.64 µg (source `foundation`)
  - MEXT [analysed] 10 — ID (main volume)
  - CIQUAL [compiled] 120 — Iode
  - CoFID [compiled] 5 — Iodine; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 57.2 — Iodine; food-level derivation: Recipe
  - FCDB [analysed] 26.5 — Iodine; src [2068] Fish and fish products - Determination of nutrient content (2015)
  - BLS [borrowed] 90.5 — ID [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - IodineDB [analysed] 14.2 — Iodine DB R4; SD=11.1

### Selenium (1103) — region_keep
- region-sensitive; foreign cluster differs: MEXT 27, CIQUAL 34, CoFID 34, FCDB 29.5 (n=2) — US mean kept unless defective
- suggestion: 19.48 µg (source `foundation`)
  - MEXT [analysed] 27 — SE (main volume)
  - CIQUAL [compiled] 34 — Sélénium
  - CoFID [compiled] 34 — Selenium; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 43.7 — Selenium; food-level derivation: Recipe
  - FCDB [analysed] 29.5 — Selenium; src [2068] Fish and fish products - Determination of nutrient content (2015)

### Vitamin A (1106) — region_keep
- region-sensitive; foreign cluster differs: MEXT 0, CIQUAL 6.66, FCDB 0 (n=2) — US mean kept unless defective
- detection-limit info: CoFID trace
- suggestion: 2.15717 IU (source `foundation`)
  - MEXT [analysed] 0 — RETOL (main volume)
  - CIQUAL [compiled] 6.66 — Rétinol
  - CoFID [trace] 0 — Retinol; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 3.33 — Retinol (preformed); food-level derivation: Recipe
  - FCDB [analysed] 0 — Retinol; src [2068] Fish and fish products - Determination of nutrient content (2015)
  - BLS [borrowed] 7.659 — RETOL [Nährstoffdatenbank] Converted value from: Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzu

### Vitamin D (1110) — region_keep
- region-sensitive; foreign cluster differs: MEXT 0 — US mean kept unless defective
- detection-limit info: CIQUAL <= 8, CoFID trace
- suggestion: 2 IU (source `sr_legacy`)
  - MEXT [analysed] 0 — VITD (main volume)
  - CIQUAL [censored] 8 — Vitamine D
  - CoFID [trace] 0 — Vitamin D; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0.4 — Vitamin D3 equivalents; food-level derivation: Recipe
  - FCDB [computed] 0 — Vitamin D; src [1003] Value calculated by converting various analytical data

### Thiamin (1165) — confirm
- 2/3 independent(s) within ±20%: MEXT 0.02661, FCDB 0.03 (n=2)
- detection-limit info: CoFID trace
- suggestion: 0.02 mg (source `sr_legacy`)
  - MEXT [analysed] 0.02661 — THIAHCL 0.03 x0.887 (HCl->thiamin base)
  - CIQUAL [compiled] 0.035 — B1
  - CoFID [trace] 0 — Thiamin; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0 — Thiamin; food-level derivation: Recipe
  - FCDB [analysed] 0.03 — Thiamin (Vitamin B1); src [2068] Fish and fish products - Determination of nutrient content (2015)
  - BLS [borrowed] 0.051 — THIA [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Biotin (1176) — adopt_foreign
- no USDA value; 3 measured source(s) available
- suggestion: 1.9 µg (source `literature`)
  - MEXT [analysed] 1.9 — BIOT (main volume)
  - CoFID [compiled] 3.9 — Biotin; refs: DH, Nutrient analysis of fish and fish products, 2013
  - FCDB [analysed] 1.055 — Biotin; src [2068] Fish and fish products - Determination of nutrient content (2015)
  - BLS [borrowed] 1 — BIOT [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Crude Fiber (1079) — confirm
- 4/4 independent(s) within ±20%: MEXT 0, CIQUAL 0, CoFID 0, FCDB 0
- detection-limit info: CIQUAL <= 0.5
- suggestion: 0 g (source `sr_legacy`)
  - MEXT [estimated] 0 — FIBTG (main volume)
  - CIQUAL [compiled] 0 — Fibres
  - CIQUAL [censored] 0.5 — Fibres
  - CoFID [compiled] 0 — AOAC fibre; refs: DH, Nutrient analysis of fish and fish products, 2013
  - AFCD [computed] 0 — Total dietary fibre; food-level derivation: Recipe
  - FCDB [analysed] 0 — Dietary fibre; src [1655] Natural zero value for content. Not analyzed
  - BLS [computed] 0 — FIBT [Logische Null] -

### Carbohydrate (1005) — review
- all 3 independent(s) differ >±20% from foundation 0.48495: MEXT 0.7, CIQUAL 3.21, CIQUAL 0.74
- suggestion: 0.48495 g (source `foundation`)
  - MEXT [analysed] 0.7 — Carbohydrate, total (main volume)
  - CIQUAL [compiled] 3.21 — Glucides
  - CIQUAL [compiled] 0.74 — Glucides
  - AFCD [computed] 0 — Available carbohydrate w/o sugar alcohols; food-level derivation: Recipe
  - FCDB [computed] 0 — Carbohydrate by difference; src [1003] Value calculated by converting various analytical data
  - BLS [computed] 0 — CHO [Formelberechnung] -

## Verdict summary

- confirm: 31
- review: 12
- region_keep: 5
- adopt_foreign: 3
- usda_only: 1
