from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.domain import RangeStats
from src.app.ui_relative_compare.services.market.transform import transform_price_delta_to_pips


def _applied_ratios(range_stats: RangeStats) -> tuple[float, float]:
    if range_stats.apply_common:
        return float(range_stats.common_ratio), float(range_stats.common_ratio)
    long_ratio = float(range_stats.long_ratio) if range_stats.apply_long else 1.0
    short_ratio = float(range_stats.short_ratio) if range_stats.apply_short else 1.0
    return long_ratio, short_ratio


def build_relative_line_series(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
    range_stats: RangeStats,
) -> tuple[pd.Series, pd.Series, pd.Series, float, float]:
    if bars.empty:
        empty = pd.Series(dtype=float)
        return empty, empty, empty, 1.0, 1.0

    long_ratio, short_ratio = _applied_ratios(range_stats)

    long_1 = transform_price_delta_to_pips(bars["high_1"].astype(float) - bars["open_1"].astype(float), digits_1)
    short_1 = transform_price_delta_to_pips(bars["open_1"].astype(float) - bars["low_1"].astype(float), digits_1)

    long_2_raw = transform_price_delta_to_pips(bars["high_2"].astype(float) - bars["open_2"].astype(float), digits_2)
    short_2_raw = transform_price_delta_to_pips(bars["open_2"].astype(float) - bars["low_2"].astype(float), digits_2)

    long_2_scaled = long_2_raw.astype(float) * float(long_ratio)
    short_2_scaled = short_2_raw.astype(float) * float(short_ratio)

    if invert_second:
        long_2 = short_2_scaled
        short_2 = long_2_scaled
    else:
        long_2 = long_2_scaled
        short_2 = short_2_scaled

    out_1 = []
    out_2 = []
    diff = []
    acc_1 = 0.0
    acc_2 = 0.0

    for i in range(len(bars)):
        move_long_1 = float(long_1.iloc[i])
        move_short_1 = float(short_1.iloc[i])
        move_long_2 = float(long_2.iloc[i])
        move_short_2 = float(short_2.iloc[i])

        if mutual_exclusion_enabled:
            common_long = min(move_long_1, move_long_2)
            common_short = min(move_short_1, move_short_2)
            move_long_1 -= common_long
            move_long_2 -= common_long
            move_short_1 -= common_short
            move_short_2 -= common_short

        acc_1 += move_long_1 - move_short_1
        acc_2 += move_long_2 - move_short_2
        out_1.append(acc_1)
        out_2.append(acc_2)
        diff.append(acc_1 - acc_2)

    return (
        pd.Series(out_1, dtype=float),
        pd.Series(out_2, dtype=float),
        pd.Series(diff, dtype=float),
        float(long_ratio),
        float(short_ratio),
    )
