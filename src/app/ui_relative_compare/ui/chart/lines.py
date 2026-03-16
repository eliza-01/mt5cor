from __future__ import annotations

import pandas as pd
import tkinter as tk

from src.app.ui_relative_compare.constants import CHART_AXIS, CHART_BG, CHART_GRID
from .layout import LEFT_PAD, RIGHT_PAD, pair_layout, pair_positions, pair_total_width
from .selection import draw_selection_on_line


def render_relative_lines(canvas: tk.Canvas, line_1: pd.Series, line_2: pd.Series, width_adjust_px: int, pair_gap_adjust_px: int, selected_start_index: int | None, selected_end_index: int | None, colors: dict[str, str], line_zoom: float) -> None:
    canvas.update_idletasks()
    viewport_width = max(canvas.winfo_width(), 400)
    height = max(canvas.winfo_height(), 120)
    viewport_left = float(canvas.canvasx(0))
    viewport_right = viewport_left + float(viewport_width)

    canvas.delete("all")
    canvas.create_rectangle(viewport_left, 0, viewport_right, height, fill=CHART_BG, outline=CHART_BG)

    top_pad = 18
    bottom_pad = 22
    n = max(len(line_1), len(line_2))
    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
    total_width = max(viewport_width, LEFT_PAD + pair_total_width(n, layout.pair_width, layout.pair_gap) + RIGHT_PAD)

    max_abs = 1.0
    if not line_1.empty:
        max_abs = max(max_abs, float(line_1.abs().max()))
    if not line_2.empty:
        max_abs = max(max_abs, float(line_2.abs().max()))

    mid_y = height / 2
    usable_half = max(20.0, (height - top_pad - bottom_pad) / 2)
    scale = usable_half / (max_abs * 1.1)
    scale *= max(0.2, min(8.0, float(line_zoom or 1.0)))

    canvas.create_line(LEFT_PAD, mid_y, total_width - RIGHT_PAD, mid_y, fill=CHART_AXIS, width=1)
    canvas.create_text(12, mid_y, anchor="w", text="0", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))

    for level in [0.5, 1.0]:
        dy = max_abs * (usable_half / (max_abs * 1.1)) * level
        canvas.create_line(LEFT_PAD, mid_y - dy, total_width - RIGHT_PAD, mid_y - dy, fill=CHART_GRID)
        canvas.create_line(LEFT_PAD, mid_y + dy, total_width - RIGHT_PAD, mid_y + dy, fill=CHART_GRID)

    points_1: list[float] = []
    points_2: list[float] = []
    for i in range(n):
        _, _, pair_center_x = pair_positions(i, LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)
        points_1.extend([pair_center_x, mid_y - float(line_1.iloc[i]) * scale])
        points_2.extend([pair_center_x, mid_y - float(line_2.iloc[i]) * scale])

    if len(points_1) >= 4:
        canvas.create_line(*points_1, fill=colors["pair_1_up"], width=1, smooth=False)
    elif len(points_1) == 2:
        canvas.create_oval(points_1[0] - 1, points_1[1] - 1, points_1[0] + 1, points_1[1] + 1, fill=colors["pair_1_up"], outline=colors["pair_1_up"])

    if len(points_2) >= 4:
        canvas.create_line(*points_2, fill=colors["pair_2_up"], width=1, smooth=False)
    elif len(points_2) == 2:
        canvas.create_oval(points_2[0] - 1, points_2[1] - 1, points_2[0] + 1, points_2[1] + 1, fill=colors["pair_2_up"], outline=colors["pair_2_up"])

    draw_selection_on_line(canvas=canvas, line_1=line_1, line_2=line_2, body_half=layout.body_half, pair_gap=layout.pair_gap, pair_width=layout.pair_width, mid_y=mid_y, scale=scale, height=height, selected_start_index=selected_start_index, selected_end_index=selected_end_index)
    canvas.configure(scrollregion=(0, 0, total_width, height))
