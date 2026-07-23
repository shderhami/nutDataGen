# Nutrient CV Extraction & DB Update Plan (nutDataGen)

**Home:** this repo (`nutDataGen`) — producer of the shared `cat_food_formulator` DB. The formulator is a pure **consumer**; **zero changes to the recipeFormulator repo** in this plan.

**Goal:** compute a correct, traceable per-(ingredient, nutrient) **coefficient of variation (CV)**, stored as a **dimensionless fraction**, so the formulator can later replace its flat 25% Phase-2 margin with evidence-based per-nutrient buffers. Produces the CV **data** only; the optimizer change is a separate, formulator-side task.

**Status:** ready to implement on `feature/nutrient-cv-extraction`. Methodology converged over two prior audits; a third audit targeted this nutDataGen adaptation (19 fixes) — all folded in here, together with the two-column storage design and the ongoing-assignment resolver.

**Scope boundary:** CV = analytical/compositional content variability only — **not** bioavailability, **not** cooking-retention. Marginal per-cell CVs; cross-ingredient aggregation is the consumer's contract (§1).

---

## 0. Integration with nutDataGen

- **Two-column storage on `ingredient_nutrients`** (one row per `food_id, nutrient_id`):
  - **`coefficient_of_variation`** — *re-purposed* to the ingredient-nutrient's **own directly-measured** CV (Tiers 1–3), **fraction**, NULL when no measured data. (Was legacy percent relative-SE — corrected & re-unit'd.)
  - **`category_cv`** (NEW) — the **category-pooled / prior / supplement** CV (Tiers 4–6), fraction, populated for **every** cell.
  - **Consumer contract:** `COALESCE(coefficient_of_variation, category_cv)`; a fully-NULL result → consumer uses the conservative flat default `0.25`, never 0.
- **One shared resolver `resolve_cv()`** owns both columns, used by BOTH the batch pipeline AND the per-insert path (§4a) — so future ingredients get correct CVs automatically and the column is single-semantic.
- **`database.calculate_statistics()` CV logic is replaced by `resolve_cv()`** (it still returns `'coefficient_of_variation': None` in its dict so `create_nutrient_record` cannot `KeyError`; it may keep `estimated_se`/CIs as USDA-API provenance — noting those are no longer derivable from the CV). The 4 legacy tests (`test_database.py:392-393,458,479`, `test_integration.py:142`) are updated to the new semantics (fraction / owned-by-resolver).
- Existing ingestion pulls dispersion from the **USDA API** (no SE); the **new capability** is reading the **SR28 bulk** for real SE. Schema via **Alembic**; DB via `db_connection.get_db()`; scripts top-level (`argparse`/`--dry-run`/pg_dump), pattern `backfill_nutrients.py`. Nutrient identity in `fediaf_nutrients.py` (FEDIAF ↔ FDC `nutrient_id` ↔ USDA name).
- **Schema-ownership note:** the `cv_*`/`category_cv` columns and `cv_*` tables are **nutDataGen-Alembic-owned**. An empty-DB bootstrap via the formulator's `setup_database.py` (which uses `CREATE TABLE IF NOT EXISTS`) must be followed by re-running Alembic head + the CV pipeline.

---

## 1. Principles

1. **Reproducibility** — deterministic over pinned files; content-identical re-run (fixed `ORDER BY`, one rounding engine+mode, round-before-median, `percentile_disc`, canonical content-hash over raw config bytes).
2. **Traceability** — every CV carries tier, method, inputs, class fallback, backing count, `cv_pipeline_version`; per-run provenance (config/code/dataset SHAs + gate/sign-off) in `cv_pipeline_run`.
3. **Conservative on the corrections it owns** — the c₄ small-n unbiasing and the per-class minimum floor (`cv_detection_floor_min`) may only **raise** a CV (unit-tested). Distinct from `near_detection_clip_to_cap` (which *lowers* a near-detection over-inflated CV to `cv_cap`) and shrinkage (may lower toward the measured pool). The cap's under-buffering of skewed toxicity maxima is the downstream robust-bound owner's problem.
4. **Portability limits** — CV as a fraction multiplier on the cell mean; moisture-invariant, analyte-matched; the one limited axis is raw vs cooked (§5).
5. **SE→SD approximation** — `SD=SE·√n` (SR28 `Std_Error`=SEM of the (n−1) sample SD, null n<3); overstates for weighted means (more buffer), never understates.

