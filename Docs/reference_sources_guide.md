# Reference sources guide for AI-validation cross-checks

How to use the local reference datasets to verify AI-validator suggestions.
Written for the in-session agent driving the interactive ingredient-add
workflow, and for anyone auditing a stored `ingredient_nutrients` value.

The AI validator (`ai_validation.py`) asks the Claude API to confirm or revise
a USDA value and to cite sources (MEXT, CoFID, AFCD, BLS, Danish DTU, NEVO,
CIQUAL, NRC, literature). Those citations come from model knowledge and MUST be
verified against the local copies below before a non-USDA value is accepted —
see the memory rule "validate AI suggestions independently". Every dataset
listed here was content-verified on download (2026-08-11); provenance, SHA-256
prefixes and restore URLs live in `../data/README.md`.

## Source inventory

| Path | Source (version) | Independent of USDA? | Best for |
|---|---|---|---|
| `data/usda_bulk/` | USDA SR Legacy + Foundation + SR28 | — (it IS the source under test) | Baseline values, peer medians, SR28 standard errors |
| `data/fcdb_dk/` | Danish FCDB 6.1, 2026 (ex-Frida, DTU) | Yes — Danish analytical, per-value source + n | **Choline (only independent source)**, biotin, iodine, chloride, vit D forms, K1/K2, ARA/EPA/DPA/DHA, amino acids |
| `data/bls_de/` | German BLS 4.0, 2025 (MRI) | Mostly — check the per-value origin column | Iodide, chloride, biotin, vit D/K, ARA/EPA/DHA, amino acids; 7,140 foods |
| `data/mext_jp/` | Japan MEXT Standard Tables 2015 EN (3 volumes) | Yes — fully Japanese analytical | Iodine, selenium, biotin, vit K; fish and organ meats; AA + FA volumes |
| `data/fao_infoods/uFiSh1.0.xlsx` | FAO/INFOODS uFiSh 1.0 | Yes — global analytical compilation | Raw fish/shellfish: Atlantic salmon (farmed, raw), Nile tilapia, blue mussel; iodine, Se, AAs, full FA profiles |
| `data/ciqual_fr/` | CIQUAL 2025 FR + 2020 EN (ANSES) | Largely — French analytical/TDS | Chloride, iodine, D2/D3, K1/K2, ARA/EPA/DHA |
| `data/afcd_au/` | Australian AFCD Release 3, 2025 (FSANZ) | Yes — Australian analytical programs | Iodine, biotin, chloride, Se, amino acids, FAs; `Derivation` column flags "analysed" rows |
| `data/usda_iodine/` | USDA/FDA/ODS-NIH Iodine DB R4 (2024) | No (USDA-affiliated) — but analytical values absent from FDC | Iodine with n/SD/min/max, keyed to SR/Foundation NDB numbers |
| `data/McCance_Widdowsons…xlsx` | UK CoFID 2021 | Compilation — cite the underlying survey, not "CoFID" | Chloride, iodine, biotin, B-complex |
| `data/cvb_nl/` (untracked) | CVB Feed Table 2023 EN | Yes — Dutch feed industry | Rendered feeds (fish meal, meat meal, greaves): chloride, iodine, 18 AAs. Bone-meal analog only |
| `data/retention.csv` | Hand-compiled retention factors | — | Raw→cooked adjustments |
| `Docs/NRC2006.epub` | NRC 2006 tables 13-1/5/6/7 | Yes | Pet-food ingredient proximates, AAs, minerals, vitamins |
| `Docs/*.pdf` (papers) | See "Literature bundle" below | Yes | Taurine, organ-meat profiles |

## Which source for which sparse nutrient

