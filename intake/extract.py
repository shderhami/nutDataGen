"""Extraction orchestration: spec -> Extraction (USDA bulk + adapters +
curated literature evidence)."""
from __future__ import annotations

from intake import usda_bulk
from intake.model import Extraction, SourceValue
from intake.sources import registry
from intake.spec import IntakeSpec
from intake.units import to_fediaf


def literature_values(spec: IntakeSpec) -> list[SourceValue]:
    """Curated book/paper evidence (plan §5), unit-converted like any adapter."""
    out: list[SourceValue] = []
    for lit in spec.literature:
        scale = to_fediaf(lit.nutrient_id, 1.0, lit.unit)
        out.append(SourceValue(
            source=lit.source,
            source_food=lit.item or lit.source,
            nutrient_id=lit.nutrient_id,
            value=lit.value * scale,
            n=lit.n,
            vmin=lit.vmin * scale if lit.vmin is not None else None,
            vmax=lit.vmax * scale if lit.vmax is not None else None,
            quality=lit.quality,
            note=lit.note,
        ))
    return out


def run(spec: IntakeSpec) -> Extraction:
    fdc_ids = [i for i in (spec.foundation_fdc_id, spec.sr_fdc_id) if i]
    usda = usda_bulk.extract_many(fdc_ids)
    extraction = Extraction(
        foundation=usda.get(spec.foundation_fdc_id, {}) if spec.foundation_fdc_id else {},
        sr=usda.get(spec.sr_fdc_id, {}) if spec.sr_fdc_id else {},
    )
    adapters = registry()
    for name, refs in spec.sources.items():
        adapter = adapters[name]
        for ref in refs:
            values = adapter.extract(ref.key, note=ref.note)
            extraction.foreign.extend(values)
            food = values[0].source_food if values else str(ref.key)
            label = f"{adapter.LABEL}:{food}"
            extraction.source_notes[label] = ref.note
    for sv in literature_values(spec):
        extraction.foreign.append(sv)
        extraction.source_notes.setdefault(
            f"{sv.source}:{sv.source_food}", sv.note)
    return extraction
