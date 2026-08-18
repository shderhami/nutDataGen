"""Gated DB writer: reviewed decisions -> ingredients + 52 nutrient rows.

Two gate classes:

RECORD GATES (fail dry-run and commit — the plan itself is wrong):
- decisions slug present AND equal to the spec slug (fail-closed: an absent
  slug must never disable the cross-wire gate); duplicate nutrient_id
  entries are refused at load (shadowing);
- exactly the 52 FEDIAF nutrients, each with a FINITE, non-negative numeric
  value + source + comment (json.loads accepts NaN/Infinity — rejected);
- units convertible to the FEDIAF declared unit (entry-level `unit` edits are
  honored — see load_decisions);
- coherent stats (0 < min <= value <= max, min strictly < max — zero-width
  ranges earn falsely tight CVs; median inside the range; censored min=0
  rejected); stats-carrying sources limited to
  foundation/sr_legacy/literature (cv-v8 double-count guard);
- PUFA total (1293) >= sum of tracked components (lamb convention);
- contested status (verdicts + split tie-breaks) is taken from the sibling
  machine artifact when present, so editing the reviewed copy's verdict
  strings cannot skip the resolution requirement.

COMMIT GATES (dry-run prints them as blockers and still previews):
- food block valid per database.ingredient_field_problems (the same rules
  add_ingredient enforces — shared code, cannot drift) plus intake policy:
  known kwargs only, real nonzero price, cooking_method declared,
  protein_species for meat categories, supplements out of scope (plan §2);
- REVIEW CONTRACT: refuses the machine artifact (by its shared basename
  constant AND by its `review_contract` content marker), requires a top-level
  `reviewed_by`, `--signed-off-by` (cv_assign contract), and an operator
  `resolution` sentence on every contested-verdict row.

Commit path: pg_dump backup of the configured DB, insert, completeness check,
orphan cleanup that never masks the original failure, and a committed
`write_receipt.json` recording food_id / reviewer / signer / backup — the
durable trace of who approved the rows.
"""
from __future__ import annotations

import inspect
import json
import math
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
from intake.report import CONTESTED_VERDICTS, PROPOSED_DECISIONS_BASENAME
from intake.spec import IntakeSpec

# what the rule engine emits, plus 'calculated' for recomputed totals
# (PUFA lamb convention). Stats may ride only the first three (see gates).
_VALID_SOURCES = frozenset({"foundation", "sr_legacy", "literature", "calculated"})
_STATS_SOURCES = frozenset({"foundation", "sr_legacy", "literature"})
_PUFA_TOLERANCE = 1e-6
_SPECIES_CATEGORIES = frozenset({"Muscle Meat", "Organ Meat"})

# preferred pinned client (dumps any server <= 18), then PATH fallback —
# same rationale as backfill_nutrients.py
_PG_DUMP_CANDIDATES = ("/opt/homebrew/opt/postgresql@18/bin/pg_dump", "pg_dump")
_REPO_ROOT = Path(__file__).resolve().parents[1]


class GateFailure(ValueError):
    """A decisions file or spec failed a write gate."""


