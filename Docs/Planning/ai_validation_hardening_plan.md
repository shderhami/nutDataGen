# AI Validation Hardening — Implementation Plan

**Status:** Revision 4 — **Phases 1–5 implemented**, each audited on landing. Suite: 487 passing.
**Date:** 2026-08-06

> **Audit outcome:** 13 factual claims verified correct (including all API claims). Nine findings raised; all nine confirmed by re-checking the source. Two were live defects in the already-landed §3 guard and have been **fixed** (see §3). The remaining seven are prescription corrections, applied below and marked **[audit]**.
>
> **Re-audit of the fixes:** the orphan-cleanup fix itself introduced two `food_id` lifecycle defects (one of them a post-save data-loss window worse than the original bug). Both are fixed with regression tests — see §3, **[audit, round 2]**.
>
> **Implementation:** see §8 for what landed per phase, the defects each phase's audit caught, and the decisions still owed.
>
> **Line references in this document are stale by ~45 lines** — it was written against the pre-guard `ai_validation.py`. Re-derive every reference before implementing.

**Scope:** `ai_validation.py`, its call sites in `main.py` and `backfill_nutrients.py`, and the prompt/response contract.

---

## 1. Why

During the lamb shoulder (FDC 174326) ingredient add, AI validation rated **EPA and DHA as HIGH confidence "accept SR Legacy"** when both SR Legacy values were placeholder zeros USDA had never measured. The model could not have known better: the prompt shows the value and a sample date, and nothing else.

That single failure exposed a class of problems rather than a bug. The validator:

- cannot see the provenance metadata the pipeline already fetches,
- cannot actually search, despite prompts instructing it to,
- reports a confidence that is uncalibrated in both directions,
- has no schema slot for "this nutrient is genuinely zero",
- and silently continues when the API fails wholesale.

This plan sequences the fixes by impact and simplicity. It is deliberately staged so each phase is independently reviewable and independently revertable.

---

## 2. Evidence base — read this before trusting any number below

| Claim | Status |
|---|---|
| AI rated never-measured EPA/DHA as HIGH "accept SR Legacy" | **Verified** — observed directly in the FDC 174326 run |
| `build_prompt_*` read only `year_acquired`; other metadata discarded | **Verified** — read in source |
| No `tools=` parameter on either API call site | **Verified** — read in source (`ai_validation.py:256`, `:881`) |
| `format_ai_suggestion` hid a `0.0` recommended value | **Verified and fixed** — reproduced, fixed, regression tests added |
| 5/5 genuinely-zero nutrients returned exactly `0.0` at high confidence | **Verified** — live experiment, 6 API calls |
| Vitamin D rated LOW confidence despite 40 data points + Analytical derivation | **Verified** — from the run output |
| 16 unpatched tests were making billed API calls | **Verified and fixed** — see §3 |
| `DERIVATION_CODES` has 7 wrong meanings, 19 invented codes, 54 missing | **Verified** — diffed against USDA's own `food_nutrient_derivation.csv` |
| Structured outputs supported on current `claude-opus-4-6` | **Verified** — Models API query |
| "86.5% of bare zeros confirmed ~0 by Foundation", "183 vetted pairs", "12.8× was an artifact" | **UNVERIFIED** — attributed to an adversarial audit agent that has **no completion record**. Scratchpad artifacts (`matches.json`, `gt_detail.json`) exist but the analysis was never re-derived. **Re-run before relying on this to justify any decision.** |
| `backfill_nutrients.py` / `resolve_cv` / 19-existing-rows risks | **UNVERIFIED** — same caveat. The files exist and the code paths are real; the specific risk claims were not independently reproduced. |

> **Auditor: the two unverified rows above were used to justify reverting the unpopulated-zero rule to advisory-only.** That decision may still be correct, but its stated evidence has not been reproduced. Treat re-deriving it as a prerequisite, not an optional extra.

---

## 3. Already done (context, not proposed work)

- **Billed-call guard** — `AI_MOCK_MODE` defaulted to false and `config.load_dotenv()` put a real key in the environment, so 16 unpatched tests billed on every suite run (~270s of the 274s runtime). Now: `tests/conftest.py` forces mock mode and replaces the `anthropic` client classes with raisers; `ai_validation.assert_live_ai_calls_allowed()` guards both call sites; `main.py` asks the operator before enabling billed calls. Suite: 274s → 3.9s.

