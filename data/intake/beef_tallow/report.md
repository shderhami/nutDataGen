# Intake report: beef tallow

- generated: 2026-09-06  |  spec: `data/intake/beef_tallow.json`
- Foundation FDC: —  |  SR Legacy FDC: 171400
- category: Fish Oil  |  per 100.0 g
- engine: agreement ±20% (abs floors: g 0.01, mg 0.01, µg 1, IU 1, kcal 6); echo <0.5% at ≥5 matches and ≥40% of comparables
- note: price_per_unit 0.0353/g confirmed by Shahab 2026-09-06 (Kettle & Fire 14 oz, $14.00/397 g).
- note: PURPOSE (methionine-diluent search 2026-09-06): the catalogue's Met-zero energy diluent - replacing 10% of a recipe's ME with tallow cuts Met/1000 kcal by ~10% while adding only ~0.34 g LA/1000 kcal. Chosen over butter (community/perception: universal 'vets say avoid' surface messaging despite sound formulated-dose science) and over lard/poultry fats (LA 11-22/1000 kcal defeats the purpose).
- note: LINKED PRODUCT: Kettle & Fire 100% Grass-Fed Beef Tallow, 14 oz glass jar (ASIN B0FY7KCKTY) - the only candidate passing ALL checks: PHOTOGRAPHED single-ingredient label ('GRASS-FED AND GRASS-FINISHED BEEF TALLOW'), label panel corroborates SR 171400 to the rounding digit (929 vs 902 kcal, 50% vs 49.8% SFA, protein/Na/carb 0), durable brand. Customer guidance must say PLAIN tallow only - seasoned/garlic-infused tallows exist and allium is toxic to cats.
- note: FRAME NOTE (documented deviation, NZ-lamb pattern): SR 171400 is conventional US commodity tallow; the linked product is grass-fed/finished - LA mildly overstated by SR (~3.1 vs ~2-2.5 grass), ALA/vit E mildly understated. Immaterial at diluent doses (~0.1 g LA per 1000-kcal batch); direction favorable for the LA concern.
- note: REJECTED CANDIDATE forensics (ConsumerLab lesson applied to fat): Herd Beef Tallow ($9.98) disqualified on REPRODUCED label anomalies - jar and manufacturer site agree on ~35-38% SFA (pure beef tallow is ~50%; blend/bad-lab territory), three-way calorie drift across their own materials (110/115/120 per tbsp), fat 92% on the jar, cholesterol %DV arithmetic error, 'vitamins A D E K present' beside a panel declaring vit D 0. No stable signal to anchor an entry (unlike the NuNaturals %DV-invariance rescue).
- note: CATEGORY FLAG for Shahab: no 'Fat' category exists; 'Fish Oil' chosen because it maps to ingredient_class fat_oil (the correct CV pool + supplement-tier delivered floors for manufactured fats). The category NAME is wrong-looking for tallow - if the sibling repo displays it customer-facing, consider a rename/alias there.
- note: SR-only food (no Foundation tallow; suet 170193 exists as the raw-frame relative). SR 171400 panel: 90 nutrients, fat 100, vit E 2.7, vit D 28 IU, choline 79.8, Se 0.2, full FA panel, and EXPLICIT zeros for protein/minerals - so all AA rows are true biological zeros (rendered fat, protein 0.0).
- note: Missing-from-SR gap set (Cl, I, Mn, biotin, taurine): expect BLS/FCDB/MEXT to supply trace-or-zero values; taurine carried as a biological-zero literature row (no protein = no free AAs).

## Matched sources

| source food | frame note | independence screen |
|---|---|---|
| FCDB:1455 Fat, beef tallow | Fat, beef tallow - Danish; check for stats and echo status (FCDB fat entries are often Souci/USDA borrows) | independent (1/9 incidental matches) |
| BLS:Q890000 Beef tallow/fat | Beef tallow/fat - German Q-class rendered animal fat; chloride/iodine carrier expected; mutton tallow Q880000 is the sibling bracket, not included | independent (0/6 incidental matches) |
| MEXT:14015 Beef tallow | Beef tallow - Japanese analytical; total-K carrier and the only likely analysed independent; fats chapter (14xxx) | independent (1/6 incidental matches) |
| Biological:Rendered fat, protein 0.0 (SR-measured) | Taurine is a free amino acid; a rendered fat with SR-measured protein 0.0 carries none. Biological zero, same class as the plant-zero convention. | no USDA overlap — independence not establishable |

_value marks: † borrowed  ° compiled  ‡ computed  ~ estimated  < censored upper bound  tr trace  ≈ echo of USDA  ? unknown origin; (n=x) sample count_

## Protein

| nutrient | unit | FND | SR | BLS | Biological | FCDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|
| Crude Protein (1003) | g | — | 0? | 0.425† | — | 5 (n=2) | 0.2 | **review** |

