"""Extraction orchestration: spec -> Extraction (USDA bulk + adapters +
curated literature evidence)."""
from __future__ import annotations

from dataclasses import replace

from intake import usda_bulk
from intake.model import Extraction, SourceValue
from intake.sources import registry
from intake.spec import IntakeSpec


def literature_values(spec: IntakeSpec) -> list[SourceValue]:
    """Curated book/paper evidence (plan §5), unit-converted like any adapter."""
    return [lit.to_source_value() for lit in spec.literature]


def run(spec: IntakeSpec) -> Extraction:
    fdc_ids = [i for i in (spec.foundation_fdc_id, spec.sr_fdc_id) if i]
    usda = usda_bulk.extract_many(fdc_ids)
    extraction = Extraction(
        foundation=usda.get(spec.foundation_fdc_id, {}) if spec.foundation_fdc_id else {},
        sr=usda.get(spec.sr_fdc_id, {}) if spec.sr_fdc_id else {},
    )
    # a spec-declared USDA id that yields nothing is a spec error, not an
    # empty table (audit 2026-08-18: a typo silently flipped ~45 verdicts)
    for label, fdc_id, table in (("foundation", spec.foundation_fdc_id, extraction.foundation),
                                 ("sr_legacy", spec.sr_fdc_id, extraction.sr)):
        if fdc_id and not table:
            raise KeyError(
                f"spec {label}_fdc_id {fdc_id} matched no rows in the pinned "
                f"USDA bulk files — wrong id?")
    adapters = registry()
    for name, refs in spec.sources.items():
        adapter = adapters[name]
        # source-level lineage declaration (adapter module attribute) is
        # applied centrally so a new USDA-affiliated adapter cannot forget
        # the per-row flag on some branch (audit 2026-08-18)
        adapter_lineage = bool(getattr(adapter, "USDA_LINEAGE", False))
        for ref in refs:
            values = adapter.extract(ref.key, note=ref.note)
            if not values:
                # curated key resolved to a food but produced zero mapped
                # values — silently dropping the source would falsify the
                # spec's match documentation
                raise KeyError(
                    f"{adapter.LABEL} key {ref.key!r} produced no values — "
                    f"check the spec entry")
            if adapter_lineage:
                values = [sv if sv.usda_lineage else replace(sv, usda_lineage=True)
                          for sv in values]
            extraction.foreign.extend(values)
            label = f"{adapter.LABEL}:{values[0].source_food}"
            extraction.source_notes[label] = ref.note
    for sv in literature_values(spec):
        extraction.foreign.append(sv)
        extraction.source_notes.setdefault(
            f"{sv.source}:{sv.source_food}", sv.note)
    return extraction
