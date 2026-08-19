# Foundation reconciliation — session record (2026-08-18)

**Trigger:** Shahab's magnesium challenge on butternut squash (a recipe went
infeasible after the sweep's 34→16 fix). Re-verification found USDA's own
Foundation study (2685570, published 2024-04-18, n=8) measuring 14.95 —
unused, because neither the original add flow nor the validation sweep had a
mechanical "check Foundation bulk per cell" step (the sweep's routing doc
pointed at the international tables). Squash's own rows proved the pattern:
8 cells had been foundation-sourced at add time while Ca/Mg/Na/Fe/Mn/folate
sat on SR Legacy with a Foundation n=8 measurement next to them.

**Scope agreed with Shahab:** all Foundation-linked foods; every cell where
the stored row is not foundation-sourced but Foundation bulk carries an
analysed n≥4 value; adopt where defensible.

**Method:** programmatic scan via `intake.usda_bulk.extract_many` (data_type
filtered, unit-converted); adoption thresholds — analysed, n≥4; ranges stored
only when coherent and nonzero-width (bracket + degenerate rules); medians
only inside stored ranges; stats via `database.calculate_statistics`;
targeted international cross-checks where doctrine required (salmon DHA:
FCDB-DK n=12 = 0.657 inside the FND range; pumpkin Fe: AFCD 0.2 / CoFID 0.4
vs the unsupported old 0.8); every row's comment carries the full audit line.

**Applied: 41 cells** (squash Mg first as the trigger fix, then the 40-cell
slate approved by Shahab), across 11 foods:

| Food | Cells |
|---|---|
| 10019 squash | Mg 16→14.95, Ca 48→21.74, folate 27→55, fat, Fe, Na→0, Mn |
| 10036 pumpkin | Ca, Fe 0.8→0.063, P 44→22.3, K 340→472, Na, Cu, Mn, folate 16→31 |
| 10010 egg | folate 47→71 (n=24), ash, Cu→0 (n=22), Mn→0 (n=22) |
| 10031 yolk | vit E 3.84→8.40 IU (n=24), fat 26.5→28.8 (n=24) |
| 10014 salmon | **DHA 1.104→0.585** (n=8; modern-feed era, FCDB corroborates), B12 3.23→5.70, Mn→0 |
| 10016 breast (skin-on) | fat 7.7→4.78 + Fe 0.56→0.35 (reverses sweep manual keeps — USDA's 2025 SAME-FRAME study), K 220→332, P, Na, Cu, Mn, water |
| 10017 tilapia | Na 52→94, B12 1.58→0.76, Fe→0, Cu→0 |
| 10033 rice | fat 0.66→1.03 |
| 10001/10035/10037 | Mn cells + pork-loin fat 8.33→9.47 |

**Skipped (2, deliberate):** egg and chuck PUFA totals — Foundation totals
sit below the component sums; the lamb-convention invariant
(total ≥ Σ components) wins. Foundation corroborates egg's sum within 2%.

**Ceremony:** pg_dump backups (`pre_squash_mg_foundation_*`,
`pre_foundation_reconciliation_*`); full cv_assign re-run signed by Shahab
(2,236 cells, gate PASS; fdc_range tier 92→106); PUFA invariant verified
clean on all foods.

**Formulation consequences flagged:**
- Salmon DHA nearly halved — recipes using salmon as the DHA source need a
  compliance recheck in the formulator.
- Chicken-breast fat 7.7→4.78 changes breast energy density.
- Folates rose across egg/squash/pumpkin (no known constraint pressure).
- Squash Mg drop (the trigger) stands: three continents' analytical programs
  agree; the affected recipe needs a real Mg carrier (corrector supplement
  or a seed ingredient).

**Process fix:** the runbook's §2.3 now opens with rule 0 — check Foundation
bulk for the food's own measurement before anything else; the intake
pipeline already does this structurally for new foods (its report shows the
FND column for every nutrient).