**Aggregation contract (consumer):** marginal fractional CVs; cross-source variability is positively correlated → recommend comonotone (`σ_n≈Σ CV_in·mean_in·x_i`) for one nutrient across foods (not the Ca:P ratio). **Consumption basis:** applied per-mass before per-1000-kcal normalization.

---

## 2. Sources (pinned) & crosswalk

SR28 bulk (`NUT_DATA.txt`, real SE), FDC SR-Legacy + Foundation CSVs (min/max/n), FDC `nutrient.csv` (Foundation = authoritative crosswalk). Frida deferred. Files under `data/usda_bulk/`; SHAs in `cv_pipeline_run`.

**`nutrient_crosswalk`** (`build_nutrient_crosswalk.py`, must pass): `nutrient_name → nutrient_nbr → nutrient_id → unit → form`, built fresh from Foundation `nutrient.csv`, cross-checked vs SR-Legacy (**fail loud on mismatch**). Three dispositions per target nutrient: **has nbr** → use; **combined/ratio** (Met+Cys, Phe+Tyr, EPA+DHA, Ca:P) → allowlist → component map; **no nbr / single** → logged route to Tier-4/5 by nutrient_class. **Fail loud** only on corrupt/duplicate/many-to-one. Assert every real `nutrient_nbr` is a positive integer before the INT column. Vit A: retinol(319) only via Tier-3 animal-tissue. Bridge `NDB_number→NDB_No` (int-normalize both).

---

## 3. Schema (one Alembic migration)

```sql
-- ingredient_nutrients: re-purpose + add
coefficient_of_variation  NUMERIC(10,6)  -- NOW: own measured CV, FRACTION (0, cv_cap]; NULL if unmeasured
+ category_cv              NUMERIC(10,6)  -- category/prior/supplement CV, fraction, populated for every cell
+ cv_tier, cv_method, cv_backing_n, cv_effective_n, cv_confidence_tier,
  cv_calibration_flag, cv_class_key JSONB, cv_method_inputs JSONB,
  cv_config_sha256, cv_pipeline_version
-- ingredients: add (§5 keys on it)
+ ingredient_class TEXT                    -- + keyword-rule backfill in the same migration

cv_pipeline_run(pipeline_version PK, config_sha256, code_sha256, dataset_shas JSONB,
                gate_passed BOOL, signed_off_by TEXT, signed_at TIMESTAMP, run_at)
cv_cv_preimage(pipeline_version, food_id, nutrient_id,
               old_coefficient_of_variation, old_category_cv, ...)  -- targeted pre-image for precise revert
cv_observations(... UNIQUE(source_dataset, source_food_id, nutrient_nbr) ...)   -- raw per-source-food
cv_class(ingredient_class, nutrient_nbr INT NOT NULL DEFAULT -1,
         nutrient_class NOT NULL, pooled_cv, n_foods, pooling_method, cv_p25, cv_p75,
         source_mix JSONB, method_mix JSONB, floor_clipped_frac,
         is_literature_prior, prior_citation, pipeline_version)
--   UNIQUE(ingredient_class, nutrient_nbr, nutrient_class)  [nutrient_class NOT NULL => no NULL-distinct dup]
--   + partial UNIQUE(ingredient_class, nutrient_nbr) WHERE nutrient_nbr <> -1
```
Units: **all CVs are fractions in `(0, cv_cap=1.5]`.** `cv_assign` **asserts `0 < cv ≤ cv_cap`** and **fails loud** on any value `> cv_cap` (a surviving legacy percent). `NUMERIC(10,6)` holds fractions precisely.

---

## 4. The resolver — precedence ladder (`resolve_cv`)

`resolve_cv(cell, cv_class, priors, category) → (measured_cv|None, category_cv, tier, provenance)`. **Supplement/Fish-Oil pre-emption:** a cell whose `ingredients.category ∈ {'Supplement','Fish Oil'}` resolves at **Tier 6 first** (its own delivered floor), skipping Tiers 1–5. **Zero-mean/non-nutritive:** `value=0` or `category='Base'` (water) → **both CV columns NULL**, exempt from the §7 gate. Otherwise, top-down:

