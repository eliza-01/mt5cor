from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class SignalPlotSeries:
    line_1: pd.Series
    line_2: pd.Series
    diff: pd.Series
    applied_ratio_long: float
    applied_ratio_short: float


@dataclass(slots=True)
class SignalComputationResult:
    line_1_last: float
    line_2_last: float
    diff_last: float
    applied_ratio_long: float
    applied_ratio_short: float
