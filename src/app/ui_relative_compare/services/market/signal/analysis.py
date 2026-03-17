from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.domain import RangeStats
from .models import SignalComputationResult, SignalPlotSeries
from .relative_lines import build_relative_line_series


def build_signal_plot_series(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
    range_stats: RangeStats,
) -> SignalPlotSeries:
    line_1, line_2, diff, applied_ratio_long, applied_ratio_short = build_relative_line_series(
        bars=bars,
        digits_1=digits_1,
        digits_2=digits_2,
        invert_second=invert_second,
        mutual_exclusion_enabled=mutual_exclusion_enabled,
        range_stats=range_stats,
    )
    return SignalPlotSeries(
        line_1=line_1,
        line_2=line_2,
        diff=diff,
        applied_ratio_long=applied_ratio_long,
        applied_ratio_short=applied_ratio_short,
    )


def analyze_flow_signal(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
    range_stats: RangeStats,
) -> SignalComputationResult:
    plot = build_signal_plot_series(
        bars=bars,
        digits_1=digits_1,
        digits_2=digits_2,
        invert_second=invert_second,
        mutual_exclusion_enabled=mutual_exclusion_enabled,
        range_stats=range_stats,
    )
    return SignalComputationResult(
        line_1_last=float(plot.line_1.iloc[-1]) if not plot.line_1.empty else 0.0,
        line_2_last=float(plot.line_2.iloc[-1]) if not plot.line_2.empty else 0.0,
        diff_last=float(plot.diff.iloc[-1]) if not plot.diff.empty else 0.0,
        applied_ratio_long=float(plot.applied_ratio_long),
        applied_ratio_short=float(plot.applied_ratio_short),
    )
