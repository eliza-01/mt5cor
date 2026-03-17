from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.domain import RangeStats
from src.app.ui_relative_compare.services.market.signal import build_signal_plot_series


def build_signal_line_series(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
    range_stats: RangeStats,
) -> tuple[pd.Series, pd.Series, pd.Series, float, float]:
    plot = build_signal_plot_series(
        bars=bars,
        digits_1=digits_1,
        digits_2=digits_2,
        invert_second=invert_second,
        mutual_exclusion_enabled=mutual_exclusion_enabled,
        range_stats=range_stats,
    )
    return plot.line_1, plot.line_2, plot.diff, plot.applied_ratio_long, plot.applied_ratio_short
