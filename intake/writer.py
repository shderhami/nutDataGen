"""Gated DB writer: reviewed decisions -> ingredients + 52 nutrient rows.

Refuses to write unless every gate passes:
- the decisions file is a REVIEWED file: it carries `reviewed_by`, it is not
  the machine-generated proposed_decisions.json, and --commit requires
  --signed-off-by (same contract as cv_assign) — a rule-engine suggestion
  must never reach the DB claiming validation that did not happen;
- the food block is valid NOW (add_ingredient's VALID_* rules + kwarg check,
  price present and nonzero, cooking_method declared) — not mid-commit after
  the backup;
- exactly the 52 FEDIAF nutrients, each with value + source + comment;
- units convertible to the FEDIAF declared unit (fail at gate, not mid-write);
- coherent stats (0 < min <= value <= max; censored min=0 ranges rejected);
- stats-carrying sources limited to foundation/sr_legacy/literature — foreign
  stats on a 'calculated' row would earn a poolable fdc_range CV and
  double-count the same dataset in cv-v8 pooling;
- PUFA total (1293) >= sum of tracked components (lamb convention).

Records go through `database.create_nutrient_record`, so FEDIAF unit
conversion and the platform stats conventions apply exactly as in the
interactive flow. AI columns stay NULL — provenance lives in the comment.
Commit path: pg_dump backup (same DB coordinates as the write, from config),
insert, verify completeness; the orphan ingredient row is removed if anything
fails after it was created, without masking the original error.

After a commit the CV pipeline still must run (Phase 3 of the runbook):
    cv_assign.py --food-id <id>            # dry-run
    cv_assign.py --food-id <id> --commit --signed-off-by "..."
"""
from __future__ import annotations

import inspect
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import config
import database
from fediaf_nutrients import fediaf_unit_factor
from intake.model import (
    FEDIAF_BY_ID,
    FEDIAF_IDS,
    PUFA_COMPONENT_IDS,
    PUFA_TOTAL_ID,
)
from intake.spec import IntakeSpec

# what the rule engine emits, plus 'calculated' for recomputed totals
# (PUFA lamb convention). Stats may ride only the first three (see gates).
_VALID_SOURCES = frozenset({"foundation", "sr_legacy", "literature", "calculated"})
_STATS_SOURCES = frozenset({"foundation", "sr_legacy", "literature"})
_PUFA_TOLERANCE = 1e-6
_PROPOSED_BASENAME = "proposed_decisions.json"
_SPECIES_CATEGORIES = frozenset({"Muscle Meat", "Organ Meat"})

# preferred pinned client (dumps any server <= 18), then PATH fallback —
# same rationale as backfill_nutrients.py
_PG_DUMP_CANDIDATES = ("/opt/homebrew/opt/postgresql@18/bin/pg_dump", "pg_dump")
_REPO_ROOT = Path(__file__).resolve().parents[1]


class GateFailure(ValueError):
    """A decisions file or spec failed a write gate."""


