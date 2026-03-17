from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    size = max(1, int(window))
    return series.astype(float).rolling(size, min_periods=1).mean()
