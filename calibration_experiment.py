"""
Design-of-experiment layer over the calibration harness.

The harness measures one configuration. This runs several and compares them,
which needs a design rather than a loop:

  * The four configurations ("none", self-consistency, web search, both) are a
    2x2 FACTORIAL — search {off,on} x samples {1,N}. Run as a factorial you
    get both main effects AND their interaction from the same cases, so you
    learn whether the two fixes are redundant or complementary. Four separate
    one-factor experiments would cost more and tell you less.

  * Arms are PAIRED: every arm sees the identical case list. Paired binary
    outcomes are compared with McNemar's test, whose power depends on the
    number of cases where the arms DISAGREE rather than the total. That is
    typically a 3-5x efficiency gain, and it cancels the ground-truth noise
    (Foundation is a re-analysis, not truth) because the same noise is in
    every arm.

Two pre-checks come first, because either can cancel half the experiment for
about a dollar:

  1. CONFIDENCE SPREAD. If the model self-reports "high" on nearly everything,
     calibration is unmeasurable — there is no spread to correlate with
     accuracy — and "is confidence calibrated?" is answered "no, it is a
     constant" without any factorial design.

  2. SAMPLE DIVERGENCE. Self-consistency only measures anything if repeated
     samples actually differ. If three samples come back identical, that whole
     factor is inert and both arms containing it can be dropped.

Statistical caveats this tool reports rather than hides:
  * Cases are CLUSTERED within foods (~9 nutrients per food, 9 foods). Treating
    them as independent understates standard errors. With so few clusters,
    cluster-robust corrections are themselves unreliable, so the effective
    sample size is closer to the food count than the case count. Any p-value
    here is indicative, not confirmatory.
  * Absolute accuracy is NOT interpretable (Foundation != truth). Only
    between-arm and between-confidence-level comparisons are.

Usage:
    # Free: show the design, the case set, and the cost, run nothing
    python calibration_experiment.py --plan

    # ~$1: the two pre-checks
    AI_MOCK_MODE=false ALLOW_LIVE_AI_CALLS=1 \\
        python calibration_experiment.py --pilot --limit 20

    # Screening: max contrast, two arms
    AI_MOCK_MODE=false ALLOW_LIVE_AI_CALLS=1 \\
        python calibration_experiment.py --arms none,both

    # Full factorial
    AI_MOCK_MODE=false ALLOW_LIVE_AI_CALLS=1 \\
        python calibration_experiment.py --arms all
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

import ai_validation
import calibration_harness as ch
from ai_validation import AIValidationResult

# Opus 4.8 list price, $/token — identical to 4.6 ($5/$25 per MTok).
COST_IN_PER_TOKEN = 5.00 / 1_000_000
COST_OUT_PER_TOKEN = 25.00 / 1_000_000
# Measured with messages.count_tokens on real prompts, NOT estimated: the
# Opus 4.7+ tokenizer counts 1.425x what 4.6 counted for identical text, so a
# 4.6-era estimate understates the bill by ~40%. Same rate, more tokens.
TOKENS_IN_BASE = 1100
# Measured, not estimated: attaching web_search_20260209 adds ~5,535 input
# tokens of TOOL DEFINITION to every request, whether or not the model
# searches — a 6x increase on a ~1,100-token prompt. Retrieved page content
# is charged on top of that.
TOKENS_IN_TOOL_DEFINITION = 5535
TOKENS_IN_PER_SEARCH = 2100
SEARCHES_PER_CASE = 2
TOKENS_OUT = 115

SELF_CONSISTENCY_N = 3


@dataclass(frozen=True)
class Arm:
    """One cell of the 2x2 factorial."""
    name: str
    samples: int
    web_search: bool

    @property
    def label(self) -> str:
        bits = []
        bits.append(f"N={self.samples}")
        bits.append("search" if self.web_search else "no-search")
        return f"{self.name} ({', '.join(bits)})"

    def cost_per_case(self) -> float:
        tokens_in = TOKENS_IN_BASE
        if self.web_search:
            tokens_in += TOKENS_IN_TOOL_DEFINITION
            tokens_in += TOKENS_IN_PER_SEARCH * SEARCHES_PER_CASE
        return self.samples * (
            tokens_in * COST_IN_PER_TOKEN + TOKENS_OUT * COST_OUT_PER_TOKEN
        )


ARMS: dict[str, Arm] = {
    "none": Arm("none", samples=1, web_search=False),
    "selfcons": Arm("selfcons", samples=SELF_CONSISTENCY_N, web_search=False),
    "search": Arm("search", samples=1, web_search=True),
    "both": Arm("both", samples=SELF_CONSISTENCY_N, web_search=True),
}


@contextmanager
def _arm_config(arm: Arm) -> Iterator[None]:
    """
    Apply an arm's configuration for the duration of a run.

    The knobs are module-level in ai_validation (they are read per call, not
    captured at import), so setting and restoring them here keeps the
    experiment honest without threading config through the whole validator.
    """
    prev_samples = ai_validation.AI_SELF_CONSISTENCY_SAMPLES
    prev_search = ai_validation.AI_WEB_SEARCH_ENABLED
    ai_validation.AI_SELF_CONSISTENCY_SAMPLES = arm.samples
    ai_validation.AI_WEB_SEARCH_ENABLED = arm.web_search
    try:
        yield
    finally:
        ai_validation.AI_SELF_CONSISTENCY_SAMPLES = prev_samples
        ai_validation.AI_WEB_SEARCH_ENABLED = prev_search


# ── Pre-check 1: is confidence measurable at all? ────────────────────────────

def assess_confidence_spread(scored: list[ch.ScoredCase]) -> dict:
    """
    Can calibration even be measured on this evidence?

    If one confidence level covers nearly everything, there is no spread to
    correlate with accuracy and no threshold to place.
    """
    counts: dict[str, int] = {}
    for case in scored:
        counts[case.confidence] = counts.get(case.confidence, 0) + 1
    total = sum(counts.values())
    if not total:
        return {"measurable": False, "reason": "no scored cases", "counts": {}}

    dominant = max(counts.values()) / total
    levels_with_5 = [c for c, n in counts.items() if n >= 5]
    measurable = dominant < 0.90 and len(levels_with_5) >= 2
    return {
        "measurable": measurable,
        "counts": counts,
        "dominant_share": round(dominant, 3),
        "levels_with_n_ge_5": sorted(levels_with_5),
        "reason": (
            "usable spread across confidence levels" if measurable
            else f"one level covers {dominant:.0%} of cases; "
                 "confidence is effectively a constant"
        ),
    }


# ── Pre-check 2: does repeated sampling actually diverge? ────────────────────

def probe_sample_divergence(
    cases: list[ch.LabeledCase],
    samples: int = SELF_CONSISTENCY_N,
) -> dict:
    """
    Ask the same question N times and see whether the answers differ.

    Measured directly rather than inferred from reconcile_samples' notes, so
    the result is unambiguous. If nothing diverges, self-consistency measures
    nothing and both arms that use it can be dropped before they are paid for.
    """
    from ai_validation import (
        _build_prompt, _response_schema, call_claude_api_with_retry,
        parse_single_response,
    )

    probes = []
    for case in cases:
        nutrient_data = _case_to_nutrient_data(case)
        prompt = _build_prompt(case.description, nutrient_data, case.food_info)
        schema = _response_schema("sr_only")

        values, recommendations, confidences = [], [], []
        for _ in range(samples):
            raw = call_claude_api_with_retry(prompt, None, schema)
            parsed = parse_single_response(raw, nutrient_data)
            values.append(parsed.recommended_value)
            recommendations.append(parsed.recommendation)
            confidences.append(parsed.confidence)

        numeric = [v for v in values if v is not None]
        spread = None
        if len(numeric) > 1:
            median = statistics.median(numeric)
            spread = (
                (max(numeric) - min(numeric)) / abs(median) if median
                else (0.0 if max(numeric) == min(numeric) else float("inf"))
            )
        probes.append({
            "food": case.description,
            "nutrient_id": case.nutrient_id,
            "recommendations": recommendations,
            "values": values,
            "confidences": confidences,
            "recommendation_varied": len(set(recommendations)) > 1,
            "value_spread": None if spread is None else (
                round(spread, 4) if spread != float("inf") else "inf"
            ),
        })

    varied_rec = sum(1 for p in probes if p["recommendation_varied"])
    varied_val = sum(
        1 for p in probes
        if p["value_spread"] not in (None, 0.0)
    )
    n = len(probes)
    informative = n > 0 and (varied_rec + varied_val) > 0
    return {
        "informative": informative,
        "n_probed": n,
        "samples_per_case": samples,
        "cases_where_recommendation_varied": varied_rec,
        "cases_where_value_varied": varied_val,
        "reason": (
            "repeated samples diverge, so self-consistency measures something"
            if informative else
            "repeated samples were identical; self-consistency would add cost "
            "and no signal — drop the selfcons and both arms"
        ),
        "probes": probes,
    }


# ── Running an arm ───────────────────────────────────────────────────────────

def _case_to_nutrient_data(case: ch.LabeledCase) -> dict:
    """The validator's input for one case: SR value only, Foundation withheld."""
    return {
        "nutrient_id": case.nutrient_id,
        "nutrient_name": case.nutrient_name,
        "unit": case.nutrient_unit,
        "prompt_type": "sr_only",
        "sr_value": case.sr_value,
        "sr_metadata": case.sr_metadata,
    }


