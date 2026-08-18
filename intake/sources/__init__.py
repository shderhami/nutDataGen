"""Per-source adapters. Each module exposes:

    LABEL: str                       — short source tag used everywhere
    extract(key, note="") -> list[SourceValue]
    search(query) -> list[tuple[key, description]]

Adapters do all parsing-quirk handling and unit conversion; what leaves an
adapter is directly comparable to (and storable as) a DB row.
"""
from __future__ import annotations

from importlib import import_module

# spec-key -> module name; also the reporting order.
_MODULES = ("fcdb", "bls", "mext", "ciqual", "afcd", "cofid", "iodine_db")


def registry() -> dict[str, object]:
    """{spec key: adapter module}, imported on first use."""
    return {name: import_module(f"intake.sources.{name}") for name in _MODULES}
