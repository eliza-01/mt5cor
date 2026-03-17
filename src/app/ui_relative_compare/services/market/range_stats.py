from __future__ import annotations

import math

import pandas as pd

from src.app.ui_relative_compare.domain import RangeStats
from .transform import transform_price_delta_to_pips


EPS = 1e-12


def _safe_ratio(left: float, right: float) -> float:
    if not math.isfinite(right) or abs(right) <= EPS:
        return 1.0
    value = float(left) / float(right)
    return float(value) if math.isfinite(value) and value > EPS else 1.0


def build_range_stats(
    frame: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    apply_long: bool,
    apply_short: bool,
    apply_common: bool,
) -> RangeStats:
    long_1 = transform_price_delta_to_pips(frame["high_1"].astype(float) - frame["open_1"].astype(float), digits_1)
    short_1 = transform_price_delta_to_pips(frame["open_1"].astype(float) - frame["low_1"].astype(float), digits_1)
    long_2 = transform_price_delta_to_pips(frame["high_2"].astype(float) - frame["open_2"].astype(float), digits_2)
    short_2 = transform_price_delta_to_pips(frame["open_2"].astype(float) - frame["low_2"].astype(float), digits_2)

    long_total_1 = float(long_1.sum())
    long_total_2 = float(long_2.sum())
    short_total_1 = float(short_1.sum())
    short_total_2 = float(short_2.sum())

    return RangeStats(
        symbol_1_long_total=long_total_1,
        symbol_2_long_total=long_total_2,
        symbol_1_short_total=short_total_1,
        symbol_2_short_total=short_total_2,
        long_ratio=_safe_ratio(long_total_1, long_total_2),
        short_ratio=_safe_ratio(short_total_1, short_total_2),
        common_ratio=_safe_ratio(long_total_1 + short_total_1, long_total_2 + short_total_2),
        apply_long=bool(apply_long),
        apply_short=bool(apply_short),
        apply_common=bool(apply_common),
    )
