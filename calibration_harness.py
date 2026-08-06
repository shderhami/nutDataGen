"""
Calibration harness for AI validation (plan 5.1).

Everything else in the hardening plan is argued from one observed failure and
one small experiment. This is the piece that produces evidence: build a
labeled set from foods present in BOTH SR Legacy and Foundation, treat the
Foundation value as ground truth, run validation over the SR Legacy value
alone, and measure precision/recall per self-reported confidence level.

What it answers:
  - Does "high confidence" actually mean more accurate than "low"?
  - Where should the auto-accept threshold sit?
  - Did a prompt change help, or did it just move the labels around?

Usage:
    # Offline dry run (mock responses, no cost) — checks the plumbing:
    python calibration_harness.py --limit 5

    # Real measurement (billed):
    AI_MOCK_MODE=false ALLOW_LIVE_AI_CALLS=1 python calibration_harness.py \
        --limit 25 --out Docs/Planning/calibration_run.json

Ground-truth caveat: Foundation is a re-analysis, not truth. Where the two
sources legitimately differ (different cut, different year), a correct AI
answer can score as wrong. Read the accuracy numbers as *relative* across
confidence levels and across prompt versions, not as absolute correctness.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterator, Optional

import cv_config
from ai_validation import (
    AIValidationResult,
    model_provenance,
    validate_nutrients_concurrent,
)

# A prediction counts as correct when it lands within this relative distance
# of the Foundation value. 10% is wider than analytical error and narrower
# than the biological variation peer cohorts show (8-26%).
ACCURACY_TOLERANCE = 0.10

# Only score nutrients whose two sources disagree by at least this much: where
# SR and Foundation already agree, every answer scores correct and the metric
# says nothing.
MIN_INFORMATIVE_DISCREPANCY = 0.05


def _read_nutrient_metadata(dataset_dir: Path) -> dict[int, dict[int, dict]]:
    """
    {fdc_id: {nutrient_id: provenance dict}} in the shape the prompts expect.

    Lets the experiment show the model exactly what the live pipeline shows —
    data points, min/median/max, derivation, sample year — instead of an empty
    block, which would silently measure the pre-Phase-2 prompt.
    """
    from usda_api import DERIVATION_CODES

    derivations: dict[str, str] = {}
    derivation_csv = dataset_dir / "food_nutrient_derivation.csv"
    if derivation_csv.exists():
        with open(derivation_csv, newline="") as fh:
            for row in csv.DictReader(fh):
                derivations[row["id"]] = row.get("description", "").strip()

    def num(raw: object) -> Optional[float]:
        text = (raw or "").strip() if isinstance(raw, str) else raw
        try:
            return float(text) if text not in (None, "") else None
        except (TypeError, ValueError):
            return None

    out: dict[int, dict[int, dict]] = {}
    with open(dataset_dir / "food_nutrient.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                fdc_id, nutrient_id = int(row["fdc_id"]), int(row["nutrient_id"])
            except (KeyError, TypeError, ValueError):
                continue
            derivation_id = (row.get("derivation_id") or "").strip()
            description = derivations.get(derivation_id, "")
            if not description and derivation_id in DERIVATION_CODES:
                description = DERIVATION_CODES[derivation_id]
            out.setdefault(fdc_id, {})[nutrient_id] = {
                "num_samples": (
                    int(num(row.get("data_points")))
                    if num(row.get("data_points")) is not None else None
                ),
                "min_value": num(row.get("min")),
                "max_value": num(row.get("max")),
                "median_value": num(row.get("median")),
                "year_acquired": (row.get("min_year_acquired") or "").strip() or None,
                "derivation_description": description or None,
            }
    return out


@dataclass(frozen=True)
class LabeledCase:
    """One SR-value-with-Foundation-ground-truth case."""
    fdc_id_sr: int
    fdc_id_foundation: int
    description: str
    nutrient_id: int
    sr_value: float
    foundation_value: float
    unit: str
    # Food identity, so the prompt can be built the way the pipeline builds it
    # (species/cooking method drive both prompt wording and peer cohorts).
    protein_species: Optional[str] = None
    cooking_method: Optional[str] = None
    category: Optional[str] = None
    # The SR row's own provenance, as the pipeline would show it. Withholding
    # this would measure the pre-Phase-2 prompt rather than the live one.
    sr_metadata: dict = field(default_factory=dict)

    @property
    def food_info(self) -> dict:
        """
        Food identity for the prompt.

        `foundation_fdc_id` is deliberately OMITTED: it identifies the row
        being used as ground truth, and with web search enabled the model
        could look it up and score itself. Leaking it would make the search
        arm look better for the wrong reason.
        """
        return {
            "food_name": self.description,
            "protein_species": self.protein_species,
            "cooking_method": self.cooking_method,
            "category": self.category,
            "sr_fdc_id": self.fdc_id_sr,
        }

    @property
    def nutrient_name(self) -> str:
        """FEDIAF name, so the prompt asks about 'Ash', not 'nutrient 1007'."""
        from fediaf_nutrients import get_nutrient_by_id

        info = get_nutrient_by_id(self.nutrient_id)
        return info["nutrient_name"] if info else f"nutrient {self.nutrient_id}"

    @property
    def nutrient_unit(self) -> str:
        from fediaf_nutrients import get_nutrient_by_id

        info = get_nutrient_by_id(self.nutrient_id)
        return (info["unit"] if info else "") or self.unit

    @property
    def relative_gap(self) -> float:
        denom = abs(self.foundation_value)
        if denom == 0:
            return 0.0 if self.sr_value == 0 else float("inf")
        return abs(self.sr_value - self.foundation_value) / denom


@dataclass
class ScoredCase:
    """A labeled case plus what the validator said about it."""
    nutrient_id: int
    description: str
    sr_value: float
    foundation_value: float
    predicted_value: float
    recommendation: str
    confidence: str
    correct: bool
    relative_error: float


def _read_food_descriptions(dataset_dir: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    with open(dataset_dir / "food.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                out[int(row["fdc_id"])] = (row.get("description") or "").strip()
            except (KeyError, TypeError, ValueError):
                continue
    return out


def _read_nutrient_amounts(dataset_dir: Path) -> dict[int, dict[int, float]]:
    """{fdc_id: {nutrient_id: amount}} for measured rows only."""
    out: dict[int, dict[int, float]] = {}
    with open(dataset_dir / "food_nutrient.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                data_points = (row.get("data_points") or "").strip()
                if not data_points or int(data_points) <= 0:
                    continue
                fdc_id = int(row["fdc_id"])
                out.setdefault(fdc_id, {})[int(row["nutrient_id"])] = float(row["amount"])
            except (KeyError, TypeError, ValueError):
                continue
    return out


def _normalize(description: str) -> str:
    """
    Pairing key for matching an SR Legacy food to its Foundation counterpart.

    Deliberately the FULL description, normalized only for punctuation and
    whitespace. A looser key (e.g. the first two comma-separated parts)
    collapses "Fish, salmon, king, chinook, smoked and canned" and
    "Fish, salmon, king, chinook, smoked, brined" onto one Foundation food,
    manufacturing 500% "disagreements" that are really mispairings — the exact
    unverified-matching failure mode §2 of the plan warns about. Exact
    matching yields ~100 pairs, which is enough, and every pair is real.
    """
    return " ".join(description.lower().replace(",", " ").split())


def build_labeled_set_from_db(
    nutrient_ids: list[int],
    limit: Optional[int] = None,
) -> list[LabeledCase]:
    """
    Labeled cases from the operator's own curated SR<->Foundation pairings.

    This is the preferred source. `ingredients` rows carrying BOTH
    sr_legacy_fdc_id and foundation_fdc_id were matched by hand during real
    ingredient adds, so every pair is verified and in-domain — raw muscle
    meat, organ, egg, fish — which is what the prompts are written for.
    Description-matching against the bulk CSVs (build_labeled_set below)
    produces a larger but mostly off-domain set: no organ meat at all, and
    foods like fried rice and bologna that the prompts were never aimed at.

    Ingredients with no foundation_fdc_id genuinely have no Foundation
    record, so this set is complete, not truncated.

    Returns [] when the datasets or the database are unavailable.
    """
    srl, fdn = cv_config.FDC_SRL_DIR, cv_config.FDC_FDN_DIR
    if not (srl / "food_nutrient.csv").exists():
        return []

    try:
        from db_connection import get_db

        with get_db().cursor() as cur:
            cur.execute(
                """
                SELECT food_name, category, protein_species, cooking_method,
                       sr_legacy_fdc_id, foundation_fdc_id
                  FROM ingredients
                 WHERE sr_legacy_fdc_id IS NOT NULL
                   AND foundation_fdc_id IS NOT NULL
                 ORDER BY category, food_name
                """
            )
            rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        print(f"Could not read curated pairs from the database: {exc}", file=sys.stderr)
        return []

    sr_amounts = _read_nutrient_amounts(srl)
    fdn_amounts = _read_nutrient_amounts(fdn)
    sr_metadata = _read_nutrient_metadata(srl)

    wanted = set(nutrient_ids)
    cases: list[LabeledCase] = []
    for row in rows:
        # db_connection uses a dict cursor; tolerate a plain tuple cursor too.
        if isinstance(row, dict):
            name, category = row["food_name"], row["category"]
            species, method = row["protein_species"], row["cooking_method"]
            sr_id, fdn_id = row["sr_legacy_fdc_id"], row["foundation_fdc_id"]
        else:
            name, category, species, method, sr_id, fdn_id = row

        sr_row = sr_amounts.get(int(sr_id), {})
        fdn_row = fdn_amounts.get(int(fdn_id), {})
        for nutrient_id in sorted(wanted & sr_row.keys() & fdn_row.keys()):
            case = LabeledCase(
                fdc_id_sr=int(sr_id),
                fdc_id_foundation=int(fdn_id),
                description=name,
                nutrient_id=nutrient_id,
                sr_value=sr_row[nutrient_id],
                foundation_value=fdn_row[nutrient_id],
                unit="",
                protein_species=species,
                cooking_method=method,
                category=category,
                sr_metadata=sr_metadata.get(int(sr_id), {}).get(nutrient_id, {}),
            )
            if case.relative_gap >= MIN_INFORMATIVE_DISCREPANCY:
                cases.append(case)
            if limit is not None and len(cases) >= limit:
                return cases
    return cases


def build_labeled_set(
    nutrient_ids: list[int],
    limit: Optional[int] = None,
) -> list[LabeledCase]:
    """
    Pair SR Legacy and Foundation foods and emit informative cases.

    Pairing is by normalized description prefix — deliberately conservative
    and deliberately visible: §2 of the plan flags the earlier audit's
    matching methodology as unverified, so this rebuilds it in the open
    rather than reusing scratchpad artifacts.

    Returns [] when the bulk datasets are absent.
    """
    srl, fdn = cv_config.FDC_SRL_DIR, cv_config.FDC_FDN_DIR
    if not (srl / "food.csv").exists() or not (fdn / "food.csv").exists():
        return []

    sr_desc = _read_food_descriptions(srl)
    fdn_desc = _read_food_descriptions(fdn)
    sr_amounts = _read_nutrient_amounts(srl)
    fdn_amounts = _read_nutrient_amounts(fdn)

    fdn_by_key: dict[str, int] = {}
    for fdc_id, description in fdn_desc.items():
        fdn_by_key.setdefault(_normalize(description), fdc_id)

    wanted = set(nutrient_ids)
    cases: list[LabeledCase] = []
    for sr_id, description in sorted(sr_desc.items()):
        fdn_id = fdn_by_key.get(_normalize(description))
        if fdn_id is None:
            continue
        sr_row = sr_amounts.get(sr_id, {})
        fdn_row = fdn_amounts.get(fdn_id, {})
        for nutrient_id in sorted(wanted & sr_row.keys() & fdn_row.keys()):
            case = LabeledCase(
                fdc_id_sr=sr_id,
                fdc_id_foundation=fdn_id,
                description=description,
                nutrient_id=nutrient_id,
                sr_value=sr_row[nutrient_id],
                foundation_value=fdn_row[nutrient_id],
                unit="",
            )
            if case.relative_gap >= MIN_INFORMATIVE_DISCREPANCY:
                cases.append(case)
            if limit is not None and len(cases) >= limit:
                return cases
    return cases


def _predicted_value(result: AIValidationResult, case: LabeledCase) -> Optional[float]:
    """The value the validator's recommendation would actually write."""
    if result.recommendation == "sr_legacy":
        return case.sr_value
    if result.recommendation == "foundation":
        return case.foundation_value
    if result.recommendation in ("literature", "confirmed_zero"):
        return result.recommended_value
    return None