| # | Tier | → column | Method |
|---|---|---|---|
| 1 | `sr28_se` | measured | `s=SE·√n`; `σ̂=s/c₄(n)`; `CV=σ̂/mean`; `n≥3, SE>0` |
| 2 | `fdc_range` | measured | Wan `SD=(max−min)/ξ(n)`; `n≥2, min≠max`; **also applied to the row's own stored min/max/n** so a measured cell never downgrades |
| 3 | `component` | measured | `ρ=1`: `CV=(Σ mean_i·CV_i)/(Σ mean_i)` (Vit A←Retinol animal-tissue; Met+Cys; Phe+Tyr; EPA+DHA; PUFA-total) |
| 4 | `class_pool` | category | `cv_class` fine → coarse(-1) → broadest |
| 5 | `nutrient_prior` | category | universal literature CV by nutrient class (terminal fallback), biased high, **cited** |
| 6 | `supplement` | category | delivered floor (§6) |

Tiers 1–3 → `coefficient_of_variation`; Tiers 4–6 → `category_cv` (always computed). `cv_tier` = the effective (consumer-facing) tier.

**Pinned params** (`cv_config.py` — a Python module, matching the repo's `config.py` convention; hash = SHA256 of its raw bytes): `k=5`, `n₀=8`, `cv_cap=1.5`, per-class `cv_floor` + `cv_detection_floor_min`, calibration cutoff (`>0.05` OR both `≥0.03` & ratio outside `[1/1.5,1.5]`), confidence thresholds (`backing_n≥8`, `w≥0.8`), `effective_n` (prior=1, supplement=2), delivered-supplement floors (**0.08 / 0.15** fractions), labile-active list, **criticality Bucket A/B/C map**, `max_prior_only_frac`, `CALIB_MAX_MEDIAN_DIVERGENCE (0.05)` + `CALIB_MAX_TWIN_DIVERGENCE (0.30)`, cooking-method keywords, rounding mode + `percentile_disc`.

**Guards:** c₄ **divide** (Tier-1 only; unit-assert `1/c₄>1`; pin the SE convention); `near_detection_clip_to_cap` (clip inflated near-detection CV to `cv_cap` + flag; route pool to prior if `>30%` clipped); drop `min==max`; exclude USDA calc/imputed/borrowed via `Src_Cd`/`Deriv_Cd`/`derivation_id`; lineage dedup at Layer 2 (SR28+FDC-SRL once, prefer SE; Foundation kept); Wan large-n/outlier flag. **Pooling:** unweighted median of per-food CVs (round-before-median, `percentile_disc`, fixed `ORDER BY`). **Shrinkage:** log-scale toward the measured pool, `w=n/(n+n₀)`; **skip downward for Bucket-A** (`class_cv<cell_cv` → keep the higher measured). **confidence_tier** (exhaustive, first-match high→medium→low): high = Tier-1/2 `backing_n≥8 & w≥0.8`; medium = other Tier-1/2 / component / Tier-4 `n_foods≥k` / supplement; low = prior / Tier-4 `n_foods<k`. **Calibration** computed at Layer 1 per twin; flag propagated only to Tier-1/2 direct cells (else NULL); gate rate excludes NULLs.

### 4a. Ongoing assignment (new data inputs)
`resolve_cv()` is called by BOTH:
- **Batch** (`cv_assign.py`) — over all `ingredients × constrained nutrients`.
- **Per-insert** — `create_nutrient_record`/backfill compute the CV on write, using the cell's own USDA min/max/n (measured → old column) else the persisted `cv_class`/priors (category → new column). So a **newly-added ingredient gets a correct, provenance-tagged CV immediately**; no RSE, no NULL-until-batch.

`cv_class` (the pooled table) is the durable artifact the per-insert path reads. It is rebuilt (batch) only on a new pinned USDA snapshot or enough new ingredients; each cell carries `cv_pipeline_version` so the §7 report flags cells resolved against a stale `cv_class` vintage.

**Target set:** the constrained nutrients from **`fediaf_nutrients.py`** (in-repo authority; the formulator's `nutrient_limits` is only an optional cross-check — no cross-repo coupling).

---

## 5. Taxonomy (config)

Two axes; finest rung with `≥k` foods; coarsen ingredient before nutrient. Ingredient classes: `muscle(poultry/red)`, `organ(liver/heart/kidney/other`, species-pooled except domain splits Vit A/D/Cu/B12`)`, `fish(oily/white/shellfish)`, `egg`, `dairy`, `fat/oil`, `plant`, `Base` (water — zero-mean carve-out). Terminal fallback = **universal Tier-5 nutrient_prior by nutrient class** (not "all animal tissue"). Raw-scarcity ladder: raw-only fine → coarser → mixed(flag) → prior; `prep_state` via config cooking-method keywords (default `other`). **`ingredient_class` persisted on `ingredients`** (migration + keyword backfill); every cell provably resolves (post-run assertion). Nutrient classes: proximate(low-CV), fat, major mineral, trace mineral, Se/I, fat-sol vit, water-sol vit, amino acid, n-3 long-chain, n-6/linoleic, arachidonic; choline/iodine/Vit K explicit.

---

## 6. No-data & priors (fractions)

Supplement/Fish-Oil (Tier 6, pre-empted): analytical 2% provenance-only; **delivered floor 0.08, 0.15 for labile actives** (config list); confidence medium. Whole-food gap → pool → cited prior. Vit A → retinol animal-tissue else prior+robust; taurine → Tier-6 ≥0.15; Se/I skewed → robust bound + few-source flag (via `n_foods`/`source_mix`).

**Tier-5 priors (fractions, biased high, cited):** proximate 0.10 · fat 0.30 · major mineral 0.15 · trace 0.30 · Se/I 0.55 · fat-sol vit 0.45 · water-sol vit 0.35 · choline 0.35 · amino acid 0.20 · n-3 fish 0.25 / terrestrial 0.40 · n-6/linoleic 0.35 · arachidonic 0.45 · supplement 0.08–0.15.

**Criticality Bucket A/B/C map** (config, versioned): A = taurine, thiamine, choline, Vit A, Vit D, Cu.

---

## 7. Validation, gating & QA

**Gate runs BEFORE the live write.** `cv_assign` resolves into a staging pass, `cv_report` evaluates the gate, and only a **gate-passed + named sign-off** (`cv_pipeline_run.gate_passed`, `signed_off_by`, `signed_at`) permits the commit that stamps `cv_pipeline_version` onto `ingredient_nutrients`.

**Hard block:** any Bucket-A/critical nutrient shipping `< 0.25` via a bare Tier-5 prior **or a coarse (transplanted) class pool** (fine same-nutrient pools are exempt; zero-mean/Base carve-outs excluded); any prior row with null/sentinel citation; `prior_only_frac > max`; **twin SE-vs-range calibration** — `median |cv_se − cv_range| > CALIB_MAX_MEDIAN_DIVERGENCE (0.05)` (systematic error) OR any single **same-food** twin `> CALIB_MAX_TWIN_DIVERGENCE (0.30)` (localized error); coverage/crosswalk failed; Vit A assertion (no non-animal-tissue Vit A via 319) failed. **Escape hatch:** a prior-only critical nutrient may ship only at CV `≥ 0.25` with named sign-off. *(The per-cell calibration flag is stored as informational provenance; the gate blocks on the aggregate median + worst-twin, not the per-cell flag rate.)*

**Reports:** twin calibration; coverage/tier map (measured vs category share); pool health (`n_foods`, `p25/p75`, `source_mix`, `method_mix`, `floor_clipped_frac`, k±2); stale-vintage cells; prep_state counts; completeness (every `ingredient×constrained nutrient` has a current CV); measured-vs-`category_cv` diff; diff vs flat 25%.

---

## 8. Deliverables

| File | Does |
|---|---|
| `alembic/versions/<rev>_add_cv.py` | re-purpose `coefficient_of_variation` + `category_cv` + `cv_*` + `ingredients.ingredient_class` (backfill) + `cv_observations`/`cv_class`/`cv_pipeline_run`/`cv_cv_preimage` |
| `cv_config.py` | pinned params, taxonomy + cooking keywords, Tier-5 priors + citations, criticality map, component/allowlist maps, target map |
| `build_nutrient_crosswalk.py` | build+cross-check+validate; **fail loud** |
| `cv_sources.py` | SR28 reader (`delimiter='^'`, `quotechar='~'`, **no header**, positional NDB_No/Nutr_No/Std_Error/N/Min/Max/Src_Cd/Deriv_Cd, field-count assert) + FDC comma-CSV+header reader |
| `cv_extract.py` | per-food CV, classify, exclude calc/imputed → `cv_observations` |
| `cv_pool.py` | lineage-dedup → `median_cv` → `cv_class` (+ priors, coarse rungs) |
| `resolve_cv.py` | the shared ladder (§4/§4a) — imported by `cv_assign` AND `create_nutrient_record` |
| `cv_assign.py` | resolve all target cells; capture pre-image; **reconcile+write in ONE transaction** (see §9); pg_dump first |
| `cv_report.py` | §7 report + gate result; writes `gate_passed`/sign-off |
| tests | update the 4 legacy assertions to new semantics; add tests that both CV columns are resolver-owned, fractions, bounds-checked |

Reuse `db_connection`, `database.py` CRUD, `argparse`/`--dry-run`. `pg_dump` path/role **configurable + preflight existence check** (not hardcoded).

---

## 9. Execution order & idempotency

1. `alembic upgrade head`. 2. Pin snapshots; write `cv_config.py`; record manifest (config/code/dataset SHAs). 3. `build_nutrient_crosswalk.py` — must pass. 4. `cv_extract.py`. 5. `cv_pool.py`. 6. `cv_report.py` on the resolved staging set → **gate + named sign-off**. 7. Only if gate-passed: `cv_assign.py` commits (`--dry-run` supported).

**`cv_assign` is one transaction, reconcile-not-just-upsert:** capture the targeted pre-image → **NULL** `coefficient_of_variation`/`category_cv`/`cv_*` for every row not in the current target set or with a stale `cv_pipeline_version` → UPSERT current cells (**assert `rowcount==1` per intended cell**; pre-SELECT and hard-fail on a missing `ingredient_nutrients` row; pass only `cv_*` keys so `update_nutrient` side-effects don't fire) → run the completeness check → commit (partial failure rolls back). Audit tables are single-live-version (`DELETE FROM` reverse order → insert). **Rollback:** precise single-column revert from `cv_cv_preimage`; documented full restore = dump `--clean --if-exists` into a fresh DB + verify.

**Re-run triggers:** new/edited ingredient (per-insert resolver handles it live), new constrained nutrient, new pinned snapshot, any config/code change (bump). §7 completeness catches gaps.

---

## 10. Out of scope

Frida; **the formulator optimizer change** (CV-weighted margins / robust bounds — owner of the cap under-buffering); cross-ingredient correlation aggregation; bioavailability / cooking-retention variance; Monte-Carlo; real-assay backfill. **Zero recipeFormulator changes.**

---

## 11. Risks

Cross-source variability (conservative for symmetric; robust bounds downstream for skewed Se/I/Vit A/D and thin pools). Provenance food-dependent. Wan on cross-source extremes runs wide (conservative); ~1pp agreement overlap-only. Legacy `coefficient_of_variation` (percent RSE) is overwritten as fraction population CV; `estimated_se`/CIs stay USDA-API-derived and are **no longer** `CV·value` (documented). Two schema frameworks on one DB (governance note, §0).

---

## 12. Audit trail

Three 5-lens adversarial audits. R1 (formulator draft): 57→31. R2: 40→25 (converged, not over-engineered). **R3 (nutDataGen adaptation): 31→19 applied here** — CRITICAL unit→fraction; two-column measured/category storage (your Point 1) with `COALESCE` consumer contract; gate-before-write + named sign-off; reconcile-in-one-transaction; Supplement/Fish-Oil Tier-6 pre-emption; Base/zero-mean carve-out; executable pre-image rollback; the 4 test updates; `ingredient_class` migration; cv_class NULL-distinct fix; Python `cv_config.py` (no new YAML dep); SR28 caret/tilde parser spec; NULL-consumer contract; vocabulary split (floor-min vs clip-to-cap). Plus **Point 2**: the shared `resolve_cv()` owning both columns at batch + per-insert time. Rejections not carried: "setup_database.py drops cv_* columns" (CREATE IF NOT EXISTS), Choline/Biotin blank-`nutrient_nbr` (standard analytes), divide-by-zero (universal fixed prior).
