# Reference datasets

Everything the pipeline reads from disk, where it came from, and how to restore it.

## Tracked in git

| Path | What it is |
|---|---|
| `usda_bulk/` | USDA snapshots the CV pipeline reads. Pinned — see "Why this is committed" below. |
| `McCance_Widdowsons_Composition_of_Foods_Integrated_Dataset_2021..xlsx` | UK CoFID 2021. Covers chloride, iodine and biotin, which USDA does not track. |
| `fcdb_dk/`, `bls_de/`, `mext_jp/`, `fao_infoods/`, `ciqual_fr/`, `afcd_au/`, `usda_iodine/` | International composition databases for AI-validation cross-checks. See "International reference datasets" below. |
| `cv_curation/` | Hand-curated CV class assignments and LLM scoring outputs. Source data, not reproducible. |
| `retention.csv` | Cooking retention factors with citations. Hand-compiled. |
| `ingredient prices.xlsx` | Price inputs. |

## Not tracked

| Path | Why |
|---|---|
| `USDA data/` | 69 MB duplicate of the FDC exports already in `usda_bulk/`. Restore instructions below if you want it back. |
| `cvb_nl/` | CVB Feed Table 2023 (EN). © Stichting CVB — "no part may be copied … without written permission", so download-only. Restore: `curl -L -o "data/cvb_nl/CVB_Feed_Table_2023_EN.pdf" "https://www.cvbdiervoeding.nl/bestand/10901/cvb-feed-table-20232.pdf.ashx"` |
| `../backups/` | PostgreSQL dumps written automatically by `cv_assign.py`. Regenerated on every commit run. |
| `nutrition_database*.csv`, `ingredients.csv`, `ingredient_nutrients.csv` | Stale exports of the live database (Feb 2026 snapshots, superseded). Regenerate from PostgreSQL rather than committing snapshots. |

---

## usda_bulk/ — why this is committed

The CV pipeline hashes these datasets (`cv_assign.dataset_shas()`) and stamps the
result into **every CV it writes**. As of 2026-08-06 all 2,132 CV rows across 41
foods carry `cv_config_sha256 = a1601f65…`, and `tests/test_pipeline_version_integrity.py`
fails if the datasets drift from what produced them.

That makes these files part of the pipeline's reproducibility contract, not
scratch data — restoring a *different vintage* silently invalidates existing CVs
rather than erroring. They were deleted once and had to be re-fetched; committing
them removes that failure mode.

### Layout

```
usda_bulk/
  sr28/        NUT_DATA.txt, FOOD_DES.txt, NUTR_DEF.txt, SRC_CD.txt   (SR28-2015 ASCII)
  sr_legacy/   food.csv, food_nutrient.csv, nutrient.csv, …           (FDC SR Legacy 2018-04)
  foundation/  food.csv, food_nutrient.csv, nutrient.csv, …           (FDC Foundation)
```

`cv_config.py` resolves these paths; `peer_median.py` reads `sr_legacy/` and
`foundation/` for the peer cohorts shown in AI-validation prompts. If
`usda_bulk/` is missing, peer medians silently return empty and prompts lose
their local evidence — see `peer_median._dataset_dirs()`.

### Restoring / re-downloading

All three are free and need no registration.

**FDC exports** — <https://fdc.nal.usda.gov/download-datasets.html>
Download "SR Legacy" and "Foundation Foods" as **CSV**, unzip, and place the CSVs
directly in `sr_legacy/` and `foundation/` (flatten the
`FoodData_Central_*_csv_*` wrapper directory).

**SR28 (2015)** — <https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/methods-and-application-of-food-composition-laboratory/mafcl-site-pages/sr11-sr28/>
Download the **ASCII** distribution and place the `.txt` files in `sr28/`.
SR28 is **not** interchangeable with the FDC exports: it is the only source
carrying **standard errors**, which is what measured CVs are derived from. FDC
CSVs have `data_points`/`min`/`max`/`median` but no SE, so without SR28 every
cell falls back to category-only CVs.

### After restoring, verify the vintage