def load_decisions(path: str | Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    """(decisions by nutrient id, file-level metadata)."""
    path = Path(path)
    raw = json.loads(path.read_text())
    out: dict[int, dict[str, Any]] = {}
    for entry in raw["decisions"]:
        nid = int(entry["nutrient_id"])
        out[nid] = dict(entry["decision"] or {})
        out[nid]["_verdict"] = entry.get("verdict", "")
    meta = {
        "slug": raw.get("slug"),
        "reviewed_by": str(raw.get("reviewed_by", "") or "").strip(),
        "basename": path.name,
    }
    return out, meta


def _check_food_block(spec: IntakeSpec) -> list[str]:
    problems: list[str] = []
    food = spec.food
    allowed = set(inspect.signature(database.add_ingredient).parameters)
    unknown = set(food) - allowed
    if unknown:
        problems.append(f"food block: unknown add_ingredient fields {sorted(unknown)}")
    checks = (
        ("category", database.VALID_CATEGORIES, True),
        ("base_unit", database.VALID_BASE_UNITS, True),
        ("source", database.VALID_SOURCES, False),
        ("cooking_method", database.VALID_COOKING_METHODS, False),
        ("protein_species", database.VALID_PROTEIN_SPECIES, False),
    )
    for field, valid, required in checks:
        value = food.get(field)
        if value is None:
            if required:
                problems.append(f"food block: {field} missing")
            continue
        if value not in valid:
            problems.append(
                f"food block: {field} {value!r} invalid (one of {sorted(valid)})")
    if "cooking_method" not in food:
        problems.append(
            "food block: cooking_method must be declared explicitly "
            "(null = fed raw; the key documents the intent)")
    price = food.get("price_per_unit")
    if not isinstance(price, (int, float)) or price <= 0:
        problems.append(
            f"food block: price_per_unit {price!r} — a real nonzero price is "
            f"required (a 0-cost ingredient reads as free to the formulator)")
    if food.get("category") in _SPECIES_CATEGORIES and not food.get("protein_species"):
        problems.append(
            "food block: protein_species required for Muscle/Organ Meat "
            "(cv_assign pools on it)")
    return problems


def check_gates(spec: IntakeSpec, decisions: dict[int, dict[str, Any]]) -> list[str]:
    """Returns a list of gate failures (empty = all gates pass)."""
    problems = _check_food_block(spec)
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
        if d.get("unit"):
            try:
                fediaf_unit_factor(nid, d["unit"])
            except ValueError as exc:
                problems.append(f"{nid} {name}: {exc}")
        vmin, vmax = d.get("min_value"), d.get("max_value")
        if (vmin is None) != (vmax is None):
            problems.append(f"{nid} {name}: one-sided range")
        elif vmin is not None:
            if vmin <= 0:
                problems.append(
                    f"{nid} {name}: min_value {vmin} — censored/zero minimum "
                    f"ranges are not storable (bracket-guard rule)")
            elif not (vmin <= d["value"] <= vmax):
                problems.append(f"{nid} {name}: value outside [min,max]")
            if d.get("source") not in _STATS_SOURCES:
                problems.append(
                    f"{nid} {name}: stats on source {d.get('source')!r} would "
                    f"earn a poolable fdc_range CV (double-count risk) — use "
                    f"'literature' when the stats come from a citable source")
    if not missing and all(
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


def _pg_dump_binary() -> str:
    for candidate in _PG_DUMP_CANDIDATES:
        resolved = candidate if Path(candidate).exists() else shutil.which(candidate)
        if resolved:
            return resolved
    raise GateFailure("pg_dump not found — install postgresql client tools")


def _backup(slug: str) -> Path:
    """pg_dump of the SAME database the write will hit (config-driven)."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = _REPO_ROOT / "backups"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"{config.DATABASE_NAME}_pre_intake_{slug}_{stamp}.dump"
    env = dict(os.environ)
    env["PGPASSWORD"] = config.DATABASE_PASSWORD
    subprocess.run(
        [_pg_dump_binary(), "-Fc",
         "-h", config.DATABASE_HOST, "-p", str(config.DATABASE_PORT),
         "-U", config.DATABASE_USER, "-d", config.DATABASE_NAME,
         "-f", str(path)],
        check=True, env=env,
    )
    return path


def apply(spec: IntakeSpec, decisions: dict[int, dict[str, Any]],
          commit: bool = False, signed_off_by: Optional[str] = None,
          meta: Optional[dict[str, Any]] = None) -> Optional[int]:
    problems = check_gates(spec, decisions)
    if problems:
        raise GateFailure("write gates FAILED:\n  - " + "\n  - ".join(problems))
    meta = meta or {}
    reviewed_by = meta.get("reviewed_by", "")
    if meta.get("basename") == _PROPOSED_BASENAME or not reviewed_by:
        review_state = ("UNREVIEWED machine output — copy to decisions.json, "
                        "review it, and add top-level \"reviewed_by\"")
    else:
        review_state = f"reviewed by {reviewed_by}"
    preview = plan_records(spec, decisions, food_id=0)
    print(f"Gates PASS: {len(preview)} nutrient rows planned for "
          f"'{spec.food['food_name']}' ({review_state})")
    by_source: dict[str, int] = {}
    for r in preview:
        src = r.get("source") or "?"
        by_source[src] = by_source.get(src, 0) + 1
    print(f"  by source: {by_source}")
    if not commit:
        print("DRY RUN — nothing written. Use --commit --signed-off-by NAME to apply.")
        return None

    # review gates (cv_assign contract): a machine suggestion never writes
    if meta.get("basename") == _PROPOSED_BASENAME:
        raise GateFailure(
            f"refusing to commit {_PROPOSED_BASENAME} — it is the rule "
            f"engine's unreviewed output. Review it, save as decisions.json "
            f"with a top-level \"reviewed_by\", and retry.")
    if not reviewed_by:
        raise GateFailure(
            'decisions file has no top-level "reviewed_by" — the review must '
            "be recorded in the artifact itself")
    if not (signed_off_by or "").strip():
        raise GateFailure("--commit requires --signed-off-by NAME (cv_assign contract)")

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
        if not database.validate_nutrient_completeness(
                food_id, expected_count=len(FEDIAF_IDS)):
            raise RuntimeError("completeness validation failed after insert")
    except Exception:
        try:  # cleanup must never mask the original failure (main.py contract)
            database.delete_food(food_id)
        except Exception as cleanup_exc:  # noqa: BLE001
            print(f"WARNING: could not remove orphan ingredient {food_id}: "
                  f"{cleanup_exc}. Remove it manually (database.delete_food).")
        raise
    print(f"Inserted food_id {food_id} with {len(records)} nutrient rows "
          f"(reviewed by {reviewed_by}, signed off by {signed_off_by}).")
    print("Next: cv_assign.py --food-id "
          f"{food_id} (dry run, then --commit --signed-off-by), then cv_intl "
          "FOOD_MAP if FCDB stats exist (runbook Phases 3-4).")
    return food_id
