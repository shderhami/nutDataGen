"""Gated DB writer: reviewed decisions -> ingredients + 52 nutrient rows.

Refuses to write unless every gate passes:
- exactly the 52 FEDIAF nutrients, each with a value, source and comment;
- coherent stats (min <= value <= max when a range is given);
- PUFA total (1293) >= sum of tracked components (lamb convention);
- valid `source` labels.

Records go through `database.create_nutrient_record`, so FEDIAF unit
conversion and the platform stats conventions apply exactly as in the
interactive flow. AI columns stay NULL — provenance lives in the comment.
Commit path: pg_dump backup first, insert, verify completeness; the orphan
ingredient row is removed if anything fails after it was created.

After a commit the CV pipeline still must run (Phase 3 of the runbook):
    cv_assign.py --food-id <id>            # dry-run
    cv_assign.py --food-id <id> --commit --signed-off-by "..."
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import database
from intake.model import (
    FEDIAF_BY_ID,
    FEDIAF_IDS,
    PUFA_COMPONENT_IDS,
    PUFA_TOTAL_ID,
)
from intake.spec import IntakeSpec

_VALID_SOURCES = frozenset({
    "foundation", "sr_legacy", "literature", "calculated", "stoichiometric",
    "manual",
})
_PUFA_TOLERANCE = 1e-6


class GateFailure(ValueError):
    """A decisions file failed a write gate."""


def load_decisions(path: str | Path) -> dict[int, dict[str, Any]]:
    raw = json.loads(Path(path).read_text())
    out: dict[int, dict[str, Any]] = {}
    for entry in raw["decisions"]:
        nid = int(entry["nutrient_id"])
        out[nid] = dict(entry["decision"] or {})
        out[nid]["_verdict"] = entry.get("verdict", "")
    return out


def check_gates(spec: IntakeSpec, decisions: dict[int, dict[str, Any]]) -> list[str]:
    """Returns a list of gate failures (empty = all gates pass)."""
    problems: list[str] = []
    ids = set(decisions)
    missing, extra = FEDIAF_IDS - ids, ids - FEDIAF_IDS
    if missing:
        problems.append(f"missing nutrients: {sorted(missing)}")
    if extra:
        problems.append(f"unknown nutrient ids: {sorted(extra)}")
    for nid in sorted(ids & FEDIAF_IDS):
        d = decisions[nid]
        name = FEDIAF_BY_ID[nid]["nutrient_name"]
        if d.get("value") is None:
            problems.append(f"{nid} {name}: no value (unresolved decision)")
            continue
        if not d.get("source") or d["source"] not in _VALID_SOURCES:
            problems.append(f"{nid} {name}: source {d.get('source')!r} invalid")
        if not d.get("comment"):
            problems.append(f"{nid} {name}: empty comment (provenance required)")
        vmin, vmax = d.get("min_value"), d.get("max_value")
        if (vmin is None) != (vmax is None):
            problems.append(f"{nid} {name}: one-sided range")
        elif vmin is not None and not (vmin <= d["value"] <= vmax):
            problems.append(f"{nid} {name}: value outside [min,max]")
    if not (FEDIAF_IDS - ids) and all(
            decisions[n].get("value") is not None for n in PUFA_COMPONENT_IDS + (PUFA_TOTAL_ID,)):
        total = decisions[PUFA_TOTAL_ID]["value"]
        component_sum = sum(decisions[n]["value"] for n in PUFA_COMPONENT_IDS)
        if total + _PUFA_TOLERANCE < component_sum:
            problems.append(
                f"PUFA invariant: total {total} < component sum {component_sum:.6g} "
                f"(recompute per lamb convention)")
    return problems


def plan_records(spec: IntakeSpec, decisions: dict[int, dict[str, Any]],
                 food_id: int) -> list[database.NutrientRecord]:
    records = []
    for nid, d in sorted(decisions.items()):
        info = FEDIAF_BY_ID[nid]
        records.append(database.create_nutrient_record(
            food_name=spec.food["food_name"],
            food_id=food_id,
            nutrient_id=nid,
            fediaf_nutrient_name=info["nutrient_name"],
            usda_nutrient_name=info["usda_name"],
            unit=d.get("unit") or info["unit"],
            value=float(d["value"]),
            source=d["source"],
            comment=d["comment"],
            num_samples=d.get("num_samples"),
            min_value=d.get("min_value"),
            max_value=d.get("max_value"),
            median_value=d.get("median_value"),
            year_acquired=d.get("year_acquired"),
            derivation_description=d.get("derivation_description"),
        ))
    return records


def _backup(slug: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path("backups") / f"cat_food_formulator_pre_intake_{slug}_{stamp}.dump"
    path.parent.mkdir(exist_ok=True)
    subprocess.run(
        ["pg_dump", "-Fc", "-h", "localhost", "-U", "postgres",
         "-d", "cat_food_formulator", "-f", str(path)],
        check=True, env={"PGPASSWORD": "postgres", "PATH": "/opt/homebrew/bin:/usr/bin:/bin"},
    )
    return path


def apply(spec: IntakeSpec, decisions: dict[int, dict[str, Any]],
          commit: bool = False) -> Optional[int]:
    problems = check_gates(spec, decisions)
    if problems:
        raise GateFailure("write gates FAILED:\n  - " + "\n  - ".join(problems))
    preview = plan_records(spec, decisions, food_id=0)
    print(f"Gates PASS: {len(preview)} nutrient rows planned for "
          f"'{spec.food['food_name']}'")
    by_source: dict[str, int] = {}
    for r in preview:
        src = r.get("source") or "?"
        by_source[src] = by_source.get(src, 0) + 1
    print(f"  by source: {by_source}")
    if not commit:
        print("DRY RUN — nothing written. Use --commit to apply.")
        return None

    existing = database.food_exists_by_name(spec.food["food_name"])
    if existing is not None:
        raise GateFailure(
            f"ingredient '{spec.food['food_name']}' already exists (food_id {existing})")
    backup = _backup(spec.slug)
    print(f"Backup: {backup}")
    food_id = database.add_ingredient(**spec.food)
    try:
        records = plan_records(spec, decisions, food_id=food_id)
        database.add_food_nutrients(records)
        if not database.validate_nutrient_completeness(food_id):
            raise RuntimeError("completeness validation failed after insert")
    except Exception:
        database.delete_food(food_id)
        raise
    print(f"Inserted food_id {food_id} with {len(records)} nutrient rows.")
    print("Next: cv_assign.py --food-id "
          f"{food_id} (dry run, then --commit --signed-off-by), then cv_intl "
          "FOOD_MAP if FCDB stats exist (runbook Phases 3-4).")
    return food_id