- **[audit] Two defects in that guard, found by the audit and now fixed:**
  1. **The guard was swallowed by the sync retry loop.** `LiveAPICallBlocked` subclasses `RuntimeError`, which `call_claude_api_with_retry` catches; its message contains neither "invalid" nor "api key", so a refusal was retried 5× with ~60s of backoff and then reported as a generic `AIValidationError` — disguising a policy decision as an API failure. Fixed by re-raising it ahead of the generic handler in **both** the sync and async retry wrappers, with regression tests asserting exactly one attempt.
  2. **Declining billed calls crashed and orphaned an ingredient row.** The decline branch printed "AI validation will fail for each nutrient" and continued, but the validator raises at client creation; `main()` caught only `KeyboardInterrupt`, so the program died with a traceback leaving the row created before validation behind. Fixed twice over: the decline branch now exits cleanly *before* any row is created, and `main()` catches broad exceptions, cleans up via a new `_cleanup_incomplete_ingredient()` helper, and re-raises. That helper also closes the wider class of orphan bugs (any mid-run failure, not just this one).

- **[audit, round 2] The broad handler itself introduced two `food_id` lifecycle defects — found on re-audit of the fix above, now fixed:**
  1. **Post-save deletion window.** After `add_food_nutrients` succeeded, `food_id` stayed set until the next loop iteration reset it, so any exception in that window — an unexpected raise inside `assign_cv_for_food`, or an `EOFError` from the continue-prompt (realistic under the FIFO-driven interactive workflow) — handed a **fully-saved** ingredient to `delete_food`, which removes the row *and its just-saved nutrients* (a fresh food has no formulator references, so the FK guard would not refuse). The old code had this hole only for Ctrl-C; broadening to `except Exception` widened it to every failure type. Fixed: the ID moves to a local `saved_food_id` immediately after the save and `food_id` resets to `None`, so cleanup can never see a committed row.
  2. **`UnboundLocalError` on early failure.** `food_id` was first bound inside the while loop, so a failure ahead of the first iteration (e.g. `initialize_database`) made the handler itself raise `UnboundLocalError` while handling the real error, cluttering the traceback. Fixed: `food_id` is bound to `None` before the `try`.

  Both are pinned by `tests/test_main_cleanup.py`, which drives `main()` through a stubbed successful save and asserts (a) a post-save crash re-raises without ever calling `delete_food`, and (b) an early failure surfaces its own error, not `UnboundLocalError`. Both tests were verified to fail against the unfixed code.

  Suite now 357 passing.
- **Zero-value display fix** — `format_ai_suggestion` tested `recommended_value` for truthiness, so a correct AI answer of `0.0` rendered identically to "no value". Fixed with regression tests.

---

## 4. Phases

Each item states the problem, the change, files touched, and how to tell it worked.

### Phase 1 — Mechanical fixes (no design decisions, independently landable)

**1.1 Mass-failure gate**
*Problem:* When credits ran out, all 52 nutrients returned `recommendation="error"` with the billing message as `ai_justification`, and the pipeline walked into the review loop. Accepting would have written that text into 48 database rows.
*Change:* After each `validate_nutrients_concurrent` call, count results with `recommendation == "error"`. Above a threshold, emit `display_error` and return `[]` — `main.py` already treats an empty record list as "abort and clean up".

**[audit] Two corrections:**
1. **The gate is blind to the raise path.** Counting `error` *results* only catches failures that return. A validator that raises (the permission refusal did exactly this) never produces results at all. The raise path is now handled separately — `main()` catches broad exceptions and cleans up (fixed, see §3) — but 1.1 must not be described as covering it.
2. **The denominator is ambiguous.** Auto-skipped matches always "succeed", so a food with 40 matches and 12 billed calls that all fail sits at 23% — under a naive 25% gate. **Count errors among non-skipped results only.**

*Files:* `main.py` (4 call sites), `ai_validation.py` (helper).
*Acceptance:* Simulated all-error result aborts the food and deletes the ingredient row. Separate case: a food with many matches and a fully-failed billed set still trips the gate.