def run_arm(
    arm: Arm,
    cases: list[ch.LabeledCase],
    verbose: bool = False,
) -> list[ch.ScoredCase]:
    """Run every case through one arm and score it against Foundation."""
    scored: list[ch.ScoredCase] = []
    with _arm_config(arm):
        for description, food_cases in ch.group_by_food(cases):
            comparison = {
                "matches": [], "discrepancies": [], "foundation_only": [],
                "sr_only": [
                    {
                        "nutrient_id": c.nutrient_id,
                        "nutrient_name": c.nutrient_name,
                        "unit": c.nutrient_unit,
                        "sr_value": c.sr_value,
                        "sr_metadata": c.sr_metadata,
                    }
                    for c in food_cases
                ],
            }
            results = ai_validation.validate_nutrients_concurrent(
                food_name=description,
                comparison_result=comparison,
                sr_data={"nutrients": {}},
                foundation_data=None,
                missing_nutrients=[],
                verbose=verbose,
                food_info=food_cases[0].food_info,
            )
            scored.extend(ch.score_cases(food_cases, results))
    return scored


# ── Paired comparison ────────────────────────────────────────────────────────

def mcnemar(
    a: list[ch.ScoredCase], b: list[ch.ScoredCase]
) -> dict:
    """
    Paired comparison of two arms on the same cases.

    Uses the exact binomial test on discordant pairs — with the small case
    counts available here the normal approximation is not trustworthy.
    """
    key = lambda c: (c.description, c.nutrient_id)  # noqa: E731
    a_by, b_by = {key(c): c for c in a}, {key(c): c for c in b}
    shared = sorted(a_by.keys() & b_by.keys())

    a_only = sum(1 for k in shared if a_by[k].correct and not b_by[k].correct)
    b_only = sum(1 for k in shared if b_by[k].correct and not a_by[k].correct)
    discordant = a_only + b_only

    p_value = None
    if discordant:
        try:
            from scipy.stats import binomtest

            p_value = float(binomtest(b_only, discordant, 0.5).pvalue)
        except ImportError:
            p_value = None

    return {
        "n_paired": len(shared),
        "n_discordant": discordant,
        "first_arm_only_correct": a_only,
        "second_arm_only_correct": b_only,
        "accuracy_first": (
            round(sum(1 for k in shared if a_by[k].correct) / len(shared), 4)
            if shared else None
        ),
        "accuracy_second": (
            round(sum(1 for k in shared if b_by[k].correct) / len(shared), 4)
            if shared else None
        ),
        "p_value_exact": None if p_value is None else round(p_value, 4),
        "note": (
            "Underpowered: fewer than 25 discordant pairs. Read the direction, "
            "not the p-value." if discordant < 25 else
            "Cases are clustered within foods; treat p as indicative."
        ),
    }


