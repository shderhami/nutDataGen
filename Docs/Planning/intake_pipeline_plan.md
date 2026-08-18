# Plan: programmatic ingredient intake (replacing add-time AI validation)

| | |
|---|---|
| Status | Implementation on `feature/intake-pipeline` (43b7295); this plan formalized 2026-08-18 at the operator's request — written after the first implementation pass, before audit and merge. Gaps found while writing it are tracked in §8. |
| Owner | Shahab (decisions) + in-session agent (implementation) |
| Decision record | Operator approved building this 2026-08-18 ("make the process reproducible for the future ingredients … reliable and error proof"), on a branch, merged only after full test + verify. |

## 1. Problem

Adding an ingredient to `cat_food_formulator` requires 52 validated FEDIAF
nutrient rows. The existing add flow (`main.py`) fetches USDA data live and
asks the Claude API to validate each nutrient (~52 billed calls). The
2026-08-16/17 validation sweep of all 23 whole foods measured how that AI
step actually performs, against nine local reference datasets:

- **Invented values**: egg taurine 6/0.7/7 mg where the literature measures 0.
- **Systematic bias**: white-meat taurine overestimated 2–4× (chicken breast
  33 vs measured 15.9; turkey breast 130 vs measured 30).
- **Wrong rejections** (reverse failures): 3 cases where the AI rejected
  *correct* USDA values (mussel ARA/Cu, yolk DPA).
