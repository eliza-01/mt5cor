from __future__ import annotations

import pandas as pd

from .direction import build_spread_trade_directions
from .ma import sma
from .models import SignalComputationResult, SignalPlotSeries
from .relative_lines import build_relative_line_series


def build_signal_plot_series(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    ratio_1_to_2: float,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
    fast_window: int,
    slow_window: int,
) -> SignalPlotSeries:
    line_1, line_2 = build_relative_line_series(
        bars=bars,
        digits_1=digits_1,
        digits_2=digits_2,
        ratio_1_to_2=ratio_1_to_2,
        invert_second=invert_second,
        mutual_exclusion_enabled=mutual_exclusion_enabled,
    )
    gap = (line_1 - line_2).astype(float)
    fast_ma = sma(gap, fast_window)
    slow_ma = sma(gap, slow_window)
    ma_diff = (fast_ma - slow_ma).astype(float)
    return SignalPlotSeries(gap=gap, fast_ma=fast_ma, slow_ma=slow_ma, ma_diff=ma_diff)


def analyze_ma_gap_signal(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    ratio_1_to_2: float,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
    fast_window: int,
    slow_window: int,
    entry_threshold: float,
    exit_threshold: float,
) -> SignalComputationResult:
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

    gap_last = float(plot.gap.iloc[-1]) if not plot.gap.empty else 0.0
    fast_last = float(plot.fast_ma.iloc[-1]) if not plot.fast_ma.empty else 0.0
    slow_last = float(plot.slow_ma.iloc[-1]) if not plot.slow_ma.empty else 0.0
    ma_diff_last = float(plot.ma_diff.iloc[-1]) if not plot.ma_diff.empty else 0.0

    threshold_entry = abs(float(entry_threshold))
    threshold_exit = abs(float(exit_threshold))

    if ma_diff_last >= threshold_entry:
        signal_side = "short"
        entry_ready = True
    elif ma_diff_last <= -threshold_entry:
        signal_side = "long"
        entry_ready = True
    else:
        signal_side = "flat"
        entry_ready = False

    exit_ready = abs(ma_diff_last) <= threshold_exit

    return SignalComputationResult(
        fast_window=max(1, int(fast_window)),
        slow_window=max(1, int(slow_window)),
        entry_threshold=threshold_entry,
        exit_threshold=threshold_exit,
        gap_last=gap_last,
        fast_last=fast_last,
        slow_last=slow_last,
        ma_diff_last=ma_diff_last,
        signal_side=signal_side,
        entry_ready=entry_ready,
        exit_ready=exit_ready,
    )