**1.2 Threshold coupling assertion**
*Problem:* `SKIP_VALIDATION_THRESHOLD = 5.0` (`config.py:36`) and `DISCREPANCY_THRESHOLDS["trivial"] = 5` (`config.py:22`) must stay equal. If they diverge, every match in the gap falls through to `validate_nutrient_single` and raises `Unknown prompt type: match`. Two constants declared independently with nothing tying them.
*Change:* **[audit] Prefer deriving over asserting** — `SKIP_VALIDATION_THRESHOLD = DISCREPANCY_THRESHOLDS["trivial"]` removes the failure mode instead of detecting it. Keep an assertion only if the two must stay independently tunable.
*Acceptance:* The two cannot silently diverge.
**[audit]** The stated symptom is right only for the sync path; in the concurrent path a mismatch produces `error` results rather than a raise.

**1.3 Numeric coercion of `recommended_value`**
*Problem:* `parse_single_response` takes `parsed.get("recommended_value")` verbatim. `"50 mg"` is stored as a `str` in a field annotated `Optional[float]` and flows into `build_nutrient_record`. A g/mg confusion becomes a silent 1000× error.
*Change:* Coerce to float at parse time; on failure set `None` and downgrade confidence. Reject strings like `"trace"`.
*Acceptance:* Unit tests for numeric, numeric-string, `"trace"`, `None`.
**[audit] 2.3 supersedes most of this.** Once the schema types `recommended_value` as `number | null`, `"50 mg"` cannot occur on live calls; 1.3 then survives only for mock mode and defence-in-depth. Land 1.3 first if convenient, but do not test the same contract twice.

**1.4 `format_ai_suggestion` branch coverage**
*Problem:* Branches on `"confirmed"` and `"estimate"`, which no prompt emits; nothing for `"insufficient_data"` (which `build_prompt_missing` explicitly allows) or `"error"`. Both fall through to "AI: No recommendation", so a hard parse failure displays identically to the model having no opinion.
*Change:* Add explicit branches; make `error` visually distinct.
*Acceptance:* Each recommendation value renders distinguishably.

**1.5 Result keying / return annotation**
*Problem:* Both validators are annotated `dict[int, AIValidationResult]` but key by `nutrient_name` when `nutrient_id` is None.

**[audit] The original justification was wrong.** The claim that a string-keyed result is unreachable is false — the missing-nutrients path explicitly falls back to name-keyed lookup (`main.py:806-810`, commented "Try nutrient_id first, then fall back to nutrient_name as key"). All 52 FEDIAF nutrients currently have IDs, so **both the string-keying and the fallback are dead code**. The annotation is still a lie, but the failure mode is "two dead branches that could drift", not "silent data loss".

*Change:* Drop no-ID results with a loud log **and delete the `main.py:809` fallback in the same change** — otherwise the two sides contradict each other.
*Acceptance:* Test asserting no silent-drop path; no remaining name-keyed lookup.

**1.6 `DERIVATION_CODES` correction**
*Problem:* 64 real USDA codes; our table has 29 — 1 correct, 7 with wrong meanings (`NC` = "Calculated", ours says "Not Calculated"; `AR` = linear regression, ours says "Analytical, Assumed Zero"), 19 invented, 54 missing.
*Change:* Regenerate from `data/USDA data/.../food_nutrient_derivation.csv`.
*Note:* Harmless today (the API always supplies a description, so the lookup is a dead fallback) but **a prerequisite for 2.1** — otherwise we feed the model inverted meanings.
*Acceptance:* Table matches USDA's CSV exactly; existing `derivation_description` DB values unaffected.

**1.7 Module import identity**
*Problem:* The project root has an `__init__.py` and `tests/` has one too, so modules load under two identities in one pytest session (`ai_validation` and `nutDataGen.ai_validation`). Exception classes and `isinstance` checks then compare unequal. This already bit the guard tests, and `test_ai_validation.py:655` carries an "avoid isinstance issues" comment from a previous encounter.
*Change:* Decide on one import strategy (proposed: keep the root package, make tests import `nutDataGen.x` consistently, or drop the root `__init__.py`).
**[audit] Fix this before Phase 4**, not "eventually": 4.3 introduces typed exception handling, which means more `isinstance` / `pytest.raises` tests — exactly where dual identity bites.
*Acceptance:* `isinstance` and `pytest.raises` behave consistently regardless of test order.

