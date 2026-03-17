from __future__ import annotations

import pandas as pd
import tkinter as tk

from src.app.ui_relative_compare.constants import CHART_AXIS, CHART_BG, CHART_GRID, CHART_TEXT
from src.app.ui_relative_compare.domain.models import LiveTailSnapshot, TradePlan
from .layout import LEFT_PAD, RIGHT_PAD, pair_layout, pair_positions, pair_total_width
from .primitives import draw_body
from .selection import draw_selection_on_candles


LIVE_TAIL_TAG = "live_tail"


def _max_abs_for_scale(bars: pd.DataFrame, live_tail: LiveTailSnapshot | None) -> float:
    frames: list[pd.DataFrame] = []
    if not bars.empty:
        frames.append(bars)
    elif live_tail is not None and not live_tail.bar.empty:
        frames.append(live_tail.bar)

    max_abs = 1.0
    for frame in frames:
        for col in ["p1_high", "p1_low", "p1_close", "p2_high", "p2_low", "p2_close"]:
            val = frame[col].abs().max()
            if pd.notna(val):
                max_abs = max(max_abs, float(val))
    return max_abs


def _draw_bar(canvas: tk.Canvas, row, index: int, center_y: float, scale: float, layout, colors: dict[str, str], tags=()) -> None:
    p1_x, p2_x, _ = pair_positions(index, LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)

    p1_high_y = center_y - float(row["p1_high"]) * scale
    p1_low_y = center_y - float(row["p1_low"]) * scale
    p1_close_y = center_y - float(row["p1_close"]) * scale

    p2_high_y = center_y - float(row["p2_high"]) * scale
    p2_low_y = center_y - float(row["p2_low"]) * scale
    p2_close_y = center_y - float(row["p2_close"]) * scale

    p1_color = colors["pair_1_up"] if float(row["p1_close"]) >= 0 else colors["pair_1_down"]
    p2_color = colors["pair_2_up"] if float(row["p2_close"]) >= 0 else colors["pair_2_down"]

    canvas.create_line(p1_x, p1_high_y, p1_x, p1_low_y, fill=p1_color, width=1, tags=tags)
    canvas.create_line(p2_x, p2_high_y, p2_x, p2_low_y, fill=p2_color, width=1, tags=tags)
    draw_body(canvas, p1_x, center_y, p1_close_y, layout.body_half, p1_color)
    draw_body(canvas, p2_x, center_y, p2_close_y, layout.body_half, p2_color)


def update_live_tail_on_candles(
    canvas: tk.Canvas,
    bars: pd.DataFrame,
    trade_plan: TradePlan,
    live_tail: LiveTailSnapshot | None,
    width_adjust_px: int,
    height_adjust_px: int,
    pair_gap_adjust_px: int,
) -> None:
    canvas.update_idletasks()
    viewport_width = max(canvas.winfo_width(), 400)
    height = max(canvas.winfo_height(), 240)
    viewport_left = float(canvas.canvasx(0))
    viewport_right = viewport_left + float(viewport_width)

    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
    total_count = len(bars) + (1 if live_tail is not None and not live_tail.bar.empty else 0)
    total_width = max(viewport_width, LEFT_PAD + pair_total_width(total_count, layout.pair_width, layout.pair_gap) + RIGHT_PAD)

    center_y = height / 2
    top_pad = 40
    bottom_pad = 34
    usable_half = max(40.0, (height - top_pad - bottom_pad) / 2 - 10)

    max_abs = _max_abs_for_scale(bars, live_tail)
    base_scale = usable_half / (max_abs * 1.15)
    scale = max(0.5, base_scale + height_adjust_px)

    canvas.delete(LIVE_TAIL_TAG)

    active_plan = live_tail.trade_plan if live_tail is not None else trade_plan
    canvas.create_text(
        viewport_right - 16,
        height - 10,
        anchor="se",
        fill=CHART_TEXT,
        font=("Segoe UI", 9),
        tags=(LIVE_TAIL_TAG,),
        text=f"lots: {active_plan.symbol_1_lots:.2f} / {active_plan.symbol_2_lots:.2f}",
    )

    if live_tail is not None and not live_tail.bar.empty:
        _draw_bar(
            canvas=canvas,
            row=live_tail.bar.iloc[0],
            index=len(bars),
            center_y=center_y,
            scale=scale,
            layout=layout,
            colors={"pair_1_up": "#34d399", "pair_1_down": "#f87171", "pair_2_up": "#60a5fa", "pair_2_down": "#f59e0b"},
            tags=(LIVE_TAIL_TAG,),
        )
        _, _, preview_center_x = pair_positions(len(bars), LEFT_PAD, layout.body_half, layout.pair_gap, layout.pair_width)
        if live_tail.aggregate_progress and live_tail.aggregate_progress != "1/1":
            canvas.create_text(
                preview_center_x,
                height - 12,
                anchor="s",
                fill=CHART_TEXT,
                font=("Segoe UI", 9),
                tags=(LIVE_TAIL_TAG,),
                text=live_tail.aggregate_progress,
            )

    canvas.configure(scrollregion=(0, 0, total_width, height))