- **Ungrounded citations**: the AI cites MEXT/CoFID/BLS from parametric
  memory; the sweep found those citations frequently do not match the actual
  tables on disk (which is why the standing rule "validate AI suggestions
  independently" exists).
- **Drift-prone estimates** for sparse nutrients (chloride, iodine, biotin).
- **Cost & reproducibility**: ~52 billed calls per ingredient; a
  credit-exhausted run poisons rows with error text; none of it is
  reproducible after the fact.

Meanwhile the sweep's manual process — compare USDA against the local
international tables with independence screening and decision rules —
produced ~95 defensible corrections and caught every AI failure above. But it
ran as ad-hoc session scripting: hours per food, knowledge held in agent
memory and a runbook, transcription by hand into psql.

## 2. Goals

- **G1 Reproducibility** — every stored row mechanically explainable years
  later: pinned inputs (the hashed datasets in `data/`), versioned code, and
  committed per-ingredient artifacts (spec → report → decisions).
- **G2 Reliability** — the sweep's hard-won parsing quirks and independence
  knowledge encoded once, as code with regression tests, instead of
  re-derived per session.
- **G3 Error-proofing** — typed gates instead of conventions: FEDIAF unit
  conversion fail-loud at every boundary, 52-completeness, bracket coherence,
  PUFA invariant, backup-before-write, orphan cleanup.
- **G4 Traceability** — per-value origin decoding (who actually measured
  what), no unlabeled provenance mixing, citations in every row comment
  (sweep standing rule).
- **G5 Operator in the loop** — the rule engine is advisory; nothing reaches
  the DB without a reviewed decisions file. Judgment calls (region rule,
  frame mismatches, literature anchors) stay human.
- **G6 Zero marginal cost** — no API calls, no billing gate, works offline.
- **G7 A durable process** — one documented path (runbook Phase 1 Path A)
  any future session can follow for any new ingredient.

Non-goals: auto-writing without review; replacing the CV pipeline (cv_assign
still owns cv_* columns); deleting the AI flow (kept as Path B for foods with
zero local-source coverage); supplements (different flow, per-label data).

## 3. Why not improve the existing AI validation instead

Alternatives considered:

| Option | Why rejected |
|---|---|
| Keep AI validation, verify each suggestion manually (status quo after the sweep) | The verification IS the work; the AI step adds billing + noise on top of it. Every accepted value already had to be re-derived from the local tables. |
| Ground the AI with the local tables (RAG over `data/`) | Still nondeterministic run-to-run (fails G1); citation fidelity still model-dependent; large build for an arbitration step the decision rules already cover; still billed. |
| Pure manual process per the runbook | Proven correct but hours/food, transcription error risk (the sweep had a stale-stats slip), and it decays — quirk knowledge lives in memory files, not executable form. |
| **Deterministic pipeline + operator review (chosen)** | The decision rules are mostly mechanical (measured-beats-derived, ±20% with scale floors, derivation decode, echo detection); code applies them identically every time, tests pin the parsing, and humans keep the judgment calls. |

## 4. Design

Five stages, each leaving a committed artifact:

```
data/intake/<slug>.json      SPEC     curated matches per source + frame notes
python -m intake report      EXTRACT  USDA pinned bulk + source adapters
                             COMPARE  echo screen + rule engine (ADVISORY)
   -> <slug>/report.md + proposed_decisions.json
operator review (in chat)    REVIEW   edit decisions = the audit record
python -m intake write       WRITE    gated insert; then cv_assign / cv_intl
```

Key decisions and their reasons:

- **Pinned bulk, not the USDA API**: same input files forever (hashed in
  `data/README.md` and by `cv_assign.dataset_shas`), offline, key-free. The
  API drifts; reproducibility (G1) requires frozen inputs.
- **Adapters own unit conversion**: every value leaves an adapter in the
  nutrient's FEDIAF unit via `fediaf_unit_factor`/mass rescale/kJ→kcal,
  unknown pairs raise. One conversion boundary, not N call sites (G3;
  the mixed-unit wart of 2026-08-17 is the cautionary tale).
- **Per-value origin decoding**: FCDB `Source` sheet, BLS `Datenherkunft`
  (Aggregation = adopted), AFCD `Sampling Details` borrow-sentence scan,
  USDA derivation codes, CoFID underlying refs. Borrowed/computed values
  never count as independent confirmation (G4; kills compilation echo
  chains mechanically).
- **Echo screener**: a foreign food with ≥5 nonzero values identical to USDA
  at <0.5% (and ≥40% of comparables) is flagged ECHO wholesale — the CIQUAL
  copy-row trap from the sweep, automated.
- **Advisory verdicts** (`confirm / usda_only / region_keep / replace_suggest
  / form_defect / adopt_foreign / review / no_evidence`): encode runbook §2.3
  so review time goes to contested rows; the operator can override anything
  in the decisions file (G5).
- **Write gates**: exactly the 52 FEDIAF ids; value+source+comment per row;
  coherent ranges (min=0 censored stats rejected); PUFA total ≥ component
  sum; pg_dump backup; orphan cleanup on failure; AI columns NULL.
- **Artifacts committed to git**: the spec documents the matching, the
  decisions file documents the judgment. Re-running the writer from the
  decisions file reproduces the rows exactly.

## 5. Source coverage

Machine-readable adapters: FCDB-DK (per-value source + min/max/n), BLS-DE,
MEXT-JP (3 volumes; THIAHCL×0.887, total-K), CIQUAL-FR (censoring, K1+K2),
AFCD-AU (borrow scan, %T-vs-mass columns), CoFID-UK (compilation; underlying
refs cited), USDA Iodine DB R4 (n/SD/min/max).

**Literature & book evidence (NRC 2006, Spitze 2003, Donadelli 2019, Seong
2014/2015, Biel 2019)** enters through the spec's `literature` block:
curated per-food values with citation, unit, and stats, flowing through the
same comparison engine and appearing in the report like any other source.
Curation is manual by design — these are page/table lookups with
food-matching judgment (NRC's fatty-sample caveat, Spitze's mg/kg-wet ÷10),
not mechanical parses. *(Gap G-1: the first implementation pass omitted this
channel entirely — caught in the 2026-08-18 plan review; see §8.)*

Not covered (deliberate): uFiSh (add with the first fish ingredient —
tracked, §8), CVB (rendered feeds only), NEVO/CNF (not local / circular).

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Dataset file silently changes → adapters mis-read | SHAs in `data/README.md`; golden-pin tests fail on drift |
| Adapter parsing regression | Golden tests pin hand-verified values on sweep-validated foods |
| Rule engine miscalibration steers the operator wrong | Verdicts advisory; report shows all raw values + quality marks; review is per-row |
| Operator error in decisions file | Schema gates (completeness, sources, brackets, PUFA); dry-run before commit |
| Partial DB write | pg_dump backup first; single insert batch; orphan cleanup; completeness check post-insert |
| Borrow-detection misses a lineage (false independence) | Multi-signal: origin decode AND echo screen AND report notes; review reads the notes |
| Fixed thresholds (±20%, eps floors) misfit some nutrient | Constants in one place; report always shows raw values so review can overrule |

## 7. Testing & rollout

- Unit contract tests (conversions fail-loud), golden adapter pins, rule
  engine on synthetic evidence, write gates — no-DB where possible.
- Rollout: build on `feature/intake-pipeline` → maiden run (boneless-skinless
  chicken thigh, FND 2646171 + SR 173627) → **plan review (this doc) →
  implementation audit → fix findings** → operator review of the maiden
  report → gated write → merge only after operator verification.
- Success criteria: maiden add's rows match sweep quality (citations on every
  row, zero unit errors, stats stored where coherent); review takes minutes
  per contested row instead of hours per food; a re-run from the committed
  artifacts reproduces the rows byte-identically.

