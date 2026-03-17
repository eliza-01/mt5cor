from __future__ import annotations

import tkinter as tk

import pandas as pd

from src.app.ui_relative_compare.domain.models import FlowDiagnostics, LiveTailSnapshot, RangeStats, TradePlan
from .candles import render_candles, update_live_tail_on_candles
from .layout import LEFT_PAD, pair_layout
from .lines import render_relative_lines, update_live_tail_on_lines
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
        range_stats: RangeStats,
        flow_diagnostics: FlowDiagnostics,
        live_tail: LiveTailSnapshot | None,
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
            live_tail=live_tail,
        )

        line_1, line_2, diff, _, _ = build_signal_line_series(
            bars=bars,
            digits_1=digits_1,
            digits_2=digits_2,
            invert_second=invert_second,
            mutual_exclusion_enabled=mutual_exclusion_enabled,
            range_stats=range_stats,
        )
        render_relative_lines(
            canvas=self.line_canvas,
            line_1=line_1,
            line_2=line_2,
            diff=diff,
            width_adjust_px=width_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
            colors=colors,
            line_zoom=line_zoom,
            flow_diagnostics=flow_diagnostics,
            live_tail=live_tail,
        )

    def update_live_tail(
        self,
        bars: pd.DataFrame,
        trade_plan: TradePlan,
        live_tail: LiveTailSnapshot | None,
        width_adjust_px: int,
        height_adjust_px: int,
        pair_gap_adjust_px: int,
        line_zoom: float,
        digits_1: int,
        digits_2: int,
        invert_second: bool,
        mutual_exclusion_enabled: bool,
        range_stats: RangeStats,
        flow_diagnostics: FlowDiagnostics,
    ) -> None:
        update_live_tail_on_candles(
            canvas=self.candle_canvas,
            bars=bars,
            trade_plan=trade_plan,
            live_tail=live_tail,
            width_adjust_px=width_adjust_px,
            height_adjust_px=height_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
        )

        line_1, line_2, diff, _, _ = build_signal_line_series(
            bars=bars,
            digits_1=digits_1,
            digits_2=digits_2,
            invert_second=invert_second,
            mutual_exclusion_enabled=mutual_exclusion_enabled,
            range_stats=range_stats,
        )
        update_live_tail_on_lines(
            canvas=self.line_canvas,
            line_1=line_1,
            line_2=line_2,
            diff=diff,
            flow_diagnostics=flow_diagnostics,
            live_tail=live_tail,
            width_adjust_px=width_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
            line_zoom=line_zoom,
        )

    def get_index_at_x(self, bars_count: int, x_world: float, width_adjust_px: int, pair_gap_adjust_px: int) -> int | None:
        if bars_count <= 0:
            return None
        layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
        step = layout.pair_width + layout.pair_gap
        center_offset = LEFT_PAD + layout.pair_width / 2.0
        raw_index = round((x_world - center_offset) / step)
        return max(0, min(bars_count - 1, int(raw_index)))