### Phase 2 — Fix what the model can see (highest impact per line)

**2.1 Pass the USDA metadata already fetched**
*Problem:* `comparison.extract_nutrient_metadata` pulls `num_samples`, `min_value`, `max_value`, `median_value`, `derivation_description`; both validators thread them through as `sr_metadata` / `foundation_metadata`; all four prompt builders read only `year_acquired`. The single most diagnostic signal — a sample count of zero — is invisible to the model. This is the direct cause of the EPA/DHA failure.
*Change:* Interpolate the five fields into `build_prompt_sr_only`, `build_prompt_both_sources`, `build_prompt_foundation_only`.

**[audit] The narrowing is in `main.py`, not `ai_validation.py`.** `validate_nutrients_concurrent` forwards `sr_metadata` / `foundation_metadata` as whole dicts — nothing is dropped there, and the four-key copy applies only to *missing* nutrients, which correctly have no USDA data. The real gap is the pseudo-comparisons built in the single-source scenarios: `main.py:523-527` (SR-only) and `main.py:675-679` (Foundation-only) construct metadata with only three of six fields, dropping `min_value`, `max_value`, `median_value`.

This matters because the SR-only path is the exact shape of the lamb-shoulder failure. `num_samples` *does* survive, so the headline zero-samples signal would work without this — but min/max/median would not, and an acceptance test run on a two-source food would pass while the one-source path stayed broken.

*Files:* `ai_validation.py` (prompt builders) **and `main.py` (both pseudo-comparisons)**.
*Depends on:* 1.6.
*Acceptance:* Before/after on the FDC 174326 EPA/DHA cases — a **single-source** food, so the SR-only path is exercised. Success = the model stops rating a zero-data-point value HIGH confidence. Assert all six metadata fields reach the prompt.

**[audit] The former "asymmetry to preserve" note was dropped as vacuous.** `build_prompt_missing` serves only nutrients absent from *both* sources, so there is no USDA value that could be added to it. The concern only existed under the reverted unpopulated-zero routing, which §7 puts out of scope. If anything is worth stating, it is: *do not route unpopulated zeros into the missing prompt.*

**2.2 Identify the food properly**
*Problem:* The prompt identifies the food only by `food_name` — whatever was typed at the console, lowercased. FDC ID, cooking method, and protein species are all collected and never passed, so the model may anchor on a different cut or cooked-vs-raw state than the row being validated.
*Change:* Thread `food_info` fields into the prompt builders.
*Acceptance:* Prompt contains cut/state/species; spot-check that suggestions shift appropriately for raw vs cooked.

**2.3 Structured outputs**
*Problem:* `_extract_json_from_response` (`:483-491`) falls back to slicing first-`{` to last-`}`, which mis-parses on prose braces or two objects.
*Change:* Use `output_config.format` with a JSON schema. Confirmed supported on the current model, so **no model upgrade required**. Enumerate legal `recommendation` values in the schema — this is also where `confirmed_zero` (2.4) belongs. Delete the fallback ladder.
*Acceptance:* The brace-slicing heuristic is deleted.

**[audit] "Schema violations impossible" was overstated.** Structured outputs guarantee schema-valid JSON only on a clean stop — `stop_reason: "max_tokens"` can truncate mid-object, and a refusal need not match the schema. Mock mode also bypasses the API entirely (`_get_mock_response` returns hand-built strings), so a parse path must survive regardless. **Keep parse-failure handling; delete only the heuristic.** Note also that structured-output schemas do not support numeric range constraints (`minimum`/`maximum`), so plausibility bounds on `recommended_value` still belong in code.

**2.4 Give zero an explicit home**
*Problem:* Options are `literature` or `insufficient_data`, and the latter maps to `null` = *unknown*, not *zero*. The model reached `0.0` on its own, but nothing invites it.
*Change:* Add `confirmed_zero`; instruct explicitly that a genuinely absent nutrient should return `0`, and reserve `insufficient_data` for genuinely undeterminable.
*Depends on:* 2.3.
**[audit] This crosses a repo boundary.** `ai_recommendation` lives in a database shared with the **recipeFormulator** repo. Before emitting a new enum value, check what that repo — and any query filtering on `ai_recommendation` — expects. Add this check to the change list.
*Acceptance:* Zero-answer cases return `confirmed_zero`, not a coerced `literature: 0`; sibling-repo consumers verified.

