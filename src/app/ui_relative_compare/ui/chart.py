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


BASE_BODY_HALF = 4.0
BASE_PAIR_GAP = 10.0
LEFT_PAD = 60
RIGHT_PAD = 30


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
        pair_gap_adjust_px: int,
        divergence_stats: DivergenceStats,
        trade_plan: TradePlan,
        selected_start_index: int | None,
        selected_end_index: int | None,
    ) -> None:
        self._draw_candles(
            bars=bars,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            ratio_1_to_2=ratio_1_to_2,
            width_adjust_px=width_adjust_px,
            height_adjust_px=height_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
            divergence_stats=divergence_stats,
            trade_plan=trade_plan,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
        )
        self._draw_divergence_line(
            divergence_series=divergence_series,
            width_adjust_px=width_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
        )

    def get_index_at_x(
        self,
        bars_count: int,
        x_world: float,
        width_adjust_px: int,
        pair_gap_adjust_px: int,
    ) -> int | None:
        if bars_count <= 0:
            return None

        body_half, pair_gap, pair_width = self._pair_layout(width_adjust_px, pair_gap_adjust_px)
        step = pair_width + pair_gap
        center_offset = LEFT_PAD + pair_width / 2.0
        raw_index = round((x_world - center_offset) / step)
        return max(0, min(bars_count - 1, int(raw_index)))

    def _pair_layout(self, width_adjust_px: int, pair_gap_adjust_px: int) -> tuple[float, float, float]:
        body_half = max(2.0, BASE_BODY_HALF + width_adjust_px * 0.35)
        pair_gap = max(0.0, BASE_PAIR_GAP + pair_gap_adjust_px)
        pair_width = body_half * 4.0
        return body_half, pair_gap, pair_width

    def _pair_total_width(self, count: int, pair_width: float, pair_gap: float) -> float:
        if count <= 0:
            return 0.0
        return count * pair_width + max(0, count - 1) * pair_gap

    def _pair_positions(
        self,
        index: int,
        left_pad: float,
        body_half: float,
        pair_gap: float,
        pair_width: float,
    ) -> tuple[float, float, float]:
        pair_left = left_pad + index * (pair_width + pair_gap)
        p1_x = pair_left + body_half
        p2_x = pair_left + body_half * 3.0
        pair_center_x = pair_left + pair_width / 2.0
        return p1_x, p2_x, pair_center_x

    def _draw_candles(
        self,
        bars: pd.DataFrame,
        symbol_1: str,
        symbol_2: str,
        ratio_1_to_2: float,
        width_adjust_px: int,
        height_adjust_px: int,
        pair_gap_adjust_px: int,
        divergence_stats: DivergenceStats,
        trade_plan: TradePlan,
        selected_start_index: int | None,
        selected_end_index: int | None,
    ) -> None:
        self.candle_canvas.update_idletasks()
        viewport_width = max(self.candle_canvas.winfo_width(), 400)
        height = max(self.candle_canvas.winfo_height(), 340)

        viewport_left = float(self.candle_canvas.canvasx(0))
        viewport_right = viewport_left + float(viewport_width)

        self.candle_canvas.delete("all")
        self.candle_canvas.create_rectangle(
            viewport_left,
            0,
            viewport_right,
            height,
            fill=CHART_BG,
            outline=CHART_BG,
        )

        center_y = height / 2
        left_pad = LEFT_PAD
        right_pad = RIGHT_PAD
        top_pad = 118
        bottom_pad = 34

        n = len(bars)
        body_half, pair_gap, pair_width = self._pair_layout(width_adjust_px, pair_gap_adjust_px)
        total_width = max(viewport_width, left_pad + self._pair_total_width(n, pair_width, pair_gap) + right_pad)

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
            p1_x, p2_x, _ = self._pair_positions(i, left_pad, body_half, pair_gap, pair_width)

            p1_high_y = center_y - float(row["p1_high"]) * scale
            p1_low_y = center_y - float(row["p1_low"]) * scale
            p1_close_y = center_y - float(row["p1_close"]) * scale

            p2_high_y = center_y - float(row["p2_high"]) * scale
            p2_low_y = center_y - float(row["p2_low"]) * scale
            p2_close_y = center_y - float(row["p2_close"]) * scale

            p1_color = PAIR_1_UP if float(row["close_1"]) >= float(row["open_1"]) else PAIR_1_DOWN
            p2_color = PAIR_2_UP if float(row["close_2"]) >= float(row["open_2"]) else PAIR_2_DOWN

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

        self._draw_selection_on_candles(
            bars=bars,
            body_half=body_half,
            pair_gap=pair_gap,
            pair_width=pair_width,
            center_y=center_y,
            scale=scale,
            height=height,
            top_pad=top_pad,
            bottom_pad=bottom_pad,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
        )

        title_x = viewport_left + viewport_width / 2.0
        fixed_left_x = viewport_left + 16
        fixed_right_x = viewport_right - 16

        self.candle_canvas.create_text(
            title_x,
            10,
            anchor="n",
            fill=CHART_TEXT,
            font=("Segoe UI", 10),
            text="внутри пары без зазора, между парами регулируемый отступ, горизонтальный скролл",
        )

        self._draw_pair_legend(symbol_1, symbol_2, fixed_left_x, 10)

        mode_text = "с коэф" if divergence_stats.uses_ratio else "реал"
        divergence_text = (
            f"Δ режим: {mode_text}\n"
            f"Лента Δ: {divergence_stats.total_diff_pips:+.2f} п\n"
            f"Текущая свеча Δ: {divergence_stats.current_bar_diff_pips:+.2f} п\n"
            f"Live bid Δ: {divergence_stats.live_diff_pips:+.2f} п"
        )
        self.candle_canvas.create_text(
            fixed_right_x,
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
            fixed_right_x,
            height - 10,
            anchor="se",
            fill=CHART_TEXT,
            font=("Segoe UI", 9),
            text=(
                f"{symbol_2} | scale coef 1/2 = {ratio_1_to_2:.6f} | "
                f"width={width_adjust_px:+d}px | height={height_adjust_px:+d}px | pair_gap={pair_gap_adjust_px:+d}px"
            ),
        )

        self.candle_canvas.configure(scrollregion=(0, 0, total_width, height))

    def _draw_divergence_line(
        self,
        divergence_series: pd.Series,
        width_adjust_px: int,
        pair_gap_adjust_px: int,
        selected_start_index: int | None,
        selected_end_index: int | None,
    ) -> None:
        self.line_canvas.update_idletasks()
        viewport_width = max(self.line_canvas.winfo_width(), 400)
        height = max(self.line_canvas.winfo_height(), 120)

        viewport_left = float(self.line_canvas.canvasx(0))
        viewport_right = viewport_left + float(viewport_width)

        self.line_canvas.delete("all")
        self.line_canvas.create_rectangle(
            viewport_left,
            0,
            viewport_right,
            height,
            fill=CHART_BG,
            outline=CHART_BG,
        )

        left_pad = LEFT_PAD
        right_pad = RIGHT_PAD
        top_pad = 18
        bottom_pad = 22

        n = len(divergence_series)
        body_half, pair_gap, pair_width = self._pair_layout(width_adjust_px, pair_gap_adjust_px)
        total_width = max(viewport_width, left_pad + self._pair_total_width(n, pair_width, pair_gap) + right_pad)

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
            _, _, pair_center_x = self._pair_positions(i, left_pad, body_half, pair_gap, pair_width)
            y = mid_y - float(value) * scale
            points.extend([pair_center_x, y])

        if len(points) >= 4:
            self.line_canvas.create_line(*points, fill="#eab308", width=2, smooth=False)
        elif len(points) == 2:
            self.line_canvas.create_oval(points[0] - 2, points[1] - 2, points[0] + 2, points[1] + 2, fill="#eab308", outline="#eab308")

        self._draw_selection_on_line(
            divergence_series=divergence_series,
            body_half=body_half,
            pair_gap=pair_gap,
            pair_width=pair_width,
            mid_y=mid_y,
            scale=scale,
            height=height,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
        )

        self.line_canvas.create_text(
            viewport_left + 16,
            6,
            anchor="nw",
            fill=CHART_TEXT,
            font=("Segoe UI", 9, "bold"),
            text="Линия расхождения",
        )

        self.line_canvas.configure(scrollregion=(0, 0, total_width, height))

    def _draw_selection_on_candles(
        self,
        bars: pd.DataFrame,
        body_half: float,
        pair_gap: float,
        pair_width: float,
        center_y: float,
        scale: float,
        height: float,
        top_pad: float,
        bottom_pad: float,
        selected_start_index: int | None,
        selected_end_index: int | None,
    ) -> None:
        if selected_start_index is None or bars.empty:
            return

        start_index = max(0, min(len(bars) - 1, int(selected_start_index)))
        end_index = start_index if selected_end_index is None else max(0, min(len(bars) - 1, int(selected_end_index)))

        if end_index < start_index:
            start_index, end_index = end_index, start_index

        start_p1_x, start_p2_x, start_center_x = self._pair_positions(start_index, LEFT_PAD, body_half, pair_gap, pair_width)
        end_p1_x, end_p2_x, end_center_x = self._pair_positions(end_index, LEFT_PAD, body_half, pair_gap, pair_width)

        start_left = start_p1_x - body_half - 4
        end_right = end_p2_x + body_half + 4

        if end_index > start_index:
            self.candle_canvas.create_rectangle(
                start_left,
                top_pad - 8,
                end_right,
                height - bottom_pad + 4,
                outline="#a78bfa",
                dash=(5, 3),
                width=1,
            )

        self.candle_canvas.create_line(
            start_center_x,
            top_pad - 10,
            start_center_x,
            height - bottom_pad + 6,
            fill="#22c55e",
            dash=(4, 3),
            width=2,
        )
        self.candle_canvas.create_text(
            start_center_x,
            top_pad - 16,
            anchor="s",
            fill="#22c55e",
            font=("Segoe UI", 9, "bold"),
            text="START",
        )

        if selected_end_index is not None:
            self.candle_canvas.create_line(
                end_center_x,
                top_pad - 10,
                end_center_x,
                height - bottom_pad + 6,
                fill="#ef4444",
                dash=(4, 3),
                width=2,
            )
            self.candle_canvas.create_text(
                end_center_x,
                top_pad - 16,
                anchor="s",
                fill="#ef4444",
                font=("Segoe UI", 9, "bold"),
                text="END",
            )

        start_row = bars.iloc[start_index]
        self._draw_marker(self.candle_canvas, start_p1_x, center_y - float(start_row["p1_close"]) * scale, "#22c55e")
        self._draw_marker(self.candle_canvas, start_p2_x, center_y - float(start_row["p2_close"]) * scale, "#22c55e")

        if selected_end_index is not None:
            end_row = bars.iloc[end_index]
            self._draw_marker(self.candle_canvas, end_p1_x, center_y - float(end_row["p1_close"]) * scale, "#ef4444")
            self._draw_marker(self.candle_canvas, end_p2_x, center_y - float(end_row["p2_close"]) * scale, "#ef4444")

    def _draw_selection_on_line(
        self,
        divergence_series: pd.Series,
        body_half: float,
        pair_gap: float,
        pair_width: float,
        mid_y: float,
        scale: float,
        height: float,
        selected_start_index: int | None,
        selected_end_index: int | None,
    ) -> None:
        if selected_start_index is None or divergence_series.empty:
            return

        start_index = max(0, min(len(divergence_series) - 1, int(selected_start_index)))
        end_index = start_index if selected_end_index is None else max(0, min(len(divergence_series) - 1, int(selected_end_index)))

        if end_index < start_index:
            start_index, end_index = end_index, start_index

        _, _, start_center_x = self._pair_positions(start_index, LEFT_PAD, body_half, pair_gap, pair_width)
        _, _, end_center_x = self._pair_positions(end_index, LEFT_PAD, body_half, pair_gap, pair_width)

        start_y = mid_y - float(divergence_series.iloc[start_index]) * scale
        end_y = mid_y - float(divergence_series.iloc[end_index]) * scale

        if end_index > start_index:
            self.line_canvas.create_rectangle(
                start_center_x - pair_width / 2.0,
                10,
                end_center_x + pair_width / 2.0,
                height - 10,
                outline="#a78bfa",
                dash=(5, 3),
                width=1,
            )

        self.line_canvas.create_line(start_center_x, 8, start_center_x, height - 8, fill="#22c55e", dash=(4, 3), width=2)
        self._draw_marker(self.line_canvas, start_center_x, start_y, "#22c55e")

        if selected_end_index is not None:
            self.line_canvas.create_line(end_center_x, 8, end_center_x, height - 8, fill="#ef4444", dash=(4, 3), width=2)
            self._draw_marker(self.line_canvas, end_center_x, end_y, "#ef4444")

    def _draw_pair_legend(self, symbol_1: str, symbol_2: str, x0: float, y0: float) -> None:
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

    def _draw_marker(self, canvas: tk.Canvas, x: float, y: float, color: str) -> None:
        radius = 5
        canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline=color,
            width=2,
        )
        canvas.create_oval(
            x - 1,
            y - 1,
            x + 1,
            y + 1,
            outline=color,
            fill=color,
        )

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