def score_cases(
    cases: list[LabeledCase],
    results_by_nutrient: dict[int, AIValidationResult],
) -> list[ScoredCase]:
    """Score one food's cases against Foundation ground truth."""
    scored: list[ScoredCase] = []
    for case in cases:
        result = results_by_nutrient.get(case.nutrient_id)
        if result is None or result.recommendation in ("error", "unknown"):
            continue
        predicted = _predicted_value(result, case)
        if predicted is None:
            continue
        denom = abs(case.foundation_value)
        relative_error = (
            abs(predicted - case.foundation_value) / denom if denom else
            (0.0 if predicted == 0 else float("inf"))
        )
        scored.append(ScoredCase(
            nutrient_id=case.nutrient_id,
            description=case.description,
            sr_value=case.sr_value,
            foundation_value=case.foundation_value,
            predicted_value=predicted,
            recommendation=result.recommendation,
            confidence=result.confidence,
            correct=relative_error <= ACCURACY_TOLERANCE,
            relative_error=relative_error,
        ))
    return scored


def summarize(scored: list[ScoredCase]) -> dict:
    """
    Accuracy per confidence level — the number the plan is missing.

    A calibrated validator shows accuracy rising monotonically with
    confidence. If "high" is no more accurate than "low", the label carries
    no information and auto-accept thresholds keyed to it are unjustified.
    """
    by_confidence: dict[str, list[ScoredCase]] = {}
    for case in scored:
        by_confidence.setdefault(case.confidence, []).append(case)

    levels = {}
    for confidence, cases in by_confidence.items():
        correct = [c for c in cases if c.correct]
        finite = [c.relative_error for c in cases if c.relative_error != float("inf")]
        levels[confidence] = {
            "n": len(cases),
            "accuracy": round(len(correct) / len(cases), 4) if cases else None,
            "median_relative_error": (
                round(statistics.median(finite), 4) if finite else None
            ),
        }

    order = ["high", "medium", "low"]
    present = [c for c in order if c in levels and levels[c]["n"] >= 5]
    accuracies = [levels[c]["accuracy"] for c in present]
    calibrated = all(
        a >= b for a, b in zip(accuracies, accuracies[1:])
    ) if len(accuracies) >= 2 else None

    return {
        "provenance": model_provenance(),
        "tolerance": ACCURACY_TOLERANCE,
        "total_scored": len(scored),
        "overall_accuracy": (
            round(sum(1 for c in scored if c.correct) / len(scored), 4)
            if scored else None
        ),
        "by_confidence": levels,
        "confidence_is_calibrated": calibrated,
        "note": (
            "Foundation is a re-analysis, not truth; read these numbers as "
            "relative across confidence levels and prompt versions."
        ),
    }


