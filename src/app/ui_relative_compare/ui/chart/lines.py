from __future__ import annotations

import pandas as pd
import tkinter as tk

from src.app.ui_relative_compare.constants import CHART_AXIS, CHART_BG, CHART_GRID, CHART_TEXT
from .layout import LEFT_PAD, RIGHT_PAD, pair_layout, pair_positions, pair_total_width
from .selection import draw_selection_on_line


GAP_COLOR = "#6b7280"
FAST_COLOR = "#22c55e"
SLOW_COLOR = "#f59e0b"
DIFF_COLOR = "#22c55e"


def _normalize(series: pd.Series) -> pd.Series:
    return pd.Series(series, dtype=float).reset_index(drop=True)


def _extend_points(
    series: pd.Series,
    mid_y: float,
    scale: float,
    n: int,
    width_adjust_px: int,
    pair_gap_adjust_px: int,
) -> tuple[list[float], float, float]:
    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
    points: list[float] = []
    last_center_x = 0.0
    last_y = mid_y
    for i in range(n):
        _, _, pair_center_x = pair_positions(i, LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)
        y = mid_y - float(series.iloc[i]) * scale
        points.extend([pair_center_x, y])
        last_center_x = float(pair_center_x)
        last_y = float(y)
    return points, last_center_x, last_y


def _plot_gap_ma_mode(gap: pd.Series, fast_ma: pd.Series, slow_ma: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    midpoint = ((fast_ma + slow_ma) / 2.0).astype(float)
    plot_gap = (gap - midpoint).astype(float)
    plot_fast = (fast_ma - midpoint).astype(float)
    plot_slow = (slow_ma - midpoint).astype(float)
    return plot_gap, plot_fast, plot_slow


def _plot_gap_diff_mode(gap: pd.Series, fast_ma: pd.Series, slow_ma: pd.Series) -> tuple[pd.Series, pd.Series]:
    diff = (fast_ma - slow_ma).astype(float)
    return gap.astype(float), diff


def render_relative_lines(
    canvas: tk.Canvas,
    gap: pd.Series,
    fast_ma: pd.Series,
    slow_ma: pd.Series,
    width_adjust_px: int,
    pair_gap_adjust_px: int,
    selected_start_index: int | None,
    selected_end_index: int | None,
    colors: dict[str, str],
    line_zoom: float,
    entry_threshold: float,
    exit_threshold: float,
    chart_mode: str,
    aggregate_progress_text: str | None,
) -> None:
    canvas.update_idletasks()
    viewport_width = max(canvas.winfo_width(), 400)
    height = max(canvas.winfo_height(), 120)
    viewport_left = float(canvas.canvasx(0))
    viewport_right = viewport_left + float(viewport_width)

    canvas.delete("all")
    canvas.create_rectangle(viewport_left, 0, viewport_right, height, fill=CHART_BG, outline=CHART_BG)

    gap = _normalize(gap)
    fast_ma = _normalize(fast_ma)
    slow_ma = _normalize(slow_ma)

    top_pad = 18
    bottom_pad = 22
    n = len(gap)
    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
    total_width = max(viewport_width, LEFT_PAD + pair_total_width(n, layout.pair_width, layout.pair_gap) + RIGHT_PAD)

    mode = chart_mode if chart_mode in {"gap_ma", "gap_diff"} else "gap_ma"
    if mode == "gap_diff":
        plot_gap, plot_diff = _plot_gap_diff_mode(gap, fast_ma, slow_ma)
        plot_slow = pd.Series(dtype=float)
        series_for_scale = [plot_gap, plot_diff]
    else:
        plot_gap, plot_fast, plot_slow = _plot_gap_ma_mode(gap, fast_ma, slow_ma)
        series_for_scale = [plot_gap, plot_fast, plot_slow]

    max_abs = 1.0
    for series in series_for_scale:
        if not series.empty:
            max_abs = max(max_abs, float(series.abs().max()))

    if mode == "gap_diff":
        max_abs = max(max_abs, abs(float(entry_threshold)), abs(float(exit_threshold)))

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

    if mode == "gap_diff":
        entry_y_top = mid_y - float(entry_threshold) * scale
        entry_y_bottom = mid_y + float(entry_threshold) * scale
        exit_y_top = mid_y - float(exit_threshold) * scale
        exit_y_bottom = mid_y + float(exit_threshold) * scale
        canvas.create_line(LEFT_PAD, entry_y_top, total_width - RIGHT_PAD, entry_y_top, fill="#7f1d1d", dash=(4, 3))
        canvas.create_line(LEFT_PAD, entry_y_bottom, total_width - RIGHT_PAD, entry_y_bottom, fill="#7f1d1d", dash=(4, 3))
        canvas.create_line(LEFT_PAD, exit_y_top, total_width - RIGHT_PAD, exit_y_top, fill="#1f2937", dash=(2, 3))
        canvas.create_line(LEFT_PAD, exit_y_bottom, total_width - RIGHT_PAD, exit_y_bottom, fill="#1f2937", dash=(2, 3))

    gap_points, _, _ = _extend_points(plot_gap, mid_y, scale, n, width_adjust_px, pair_gap_adjust_px)
    if len(gap_points) >= 4:
        canvas.create_line(*gap_points, fill=GAP_COLOR, width=1, smooth=False)

    if mode == "gap_diff":
        diff_points, _, _ = _extend_points(plot_diff, mid_y, scale, n, width_adjust_px, pair_gap_adjust_px)
        if len(diff_points) >= 4:
            canvas.create_line(*diff_points, fill=DIFF_COLOR, width=2, smooth=False)

        draw_selection_on_line(
            canvas=canvas,
            line_1=plot_gap,
            line_2=plot_diff,
            body_half=layout.body_half,
            pair_gap=layout.pair_gap,
            pair_width=layout.pair_width,
            mid_y=mid_y,
            scale=scale,
            height=height,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
        )
    else:
        fast_points, _, _ = _extend_points(plot_fast, mid_y, scale, n, width_adjust_px, pair_gap_adjust_px)
        slow_points, _, _ = _extend_points(plot_slow, mid_y, scale, n, width_adjust_px, pair_gap_adjust_px)

        if len(fast_points) >= 4:
            canvas.create_line(*fast_points, fill=FAST_COLOR, width=2, smooth=False)
        if len(slow_points) >= 4:
            canvas.create_line(*slow_points, fill=SLOW_COLOR, width=2, smooth=False)

        draw_selection_on_line(
            canvas=canvas,
            line_1=plot_fast,
            line_2=plot_slow,
            body_half=layout.body_half,
            pair_gap=layout.pair_gap,
            pair_width=layout.pair_width,
            mid_y=mid_y,
            scale=scale,
            height=height,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
        )

    if aggregate_progress_text and aggregate_progress_text != "1/1" and n > 0:
        _, _, last_center_x = pair_positions(n - 1, LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)
        canvas.create_text(
            last_center_x,
            height - 10,
            anchor="s",
            fill=CHART_TEXT,
            font=("Segoe UI", 9),
            text=aggregate_progress_text,
        )

    canvas.configure(scrollregion=(0, 0, total_width, height))