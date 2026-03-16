from __future__ import annotations

import pandas as pd
import tkinter as tk

from src.app.ui_relative_compare.constants import CHART_AXIS, CHART_BG, CHART_GRID, CHART_TEXT
from src.app.ui_relative_compare.domain import TradePlan
from .layout import LEFT_PAD, RIGHT_PAD, pair_layout, pair_positions, pair_total_width
from .primitives import draw_body, draw_buy_arrow, draw_sell_arrow
from .selection import draw_selection_on_candles


def render_candles(canvas: tk.Canvas, bars: pd.DataFrame, symbol_1: str, symbol_2: str, ratio_1_to_2: float, width_adjust_px: int, height_adjust_px: int, pair_gap_adjust_px: int, trade_plan: TradePlan, selected_start_index: int | None, selected_end_index: int | None, colors: dict[str, str]) -> None:
    canvas.update_idletasks()
    viewport_width = max(canvas.winfo_width(), 400)
    height = max(canvas.winfo_height(), 240)
    viewport_left = float(canvas.canvasx(0))
    viewport_right = viewport_left + float(viewport_width)

    canvas.delete("all")
    canvas.create_rectangle(viewport_left, 0, viewport_right, height, fill=CHART_BG, outline=CHART_BG)

    center_y = height / 2
    top_pad = 56
    bottom_pad = 34

    n = len(bars)
    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
    total_width = max(viewport_width, LEFT_PAD + pair_total_width(n, layout.pair_width, layout.pair_gap) + RIGHT_PAD)

    max_abs = 1.0
    for col in ["p1_high", "p1_low", "p1_close", "p2_high", "p2_low", "p2_close"]:
        val = bars[col].abs().max()
        if pd.notna(val):
            max_abs = max(max_abs, float(val))

    usable_half = max(40.0, (height - top_pad - bottom_pad) / 2 - 10)
    base_scale = usable_half / (max_abs * 1.15)
    scale = max(0.5, base_scale + height_adjust_px)

    canvas.create_line(LEFT_PAD, center_y, total_width - RIGHT_PAD, center_y, fill=CHART_AXIS, width=1)
    canvas.create_text(12, center_y, anchor="w", text="OPEN", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))

    for level in [0.25, 0.5, 0.75, 1.0]:
        dy = max_abs * base_scale * level
        canvas.create_line(LEFT_PAD, center_y - dy, total_width - RIGHT_PAD, center_y - dy, fill=CHART_GRID)
        canvas.create_line(LEFT_PAD, center_y + dy, total_width - RIGHT_PAD, center_y + dy, fill=CHART_GRID)

    last_points: list[dict[str, float]] = []
    for i, row in bars.iterrows():
        p1_x, p2_x, _ = pair_positions(i, LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)
        p1_high_y = center_y - float(row["p1_high"]) * scale
        p1_low_y = center_y - float(row["p1_low"]) * scale
        p1_close_y = center_y - float(row["p1_close"]) * scale
        p2_high_y = center_y - float(row["p2_high"]) * scale
        p2_low_y = center_y - float(row["p2_low"]) * scale
        p2_close_y = center_y - float(row["p2_close"]) * scale

        p1_color = colors["pair_1_up"] if float(row["close_1"]) >= float(row["open_1"]) else colors["pair_1_down"]
        p2_color = colors["pair_2_up"] if float(row["close_2"]) >= float(row["open_2"]) else colors["pair_2_down"]

        canvas.create_line(p1_x, p1_high_y, p1_x, p1_low_y, fill=p1_color, width=1)
        canvas.create_line(p2_x, p2_high_y, p2_x, p2_low_y, fill=p2_color, width=1)
        draw_body(canvas, p1_x, center_y, p1_close_y, layout.body_half, p1_color)
        draw_body(canvas, p2_x, center_y, p2_close_y, layout.body_half, p2_color)

        if i >= max(0, n - 2):
            last_points.append({"p1_x": p1_x, "p2_x": p2_x, "p1_high_y": p1_high_y, "p1_low_y": p1_low_y, "p2_high_y": p2_high_y, "p2_low_y": p2_low_y})

    draw_selection_on_candles(canvas=canvas, bars=bars, body_half=layout.body_half, pair_gap=layout.pair_gap, pair_width=layout.pair_width, center_y=center_y, scale=scale, height=height, top_pad=top_pad, bottom_pad=bottom_pad, selected_start_index=selected_start_index, selected_end_index=selected_end_index)

    title_x = viewport_left + viewport_width / 2.0
    canvas.create_text(title_x, 8, anchor="n", fill=CHART_TEXT, font=("Segoe UI", 10), text=f"{symbol_1} vs {symbol_2} | свечи рядом, без зеркала")

    sell_color = "#ef4444"
    buy_color = "#2563eb"
    for point in last_points:
        if trade_plan.sell_symbol == symbol_1:
            draw_sell_arrow(canvas, float(point["p1_x"]), float(point["p1_high_y"]) - 18, sell_color)
        if trade_plan.buy_symbol == symbol_1:
            draw_buy_arrow(canvas, float(point["p1_x"]), float(point["p1_low_y"]) + 18, buy_color, height)
        if trade_plan.sell_symbol == symbol_2:
            draw_sell_arrow(canvas, float(point["p2_x"]), float(point["p2_high_y"]) - 18, sell_color)
        if trade_plan.buy_symbol == symbol_2:
            draw_buy_arrow(canvas, float(point["p2_x"]), float(point["p2_low_y"]) + 18, buy_color, height)

    canvas.create_text(viewport_right - 16, height - 10, anchor="se", fill=CHART_TEXT, font=("Segoe UI", 9), text=f"{symbol_2} | scale coef 1/2 = {ratio_1_to_2:.6f} | width={width_adjust_px:+d}px | height={height_adjust_px:+d}px | pair_gap={pair_gap_adjust_px:+d}px")
    canvas.configure(scrollregion=(0, 0, total_width, height))