def factorial_effects(by_arm: dict[str, list[ch.ScoredCase]]) -> dict:
    """
    Main effects and interaction from the 2x2, when all four arms have run.

    Effects are differences in accuracy: the search effect averaged over
    sampling levels, the sampling effect averaged over search levels, and
    the interaction (do they overlap, or do they fix different errors?).
    """
    needed = {"none", "selfcons", "search", "both"}
    if not needed <= by_arm.keys():
        return {"available": False, "reason": "needs all four arms"}

    def accuracy(name: str) -> Optional[float]:
        cases = by_arm[name]
        return sum(1 for c in cases if c.correct) / len(cases) if cases else None

    acc = {name: accuracy(name) for name in needed}
    if any(v is None for v in acc.values()):
        return {"available": False, "reason": "an arm produced no scored cases"}

    search_effect = 0.5 * ((acc["search"] - acc["none"]) + (acc["both"] - acc["selfcons"]))
    sampling_effect = 0.5 * ((acc["selfcons"] - acc["none"]) + (acc["both"] - acc["search"]))
    interaction = (acc["both"] - acc["search"]) - (acc["selfcons"] - acc["none"])

    return {
        "available": True,
        "accuracy_by_arm": {k: round(v, 4) for k, v in acc.items()},
        "search_main_effect": round(search_effect, 4),
        "sampling_main_effect": round(sampling_effect, 4),
        "interaction": round(interaction, 4),
        "interpretation": (
            "Positive interaction: the two fix different errors and stack. "
            "Negative: they overlap, so buying both is largely wasted."
        ),
    }


