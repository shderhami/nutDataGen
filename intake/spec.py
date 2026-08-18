"""Ingredient intake spec: the curated per-ingredient input file.

One JSON per ingredient under `data/intake/<slug>.json`:

    {
      "slug": "chicken_thigh_skinless",
      "food": { ... add_ingredient kwargs ... },
      "sources": {
        "fcdb":   {"key": 795, "note": "whole-bird flesh — frame caveat"},
        "mext":   {"key": "11224"},
        ...
      },
      "literature": [
        {"source": "Spitze03", "item": "chicken dark meat",
         "nutrient_id": 1234, "value": 169, "unit": "mg",
         "note": "Table 1; reported mg/kg wet basis /10"}
      ]
    }

`food` must carry every add_ingredient argument the DB needs;
`sources` keys must be adapter names; each entry's `note` records the frame
caveat that goes into the report verbatim (trim mismatch, cooked entry, ...).

`literature` is the curated channel for book/paper evidence (NRC 2006,
Spitze, Seong, Donadelli, Biel — plan §5): page/table lookups with
food-matching judgment that no parser should attempt. Each entry needs
`source` (short label), `nutrient_id`, `value`, `unit`; optional `item`,
`n`, `min`, `max`, `quality` (default analysed) and `note` (cite the table).
Entries flow through the same comparison engine as adapter values.

The spec is committed to git — it IS the match documentation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from intake.model import FEDIAF_IDS, Q_ANALYSED
from intake.sources import _MODULES

_REQUIRED_FOOD_FIELDS = ("food_name", "category", "base_unit", "portion_qty",
                         "grams_per_unit")
_REQUIRED_LIT_FIELDS = ("source", "nutrient_id", "value", "unit")


@dataclass
class SourceRef:
    key: Any
    note: str = ""


@dataclass
class LiteratureValue:
    source: str                 # short label, e.g. "NRC2006", "Spitze03"
    nutrient_id: int
    value: float
    unit: str                   # as published; converted at extraction
    item: str = ""              # the book/paper's own food description
    n: Optional[int] = None
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    quality: str = Q_ANALYSED
    note: str = ""


@dataclass
class IntakeSpec:
    slug: str
    food: dict[str, Any]
    sources: dict[str, list[SourceRef]]   # adapter name -> matched entries
    path: Path
    notes: list[str] = field(default_factory=list)
    literature: list[LiteratureValue] = field(default_factory=list)

    @property
    def out_dir(self) -> Path:
        return self.path.parent / self.slug

    @property
    def sr_fdc_id(self):
        return self.food.get("sr_legacy_fdc_id")

    @property
    def foundation_fdc_id(self):
        return self.food.get("foundation_fdc_id")


def load_spec(path: str | Path) -> IntakeSpec:
    path = Path(path)
    raw = json.loads(path.read_text())
    for key in ("slug", "food", "sources"):
        if key not in raw:
            raise ValueError(f"spec {path}: missing top-level '{key}'")
    missing = [f for f in _REQUIRED_FOOD_FIELDS if f not in raw["food"]]
    if missing:
        raise ValueError(f"spec {path}: food block missing {missing}")
    if not raw["food"].get("sr_legacy_fdc_id") and not raw["food"].get("foundation_fdc_id"):
        raise ValueError(f"spec {path}: need at least one of sr_legacy_fdc_id/foundation_fdc_id")
    sources: dict[str, list[SourceRef]] = {}
    for name, entry in raw["sources"].items():
        if name not in _MODULES:
            raise ValueError(f"spec {path}: unknown source '{name}' (know: {_MODULES})")
        entries = entry if isinstance(entry, list) else [entry]
        refs = []
        for e in entries:
            if isinstance(e, dict):
                refs.append(SourceRef(key=e["key"], note=str(e.get("note", ""))))
            else:
                refs.append(SourceRef(key=e))
        sources[name] = refs
    literature: list[LiteratureValue] = []
    for i, entry in enumerate(raw.get("literature", [])):
        missing_lit = [f for f in _REQUIRED_LIT_FIELDS if f not in entry]
        if missing_lit:
            raise ValueError(f"spec {path}: literature[{i}] missing {missing_lit}")
        nid = int(entry["nutrient_id"])
        if nid not in FEDIAF_IDS:
            raise ValueError(f"spec {path}: literature[{i}] unknown nutrient_id {nid}")
        literature.append(LiteratureValue(
            source=str(entry["source"]), nutrient_id=nid,
            value=float(entry["value"]), unit=str(entry["unit"]),
            item=str(entry.get("item", "")),
            n=int(entry["n"]) if entry.get("n") is not None else None,
            vmin=float(entry["min"]) if entry.get("min") is not None else None,
            vmax=float(entry["max"]) if entry.get("max") is not None else None,
            quality=str(entry.get("quality", Q_ANALYSED)),
            note=str(entry.get("note", "")),
        ))
    return IntakeSpec(
        slug=str(raw["slug"]), food=dict(raw["food"]), sources=sources,
        path=path, notes=[str(n) for n in raw.get("notes", [])],
        literature=literature,
    )
