from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .models import SpreadFitResult

try:
    from statsmodels.tsa.stattools import adfuller, coint
except Exception:  # pragma: no cover - optional at runtime
    adfuller = None
    coint = None


def _effective_log_price(close: pd.Series, side_relation: str) -> pd.Series:
    safe = close.astype(float).clip(lower=1e-12)
    series = np.log(safe)
    if side_relation == "same":
        series = -series
    return pd.Series(series, index=close.index, dtype=float)


def fit_spread_model(close_1: pd.Series, close_2: pd.Series, side_relation: str) -> SpreadFitResult:
    x = pd.Series(np.log(close_1.astype(float).clip(lower=1e-12)), index=close_1.index, dtype=float)
    y = _effective_log_price(close_2, side_relation=side_relation)
    frame = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if len(frame) < 10:
        raise RuntimeError("Недостаточно точек для spread model")

    design = np.column_stack([np.ones(len(frame)), frame["y"].to_numpy(dtype=float)])
    target = frame["x"].to_numpy(dtype=float)
    coeffs, _, _, _ = np.linalg.lstsq(design, target, rcond=None)
    intercept = float(coeffs[0])
    beta = float(coeffs[1])

    spread = frame["x"] - intercept - beta * frame["y"]
    mean = float(spread.mean())
    std = float(spread.std(ddof=1)) if len(spread) > 1 else 0.0
    last = float(spread.iloc[-1])
    zscore = 0.0 if std <= 1e-12 or not math.isfinite(std) else (last - mean) / std

    coint_pvalue = None
    adf_pvalue = None
    if coint is not None:
        try:
            _, pvalue, _ = coint(frame["x"], frame["y"])
            coint_pvalue = float(pvalue)
        except Exception:
            coint_pvalue = None
    if adfuller is not None and len(spread) >= 20:
        try:
            _, pvalue, *_ = adfuller(spread)
            adf_pvalue = float(pvalue)
        except Exception:
            adf_pvalue = None

    return SpreadFitResult(
        beta=beta,
        intercept=intercept,
        series=spread.reset_index(drop=True),
        mean=mean,
        std=std,
        last=last,
        zscore=float(zscore),
        coint_pvalue=coint_pvalue,
        adf_pvalue=adf_pvalue,
    )
