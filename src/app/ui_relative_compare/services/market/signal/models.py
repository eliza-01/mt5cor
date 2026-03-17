from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class SignalPlotSeries:
    gap: pd.Series
    fast_ma: pd.Series
    slow_ma: pd.Series
    ma_diff: pd.Series


@dataclass(slots=True)
class SignalComputationResult:
    fast_window: int
    slow_window: int
    entry_threshold: float
    exit_threshold: float
    gap_last: float
    fast_last: float
    slow_last: float
    ma_diff_last: float
    signal_side: str
    entry_ready: bool
    exit_ready: bool
