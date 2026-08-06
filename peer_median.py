"""
Peer medians from the local USDA bulk datasets.

The one evidence source fully under our control and impossible for a model to
fabricate: for a nutrient in a food, what do *comparable* USDA foods actually
report? This is the cross-check that was previously done by hand after the
fact — computing it up front lets the validator reason over supplied evidence
instead of recalling numbers.

Cohort selection is deliberately conservative: same protein species, same
cooked/raw state, and only rows USDA actually measured (data_points > 0). A
cohort assembled from placeholder zeros would manufacture the very artifact
this is meant to catch.

Caveats the caller must keep in mind (plan 3.2):
  - Peer cohorts carry provenance bias (e.g. lamb peers skew NZ-imported).
    `sample_size` and `source` are returned so a thin or skewed cohort is
    visible rather than implied.
  - Measured biological CV in a tight lamb cohort is 8-26%, which bounds the
    precision any peer median can claim.

Datasets are gitignored; every entry point degrades to None when they are
absent rather than raising.
"""
from __future__ import annotations

import csv
import re
import statistics
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Optional

import cv_config

# Cooked/raw state must match: cooking concentrates nutrients per 100 g, so a
# raw food's peer median must not be drawn from cooked peers.
_COOKED_MARKERS = (
    "cooked", "roasted", "braised", "broiled", "grilled", "baked",
    "boiled", "fried", "steamed", "stewed",
)
_RAW_MARKERS = ("raw",)

# Cohort must be big enough that a median means something.
MIN_COHORT_SIZE = 3


@dataclass(frozen=True)
class PeerMedian:
    """A peer-derived reference value for one nutrient."""
    nutrient_id: int
    median: float
    minimum: float
    maximum: float
    sample_size: int
    state: str          # "cooked" | "raw" | "any"
    species: str
    source: str         # which dataset the cohort came from


def _state_of(description: str) -> str:
    """Classify a USDA food description as cooked, raw, or unknown."""
    text = description.lower()
    if any(marker in text for marker in _COOKED_MARKERS):
        return "cooked"
    if any(marker in text for marker in _RAW_MARKERS):
        return "raw"
    return "unknown"


def _dataset_dirs() -> list[tuple[str, Path]]:
    """Pinned bulk dataset directories that are actually present on disk."""
    candidates = [
        ("FDC-SRL", cv_config.FDC_SRL_DIR),
        ("FDC-FDN", cv_config.FDC_FDN_DIR),
    ]
    return [
        (label, path) for label, path in candidates
        if (path / "food.csv").exists() and (path / "food_nutrient.csv").exists()
    ]


@lru_cache(maxsize=4)
def _load_foods(dataset_dir: str) -> tuple[tuple[int, str, str], ...]:
    """(fdc_id, description, state) for every food in a dataset."""
    path = Path(dataset_dir) / "food.csv"
    out = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                fdc_id = int(row["fdc_id"])
            except (KeyError, TypeError, ValueError):
                continue
            description = (row.get("description") or "").strip()
            out.append((fdc_id, description, _state_of(description)))
    return tuple(out)


def _matching_fdc_ids(
    dataset_dir: Path, species: str, state: str
) -> tuple[set[int], str]:
    """
    FDC IDs of foods matching the species (and state, when known).

    Returns (ids, effective_state) — the state actually used, which falls back
    to "any" when a state-matched cohort would be too thin to be meaningful.
    """
    species_pattern = re.compile(rf"\b{re.escape(species.lower())}\b")
    species_matches = [
        (fdc_id, food_state)
        for fdc_id, description, food_state in _load_foods(str(dataset_dir))
        if species_pattern.search(description.lower())
    ]
    if state in ("cooked", "raw"):
        state_matched = {fid for fid, s in species_matches if s == state}
        if len(state_matched) >= MIN_COHORT_SIZE:
            return state_matched, state
    return {fid for fid, _ in species_matches}, "any"