## 8. Gap register (from the 2026-08-18 plan review & audit)

| # | Gap | Status |
|---|---|---|
| G-1 | Literature/book evidence channel (NRC 2006, Spitze, Seong, Donadelli, Biel) missing from the first implementation — sources the sweep used routinely had no path into the comparison | **Fixed**: `literature` block in the spec; entries flow through compare/report/decisions like any adapter value |
| G-2 | Maiden spec carried no literature entries (taurine sat at `no_evidence` despite Spitze having chicken dark-meat data; NRC 13-1 not consulted) | **Fixed**: spec updated with curated Spitze + NRC entries |
| G-3 | uFiSh adapter deferred | Open — add with the first fish ingredient intake |
| G-4 | **Implementation audit (2026-08-18, 8-angle review of the branch)** — 10 findings confirmed and fixed, plus cleanup | **Fixed** — see below |

### G-4 audit outcome (all fixed on the branch, 640 tests pass)

Correctness (each with a regression test):
1. No operator-review gate — machine `proposed_decisions.json` was directly
   commit-able with machine-written "Validated" comments → `--commit` now
   refuses the proposed file, requires a top-level `reviewed_by` in the
   decisions file AND `--signed-off-by` (cv_assign contract).
2. `to_fediaf` silently skipped the IU factor for blank/None units (vit A
   3.33×, vit D 40× low) → missing units now raise.
3. Echo screener compared each nutrient against only the FIRST USDA table —
   verbatim SR copies could escape when Foundation differed → compares
   against both tables; marking is key-based, not object-identity.
4. BLS `Logische Null`/`Reskalierung`/`Spuren` origins fell to `unknown` and
   counted as independent evidence (a definitional zero "confirmed" fiber)
   → classified computed/trace; trace no longer counts as independent.
5. Analysed zeros were dropped from adopt/replace medians (iodine anchor
   biased 2.25×; unanimous zeros produced a self-contradictory review) →
   zeros stay in the evidence pool; replace fires only on a nonzero median.
6. Trace values manufactured false `review` verdicts and suppressed the
   censored-bounds branch → trace/censored are detection-limit info lines.
7. Median-tie anchors were decided by float rounding (taurine 33.7-vs-169)
   → deterministic tie-break (n, then quality, then lower value) with an
   explicit "review must arbitrate" reason.
8. `_backup` hardcoded DB coordinates while the insert used config → backup
   now uses `config.DATABASE_*`, the pinned postgresql@18 pg_dump with PATH
   fallback, repo-anchored backups dir.
9. String-typed fdc ids / typo'd source keys silently produced empty
   extractions → spec coerces ids; extraction fails loud on empty results.
10. Food block validated only mid-commit after the backup; price/cooking
    optional → full validation at gate time (VALID_* + kwarg check, nonzero
    price, cooking_method declared, protein_species for meat categories).

Also fixed from the cleanup angles: positional column maps now verified
against dataset headers at load (CIQUAL/AFCD/CoFID tripwire); vitamin-K
totals matched by a structured `form` field instead of note-text sniffing;
USDA-lineage sources (Iodine DB) declared and excluded from independence;
engine thresholds stamped into report + decisions artifacts; stats-carrying
sources restricted (cv-v8 double-count guard); censored min=0 stats rejected
at the write gate; completeness check uses len(FEDIAF_IDS); orphan cleanup
no longer masks the original failure; USDA crosswalks consolidated into one
table; FCDB loader split (46 MB / 11 s → filtered per-food cache) and BLS
row cache added; assorted dead code removed.

Accepted (documented, not changed): intake keeps its own bulk-CSV readers
rather than reusing cv_sources (deliberately self-contained; divergence risk
noted in code comments); FCDB "Vitamin D" (value match) vs cv_intl
"Vitamin D3" (dispersion match) is a documented split, not a drift.
