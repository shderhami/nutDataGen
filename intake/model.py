"""Shared data model for the intake pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from fediaf_nutrients import FEDIAF_NUTRIENTS

# Canonical FEDIAF panel (52 nutrients), keyed by USDA nutrient id.
FEDIAF_BY_ID: dict[int, dict] = {n["nutrient_id"]: n for n in FEDIAF_NUTRIENTS}
FEDIAF_IDS: frozenset[int] = frozenset(FEDIAF_BY_ID)
FEDIAF_NUTRIENTS_ORDER: tuple[int, ...] = tuple(n["nutrient_id"] for n in FEDIAF_NUTRIENTS)

# PUFA-total invariant (the "lamb convention"): 1293 >= sum of tracked components.
PUFA_TOTAL_ID = 1293
PUFA_COMPONENT_IDS: tuple[int, ...] = (1269, 1270, 1271, 1272, 1278, 1280)

# Feed/soil-driven nutrients: international tables detect data-quality defects
# only — never re-center a sound US mean (region rule, decided 2026-08-16).
REGION_SENSITIVE_IDS: frozenset[int] = frozenset(
    {1100, 1103, 1106, 1109, 1110, 1272, 1278, 1280}
)

# Quality of a source value (how it was obtained, per that source's metadata).
Q_ANALYSED = "analysed"      # the source measured it
Q_BORROWED = "borrowed"      # the source copied it (USDA, M&W, Fineli, ...)
Q_COMPILED = "compiled"      # compilation table without per-value origin (CoFID)
Q_COMPUTED = "computed"      # calculated/recipe/formula/definitional value
Q_ESTIMATED = "estimated"    # source flags it estimated (MEXT parentheses)
Q_CENSORED = "censored"      # below detection/quantification ("< X"): value = X upper bound
Q_TRACE = "trace"            # source says trace: value stored as 0.0
Q_ECHO = "echo"              # screener verdict: this source's food copies USDA
Q_UNKNOWN = "unknown"

# Qualities that count as independent supporting evidence in the rule engine.
# Trace and censored values are detection-limit information, not measurements —
# they are reported alongside verdicts but never confirm or contest a value
# (audit finding 2026-08-18: a trace manufactured false `review` verdicts and
# suppressed the censored-bounds branch).
INDEPENDENT_QUALITIES = frozenset({Q_ANALYSED, Q_COMPILED, Q_ESTIMATED, Q_UNKNOWN})

# Vitamin K form tags (menaquinone doctrine): adapters declare what their K
# column covers so the rule engine never has to sniff free-text notes.
FORM_TOTAL_K = "total_k"     # K1 + menaquinones (MEXT VITK, BLS VITK, CIQUAL K1+K2)
FORM_K1_ONLY = "k1_only"     # phylloquinone only (SR/FND 1185, CoFID)
FORM_MK4_ONLY = "mk4_only"   # menaquinone-4 only (USDA 1183 with no 1185 row)


@dataclass(frozen=True)
class SourceValue:
    """One source's value for one FEDIAF nutrient, in the FEDIAF declared unit.

    Adapters do all unit conversion before constructing this, so values from
    different tables are directly comparable and directly storable.
    """

    source: str                      # short label: FND, SR, FCDB, BLS, MEXT, ...
    source_food: str                 # the source's own food id/name, verbatim
    nutrient_id: int
    value: float                     # in FEDIAF_BY_ID[nutrient_id]["unit"]
    n: Optional[int] = None
    vmin: Optional[float] = None     # same unit as value
    vmax: Optional[float] = None
    quality: str = Q_UNKNOWN
    note: str = ""                   # origin detail: derivation code, refs, form info
    year: Optional[str] = None
    form: str = ""                   # nutrient-form tag (FORM_TOTAL_K, FORM_K1_ONLY, ...)
    usda_lineage: bool = False       # source is USDA-affiliated: real evidence, but
                                     # never *independent* confirmation of USDA

    @property
    def unit(self) -> str:
        return FEDIAF_BY_ID[self.nutrient_id]["unit"]

    def with_note(self, extra: str) -> "SourceValue":
        note = f"{self.note}; {extra}" if self.note else extra
        return replace(self, note=note)

    def as_echo(self) -> "SourceValue":
        return replace(self, quality=Q_ECHO, note=(
            f"{self.note}; was {self.quality}" if self.note else f"was {self.quality}"
        ))


@dataclass
class Extraction:
    """Everything extracted for one ingredient before comparison."""

    foundation: dict[int, SourceValue] = field(default_factory=dict)
    sr: dict[int, SourceValue] = field(default_factory=dict)
    foreign: list[SourceValue] = field(default_factory=list)
    source_notes: dict[str, str] = field(default_factory=dict)  # label -> frame/caveat note