def render_candles(
    canvas: tk.Canvas,
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
    live_tail: LiveTailSnapshot | None,
) -> None:
    canvas.update_idletasks()
    viewport_width = max(canvas.winfo_width(), 400)
    height = max(canvas.winfo_height(), 240)
    viewport_left = float(canvas.canvasx(0))
    viewport_right = viewport_left + float(viewport_width)

    canvas.delete("all")
    canvas.create_rectangle(viewport_left, 0, viewport_right, height, fill=CHART_BG, outline=CHART_BG)

    center_y = height / 2
    top_pad = 40
    bottom_pad = 34

    layout = pair_layout(width_adjust_px, pair_gap_adjust_px)
    total_count = len(bars) + (1 if live_tail is not None and not live_tail.bar.empty else 0)
    total_width = max(viewport_width, LEFT_PAD + pair_total_width(total_count, layout.pair_width, layout.pair_gap) + RIGHT_PAD)

    max_abs = _max_abs_for_scale(bars, live_tail)
    usable_half = max(40.0, (height - top_pad - bottom_pad) / 2 - 10)
    base_scale = usable_half / (max_abs * 1.15)
    scale = max(0.5, base_scale + height_adjust_px)

    canvas.create_line(LEFT_PAD, center_y, total_width - RIGHT_PAD, center_y, fill=CHART_AXIS, width=1)
    canvas.create_text(12, center_y, anchor="w", text="OPEN", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))

    for level in [0.25, 0.5, 0.75, 1.0]:
        dy = max_abs * base_scale * level
        canvas.create_line(LEFT_PAD, center_y - dy, total_width - RIGHT_PAD, center_y - dy, fill=CHART_GRID)
        canvas.create_line(LEFT_PAD, center_y + dy, total_width - RIGHT_PAD, center_y + dy, fill=CHART_GRID)

    for i, row in bars.iterrows():
        _draw_bar(canvas, row, i, center_y, scale, layout, colors)

    draw_selection_on_candles(
        canvas=canvas,
        bars=bars,
        body_half=layout.body_half,
        pair_gap=layout.pair_gap,
        pair_width=layout.pair_width,
        center_y=center_y,
        scale=scale,
        height=height,
        top_pad=top_pad,
        bottom_pad=bottom_pad,
        selected_start_index=selected_start_index,
        selected_end_index=selected_end_index,
    )

    relation_text = "авто-инверсия 2-й пары" if invert_second else "одна направленность"
    canvas.create_text(
        viewport_left + 12,
        8,
        anchor="nw",
        fill=CHART_TEXT,
        font=("Segoe UI", 10),
        text=f"{symbol_1} vs {symbol_2} | {relation_text}",
    )

    canvas.create_text(
        viewport_right - 16,
        height - 26,
        anchor="se",
        fill=CHART_TEXT,
        font=("Segoe UI", 9),
        text=f"width={width_adjust_px:+d}px | height={height_adjust_px:+d}px | pair_gap={pair_gap_adjust_px:+d}px",
    )

    update_live_tail_on_candles(
        canvas=canvas,
        bars=bars,
        trade_plan=trade_plan,
        live_tail=live_tail,
        width_adjust_px=width_adjust_px,
        height_adjust_px=height_adjust_px,
        pair_gap_adjust_px=pair_gap_adjust_px,
    )