## Amino Acid

| nutrient | unit | FND | SR | BLS | Biological | FCDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|
| Arginine (1220) | g | — | 0? | 0.023‡ | — | 0.272 | — | **review** |
| Histidine (1221) | g | — | 0? | 0.011‡ | — | 0.128 | — | **review** |
| Isoleucine (1212) | g | — | 0? | 0.013‡ | — | 0.152 | — | **review** |
| Leucine (1213) | g | — | 0? | 0.025‡ | — | 0.296 | — | **review** |
| Lysine (1214) | g | — | 0? | 0.029‡ | — | 0.336 | — | **review** |
| Methionine (1215) | g | — | 0? | 0.004‡ | — | 0.044 | — | **review** |
| Cystine (1216) | g | — | 0? | 0.003‡ | — | 0.036 | — | **review** |
| Phenylalanine (1217) | g | — | 0? | 0.016‡ | — | 0.184 | — | **review** |
| Tyrosine (1218) | g | — | 0? | 0.009‡ | — | 0.104 | — | **review** |
| Threonine (1211) | g | — | 0? | 0.012‡ | — | 0.136 | — | **review** |
| Tryptophan (1210) | g | — | 0? | 0.01‡ | — | 0.112 | — | **review** |
| Valine (1219) | g | — | 0? | 0.018‡ | — | 0.216 | — | **review** |
| Taurine (1234) | mg | — | — | — | 0 | — | — | **adopt_foreign** |

## Fat

| nutrient | unit | FND | SR | BLS | Biological | FCDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|
| Total Fat (1004) | g | — | 100? | 99.5† | — | 95‡ | 99.8 | **confirm** |

## Fatty Acid

| nutrient | unit | FND | SR | BLS | Biological | FCDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|
| Linoleic acid (1269) | g | — | 3.1 (n=15) | 2.516† | — | 3.03628† (n=15) | 3.3 | **confirm** |
| Arachidonic acid (1271) | g | — | 0? | 0.24† | — | 0† | 0 | **confirm** |
| Alpha-linolenic acid (1270) | g | — | 0.6 (n=9) | 0.4395† | — | 0.588667† (n=9) | 0.17 | **review** |
| EPA (1278) | g | — | 0? | — | — | 0† | 0 | **confirm** |
| DHA (1272) | g | — | 0? | — | — | 0† | 0 | **confirm** |
| Fatty acids, total polyunsaturated (1293) | g | — | 4? | 3.196‡ | — | 3.62495‡ | 3.61 | **confirm** |
| DPA 22:5 n-3 (1280) | g | — | 0? | — | — | 0† | 0 | **confirm** |

## Mineral

| nutrient | unit | FND | SR | BLS | Biological | FCDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|
| Calcium (1087) | mg | — | 0? | — | — | 0† | 0 tr | **usda_only** |
| Phosphorus (1091) | mg | — | 0? | 7† | — | 0† | 1 | **review** |
| Potassium (1092) | mg | — | 0 (n=1) | 6† | — | 0† (n=1) | 1 | **review** |
| Sodium (1093) | mg | — | 0 (n=1) | 10† | — | 0† (n=1) | 1 | **review** |
| Chloride (1088) | mg | — | — | — | — | — | — | **no_evidence** |
| Magnesium (1090) | mg | — | 0? | — | — | 0† | 0 | **confirm** |
| Iron (1089) | mg | — | 0? | 0.32† | — | 0† | 0.1 | **review** |
| Copper (1098) | mg | — | 0? | — | — | — | 0 tr | **usda_only** |
| Manganese (1101) | mg | — | — | 0.001† | — | — | — | **review** |
| Zinc (1095) | mg | — | 0? | — | — | 0† | 0 tr | **usda_only** |
| Iodine (1100) | µg | — | — | — | — | 0† (n=1) | — | **review** |
| Selenium (1103) | µg | — | 0.2† | — | — | 1† (n=1) | — | **usda_only** |

## Vitamin

