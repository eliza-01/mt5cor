from __future__ import annotations

import pandas as pd
import tkinter as tk

from src.app.ui_relative_compare.constants import CHART_AXIS, CHART_BG, CHART_GRID, CHART_TEXT
from src.app.ui_relative_compare.domain.models import FlowDiagnostics, LiveTailSnapshot
from .layout import LEFT_PAD, RIGHT_PAD, pair_layout, pair_positions, pair_total_width
from .selection import draw_selection_on_line


LINE_1_COLOR = "#22c55e"
LINE_2_COLOR = "#f59e0b"
DIFF_COLOR = "#6b7280"
LIVE_TAIL_TAG = "live_tail"


def _normalize(series: pd.Series) -> pd.Series:
    return pd.Series(series, dtype=float).reset_index(drop=True)


def _format(value: float) -> str:
    text = f"{float(value):+.2f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _plot_base(line_1: pd.Series, line_2: pd.Series, diff: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    midpoint = ((line_1 + line_2) / 2.0).astype(float)
    return (line_1 - midpoint).astype(float), (line_2 - midpoint).astype(float), diff.astype(float)


def _extend_points(series: pd.Series, mid_y: float, scale: float, width_adjust_px: int, pair_gap_adjust_px: int) -> tuple[list[float], float]:
    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
    points: list[float] = []
    last_center_x = 0.0
    for i in range(len(series)):
        _, _, pair_center_x = pair_positions(i, LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)
        y = mid_y - float(series.iloc[i]) * scale
        points.extend([pair_center_x, y])
        last_center_x = float(pair_center_x)
    return points, last_center_x


def update_live_tail_on_lines(
    canvas: tk.Canvas,
    line_1: pd.Series,
    line_2: pd.Series,
    diff: pd.Series,
    flow_diagnostics: FlowDiagnostics,
    live_tail: LiveTailSnapshot | None,
    width_adjust_px: int,
    pair_gap_adjust_px: int,
    line_zoom: float,
) -> None:
    canvas.update_idletasks()
    viewport_width = max(canvas.winfo_width(), 400)
    height = max(canvas.winfo_height(), 140)
    viewport_left = float(canvas.canvasx(0))
    viewport_right = viewport_left + float(viewport_width)

    line_1 = _normalize(line_1)
    line_2 = _normalize(line_2)
    diff = _normalize(diff)

    plot_1, plot_2, plot_diff = _plot_base(line_1, line_2, diff)
    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)

    max_abs = 1.0
    series_for_scale = [plot_1, plot_2, plot_diff]
    if not plot_diff.empty:
        for series in series_for_scale:
            max_abs = max(max_abs, float(series.abs().max()))
    elif live_tail is not None:
        max_abs = max(
            max_abs,
            abs(float(live_tail.flow_diagnostics.line_1_last)),
            abs(float(live_tail.flow_diagnostics.line_2_last)),
            abs(float(live_tail.flow_diagnostics.diff_last)),
        )

    top_pad = 18
    bottom_pad = 22
    mid_y = height / 2
    usable_half = max(22.0, (height - top_pad - bottom_pad) / 2)
    scale = usable_half / (max_abs * 1.1)
    scale *= max(0.2, min(8.0, float(line_zoom or 1.0)))

    total_count = len(plot_diff) + (1 if live_tail is not None and not live_tail.bar.empty else 0)
    total_width = max(viewport_width, LEFT_PAD + pair_total_width(total_count, layout.pair_width, layout.pair_gap) + RIGHT_PAD)

    canvas.delete(LIVE_TAIL_TAG)

    display_flow = live_tail.flow_diagnostics if live_tail is not None else flow_diagnostics
    canvas.create_text(
        viewport_left + 10,
        8,
        anchor="nw",
        fill=CHART_TEXT,
        font=("Segoe UI", 9),
        tags=(LIVE_TAIL_TAG,),
        text=(
            f"ход 1 (green) | ход 2 (orange) | diff (gray) | "
            f"long coef={display_flow.applied_ratio_long:.3f} short coef={display_flow.applied_ratio_short:.3f} | "
            f"diff={_format(display_flow.diff_last)}"
        ),
    )

    last_x_for_text = 0.0
    if not plot_diff.empty:
        _, last_x_for_text = _extend_points(plot_diff, mid_y, scale, width_adjust_px, pair_gap_adjust_px)

    if live_tail is not None and not live_tail.bar.empty:
        preview_index = len(plot_diff)
        _, _, preview_x = pair_positions(preview_index, LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)

        preview_mid = (float(display_flow.line_1_last) + float(display_flow.line_2_last)) / 2.0
        preview_y_1 = mid_y - (float(display_flow.line_1_last) - preview_mid) * scale
        preview_y_2 = mid_y - (float(display_flow.line_2_last) - preview_mid) * scale
        preview_y_diff = mid_y - float(display_flow.diff_last) * scale

        if len(plot_diff) > 0:
            _, _, last_center_x = pair_positions(len(plot_diff) - 1, LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)
            last_y_1 = mid_y - float(plot_1.iloc[-1]) * scale
            last_y_2 = mid_y - float(plot_2.iloc[-1]) * scale
            last_y_diff = mid_y - float(plot_diff.iloc[-1]) * scale

            canvas.create_line(last_center_x, last_y_1, preview_x, preview_y_1, fill=LINE_1_COLOR, width=2, tags=(LIVE_TAIL_TAG,))
            canvas.create_line(last_center_x, last_y_2, preview_x, preview_y_2, fill=LINE_2_COLOR, width=2, tags=(LIVE_TAIL_TAG,))
            canvas.create_line(last_center_x, last_y_diff, preview_x, preview_y_diff, fill=DIFF_COLOR, width=1, tags=(LIVE_TAIL_TAG,))
        else:
            canvas.create_line(preview_x, mid_y, preview_x, preview_y_1, fill=LINE_1_COLOR, width=2, tags=(LIVE_TAIL_TAG,))
            canvas.create_line(preview_x, mid_y, preview_x, preview_y_2, fill=LINE_2_COLOR, width=2, tags=(LIVE_TAIL_TAG,))
            canvas.create_line(preview_x, mid_y, preview_x, preview_y_diff, fill=DIFF_COLOR, width=1, tags=(LIVE_TAIL_TAG,))

        last_x_for_text = preview_x
        if live_tail.aggregate_progress and live_tail.aggregate_progress != "1/1":
            canvas.create_text(
                preview_x,
                height - 10,
                anchor="s",
                fill=CHART_TEXT,
                font=("Segoe UI", 9),
                tags=(LIVE_TAIL_TAG,),
                text=live_tail.aggregate_progress,
            )

    if total_count > 0:
        canvas.create_text(
            last_x_for_text,
            16,
            anchor="n",
            fill=CHART_TEXT,
            font=("Segoe UI", 10, "bold"),
            tags=(LIVE_TAIL_TAG,),
            text=f"{_format(display_flow.line_1_last)} | {_format(display_flow.line_2_last)} | diff {_format(display_flow.diff_last)}",
        )

    canvas.configure(scrollregion=(0, 0, total_width, height))


