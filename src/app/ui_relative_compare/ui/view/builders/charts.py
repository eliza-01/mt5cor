from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.app.ui_relative_compare.constants import ACTION_BG, ACTION_TEXT, PANE_BORDER, PANE_MIN_EXPANDED_BOTTOM, PANE_MIN_EXPANDED_TOP


def build_chart_area(window, parent) -> None:
    chart_wrap = ttk.LabelFrame(parent, text="Сравнение свечей", padding=8)
    chart_wrap.pack(fill="both", expand=True, pady=(10, 0))

    chart_layout = ttk.Frame(chart_wrap)
    chart_layout.pack(fill="both", expand=True)

    window.left_chart_panel = ttk.Frame(chart_layout, width=200)
    window.left_chart_panel.pack(side="left", fill="y")
    window.left_chart_panel.pack_propagate(False)

    ttk.Label(window.left_chart_panel, text="Агрегация ленты", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 10))
    ttk.Label(window.left_chart_panel, text="Баров в 1 свече").pack(anchor="w")
    ttk.Entry(window.left_chart_panel, textvariable=window.aggregate_bars_var, width=10).pack(anchor="w", pady=(4, 10))
    ttk.Button(window.left_chart_panel, text="Применить", command=window.controller.render_once).pack(anchor="w", pady=(0, 10))
    ttk.Label(window.left_chart_panel, text="Текущая сборка").pack(anchor="w")
    ttk.Label(window.left_chart_panel, textvariable=window.aggregate_info_var).pack(anchor="w", pady=(4, 10))

    ttk.Separator(chart_layout, orient="vertical").pack(side="left", fill="y", padx=8)

    charts_right = ttk.Frame(chart_layout)
    charts_right.pack(side="left", fill="both", expand=True)
    charts_right.columnconfigure(0, weight=1)
    charts_right.rowconfigure(1, weight=1)

    build_action_bar(window, charts_right)
    build_panes(window, charts_right)


