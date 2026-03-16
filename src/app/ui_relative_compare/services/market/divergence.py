from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.domain import DivergenceStats
from .common import pip_size_from_digits


def build_divergence_series(frame: pd.DataFrame, digits_1: int, digits_2: int, ratio_1_to_2: float, use_ratio_in_divergence: bool, bid_1: float | None = None, bid_2: float | None = None) -> tuple[pd.Series, DivergenceStats]:
    pip_1 = pip_size_from_digits(digits_1)
    pip_2 = pip_size_from_digits(digits_2)
    factor = ratio_1_to_2 if use_ratio_in_divergence else 1.0

    diff_series = (((frame["close_1"] - frame["open_1"]) / pip_1) - (((frame["close_2"] - frame["open_2"]) / pip_2) * factor)).astype(float)

    current_bar_diff_pips = float(diff_series.iloc[-1])
    live_diff_pips = current_bar_diff_pips
    render_series = diff_series.copy()

    if bid_1 is not None and bid_2 is not None:
        last = frame.iloc[-1]
        live_diff_pips = float(
            ((float(bid_1) - float(last["open_1"])) / pip_1)
            - (((float(bid_2) - float(last["open_2"])) / pip_2) * factor)
        )
        render_series.iloc[-1] = live_diff_pips

    total_diff_pips = float(render_series.sum())
    return render_series.reset_index(drop=True), DivergenceStats(total_diff_pips=total_diff_pips, current_bar_diff_pips=current_bar_diff_pips, live_diff_pips=live_diff_pips, uses_ratio=use_ratio_in_divergence)