### Phase 3 — Make the evidence real

**3.1 Web search tool**
*Problem:* Prompts say "Search ONLY scientific literature"; no `tools` parameter is passed. All citations come from parametric memory. Coordinates drift (audit caught "Enser 1996 Meat Science 44(4):443-458" vs the real 42(4):443-456).
*Change:* Add `web_search_20260209` (supported on the current model; dynamic filtering built in — do **not** separately declare `code_execution`). Handle `stop_reason: "pause_turn"`.

**[audit] This breaks response parsing, which the original plan omitted.** Both call sites read `message.content[0].text`. With web search enabled, `content` contains `server_tool_use` / `web_search_tool_result` blocks *before* any text, so indexing `[0]` fails or returns the wrong block. **Iterate `content` for text blocks first** — this is also a prerequisite for `pause_turn` handling, which replays `response.content`.
*Cost/latency:* Increases both. Measure before rolling out to all 52 nutrients.
*Acceptance:* Citations resolve to real, checkable sources.

**3.2 Local bulk-CSV peer median in the prompt**
*Problem:* `data/USDA data/` has both bulk datasets with `data_points`, `derivation_id`, `min`, `max`, `median`. The validator never touches them. This is the one evidence source fully under our control and impossible to fabricate — and it is exactly the manual cross-check currently done by hand after the fact.
*Change:* Precompute a peer median across comparable foods (same species/cut class/state, `data_points > 0`) and include it in the prompt.
*Caveats:* Peer cohorts carry provenance bias (lamb peers skew NZ-imported); split and compare before trusting a median. Measured biological CV in a tight lamb cohort is 8–26%, so this bounds achievable precision.
*Acceptance:* Prompt contains a peer figure; model reasons over supplied evidence rather than recalling numbers.

### Phase 4 — Calibration and robustness

**4.1 Self-consistency sampling** — 3 samples, take the median, treat material disagreement as the escalation signal. Replaces uncalibrated self-reported confidence with a measured one. Triples cost per nutrient.
**[audit]** This depends on output variance. Today `temperature=0.3` supplies some; after the model upgrade that parameter must be **deleted** (it 400s), so diversity comes only from default sampling. Validate that spread is still usable before relying on it.

**4.2 Fix confidence semantics** — `create_skipped_result` (`:654-663`) stamps `confidence="high"` on nutrients never sent to the AI, so `ai_confidence='high'` means *either* "model was confident" *or* "we never asked". Any query filtering on it sweeps in unvalidated rows. Add a distinct `skipped` value or a separate `validated` boolean. **Requires a decision on existing DB rows.**

**4.3 Retry/exception handling** — `call_claude_api` wraps everything in `RuntimeError(f"Claude API error: {e}")`, destroying the typed exception; the retry wrapper then substring-matches the message (`:435`); the async version catches bare `Exception` (`:920`). Combined with the SDK's own 2 retries, one rate-limited nutrient can issue ~15 requests and burn 60s of backoff. Catch `anthropic.RateLimitError` / `BadRequestError` directly; set `max_retries` on the client.

**4.4 Auto-accept disagreement trail** — Matches (`main.py:312`) and Foundation-only nutrients (`:445-479`) never prompt. For Foundation-only the suggestion prints and the Foundation value is written anyway, with `ai_recommendation="literature"` stored beside it. The database records a contradiction with no review trail. **Requires a decision on what to record.**

**4.5 Prompt provenance** — Store a prompt version hash alongside `ai_model`, mirroring the AST-normalized hashing already used for the CV pipeline, so a stored justification can be traced to the prompt that produced it.

### Phase 5 — Measurement (the item that tells you whether any of this worked)

**5.1 Calibration harness**
Build a labeled set from foods present in both SR Legacy and Foundation, treating Foundation as ground truth. Run validation over it and measure precision/recall per confidence level. This converts "the confidence label is uncalibrated" from an assertion into a number, and gives a threshold for auto-accept vs escalate.
*Note:* Scratchpad artifacts from the earlier audit may be reusable, but per §2 the matching methodology is unverified — expect to rebuild it.
*This phase also re-derives the §2 unverified claims.*

