# New-ingredient workflow: add, validate, CV — the full process

Agent-facing runbook. Follow it end-to-end whenever an ingredient is added to
`cat_food_formulator`, and for re-validation passes. It encodes the methodology
and defect taxonomy from the 23-food validation sweep (2026-08-16/17).
Companion references: `Docs/reference_sources_guide.md` (per-source reading
quirks, nutrient→source routing), `data/README.md` (dataset provenance).

## Phase 1 — Add

**Path A (preferred): the intake pipeline** — `Docs/intake_pipeline.md`.
Curate `data/intake/<slug>.json` (USDA FDC ids + the matched entry per local
source, with frame caveats), then:

```bash
.venv/bin/python -m intake report --spec data/intake/<slug>.json   # artifacts
# review report.md with the operator, finalize decisions.json (Phase 2 rules)
# and add top-level "reviewed_by" — the writer refuses unreviewed files
.venv/bin/python -m intake write --spec ... --decisions ... --commit --signed-off-by "Shahab"
```

Extraction is from the pinned bulk datasets (no API, no billing); Phase 2
below is encoded in its rule engine but every verdict is reviewed before the
gated write. Spec + report + decisions are committed to git as the audit
record. Then continue with Phase 3.

**Path B (fallback — no local-source coverage): interactive add (main.py)**

1. Collect up front: SR Legacy + Foundation FDC IDs (no in-app search — look
   them up first), category, base unit/portion, price. Whole foods are stored
   per 100 g; data is entered **raw-basis** even when `cooking_method` is set
   (the flag records how it is fed; the formulator applies retention factors).
2. Billing gate: live AI validation bills ~52 requests/ingredient. Check
   Anthropic credits first; a credit-exhausted run poisons every row with error
   text (abort rather than continue).
3. Drive `main.py` via the FIFO method if the operator wants in-chat help
   (see memory: interactive-ingredient-add-workflow). `add_ingredient` inserts
   the ingredients row up front — after an aborted run, remove the orphan with
   `database.delete_food(food_id)`.
4. Never relay an AI validation suggestion unverified (Phase 2 applies to every
   discrepancy decision made during the add).

## Phase 2 — International validation (per nutrient row)

### 2.1 Match the food in each source

Map the exact cut/state, not just the species. Hard-won name mappings:

| Concept | Aliases seen in the tables |
|---|---|
| top round (beef) | topside (UK/AU/DK), Oberschale (DE), tende de tranche (FR), inside round (JP) |
| chuck (beef) | braising steak / chuck and blade (UK), paleron (FR), Kamm/Schulter (DE), kata/chuck (JP) |
| pork shoulder | hand (UK & DK!), Bug/Schulter (DE), épaule (FR), picnic shoulder (JP) |
| pork loin | Kotelett/Lachs (DE), côte/carré/filet (FR), loin (JP: lean & lean-and-fat variants) |
| skin-on poultry | verify BOTH USDA entries say "meat and skin"; match only skin-on comparators (BLS often has only skinless) |
| butternut | a "pumpkin" in AU; doubeurre (FR) |

