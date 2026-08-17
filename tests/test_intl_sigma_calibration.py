"""Drift guard for the cv-v8 pooling calibration.

The observations file grows with each validated ingredient; sigma^2 must be
recalibrated when the accumulated evidence moves it materially. This test IS
that process: when it fails, recompute with `python cv_intl.py`, update
cv_config.INTL_CV_SIGMA2, bump PIPELINE_VERSION, and re-commit the pipeline.
"""
from __future__ import annotations

import pytest

import cv_config
import cv_intl

_TOL = 1.75   # wide band: sigma^2 is itself a noisy estimate


def test_applied_sigma2_matches_recomputed() -> None:
    if not cv_intl.INTL_CSV.exists():
        pytest.skip("no intl observations file")
    res = cv_intl.recompute_sigma2()
    if res is None:
        pytest.skip("not enough calibration pairs")
    lo, hi = res["sigma2"] / _TOL, res["sigma2"] * _TOL
    assert lo <= cv_config.INTL_CV_SIGMA2 <= hi, (
        f"INTL_CV_SIGMA2={cv_config.INTL_CV_SIGMA2} has drifted from the recomputed "
        f"{res['sigma2']:.3f} ({res['pairs']} pairs). Update the constant, bump "
        f"PIPELINE_VERSION, and re-commit the pipeline (cv_assign --commit).")
