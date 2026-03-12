# src/app/ui_relative_compare/ui/chart.py
# Draws a fixed-size scrollable candle tape and a synced divergence line chart below it.
from __future__ import annotations

import tkinter as tk

import pandas as pd

from src.app.ui_relative_compare.constants import (
    CHART_AXIS,
    CHART_BG,
    CHART_GRID,
    CHART_TEXT,
    PAIR_1_DOWN,
    PAIR_1_UP,
    PAIR_2_DOWN,
    PAIR_2_UP,
)
from src.app.ui_relative_compare.models import DivergenceStats, TradePlan


BASE_STEP_X = 28.0
BASE_BODY_HALF = 4.0
BASE_WICK_OFFSET = 7.0


class RelativeChart:
    def __init__(self, candle_canvas: tk.Canvas, line_canvas: tk.Canvas) -> None:
        self.candle_canvas = candle_canvas
        self.line_canvas = line_canvas

    def draw(
        self,
        bars: pd.DataFrame,
        divergence_series: pd.Series,
        symbol_1: str,
        symbol_2: str,
        ratio_1_to_2: float,
        width_adjust_px: int,
        height_adjust_px: int,
        divergence_stats: DivergenceStats,
        trade_plan: TradePlan,
    ) -> None:
        self._draw_candles(
            bars=bars,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            ratio_1_to_2=ratio_1_to_2,
            width_adjust_px=width_adjust_px,
            height_adjust_px=height_adjust_px,
            divergence_stats=divergence_stats,
            trade_plan=trade_plan,
        )
        self._draw_divergence_line(
            divergence_series=divergence_series,
            width_adjust_px=width_adjust_px,
        )

    def _draw_candles(
        self,
        bars: pd.DataFrame,
        symbol_1: str,
        symbol_2: str,
        ratio_1_to_2: float,
        width_adjust_px: int,
        height_adjust_px: int,
        divergence_stats: DivergenceStats,
        trade_plan: TradePlan,
    ) -> None:
        self.candle_canvas.update_idletasks()
        viewport_width = max(self.candle_canvas.winfo_width(), 400)
        height = max(self.candle_canvas.winfo_height(), 340)

        self.candle_canvas.delete("all")
        self.candle_canvas.create_rectangle(0, 0, viewport_width, height, fill=CHART_BG, outline=CHART_BG)

        center_y = height / 2
        left_pad = 60
        right_pad = 30
        top_pad = 118
        bottom_pad = 34

        n = len(bars)
        step_x = max(16.0, BASE_STEP_X + width_adjust_px)
        body_half = max(2.0, BASE_BODY_HALF + width_adjust_px * 0.35)
        wick_offset = max(body_half + 2.0, BASE_WICK_OFFSET + width_adjust_px * 0.35)

        total_width = max(viewport_width, left_pad + right_pad + n * step_x + step_x)

        max_abs = 1.0
        for col in ["p1_high", "p1_low", "p1_close", "p2_high", "p2_low", "p2_close"]:
            val = bars[col].abs().max()
            if pd.notna(val):
                max_abs = max(max_abs, float(val))

        usable_half = max(40.0, (height - top_pad - bottom_pad) / 2 - 10)
        base_scale = usable_half / (max_abs * 1.15)
        scale = max(0.5, base_scale + height_adjust_px)

        self.candle_canvas.create_line(left_pad, center_y, total_width - right_pad, center_y, fill=CHART_AXIS, width=1)
        self.candle_canvas.create_text(12, center_y, anchor="w", text="OPEN", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))

        for level in [0.25, 0.5, 0.75, 1.0]:
            dy = max_abs * base_scale * level
            self.candle_canvas.create_line(left_pad, center_y - dy, total_width - right_pad, center_y - dy, fill=CHART_GRID)
            self.candle_canvas.create_line(left_pad, center_y + dy, total_width - right_pad, center_y + dy, fill=CHART_GRID)

        last_points: list[dict[str, float]] = []

        for i, row in bars.iterrows():
            x = left_pad + step_x * i + step_x / 2

            p1_high_y = center_y - float(row["p1_high"]) * scale
            p1_low_y = center_y - float(row["p1_low"]) * scale
            p1_close_y = center_y - float(row["p1_close"]) * scale

            p2_high_y = center_y - float(row["p2_high"]) * scale
            p2_low_y = center_y - float(row["p2_low"]) * scale
            p2_close_y = center_y - float(row["p2_close"]) * scale

            p1_color = PAIR_1_UP if float(row["close_1"]) >= float(row["open_1"]) else PAIR_1_DOWN
            p2_color = PAIR_2_UP if float(row["close_2"]) >= float(row["open_2"]) else PAIR_2_DOWN

            p1_x = x - wick_offset
            p2_x = x + wick_offset

            self.candle_canvas.create_line(p1_x, p1_high_y, p1_x, p1_low_y, fill=p1_color, width=1)
            self.candle_canvas.create_line(p2_x, p2_high_y, p2_x, p2_low_y, fill=p2_color, width=1)

            self._draw_body(self.candle_canvas, p1_x, center_y, p1_close_y, body_half, p1_color)
            self._draw_body(self.candle_canvas, p2_x, center_y, p2_close_y, body_half, p2_color)

            if i >= max(0, n - 2):
                last_points.append(
                    {
                        "p1_x": p1_x,
                        "p2_x": p2_x,
                        "p1_high_y": p1_high_y,
                        "p1_low_y": p1_low_y,
                        "p2_high_y": p2_high_y,
                        "p2_low_y": p2_low_y,
                    }
                )

        self.candle_canvas.create_text(
            total_width / 2,
            10,
            anchor="n",
            fill=CHART_TEXT,
            font=("Segoe UI", 10),
            text="свечи рядом, фиксированный размер, горизонтальный скролл",
        )

        self._draw_pair_legend(symbol_1, symbol_2)

        mode_text = "с коэф" if divergence_stats.uses_ratio else "реал"
        divergence_text = (
            f"Δ режим: {mode_text}\n"
            f"Лента Δ: {divergence_stats.total_diff_pips:+.2f} п\n"
            f"Текущая свеча Δ: {divergence_stats.current_bar_diff_pips:+.2f} п\n"
            f"Live bid Δ: {divergence_stats.live_diff_pips:+.2f} п"
        )
        self.candle_canvas.create_text(
            total_width - right_pad,
            10,
            anchor="ne",
            fill=CHART_TEXT,
            font=("Segoe UI", 10, "bold"),
            justify="right",
            text=divergence_text,
        )

        self._draw_trade_arrows(
            last_points=last_points,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            trade_plan=trade_plan,
            height=height,
        )

        self.candle_canvas.create_text(
            total_width - right_pad,
            height - 10,
            anchor="se",
            fill=CHART_TEXT,
            font=("Segoe UI", 9),
            text=f"{symbol_2} | scale coef 1/2 = {ratio_1_to_2:.6f} | width={width_adjust_px:+d}px | height={height_adjust_px:+d}px",
        )

        self.candle_canvas.configure(scrollregion=(0, 0, total_width, height))

    def _draw_divergence_line(
        self,
        divergence_series: pd.Series,
        width_adjust_px: int,
    ) -> None:
        self.line_canvas.update_idletasks()
        viewport_width = max(self.line_canvas.winfo_width(), 400)
        height = max(self.line_canvas.winfo_height(), 120)

        self.line_canvas.delete("all")
        self.line_canvas.create_rectangle(0, 0, viewport_width, height, fill=CHART_BG, outline=CHART_BG)

        left_pad = 60
        right_pad = 30
        top_pad = 18
        bottom_pad = 22

        n = len(divergence_series)
        step_x = max(16.0, BASE_STEP_X + width_adjust_px)
        total_width = max(viewport_width, left_pad + right_pad + n * step_x + step_x)

        max_abs = max(1.0, float(divergence_series.abs().max()) if not divergence_series.empty else 1.0)
        mid_y = height / 2
        usable_half = max(20.0, (height - top_pad - bottom_pad) / 2)
        scale = usable_half / (max_abs * 1.1)

        self.line_canvas.create_line(left_pad, mid_y, total_width - right_pad, mid_y, fill=CHART_AXIS, width=1)
        self.line_canvas.create_text(12, mid_y, anchor="w", text="0", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))

        for level in [0.5, 1.0]:
            dy = max_abs * scale * level
            self.line_canvas.create_line(left_pad, mid_y - dy, total_width - right_pad, mid_y - dy, fill=CHART_GRID)
            self.line_canvas.create_line(left_pad, mid_y + dy, total_width - right_pad, mid_y + dy, fill=CHART_GRID)

        points: list[float] = []
        for i, value in enumerate(divergence_series.tolist()):
            x = left_pad + step_x * i + step_x / 2
            y = mid_y - float(value) * scale
            points.extend([x, y])

        if len(points) >= 4:
            self.line_canvas.create_line(*points, fill="#eab308", width=2, smooth=False)

        self.line_canvas.create_text(
            left_pad,
            6,
            anchor="nw",
            fill=CHART_TEXT,
            font=("Segoe UI", 9, "bold"),
            text="Линия расхождения",
        )

        self.line_canvas.configure(scrollregion=(0, 0, total_width, height))

    def _draw_pair_legend(self, symbol_1: str, symbol_2: str) -> None:
        x0 = 16
        y0 = 10
        row_h = 22
        box = 10

        self.candle_canvas.create_text(
            x0,
            y0,
            anchor="nw",
            fill=CHART_TEXT,
            font=("Segoe UI", 10, "bold"),
            text="Цвета:",
        )

        y1 = y0 + 22
        self.candle_canvas.create_rectangle(x0, y1, x0 + box, y1 + box, fill=PAIR_1_UP, outline=PAIR_1_UP)
        self.candle_canvas.create_rectangle(x0 + 14, y1, x0 + 14 + box, y1 + box, fill=PAIR_1_DOWN, outline=PAIR_1_DOWN)
        self.candle_canvas.create_text(
            x0 + 32,
            y1 + box / 2,
            anchor="w",
            fill=CHART_TEXT,
            font=("Segoe UI", 9, "bold"),
            text=f"{symbol_1}  up/down",
        )

        y2 = y1 + row_h
        self.candle_canvas.create_rectangle(x0, y2, x0 + box, y2 + box, fill=PAIR_2_UP, outline=PAIR_2_UP)
        self.candle_canvas.create_rectangle(x0 + 14, y2, x0 + 14 + box, y2 + box, fill=PAIR_2_DOWN, outline=PAIR_2_DOWN)
        self.candle_canvas.create_text(
            x0 + 32,
            y2 + box / 2,
            anchor="w",
            fill=CHART_TEXT,
            font=("Segoe UI", 9, "bold"),
            text=f"{symbol_2}  up/down",
        )

    def _draw_trade_arrows(
        self,
        last_points: list[dict[str, float]],
        symbol_1: str,
        symbol_2: str,
        trade_plan: TradePlan,
        height: int,
    ) -> None:
        sell_color = "#ef4444"
        buy_color = "#22c55e"

        sell_is_p1 = trade_plan.sell_symbol == symbol_1
        buy_is_p1 = trade_plan.buy_symbol == symbol_1
        sell_is_p2 = trade_plan.sell_symbol == symbol_2
        buy_is_p2 = trade_plan.buy_symbol == symbol_2

        for point in last_points:
            if sell_is_p1:
                self._draw_sell_arrow(float(point["p1_x"]), float(point["p1_high_y"]) - 18, sell_color)
            if buy_is_p1:
                self._draw_buy_arrow(float(point["p1_x"]), float(point["p1_low_y"]) + 18, buy_color, height)

            if sell_is_p2:
                self._draw_sell_arrow(float(point["p2_x"]), float(point["p2_high_y"]) - 18, sell_color)
            if buy_is_p2:
                self._draw_buy_arrow(float(point["p2_x"]), float(point["p2_low_y"]) + 18, buy_color, height)

    def _draw_sell_arrow(self, x: float, y: float, color: str) -> None:
        y = max(92.0, y)
        self.candle_canvas.create_text(x, y, anchor="s", fill=color, font=("Segoe UI", 12, "bold"), text="↓")

    def _draw_buy_arrow(self, x: float, y: float, color: str, height: int) -> None:
        y = min(float(height - 20), y)
        self.candle_canvas.create_text(x, y, anchor="n", fill=color, font=("Segoe UI", 12, "bold"), text="↑")

    def _draw_body(
        self,
        canvas: tk.Canvas,
        x: float,
        y_open: float,
        y_close: float,
        half_width: float,
        color: str,
    ) -> None:
        top = min(y_open, y_close)
        bottom = max(y_open, y_close)

        if abs(bottom - top) < 2:
            canvas.create_line(x - half_width, y_close, x + half_width, y_close, fill=color, width=3)
            return

        canvas.create_rectangle(
            x - half_width,
            top,
            x + half_width,
            bottom,
            outline=color,
            fill=color,
        )