| nutrient | unit | FND | SR | BLS | Biological | FCDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|
| Vitamin A (1106) | IU | — | 0? | 732.6† | — | 63.27† (n=1) | 283.05 | **region_keep** |
| Vitamin D (1110) | IU | — | 28? | — | — | 92‡ | 0 | **region_keep** |
| Vitamin E (1109) | IU | — | 4.023 (n=1) | 1.937† | — | 1.639‡ (n=3) | 0.894 | **region_keep** |
| Vitamin K (1185) | µg | — | 0† | 5‡ | — | 0‡ | 26 | **replace_suggest** |
| Thiamin (1165) | mg | — | 0? | — | — | 0† | 0 | **confirm** |
| Riboflavin (1166) | mg | — | 0? | — | — | 0† | 0 | **confirm** |
| Niacin (1167) | mg | — | 0? | — | — | 0† | 0 | **confirm** |
| Pantothenic acid (1170) | mg | — | 0? | — | — | 0† | — | **usda_only** |
| Pyridoxine (1175) | mg | — | 0? | — | — | 0† | — | **usda_only** |
| Folic acid (1177) | µg | — | 0? | — | — | 0† | — | **usda_only** |
| Cobalamin (1178) | µg | — | 0? | — | — | 0† | — | **usda_only** |
| Biotin (1176) | µg | — | — | — | — | — | — | **no_evidence** |
| Choline (1180) | mg | — | 79.8† | — | — | 79.8† (n=1) | — | **usda_only** |

## Other

| nutrient | unit | FND | SR | BLS | Biological | FCDB | MEXT | verdict |
|---|---|---|---|---|---|---|---|---|
| Energy (1008) | kcal | — | 902‡ | 897‡ | — | 875‡ | 940‡ | **usda_only** |
| Water (1051) | g | — | 0? | 0 tr | — | 0† | 0 tr | **usda_only** |
| Ash (1007) | g | — | 0? | 0.07† | — | 0† | 0 | **confirm** |
| Crude Fiber (1079) | g | — | 0? | 0‡ | — | 0 | 0 | **confirm** |
| Carbohydrate (1005) | g | — | 0? | 0‡ | — | 0‡ | 0 | **confirm** |

## Needs attention (contested rows + detection-limit context)