| Nutrient | Check in (best first) |
|---|---|
| Choline | FCDB only. Everything else with choline (CNF, old USDA choline DB) is USDA lineage |
| Taurine | Literature only: Spitze 2003, Donadelli 2019, FCDB (6 foods). No national table has it |
| Iodine | USDA Iodine DB R4 (has n/SD), FCDB, MEXT, AFCD, BLS, CIQUAL, CoFID |
| Chloride | FCDB, BLS, CIQUAL, AFCD, CoFID, CVB (feeds) |
| Biotin | FCDB, MEXT, AFCD, BLS, CoFID |
| Vitamin D (D2/D3/25-OH) | FCDB, BLS, CIQUAL, MEXT, AFCD (D3-eq) |
| Vitamin K (K1/K2) | FCDB, BLS, CIQUAL, MEXT (K total) |
| Arachidonic acid 20:4 n-6 | uFiSh (fish), FCDB, BLS, CIQUAL, AFCD, MEXT FA volume |
| EPA / DPA / DHA | uFiSh (fish), FCDB, MEXT FA volume, AFCD, BLS (EPA/DHA), CIQUAL (EPA/DHA) |
| Amino acids | MEXT AA volume, FCDB, BLS, AFCD, uFiSh (fish), NRC 2006, Donadelli 2019 |
| Organ-meat anything | Seong papers (chicken/pork/beef organs), Biel 2019, FCDB ("Heart, beef, raw" etc.), BLS ("Chicken liver, raw") |
| Selenium | MEXT, FCDB, AFCD, uFiSh, CIQUAL (BLS and CVB have no selenium — verified) |

## File-reading notes (quirks that will bite you)

- **FCDB** (`FCDB_6.1_Dataset.xlsx`): sheets `Data_Table` (wide),
  `Data_Normalised` (long — has per-value Source, min/max/median,
  NumberOfDeterminations; prefer this for verification), `Food`, `Parameter`,
  `Source`. Columns are bilingual: Danish first, English second
  (`FoodName` is column B on `Food`). Units per 100 g.
- **BLS** (`BLS_4_0_Daten_2025_DE.xlsx`): one sheet, 7,140 rows × 418 cols.
  Per nutrient: `<CODE> value`, `<CODE> Datenherkunft` (origin),
  `<CODE> Referenz`. English food name = column C. Nutrient codes are in
  `BLS_4_0_Components_DE_EN.xlsx` (CLD=chloride, ID=iodide, BIOT=biotin,
  F20D4CN6=arachidonic…). Filter on the origin column — some BLS values are
  calculated, not analytical. Units mixed (see components file); per 100 g.
- **MEXT** (3 files): data starts below a multi-row header — the header text
  row is row 6 (0-indexed 5) on sheet `Table`. Main volume: minerals incl.
  Iodine/Selenium, vitamins incl. K and Biotin. AA volume: use
  `Table 1(per 100 g EP)` (the other tables are per g N / per g protein).
  FA volume: use `Table 1(per 100 g EP)`; `Table 2` is per 100 g total FA —
  do NOT read Table 2 values as per-100 g-food.
- **uFiSh**: values sheet `04 NV_sum (per 100 g EP)` is the one to read
  (`05 NV_stat` adds min/max/n). CAUTION: sheet `06 AA` is **per g nitrogen**
  (multiply by NT g/100g from sheet 04) and sheet `07 FA` is **per 100 g total
  fatty acids** (scale by FACID from sheet 04). `State of food`: `r` = raw.
  INFOODS tagnames (ID = iodine µg, CHOCAL = vit D3).
- **CIQUAL**: use `Table_Ciqual_2020_ENG.xls` for English food names
  (col `alim_nom_eng`, 3,186 foods); `Table_Ciqual_2025_FR.xlsx` is newer
  (3,484 foods, food name col `alim_nom_fr`, index 8). Values are strings and
  may be `"< 0,5"` or use comma decimals — parse accordingly. The 2020 file is
  legacy `.xls` (openpyxl cannot read it; use xlrd or read the 2025 file).
- **AFCD**: `AFCD_R3_Nutrient_profiles.xlsx`, sheet
  `All solids & liquids per 100 g`, header on row 3. Column `Derivation`:
  prefer `analysed` rows over `recipe`/`borrowed`. AA columns exist in both
  mass and per-g-N expressions — check the column header unit.
- **USDA Iodine DB**: `Iodine Database_Release 4_Per 100g.xlsx`, single sheet,
  data has group-header rows interleaved. Column B = SR/Foundation NDB number —
  join directly against `ingredients.sr_legacy_fdc_id`/`foundation_fdc_id`.
