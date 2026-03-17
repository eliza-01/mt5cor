from __future__ import annotations

from tkinter import ttk

from .common import kv


def build_info_blocks(window, parent) -> None:
    sizing_wrap = ttk.LabelFrame(parent, text="Размеры и отступы", padding=8)
    sizing_wrap.pack(fill="x", pady=(10, 0))
    header = ttk.Frame(sizing_wrap)
    header.pack(fill="x")
    ttk.Button(header, textvariable=window.sizing_toggle_var, width=2, command=window.controller.toggle_sizing_panel).pack(side="left")
    ttk.Label(header, text="Показать / скрыть").pack(side="left", padx=(6, 0))

    window.sizing_body = ttk.Frame(sizing_wrap)
    window.sizing_body.pack(fill="x", pady=(8, 0))

    ttk.Label(window.sizing_body, text="Ширина").grid(row=0, column=0, sticky="w")
    ttk.Button(window.sizing_body, text="-1px", command=lambda: window.controller.change_size("width", -1)).grid(row=1, column=0, padx=(0, 4), sticky="w")
    ttk.Button(window.sizing_body, text="+1px", command=lambda: window.controller.change_size("width", 1)).grid(row=1, column=1, padx=(0, 10), sticky="w")
    ttk.Label(window.sizing_body, textvariable=window.width_size_var).grid(row=1, column=2, padx=(0, 18), sticky="w")

    ttk.Label(window.sizing_body, text="Высота").grid(row=2, column=0, sticky="w", pady=(10, 0))
    ttk.Button(window.sizing_body, text="-1px", command=lambda: window.controller.change_size("height", -1)).grid(row=3, column=0, padx=(0, 4), sticky="w")
    ttk.Button(window.sizing_body, text="+1px", command=lambda: window.controller.change_size("height", 1)).grid(row=3, column=1, padx=(0, 10), sticky="w")
    ttk.Label(window.sizing_body, textvariable=window.height_size_var).grid(row=3, column=2, padx=(0, 18), sticky="w")

    ttk.Label(window.sizing_body, text="Между парами").grid(row=4, column=0, sticky="w", pady=(10, 0))
    ttk.Button(window.sizing_body, text="-1px", command=lambda: window.controller.change_pair_gap(-1)).grid(row=5, column=0, padx=(0, 4), sticky="w")
    ttk.Button(window.sizing_body, text="+1px", command=lambda: window.controller.change_pair_gap(1)).grid(row=5, column=1, padx=(0, 10), sticky="w")
    ttk.Label(window.sizing_body, textvariable=window.pair_gap_size_var).grid(row=5, column=2, padx=(0, 18), sticky="w")
    ttk.Button(window.sizing_body, text="Сбросить", command=window.controller.reset_size).grid(row=5, column=3, sticky="w")

    info = ttk.LabelFrame(parent, text="Текущие параметры", padding=10)
    info.pack(fill="x", pady=(10, 0))
    kv(info, 0, 0, "Статус", window.status_var)
    kv(info, 0, 2, "Аккаунт", window.account_var)
    kv(info, 0, 4, "Последний бар", window.last_bar_time_var)
    kv(info, 1, 0, "Сборка", window.aggregate_info_var)
    kv(info, 1, 2, "Связь пар", window.auto_relation_var)

    stats = ttk.LabelFrame(parent, text="Статистика диапазонов", padding=10)
    stats.pack(fill="x", pady=(10, 0))
    ttk.Checkbutton(stats, variable=window.apply_long_ratio_var, command=window.controller.on_ratio_checkbox_changed).grid(row=0, column=0, sticky="w")
    ttk.Label(stats, textvariable=window.range_long_var).grid(row=0, column=1, sticky="w")
    ttk.Checkbutton(stats, variable=window.apply_short_ratio_var, command=window.controller.on_ratio_checkbox_changed).grid(row=1, column=0, sticky="w")
    ttk.Label(stats, textvariable=window.range_short_var).grid(row=1, column=1, sticky="w")
    ttk.Checkbutton(stats, variable=window.apply_common_ratio_var, command=window.controller.on_ratio_checkbox_changed).grid(row=2, column=0, sticky="w")
    ttk.Label(stats, textvariable=window.range_common_var).grid(row=2, column=1, sticky="w")

    trade = ttk.LabelFrame(parent, text="Текущий перекос и лоты", padding=10)
    trade.pack(fill="x", pady=(10, 0))
    kv(trade, 0, 0, "Состояние", window.trade_hint_var)

    selection = ttk.LabelFrame(parent, text="Выбранный отрезок close-to-close", padding=10)
    selection.pack(fill="x", pady=(10, 0))
    ttk.Label(selection, textvariable=window.selection_range_var, justify="left").pack(anchor="w")
    ttk.Label(selection, textvariable=window.selection_pair_1_var, justify="left").pack(anchor="w")
    ttk.Label(selection, textvariable=window.selection_pair_2_var, justify="left").pack(anchor="w")
    ttk.Label(selection, textvariable=window.selection_diff_var, justify="left").pack(anchor="w")