MEXT lists multiple populations (wagyu/Holstein/crossbred/**imported**) — the
*imported* entry is usually the best US-market comparator.

### 2.2 Independence screening (CRITICAL — do this before comparing)

Compilations copy each other and USDA. A "confirming" table may be an echo:

- **CIQUAL**: raw-meat/organ entries are frequently full USDA copies (match to
  3 decimals). Diff a few values against SR before counting it independent.
  Its chloride/iodine are usually genuinely French.
- **CoFID**: a compilation — cite the underlying survey (`Main data
  references`), and expect its butternut/etc. rows to echo USDA.
- **FCDB**: decode `Source` IDs via the `Source` sheet. Many rows are borrowed
  (USDA 1976/SR20, McCance 1978/1991, Fineli, Swedish DB); Danish-analytical
  rows carry Min/Max/n and are gold.
- **AFCD**: `Food Details → Sampling Details` explicitly names which nutrients
  were borrowed from which USDA FDC ID. Always read it.
- **BLS**: trust `[Analyse]` origin; `[Übernommener Wert]`/`[Literatur]`/
  `[Nährstoffdatenbank]` are adopted values.

### 2.3 Judge each row

Decision rules, in order:

1. **Measured beats derived.** USDA analytical values (real `data_points`)
   survive unless ≥3 independents + a physiology cross-check agree they are
   defective (this happened twice in 23 foods: chicken-liver vit A n=4 below
   every table's minimum; chicken-heart Zn 3× everything including USDA's own
   other species).
2. **Region rule** (US customer base): for feed/soil-driven nutrients (Se,
   iodine, vit A/D/E, n-3), international tables detect *data-quality defects*
   only — never re-center a sound US mean. When overriding a defective value,
   pick the edge of the international cluster consistent with US practice
   (grain-fed → low n-3 edge, etc.). Exceptions: imported supply chains follow
   the farm country (salmon = Chile/Norway; lamb = AU/NZ — confirmed by
   operator 2026-08-17).
3. **Check the derivation code** of every SR zero/low value in bulk
   `food_nutrient_derivation.csv`. Assumed/borrowed zeros (`Z`, `BFxx`) on
   LC-PUFAs and vit K are usually wrong. A *measured* zero can be real
   (mussel vit D; rice biotin; egg-white fat-solubles).
4. **Menaquinone blindness**: SR vitamin K counts K1 only. Hearts, thigh+skin,
   yolk, pork muscle, livers all carry MK-4 (BLS/MEXT/CIQUAL K2 columns).
   A near-zero SR vit K on an animal food is a form-coverage defect.
5. **"Physical composition" computed rows** (common on retail cuts): vintage
   matters — modern computations (2011+ turkey) validate well; legacy chicken
   ones did not. Cross-check, don't auto-trust.
6. **Known AI failure modes**: white-meat taurine overestimated (breast ≈
   15–30, not 33–130); occasional wrong *rejections* of correct SR values
   (mussel ARA/Cu, yolk DPA) — check the rejected value too; chloride
   estimates drift; plants have zero taurine and (for cats) zero vitamin A
   activity from carotenoids — do not "fix" plant vit A to human RAE.
7. **±20% agreement** between two independents = support. Folate/biotin have
   structural assay splits (UK/AU microbiological reads high) — judge within
   assay families.
8. **Crosswalk gap**: Foundation sometimes publishes retinol (1105) without
   RAE (1106) — check bulk before believing "SR only" for vitamin A.

### 2.4 Apply

- `pg_dump -Fc` backup to `backups/cat_food_formulator_pre_<food>_validation_*.dump`.
- One transaction; every touched row gets a comment:
  `Validated YYYY-MM-DD: <old> -> <new> per <sources with n>; <reasoning>.`
  Keeps get evidence comments too ("kept X - refs...", or an explicit
  "NO measurement exists in any local resource" note).
- Source flips (`sr_legacy` → `literature` etc.): clear stale
  `num_samples`/`min_value`/`max_value`/`derivation_description` — they
  described the old value (bracket-guard rule).
- **Store the anchor source's stats** when it publishes them (n + min/max →
  also SE/CI per `database.calculate_statistics` convention: SD≈range/4).
  A literature-sourced row whose own stats bracket the value gets a
  same-source `literature_range` CV automatically (cv-v7). Don't attach
  stats from a different item than the value's source; don't store
  censored ranges (min=0).

## Phase 3 — CV pipeline

```bash
.venv/bin/python cv_assign.py --food-id <id>              # dry-run, gate must PASS
.venv/bin/python cv_assign.py --food-id <id> --commit --signed-off-by "Shahab"
```

Value edits change CV eligibility (a zero leaving the carve-out gains a pool
CV). Verify the interesting cells afterwards (`cv_tier`, `cv_backing_n`,
`cv_method_inputs`).

## Phase 4 — International CV observations (cv-v8)

1. If a foreign table (FCDB above all) has the food with Min/Max/n rows:
   add the mapping to `cv_intl.FOOD_MAP` (+ any frame-mismatch rows to
   `EXCLUDES` with the reason — trim mismatch, multi-decade monitoring, etc.).
2. Regenerate: `.venv/bin/python cv_intl.py build`
   (rewrites `data/cv_curation/intl_cv_observations.csv`).
3. Run pytest. `tests/test_intl_sigma_calibration.py` recomputes σ² from the
   grown evidence and **fails with instructions when recalibration is due** —
   then update `cv_config.INTL_CV_SIGMA2`, bump `PIPELINE_VERSION`, and
   re-run `cv_assign.py --commit` (full, signed).
4. The CSV change alone alters `dataset_shas()` → the next commit records it.

## Phase 5 — Invariants & closeout

- PUFA total (1293) must be ≥ the sum of tracked components
  (LA+ALA+ARA+EPA+DHA+DPA). If edits broke it, recompute to the component sum
  (source `calculated`, "lamb convention").
- Re-run recipe compliance in recipeFormulator when a change is
  formulation-relevant (Zn, taurine, vit A on heavily-used ingredients).
- Commit code/dataset changes to git (dual-push: GitHub + GitLab).
- Record the outcome in the agent memory (db-validation-initiative).

## Standing conventions

- **FEDIAF platform units, one unit per nutrient** (DB normalized 2026-08-17):
  vitamins A/D/E are stored in IU everywhere (A: µg retinol ×3.33 — RAE :=
  retinol in this DB; E: mg ×1.49). `create_nutrient_record` converts payload
  units at add time (`fediaf_nutrients.fediaf_unit_factor`, fail-loud on
  unknown pairs); `tests/test_unit_uniformity.py` guards the invariant. The
  factors mirror recipeFormulator's `config/nutrients.yaml`
  `unit_conversions_nutrient` (kept as its safety net — do not remove them).
  When hand-entering literature values for A/E, enter IU.
- All CVs are fractions; pooling/shrinkage happens in log space.
- `cv_*` columns are pipeline-owned — never hand-edit them; change inputs and
  re-run cv_assign.
- Evidence may be combined only through labeled, versioned mechanisms
  (tiers, `+intl` pooling); never mix provenance inside one unlabeled value.
- Ingredients whose sparse nutrients rest on wholly-unverifiable AI estimates
  (e.g. turkey heart) should be avoided in recipes.
