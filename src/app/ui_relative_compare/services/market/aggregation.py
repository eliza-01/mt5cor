from __future__ import annotations

import pandas as pd


def aggregate_pair_frame(frame: pd.DataFrame, bars_per_candle: int) -> pd.DataFrame:
    if bars_per_candle <= 1:
        out = frame.copy().reset_index(drop=True)
        out["agg_progress"] = "1/1"
        return out

    grouped = frame.copy().reset_index(drop=True)
    grouped["_group"] = pd.Series(range(len(grouped)), index=grouped.index) // bars_per_candle
    grouped["_bar_in_group"] = grouped.groupby("_group", sort=True).cumcount() + 1

    aggregated = (
        grouped.groupby("_group", sort=True)
        .agg(
            {
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
                "_bar_in_group": "last",
            }
        )
        .reset_index(drop=True)
    )

    aggregated["agg_progress"] = aggregated["_bar_in_group"].astype(int).astype(str) + f"/{int(bars_per_candle)}"
    return aggregated.drop(columns=["_bar_in_group"])