from __future__ import annotations

from tkinter import ttk

from .common import kv


def build_info_blocks(window, parent) -> None:
    sizing = ttk.LabelFrame(parent, text="Фиксированные размеры и отступы", padding=10)
    sizing.pack(fill="x", pady=(10, 0))

    ttk.Label(sizing, text="Ширина").grid(row=0, column=0, sticky="w")
    ttk.Button(sizing, text="-1px", command=lambda: window.controller.change_size("width", -1)).grid(row=0, column=1, padx=(6, 4), sticky="w")
    ttk.Button(sizing, text="+1px", command=lambda: window.controller.change_size("width", 1)).grid(row=0, column=2, padx=(0, 10), sticky="w")
    ttk.Label(sizing, textvariable=window.width_size_var).grid(row=0, column=3, padx=(0, 18), sticky="w")

    ttk.Label(sizing, text="Высота").grid(row=0, column=4, sticky="w")
    ttk.Button(sizing, text="-1px", command=lambda: window.controller.change_size("height", -1)).grid(row=0, column=5, padx=(6, 4), sticky="w")
    ttk.Button(sizing, text="+1px", command=lambda: window.controller.change_size("height", 1)).grid(row=0, column=6, padx=(0, 10), sticky="w")
    ttk.Label(sizing, textvariable=window.height_size_var).grid(row=0, column=7, padx=(0, 18), sticky="w")

    ttk.Label(sizing, text="Между парами").grid(row=0, column=8, sticky="w")
    ttk.Button(sizing, text="-1px", command=lambda: window.controller.change_pair_gap(-1)).grid(row=0, column=9, padx=(6, 4), sticky="w")
    ttk.Button(sizing, text="+1px", command=lambda: window.controller.change_pair_gap(1)).grid(row=0, column=10, padx=(0, 10), sticky="w")
    ttk.Label(sizing, textvariable=window.pair_gap_size_var).grid(row=0, column=11, padx=(0, 18), sticky="w")

    ttk.Button(sizing, text="Сбросить", command=window.controller.reset_size).grid(row=0, column=12, sticky="w")

    info = ttk.LabelFrame(parent, text="Текущие параметры", padding=10)
    info.pack(fill="x", pady=(10, 0))
    kv(info, 0, 0, "Статус", window.status_var)
    kv(info, 0, 2, "Аккаунт", window.account_var)
    kv(info, 0, 4, "Последний бар", window.last_bar_time_var)
    kv(info, 1, 0, "Коэф 1/2", window.manual_ratio_1_to_2_var)
    kv(info, 1, 2, "Сборка", window.aggregate_info_var)

    trade = ttk.LabelFrame(parent, text="Текущая логика и объем", padding=10)
    trade.pack(fill="x", pady=(10, 0))
    kv(trade, 0, 0, "Состояние", window.trade_hint_var)

    selection = ttk.LabelFrame(parent, text="Выбранный отрезок close-to-close", padding=10)
    selection.pack(fill="x", pady=(10, 0))
    kv(selection, 0, 0, "Отрезок", window.selection_range_var)
    kv(selection, 1, 0, "Пара 1", window.selection_pair_1_var)
    kv(selection, 1, 2, "Пара 2", window.selection_pair_2_var)
    kv(selection, 1, 4, "Diff", window.selection_diff_var)