from __future__ import annotations

import pandas as pd


def aggregate_pair_frame(frame: pd.DataFrame, bars_per_candle: int) -> pd.DataFrame:
    if bars_per_candle <= 1:
        return frame.copy().reset_index(drop=True)

    grouped = frame.copy()
    grouped["_group"] = pd.Series(range(len(grouped)), index=grouped.index) // bars_per_candle
    aggregated = (
        grouped.groupby("_group", sort=True)
        .agg({
            "time": "last",
            "open_1": "first",
            "high_1": "max",
            "low_1": "min",
            "close_1": "last",
            "tick_volume_1": "sum",
            "open_2": "first",
            "high_2": "max",
            "low_2": "min",
            "close_2": "last",
            "tick_volume_2": "sum",
        })
        .reset_index(drop=True)
    )
    return aggregated