### Deferred — Model upgrade

`AI_MODEL = "claude-opus-4-6"` is a generation behind. Moving to `claude-opus-5` is **not a prerequisite for anything above** (structured outputs and web search both work on 4.6), but it must be done as a unit:

- `temperature=0.3` (`:259`, `:884`) returns **400** on Opus 4.7 and later — must be deleted, not adjusted.
- Thinking is **on by default** on Opus 5 (unlike 4.7/4.8 where omitting the parameter meant no thinking).
- `max_tokens=4096` caps **thinking plus response text together** — needs headroom or responses truncate mid-answer.
- Re-baseline cost: the newer tokenizer produces more tokens for the same text.
- **[audit]** `max_tokens=4096` will not merely be tight — with thinking on by default it will *routinely truncate*. Plan for ~16K non-streaming.
- **[audit]** "A generation behind" undersells it: 4.6 is three releases behind the current Opus.

Doing this before Phases 1–2 would conflate "did the prompt change help?" with "did the model change help?".

---

## 5. Sequencing rationale

1. **Phase 1** is mechanical and unblocks 2.1 (via 1.6). Land it first; it is independently safe.
2. **Phase 2** is the direct fix for the observed failure and the highest impact per line.
3. **Phase 3** is where cost and latency change materially — measure Phase 2's delta first.
4. **Phase 4** is quality and infrastructure; 4.2 and 4.4 need product decisions.
5. **Phase 5** is the only phase that produces evidence about whether the rest worked. Consider pulling 5.1 earlier if the auditor wants measured rather than argued justification.

---

## 6. Open questions for the auditor

1. **Should Phase 5 come first?** Everything else is argued from a single observed failure plus one 6-call experiment. A calibration harness would let the rest be measured instead.
2. **§2 unverified claims** — is re-deriving them a blocker for this plan, given they justified the earlier revert?
3. **4.2 / 4.4 touch stored data.** What should happen to existing rows with ambiguous `ai_confidence` and the recorded AI/DB contradictions?
4. **Cost ceiling.** Phase 3.1 (search) and 4.1 (3× sampling) together could multiply per-ingredient cost several-fold. What is the acceptable per-ingredient budget?
5. **Is the `missing`-path asymmetry in 2.1 right?** It rests on one experiment showing the model does well unanchored. Worth a second look.
6. **1.7 (import identity)** — worth fixing now, or accept it and work around it in tests?

---

## 8. Implementation record (Revision 4)

All five phases landed, each audited before moving on. Suite 381 → 487 tests.

| Phase | Landed | Audit caught |
|---|---|---|
| 1 | Mass-failure gate (`detect_mass_failure`, 4 call sites), `SKIP_VALIDATION_THRESHOLD` derived from `DISCREPANCY_THRESHOLDS`, numeric coercion, `error`/`insufficient_data` branches, ID-only result keying (+ `main.py` fallback deleted), `DERIVATION_CODES` regenerated (29 → 64 real codes), root `__init__.py` removed | `float("nan")`/`inf` passed coercion — now rejected. Two stale tests asserted the *inverted* `NC`/`C` meanings; corrected. |
| 2 | Six-field provenance in all three value-bearing prompts + `PROVENANCE MATTERS` rule, food identity (species/method/FDC IDs), structured outputs with per-prompt-type enums, `confirmed_zero`, brace-slicing heuristic deleted | The narrowing was in `main.py` as the audit predicted; `_api_nutrient_metadata` now feeds all five sites. `anthropic>=0.40.0` was too loose for `output_config` — pinned to `>=0.79.0`. Cross-repo check done: `ai_recommendation` is `VARCHAR(50)`, no CHECK constraint, formulator never filters on its value → additive. |
| 3 | Web search (off by default, `web_search_20260209`, content-block iteration, capped `pause_turn` resumes), `peer_median.py` reusing the pinned `cv_config` datasets | Naive per-nutrient scanning cost ~35 s/ingredient — reworked to one scan per cohort (0.7 s for all 52). Datasets are gitignored, so every entry point degrades to `None`. |
| 4 | Self-consistency sampling (N=1 default), `confidence="skipped"`, typed `NonRetryableAPIError` + SDK `max_retries=0`, auto-accept disagreement trail at all three no-prompt sites, prompt-version hash in `ai_model` | A partial abstention (one sample returns no value) counted as agreement — now forces low confidence. **`importlib.reload(ai_validation)` in an old test rebound every class**, so `isinstance` failed by test order — the 1.7 failure mode from a second cause; removed and pinned by a regression test. |
| 5 | `calibration_harness.py` — SR↔Foundation labeled set, accuracy per confidence level, `confidence_is_calibrated` verdict; mock-runnable, live-gated | **The pairing key collapsed distinct foods** (every "Fish, salmon, …" onto one Foundation food), manufacturing 500% "disagreements" — precisely the unverified-matching failure §2 warns about. Exact normalized matching now yields 793 real cases across 89 foods. |

