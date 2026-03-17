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

        self.base_trading_lot_var = tk.StringVar(value=saved_state.base_trading_lot)
        self.cost_coeff_1_var = tk.StringVar(value=saved_state.cost_coeff_1)
        self.cost_coeff_2_var = tk.StringVar(value=saved_state.cost_coeff_2)
        self.cost_coeff_1_enabled_var = tk.BooleanVar(value=saved_state.cost_coeff_1_enabled)
        self.cost_coeff_2_enabled_var = tk.BooleanVar(value=saved_state.cost_coeff_2_enabled)
        self.mutual_exclusion_var = tk.BooleanVar(value=saved_state.mutual_exclusion_enabled)

        self.apply_long_ratio_var = tk.BooleanVar(value=saved_state.apply_long_ratio)
        self.apply_short_ratio_var = tk.BooleanVar(value=saved_state.apply_short_ratio)
        self.apply_common_ratio_var = tk.BooleanVar(value=saved_state.apply_common_ratio)

        self.manual_lot_1_label_var = tk.StringVar(value="Итог EURUSD")
        self.manual_lot_2_label_var = tk.StringVar(value="Итог USDCHF")
        self.final_lot_1_var = tk.StringVar(value="0.00")
        self.final_lot_2_var = tk.StringVar(value="0.00")
        self.header_symbol_1_var = tk.StringVar(value="EURO")
        self.header_symbol_2_var = tk.StringVar(value="USD")
        self.action_pair_1_var = tk.StringVar(value=saved_state.symbol_1)
        self.action_pair_2_var = tk.StringVar(value=saved_state.symbol_2)

        self.status_var = tk.StringVar(value="idle")
        self.account_var = tk.StringVar(value="-")
        self.last_bar_time_var = tk.StringVar(value="-")
        self.trade_hint_var = tk.StringVar(value="-")
        self.auto_relation_var = tk.StringVar(value="-")

        self.range_long_var = tk.StringVar(value="-")
        self.range_short_var = tk.StringVar(value="-")
        self.range_common_var = tk.StringVar(value="-")

        self.selection_range_var = tk.StringVar(value="-")
        self.selection_pair_1_var = tk.StringVar(value="-")
        self.selection_pair_2_var = tk.StringVar(value="-")
        self.selection_diff_var = tk.StringVar(value="-")

        self.width_adjust_px = int(saved_state.width_adjust_px)
        self.height_adjust_px = int(saved_state.height_adjust_px)
        self.pair_gap_adjust_px = int(saved_state.pair_gap_adjust_px)
        self.chart_split_y = int(saved_state.chart_split_y)
        self.sizing_collapsed = bool(saved_state.sizing_collapsed)
        self.candle_collapsed = bool(saved_state.candle_collapsed)
        self.line_collapsed = bool(saved_state.line_collapsed)

        self.width_size_var = tk.StringVar(value=f"{self.width_adjust_px:+d}px")
        self.height_size_var = tk.StringVar(value=f"{self.height_adjust_px:+d}px")
        self.pair_gap_size_var = tk.StringVar(value=f"{self.pair_gap_adjust_px:+d}px")
        self.sizing_toggle_var = tk.StringVar()
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

        self.scroll_canvas: tk.Canvas | None = None
        self.scroll_body: ttk.Frame | None = None
        self.scroll_window_id: int | None = None
        self.main_root_frame: ttk.Frame | None = None

        self.build_ui()
        self._bind_global_scroll()

    def build_ui(self) -> None:
        shell = ttk.Frame(self)
        shell.pack(fill="both", expand=True)

        self.scroll_canvas = tk.Canvas(shell, highlightthickness=0, bd=0)
        v_scroll = ttk.Scrollbar(shell, orient="vertical", command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=v_scroll.set)

        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        self.scroll_body = ttk.Frame(self.scroll_canvas)
        self.scroll_window_id = self.scroll_canvas.create_window((0, 0), window=self.scroll_body, anchor="nw")

        self.scroll_body.bind("<Configure>", self._on_scroll_body_configure)
        self.scroll_canvas.bind("<Configure>", self._on_scroll_canvas_configure)

        self.main_root_frame = ttk.Frame(self.scroll_body, padding=12)
        self.main_root_frame.pack(fill="both", expand=True)

        build_controls(self, self.main_root_frame)
        build_info_blocks(self, self.main_root_frame)
        build_chart_area(self, self.main_root_frame)

        self.after_idle(self._refresh_global_scrollregion)

    def _on_scroll_body_configure(self, _event) -> None:
        self._refresh_global_scrollregion()

    def _on_scroll_canvas_configure(self, event) -> None:
        if self.scroll_canvas is None or self.scroll_window_id is None:
            return
        self.scroll_canvas.itemconfigure(self.scroll_window_id, width=max(1, int(event.width)))
        self.after_idle(self._refresh_global_scrollregion)

    def _refresh_global_scrollregion(self) -> None:
        if self.scroll_canvas is None:
            return
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _bind_global_scroll(self) -> None:
        self.bind_all("<MouseWheel>", self._on_global_mousewheel, add="+")
        self.bind_all("<Shift-MouseWheel>", self._on_global_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_global_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_global_mousewheel, add="+")

    def _is_scroll_excluded_widget(self, widget) -> bool:
        excluded = {
            getattr(self, "candle_canvas", None),
            getattr(self, "line_canvas", None),
            getattr(self, "line_zoom_scale", None),
        }
        current = widget
        while current is not None:
            if current in excluded:
                return True
            current = getattr(current, "master", None)
        return False

    def _on_global_mousewheel(self, event) -> str | None:
        if self.scroll_canvas is None:
            return None
        if self._is_scroll_excluded_widget(getattr(event, "widget", None)):
            return None

        if getattr(event, "num", None) == 4:
            delta_units = -3
        elif getattr(event, "num", None) == 5:
            delta_units = 3
        else:
            delta = int(getattr(event, "delta", 0) or 0)
            if delta == 0:
                return None
            delta_units = -3 if delta > 0 else 3

        self.scroll_canvas.yview_scroll(delta_units, "units")
        return "break"

    def make_action_label(self, parent: tk.Widget, text_var: tk.StringVar) -> tk.Label:
        return tk.Label(parent, textvariable=text_var, bg=ACTION_BG, fg=ACTION_TEXT, font=("Segoe UI", 10, "bold"), padx=0, pady=0)

    def make_color_marker(self, parent: tk.Widget, color_key: str, arrow_text: str) -> tk.Label:
        marker = tk.Label(parent, text=arrow_text, width=2, bg=self.chart_colors[color_key], fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="solid", bd=1, cursor="hand2", padx=2, pady=1)
        marker.bind("<Button-1>", lambda _event, key=color_key: self.controller.pick_color(key))
        return marker

    def make_action_button(self, parent: tk.Widget, text: str, command, bg_color: str, width_px: int, height_px: int = 28, store_key: str | None = None) -> tk.Frame:
        frame = tk.Frame(parent, width=width_px, height=height_px, bg=ACTION_BG, highlightthickness=0, bd=0)
        frame.pack_propagate(False)
        button = tk.Button(frame, text=text, command=command, bg=bg_color, fg="#ffffff", activebackground=bg_color, activeforeground="#ffffff", highlightthickness=0, relief="flat", bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2", padx=0, pady=0)
        button.pack(fill="both", expand=True)
        if store_key:
            self.action_button_widgets[store_key] = button
        return frame

    def make_chart_panel_header(self, parent: tk.Widget, title: str, indicator_var: tk.StringVar, command) -> tk.Frame:
        header = tk.Frame(parent, bg=PANE_HEADER_BG, height=32, highlightthickness=1, highlightbackground=PANE_BORDER, bd=0)
        header.pack_propagate(False)
        toggle = tk.Button(header, textvariable=indicator_var, command=command, bg=PANE_HEADER_BG, fg=ACTION_TEXT, activebackground=PANE_HEADER_BG, activeforeground="#ffffff", highlightthickness=0, relief="flat", bd=0, font=("Segoe UI", 10, "bold"), width=2, cursor="hand2", padx=0, pady=0)
        toggle.pack(side="left", padx=(6, 4), pady=2)
        tk.Label(header, text=title, bg=PANE_HEADER_BG, fg=ACTION_TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        return header

    def make_paned_window(self, parent: tk.Widget) -> tk.PanedWindow:
        cfg_full = dict(orient="vertical", sashwidth=12, sashpad=2, bg=PANE_BORDER, bd=0, relief="flat", opaqueresize=True, sashrelief="raised", sashcursor="sb_v_double_arrow", showhandle=True, handlesize=10, handlepad=0)
        try:
            return tk.PanedWindow(parent, **cfg_full)
        except tk.TclError:
            cfg_safe = dict(orient="vertical", sashwidth=12, sashpad=2, bg=PANE_BORDER, bd=0, relief="flat", opaqueresize=True, sashrelief="raised", sashcursor="sb_v_double_arrow")
            return tk.PanedWindow(parent, **cfg_safe)

    def set_panel_body_visible(self, panel_body: tk.Frame, visible: bool) -> None:
        manager = str(panel_body.winfo_manager())
        if visible:
            if manager != "pack":
                panel_body.pack(fill="both", expand=True)
        elif manager == "pack":
            panel_body.pack_forget()
        self.after_idle(self._refresh_global_scrollregion)

    def current_chart_split_y(self) -> int:
        try:
            return int(float(self.chart_panes.sash_coord(0)[1]))
        except Exception:
            return int(self.chart_split_y)