```bash
python -c "import cv_config; print(cv_config.config_sha256())"
```

Compare against `cv_config_sha256` on existing rows:

```sql
SELECT DISTINCT cv_pipeline_version, cv_config_sha256 FROM ingredient_nutrients
WHERE cv_config_sha256 IS NOT NULL;
```

A mismatch means a different vintage — expect `test_pipeline_version_integrity.py`
to fail, and do **not** run `cv_assign.py --commit` until it is resolved.

---

## UK CoFID

McCance & Widdowson's Composition of Foods Integrated Dataset 2021, GOV.UK,
**Open Government Licence v3.0** (free reuse including commercial, attribution
required).

<https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid>

```bash
curl -L -o "data/McCance_Widdowsons_Composition_of_Foods_Integrated_Dataset_2021..xlsx" \
  "https://assets.publishing.service.gov.uk/media/60538b91e90e07527df82ae4/McCance_Widdowsons_Composition_of_Foods_Integrated_Dataset_2021..xlsx"
```

SHA-256 `436e9445ef2adb2a75f3d7edd51302de3adad25385f9795fc94ba58bd030e97d`, 4.42 MB.

Sheet `1.4 Inorganics` carries chloride, iodine, selenium and manganese; `1.5
Vitamins` carries biotin and the B-complex. **CoFID is a compilation** — the lamb
entries trace to *LGC, Nutrient analysis of retail cuts of lamb, 1990s*, so cite
the underlying survey and its vintage, not "CoFID 2021".

## International reference datasets (added 2026-08-11)

Downloaded to give the in-session AI-validation agent local, independent
evidence for the databases the prompts in `ai_validation.py` already cite
(MEXT, AFCD, BLS, Danish DTU, CIQUAL). **Usage guide — which source to check
for which nutrient, plus file-reading quirks: `../Docs/reference_sources_guide.md`.** All verified on download: correct file
type, expected sheets/columns, and presence of target foods (raw livers,
hearts, Atlantic salmon, blue mussel, eggs). SHA-256 prefixes recorded below.

| Path | Dataset (version) | License | Sparse nutrients it covers | SHA-256 (12) |
|---|---|---|---|---|
| `fcdb_dk/FCDB_6.1_Dataset.xlsx` | Danish Food Composition Database 6.1, May 2026 (ex-Frida, DTU) — 1,390 foods, bilingual DA/EN, per-value provenance | CC BY 4.0 | **Choline (only independent source), taurine (6 foods)**, biotin, iodine, chloride, D2/D3/25-OH-D, K1/K2, ARA/EPA/DPA/DHA, full amino acids | `aba52ade9dd7` |
| `bls_de/BLS_4_0_2025_DE/` | German BLS 4.0, Dec 2025 (MRI) — 7,140 foods × 418 cols, EN food names, per-datapoint origin | CC BY 4.0 | Iodide, chloride, biotin, D2/D3, K1/K2, ARA/EPA/DHA, full amino acids. No choline | `524bbefe25b6` |
| `mext_jp/` (3 files) | Japan Standard Tables 2015, 7th rev., English — main + amino-acid + fatty-acid volumes, 2,188 foods | JP gov't terms (attribution) | Iodine, selenium, biotin, vitamin K, D; AA and FA volumes incl. ARA/EPA/DPA/DHA. Fully USDA-independent; best fish/organ coverage | `5c968f1801f7` (main) |
| `fao_infoods/uFiSh1.0.xlsx` | FAO/INFOODS uFiSh 1.0 (2016) — 515 fish/shellfish items incl. Atlantic salmon farmed raw, Nile tilapia raw, blue mussel raw | FAO, free download (no explicit license — treat as research use) | Iodine, selenium, full AA (per g N), exhaustive individual FAs (ARA/EPA/DPA/DHA) | `2755bdeb7b8e` |
| `ciqual_fr/` | CIQUAL 2025 (FR, 3,484 foods) + CIQUAL 2020 (EN, 3,186 foods) (ANSES) | Etalab Open Licence 2.0 | Chloride, iodine, D2/D3, K1/K2, ARA/EPA/DHA. No AAs/biotin/choline | `5555c572fa37` / `5551841f12f4` |
| `afcd_au/` | Australian Food Composition Database Release 3, Dec 2025 (FSANZ) — 1,588 foods, `Derivation` flags analysed vs recipe | CC BY 4.0 | Iodine, biotin, chloride, selenium, D3-eq, full AAs, ARA/EPA/DPA/DHA. No K/choline | `14cb3e73dbf5` (profiles) |
| `usda_iodine/` | USDA/FDA/ODS-NIH Iodine Database Release 4 (2024) — 478 foods with n/SD/min/max, keyed to SR/Foundation IDs | Public domain | Analytical iodine absent from FDC (complements, not independent of, USDA) | `4627a296ff49` |
| `cvb_nl/` (untracked) | CVB Feed Table 2023 EN (Stichting CVB) — rendered feed ingredients (fish meal, meat meal, greaves) | © CVB, no redistribution | Chloride, iodine, 18 AAs for bone-meal analogs. No vitamins/Se/EPA/DHA | — |

