"""Per-source adapters. Each module exposes:

    LABEL: str                       — short source tag used everywhere
    extract(key, note="") -> list[SourceValue]
    search(query) -> list[tuple[key, description]]

Contract: extract() raises KeyError for an unknown key (never returns [] for
one — extract.run treats an empty result as a spec error); every value leaves
the adapter in its FEDIAF unit with quality/form tags set. A USDA-affiliated
source declares `USDA_LINEAGE = True` at module level — extract.run stamps
every row centrally so the source can never count as independent
confirmation of USDA (see iodine_db).
"""
from __future__ import annotations

from importlib import import_module

# spec-key -> module name; also the reporting order.
_MODULES = ("fcdb", "bls", "mext", "ciqual", "afcd", "cofid", "iodine_db")


def registry() -> dict[str, object]:
    """{spec key: adapter module}, imported on first use."""
    return {name: import_module(f"intake.sources.{name}") for name in _MODULES}
