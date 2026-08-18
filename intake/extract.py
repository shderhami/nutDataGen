"""Extraction orchestration: spec -> Extraction (USDA bulk + all adapters)."""
from __future__ import annotations

from intake import usda_bulk
from intake.model import Extraction
from intake.sources import registry
from intake.spec import IntakeSpec


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
    return extraction