Restore URLs (all verified 2026-08-11):

- FCDB: <https://doi.org/10.11583/DTU.32312844> (xlsx: `https://ndownloader.figshare.com/files/65016537`, docs PDF: `.../65016552`)
- BLS: <https://blsdb.de/download> (session-tokenized link to `BLS_4_0_2025_DE.zip`; fetch the page first)
- MEXT EN 2015: <https://www.mext.go.jp/en/policy/science_technology/policy/title01/detail01/1374030.htm>
- uFiSh: <https://www.fao.org/infoods/infoods/tables-and-databases/faoinfoods-databases/en/>
- CIQUAL: <https://doi.org/10.57745/RDMHWY> (2025), 2020 EN xls from ciqual.anses.fr
- AFCD: <https://www.foodstandards.gov.au/science-data/food-nutrient-databases/afcd/data-files>
- USDA iodine: <https://www.ars.usda.gov/ARSUserFiles/80400535/Data/Iodine/IODINE_RELEASE_4.zip>

Known gaps: **taurine** is absent from every national table (FCDB has 6 foods) —
use the literature PDFs in `../Docs/` (Spitze 2003, Donadelli 2019, Seong
2014/2015 organ papers, Biel 2019). **Choline** outside USDA exists only in the
Danish FCDB. Canadian CNF was deliberately skipped: it is derived from USDA SR
≤27, so it cannot serve as an independent check.

## Other reference sources

Not in `data/` but cited in `ingredient_nutrients.comment`:

- `../Docs/NRC2006.epub` — Nutrient Requirements of Dogs and Cats (NRC 2006).
  Ingredient tables 13-1 (proximate), 13-5 (amino acid), 13-6 (mineral),
  13-7 (vitamin). **Parsing caveat:** the header's first cell spans *two* data
  cells, so `data[i+1]` aligns with `header[i]`; a naive `zip()` mislabels every
  column. NRC samples are also fatty (lamb ground is 23.4% fat) and need scaling
  to lean cuts.
- `../Docs/Spitze_2003_Taurine_concentrations_in_animal_feed_ingredients.pdf` —
  the taurine reference named in `fediaf_nutrients.py` notes.
- Organ-meat & taurine literature (added 2026-08-11, all open access):
  `../Docs/Donadelli_2019_AA_taurine_pet_food_protein_ingredients.pdf` (CC BY —
  taurine + full AAs for 16 pet-food protein ingredients incl. egg products and
  chicken meals), `../Docs/Seong_2014_pork_byproducts_nutritional_composition.pdf`,
  `../Docs/Seong_2014_hanwoo_beef_byproducts_nutritional_composition.pdf`,
  `../Docs/Seong_2015_chicken_byproducts_nutritional_composition.pdf` (CC BY-NC —
  heart/liver/organ proximates, vitamins, AAs, minerals, FAs per species),
  `../Docs/Biel_2019_offal_composition_veal_beef_lamb.pdf` (CC BY — liver, heart,
  kidney, tongue, brain trace elements and proximates).
