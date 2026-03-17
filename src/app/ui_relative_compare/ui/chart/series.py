from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.services.market.signal import build_signal_plot_series


def build_signal_line_series(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    ratio_1_to_2: float,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
    fast_window: int,
    slow_window: int,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    plot = build_signal_plot_series(
        bars=bars,
        digits_1=digits_1,
        digits_2=digits_2,
        ratio_1_to_2=ratio_1_to_2,
        invert_second=invert_second,
        mutual_exclusion_enabled=mutual_exclusion_enabled,
        fast_window=fast_window,
        slow_window=slow_window,
    )
    return plot.gap, plot.fast_ma, plot.slow_ma
