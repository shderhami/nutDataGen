# Supplement Ash Estimation — Plan

**Status:** **COMPLETE, AUDITED & VALIDATOR-VERIFIED** — executed 2026-08-07, audited 2026-08-08 (§15), recipeFormulator independent validator run on all 8 affected recipes 2026-08-08 (§15.5: 5 clean passes; recipe 4 fails on the predicted Ca shortfall; recipes 1 & 6 fail on pre-existing conditions not caused by this effort). All §11 acceptance criteria satisfied. Remaining follow-ups: recipe 4 reformulation (Shahab), recipe 6 vitamin E & recipe 1 review (pre-existing), commit of artifacts, recipe-1 yeast unit fix (spawned task). Bone meal detail: [../bone_meal_nutrient_derivation.md](../bone_meal_nutrient_derivation.md).
**Date:** 2026-08-07
**Goal:** Populate accurate Ash values for all 17 `category='Supplement'` ingredients so dry-matter (DM) macro analysis of recipes is correct.

**Scope:** `ingredient_nutrients` Ash rows (and, where decided below, Carbohydrate rows) for the 17 supplements; three data bugs found during the audit that corrupt DM math independently of ash; verification against labels, USDA data, and stoichiometry. No code changes to nutDataGen or recipeFormulator.

---

## 1. Why

15 of 17 supplements have `Ash = 0` with source `not_in_supplement`. Most of these are mineral salts — largely or entirely ash. On a DM basis this error is severe: e.g., potassium citrate powder is ~64% ash and currently contributes 0. Recipe-level ash %DM is understated and, if NFE is derived by difference anywhere, NFE is overstated by the same mass.

Only three supplements have real values today:

| food_id | Product | Ash | Source | Verdict |
|---|---|---|---|---|
| 10026 | Nutritional yeast flakes | 5.65 g / 100 g | USDA FDC 175043 | Keep |
| 10034 | KI drops (MaryRuth) | 0.000164 g / drop | product_label (stoichiometric KI mass) | Keep |
| 10012 | Chicken bone meal | 12.8 g / 125 g | "literature: AI" | Verify (Phase 0) — AI-sourced, and the row's other proximates fail sanity checks |

## 2. Evidence base — verified facts

- **Value basis:** `ingredient_nutrients.value` is per **label serving** = `portion_qty` × `base_unit`. Confirmed in recipeFormulator `src/calculators/nutrient_pipeline.py` (step 1 divides by `portion_qty`). All ash estimates must be entered on this basis.
- **Stoichiometry closes on the existing data** (strong evidence the label claims in the DB are reliable):
  - Morton salt: 590 mg Na × 2.5421 = 1.500 g NaCl = exactly the ¼-tsp label serving mass; Cl 910 mg × 1.6485 = 1.500 g NaCl as well.
  - Bulk zinc gluconate: label Zn density 40 mg / 285 mg = 14.0% vs pure zinc gluconate 14.35%.
  - MaryRuth KI: iodine 125 µg × 1.3081 = 163.5 µg = the stored ash value.
- **Recipe usage** (prioritization): vitamin E and yeast in 7 recipes; taurine and KI drops in 6; manganese, iron, choline in 5; copper and zinc NOW in 4; salt and K-citrate in 3; KI stock, bone meal, bulk zinc in 1; CaCO₃, Rx Essentials, K-gluconate in 0.

## 3. Agreed decisions (2026-08-07)

1. **Purity basis: theoretical.** For single-ingredient powders, assume the pure compound (labels legally round down). The label-derived value becomes the lower bound of the stored uncertainty.
2. **Mass closure: decided per product** in §7, with a material-impact estimate for each.
3. **Data bugs are in scope** — fixed in Phase 0, before ash, because they distort DM more than ash does.
4. **Excipient ash is included** — a bounded allowance per capsule/tablet product derived from the online ingredient deck, documented in the row comment and reflected in the uncertainty.

## 4. Method — ashing chemistry

Crude ash = residue after combustion at 550–600 °C (AOAC 942.05, the basis of FEDIAF/AAFCO ash). For a known chemical form the residue is deterministic:

| Element in salt | Residue at 550–600 °C | Factor (g residue / g element) |
|---|---|---|
| K (gluconate, citrate) | K₂CO₃ | 1.7674 |
| Ca (carbonate) | CaCO₃ (stable at this temp) | 2.4972 |
| Na (chloride) | NaCl (unchanged) | 2.5421 |
| Zn (gluconate) | ZnO | 1.2447 |
| Fe (bisglycinate) | Fe₂O₃ | 1.4297 |
| Cu (glycinate) | CuO | 1.2518 |
| Mn (citrate) | Mn₃O₄ (range MnO 1.2911 – MnO₂ 1.5828) | 1.3883 |
| I (as KI) | KI (partial volatilization possible; trace amounts, ignore) | 1.3081 |

