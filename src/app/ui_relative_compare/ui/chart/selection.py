from __future__ import annotations

import pandas as pd
import tkinter as tk

from .layout import LEFT_PAD, pair_positions
from .primitives import draw_marker


def draw_selection_on_candles(canvas: tk.Canvas, bars: pd.DataFrame, body_half: float, pair_gap: float, pair_width: float, center_y: float, scale: float, height: float, top_pad: float, bottom_pad: float, selected_start_index: int | None, selected_end_index: int | None) -> None:
    if selected_start_index is None or bars.empty:
        return

    start_index = max(0, min(len(bars) - 1, int(selected_start_index)))
    end_index = start_index if selected_end_index is None else max(0, min(len(bars) - 1, int(selected_end_index)))
    if end_index < start_index:
        start_index, end_index = end_index, start_index

    start_p1_x, start_p2_x, start_center_x = pair_positions(start_index, LEFT_PAD, body_half, pair_gap, pair_width)
    end_p1_x, end_p2_x, end_center_x = pair_positions(end_index, LEFT_PAD, body_half, pair_gap, pair_width)

    start_left = start_p1_x - body_half - 4
    end_right = end_p2_x + body_half + 4

    if end_index > start_index:
        canvas.create_rectangle(start_left, top_pad - 8, end_right, height - bottom_pad + 4, outline="#a78bfa", dash=(5, 3), width=1)

    canvas.create_line(start_center_x, top_pad - 10, start_center_x, height - bottom_pad + 6, fill="#22c55e", dash=(4, 3), width=2)
    canvas.create_text(start_center_x, top_pad - 16, anchor="s", fill="#22c55e", font=("Segoe UI", 9, "bold"), text="START")

    if selected_end_index is not None:
        canvas.create_line(end_center_x, top_pad - 10, end_center_x, height - bottom_pad + 6, fill="#ef4444", dash=(4, 3), width=2)
        canvas.create_text(end_center_x, top_pad - 16, anchor="s", fill="#ef4444", font=("Segoe UI", 9, "bold"), text="END")

    start_row = bars.iloc[start_index]
    draw_marker(canvas, start_p1_x, center_y - float(start_row["p1_close"]) * scale, "#22c55e")
    draw_marker(canvas, start_p2_x, center_y - float(start_row["p2_close"]) * scale, "#22c55e")

    if selected_end_index is not None:
        end_row = bars.iloc[end_index]
        draw_marker(canvas, end_p1_x, center_y - float(end_row["p1_close"]) * scale, "#ef4444")
        draw_marker(canvas, end_p2_x, center_y - float(end_row["p2_close"]) * scale, "#ef4444")


def draw_selection_on_line(canvas: tk.Canvas, line_1: pd.Series, line_2: pd.Series, body_half: float, pair_gap: float, pair_width: float, mid_y: float, scale: float, height: float, selected_start_index: int | None, selected_end_index: int | None) -> None:
    if selected_start_index is None or line_1.empty or line_2.empty:
        return

    limit = min(len(line_1), len(line_2)) - 1
    start_index = max(0, min(limit, int(selected_start_index)))
    end_index = start_index if selected_end_index is None else max(0, min(limit, int(selected_end_index)))
    if end_index < start_index:
        start_index, end_index = end_index, start_index

    _, _, start_center_x = pair_positions(start_index, LEFT_PAD, body_half, pair_gap, pair_width)
    _, _, end_center_x = pair_positions(end_index, LEFT_PAD, body_half, pair_gap, pair_width)

    start_y_1 = mid_y - float(line_1.iloc[start_index]) * scale
    start_y_2 = mid_y - float(line_2.iloc[start_index]) * scale
    end_y_1 = mid_y - float(line_1.iloc[end_index]) * scale
    end_y_2 = mid_y - float(line_2.iloc[end_index]) * scale

    if end_index > start_index:
        canvas.create_rectangle(start_center_x - pair_width / 2.0, 10, end_center_x + pair_width / 2.0, height - 10, outline="#a78bfa", dash=(5, 3), width=1)

    canvas.create_line(start_center_x, 8, start_center_x, height - 8, fill="#22c55e", dash=(4, 3), width=2)
    draw_marker(canvas, start_center_x, start_y_1, "#22c55e")
    draw_marker(canvas, start_center_x, start_y_2, "#22c55e")

    if selected_end_index is not None:
        canvas.create_line(end_center_x, 8, end_center_x, height - 8, fill="#ef4444", dash=(4, 3), width=2)
        draw_marker(canvas, end_center_x, end_y_1, "#ef4444")
        draw_marker(canvas, end_center_x, end_y_2, "#ef4444")
