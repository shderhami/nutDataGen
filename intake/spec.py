"""Ingredient intake spec: the curated per-ingredient input file.

One JSON per ingredient under `data/intake/<slug>.json`:

    {
      "slug": "chicken_thigh_skinless",
      "food": { ... add_ingredient kwargs ... },
      "sources": {
        "fcdb":   {"key": 795, "note": "whole-bird flesh — frame caveat"},
        "mext":   {"key": "11224"},
        ...
      }
    }

`food` must carry every add_ingredient argument the DB needs;
`sources` keys must be adapter names; each entry's `note` records the frame
caveat that goes into the report verbatim (trim mismatch, cooked entry, ...).
The spec is committed to git — it IS the match documentation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from intake.sources import _MODULES

_REQUIRED_FOOD_FIELDS = ("food_name", "category", "base_unit", "portion_qty",
                         "grams_per_unit")


@dataclass
class SourceRef:
    key: Any
    note: str = ""


@dataclass
class IntakeSpec:
    slug: str
    food: dict[str, Any]
    sources: dict[str, list[SourceRef]]   # adapter name -> matched entries
    path: Path
    notes: list[str] = field(default_factory=list)

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
    return IntakeSpec(
        slug=str(raw["slug"]), food=dict(raw["food"]), sources=sources,
        path=path, notes=[str(n) for n in raw.get("notes", [])],
    )