def _measured_amounts_by_nutrient(
    dataset_dir: Path, fdc_ids: frozenset[int]
) -> dict[int, list[float]]:
    """
    Amounts per nutrient across a cohort, measured rows only, in ONE file scan.

    food_nutrient.csv is 35 MB; scanning it once per nutrient would cost ~35 s
    per ingredient, so the whole cohort is collected in a single pass.

    Rows with no data points are USDA placeholders, not measurements —
    including them would pull a peer median toward zero for exactly the
    nutrients this check exists to scrutinise.
    """
    out: dict[int, list[float]] = {}
    with open(dataset_dir / "food_nutrient.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                if int(row["fdc_id"]) not in fdc_ids:
                    continue
                data_points = (row.get("data_points") or "").strip()
                if not data_points or int(data_points) <= 0:
                    continue
                out.setdefault(int(row["nutrient_id"]), []).append(float(row["amount"]))
            except (KeyError, TypeError, ValueError):
                continue
    return out


@lru_cache(maxsize=8)
def _cohort_amounts(
    dataset_dir: str, fdc_ids: frozenset[int]
) -> dict[int, list[float]]:
    """Cached single-scan cohort amounts (one entry per food processed)."""
    return _measured_amounts_by_nutrient(Path(dataset_dir), fdc_ids)


def compute_peer_medians(
    nutrient_ids: list[int],
    species: Optional[str],
    cooking_method: Optional[str] = None,
) -> dict[int, PeerMedian]:
    """
    Peer medians for many nutrients at once — one dataset scan per cohort.

    Args:
        nutrient_ids: USDA nutrient IDs to compute medians for.
        species: Protein species to match (e.g. "lamb"). Required — without it
            there is no defensible cohort.
        cooking_method: Free text; classified to cooked/raw when recognisable.

    Returns:
        {nutrient_id: PeerMedian} for those nutrients with a usable cohort.
        Empty when the datasets are absent or the species is unknown.
    """
    if not species or not nutrient_ids:
        return {}

    state = _state_of(cooking_method or "")
    wanted = set(nutrient_ids)

    for label, dataset_dir in _dataset_dirs():
        fdc_ids, effective_state = _matching_fdc_ids(dataset_dir, species, state)
        if not fdc_ids:
            continue
        amounts_by_nutrient = _cohort_amounts(str(dataset_dir), frozenset(fdc_ids))
        results: dict[int, PeerMedian] = {}
        for nutrient_id in wanted:
            amounts = amounts_by_nutrient.get(nutrient_id, [])
            if len(amounts) < MIN_COHORT_SIZE:
                continue
            results[nutrient_id] = PeerMedian(
                nutrient_id=nutrient_id,
                median=round(statistics.median(amounts), 6),
                minimum=round(min(amounts), 6),
                maximum=round(max(amounts), 6),
                sample_size=len(amounts),
                state=effective_state,
                species=species,
                source=label,
            )
        if results:
            return results
    return {}


def compute_peer_median(
    nutrient_id: int,
    species: Optional[str],
    cooking_method: Optional[str] = None,
) -> Optional[PeerMedian]:
    """Single-nutrient convenience wrapper around compute_peer_medians."""
    return compute_peer_medians([nutrient_id], species, cooking_method).get(nutrient_id)


def format_peer_median(peer: Optional[PeerMedian]) -> str:
    """
    Render a peer median as a prompt block, or "" when unavailable.

    The cohort description is part of the evidence: a median over 4 "any-state"
    foods deserves less weight than one over 30 state-matched foods, and the
    model can only weigh that if it is told.
    """
    if peer is None:
        return ""
    state = "cooked or raw" if peer.state == "any" else peer.state
    return (
        f"\nLOCAL USDA PEER COHORT (measured rows only, data_points > 0):\n"
        f"- Cohort: {peer.sample_size} {peer.species} foods ({state}) from {peer.source}\n"
        f"- Peer median: {peer.median} (range {peer.minimum} to {peer.maximum})\n"
        f"- This cohort is computed from USDA bulk data, not recalled. Peer "
        f"cohorts carry provenance bias and biological variation of roughly "
        f"8-26%, so treat it as a plausibility check, not ground truth.\n"
    )
