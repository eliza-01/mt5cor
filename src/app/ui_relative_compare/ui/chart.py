
# src/app/ui_relative_compare/ui/chart.py
# Draws two non-mirrored relative candle streams side by side on one canvas.
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
from src.app.ui_relative_compare.models import DivergenceStats


class RelativeChart:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas

    def draw(
        self,
        bars: pd.DataFrame,
        symbol_1: str,
        symbol_2: str,
        ratio_1_to_2: float,
        width_adjust_px: int,
        height_adjust_px: int,
        divergence_stats: DivergenceStats,
    ) -> None:
        self.canvas.update_idletasks()
        width = max(self.canvas.winfo_width(), 400)
        height = max(self.canvas.winfo_height(), 300)

        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, width, height, fill=CHART_BG, outline=CHART_BG)

        center_y = height / 2
        left_pad = 60
        right_pad = 20
        top_pad = 88
        bottom_pad = 34

        max_abs = 1.0
        for col in ["p1_high", "p1_low", "p1_close", "p2_high", "p2_low", "p2_close"]:
            val = bars[col].abs().max()
            if pd.notna(val):
                max_abs = max(max_abs, float(val))

        usable_half = (height - top_pad - bottom_pad) / 2 - 10
        base_scale = usable_half / (max_abs * 1.15)
        scale = max(0.5, base_scale + height_adjust_px)

        self.canvas.create_line(left_pad, center_y, width - right_pad, center_y, fill=CHART_AXIS, width=1)
        self.canvas.create_text(12, center_y, anchor="w", text="OPEN", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))

        for level in [0.25, 0.5, 0.75, 1.0]:
            dy = max_abs * base_scale * level
            self.canvas.create_line(left_pad, center_y - dy, width - right_pad, center_y - dy, fill=CHART_GRID)
            self.canvas.create_line(left_pad, center_y + dy, width - right_pad, center_y + dy, fill=CHART_GRID)

        n = len(bars)
        step_x = max(10, (width - left_pad - right_pad) / max(n, 1))
        body_half = max(2.0, min(step_x * 0.42, step_x * 0.18 + width_adjust_px))
        wick_offset = max(body_half + 2.0, min(step_x * 0.46, body_half + 3.0))

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

            self.canvas.create_line(x - wick_offset, p1_high_y, x - wick_offset, p1_low_y, fill=p1_color, width=1)
            self.canvas.create_line(x + wick_offset, p2_high_y, x + wick_offset, p2_low_y, fill=p2_color, width=1)

            self._draw_body(x - wick_offset, center_y, p1_close_y, body_half, p1_color)
            self._draw_body(x + wick_offset, center_y, p2_close_y, body_half, p2_color)

        mode_text = "с коэф" if divergence_stats.uses_ratio else "реал"
        divergence_text = (
            f"Δ режим: {mode_text}\n"
            f"Лента Δ: {divergence_stats.total_diff_pips:+.2f} п\n"
            f"Текущая свеча Δ: {divergence_stats.current_bar_diff_pips:+.2f} п\n"
            f"Live bid Δ: {divergence_stats.live_diff_pips:+.2f} п"
        )

        self.canvas.create_text(left_pad, 10, anchor="nw", fill=CHART_TEXT, font=("Segoe UI", 10, "bold"), text=symbol_1)
        self.canvas.create_text(width / 2, 10, anchor="n", fill=CHART_TEXT, font=("Segoe UI", 10), text="свечи рядом, без зеркала")
        self.canvas.create_text(width - right_pad, 10, anchor="ne", fill=CHART_TEXT, font=("Segoe UI", 10, "bold"), justify="right", text=divergence_text)

        self.canvas.create_text(
            width - right_pad,
            height - 10,
            anchor="se",
            fill=CHART_TEXT,
            font=("Segoe UI", 9),
            text=f"{symbol_2} | scale coef 1/2 = {ratio_1_to_2:.6f} | width={width_adjust_px:+d}px | height={height_adjust_px:+d}px",
        )

    def _draw_body(self, x: float, y_open: float, y_close: float, half_width: float, color: str) -> None:
        top = min(y_open, y_close)
        bottom = max(y_open, y_close)

        if abs(bottom - top) < 2:
            self.canvas.create_line(x - half_width, y_close, x + half_width, y_close, fill=color, width=3)
            return

        self.canvas.create_rectangle(
            x - half_width,
            top,
            x + half_width,
            bottom,
            outline=color,
            fill=color,
        )