**Defaults are deliberately conservative:** web search off, self-consistency N=1, mass-failure threshold 25% of non-skipped results. Phase 3 and 4.1 are the cost multipliers and stay opt-in until §6 Q4 is answered.

### Still owed (not code)

1. **§6 Q3 — existing DB rows: DECIDED 2026-08-06 — leave untouched.** No backfill; affected ingredients get corrected naturally if and when they are re-run. Consequence to keep in mind: `ai_confidence` and `ai_model` now carry **mixed semantics** across rows. A row is post-hardening iff `ai_model` contains `+p:`; only those rows use `'skipped'` to mean "never sent to the AI". Any query filtering on `ai_confidence='high'` must therefore either scope itself to `ai_model LIKE '%+p:%'` or accept that older `'high'` rows may be unvalidated.
2. **§6 Q4 — cost ceiling.** Unanswered, which is why 3.1 and 4.1 ship off.
3. **§2 unverified claims.** 5.1 provides the machinery to re-derive them; it has not been run live.
4. **Deferred model upgrade.** Untouched. `temperature=0.3` still present (valid on 4.6, 400s on 4.7+) and `max_tokens=4096` still needs raising before any upgrade.

---

## 9. Phase 6 — Reference datasets and cohort matching (proposed, 2026-08-06)

Both items come from the **lamb shoulder (10046) live run**, where every value was reviewed against NRC 2006 and UK CoFID by hand *after* the pipeline had finished. That manual cross-check found things the pipeline could not, so it belongs in the pipeline.

### 6.1 Add NRC 2006 and UK CoFID as reference datasets

*Problem:* `peer_median.py` consults only the USDA bulk CSVs. For the four nutrients USDA does not track — **chloride, iodine, biotin, taurine** — the prompt therefore carries no local evidence at all, and the reviewer is left with the model's unverifiable recollection. In the 10046 run those four were the only nutrients decided without a peer block.

*Evidence this matters (all from the 10046 review):*
- **Chloride** — absent from USDA, NRC (Table 13-6 cell empty) and FAO. UK CoFID 18-475 gives **74 mg/100 g** from a named analytical survey (LGC, 1990s), and its sodium (70) matches our accepted sodium exactly, making the value directly transferable.
- **Biotin** — NRC has **no** biotin value for lamb. CoFID gives **2.0 µg/100 g**. This is the nutrient where a fabricated NRC citation was written to the database (see 6.1a).
- **Iodine** — absent from USDA and NRC. CoFID gives 3–6 µg depending on cut.
- **Taurine** — absent from all three; **Spitze et al. 2003** (now at `Docs/Spitze_2003_...pdf`) gives lamb leg raw **473 mg/kg = 47.3 mg/100 g**, n=11.
- **Folate** — the cross-check *resolved* a contested decision: USDA 23 µg and NRC 18 µg cluster against CoFID 6 µg, confirming a US-vs-UK assay-method split rather than an error, and retrospectively justifying rejecting the AI's 3.0.
- **Niacin** — CoFID lists preformed niacin (5.4) *and* niacin equivalents (9.3) as separate columns, confirming the units-class error behind the AI's 6.0 suggestion.

*Change:* extend `peer_median.py` (or a sibling `reference_data.py`) to read NRC 2006 Tables 13-1/13-5/13-6/13-7 and the CoFID workbook, and attach their values to the prompt alongside the USDA peer median. Both are already on disk (`Docs/NRC2006.epub`, `data/McCance_Widdowsons_..._2021..xlsx`).