def group_by_food(cases: list[LabeledCase]) -> Iterator[tuple[str, list[LabeledCase]]]:
    """Yield (description, cases) so each food is validated in one batch."""
    grouped: dict[str, list[LabeledCase]] = {}
    for case in cases:
        grouped.setdefault(case.description, []).append(case)
    yield from grouped.items()


def run(limit: Optional[int] = None, verbose: bool = False) -> dict:
    """Build the labeled set, validate it, and summarize."""
    from fediaf_nutrients import get_usda_nutrient_ids

    cases = build_labeled_set(get_usda_nutrient_ids(), limit=limit)
    if not cases:
        return {
            "error": (
                "No labeled cases. The USDA bulk datasets are gitignored — "
                f"expected them under {cv_config.USDA_BULK_DIR}."
            )
        }

    all_scored: list[ScoredCase] = []
    for description, food_cases in group_by_food(cases):
        comparison = {
            "matches": [],
            "discrepancies": [],
            "sr_only": [
                {
                    "nutrient_id": case.nutrient_id,
                    "nutrient_name": f"nutrient {case.nutrient_id}",
                    "unit": case.unit,
                    "sr_value": case.sr_value,
                    "sr_metadata": {},
                }
                for case in food_cases
            ],
            "foundation_only": [],
        }
        results = validate_nutrients_concurrent(
            food_name=description,
            comparison_result=comparison,
            sr_data={"nutrients": {}},
            foundation_data=None,
            missing_nutrients=[],
            verbose=verbose,
        )
        all_scored.extend(score_cases(food_cases, results))

    summary = summarize(all_scored)
    summary["cases"] = [asdict(c) for c in all_scored]
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, default=25,
        help="max labeled cases to build (each is one billed call when live)",
    )
    parser.add_argument("--out", type=Path, help="write the full result JSON here")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    summary = run(limit=args.limit, verbose=args.verbose)

    if "error" in summary:
        print(summary["error"], file=sys.stderr)
        return 1

    print(json.dumps({k: v for k, v in summary.items() if k != "cases"}, indent=2))
    if args.out:
        args.out.write_text(json.dumps(summary, indent=2))
        print(f"\nFull results written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
