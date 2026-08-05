"""Automatic per-ingredient CV assignment for freshly-saved ingredients.

Wraps cv_assign's gated incremental path so the interactive add flow can give a new
ingredient its CVs immediately, instead of leaving them NULL until a manual
`cv_assign.py --food-id N --commit` run (NULL -> the consumer falls back to a flat
0.25/0.30, a silent degradation).

Deliberately BEST-EFFORT: the ingredient and its nutrients are already saved before
this runs, so any failure here — QA gate block, missing pinned datasets, DB error — is
reported and swallowed rather than raised, leaving the CVs NULL (recoverable with a
manual run) instead of corrupting or discarding the just-entered ingredient.

NOT a member of cv_assign._PIPELINE_FILES: this is orchestration (which food, when),
not CV logic, so it is intentionally excluded from the reproducibility hash. Every CV
value it writes still comes entirely from the hashed resolve_cv / cv_config.
"""
from __future__ import annotations

# Signer recorded on the (skipped) run record; used only if record_run were ever True.
AUTO_SIGNER = "auto:add"


def assign_cv_for_food(food_id: int) -> tuple[bool, str]:
    """Resolve and write CVs for one ingredient's nutrient cells.

    Gated (QA gate must pass), incremental (only this food's cells, no whole-table
    rewrite), no pg_dump backup, and no cv_pipeline_run sign-off update. Returns
    (ok, message) and never raises — callers surface the message to the user.
    """
    try:
        from cv_assign import resolve_all, commit
        from cv_report import evaluate_gate

        resolutions = resolve_all(food_id)
        if not resolutions:
            return True, f"no CV-target nutrient cells for food_id={food_id}"

        passed, failures = evaluate_gate(resolutions)
        if not passed:
            return False, "QA gate blocked: " + "; ".join(failures)

        commit(resolutions, AUTO_SIGNER, full=False, record_run=False)
        measured = sum(1 for r in resolutions if r["resolution"]["measured_cv"] is not None)
        return True, (f"{len(resolutions)} cells "
                      f"({measured} measured, {len(resolutions) - measured} category)")
    except (Exception, SystemExit) as exc:  # noqa: BLE001 — best-effort by design
        return False, f"{type(exc).__name__}: {exc}"