Fully organic actives (taurine, choline bitartrate, inositol, tocopherols) leave ~0 residue. Excipient allowances: rice flour ash ≈ 0.6% of its mass; cellulose/hypromellose ≈ 0.2%; silicon dioxide = 100%; magnesium stearate → MgO ≈ 6.8% of its mass; croscarmellose sodium → Na₂CO₃ ≈ 15% of its mass.

Molar masses (PubChem/CRC): Ca 40.078, CaCO₃ 100.087, Na 22.990, NaCl 58.443, K 39.098, K₂CO₃ 138.205, Zn 65.38, ZnO 81.38, Fe 55.845, Fe₂O₃ 159.688, Cu 63.546, CuO 79.545, Mn 54.938, Mn₃O₄ 228.812, I 126.904, KI 166.003. K₃-citrate·H₂O 324.41 (ash fraction 63.9%), anhydrous 306.40 (67.7%). Zinc gluconate 455.70 (ash fraction 17.86%).

---

## 5. Phase 0 — data bug fixes (do first)

| # | Bug | Evidence | Fix |
|---|---|---|---|
| 0.1 | **Morton salt `grams_per_unit` = 1.5 g/tsp; true value ≈ 6 g/tsp.** 1.5 g is the ¼-tsp *serving* weight. As stored, a serving weighs 0.375 g yet contains 590 mg Na → 157% sodium by mass. Every recipe using salt understates its mass (and DM) 4×. | Morton label: ¼ tsp = 1.5 g, 590 mg Na. Na and Cl both back-calculate to exactly 1.5 g NaCl. | `UPDATE ingredients SET grams_per_unit = 6.0 WHERE food_id = 10025;` then re-check the 3 recipes using it. |
| 0.2 | **KI stock K = 235 mg/mL; should be ≈ 0.236 mg.** 765 µg iodine brings only 765 × (39.098/126.904) = 235.7 **µg** K. A µg value was entered in a mg column. | Stoichiometry of KI. | Set K value to 0.000236 g-equivalent in its stored unit (0.2357 mg). |
| 0.3 | **KI stock Water = 0.764 g/mL; should be ≈ 0.999 g.** The stored value is exactly 1 − 0.2358 — the same µg/mg error propagated into water-by-difference. Adds 0.235 g phantom DM per mL. | Arithmetic identity; dilute aqueous solution ≈ 0.999 g water/mL. | Set Water = 0.999 g/mL. |
| 0.4 | **Bone meal proximates implausible** (per 125 g: CP 9.5%, carb 12.7%, water 57%). Raw ground chicken frames run ~15–17% CP and ~0–1% carb; bone contributes no carbohydrate. AI-sourced — the standing rule is to validate independently. | Row source = "literature: AI"; memory rule `validate-ai-suggestions-independently`. | Re-derive CP/fat/carb/ash/water from USDA poultry + rendering literature (NRC 2006 in Docs/); expect ash ≈ 10–14% as-fed (≈ 24–30% DM), carb ≈ 0. |

All Phase 0 changes: `pg_dump` backup first, single transaction, update `comment` + `last_updated` on every touched row.

## 6. Phase 1 — online label collection

For each product, fetch from the manufacturer page (preferred) and the Amazon listing already stored in `ingredients.amazon_url`:

1. Serving size and serving mass; capsule/tablet fill mass if stated.
2. Elemental claim(s) and the **chemical form** of each active (e.g., "ferrous bisglycinate (Ferrochel)", "zinc gluconate", "choline bitartrate").
3. Full excipient deck ("Other ingredients"), in order.
4. Any COA / spec sheet (BulkSupplements publishes COAs; NOW publishes product specs).

Record results in `data/supplement_labels/labels.csv` with columns: `food_id, product, url_used, serving_desc, serving_g, active_form, elemental_claim, other_ingredients, coa_url, fetched_date`. This file is the citable provenance for every Phase 2 number.

Products needing form confirmation (assumed forms in §7 to be verified): 10011 (Mn citrate?), 10022 (Fe bisglycinate?), 10023 (Cu glycinate — bisglycinate?), 10032 (choline bitartrate? Choline & Inositol blend — the DB capsule mass 0.8174 g suggests a 500 mg combined active), 10039/10040 (excipient decks), 10006 (full deck — see Phase 3).

## 7. Phase 2 — stoichiometric computation

Preliminary values (finalize after Phase 1 confirms forms/decks). "Serving" = `portion_qty` × `grams_per_unit` (post-Phase-0 masses). CV encodes the label-vs-theoretical spread plus excipient uncertainty.