*Non-obvious requirements, learned the hard way:*
- **NRC table parsing is offset by one.** The header's first cell (`Feed Name Description`) spans **two** data cells, so `data[i+1]` aligns with `header[i]`. A naive `zip()` silently mis-labels every column — that is exactly how folate 0.18 mg/kg was read as biotin. Any parser must assert plausibility (e.g. niacin in meat cannot be 0.18 mg/kg) rather than trust positional alignment.
- **NRC samples are fatty.** Lamb Ground is 23.4% fat vs a lean cut's 6.76%. Values must be scaled — protein-scaling (CP 16.60 → 19.55) reproduced our amino acids to within 2% across all twelve, so it is a validated method.
- **CoFID entries differ by trim.** `18-475 "lean only, raw, average"` and `18-170 "shoulder, raw, lean and fat"` disagree ~2× on iodine. Pick by composition match, not by name similarity.
- **CoFID is a compilation**, not a study; the lamb minerals trace to a 1990s UK retail survey. Cite the underlying source and vintage, not just "CoFID 2021". Licence is OGL v3.0 — attribution required, commercial use permitted.

*Acceptance:* the four USDA-untracked nutrients carry a local reference value in the prompt; a re-run of 10046 reproduces chloride 74, biotin 2.0, taurine 47.3 without web search.

#### 6.1a Guard against fabricated citations

*Problem:* during the 10046 run a citation asserting `NRC 2006 Table 13-7: lamb ground biotin 0.18 mg/kg` was **written to the database**. NRC has no biotin value for lamb; 0.18 was folate, misread from a mis-aligned table. It was caught only by the manual cross-check, after the save.

*Change:* whatever ingests NRC/CoFID must expose the *source cell* it read, so a citation can be regenerated from data rather than composed prose. Consider recording a machine-checkable reference (dataset + table + row key) in the comment alongside the human sentence.

### 6.2 Make peer cohorts tissue- and cut-aware

*Problem:* `peer_median._matching_fdc_ids` filters on **species** and **raw/cooked state** only. It does not exclude organ meats, and it does not distinguish anatomical cut. For minerals that vary with bone proximity or fibre type, the pooled median is the wrong comparator — and it moved the answer in **both** directions during the 10046 review.

*Evidence:*
| Nutrient | Pooled cohort | Refined cohort | Effect on the decision |
|---|---|---|---|
| **Calcium** | 8.0 mg (all raw lamb, n=66, incl. mechanically-separated at 162) | Shoulder cuts 12–16 mg (US choice, 32 data points each) | Pooled median made SR's 15 look like a +88% outlier; cut-matched, it is the **median of its own group**. Kept SR. |
| **Selenium** | 7.0 µg (n=47, incl. kidney 126.9 / liver 82.4) | Muscle-only **5.45** (n=42), shoulder 5.3 (n=3) | Organs inflated the pooled figure; stripping them **strengthened** the case against SR's 22.2. Overrode to 5.5. |
| **Folate** | 23.0 µg (n=19, incl. liver 230) | Muscle-only 23.0 (n=13, range 21–24) | Robust either way — but the tight muscle cluster is what made rejecting the AI's 3.0 defensible. |

*Change:* add tissue-class exclusion (variety meats / by-products / mechanically separated) and an optional cut-class filter, with `MIN_COHORT_SIZE` fallback when a refined cohort is too thin. Return the cohort definition actually used so the prompt and the reviewer can see it.

*Caution:* refinement trades sample size for specificity — the shoulder-only selenium cohort was n=3, all single-data-point NZ imports. The existing thin-cohort warning must apply to refined cohorts too, and the fallback must be visible, not silent.

*Acceptance:* calcium for 10046 reports a shoulder-matched cohort; selenium reports a muscle-only cohort; both surface `sample_size` and the effective filter in the prompt.

### Why this is Phase 6 and not earlier

Phases 1–5 fix what the validator *does with* the evidence it has. Phase 6 changes *what evidence exists*. It is independent of the model-upgrade decision and of §6 Q4's cost ceiling, since both datasets are local files — no API cost, no latency.

---

## 7. Non-goals

- Changing the unpopulated-zero rule. It is advisory-only as of 2026-08-05 and out of scope here.
- Rewriting the CV pipeline.
- Migrating off the interactive `main.py` flow.
