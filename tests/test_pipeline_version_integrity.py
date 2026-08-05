"""Guard against the config-hash landmine.

cv_config.config_sha256() and cv_assign.code_sha256() hash the RAW BYTES of the
pipeline files, and cv_assign's commit() refuses to run if those hashes no longer
match what was stored for the current PIPELINE_VERSION. So editing ANY _PIPELINE_FILES
file (cv_config.py, resolve_cv.py, cv_assign.py, ...) after a committed run — even a
comment or whitespace — makes the NEXT `cv_assign --commit` (full OR --food-id) fail
with "config/code/dataset changed under pipeline_version ... bump PIPELINE_VERSION".

This surfaces that drift at pytest time instead of at --commit time, so you find out
while editing rather than the next time you try to assign CVs (e.g. for a new
ingredient). If this fails: bump PIPELINE_VERSION (a real pipeline change) or revert
the edit (a cosmetic one).

DB-optional: skips when the DB is unreachable or the current PIPELINE_VERSION has no
committed run yet (a version under development), so it never blocks a fully-mocked or
CI run and never fires on a not-yet-shipped version.
"""
from __future__ import annotations

import pytest

import cv_config
from cv_assign import code_sha256


def _committed_hashes(version: str):
    """(config_sha256, code_sha256) stored for `version`, or None if unavailable."""
    try:
        from db_connection import get_db
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT config_sha256, code_sha256 FROM cv_pipeline_run "
                "WHERE pipeline_version = %s",
                (version,),
            )
            row = cur.fetchone()
    except Exception:  # noqa: BLE001 — DB down / not configured: nothing to guard
        return None
    if row is None:
        return None
    return row["config_sha256"], row["code_sha256"]


def test_pipeline_files_unchanged_under_committed_version() -> None:
    version = cv_config.PIPELINE_VERSION
    stored = _committed_hashes(version)
    if stored is None:
        pytest.skip(f"{version} has no committed run (or DB unavailable) — nothing to guard")

    stored_config, stored_code = stored
    assert cv_config.config_sha256() == stored_config, (
        f"cv_config.py changed under already-committed PIPELINE_VERSION={version}. "
        "This will make the next `cv_assign --commit` refuse. Bump PIPELINE_VERSION "
        "for a real config change, or revert the edit if it was cosmetic."
    )
    assert code_sha256() == stored_code, (
        f"A pipeline file (resolve_cv/cv_assign/cv_stats/...) changed under "
        f"already-committed PIPELINE_VERSION={version}. Bump PIPELINE_VERSION or "
        "revert the edit."
    )
