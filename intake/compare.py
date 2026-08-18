"""Comparison + rule engine: assemble per-nutrient evidence, screen echoes,
and produce ADVISORY verdicts per the sweep decision rules (runbook §2.3).

Nothing here decides anything — the operator reviews every verdict; the rule
engine exists so review time goes to the genuinely contested rows.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from intake.model import (
    FEDIAF_BY_ID,
    FEDIAF_NUTRIENTS_ORDER,
    INDEPENDENT_QUALITIES,
    Q_BORROWED,
    Q_CENSORED,
    REGION_SENSITIVE_IDS,
    Extraction,
    SourceValue,
)

# Scale-aware agreement floor per FEDIAF unit: differences below this are
# noise regardless of ratio (the sweep's LC-PUFA lesson).
_EPS_BY_UNIT = {"g": 0.01, "mg": 0.01, "µg": 1.0, "IU": 1.0, "kcal": 6.0}
AGREEMENT_RTOL = 0.20

# Echo screening thresholds: a foreign food is an echo when many of its
# nonzero values are USDA to <0.5%.
_ECHO_RTOL = 0.005
_ECHO_MIN_MATCHES = 5
_ECHO_MIN_RATIO = 0.4

V_CONFIRM = "confirm"
V_USDA_ONLY = "usda_only"
V_REGION_KEEP = "region_keep"
V_REPLACE = "replace_suggest"
V_FORM_DEFECT = "form_defect"
V_ADOPT = "adopt_foreign"
V_REVIEW = "review"
V_NO_EVIDENCE = "no_evidence"


@dataclass
class Suggestion:
    value: float
    source: str                      # foundation | sr_legacy | literature
    comment: str
    num_samples: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    median_value: Optional[float] = None
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
    return _EPS_BY_UNIT.get(unit, 0.01)


def agrees(a: float, b: float, unit: str) -> bool:
    return abs(a - b) <= max(AGREEMENT_RTOL * max(abs(a), abs(b)), _eps(unit))


def screen_echoes(extraction: Extraction) -> dict[str, str]:
    """Flag foreign source-foods that copy USDA; returns {source_food: summary}."""
    usda_values: dict[int, list[float]] = {}
    for table in (extraction.foundation, extraction.sr):
        for nid, sv in table.items():
            usda_values.setdefault(nid, []).append(sv.value)

    verdicts: dict[str, str] = {}
    by_food: dict[str, list[SourceValue]] = {}
    for sv in extraction.foreign:
        by_food.setdefault(f"{sv.source}:{sv.source_food}", []).append(sv)

    flagged: list[SourceValue] = []
    for food_key, svs in by_food.items():
        comparable = matches = 0
        for sv in svs:
            for uv in usda_values.get(sv.nutrient_id, ()):
                if sv.value > 0 and uv > 0:
                    comparable += 1
                    if abs(sv.value - uv) / uv < _ECHO_RTOL:
                        matches += 1
                    break
        if comparable and matches >= _ECHO_MIN_MATCHES and matches / comparable >= _ECHO_MIN_RATIO:
            verdicts[food_key] = f"ECHO of USDA ({matches}/{comparable} values identical to <0.5%)"
            flagged.extend(svs)
        else:
            verdicts[food_key] = f"independent ({matches}/{comparable} incidental matches)"
    if flagged:
        flagged_set = {id(sv) for sv in flagged}
        extraction.foreign = [
            sv.as_echo() if id(sv) in flagged_set else sv for sv in extraction.foreign
        ]
    return verdicts


def _independents(foreign: list[SourceValue]) -> list[SourceValue]:
    return [sv for sv in foreign if sv.quality in INDEPENDENT_QUALITIES]


def _cite(svs: list[SourceValue]) -> str:
    return ", ".join(
        f"{sv.source} {sv.value:g}" + (f" (n={sv.n})" if sv.n else "")
        for sv in svs
    )


def _stats_from(sv: SourceValue) -> dict:
    """Anchor-source stats worth storing (cv-v7: coherent {min,max,n} only)."""
    if sv.n and sv.vmin is not None and sv.vmax is not None and 0 < sv.vmin <= sv.value <= sv.vmax:
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
    nonzero_ind = [sv for sv in independents if sv.value > 0]

    if primary is None:
        if nonzero_ind:
            med = statistics.median(sv.value for sv in nonzero_ind)
            anchor = min(nonzero_ind, key=lambda sv: abs(sv.value - med))
            comparison.verdict = V_ADOPT
            comparison.reasons.append(
                f"no USDA value; {len(nonzero_ind)} independent(s) available"
            )
            comparison.suggestion = Suggestion(
                value=anchor.value, source="literature",
                comment=(f"Validated {today}: no USDA value; set from {anchor.source} "
                         f"({anchor.source_food}) — refs: {_cite(nonzero_ind)}"),
                **_stats_from(anchor),
            )
        elif comparison.foreign:
            comparison.verdict = V_REVIEW
            comparison.reasons.append(
                "no USDA value and no independent foreign value (only "
                + ", ".join(sorted({sv.quality for sv in comparison.foreign}))
                + ") — operator/literature call"
            )
        else:
            comparison.verdict = V_NO_EVIDENCE
            comparison.reasons.append(
                "no measurement in any local resource — operator/literature call"
            )
        return

    stats = _stats_from(primary)
    base = Suggestion(
        value=primary.value, source=primary_src,
        comment="", year_acquired=primary.year,
        derivation_description=primary.note.split(";")[0] if primary.note.startswith("deriv") else None,
        **stats,
    )

    # assumed/borrowed zero vs nonzero independents (runbook rule 3)
    if primary.value == 0 and primary.quality == Q_BORROWED and nonzero_ind:
        pick = (min(nonzero_ind, key=lambda sv: sv.value)
                if nid in REGION_SENSITIVE_IDS
                else min(nonzero_ind, key=lambda sv: abs(sv.value - statistics.median(v.value for v in nonzero_ind))))
        comparison.verdict = V_REPLACE
        comparison.reasons.append(
            f"USDA zero is assumed/borrowed ({primary.note[:60]}) but "
            f"{len(nonzero_ind)} independent(s) measure nonzero"
        )
        edge = " (low edge, US practice)" if nid in REGION_SENSITIVE_IDS else ""
        comparison.suggestion = Suggestion(
            value=pick.value, source="literature",
            comment=(f"Validated {today}: USDA assumed zero replaced{edge} per "
                     f"{pick.source} ({pick.source_food}); refs: {_cite(nonzero_ind)}"),
            **_stats_from(pick),
        )
        return

    # menaquinone form defect (runbook rule 4)
    if nid == 1185 and nonzero_ind:
        totals = [sv for sv in nonzero_ind
                  if "total" in sv.note.lower() or "k2" in sv.note.lower()]
        if totals:
            med = statistics.median(sv.value for sv in totals)
            if med >= 3 * max(primary.value, 1.0):
                pick = min(totals, key=lambda sv: abs(sv.value - med))
                comparison.verdict = V_FORM_DEFECT
                comparison.reasons.append(
                    f"USDA K row is K1-only ({primary.value:g} µg); "
                    f"menaquinone-inclusive tables read ~{med:g} µg"
                )
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
            f"{len(hits)}/{len(independents)} independent(s) within ±20%: {_cite(hits)}"
        )
        base.comment = (f"Validated {today}: kept {primary_src} {primary.value:g} {unit}; "
                        f"refs within range: {_cite(hits)}")
        comparison.suggestion = base
        return

    if not independents:
        censored = [sv for sv in comparison.foreign if sv.quality == Q_CENSORED]
        comparison.verdict = V_USDA_ONLY
        note = "no independent foreign value"
        if censored:
            note += f"; censored bounds: {_cite(censored)}"
        comparison.reasons.append(note)
        base.comment = (f"Validated {today}: kept {primary_src} {primary.value:g} {unit} — "
                        f"no independent measurement in any local resource")
        comparison.suggestion = base
        return

    if nid in REGION_SENSITIVE_IDS:
        comparison.verdict = V_REGION_KEEP
        comparison.reasons.append(
            f"region-sensitive; foreign cluster differs: {_cite(independents)} — "
            f"US mean kept unless defective"
        )
        base.comment = (f"Validated {today}: kept {primary_src} {primary.value:g} {unit} "
                        f"(region rule; intl: {_cite(independents)})")
        comparison.suggestion = base
        return

    comparison.verdict = V_REVIEW
    comparison.reasons.append(
        f"all {len(independents)} independent(s) differ >±20% from "
        f"{primary_src} {primary.value:g}: {_cite(independents)}"
    )
    base.comment = (f"Validated {today}: kept {primary_src} {primary.value:g} {unit} "
                    f"after review (intl differ: {_cite(independents)})")
    comparison.suggestion = base  # USDA as the starting point; operator decides


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
