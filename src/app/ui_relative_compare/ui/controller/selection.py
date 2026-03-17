from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.services.market.transform import transform_price_delta_to_pips
from .helpers import format_pips, format_symbol_for_stats


class ControllerSelectionMixin:
    def bind_scroll_events(self) -> None:
        for widget in (self.view.candle_canvas, self.view.line_canvas):
            widget.bind("<MouseWheel>", self.on_mousewheel_horizontal)
            widget.bind("<Shift-MouseWheel>", self.on_mousewheel_horizontal)
            widget.bind("<Button-4>", self.on_mousewheel_horizontal)
            widget.bind("<Button-5>", self.on_mousewheel_horizontal)
            widget.bind("<ButtonPress-1>", self.on_button_press)
            widget.bind("<B1-Motion>", self.on_scan_drag)
            widget.bind("<ButtonRelease-1>", self.on_button_release)

    def set_scrollbar(self, first: str, last: str) -> None:
        self.view.h_scroll.set(first, last)

    def on_scrollbar(self, *args) -> None:
        self.view.candle_canvas.xview(*args)
        self.view.line_canvas.xview(*args)

    def sync_canvas_view(self, first_fraction: float) -> None:
        pos = max(0.0, min(1.0, float(first_fraction)))
        self.view.candle_canvas.xview_moveto(pos)
        self.view.line_canvas.xview_moveto(pos)

    def on_mousewheel_horizontal(self, event) -> str:
        if getattr(event, "num", None) == 4:
            delta_units = -3
        elif getattr(event, "num", None) == 5:
            delta_units = 3
        else:
            delta = int(getattr(event, "delta", 0) or 0)
            if delta == 0:
                return "break"
            delta_units = -3 if delta > 0 else 3
        self.view.candle_canvas.xview_scroll(delta_units, "units")
        self.view.line_canvas.xview_scroll(delta_units, "units")
        return "break"

    def on_button_press(self, event) -> str:
        self.drag_start_x = int(event.x)
        self.drag_active = False
        self.view.candle_canvas.scan_mark(event.x, 0)
        self.view.line_canvas.scan_mark(event.x, 0)
        return "break"

    def on_scan_drag(self, event) -> str:
        if abs(int(event.x) - self.drag_start_x) >= 4:
            self.drag_active = True
        self.view.candle_canvas.scan_dragto(event.x, 0, gain=1)
        self.view.line_canvas.scan_dragto(event.x, 0, gain=1)
        return "break"

    def on_button_release(self, event) -> str:
        if not self.drag_active:
            self.handle_chart_click(event.widget, int(event.x))
        self.drag_active = False
        return "break"

    def handle_chart_click(self, widget, x_local: int) -> None:
        if self.current_snapshot is None or self.current_snapshot.bars.empty:
            return
        canvas = self.view.candle_canvas if widget is self.view.candle_canvas else self.view.line_canvas
        x_world = float(canvas.canvasx(x_local))
        index = self.chart.get_index_at_x(len(self.current_snapshot.bars), x_world, self.view.width_adjust_px, self.view.pair_gap_adjust_px)
        if index is None:
            return
        self.selection.register_click(self.current_snapshot.bars, index)
        self.redraw_current_snapshot()

    def _format_range_start_end(self, start_ts, end_ts, candles_distance: int) -> str:
        start = pd.Timestamp(start_ts)
        end = pd.Timestamp(end_ts)
        same_year = start.year == end.year
        same_day = start.normalize() == end.normalize()
        if same_day:
            start_text = start.strftime("%H:%M:%S")
            end_text = end.strftime("%H:%M:%S")
        elif same_year:
            start_text = start.strftime("%d.%m %H:%M:%S")
            end_text = end.strftime("%d.%m %H:%M:%S")
        else:
            start_text = start.strftime("%d.%m.%Y %H:%M:%S")
            end_text = end.strftime("%d.%m.%Y %H:%M:%S")
        return f"{start_text} ->\n{end_text} ({candles_distance} свечей)"

    def update_selection_stats(self) -> None:
        if self.current_snapshot is None or self.current_snapshot.bars.empty:
            self.view.selection_range_var.set("-")
            self.view.selection_pair_1_var.set("-")
            self.view.selection_pair_2_var.set("-")
            self.view.selection_diff_var.set("-")
            return

        if self.selection.start_index is None:
            self.view.selection_range_var.set("кликни стартовую пару/точку")
            self.view.selection_pair_1_var.set("-")
            self.view.selection_pair_2_var.set("-")
            self.view.selection_diff_var.set("-")
            return

        bars = self.current_snapshot.bars
        start_index = int(self.selection.start_index)
        end_index = start_index if self.selection.end_index is None else int(self.selection.end_index)
        start_row = bars.iloc[start_index]
        end_row = bars.iloc[end_index]

        if self.selection.end_index is None:
            self.view.selection_range_var.set(f"START: {pd.Timestamp(start_row['time']).strftime('%H:%M:%S')} ->\nжду END")
            self.view.selection_pair_1_var.set("-")
            self.view.selection_pair_2_var.set("-")
            self.view.selection_diff_var.set("-")
            return

        move_1_pips = float(transform_price_delta_to_pips(float(end_row["close_1"]) - float(start_row["close_1"]), self.current_snapshot.digits_1))
        move_2_pips = float(transform_price_delta_to_pips(float(end_row["close_2"]) - float(start_row["close_2"]), self.current_snapshot.digits_2, 1.0, self.current_snapshot.negative_correlation))
        diff_pips = move_1_pips - move_2_pips
        candles_distance = max(0, end_index - start_index)

        self.view.selection_range_var.set(self._format_range_start_end(start_row["time"], end_row["time"], candles_distance))
        self.view.selection_pair_1_var.set(f"{format_symbol_for_stats(self.view.symbol_1_var.get().strip())}: {format_pips(move_1_pips)}")
        self.view.selection_pair_2_var.set(f"{format_symbol_for_stats(self.view.symbol_2_var.get().strip())}: {format_pips(move_2_pips)}")
        self.view.selection_diff_var.set(f"diff: {format_pips(diff_pips)}")
