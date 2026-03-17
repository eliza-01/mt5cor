from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class PnLSeriesResult:
    values: pd.Series
    conversion_mode: str


@dataclass(slots=True)
class SpreadFitResult:
    beta: float
    intercept: float
    series: pd.Series
    mean: float
    std: float
    last: float
    zscore: float
    coint_pvalue: float | None
    adf_pvalue: float | None


@dataclass(slots=True)
class HedgeComputationResult:
    window: int
    correlation: float
    execution_ratio: float
    execution_ratio_abs: float
    side_relation: str
    spread: SpreadFitResult
    conversion_mode_1: str
    conversion_mode_2: str