def load_decisions(path: str | Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    """(decisions by nutrient id, file-level metadata).

    The entry-level `unit` (what the artifact displays to the reviewer) is
    folded into the decision when the decision has none, so a reviewed unit
    edit takes effect instead of being silently discarded (audit 2026-08-18).
    """
    path = Path(path)
    raw = json.loads(path.read_text())
    out: dict[int, dict[str, Any]] = {}
    duplicates: list[int] = []
    for entry in raw["decisions"]:
        nid = int(entry["nutrient_id"])
        if nid in out:
            # last-wins shadowing would let a second entry below the fold
            # silently replace the reviewed one (round-3 fuzzing)
            duplicates.append(nid)
            continue
        decision = dict(entry["decision"] or {})
        if entry.get("unit") and not decision.get("unit"):
            decision["unit"] = entry["unit"]
        decision["_verdict"] = entry.get("verdict", "")
        # a split-source tie-break needs arbitration regardless of verdict
        # (e.g. an adopt_foreign anchored between 169 and 33.7)
        decision["_tie_break"] = any(
            "tie-break between split sources" in str(r)
            for r in entry.get("reasons", []))
        out[nid] = decision
    if duplicates:
        raise GateFailure(
            f"decisions file contains duplicate nutrient_id entries "
            f"{sorted(set(duplicates))} — a shadowed entry cannot be reviewed")
    meta = {
        "slug": raw.get("slug"),
        "reviewed_by": str(raw.get("reviewed_by", "") or "").strip(),
        "basename": path.name,
        "has_review_contract": "review_contract" in raw,
    }
    _restore_machine_verdicts(path, raw, out)
    return out, meta


def _restore_machine_verdicts(path: Path, raw: dict,
                              decisions: dict[int, dict[str, Any]]) -> None:
    """Contested status comes from the MACHINE artifact when it is present.

    The reviewed file's own verdict strings are self-attested — editing
    'review' to 'confirm' (or dropping the reasons array) would silently
    skip the resolution requirement (round-3 fuzzing). When the sibling
    proposed_decisions.json exists for the same slug, its verdicts and
    tie-break reasons override the reviewed copy's for gating purposes.
    """
    if path.name == PROPOSED_DECISIONS_BASENAME:
        return
    machine_path = path.parent / PROPOSED_DECISIONS_BASENAME
    if not machine_path.exists():
        return
    try:
        machine = json.loads(machine_path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    if machine.get("slug") != raw.get("slug"):
        return
    for entry in machine.get("decisions", []):
        nid = int(entry["nutrient_id"])
        if nid not in decisions:
            continue
        decisions[nid]["_verdict"] = entry.get("verdict", "")
        decisions[nid]["_tie_break"] = any(
            "tie-break between split sources" in str(r)
            for r in entry.get("reasons", []))


def _check_food_block(spec: IntakeSpec) -> list[str]:
    """Commit blockers from the food block (shared DB rules + intake policy)."""
    problems: list[str] = []
    food = spec.food
    allowed = set(inspect.signature(database.add_ingredient).parameters)
    unknown = set(food) - allowed
    if unknown:
        problems.append(f"food block: unknown add_ingredient fields {sorted(unknown)}")
    # the exact rules add_ingredient will enforce, checked NOW (shared code)
    problems += [f"food block: {p}" for p in database.ingredient_field_problems(
        category=food.get("category", ""),
        base_unit=food.get("base_unit", ""),
        cooking_method=food.get("cooking_method"),
        source=food.get("source", "grocery"),
        protein_species=food.get("protein_species"),
        supplement_info=food.get("supplement_info"),
        is_corrector=bool(food.get("is_corrector", False)),
    )]
    # intake policy on top
    if food.get("category") == "Supplement":
        problems.append(
            "food block: supplements are out of intake scope (plan §2 "
            "non-goal) — use the interactive Path B flow")
    if "cooking_method" not in food:
        problems.append(
            "food block: cooking_method must be declared explicitly "
            "(null = fed raw; the key documents the intent)")
    price = food.get("price_per_unit")
    if not _numeric(price) or price <= 0:
        problems.append(
            f"food block: price_per_unit {price!r} — a real nonzero price is "
            f"required (a 0-cost ingredient reads as free to the formulator)")
    for mass_field in ("portion_qty", "grams_per_unit"):
        mass = food.get(mass_field)
        if not _numeric(mass) or mass <= 0:
            problems.append(
                f"food block: {mass_field} {mass!r} must be a positive number "
                f"(zero would divide-by-zero the per-gram nutrient math)")
    if food.get("category") in _SPECIES_CATEGORIES and not food.get("protein_species"):
        problems.append(
            "food block: protein_species required for Muscle/Organ Meat "
            "(cv_assign pools on it)")
    return problems


def _numeric(value: Any) -> bool:
    # json.loads accepts bare NaN/Infinity — non-finite values pass every
    # comparison gate and PostgreSQL numeric stores them (round-3 fuzzing)
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def check_gates(spec: IntakeSpec, decisions: dict[int, dict[str, Any]],
                meta: Optional[dict[str, Any]] = None) -> tuple[list[str], list[str]]:
    """(record problems, commit blockers). Record problems invalidate even a
    dry-run preview; commit blockers only stop --commit."""
    problems: list[str] = []
    commit_problems = _check_food_block(spec)
    meta = meta or {}
    if meta:
        # fail CLOSED: the slug is the only binding between a decisions file
        # and a spec — an absent/empty slug disabled the gate (round-3 fuzzing)
        if not meta.get("slug"):
            problems.append(
                "decisions file has no top-level 'slug' — required to bind "
                "it to the spec (fail-closed cross-wire gate)")
        elif meta["slug"] != spec.slug:
            problems.append(
                f"decisions file is for slug '{meta['slug']}' but the spec is "
                f"'{spec.slug}' — refusing to cross-wire foods")
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
        bad_types = [f for f in ("value", "min_value", "max_value", "median_value")
                     if d.get(f) is not None and not _numeric(d[f])]
        if bad_types:
            problems.append(f"{nid} {name}: non-numeric/non-finite {bad_types} "
                            f"(hand-edit left a string, NaN or Infinity?)")
            continue
        if d["value"] < 0:
            problems.append(f"{nid} {name}: negative value {d['value']} — "
                            f"nutrient concentrations are non-negative")
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
            elif vmin >= vmax:
                problems.append(
                    f"{nid} {name}: degenerate range [{vmin}, {vmax}] — a "
                    f"zero-width range would earn a falsely tight CV")
            elif not (vmin <= d["value"] <= vmax):
                problems.append(f"{nid} {name}: value outside [min,max]")
            elif d.get("median_value") is not None and not (vmin <= d["median_value"] <= vmax):
                problems.append(f"{nid} {name}: median outside [min,max]")
            if d.get("source") not in _STATS_SOURCES:
                problems.append(
                    f"{nid} {name}: stats on source {d.get('source')!r} would "
                    f"earn a poolable fdc_range CV (double-count risk) — use "
                    f"'literature' when the stats come from a citable source")
        elif d.get("median_value") is not None:
            problems.append(f"{nid} {name}: median_value without a min/max range")
        contested = (d.get("_verdict") in CONTESTED_VERDICTS
                     or d.get("_tie_break"))
        if contested and not str(d.get("resolution", "") or "").strip():
            label = (f"verdict '{d['_verdict']}'" if d.get("_verdict") in CONTESTED_VERDICTS
                     else "split-source tie-break")
            commit_problems.append(
                f"{nid} {name}: {label} needs an operator 'resolution' "
                f"sentence in the decision before commit")
    if not missing and all(
            _numeric(decisions[n].get("value"))
            for n in PUFA_COMPONENT_IDS + (PUFA_TOTAL_ID,)):
        total = decisions[PUFA_TOTAL_ID]["value"]
        component_sum = sum(decisions[n]["value"] for n in PUFA_COMPONENT_IDS)
        if total + _PUFA_TOLERANCE < component_sum:
            problems.append(
                f"PUFA invariant: total {total} < component sum {component_sum:.6g} "
                f"(recompute per lamb convention)")
    return problems, commit_problems


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


def _review_refusal(meta: dict[str, Any], signed_off_by: Optional[str]) -> Optional[str]:
    """The commit-time review contract, in one place."""
    if meta.get("basename") == PROPOSED_DECISIONS_BASENAME:
        return (f"refusing to commit {PROPOSED_DECISIONS_BASENAME} — it is the "
                f"rule engine's unreviewed output. Review it, save as "
                f"decisions.json with a top-level \"reviewed_by\", and retry.")
    if meta.get("has_review_contract"):
        return ("decisions file still carries the machine 'review_contract' "
                "marker — reviewing includes removing it (renaming the file "
                "is not a review)")
    if not meta.get("reviewed_by"):
        return ('decisions file has no top-level "reviewed_by" — the review '
                "must be recorded in the artifact itself")
    if not (signed_off_by or "").strip():
        return "--commit requires --signed-off-by NAME (cv_assign contract)"
    return None


def _write_receipt(spec: IntakeSpec, food_id: int, reviewed_by: str,
                   signed_off_by: str, backup: Path,
                   decisions_basename: str) -> Path:
    """Durable, committed record of who approved the write (the sign-off
    otherwise exists only in terminal scrollback)."""
    receipt = {
        "slug": spec.slug, "food_id": food_id,
        "written_at": datetime.now().isoformat(timespec="seconds"),
        "reviewed_by": reviewed_by, "signed_off_by": signed_off_by,
        "decisions_file": decisions_basename, "backup": str(backup),
    }
    path = spec.out_dir / "write_receipt.json"
    path.write_text(json.dumps(receipt, indent=2))
    return path


def apply(spec: IntakeSpec, decisions: dict[int, dict[str, Any]],
          commit: bool = False, signed_off_by: Optional[str] = None,
          meta: Optional[dict[str, Any]] = None) -> Optional[int]:
    meta = meta or {}
    problems, commit_problems = check_gates(spec, decisions, meta)
    if problems:
        raise GateFailure("write gates FAILED:\n  - " + "\n  - ".join(problems))
    if commit and commit_problems:
        raise GateFailure("commit blockers:\n  - " + "\n  - ".join(commit_problems))
    refusal = _review_refusal(meta, signed_off_by)
    if commit and refusal:
        raise GateFailure(refusal)

    preview = plan_records(spec, decisions, food_id=0)
    reviewed = (meta.get("reviewed_by")
                and meta.get("basename") != PROPOSED_DECISIONS_BASENAME
                and not meta.get("has_review_contract"))
    review_state = (f"reviewed by {meta['reviewed_by']}" if reviewed
                    else "UNREVIEWED machine output — review before commit")
    print(f"Gates PASS: {len(preview)} nutrient rows planned for "
          f"'{spec.food['food_name']}' ({review_state})")
    by_source: dict[str, int] = {}
    for r in preview:
        src = r.get("source") or "?"
        by_source[src] = by_source.get(src, 0) + 1
    print(f"  by source: {by_source}")
    if not commit:
        for blocker in commit_problems:
            print(f"  COMMIT BLOCKER: {blocker}")
        print("DRY RUN — nothing written. Use --commit --signed-off-by NAME to apply.")
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
        if not database.validate_nutrient_completeness(
                food_id, expected_count=len(FEDIAF_IDS)):
            raise RuntimeError("completeness validation failed after insert")
    except Exception:
        try:  # cleanup must never mask the original failure (main.py contract)
            database.delete_food(food_id)
            print(f"Removed orphan ingredient {food_id} after the failure "
                  f"below — the DB is clean.")
        except Exception as cleanup_exc:  # noqa: BLE001
            print(f"WARNING: could not remove orphan ingredient {food_id}: "
                  f"{cleanup_exc}. Remove it manually (database.delete_food).")
        raise
    receipt = _write_receipt(spec, food_id, meta["reviewed_by"],
                             str(signed_off_by), backup,
                             meta.get("basename", "?"))
    print(f"Inserted food_id {food_id} with {len(records)} nutrient rows "
          f"(reviewed by {meta['reviewed_by']}, signed off by {signed_off_by}).")
    print(f"Receipt: {receipt} — commit it with the decisions file.")
    print("Next: cv_assign.py --food-id "
          f"{food_id} (dry run, then --commit --signed-off-by), then cv_intl "
          "FOOD_MAP if FCDB stats exist (runbook Phases 3-4).")
    return food_id
