"""Best-effort contract of cv_autoassign.assign_cv_for_food.

It must never raise (the ingredient is already saved), it must NOT commit when the QA
gate blocks, and it must call cv_assign.commit as an incremental, non-run-recording
write (full=False, record_run=False).
"""
import sys
import types

import cv_autoassign


def _install(monkeypatch, *, resolve_all=None, evaluate_gate=None, commit=None):
    """Replace the lazily-imported cv_assign / cv_report symbols with fakes."""
    ca = types.ModuleType("cv_assign")
    ca.resolve_all = resolve_all if resolve_all is not None else (lambda fid: [])
    ca.commit = commit if commit is not None else (lambda *a, **k: None)
    cr = types.ModuleType("cv_report")
    cr.evaluate_gate = evaluate_gate if evaluate_gate is not None else (lambda res: (True, []))
    monkeypatch.setitem(sys.modules, "cv_assign", ca)
    monkeypatch.setitem(sys.modules, "cv_report", cr)


def test_no_target_cells_is_ok(monkeypatch):
    _install(monkeypatch, resolve_all=lambda fid: [])
    ok, msg = cv_autoassign.assign_cv_for_food(10001)
    assert ok
    assert "no CV-target" in msg


def test_gate_block_returns_false_and_does_not_commit(monkeypatch):
    called = {"commit": False}

    def commit(*a, **k):
        called["commit"] = True

    _install(
        monkeypatch,
        resolve_all=lambda fid: [{"resolution": {"measured_cv": None}}],
        evaluate_gate=lambda res: (False, ["Bucket-A nutrient ships too low"]),
        commit=commit,
    )
    ok, msg = cv_autoassign.assign_cv_for_food(10001)
    assert not ok
    assert "QA gate blocked" in msg
    assert called["commit"] is False


def test_exceptions_are_swallowed(monkeypatch):
    def boom(fid):
        raise RuntimeError("db down")

    _install(monkeypatch, resolve_all=boom)
    ok, msg = cv_autoassign.assign_cv_for_food(10001)
    assert not ok
    assert "RuntimeError: db down" in msg


def test_happy_path_commits_incremental_without_recording_run(monkeypatch):
    seen = {}

    def commit(resolutions, signer, full, record_run=True):
        seen.update(signer=signer, full=full, record_run=record_run, n=len(resolutions))

    _install(
        monkeypatch,
        resolve_all=lambda fid: [
            {"resolution": {"measured_cv": 0.1}},
            {"resolution": {"measured_cv": None}},
        ],
        commit=commit,
    )
    ok, msg = cv_autoassign.assign_cv_for_food(10001)
    assert ok
    assert seen == {"signer": cv_autoassign.AUTO_SIGNER, "full": False, "record_run": False, "n": 2}
    assert "1 measured" in msg and "1 category" in msg
