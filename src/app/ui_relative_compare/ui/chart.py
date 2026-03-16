from __future__ import annotations

import tkinter as tk

import pandas as pd

from src.app.ui_relative_compare.constants import CHART_AXIS, CHART_BG, CHART_GRID, CHART_TEXT
from src.app.ui_relative_compare.models import DivergenceStats, TradePlan


BASE_BODY_HALF = 4.0
BASE_PAIR_GAP = 10.0
LEFT_PAD = 60
RIGHT_PAD = 30
EPS = 1e-12


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
        colors: dict[str, str],
        line_zoom: float,
    ) -> None:
        _ = divergence_series
        _ = divergence_stats

        self._draw_candles(
            bars=bars,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            ratio_1_to_2=ratio_1_to_2,
            width_adjust_px=width_adjust_px,
            height_adjust_px=height_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
            trade_plan=trade_plan,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
            colors=colors,
        )

        line_1, line_2 = self._build_relative_line_series(bars, ratio_1_to_2)

        self._draw_relative_lines(
            line_1=line_1,
            line_2=line_2,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            width_adjust_px=width_adjust_px,
            pair_gap_adjust_px=pair_gap_adjust_px,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
            colors=colors,
            line_zoom=line_zoom,
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

    def _estimate_pip_size(
        self,
        price_delta: pd.Series,
        scaled_delta: pd.Series,
        factor: float,
        default: float,
    ) -> float:
        candidates: list[float] = []

        for raw_delta, scaled in zip(price_delta.tolist(), scaled_delta.tolist()):
            raw_value = float(raw_delta)
            scaled_value = float(scaled)
            if abs(raw_value) <= EPS or abs(scaled_value) <= EPS:
                continue
            candidates.append(abs((raw_value * factor) / scaled_value))

        if not candidates:
            return default

        candidates.sort()
        return float(candidates[len(candidates) // 2])

    def _build_relative_line_series(
        self,
        bars: pd.DataFrame,
        ratio_1_to_2: float,
    ) -> tuple[pd.Series, pd.Series]:
        if bars.empty:
            return pd.Series(dtype=float), pd.Series(dtype=float)

        raw_delta_1 = (bars["close_1"] - bars["open_1"]).astype(float)
        raw_delta_2 = (bars["close_2"] - bars["open_2"]).astype(float)

        pip_1 = self._estimate_pip_size(
            price_delta=raw_delta_1,
            scaled_delta=bars["p1_close"].astype(float),
            factor=1.0,
            default=0.0001,
        )
        pip_2 = self._estimate_pip_size(
            price_delta=raw_delta_2,
            scaled_delta=bars["p2_close"].astype(float),
            factor=max(float(ratio_1_to_2), EPS),
            default=0.0001,
        )

        close_to_close_1 = bars["close_1"].astype(float).diff().fillna(0.0) / pip_1
        close_to_close_2 = bars["close_2"].astype(float).diff().fillna(0.0) / pip_2

        out_1: list[float] = [0.0]
        out_2: list[float] = [0.0]

        acc_1 = 0.0
        acc_2 = 0.0

        for i in range(1, len(bars)):
            move_1 = float(close_to_close_1.iloc[i])
            move_2 = float(close_to_close_2.iloc[i])

            if move_1 * move_2 > 0:
                common = min(abs(move_1), abs(move_2))
                direction = 1.0 if move_1 > 0 else -1.0
                move_1 -= direction * common
                move_2 -= direction * common

            acc_1 += move_1
            acc_2 += move_2

            out_1.append(acc_1)
            out_2.append(acc_2)

        return pd.Series(out_1, dtype=float), pd.Series(out_2, dtype=float)

    def _draw_candles(
        self,
        bars: pd.DataFrame,
        symbol_1: str,
        symbol_2: str,
        ratio_1_to_2: float,
        width_adjust_px: int,
        height_adjust_px: int,
        pair_gap_adjust_px: int,
        trade_plan: TradePlan,
        selected_start_index: int | None,
        selected_end_index: int | None,
        colors: dict[str, str],
    ) -> None:
        self.candle_canvas.update_idletasks()
        viewport_width = max(self.candle_canvas.winfo_width(), 400)
        height = max(self.candle_canvas.winfo_height(), 240)

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
        top_pad = 56
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

            p1_color = colors["pair_1_up"] if float(row["close_1"]) >= float(row["open_1"]) else colors["pair_1_down"]
            p2_color = colors["pair_2_up"] if float(row["close_2"]) >= float(row["open_2"]) else colors["pair_2_down"]

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
        self.candle_canvas.create_text(
            title_x,
            8,
            anchor="n",
            fill=CHART_TEXT,
            font=("Segoe UI", 10),
            text=f"{symbol_1} vs {symbol_2} | свечи рядом, без зеркала",
        )

        self._draw_trade_arrows(last_points=last_points, symbol_1=symbol_1, symbol_2=symbol_2, trade_plan=trade_plan, height=height)

        self.candle_canvas.create_text(
            viewport_right - 16,
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

    def _draw_relative_lines(
            self,
            line_1: pd.Series,
            line_2: pd.Series,
            symbol_1: str,
            symbol_2: str,
            width_adjust_px: int,
            pair_gap_adjust_px: int,
            selected_start_index: int | None,
            selected_end_index: int | None,
            colors: dict[str, str],
            line_zoom: float,
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

        n = max(len(line_1), len(line_2))
        body_half, pair_gap, pair_width = self._pair_layout(width_adjust_px, pair_gap_adjust_px)
        total_width = max(viewport_width, left_pad + self._pair_total_width(n, pair_width, pair_gap) + right_pad)

        max_abs = 1.0
        if not line_1.empty:
            max_abs = max(max_abs, float(line_1.abs().max()))
        if not line_2.empty:
            max_abs = max(max_abs, float(line_2.abs().max()))

        mid_y = height / 2
        usable_half = max(20.0, (height - top_pad - bottom_pad) / 2)
        scale = usable_half / (max_abs * 1.1)

        zoom = float(line_zoom or 1.0)
        zoom = max(0.2, min(8.0, zoom))
        scale *= zoom

        self.line_canvas.create_line(left_pad, mid_y, total_width - right_pad, mid_y, fill=CHART_AXIS, width=1)
        self.line_canvas.create_text(12, mid_y, anchor="w", text="0", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))

        for level in [0.5, 1.0]:
            dy = max_abs * (usable_half / (max_abs * 1.1)) * level
            self.line_canvas.create_line(left_pad, mid_y - dy, total_width - right_pad, mid_y - dy, fill=CHART_GRID)
            self.line_canvas.create_line(left_pad, mid_y + dy, total_width - right_pad, mid_y + dy, fill=CHART_GRID)

        points_1: list[float] = []
        points_2: list[float] = []

        for i in range(n):
            _, _, pair_center_x = self._pair_positions(i, left_pad, body_half, pair_gap, pair_width)

            y_1 = mid_y - float(line_1.iloc[i]) * scale
            y_2 = mid_y - float(line_2.iloc[i]) * scale

            points_1.extend([pair_center_x, y_1])
            points_2.extend([pair_center_x, y_2])

        if len(points_1) >= 4:
            self.line_canvas.create_line(*points_1, fill=colors["pair_1_up"], width=1, smooth=False)
        elif len(points_1) == 2:
            self.line_canvas.create_oval(
                points_1[0] - 1, points_1[1] - 1, points_1[0] + 1, points_1[1] + 1,
                fill=colors["pair_1_up"], outline=colors["pair_1_up"]
            )

        if len(points_2) >= 4:
            self.line_canvas.create_line(*points_2, fill=colors["pair_2_up"], width=1, smooth=False)
        elif len(points_2) == 2:
            self.line_canvas.create_oval(
                points_2[0] - 1, points_2[1] - 1, points_2[0] + 1, points_2[1] + 1,
                fill=colors["pair_2_up"], outline=colors["pair_2_up"]
            )

        self._draw_selection_on_line(
            line_1=line_1,
            line_2=line_2,
            body_half=body_half,
            pair_gap=pair_gap,
            pair_width=pair_width,
            mid_y=mid_y,
            scale=scale,
            height=height,
            selected_start_index=selected_start_index,
            selected_end_index=selected_end_index,
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
        line_1: pd.Series,
        line_2: pd.Series,
        body_half: float,
        pair_gap: float,
        pair_width: float,
        mid_y: float,
        scale: float,
        height: float,
        selected_start_index: int | None,
        selected_end_index: int | None,
    ) -> None:
        if selected_start_index is None or line_1.empty or line_2.empty:
            return

        limit = min(len(line_1), len(line_2)) - 1
        start_index = max(0, min(limit, int(selected_start_index)))
        end_index = start_index if selected_end_index is None else max(0, min(limit, int(selected_end_index)))

        if end_index < start_index:
            start_index, end_index = end_index, start_index

        _, _, start_center_x = self._pair_positions(start_index, LEFT_PAD, body_half, pair_gap, pair_width)
        _, _, end_center_x = self._pair_positions(end_index, LEFT_PAD, body_half, pair_gap, pair_width)

        start_y_1 = mid_y - float(line_1.iloc[start_index]) * scale
        start_y_2 = mid_y - float(line_2.iloc[start_index]) * scale
        end_y_1 = mid_y - float(line_1.iloc[end_index]) * scale
        end_y_2 = mid_y - float(line_2.iloc[end_index]) * scale

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
        self._draw_marker(self.line_canvas, start_center_x, start_y_1, "#22c55e")
        self._draw_marker(self.line_canvas, start_center_x, start_y_2, "#22c55e")

        if selected_end_index is not None:
            self.line_canvas.create_line(end_center_x, 8, end_center_x, height - 8, fill="#ef4444", dash=(4, 3), width=2)
            self._draw_marker(self.line_canvas, end_center_x, end_y_1, "#ef4444")
            self._draw_marker(self.line_canvas, end_center_x, end_y_2, "#ef4444")

    def _draw_trade_arrows(
        self,
        last_points: list[dict[str, float]],
        symbol_1: str,
        symbol_2: str,
        trade_plan: TradePlan,
        height: int,
    ) -> None:
        sell_color = "#ef4444"
        buy_color = "#2563eb"

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
        y = max(50.0, y)
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
