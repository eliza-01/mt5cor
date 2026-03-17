from __future__ import annotations

import math

import pandas as pd


def estimate_execution_ratio(pnl_1: pd.Series, pnl_2: pd.Series) -> tuple[float, float]:
    series = pd.concat([pnl_1.astype(float), pnl_2.astype(float)], axis=1).dropna()
    if len(series) < 3:
        return 0.0, 0.0

    left = series.iloc[:, 0]
    right = series.iloc[:, 1]
    var_right = float(right.var(ddof=1))
    if not math.isfinite(var_right) or var_right <= 1e-12:
        return 0.0, float(left.corr(right) or 0.0)

    cov = float(left.cov(right))
    corr = float(left.corr(right) or 0.0)
    ratio = -cov / var_right
    if not math.isfinite(ratio):
        ratio = 0.0
    return float(ratio), corr