# ── Cost ─────────────────────────────────────────────────────────────────────

def estimate_cost(arms: list[Arm], n_cases: int) -> dict:
    # Total is summed over the LIST, not over the per-arm dict: keying by name
    # would silently collapse a repeated arm and understate the bill.
    total = sum(a.cost_per_case() * n_cases for a in arms)
    per_arm = {a.name: round(a.cost_per_case() * n_cases, 2) for a in arms}
    return {
        "n_cases": n_cases,
        "per_arm_usd": per_arm,
        "total_usd": round(total, 2),
        "note": "List-price estimate; excludes any per-search server fee.",
    }


# ── Orchestration ────────────────────────────────────────────────────────────

@dataclass
class Experiment:
    cases: list[ch.LabeledCase]
    by_arm: dict[str, list[ch.ScoredCase]] = field(default_factory=dict)

    @property
    def n_foods(self) -> int:
        return len({c.description for c in self.cases})

    def design_summary(self) -> dict:
        return {
            "n_cases": len(self.cases),
            "n_foods_effective_clusters": self.n_foods,
            "cases_per_food": round(len(self.cases) / self.n_foods, 1) if self.n_foods else 0,
            "foods": sorted({c.description for c in self.cases}),
            "clustering_warning": (
                f"{len(self.cases)} cases nested in {self.n_foods} foods. Nutrients "
                "within a food share species, provenance and sample, so the "
                "effective sample size is nearer the food count. Any p-value is "
                "indicative, not confirmatory."
            ),
        }


def stratify(cases: list[ch.LabeledCase], limit: int) -> list[ch.LabeledCase]:
    """
    Take `limit` cases spread evenly across foods, not the first `limit` rows.

    Truncating in list order concentrates a small pilot on whichever food
    sorts first — a 20-case pilot drawn entirely from three egg products says
    almost nothing about beef or fish, and collapses the cluster count that
    already limits this design. Round-robin keeps every food represented.
    """
    by_food: dict[str, list[ch.LabeledCase]] = {}
    for case in cases:
        by_food.setdefault(case.description, []).append(case)

    picked: list[ch.LabeledCase] = []
    round_index = 0
    while len(picked) < limit:
        added = False
        for food in sorted(by_food):
            if round_index < len(by_food[food]):
                picked.append(by_food[food][round_index])
                added = True
                if len(picked) == limit:
                    return picked
        if not added:
            break
        round_index += 1
    return picked


