"""Comparison + rule engine: assemble per-nutrient evidence, screen echoes,
and produce ADVISORY verdicts per the sweep decision rules (runbook §2.3).

Nothing here decides anything — the operator reviews every verdict; the rule
engine exists so review time goes to the genuinely contested rows.

Evidence semantics (2026-08-18 audit):
- `independent` evidence = INDEPENDENT_QUALITIES minus USDA-lineage sources.
  USDA-affiliated tables (Iodine DB) are real measurements and may anchor a
  value when USDA has none, but can never *confirm* USDA.
- Measured zeros are evidence and stay in medians/agreement.
- Trace and censored values are detection-limit information only: reported in
  reasons, never counted as agreeing or disagreeing measurements.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from intake.model import (
    FEDIAF_BY_ID,
    FEDIAF_NUTRIENTS_ORDER,
    FORM_TOTAL_K,
    INDEPENDENT_QUALITIES,
    Q_BORROWED,
    Q_CENSORED,
    Q_TRACE,
    REGION_SENSITIVE_IDS,
    Extraction,
    SourceValue,
)

# Scale-aware agreement floor per FEDIAF unit: differences below this are
# noise regardless of ratio (the sweep's LC-PUFA lesson).
EPS_BY_UNIT = {"g": 0.01, "mg": 0.01, "µg": 1.0, "IU": 1.0, "kcal": 6.0}
AGREEMENT_RTOL = 0.20

# Echo screening thresholds: a foreign food is an echo when many of its
# nonzero values are USDA (either table) to <0.5%.
ECHO_RTOL = 0.005
ECHO_MIN_MATCHES = 5
ECHO_MIN_RATIO = 0.4

V_CONFIRM = "confirm"
V_USDA_ONLY = "usda_only"
V_REGION_KEEP = "region_keep"
V_REPLACE = "replace_suggest"
V_FORM_DEFECT = "form_defect"
V_ADOPT = "adopt_foreign"
V_REVIEW = "review"
V_NO_EVIDENCE = "no_evidence"


def engine_constants() -> dict:
    """The active rule-engine thresholds, stamped into every artifact so a
    committed report/decisions file records the regime it was produced under."""
    return {
        "agreement_rtol": AGREEMENT_RTOL,
        "eps_by_unit": dict(EPS_BY_UNIT),
        "echo_rtol": ECHO_RTOL,
        "echo_min_matches": ECHO_MIN_MATCHES,
        "echo_min_ratio": ECHO_MIN_RATIO,
    }


@dataclass
class Suggestion:
    value: float
    source: str                      # foundation | sr_legacy | literature
    comment: str
    num_samples: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    year_acquired: Optional[str] = None
    derivation_description: Optional[str] = None


@dataclass
class NutrientComparison:
    nutrient_id: int
    name: str
    unit: str
    foundation: Optional[SourceValue]
    sr: Optional[SourceValue]
    foreign: list[SourceValue]
    verdict: str = V_NO_EVIDENCE
    reasons: list[str] = field(default_factory=list)
    suggestion: Optional[Suggestion] = None


def _eps(unit: str) -> float:
    return EPS_BY_UNIT.get(unit, 0.01)


def agrees(a: float, b: float, unit: str) -> bool:
    return abs(a - b) <= max(AGREEMENT_RTOL * max(abs(a), abs(b)), _eps(unit))


def _food_key(sv: SourceValue) -> str:
    return f"{sv.source}:{sv.source_food}"


def screen_echoes(extraction: Extraction) -> dict[str, str]:
    """Flag foreign source-foods that copy USDA; returns {source_food: summary}.

    Every nonzero foreign value is compared against BOTH USDA tables — a copy
    of SR must not escape because Foundation happens to publish a different
    number for the same nutrient (audit finding 2026-08-18). USDA-lineage
    sources are labeled as such and never counted independent.
    """
    usda_values: dict[int, list[float]] = {}
    for table in (extraction.foundation, extraction.sr):
        for nid, sv in table.items():
            usda_values.setdefault(nid, []).append(sv.value)

    by_food: dict[str, list[SourceValue]] = {}
    for sv in extraction.foreign:
        by_food.setdefault(_food_key(sv), []).append(sv)

    verdicts: dict[str, str] = {}
    echoed: set[str] = set()
    for food_key, svs in by_food.items():
        if any(sv.usda_lineage for sv in svs):
            verdicts[food_key] = "USDA-affiliated — evidence, never independent confirmation"
            continue
        comparable = matches = 0
        for sv in svs:
            candidates = [uv for uv in usda_values.get(sv.nutrient_id, ()) if uv > 0]
            if sv.value <= 0 or not candidates:
                continue
            comparable += 1
            if any(abs(sv.value - uv) / uv < ECHO_RTOL for uv in candidates):
                matches += 1
        if comparable == 0:
            verdicts[food_key] = "no USDA overlap — independence not establishable"
        elif matches >= ECHO_MIN_MATCHES and matches / comparable >= ECHO_MIN_RATIO:
            verdicts[food_key] = (
                f"ECHO of USDA ({matches}/{comparable} values identical to "
                f"<{ECHO_RTOL:.1%})")
            echoed.add(food_key)
        else:
            verdicts[food_key] = f"independent ({matches}/{comparable} incidental matches)"
    if echoed:
        extraction.foreign = [
            sv.as_echo() if _food_key(sv) in echoed else sv
            for sv in extraction.foreign
        ]
    return verdicts


def _independents(foreign: list[SourceValue]) -> list[SourceValue]:
    """Values that can confirm/contest USDA: independent qualities, non-lineage."""
    return [sv for sv in foreign
            if sv.quality in INDEPENDENT_QUALITIES and not sv.usda_lineage]


def _measured_evidence(foreign: list[SourceValue]) -> list[SourceValue]:
    """Values usable as an anchor when USDA has nothing: independents plus
    USDA-lineage measurements (real data absent from FDC, e.g. Iodine DB)."""
    return [sv for sv in foreign if sv.quality in INDEPENDENT_QUALITIES]


def _bounds_info(foreign: list[SourceValue]) -> str:
    """Detection-limit context (trace/censored), for reasons lines."""
    bounds = [sv for sv in foreign if sv.quality in (Q_CENSORED, Q_TRACE)]
    if not bounds:
        return ""
    parts = []
    for sv in bounds:
        parts.append(f"{sv.source} <= {sv.value:g}" if sv.quality == Q_CENSORED
                     else f"{sv.source} trace")
    return "detection-limit info: " + ", ".join(parts)


def _quality_rank(sv: SourceValue) -> int:
    order = ("analysed", "compiled", "estimated", "unknown")
    return order.index(sv.quality) if sv.quality in order else len(order)


def closest_to_median(svs: list[SourceValue]) -> tuple[SourceValue, bool]:
    """(anchor, was_split). Deterministic: distance to median, ties broken by
    larger n, then quality rank, then lower value — never floating-point noise
    (audit finding 2026-08-18: a two-way literature split was decided by the
    16th decimal digit of the distance).

    was_split is True only when the equidistant candidates carry DIFFERENT
    values — identical measurements are agreement, not a split, and must not
    trigger the review-must-arbitrate flag (round-2 audit: the flag fired on
    every even-count set, teaching operators to skim past it)."""
    med = statistics.median(sv.value for sv in svs)
    tol = 1e-9 * max(1.0, abs(med))
    best = min(abs(sv.value - med) for sv in svs)
    tied = [sv for sv in svs if abs(sv.value - med) - best <= tol]
    if len(tied) == 1:
        return tied[0], False
    tied.sort(key=lambda sv: (-(sv.n or 0), _quality_rank(sv), sv.value))
    was_split = len({sv.value for sv in tied}) > 1
    return tied[0], was_split


_TIE_REASON = "anchor is a tie-break between split sources — review must arbitrate"


def _cite(svs: list[SourceValue]) -> str:
    return ", ".join(
        f"{sv.source} {sv.value:g}" + (f" (n={sv.n})" if sv.n else "")
        for sv in svs
    )


def _stats_from(sv: SourceValue) -> dict:
    """Anchor-source stats worth storing (cv-v7: coherent {min,max,n} only;
    a zero-width range is a single-determination artifact, not a spread)."""
    if (sv.n and sv.vmin is not None and sv.vmax is not None
            and 0 < sv.vmin <= sv.value <= sv.vmax and sv.vmin < sv.vmax):
        return {"num_samples": sv.n, "min_value": sv.vmin, "max_value": sv.vmax}
    return {"num_samples": sv.n} if sv.n else {}


def judge(comparison: NutrientComparison) -> None:
    """Apply the runbook §2.3 rules; fills verdict/reasons/suggestion in place."""
    nid = comparison.nutrient_id
    unit = comparison.unit
    today = date.today().isoformat()
    primary = comparison.foundation or comparison.sr
    primary_src = "foundation" if comparison.foundation else "sr_legacy"
    independents = _independents(comparison.foreign)
    bounds_note = _bounds_info(comparison.foreign)

    if primary is None:
        evidence = _measured_evidence(comparison.foreign)
        if evidence:
            anchor, tied = closest_to_median(evidence)
            comparison.verdict = V_ADOPT
            comparison.reasons.append(
                f"no USDA value; {len(evidence)} measured source(s) available")
            if tied:
                comparison.reasons.append(_TIE_REASON)
            if bounds_note:
                comparison.reasons.append(bounds_note)
            comparison.suggestion = Suggestion(
                value=anchor.value, source="literature",
                comment=(f"Validated {today}: no USDA value; set from {anchor.source} "
                         f"({anchor.source_food}) — refs: {_cite(evidence)}"),
                **_stats_from(anchor),
            )
        elif comparison.foreign:
            comparison.verdict = V_REVIEW
            qualities = ", ".join(sorted({sv.quality for sv in comparison.foreign}))
            comparison.reasons.append(
                f"no USDA value and no measured foreign value (only {qualities}) "
                f"— operator/literature call")
            if bounds_note:
                comparison.reasons.append(bounds_note)
        else:
            comparison.verdict = V_NO_EVIDENCE
            comparison.reasons.append(
                "no measurement in any local resource — operator/literature call")
        return

    stats = _stats_from(primary)
    base = Suggestion(
        value=primary.value, source=primary_src,
        comment="", year_acquired=primary.year,
        derivation_description=primary.note.split(";")[0] if primary.note.startswith("deriv") else None,
        **stats,
    )
    nonzero_ind = [sv for sv in independents if sv.value > 0]

    # assumed/borrowed zero vs nonzero independents (runbook rule 3) — fires
    # only when the independents' *median* is genuinely nonzero (independents
    # measuring zero argue the zero is real, audit 2026-08-18).
    if (primary.value == 0 and primary.quality == Q_BORROWED and nonzero_ind
            and statistics.median(sv.value for sv in independents) > _eps(unit)):
        if nid in REGION_SENSITIVE_IDS:
            pick = min(nonzero_ind, key=lambda sv: sv.value)
            edge = " (low edge, US practice)"
            tied = False
        else:
            pick, tied = closest_to_median(nonzero_ind)
            edge = ""
        comparison.verdict = V_REPLACE
        comparison.reasons.append(
            f"USDA zero is assumed/borrowed ({primary.note[:60]}) but "
            f"{len(nonzero_ind)} independent(s) measure nonzero")
        if tied:
            comparison.reasons.append(_TIE_REASON)
        if bounds_note:
            comparison.reasons.append(bounds_note)
        comparison.suggestion = Suggestion(
            value=pick.value, source="literature",
            comment=(f"Validated {today}: USDA assumed zero replaced{edge} per "
                     f"{pick.source} ({pick.source_food}); refs: {_cite(nonzero_ind)}"),
            **_stats_from(pick),
        )
        return

    # menaquinone form defect (runbook rule 4): compare against form-declared
    # total-K values only — never against note text (audit 2026-08-18).
    if nid == 1185:
        totals = [sv for sv in nonzero_ind if sv.form == FORM_TOTAL_K]
        if totals:
            med = statistics.median(sv.value for sv in totals)
            if med >= 3 * max(primary.value, 1.0):
                pick, tied = closest_to_median(totals)
                comparison.verdict = V_FORM_DEFECT
                comparison.reasons.append(
                    f"USDA K row is K1-only ({primary.value:g} µg); "
                    f"menaquinone-inclusive tables read ~{med:g} µg")
                if tied:
                    comparison.reasons.append(_TIE_REASON)
                comparison.suggestion = Suggestion(
                    value=pick.value, source="literature",
                    comment=(f"Validated {today}: SR vit K counts K1 only; total-K "
                             f"(incl. MK-4) set per {pick.source} ({pick.source_food}); "
                             f"refs: {_cite(totals)}"),
                    **_stats_from(pick),
                )
                return

    hits = [sv for sv in independents if agrees(sv.value, primary.value, unit)]
    if hits:
        comparison.verdict = V_CONFIRM
        comparison.reasons.append(
            f"{len(hits)}/{len(independents)} independent(s) within "
            f"±{AGREEMENT_RTOL:.0%}: {_cite(hits)}")
        if bounds_note:
            comparison.reasons.append(bounds_note)
        base.comment = (f"Validated {today}: kept {primary_src} {primary.value:g} {unit}; "
                        f"refs within range: {_cite(hits)}")
        comparison.suggestion = base
        return

    if not independents:
        lineage = [sv for sv in _measured_evidence(comparison.foreign)
                   if sv.usda_lineage]
        comparison.verdict = V_USDA_ONLY
        note = "no independent foreign value"
        if lineage:
            note += f"; USDA-lineage evidence: {_cite(lineage)}"
        comparison.reasons.append(note)
        if bounds_note:
            comparison.reasons.append(bounds_note)
        base.comment = (f"Validated {today}: kept {primary_src} {primary.value:g} {unit} — "
                        f"no independent measurement in any local resource")
        comparison.suggestion = base
        return

    if nid in REGION_SENSITIVE_IDS:
        comparison.verdict = V_REGION_KEEP
        comparison.reasons.append(
            f"region-sensitive; foreign cluster differs: {_cite(independents)} — "
            f"US mean kept unless defective")
        if bounds_note:
            comparison.reasons.append(bounds_note)
        base.comment = (f"Validated {today}: kept {primary_src} {primary.value:g} {unit} "
                        f"(region rule; intl: {_cite(independents)})")
        comparison.suggestion = base
        return

    comparison.verdict = V_REVIEW
    comparison.reasons.append(
        f"all {len(independents)} independent(s) differ >±{AGREEMENT_RTOL:.0%} "
        f"from {primary_src} {primary.value:g}: {_cite(independents)}")
    if bounds_note:
        comparison.reasons.append(bounds_note)
    base.comment = (f"Validated {today}: kept {primary_src} {primary.value:g} {unit} "
                    f"after review (intl differ: {_cite(independents)})")
    comparison.suggestion = base  # USDA as the starting point; operator decides


def verdict_counts(comparisons: list[NutrientComparison]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in comparisons:
        counts[c.verdict] = counts.get(c.verdict, 0) + 1
    return counts


def compare_all(extraction: Extraction) -> tuple[list[NutrientComparison], dict[str, str]]:
    echo_verdicts = screen_echoes(extraction)
    foreign_by_nid: dict[int, list[SourceValue]] = {}
    for sv in extraction.foreign:
        foreign_by_nid.setdefault(sv.nutrient_id, []).append(sv)

    comparisons = []
    for nid in FEDIAF_NUTRIENTS_ORDER:
        info = FEDIAF_BY_ID[nid]
        comparison = NutrientComparison(
            nutrient_id=nid, name=info["nutrient_name"], unit=info["unit"],
            foundation=extraction.foundation.get(nid),
            sr=extraction.sr.get(nid),
            foreign=foreign_by_nid.get(nid, []),
        )
        judge(comparison)
        comparisons.append(comparison)
    return comparisons, echo_verdicts
