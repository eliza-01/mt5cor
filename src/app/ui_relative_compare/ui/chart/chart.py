from __future__ import annotations

import tkinter as tk

import pandas as pd

from src.app.ui_relative_compare.domain import SignalDiagnostics, TradePlan
from .candles import render_candles
from .layout import LEFT_PAD, pair_layout
from .lines import render_relative_lines
from .series import build_signal_line_series


class RelativeChart:
    def __init__(self, candle_canvas: tk.Canvas, line_canvas: tk.Canvas) -> None:
        self.candle_canvas = candle_canvas
        self.line_canvas = line_canvas

    def draw(
        self,
        bars: pd.DataFrame,
        symbol_1: str,
        symbol_2: str,
        ratio_1_to_2: float,
        invert_second: bool,
        width_adjust_px: int,
        height_adjust_px: int,
        pair_gap_adjust_px: int,
        trade_plan: TradePlan,
        selected_start_index: int | None,
        selected_end_index: int | None,
        colors: dict[str, str],
        line_zoom: float,
        digits_1: int,
        digits_2: int,
        mutual_exclusion_enabled: bool,
        signal_diagnostics: SignalDiagnostics,
        line_chart_mode: str,
    ) -> None:
        render_candles(
            canvas=self.candle_canvas,
            bars=bars,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            ratio_1_to_2=ratio_1_to_2,
            invert_second=invert_second,
            width_adjust_px=width_adjust_px,
            height_adjust_px=height_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
            trade_plan=trade_plan,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
            colors=colors,
        )
        gap, fast_ma, slow_ma = build_signal_line_series(
            bars,
            digits_1=digits_1,
            digits_2=digits_2,
            ratio_1_to_2=ratio_1_to_2,
            invert_second=invert_second,
            mutual_exclusion_enabled=mutual_exclusion_enabled,
            fast_window=signal_diagnostics.fast_window,
            slow_window=signal_diagnostics.slow_window,
        )
        render_relative_lines(
            canvas=self.line_canvas,
            gap=gap,
            fast_ma=fast_ma,
            slow_ma=slow_ma,
            width_adjust_px=width_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
            colors=colors,
            line_zoom=line_zoom,
            entry_threshold=signal_diagnostics.entry_threshold,
            exit_threshold=signal_diagnostics.exit_threshold,
            chart_mode=line_chart_mode,
        )

    def get_index_at_x(self, bars_count: int, x_world: float, width_adjust_px: int, pair_gap_adjust_px: int) -> int | None:
        if bars_count <= 0:
            return None
        layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
        step = layout.pair_width + layout.pair_gap
        center_offset = LEFT_PAD + layout.pair_width / 2.0
        raw_index = round((x_world - center_offset) / step)
        return max(0, min(bars_count - 1, int(raw_index)))