- **CoFID**: sheet `1.4 Inorganics` (chloride, iodine, Se, Mn), `1.5 Vitamins`
  (biotin, B-complex). It is a compilation — trace the footnoted survey.
- **NRC 2006 epub**: tables 13-1/13-5/13-6/13-7; the header's first cell spans
  two data cells, so `data[i+1]` aligns with `header[i]` — a naive `zip()`
  mislabels every column. Samples are fatty; scale to lean cuts.
- **CVB PDF** (untracked; restore URL in `data/README.md`): per-product sheets;
  Weende proximates, Ca/P/Mg/K/Na/Cl, trace incl. J (iodine), 18 total AAs +
  SID. No vitamins, no Se, no EPA/DHA. Rendered feeds ≠ raw meats — use only
  for bone meal / yeast / fish-meal-analog plausibility.

## Literature bundle (`Docs/`)

- `Spitze_2003_…taurine…` — taurine in feed ingredients; the canonical source
  named in `fediaf_nutrients.py`.
- `Donadelli_2019_AA_taurine_pet_food_protein_ingredients.pdf` — taurine + full
  AAs for 16 pet-food proteins (egg products, chicken meals). CC BY.
- `Seong_2015_chicken_byproducts…`, `Seong_2014_pork_byproducts…`,
  `Seong_2014_hanwoo_beef_byproducts…` — organ proximates, vitamins
  (A/B1/B2/niacin/B5/B6), AAs, minerals, FAs per species. CC BY-NC.
- `Biel_2019_offal_composition_veal_beef_lamb.pdf` — liver/heart/kidney/tongue/
  brain proximates + trace elements. CC BY.
- `FEDIAF-Nutritional-Guidelines_2025-ONLINE.pdf` — requirements, not
  composition.

## Sources deliberately NOT collected

- **Canadian CNF** — removed from the `ai_validation.py` citation list
  (2026-08-13) after verifying its Users' Guide (2015 ed.): "Much of the data
  in the CNF have been derived from the… USDA National Nutrient Database for
  Standard Reference, up to and including standard release 27" and "full
  profiles, or near full profiles, are borrowed only from USDA". Canada's own
  SNAP-CAN analyses cover processed staples (cereals, yogourts, deli meats,
  soups…) — none of our raw meat/organ/fish/egg classes. Citing CNF to confirm
  a USDA value is circular.
- **USDA Choline DB (2008)** — folded into SR; same lineage as FDC.
- **Dutch NEVO** — registration-gated; no biotin/choline/chloride/AAs; adds
  little over the above. Still fine for the API model to cite; just not local.
- **feedtables.com (INRAE-AFZ)** — no bulk download, unclear terms. Browse
  per-feed datasheets online when a rendered-feed range is needed.
- **CNF-style caveat for Norway/Switzerland**: their tables carry many borrowed
  values; not downloaded.

## Cross-checking rules of thumb

1. Prefer an "analysed"/sourced row (FCDB `Data_Normalised`, AFCD `analysed`,
   BLS origin column) over any table's headline number.
2. Match the food state: raw to raw. Use `data/retention.csv` before comparing
   a cooked entry to a raw one.
3. Everything above is per 100 g as-fed unless flagged (uFiSh AA/FA sheets,
   MEXT FA Table 2, AA per-g-N expressions). Convert before comparing.
4. Units follow `fediaf_nutrients.py` (IU for A/D/E; µg for iodine, Se, K,
   biotin, folate, B12): vit D µg × 40 = IU; vit E mg α-tocopherol × 1.49 = IU;
   vit A: RAE and IU are NOT interconvertible without the retinol/carotenoid
   split — for animal products retinol dominates, 1 µg retinol = 3.33 IU.
5. Two independent tables agreeing within ~±20 % is strong support for a
   nutrient with real analytical spread; minerals/AAs usually agree tighter.
6. When only one source exists (choline → FCDB, taurine → literature), record
   that source explicitly in `ingredient_nutrients.comment`.