def render_relative_lines(
    canvas: tk.Canvas,
    line_1: pd.Series,
    line_2: pd.Series,
    diff: pd.Series,
    width_adjust_px: int,
    pair_gap_adjust_px: int,
    selected_start_index: int | None,
    selected_end_index: int | None,
    colors: dict[str, str],
    line_zoom: float,
    flow_diagnostics: FlowDiagnostics,
    live_tail: LiveTailSnapshot | None,
) -> None:
    canvas.update_idletasks()
    viewport_width = max(canvas.winfo_width(), 400)
    height = max(canvas.winfo_height(), 140)
    viewport_left = float(canvas.canvasx(0))
    viewport_right = viewport_left + float(viewport_width)

    canvas.delete("all")
    canvas.create_rectangle(viewport_left, 0, viewport_right, height, fill=CHART_BG, outline=CHART_BG)

    line_1 = _normalize(line_1)
    line_2 = _normalize(line_2)
    diff = _normalize(diff)

    plot_1, plot_2, plot_diff = _plot_base(line_1, line_2, diff)

    top_pad = 18
    bottom_pad = 22
    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
    total_count = len(plot_diff) + (1 if live_tail is not None and not live_tail.bar.empty else 0)
    total_width = max(viewport_width, LEFT_PAD + pair_total_width(total_count, layout.pair_width, layout.pair_gap) + RIGHT_PAD)

    max_abs = 1.0
    for series in (plot_1, plot_2, plot_diff):
        if not series.empty:
            max_abs = max(max_abs, float(series.abs().max()))

    mid_y = height / 2
    usable_half = max(22.0, (height - top_pad - bottom_pad) / 2)
    scale = usable_half / (max_abs * 1.1)
    scale *= max(0.2, min(8.0, float(line_zoom or 1.0)))

    canvas.create_line(LEFT_PAD, mid_y, total_width - RIGHT_PAD, mid_y, fill=CHART_AXIS, width=1)
    canvas.create_text(12, mid_y, anchor="w", text="0", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))
    for level in [0.5, 1.0]:
        dy = max_abs * (usable_half / (max_abs * 1.1)) * level
        canvas.create_line(LEFT_PAD, mid_y - dy, total_width - RIGHT_PAD, mid_y - dy, fill=CHART_GRID)
        canvas.create_line(LEFT_PAD, mid_y + dy, total_width - RIGHT_PAD, mid_y + dy, fill=CHART_GRID)

    diff_points, _ = _extend_points(plot_diff, mid_y, scale, width_adjust_px, pair_gap_adjust_px)
    line_1_points, _ = _extend_points(plot_1, mid_y, scale, width_adjust_px, pair_gap_adjust_px)
    line_2_points, _ = _extend_points(plot_2, mid_y, scale, width_adjust_px, pair_gap_adjust_px)

    if len(diff_points) >= 4:
        canvas.create_line(*diff_points, fill=DIFF_COLOR, width=1, smooth=False)
    if len(line_1_points) >= 4:
        canvas.create_line(*line_1_points, fill=LINE_1_COLOR, width=2, smooth=False)
    if len(line_2_points) >= 4:
        canvas.create_line(*line_2_points, fill=LINE_2_COLOR, width=2, smooth=False)

    draw_selection_on_line(
        canvas=canvas,
        line_1=plot_1,
        line_2=plot_2,
        body_half=layout.body_half,
        pair_gap=layout.pair_gap,
        pair_width=layout.pair_width,
        mid_y=mid_y,
        scale=scale,
        height=height,
        selected_start_index=selected_start_index,
        selected_end_index=selected_end_index,
    )

    update_live_tail_on_lines(
        canvas=canvas,
        line_1=line_1,
        line_2=line_2,
        diff=diff,
        flow_diagnostics=flow_diagnostics,
        live_tail=live_tail,
        width_adjust_px=width_adjust_px,
        pair_gap_adjust_px=pair_gap_adjust_px,
        line_zoom=line_zoom,
    )