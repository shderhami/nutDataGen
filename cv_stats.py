"""Shared CV statistics (used by cv_extract and resolve_cv).

All CVs are dimensionless fractions.  Conventions match the plan §4:
  * Tier-1 (SR28 SE):   s = SE*sqrt(n)  (sample SD);  sigma_hat = s / c4(n)  -> RAISES.
  * Tier-2 (FDC range): SD = (max-min) / xi(n)  (Wan et al. 2014).
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Optional

_N = NormalDist()


def c4(n: int) -> float:
    """Unbiasing constant for the sample SD (c4(n) < 1 for finite n; -> 1)."""
    if n < 2:
        return 1.0
    return math.sqrt(2.0 / (n - 1)) * math.exp(
        math.lgamma(n / 2.0) - math.lgamma((n - 1) / 2.0)
    )


def wan_sd(mn: float, mx: float, n: int) -> Optional[float]:
    """Population SD from {min, max, n} (Wan 2014 range estimator)."""
    if n is None or n < 2 or mx is None or mn is None or mx <= mn:
        return None
    xi = 2.0 * _N.inv_cdf((n - 0.375) / (n + 0.25))
    return (mx - mn) / xi if xi > 0 else None


def cv_from_se(value: Optional[float], se: Optional[float], n: Optional[int]) -> Optional[float]:
    """Population CV from a reported SE of the mean (Tier 1). Requires n >= 3."""
    if value is None or value <= 0 or se is None or se <= 0 or n is None or n < 3:
        return None
    s = se * math.sqrt(n)          # sample SD
    sigma = s / c4(n)              # unbiased (divide by c4<1 => raises)
    return sigma / value


def cv_from_range(value: Optional[float], mn: Optional[float], mx: Optional[float],
                  n: Optional[int]) -> Optional[float]:
    """Population CV from {min, max, n} (Tier 2). Requires n >= 2, min != max."""
    if value is None or value <= 0:
        return None
    sd = wan_sd(mn, mx, n)
    return (sd / value) if sd is not None else None


def clip_cv(cv: Optional[float], cap: float) -> tuple[Optional[float], bool]:
    """Clip an over-inflated (near-detection) CV to the cap; returns (cv, was_clipped)."""
    if cv is None:
        return None, False
    if cv > cap:
        return cap, True
    return cv, False
