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

### G-5 Second audit (2026-08-18, fresh 8-angle pass over the fixed branch)

10 further findings confirmed and fixed (668 tests pass), several in the
round-1 fixes themselves:
1. Decisions/spec slug never cross-checked — another food's decisions file
   could write under this spec's ingredient → hard gate.
2. CIQUAL K2 "traces" fabricated menaquinone totals (47 foods) → traces
   never make a total; K1-only rows carry form=k1_only.
3. Reviewed `unit` edits (entry-level key) were silently discarded →
   load_decisions folds them in; the unit gate now actually fires.
4. Header tripwire holes (family-token collisions, substring matches, CoFID
   twin columns, IndexError on shrunk headers; iodine_db unguarded) →
   every-word exact matching, guarded indexing, iodine tripwire added.
5. Trace demotion hid detection-limit context from the rendered report →
   bounds lines now emitted in all verdict branches and such rows join the
   needs-attention section.
6. MK-4-only foods (74 in Foundation) got formless K rows mislabeled
   "K1 only" → form=mk4_only with an honest note.
7. BLS 'Labelangabe' (package declarations, 201 rows) counted independent →
   classified borrowed. USDA AS/AR (summed/regression) no longer classify
   as analysed (aligns with the CV pipeline's derivation rules).
8. Tie flag fired on identical values, diluting the arbitrate signal → flags
   only genuine value splits; single shared phrasing.
9. Review-gate depth: producer/gate share one basename constant; the machine
   `review_contract` marker must be DELETED by review (renaming is not a
   review); contested rows (review/no_evidence verdicts + split tie-breaks)
   each require an operator `resolution` sentence before commit; a committed
   write drops a git-committable write_receipt.json (reviewer, signer,
   backup) — the durable approval trace.
10. Gate placement: food-block/price/resolution issues are COMMIT BLOCKERS
    (dry-run previews and lists them); record-level defects still fail both.
    add_ingredient's field rules extracted to shared
    database.ingredient_field_problems so the gate cannot drift; supplements
    explicitly out of intake scope; non-numeric hand-edits are gate problems,
    not tracebacks; median_value fully gated.

Also from measurement: round-1 loader fixes verified (cold run 15 s → 5.5 s;
FCDB search 11 s → 0.16 s). Accepted: FCDB's remaining 2.5 s openpyxl parse
(a derived pickle cache was judged not worth the staleness surface);
CoFID's per-sheet loads (+0.15 s on report, big win on search); BLS
single-key scan shape. Test-quality gaps closed: crosswalk/precedence/MK-4
pins on real foods, echo→judge integration test, extract fail-loud tests,
replace-median negative case, review-gate ordering tests.

### G-6 Third audit (2026-08-18, escalated methodology at the operator's
request: 3 reading angles + adversarial fuzzing + full-corpus sweep + live
test-DB write + mutation testing + docs consistency)

Execution angles (the new methodology) carried the round:
- **Fuzzing** (executed attacks): slug gate failed OPEN on an absent key →
  fail-closed; NaN/Infinity and negative values passed all gates → finite,
  non-negative required; portion/gram masses unguarded → positive required;
  duplicate nutrient_id entries silently last-won → refused at load; verdict
  self-attestation → contested status now restored from the sibling machine
  artifact. Held: bool rejection, homoglyph units, review-contract refusals,
  parameterized SQL.
- **Full-corpus sweep** (~19,000 foods, ~697k values; 5/8 adapters fully
  clean): BLS TR/<LOD/<LOQ tokens crashed 408 foods → parsed; FCDB min/max
  corrupt in 26% of foods → coherent-and-nonzero-width guard at the adapter;
  CoFID "carbohydrate" is monosaccharide equivalents → unmapped from 1005;
  USDA sub-sample ids resolved as plausible 1-row foods → data_type filter;
  negative carb-by-difference artifacts → clamped with note.
- **Live end-to-end write** (cat_food_formulator_test): the full commit path
  executed correctly (backup coordinates, 52 rows, µg→IU stored conversion,
  duplicate-name gate before backup, orphan cleanup without masking).
  Fixes: GateFailure refusals print as messages (exit 2) not tracebacks;
  successful orphan cleanup announces itself.
- **Mutation testing**: 12/12 deliberate guard-breaks killed by named
  regression tests; zero survivors — the test suite empirically guards
  every probed invariant.
- Reading angles (run inline after sustained API overloads): degenerate
  zero-width ranges could earn falsely tight CVs → strict min<max at the
  FCDB adapter, _stats_from and the write gate; docs/docstrings updated to
  the current gate reality.

**Audit-process incident (2026-08-18):** the fuzzing agent's harness had a
monkeypatch gap — one commit-path probe ran with the backup stubbed but the
real database live, writing a 52-row test ingredient into PRODUCTION while
the agent's report claimed no DB was touched. Caught by this round's
DB-linked-id verification, removed (delete_food 10047; counts verified back
to 43/pre-state). Standing mitigations: tests/conftest.py now carries a
production-mutation tripwire (fails any pytest session that changes
production row counts), and verification harnesses must target
cat_food_formulator_test via DATABASE_NAME and prove cleanliness with
before/after counts — assertions are not evidence.
