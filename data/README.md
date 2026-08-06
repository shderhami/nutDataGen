# Reference datasets

Everything the pipeline reads from disk, where it came from, and how to restore it.

## Tracked in git

| Path | What it is |
|---|---|
| `usda_bulk/` | USDA snapshots the CV pipeline reads. Pinned — see "Why this is committed" below. |
| `McCance_Widdowsons_Composition_of_Foods_Integrated_Dataset_2021..xlsx` | UK CoFID 2021. Covers chloride, iodine and biotin, which USDA does not track. |
| `cv_curation/` | Hand-curated CV class assignments and LLM scoring outputs. Source data, not reproducible. |
| `retention.csv` | Cooking retention factors with citations. Hand-compiled. |
| `ingredient prices.xlsx` | Price inputs. |

## Not tracked

| Path | Why |
|---|---|
| `USDA data/` | 69 MB duplicate of the FDC exports already in `usda_bulk/`. Restore instructions below if you want it back. |
| `../backups/` | PostgreSQL dumps written automatically by `cv_assign.py`. Regenerated on every commit run. |

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