def load_cases(limit: Optional[int]) -> list[ch.LabeledCase]:
    """Curated DB pairings, falling back to description matching."""
    from fediaf_nutrients import get_usda_nutrient_ids

    nutrient_ids = get_usda_nutrient_ids()
    # Build the FULL set, then stratify — passing `limit` down would truncate
    # in list order and defeat the point.
    cases = ch.build_labeled_set_from_db(nutrient_ids)
    if not cases:
        print(
            "No curated DB pairings available; falling back to description "
            "matching (larger but mostly off-domain — see "
            "build_labeled_set_from_db).",
            file=sys.stderr,
        )
        cases = ch.build_labeled_set(nutrient_ids)
    if limit is not None and len(cases) > limit:
        cases = stratify(cases, limit)
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true",
                        help="print the design and cost, run nothing (free)")
    parser.add_argument("--pilot", action="store_true",
                        help="the two pre-checks only (cheapest useful run)")
    parser.add_argument("--arms", default="none",
                        help="comma-separated arm names, or 'all'")
    parser.add_argument("--limit", type=int, default=None,
                        help="cap the number of cases (pilot defaults to 20)")
    parser.add_argument("--out", type=Path, help="write full results JSON here")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    limit = args.limit if args.limit is not None else (20 if args.pilot else None)
    cases = load_cases(limit)
    if not cases:
        print("No labeled cases available (datasets or database missing).",
              file=sys.stderr)
        return 1

    experiment = Experiment(cases=cases)
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": ai_validation.model_provenance(),
        "design": experiment.design_summary(),
    }

    if args.plan:
        report["cost_estimates"] = {
            "pilot (pre-checks, 20 cases)": estimate_cost(
                [ARMS["none"], ARMS["selfcons"]], min(20, len(cases))
            ),
            "screening (none vs both)": estimate_cost(
                [ARMS["none"], ARMS["both"]], len(cases)
            ),
            "full 2x2": estimate_cost(list(ARMS.values()), len(cases)),
        }
        print(json.dumps(report, indent=2))
        return 0

    if args.pilot:
        # Pre-check 1 needs one cheap baseline pass; pre-check 2 re-asks a
        # handful of those same questions N times.
        baseline = run_arm(ARMS["none"], cases, verbose=args.verbose)
        experiment.by_arm["none"] = baseline
        report["precheck_confidence_spread"] = assess_confidence_spread(baseline)
        report["precheck_sample_divergence"] = probe_sample_divergence(
            cases[: min(8, len(cases))]
        )
        report["baseline_summary"] = ch.summarize(baseline)
        report["verdict"] = _pilot_verdict(report)
    else:
        names = list(ARMS) if args.arms == "all" else [
            n.strip() for n in args.arms.split(",") if n.strip()
        ]
        unknown = [n for n in names if n not in ARMS]
        if unknown:
            print(f"Unknown arm(s): {unknown}. Known: {list(ARMS)}", file=sys.stderr)
            return 1

        report["cost_estimate"] = estimate_cost([ARMS[n] for n in names], len(cases))
        for name in names:
            print(f"Running arm {ARMS[name].label} over {len(cases)} cases...",
                  file=sys.stderr)
            experiment.by_arm[name] = run_arm(ARMS[name], cases, verbose=args.verbose)

        report["summary_by_arm"] = {
            name: ch.summarize(scored) for name, scored in experiment.by_arm.items()
        }
        report["paired_comparisons"] = {
            f"{a}_vs_{b}": mcnemar(experiment.by_arm[a], experiment.by_arm[b])
            for i, a in enumerate(names) for b in names[i + 1:]
        }
        report["factorial"] = factorial_effects(experiment.by_arm)

    printable = {k: v for k, v in report.items() if k != "raw"}
    print(json.dumps(printable, indent=2, default=str))

    if args.out:
        report["raw"] = {
            name: [c.__dict__ for c in scored]
            for name, scored in experiment.by_arm.items()
        }
        args.out.write_text(json.dumps(report, indent=2, default=str))
        print(f"\nFull results written to {args.out}", file=sys.stderr)
    return 0


def _pilot_verdict(report: dict) -> dict:
    """Turn the two pre-checks into a go/no-go on the rest of the experiment."""
    spread = report["precheck_confidence_spread"]
    divergence = report["precheck_sample_divergence"]
    actions = []
    if not spread["measurable"]:
        actions.append(
            "Calibration is not measurable: confidence is effectively constant. "
            "Skip per-confidence analysis; consider whether auto-accept "
            "thresholds keyed to confidence are justifiable at all."
        )
    else:
        actions.append("Calibration is measurable: proceed with per-confidence analysis.")

    if not divergence["informative"]:
        actions.append(
            "Self-consistency is inert (samples identical): drop the 'selfcons' "
            "and 'both' arms and run 'none' vs 'search' only — halving the cost."
        )
    else:
        actions.append("Self-consistency has signal: keep it in the factorial.")

    return {"next_steps": actions}


if __name__ == "__main__":
    raise SystemExit(main())
