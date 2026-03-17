from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.app.ui_relative_compare.constants import ACTION_BG, ACTION_TEXT, PANE_BORDER, PANE_HEADER_BG
from src.app.ui_relative_compare.services.ui_state import UIState
from .builders.charts import build_chart_area
from .builders.controls import build_controls
from .builders.info import build_info_blocks


class RelativeCompareWindow(tk.Tk):
    def __init__(self, controller, saved_state: UIState) -> None:
        super().__init__()
        self.controller = controller
        self.saved_state = saved_state

        self.title("MT5 Relative Compare")
        self.geometry(saved_state.window_geometry or "1380x980")
        self.minsize(1240, 860)

        self.symbol_1_var = tk.StringVar(value=saved_state.symbol_1)
        self.symbol_2_var = tk.StringVar(value=saved_state.symbol_2)
        self.timeframe_var = tk.StringVar(value=saved_state.timeframe)
        self.visible_bars_var = tk.StringVar(value=saved_state.visible_bars)
        self.refresh_ms_var = tk.StringVar(value=saved_state.refresh_ms)
        self.aggregate_bars_var = tk.StringVar(value=saved_state.aggregate_bars)
        self.aggregate_info_var = tk.StringVar(value=f"{saved_state.timeframe} x {saved_state.aggregate_bars}")
        self.manual_ratio_1_to_2_var = tk.StringVar(value=saved_state.manual_ratio_1_to_2)
        self.negative_correlation_var = tk.BooleanVar(value=saved_state.negative_correlation)
        self.mutual_exclusion_var = tk.BooleanVar(value=saved_state.mutual_exclusion_enabled)

        self.auto_volume_var = tk.BooleanVar(value=saved_state.auto_volume)
        self.manual_lot_1_var = tk.StringVar(value=saved_state.manual_lot_1)
        self.manual_lot_2_var = tk.StringVar(value=saved_state.manual_lot_2)
        self.signal_fast_ma_var = tk.StringVar(value=saved_state.signal_fast_ma)
        self.signal_slow_ma_var = tk.StringVar(value=saved_state.signal_slow_ma)
        self.signal_entry_threshold_var = tk.StringVar(value=saved_state.signal_entry_threshold)
        self.signal_exit_threshold_var = tk.StringVar(value=saved_state.signal_exit_threshold)
        self.line_chart_mode_var = tk.StringVar(value=saved_state.line_chart_mode or "gap_ma")

        self.manual_lot_1_label_var = tk.StringVar(value="Lot EURUSD")
        self.manual_lot_2_label_var = tk.StringVar(value="Lot AUDUSD")
        self.header_symbol_1_var = tk.StringVar(value="EURO")
        self.header_symbol_2_var = tk.StringVar(value="AUD")
        self.action_pair_1_var = tk.StringVar(value=saved_state.symbol_1)
        self.action_pair_2_var = tk.StringVar(value=saved_state.symbol_2)

        self.status_var = tk.StringVar(value="idle")
        self.account_var = tk.StringVar(value="-")
        self.last_bar_time_var = tk.StringVar(value="-")
        self.trade_hint_var = tk.StringVar(value="-")

        self.selection_range_var = tk.StringVar(value="-")
        self.selection_pair_1_var = tk.StringVar(value="-")
        self.selection_pair_2_var = tk.StringVar(value="-")
        self.selection_diff_var = tk.StringVar(value="-")

        self.width_adjust_px = int(saved_state.width_adjust_px)
        self.height_adjust_px = int(saved_state.height_adjust_px)
        self.pair_gap_adjust_px = int(saved_state.pair_gap_adjust_px)
        self.chart_split_y = int(saved_state.chart_split_y)
        self.candle_collapsed = bool(saved_state.candle_collapsed)
        self.line_collapsed = bool(saved_state.line_collapsed)

        self.width_size_var = tk.StringVar(value=f"{self.width_adjust_px:+d}px")
        self.height_size_var = tk.StringVar(value=f"{self.height_adjust_px:+d}px")
        self.pair_gap_size_var = tk.StringVar(value=f"{self.pair_gap_adjust_px:+d}px")
        self.candle_toggle_var = tk.StringVar()
        self.line_toggle_var = tk.StringVar()
        self.line_zoom_var = tk.DoubleVar(value=float(saved_state.line_zoom or 1.0))

        self.chart_colors: dict[str, str] = {
            "pair_1_up": saved_state.pair_1_up_color,
            "pair_1_down": saved_state.pair_1_down_color,
            "pair_2_up": saved_state.pair_2_up_color,
            "pair_2_down": saved_state.pair_2_down_color,
        }
        self.color_marker_widgets: dict[str, tk.Label] = {}
        self.action_button_widgets: dict[str, tk.Button] = {}

        self.build_ui()

    def build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        build_controls(self, root)
        build_info_blocks(self, root)
        build_chart_area(self, root)

    def make_action_label(self, parent: tk.Widget, text_var: tk.StringVar) -> tk.Label:
        return tk.Label(parent, textvariable=text_var, bg=ACTION_BG, fg=ACTION_TEXT, font=("Segoe UI", 10, "bold"), padx=0, pady=0)

    def make_color_marker(self, parent: tk.Widget, color_key: str, arrow_text: str) -> tk.Label:
        marker = tk.Label(parent, text=arrow_text, width=2, bg=self.chart_colors[color_key], fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="solid", bd=1, cursor="hand2", padx=2, pady=1)
        marker.bind("<Button-1>", lambda _event, key=color_key: self.controller.pick_color(key))
        return marker

    def make_action_button(self, parent: tk.Widget, text: str, command, bg_color: str, width_px: int, height_px: int = 28, store_key: str | None = None) -> tk.Frame:
        frame = tk.Frame(parent, width=width_px, height=height_px, bg=ACTION_BG, highlightthickness=0, bd=0)
        frame.pack_propagate(False)
        button = tk.Button(
            frame,
            text=text,
            command=command,
            bg=bg_color,
            fg="#ffffff",
            activebackground=bg_color,
            activeforeground="#ffffff",
            highlightthickness=0,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=0,
            pady=0,
        )
        button.pack(fill="both", expand=True)
        if store_key:
            self.action_button_widgets[store_key] = button
        return frame

    def make_chart_panel_header(self, parent: tk.Widget, title: str, indicator_var: tk.StringVar, command) -> tk.Frame:
        header = tk.Frame(parent, bg=PANE_HEADER_BG, height=32, highlightthickness=1, highlightbackground=PANE_BORDER, bd=0)
        header.pack_propagate(False)
        toggle = tk.Button(
            header,
            textvariable=indicator_var,
            command=command,
            bg=PANE_HEADER_BG,
            fg=ACTION_TEXT,
            activebackground=PANE_HEADER_BG,
            activeforeground="#ffffff",
            highlightthickness=0,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            width=2,
            cursor="hand2",
            padx=0,
            pady=0,
        )
        toggle.pack(side="left", padx=(6, 4), pady=2)
        tk.Label(header, text=title, bg=PANE_HEADER_BG, fg=ACTION_TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        return header

    def make_paned_window(self, parent: tk.Widget) -> tk.PanedWindow:
        cfg_full = dict(
            orient="vertical",
            sashwidth=12,
            sashpad=2,
            bg=PANE_BORDER,
            bd=0,
            relief="flat",
            opaqueresize=True,
            sashrelief="raised",
            sashcursor="sb_v_double_arrow",
            showhandle=True,
            handlesize=10,
            handlepad=0,
        )
        try:
            return tk.PanedWindow(parent, **cfg_full)
        except tk.TclError:
            cfg_safe = dict(
                orient="vertical",
                sashwidth=12,
                sashpad=2,
                bg=PANE_BORDER,
                bd=0,
                relief="flat",
                opaqueresize=True,
                sashrelief="raised",
                sashcursor="sb_v_double_arrow",
            )
            return tk.PanedWindow(parent, **cfg_safe)

    def set_panel_body_visible(self, panel_body: tk.Frame, visible: bool) -> None:
        manager = str(panel_body.winfo_manager())
        if visible:
            if manager != "pack":
                panel_body.pack(fill="both", expand=True)
        elif manager == "pack":
            panel_body.pack_forget()

    def current_chart_split_y(self) -> int:
        try:
            return int(float(self.chart_panes.sash_coord(0)[1]))
        except Exception:
            return int(self.chart_split_y)