### Crude Protein (1003) — review
- all 2 independent(s) differ >±20% from sr_legacy 0: FCDB 5 (n=2), MEXT 0.2
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 5 — Protein; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, conver
  - BLS [borrowed] 0.425 — PROT625 [Literatur] Converted value from: Scherz H.; Milch, Milchprodukte, Käse, Eier, Fette, Öle (M
  - MEXT [analysed] 0.2 — Protein, calculated from reference (main volume)

### Arginine (1220) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.272
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.272 — Arginine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, conve
  - BLS [computed] 0.023 — ARG [Musterberechnung] -

### Histidine (1221) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.128
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.128 — Histidine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, conv
  - BLS [computed] 0.011 — HIS [Musterberechnung] -

### Isoleucine (1212) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.152
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.152 — Isoleucine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, con
  - BLS [computed] 0.013 — ILE [Musterberechnung] -

### Leucine (1213) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.296
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.296 — Leucine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, conver
  - BLS [computed] 0.025 — LEU [Musterberechnung] -

### Lysine (1214) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.336
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.336 — Lysine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, convert
  - BLS [computed] 0.029 — LYS [Musterberechnung] -

### Methionine (1215) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.044
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.044 — Methionine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, con
  - BLS [computed] 0.004 — MET [Musterberechnung] -

### Cystine (1216) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.036
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.036 — Cystine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, conver
  - BLS [computed] 0.003 — CYSTE [Musterberechnung] -

### Phenylalanine (1217) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.184
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.184 — Phenylalanine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, 
  - BLS [computed] 0.016 — PHE [Musterberechnung] -

### Tyrosine (1218) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.104
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.104 — Tyrosine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, conve
  - BLS [computed] 0.009 — TYR [Musterberechnung] -

### Threonine (1211) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.136
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.136 — Threonine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, conv
  - BLS [computed] 0.012 — THR [Musterberechnung] -

### Tryptophan (1210) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.112
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.112 — Tryptophan; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, con
  - BLS [computed] 0.01 — TRP [Musterberechnung] -

### Valine (1219) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: FCDB 0.216
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [analysed] 0.216 — Valine; src [1059] The amino acid content of Danish foods. Supplement with average values ​​for groups of foods, convert
  - BLS [computed] 0.018 — VAL [Musterberechnung] -

### Taurine (1234) — adopt_foreign
- no USDA value; 1 measured source(s) available
- suggestion: 0 mg (source `literature`)
  - Biological [analysed] 0 — Taurine is a free amino acid; a rendered fat with SR-measured protein 0.0 carries none. Biological zero, same class as t

### Alpha-linolenic acid (1270) — review
- all 1 independent(s) differ >±20% from sr_legacy 0.6: MEXT 0.17
- suggestion: 0.6 g (source `sr_legacy`)
  - FCDB [borrowed] 0.588667 — C18:3,n-3; src [1342] USDA Table for Standard Reference (1976)
  - BLS [borrowed] 0.4395 — F18:3CN3 [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.17 — F18D3N3 (FA volume, per 100 g EP)

### Calcium (1087) — usda_only
- no independent foreign value
- detection-limit info: MEXT trace
- suggestion: 0 mg (source `sr_legacy`)
  - FCDB [borrowed] 0 — Calcium; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - MEXT [trace] 0 — CA (main volume)

### Phosphorus (1091) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: MEXT 1
- suggestion: 0 mg (source `sr_legacy`)
  - FCDB [borrowed] 0 — Phosphorus; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - BLS [borrowed] 7 — P [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 1 — P (main volume)

### Potassium (1092) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: MEXT 1
- suggestion: 0 mg (source `sr_legacy`)
  - FCDB [borrowed] 0 — Potassium; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - BLS [borrowed] 6 — K [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 1 — K (main volume)

### Sodium (1093) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: MEXT 1
- suggestion: 0 mg (source `sr_legacy`)
  - FCDB [borrowed] 0 — Sodium; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - BLS [borrowed] 10 — NA [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 1 — NA (main volume)

### Chloride (1088) — no_evidence
- no measurement in any local resource — operator/literature call

### Iron (1089) — review
- all 1 independent(s) differ >±20% from sr_legacy 0: MEXT 0.1
- suggestion: 0 mg (source `sr_legacy`)
  - FCDB [borrowed] 0 — Iron; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - BLS [borrowed] 0.32 — FE [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.1 — FE (main volume)

### Copper (1098) — usda_only
- no independent foreign value
- detection-limit info: MEXT trace
- suggestion: 0 mg (source `sr_legacy`)
  - MEXT [trace] 0 — CU (main volume)

### Manganese (1101) — review
- no USDA value and no measured foreign value (only borrowed) — operator/literature call
  - BLS [borrowed] 0.001 — MN [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -

### Zinc (1095) — usda_only
- no independent foreign value
- detection-limit info: MEXT trace
- suggestion: 0 mg (source `sr_legacy`)
  - FCDB [borrowed] 0 — Zinc; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - MEXT [trace] 0 — ZN (main volume)

### Iodine (1100) — review
- no USDA value and no measured foreign value (only borrowed) — operator/literature call
  - FCDB [borrowed] 0 — Iodine; src [2136] The Norwegian Food Composition Table 2017 (2017)

### Vitamin A (1106) — region_keep
- region-sensitive; foreign cluster differs: MEXT 283.05 — US mean kept unless defective
- suggestion: 0 IU (source `sr_legacy`)
  - FCDB [borrowed] 63.27 — Retinol; src [2284] The Swedish Food Composition Database, Version 2025-06-09 (2025)
  - BLS [borrowed] 732.6 — RETOL [Nährstoffdatenbank] Converted value from: Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzu
  - MEXT [analysed] 283.05 — RETOL (main volume)

### Vitamin D (1110) — region_keep
- region-sensitive; foreign cluster differs: MEXT 0 — US mean kept unless defective
- suggestion: 28 IU (source `sr_legacy`)
  - FCDB [computed] 92 — Vitamin D; src [1003] Value calculated by converting various analytical data
  - MEXT [analysed] 0 — VITD (main volume)

### Vitamin E (1109) — region_keep
- region-sensitive; foreign cluster differs: MEXT 0.894 — US mean kept unless defective
- suggestion: 4.023 IU (source `sr_legacy`)
  - FCDB [computed] 1.639 — alpha-Tocopherol; src [1034] Vitamin E content of Danish foods, as well as approximate calculation of the vitamin E supp
  - BLS [borrowed] 1.937 — TOCPHA [Nährstoffdatenbank] Kirchhoff, E; Souci - Fachmann - Kraut - Die Zusammensetzung der Lebensmittel -
  - MEXT [analysed] 0.894 — TOCPHA (main volume)

### Vitamin K (1185) — replace_suggest
- USDA zero is assumed/borrowed (deriv Z: Assumed zero (Insignificant amount or not naturally) but 1 independent(s) measure nonzero
- suggestion: 26 µg (source `literature`)
  - FCDB [computed] 0 — Vitamin K; src [1003] Value calculated by converting various analytical data
  - BLS [computed] 5 — VITK [Formelberechnung] -; VITK1=1µg, VITK2=4µg
  - MEXT [analysed] 26 — VITK (main volume); menaquinone-inclusive total K

### Biotin (1176) — no_evidence
- no measurement in any local resource — operator/literature call

### Water (1051) — usda_only
- no independent foreign value
- detection-limit info: BLS trace, MEXT trace
- suggestion: 0 g (source `sr_legacy`)
  - FCDB [borrowed] 0 — Water; src [1938] USDA National Nutrient Database for Standard Reference, Release 20 (2007)
  - BLS [trace] 0 — WATER [Spuren] -
  - MEXT [trace] 0 — WATER (main volume)

## Verdict summary

- review: 20
- confirm: 14
- usda_only: 11
- region_keep: 3
- no_evidence: 2
- adopt_foreign: 1
- replace_suggest: 1