| food_id | Product | Serving | Calculation | Ash (g/serving) | %mass | CV | Closure decision (Carbohydrate row) |
|---|---|---|---|---|---|---|---|
| 10003 | Taurine powder | 1.0 g | pure organic → 0 | 0 | 0% | — | Leave carb 0. **Flag, decision deferred:** Kjeldahl N×6.25 would call taurine ~70% CP; currently CP=0. Nutritionally defensible either way — decide when protein DM accuracy matters. |
| 10004 | CaCO₃ powder | 1.7 g | pure CaCO₃, residue = CaCO₃ | **1.70** | 100% | 4% (lower bound: label 600 mg Ca → 1.498 g) | Carb 0; closes by construction. |
| 10008 | KI stock | 1 mL | 765 µg I × 1.3081 | **0.0010** | 0.1% | 5% | Carb 0; water 0.999 (Phase 0) closes it. |
| 10011 | Manganese (Pure Enc.) | 0.1662 g | 8 mg Mn × 1.3883 + capsule ≈ 0.2 mg | **0.0113** | 6.8% | 12% (Mn oxide range 10.3–12.7 mg) | Carb 0. Organic remainder ~0.15 g/capsule; ≤5 capsules/recipe → immaterial. |
| 10015 | Vitamin E liquid | 0.0315 g | oil → 0 | 0 | 0% | — | Carb 0. |
| 10022 | Iron 18 mg (NOW) | 0.3984 g | 18 mg Fe × 1.4297 + rice-flour allowance ≈ 1.5 mg | **0.0273** | 6.9% | 10% | Carb 0; immaterial at capsule doses. |
| 10023 | Copper glycinate | 0.1510 g | 2 mg Cu × 1.2518 + excipient ≈ 0.3 mg | **0.0028** | 1.9% | 15% | Carb 0. |
| 10024 | Zinc gluconate powder (bulk) | 0.285 g | pure salt: 285 mg × 17.86% | **0.0509** | 17.9% | 3% (lower bound label: 0.0498) | **Set carb = 0.234 g** (serving − ash): pure gluconate, organic fraction is real, energy-bearing DM. Gram-based item → FEDIAF ME formula picks it up (~0.8 kcal/serving; verify recipe deltas in Phase 5). |
| 10025 | Iodized salt (Morton) | 1.5 g (post-fix) | NaCl + calcium silicate; dextrose <0.1% | **1.497** | 99.8% | 1% | Carb 0 (dextrose negligible). |
| 10026 | Nutritional yeast | 100 g | keep FDC 175043 | 5.65 | 5.65% | — | No change. |
| 10032 | Choline (NOW) | 0.8174 g | bitartrate + inositol organic → ~0 + excipient ≈ 2 mg | **0.002** | 0.2% | 50% (tiny absolute) | **Set carb** only if closure matters: serving is ~100% organic DM currently invisible to by-difference math; at 5 recipes × ~1–2 caps this is ~1–1.6 g DM/recipe — decide after Phase 5 impact query; default: set carb = 0.815 g with comment "organic actives, by-difference convention". |
| 10034 | KI drops | 0.0413 g | keep (already stoichiometric) | 0.000164 | 0.4% | — | No change. |
| 10039 | Zinc gluconate (NOW tab) | 0.5303 g | 50 mg Zn × 1.2447 + excipient allowance ≈ 4 mg | **0.066** | 12.5% | 10% | **Set carb = serving − ash − fiber(0.22) ≈ 0.24 g** — tablet binder + gluconate organics; used in 4 recipes. |
| 10040 | K gluconate (NOW tab) | 0.700 g | 99 mg K × 1.7674 + excipient ≈ 4 mg | **0.179** | 25.6% | 6% | **Set carb ≈ 0.47 g** (gluconate organics + binder − fiber 0.05). Not in any recipe yet; do it for consistency. |
| 10041 | K citrate powder (NOW) | 1.4 g | pure K₃-citrate·H₂O: 1.4 × 63.9% | **0.895** | 63.9% | 6% (bounds: label 0.792 – anhydrous 0.948) | **Set carb = 0.505 g** (citrate organics; ~3.5 kcal/g real energy). Used in 3 recipes — the single biggest ash correction in active use. |
| 10012 | Chicken bone meal | 125 g | Phase 0.4 literature re-derivation | ~12.8–15 (verify) | ~10–12% | per lit. spread | Re-derive whole row; set carb ≈ 0. |
| 10006 | Rx Essentials | 4.0 g | Phase 3 | TBD (bracket 0.2–0.6) | 5–15% | 25–30% | Decide in Phase 3 with the deck in hand. |

**Closure rule applied above:** set Carbohydrate-by-difference only where the invisible organic fraction exceeds ~5% of serving mass **and** the product appears in recipes (plus 10040 for family consistency); otherwise leave 0. Rationale: below that, recipe-level DM shift is < 0.1% for typical inclusion rates. Phase 5 quantifies the actual per-recipe deltas before anything is committed.

## 8. Phase 3 — Rx Essentials reconstruction (10006)

Multi-nutrient blend on an unknown carrier; the carrier dominates ash. Steps:

1. Phase 1 fetch: full supplement-facts panel + ingredient deck from Rx Vitamins (manufacturer) — the Amazon listing may truncate it.
2. Attribute each labeled mineral to its salt form (deck order + typical forms) → stoichiometric salt ash.
3. Identify carrier(s); take carrier ash from USDA bulk CSVs (e.g., rice bran ≈ 7–10%, whey ≈ 8%, brewer's yeast ≈ 6–7%).
4. Sum; sanity-bound below by DB minerals (Ca 25 + K 20 + Mg 1.75 + Zn 1 mg → salts alone ≥ ~0.1 g/tsp).
5. If the deck is ambiguous, email Rx Vitamins for a COA; store the bracketed estimate with CV 25–30% meanwhile.

Not currently used in any recipe, so accuracy pressure is low — but do it properly once.

## 9. Phase 4 — verification & cross-checks

1. **Elemental consistency:** for every supplement, `ash ≥ Σ(mineral elements × their residue factors)` and `ash ≤ serving mass − water`. SQL check over all 17.
2. **Mass closure audit:** `|serving − water − CP − fat − ash − carb|` per supplement; must be ≤ tolerance for closure products, and the residual for non-closure products must equal the documented organic fraction.
3. **Independent sources** (per the standing memory rule — no AI value trusted unverified): salt vs USDA FDC table salt (ash 99.8 g/100 g); yeast already FDC; molar masses vs PubChem; NOW/BulkSupplements COAs where published.
4. **Recipe-level impact report:** for each of the 7+ affected recipes, before/after ash %DM, carb/NFE %DM, and total DM. This is the deliverable that proves the fix and catches surprises (esp. the salt mass fix and K-citrate ash).

## 10. Phase 5 — DB write & downstream re-validation

1. `pg_dump` backup of `cat_food_formulator` to `backups/` first.
2. One transaction; per row: `value`, `source` (`stoichiometric` / `label_reconstruction` / `literature`), `comment` (the actual formula, e.g. "99 mg K × 1.7674 (K→K₂CO₃, AOAC 550°C) + 4 mg excipient allowance; label via labels.csv 2026-08-07"), `estimated_se`/CV per §7, `last_updated`.
3. Mirror any schema-relevant conventions to the test DB if tests depend on supplement fixtures.
4. Re-run recipeFormulator's independent validator on affected recipes; confirm the Phase 4.4 report numbers reproduce.
5. Commit `labels.csv` + this plan's final numbers; note in the sibling-repo workflow that published recipes may need re-publishing if DM macros are displayed anywhere.

## 11. Acceptance criteria

- No supplement has ash = 0 unless it is genuinely organic/oil (10003, 10015; 10032 ≈ 0 allowed).
- Every ash row's comment contains a reproducible calculation traceable to `labels.csv` or a cited source.
- Elemental-consistency and closure audits (§9.1–9.2) pass for all 17.
- The three Phase 0 bugs are fixed and the salt-using recipes re-validated.
- Before/after recipe impact report reviewed by Shahab before the transaction is committed.

---

## 12. Phase 0 execution log (2026-08-07)

Backup: `backups/cat_food_formulator_pre_phase0_ash_20260807_193229.dump` (pg_dump 18.4 custom format; server is PG 17 — restore with `pg_restore` ≥ 17).

### 12.1 Fix 0.1 — Morton salt serving mass (food_id 10025)

`ingredients.grams_per_unit`: **1.5 → 6.0 g/tsp**. 1.5 g is Morton's ¼-tsp serving weight, not the per-tsp weight; both Na (590 mg × 2.5421 = 1.500 g NaCl) and Cl (910 mg × 1.6485 = 1.500 g NaCl) back-calculate to exactly the 1.5 g serving. Nutrient rows unchanged (they are per serving, so recipe Na is unaffected); only mass/DM was wrong. Salt-using recipes (4, 7, 8, 13) each gain the missing 3/4 of the salt mass — e.g., recipe 4's salt: 0.19 g → 0.77 g.

### 12.2 Fix 0.2 — KI stock potassium (food_id 10008, row id 373)

Potassium: **235 mg → 0.235689 mg per 1 mL serving** (µg value had been entered in the mg column). Stoichiometric: 765 µg I × (39.0983/126.90447 K/I molar ratio) = 235.7 µg. Source changed `product_label` → `stoichiometric`.

### 12.3 Fix 0.3 — KI stock water (food_id 10008, row id 397)

Water: **0.764235 → 0.999 g per 1 mL serving**. Old value was exactly 1 − 0.2358 — the phantom 0.236 g of "potassium" from bug 0.2 propagated into water-by-difference, creating 0.235 g phantom DM per mL. Dilute aqueous KI ≈ 0.999 g water/mL.

### 12.4 Fix 0.4 — chicken bone meal re-derivation (food_id 10012)

**Product identity (from Shahab, 2026-08-07):** pressure-cooked bone paste — 1000 g raw chicken bones + 250 mL water, cooked closed and blended. Mass conservation ⇒ the 125 g portion = **100 g raw bone + 25 g water**. Decision: re-derive from literature, do **not** preserve the old AI Ca/P anchors; recipe 4 is reformulated by Shahab.

**Why the old row was wrong:** AI-sourced; carb 15.93 g contradicted its own justification; AA justifications cited CP anywhere from 12–35%; Ca 7000 mg implied ~18 g bone mineral against a stored ash of 12.8 g.

Executed 2026-08-07 (27 rows: proximates/Ca/P/energy re-derived, AAs ×1.6 and FAs ×0.81 rescaled), then superseded by the full profile re-estimation and clean-bone recalibration of §14. **The complete derivation, all old→new values, calculations, and literature record now live in [../bone_meal_nutrient_derivation.md](../bone_meal_nutrient_derivation.md).**

---

## 13. Phase 1–3 execution log (2026-08-07) — labels collected, ash computed, APPROVED & WRITTEN (see §13.6)

Phase 1 ran as three parallel research agents; every fact verified at rendering URLs (manufacturer pages preferred; Amazon pages identified by ASIN via redirect only). Full provenance: `data/supplement_labels/labels.csv`. Rx Vitamins' own PDFs are the panel source for 10006.

### 13.1 Label findings that changed the Phase 2 math

1. **All chemical forms confirmed** as §7 assumed, except 10011 (Pure Enc. manganese) which is a **dual aspartate/citrate** salt — irrelevant to ash (residue depends only on the 8 mg Mn).
2. **Compound masses are on the labels** (not just elemental): Fe capsule = 90 mg Ferrochel bisglycinate; choline capsule = 730 mg bitartrate; Zn tablet = 403 mg gluconate; K tablet = 619 mg gluconate; K-citrate serving = 1,400 mg compound (= entire 1.4 g serving → 100% pure); CaCO₃ serving = 1,700 mg compound (= entire serving → 100% pure).
3. **Excipient decks verbatim**: 10022 rice flour/hypromellose/stearic acid/**SiO₂**; 10032 hypromellose/ascorbyl palmitate/**SiO₂**; 10039 MCC/coating/Mg-stearate/**SiO₂**; 10040 MCC/stearic acid/**SiO₂**/Mg-stearate; 10011+10023 cellulose only; 10003, 10004, 10024, 10041 no other ingredients.
4. **Morton confirmed exactly**: ¼ tsp = 1.5 g, Na 590 mg; deck "salt, calcium silicate, dextrose, potassium iodide"; Morton FAQ: calcium silicate <0.5%, dextrose 0.04%.
5. **BulkSupplements COA spec**: NLT 90% zinc gluconate, NLT 12.3% Zn (label 14.0% Zn — consistent).
6. **BUG 0.5 — Rx Essentials serving basis — RESOLVED, no DB change**: manufacturer's current web PDFs put the amounts per ½ tsp, but Shahab's physical jar label (photo, 2026-08-07) reads **"Guaranteed Analysis per 1 teaspoon (4 g)"** with the same amounts — a label-era difference (like the CaCO₃ case in labels.csv). The DB's 1 tsp = 4 g basis matches the jar actually in use, so it stands; ash was computed on that basis (§13.2). Still open (minor, out of ash scope): DB omits label items (vit C 20 mg, PABA 1 mg, spirulina 25 mg, milk thistle 10 mg, GLA 5 mg, kelp 25 µg — an iodine source), and the label nutrient is niacinamide (DB "Niacin") and D2 ergocalciferol (DB "Vitamin D").
7. **NEW FLAG — recipe 1 stores yeast (10026) in `unit='g'`** while `base_unit='tbsp'`; any consumer multiplying by `grams_per_unit` without checking `ri.unit` mis-scales it 8×. Verify recipeFormulator's handling separately.
8. **Unit masses label-unverified** (labels state volume/count only): NOW drop 0.0315 g, capsule/tablet masses (0.3984/0.8174/0.5303/0.700/0.1662/0.1510 g), MaryRuth drop 0.0413 g (label: 0.035 mL/drop; implies density 1.18 g/mL — plausible for glycerin/water). DB values retained as plausible; recorded as DB-sourced, not label-sourced.
9. Minor closure note: 10015 vitamin E drop is 100% oil (tocopherol in olive oil) but DB fat = 0; ~0.03 g fat/drop unbooked. Immaterial (<0.2 g/recipe); not changed.

### 13.2 Final ash values (approved by Shahab and written 2026-08-07; 10006 row superseded — see §13.6)

Per label serving (= `portion_qty` × base_unit). "Residue" chemistry per §4. min/max stored in `min_value`/`max_value`.

| food_id | Product | Ash g/serving (min–max) | Calculation |
|---|---|---|---|
| 10003 | Taurine | **0** (unchanged) | pure free-form taurine, fully organic; provenance comment only |
| 10004 | CaCO₃ | **1.700** (1.498–1.700) | serving = 1,700 mg CaCO₃ (label), stable ≤600 °C; min = label-Ca basis 600×2.4972 |
| 10006 | Rx Essentials | **0.220** (0.15–0.30) per ½ tsp ≈ 2.52 g — **held pending bug 0.5 decision** | salts: Ca 25→CaCO₃ 62.4 + K 20→K₂CO₃ 35.4 + Mg 1.75→MgO 2.9 + Zn 1→ZnO 1.2 + pantothenate-Ca ≈1.0 ⇒ ~103 mg; carrier ~2.2 g (molasses ~9% ash / defatted liver ~6% / maltodextrin ~0.5%, split unknown, ≈ thirds) ⇒ ~110 mg; spirulina ≈2 mg |
| 10008 | KI stock | **0.001001** | 765 µg I × 1.3081 = 1.0 mg KI |
| 10011 | Mn capsule | **0.0114** (0.0106–0.0130) | Mn₃O₄ = 8×1.3883 = 11.11 mg + cellulose ≈0.3 mg; range = MnO–MnO₂ residue bounds |
| 10015 | Vitamin E | **0** (unchanged) | d-alpha tocopherol in olive oil; provenance comment only |
| 10022 | Iron capsule | **0.0292** (0.0257–0.0330) | Fe₂O₃ = 18×1.4297 = 25.73 mg + rice flour ≈1.1 (0.6%×~180 mg) + SiO₂ ≈2 + shell ≈0.2; min = Fe₂O₃ alone |
| 10023 | Cu capsule | **0.0028** (0.0025–0.0033) | CuO = 2×1.2518 = 2.50 mg + cellulose ≈0.3 mg (no SiO₂ in deck) |
| 10024 | Zn gluconate powder | **0.0509** (0.0498–0.0509) | theoretical pure: 285 mg × 17.86% (ZnO mass fraction of zinc gluconate) = 50.9 mg; min = label-Zn basis 40×1.2447 |
| 10025 | Iodized salt | **1.499** (1.492–1.500) | 1.5 g − dextrose 0.04% (0.6 mg); NaCl + calcium silicate + KI all survive ashing |
| 10032 | Choline capsule | **0.0030** (0.0010–0.0070) | bitartrate fully combusts; SiO₂ ≈2.5 mg + shell ≈0.2 mg |
| 10034 | KI drops | **0.000164** (unchanged) | already stoichiometric; verified 125 µg I × 1.3081 = 163.5 µg |
| 10039 | Zn tablet | **0.0672** (0.0622–0.0720) | ZnO = 50×1.2447 = 62.2 mg + SiO₂ ≈4 + MgO (stearate) ≈0.5 + MCC ≈0.4; min = ZnO alone |
| 10040 | K gluconate tablet | **0.1800** (0.1750–0.1850) | K₂CO₃ = 99×1.7674 = 175.0 mg + SiO₂ ≈4 + MgO ≈0.5 + MCC ≈0.4; min = K₂CO₃ alone |
| 10041 | K citrate powder | **0.8950** (0.7918–0.9472) | monohydrate basis: 1,400 mg × 63.90% = 894.6 mg (USP grade is typically monohydrate); min = label-K 448×1.7674; max = anhydrous 67.66% |
| 10012 | Bone meal | 11.0 — already written in Phase 0.4 | see §12.4 |
| 10026 | Yeast | 5.65/100 g — unchanged (USDA FDC 175043) | — |

### 13.3 Carbohydrate closure (per §3 decision 2 and §7 rule)

Set where the combustible organic fraction >5% of serving (by-difference convention: carb = serving − water − CP − fat − ash; carb *includes* fiber, NFE = carb − fiber downstream):

| food_id | Carb g/serving | Arithmetic |
|---|---|---|
| 10024 | 0.2341 | 0.285 − 0.0509 |
| 10032 | 0.8144 | 0.8174 − 0.0030 |
| 10039 | 0.4583 | 0.5303 − 0.00478 (fat) − 0.0672 |
| 10040 | 0.5050 | 0.700 − 0.015 (fat) − 0.180 |
| 10041 | 0.5050 | 1.400 − 0.895 |

Left at 0: 10004, 10008, 10011, 10022, 10023, 10025 (organic fraction negligible or <5%), 10003 (taurine CP question deferred per §7), 10015 (oil; see §13.1.9).

### 13.4 Recipe impact report (computed against live DB, Phase 0 already applied)

| Recipe | DM g | Ash before → after (g) | Ash %DM before → after | Carb Δ (g) |
|---|---|---|---|---|
| 1 full chicken | 197 | 10.23 → 10.25 | 5.20 → 5.21 | +0.04 |
| 2 X | 31 | 0.85 → 0.85 | 2.72 → 2.72 | 0 |
| 4 Mix Protein Growth Starter | 195 | 11.98 → 12.75 | 6.16 → 6.55 | 0 |
| 5 Chicken and salmon meal | 199 | 10.59 → 11.66 | 5.31 → 5.85 | +2.20 |
| 6 Chicken Recipe for Indoor Adult | 201 | 10.68 → 12.08 | 5.30 → 6.00 | +1.91 |
| 7 Beef and pork meal | 200 | 10.68 → 10.95 | 5.35 → 5.49 | +1.85 |
| 8 Turkey meal | 204 | 11.95 → 12.99 | 5.86 → 6.37 | +0.88 |
| 9 Beef and chicken meal | 199 | 11.86 → 11.87 | 5.96 → 5.96 | +1.75 |
| 13 Chicken, lamb and salmon meal | 201 | 11.35 → 12.10 | 5.65 → 6.03 | +0.75 |

Largest shift: recipe 6, +0.70 ash %DM points (driven by K-citrate). All shifts are upward, as expected — zero-ash supplements were hiding real mineral mass.

### 13.5 Write plan (on approval)

One transaction: 13 Ash rows (11 new values + 2 provenance-comment-only for 10003/10015), 5 Carbohydrate rows, `source='stoichiometric'` (or `'label_reconstruction'` for 10006 if unheld), full calculation in each `comment`, `min_value`/`max_value` per §13.2, `last_updated=CURRENT_DATE`. 10006 ash + bug 0.5 handled per Shahab's decision. Fresh `pg_dump` first.

### 13.6 Write executed & verified (2026-08-07)

Backup: `backups/cat_food_formulator_pre_phase2_ash_20260807_223317.dump`. One transaction, 19 rows:

- 11 Ash values per §13.2 + 2 provenance-only updates (10003, 10015 → verified zeros, `source='stoichiometric'`).
- **10006 Rx Essentials written at the jar-label basis** (bug 0.5 resolved — §13.1.6): Ash = **0.29 g per 1 tsp (4 g)** serving (min 0.20, max 0.40), `source='label_reconstruction'`. Same salt arithmetic as §13.2 (~103 mg) + carrier rescaled to ~3.65 g (~189 mg) + spirulina ~2 mg.
- 5 Carbohydrate closure rows per §13.3.

Post-write verification, all passing:

1. Mass-consistency (`ash ≤ serving − water`): **17/17 OK**.
2. Only zero-ash rows remaining are the genuine organics (taurine, vitamin E) — acceptance criterion §11.1 met.
3. Recipe-level ash reproduces the §13.4 "after" column exactly (e.g., recipe 4: 12.75 g / 6.55 %DM; recipe 6: 12.08 g / 6.00 %DM).
4. Every written row carries its calculation in `comment`, traceable to `data/supplement_labels/labels.csv` — criterion §11.2 met.

**Plan complete.** Open follow-ups: recipe 4 reformulation (Shahab; Ca basis changed in Phase 0.4); bone meal micronutrient rows still AI-basis (§12.4); recipe-1 yeast `unit='g'` vs `base_unit='tbsp'` handling in recipeFormulator (spawned as separate task); 10006 minor label gaps (§13.1.6); taurine-as-CP question (§7, deferred); 10015 fat-closure note (§13.1.9).

---

## 14. Bone meal full profile re-derivation, recalibration & literature validation (2026-08-07/08)

Follow-up to §12.4, requested by Shahab: the AI amino-acid/fatty-acid shapes and all micronutrients were discarded and re-estimated from measured sources (USDA SR28 gelatin/chicken items, Spitze 2003, NIST bone-reference certificates), then recalibrated after Shahab confirmed the bones are **stripped quite clean** (70/30 collagen/muscle CP model, 90/10 depot/intramuscular fat, ash 12.5 g, Ca 4750 mg, P 2250 mg, taurine 25 mg per 125 g portion), and finally validated by two independent literature-search agents (all parameters SUPPORTED or bracketed; two adjustments: Zn 2.4→3.0 mg per NIST certified ash-Zn, vitamin D 12→7 IU per Jakobsen 2021).

**All detail — models, formulas, worked examples, the complete old→new change tables, the full source list including discounted discrepant papers, validation verdicts, and revision history — is in [../bone_meal_nutrient_derivation.md](../bone_meal_nutrient_derivation.md).** DB row comments referencing "plan sec.14.x" resolve there.

Backups: `…pre_bonemeal_profiles_20260807_225640.dump`, `…pre_bonemeal_recal_20260807_234016.dump`, `…pre_validation_adj_*.dump`.

---

## 15. Implementation audit (2026-08-08)

Independent re-verification of everything this plan executed. Method: all conversion factors re-derived from IUPAC 2021 atomic weights (not the plan's own §4 table); every stored ash value recomputed from the DB's element rows; every consistency bound re-run as SQL; every promised step checked against what actually happened.

### 15.1 Verified correct

1. **All 10 stoichiometric factors** (Ca→CaCO₃ … I→KI, K-citrate·H₂O ash fraction, Zn-gluconate ZnO fraction) reproduce to 4 decimal places from independent atomic weights.
2. **All 14 computed ash values** recompute within ≤ 0.4 mg of stored values (largest: 10041 at 0.895 vs exact 0.8946 — rounding).
3. **Range sanity** (min ≤ value ≤ max): all rows pass.
4. **Mass bound** (ash ≤ serving − water): 17/17 pass. **Elemental floor** (ash ≥ Σ cation residues): 17/17 pass — this §9.1 check had never been formally run at write time (see 15.3.1); it passes now.
5. **Carbohydrate closure arithmetic** (serving − water − CP − fat − ash): exact for all 5 closure products.
6. **Phase 0 fixes still in place**: salt `grams_per_unit` 6.0; KI stock K 0.235689 mg, Water 0.999 g.
7. **Documented values match the DB** (§13.2/§13.6 tables vs live rows), and §13.4's recipe impact was reproduced from the live DB at write time (§13.6.3).
8. **§7's promised ME-delta verification for 10024** (the only gram-based supplement whose new carb feeds the FEDIAF ME formula), now done: recipe 1 uses 0.0532 g → **+0.15 kcal** — negligible, as predicted.

### 15.2 Defects found (and disposition)

1. **10032 comment/value mismatch** — comment arithmetic gave 2.7 mg but the stored value is 3.0 mg (an intentional round-up within the 1–7 mg range that the comment didn't explain). *Fixed: comment now states the rounding.*
2. No numerical defects found. The 10022 (−0.17 mg) and 10040 (−0.13 mg) recomputation deltas trace to rounded excipient allowances inside their documented uncertainty — noted, not fixed.

### 15.3 Promised but not executed (open items)

1. **§9.1 elemental-consistency SQL "over all 17"** — never run during Phases 4–5; the §13.6 verification only ran the mass bound. Closed by this audit (passes).
2. **§10.4 "re-run recipeFormulator's independent validator on affected recipes"** — **still not done.** The recipe impact was computed via direct SQL, but the sibling repo's own validator has not been run against the new values. This is the one remaining substantive step; recipes 4/5/6/8/13 carry the largest ash shifts, and recipe 4 additionally has the bone meal re-derivation.
3. **§10.5 "commit labels.csv + plan"** — all artifacts (plan, labels.csv, bone_meal_nutrient_derivation.md) remain uncommitted in the working tree. Awaiting Shahab's go-ahead.
4. **§10.3 test-DB mirror** — `cat_food_formulator_test` holds 884 stale supplement nutrient rows (pre-fix values). No schema change occurred, so tests that build their own fixtures are unaffected; any test that *reads* pre-seeded supplement data would see old values. Low risk; verify when the test suite next runs.

### 15.4 Observations (no action required)

- The 10 untouched Carbohydrate rows on non-closure supplements still carry `source='not_in_supplement'` — deliberate (their carb genuinely is ~0), but the label now understates what we know; cosmetic upgrade possible.
- Energy rows for the tablet/capsule closure products remain 0 — inert by design (non-gram items take ME from `ingredients.me_kcal_per_unit`, not the Energy row).
- Pre-existing, out of scope: recipe 1 stores yeast in `unit='g'` vs `base_unit='tbsp'` (spawned task); salt iodine row 61.2 µg vs current label ~67.5 µg.

**Verdict:** implementation is numerically sound and matches its documentation; the audit's substantive finding is process-level — the recipeFormulator validator re-run (§10.4) is the one step still owed before the plan's §11.4 criterion is fully satisfied.

### 15.5 §10.4 closed — recipeFormulator independent validator run (2026-08-08)

All 8 supplement-bearing recipes evaluated via `--recipe … --cross-validate` (read-only; evaluation mode runs Stage 1 — the full independent recomputation from raw DB rows against FEDIAF minima/maxima, enforced ratios, EU legal maxima, and advisory ceilings; Stages 2–3 exist only in optimization mode). Each recipe used its stored Ca:P override and a profile matching its life stage. Logs in the session scratchpad (`xval_<id>.log`).

| Recipe | Result | Notes |
|---|---|---|
| 5, 7, 8, 9, 13 | **PASS** (43/43 checks, 0 warnings) | new supplement data flows cleanly; no integrity errors, no NFE clamps |
| 4 (growth) | FAIL — **expected** | Ca 2.34 < 2.50 g/1000 kcal; Ca:P 1.09 < 1.20 — the direct, predicted consequence of the bone meal Ca correction (§14). This is the reformulation Shahab already owns. Taurine passes (1.68 vs 0.63 min). |
| 6 | FAIL — **pre-existing** | FEDIAF fish-oil vitamin E rule: 23.9 IU < required 27.1. No Vitamin E or PUFA row of any recipe-6 ingredient was touched in this effort (verified by `last_updated` query); recipe predates the peroxidation-rule/editorial handling that recipes 8/13 were formulated under. |
| 1 | FAIL — **pre-existing + distorted evaluation** | Choline/iodine/taurine below minima, Ca:P 0.94. Not attributable to this effort (no Ca/P source touched in recipe 1); additionally its yeast row (13.94 stored with `unit='g'`, base tbsp) is read as 13.94 tbsp = 111.5 g by evaluation — the known unit-mismatch bug (spawned task) inflates yeast 8×, so this evaluation is unreliable until that row is fixed. Recipe 1 likely needs review independent of ash. |

**Conclusion:** acceptance criterion §11.4 is now fully satisfied. The validator confirms the corrected data produces clean, internally consistent recipe analyses; the only failures are the predicted recipe-4 calcium shortfall and two pre-existing conditions (recipe 6 vitamin E rule, recipe 1 age/unit issues) that this effort surfaced but did not cause.