def build_action_bar(window, parent) -> None:
    window.action_bar = tk.Frame(parent, bg=ACTION_BG, height=78, highlightthickness=0, bd=0)
    window.action_bar.grid(row=0, column=0, sticky="ew")
    window.action_bar.grid_propagate(False)

    legend_wrap = tk.Frame(window.action_bar, bg=ACTION_BG)
    legend_wrap.pack(side="left", fill="y", padx=(10, 6))

    window.legend_label_1 = window.make_action_label(legend_wrap, window.header_symbol_1_var)
    window.legend_label_1.pack(side="left", padx=(0, 6))
    window.color_marker_widgets["pair_1_up"] = window.make_color_marker(legend_wrap, "pair_1_up", "↑")
    window.color_marker_widgets["pair_1_up"].pack(side="left", padx=(0, 4), pady=8)
    window.color_marker_widgets["pair_1_down"] = window.make_color_marker(legend_wrap, "pair_1_down", "↓")
    window.color_marker_widgets["pair_1_down"].pack(side="left", padx=(0, 14), pady=8)

    window.legend_label_2 = window.make_action_label(legend_wrap, window.header_symbol_2_var)
    window.legend_label_2.pack(side="left", padx=(0, 6))
    window.color_marker_widgets["pair_2_up"] = window.make_color_marker(legend_wrap, "pair_2_up", "↑")
    window.color_marker_widgets["pair_2_up"].pack(side="left", padx=(0, 4), pady=8)
    window.color_marker_widgets["pair_2_down"] = window.make_color_marker(legend_wrap, "pair_2_down", "↓")
    window.color_marker_widgets["pair_2_down"].pack(side="left", padx=(0, 10), pady=8)

    toolbar_right = tk.Frame(window.action_bar, bg=ACTION_BG)
    toolbar_right.pack(side="right", padx=(6, 10), pady=6)

    global_actions = tk.Frame(toolbar_right, bg=ACTION_BG)
    global_actions.pack(side="right", padx=(12, 0), fill="y")
    window.make_action_button(global_actions, "ЗАКРЫТЬ ВСЕ", window.controller.close_current_pair_positions, "#2f2f2f", 112, height_px=28).pack(side="top", pady=(0, 6))
    window.make_action_button(global_actions, "РАЗВЕРНУТЬ", window.controller.reverse_current_pair_positions, "#2f2f2f", 112, height_px=28).pack(side="top")

    pair_actions = tk.Frame(toolbar_right, bg=ACTION_BG)
    pair_actions.pack(side="right", padx=(0, 12), fill="y")

    pair_1_row = tk.Frame(pair_actions, bg=ACTION_BG)
    pair_1_row.pack(side="top", anchor="e", pady=(0, 6))
    tk.Label(pair_1_row, textvariable=window.action_pair_1_var, bg=ACTION_BG, fg=ACTION_TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
    pair_1_col = tk.Frame(pair_1_row, bg=ACTION_BG)
    pair_1_col.pack(side="left")
    window.make_action_button(pair_1_col, "BUY", lambda: window.controller.open_direct_order(1, "buy"), window.chart_colors["pair_1_up"], 66, height_px=24, store_key="pair_1_buy").pack(side="top", pady=(0, 2))
    window.make_action_button(pair_1_col, "SELL", lambda: window.controller.open_direct_order(1, "sell"), window.chart_colors["pair_1_down"], 66, height_px=24, store_key="pair_1_sell").pack(side="top")

    pair_2_row = tk.Frame(pair_actions, bg=ACTION_BG)
    pair_2_row.pack(side="top", anchor="e")
    tk.Label(pair_2_row, textvariable=window.action_pair_2_var, bg=ACTION_BG, fg=ACTION_TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
    pair_2_col = tk.Frame(pair_2_row, bg=ACTION_BG)
    pair_2_col.pack(side="left")
    window.make_action_button(pair_2_col, "BUY", lambda: window.controller.open_direct_order(2, "buy"), window.chart_colors["pair_2_up"], 66, height_px=24, store_key="pair_2_buy").pack(side="top")
    window.make_action_button(pair_2_col, "SELL", lambda: window.controller.open_direct_order(2, "sell"), window.chart_colors["pair_2_down"], 66, height_px=24, store_key="pair_2_sell").pack(side="top", pady=(0, 2))


def build_panes(window, parent) -> None:
    window.chart_panes = window.make_paned_window(parent)
    window.chart_panes.grid(row=1, column=0, sticky="nsew")

    window.candle_wrap = tk.Frame(window.chart_panes, bg=ACTION_BG, highlightthickness=1, highlightbackground=PANE_BORDER, bd=0)
    window.line_wrap = tk.Frame(window.chart_panes, bg=ACTION_BG, highlightthickness=1, highlightbackground=PANE_BORDER, bd=0)

    window.candle_header = window.make_chart_panel_header(window.candle_wrap, title="Свечи", indicator_var=window.candle_toggle_var, command=window.controller.toggle_candle_panel)
    window.candle_header.pack(fill="x", side="top")
    window.candle_body = tk.Frame(window.candle_wrap, bg=ACTION_BG, highlightthickness=0, bd=0)
    window.candle_body.pack(fill="both", expand=True)
    window.candle_canvas = tk.Canvas(window.candle_body, bg=ACTION_BG, highlightthickness=0)
    window.candle_canvas.pack(fill="both", expand=True)

    window.line_header = window.make_chart_panel_header(window.line_wrap, title="Средние скользящие", indicator_var=window.line_toggle_var, command=window.controller.toggle_line_panel)
    window.line_header.pack(fill="x", side="top")
    window.line_body = tk.Frame(window.line_wrap, bg=ACTION_BG, highlightthickness=0, bd=0)
    window.line_body.pack(fill="both", expand=True)
    line_inner = tk.Frame(window.line_body, bg=ACTION_BG)
    line_inner.pack(fill="both", expand=True)

    window.line_zoom_scale = tk.Scale(line_inner, from_=8.0, to=1.0, resolution=0.1, orient="vertical", variable=window.line_zoom_var, showvalue=0, bg=ACTION_BG, fg=ACTION_TEXT, troughcolor="#0b0b0b", highlightthickness=0, bd=0, sliderrelief="flat", width=14, cursor="hand2", command=lambda _v: window.controller.on_line_zoom_changed())
    window.line_zoom_scale.pack(side="left", fill="y", padx=(6, 6), pady=(6, 6))
    window.line_zoom_scale.bind("<MouseWheel>", window.controller.on_line_zoom_wheel)
    window.line_zoom_scale.bind("<Button-4>", window.controller.on_line_zoom_wheel)
    window.line_zoom_scale.bind("<Button-5>", window.controller.on_line_zoom_wheel)

    window.line_canvas = tk.Canvas(line_inner, bg=ACTION_BG, highlightthickness=0)
    window.line_canvas.pack(side="left", fill="both", expand=True)

    window.chart_panes.add(window.candle_wrap, minsize=PANE_MIN_EXPANDED_TOP, stretch="always")
    window.chart_panes.add(window.line_wrap, minsize=PANE_MIN_EXPANDED_BOTTOM, stretch="always")

    window.h_scroll = ttk.Scrollbar(parent, orient="horizontal", command=window.controller.on_scrollbar)
    window.h_scroll.grid(row=2, column=0, sticky="ew", pady=(8, 0))
    window.candle_canvas.configure(xscrollcommand=window.controller.set_scrollbar)
    window.line_canvas.configure(xscrollcommand=window.controller.set_scrollbar)
