from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.domain import DivergenceStats
from .transform import transform_price_delta_to_pips


def build_divergence_series(
    frame: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    ratio_1_to_2: float,
    invert_second: bool = False,
    bid_1: float | None = None,
    bid_2: float | None = None,
) -> tuple[pd.Series, DivergenceStats]:
    move_1 = transform_price_delta_to_pips(frame["close_1"] - frame["open_1"], digits_1)
    move_2 = transform_price_delta_to_pips(
        frame["close_2"] - frame["open_2"],
        digits_2,
        ratio_1_to_2,
        invert_second,
    )
    diff_series = (move_1 - move_2).astype(float)

    current_bar_diff_pips = float(diff_series.iloc[-1])
    live_diff_pips = current_bar_diff_pips
    render_series = diff_series.copy()

    if bid_1 is not None and bid_2 is not None:
        last = frame.iloc[-1]
        live_1 = transform_price_delta_to_pips(float(bid_1) - float(last["open_1"]), digits_1)
        live_2 = transform_price_delta_to_pips(
            float(bid_2) - float(last["open_2"]),
            digits_2,
            ratio_1_to_2,
            invert_second,
        )
        live_diff_pips = float(live_1 - live_2)
        render_series.iloc[-1] = live_diff_pips

    total_diff_pips = float(render_series.sum())
    return render_series.reset_index(drop=True), DivergenceStats(
        total_diff_pips=total_diff_pips,
        current_bar_diff_pips=current_bar_diff_pips,
        live_diff_pips=live_diff_pips,
        uses_ratio=abs(float(ratio_1_to_2) - 1.0) > 1e-12,
    )