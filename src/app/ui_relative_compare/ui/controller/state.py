from __future__ import annotations

from tkinter import colorchooser

from src.app.ui_relative_compare.constants import MARKER_BORDER
from src.app.ui_relative_compare.services.ui_state import UIState, save_ui_state
from .helpers import base_label, normalize_symbol


class ControllerStateMixin:
    def bind_state_persistence(self) -> None:
        tracked = [
            self.view.symbol_1_var,
            self.view.symbol_2_var,
            self.view.timeframe_var,
            self.view.visible_bars_var,
            self.view.refresh_ms_var,
            self.view.aggregate_bars_var,
            self.view.manual_ratio_1_to_2_var,
            self.view.negative_correlation_var,
            self.view.mutual_exclusion_var,
            self.view.auto_volume_var,
            self.view.manual_lot_1_var,
            self.view.manual_lot_2_var,
            self.view.signal_fast_ma_var,
            self.view.signal_slow_ma_var,
            self.view.signal_entry_threshold_var,
            self.view.signal_exit_threshold_var,
            self.view.line_chart_mode_var,
            self.view.line_zoom_var,
        ]
        for var in tracked:
            var.trace_add("write", self.schedule_state_save)

        self.view.symbol_1_var.trace_add("write", self.on_symbols_changed)
        self.view.symbol_2_var.trace_add("write", self.on_symbols_changed)
        self.view.manual_lot_1_var.trace_add("write", self.on_manual_volume_changed)
        self.view.manual_lot_2_var.trace_add("write", self.on_manual_volume_changed)
        self.view.manual_ratio_1_to_2_var.trace_add("write", self.on_manual_ratio_changed)
        self.view.signal_fast_ma_var.trace_add("write", self.on_signal_param_changed)
        self.view.signal_slow_ma_var.trace_add("write", self.on_signal_param_changed)
        self.view.signal_entry_threshold_var.trace_add("write", self.on_signal_param_changed)
        self.view.signal_exit_threshold_var.trace_add("write", self.on_signal_param_changed)

        self.view.bind("<Configure>", self.on_window_configure)
        self.view.chart_panes.bind("<ButtonRelease-1>", self.on_chart_panes_release)

    def on_window_configure(self, event) -> None:
        if event.widget is self.view:
            self.schedule_state_save()

    def on_chart_panes_release(self, _event) -> None:
        if not self.view.candle_collapsed and not self.view.line_collapsed:
            self.view.chart_split_y = self.view.current_chart_split_y()
        self.schedule_state_save()

    def schedule_state_save(self, *_args) -> None:
        if self.state_save_job is not None:
            self.view.after_cancel(self.state_save_job)
        self.state_save_job = self.view.after(250, self.save_state_now)

    def save_state_now(self) -> None:
        self.state_save_job = None
        try:
            save_ui_state(self.base_cfg, self.collect_ui_state())
        except Exception:
            pass

    def collect_ui_state(self) -> UIState:
        return UIState(
            symbol_1=self.view.symbol_1_var.get().strip() or "EURUSD",
            symbol_2=self.view.symbol_2_var.get().strip() or "AUDUSD",
            timeframe=self.view.timeframe_var.get().strip() or "M1",
            visible_bars=self.view.visible_bars_var.get().strip() or "120",
            refresh_ms=self.view.refresh_ms_var.get().strip() or "250",
            aggregate_bars=self.view.aggregate_bars_var.get().strip() or "1",
            manual_ratio_1_to_2=self.view.manual_ratio_1_to_2_var.get().strip() or "1.000000",
            negative_correlation=bool(self.view.negative_correlation_var.get()),
            mutual_exclusion_enabled=bool(self.view.mutual_exclusion_var.get()),
            auto_volume=bool(self.view.auto_volume_var.get()),
            manual_lot_1=self.view.manual_lot_1_var.get().strip() or "0.10",
            manual_lot_2=self.view.manual_lot_2_var.get().strip() or "0.10",
            signal_fast_ma=self.view.signal_fast_ma_var.get().strip() or "8",
            signal_slow_ma=self.view.signal_slow_ma_var.get().strip() or "34",
            signal_entry_threshold=self.view.signal_entry_threshold_var.get().strip() or "12.0",
            signal_exit_threshold=self.view.signal_exit_threshold_var.get().strip() or "3.0",
            line_chart_mode=self.view.line_chart_mode_var.get().strip() or "gap_ma",
            width_adjust_px=int(self.view.width_adjust_px),
            height_adjust_px=int(self.view.height_adjust_px),
            pair_gap_adjust_px=int(self.view.pair_gap_adjust_px),
            chart_split_y=int(self.view.chart_split_y if (self.view.candle_collapsed or self.view.line_collapsed) else self.view.current_chart_split_y()),
            candle_collapsed=bool(self.view.candle_collapsed),
            line_collapsed=bool(self.view.line_collapsed),
            pair_1_up_color=self.view.chart_colors["pair_1_up"],
            pair_1_down_color=self.view.chart_colors["pair_1_down"],
            pair_2_up_color=self.view.chart_colors["pair_2_up"],
            pair_2_down_color=self.view.chart_colors["pair_2_down"],
            window_geometry=str(self.view.geometry()),
            line_zoom=float(self.view.line_zoom_var.get()),
        )

    def refresh_color_markers(self) -> None:
        for key, widget in self.view.color_marker_widgets.items():
            widget.configure(bg=self.view.chart_colors[key], highlightbackground=MARKER_BORDER)

    def refresh_action_buttons(self) -> None:
        mapping = {
            "pair_1_sell": "pair_1_down",
            "pair_1_buy": "pair_1_up",
            "pair_2_sell": "pair_2_down",
            "pair_2_buy": "pair_2_up",
        }
        for btn_key, color_key in mapping.items():
            btn = self.view.action_button_widgets.get(btn_key)
            if btn is None:
                continue
            color = self.view.chart_colors[color_key]
            try:
                btn.configure(bg=color, activebackground=color)
            except Exception:
                pass

    def pick_color(self, color_key: str) -> None:
        current = self.view.chart_colors[color_key]
        selected = colorchooser.askcolor(color=current, title="Выбор цвета")
        hex_color = selected[1]
        if not hex_color:
            return
        self.view.chart_colors[color_key] = str(hex_color)
        self.refresh_color_markers()
        self.refresh_action_buttons()
        self.schedule_state_save()
        if self.current_snapshot is not None:
            self.redraw_current_snapshot()

    def update_symbol_labels(self) -> None:
        symbol_1 = self.view.symbol_1_var.get().strip() or "EURUSD"
        symbol_2 = self.view.symbol_2_var.get().strip() or "AUDUSD"
        self.view.manual_lot_1_label_var.set(f"Lot {normalize_symbol(symbol_1)}")
        self.view.manual_lot_2_label_var.set(f"Lot {normalize_symbol(symbol_2)}")
        self.view.header_symbol_1_var.set(base_label(symbol_1))
        self.view.header_symbol_2_var.set(base_label(symbol_2))
        self.view.action_pair_1_var.set(normalize_symbol(symbol_1))
        self.view.action_pair_2_var.set(normalize_symbol(symbol_2))

    def on_symbols_changed(self, *_args) -> None:
        self.update_symbol_labels()
        self.schedule_state_save()

    def on_manual_volume_changed(self, *_args) -> None:
        if not self.view.auto_volume_var.get():
            self.update_trade_hint()

    def on_manual_ratio_changed(self, *_args) -> None:
        self.update_trade_hint()

    def on_signal_param_changed(self, *_args) -> None:
        self.update_trade_hint()

    def on_line_chart_mode_changed(self) -> None:
        if self.current_snapshot is not None:
            self.redraw_current_snapshot()

    def update_manual_volume_state(self) -> None:
        state = "disabled" if self.view.auto_volume_var.get() else "normal"
        self.view.manual_lot_1_entry.configure(state=state)
        self.view.manual_lot_2_entry.configure(state=state)