from __future__ import annotations

from tkinter import ttk

from src.app.ui_relative_compare.constants import COMMON_SYMBOLS, TIMEFRAME_MINUTES


def build_controls(window, parent) -> None:
    controls = ttk.LabelFrame(parent, text="Параметры", padding=10)
    controls.pack(fill="x")

    ttk.Label(controls, text="Пара 1").grid(row=0, column=0, sticky="w")
    window.symbol_1_box = ttk.Combobox(controls, textvariable=window.symbol_1_var, values=COMMON_SYMBOLS, width=12)
    window.symbol_1_box.grid(row=0, column=1, padx=(6, 14), sticky="w")

    ttk.Label(controls, text="Пара 2").grid(row=0, column=2, sticky="w")
    window.symbol_2_box = ttk.Combobox(controls, textvariable=window.symbol_2_var, values=COMMON_SYMBOLS, width=12)
    window.symbol_2_box.grid(row=0, column=3, padx=(6, 14), sticky="w")

    ttk.Label(controls, text="Timeframe").grid(row=0, column=4, sticky="w")
    ttk.Combobox(controls, textvariable=window.timeframe_var, values=list(TIMEFRAME_MINUTES.keys()), state="readonly", width=8).grid(row=0, column=5, padx=(6, 14), sticky="w")

    ttk.Label(controls, text="Баров в ленте").grid(row=0, column=6, sticky="w")
    ttk.Entry(controls, textvariable=window.visible_bars_var, width=8).grid(row=0, column=7, padx=(6, 14), sticky="w")

    ttk.Label(controls, text="Refresh ms").grid(row=0, column=8, sticky="w")
    ttk.Entry(controls, textvariable=window.refresh_ms_var, width=8).grid(row=0, column=9, padx=(6, 14), sticky="w")

    ttk.Label(controls, text="Базовый торговый лот").grid(row=1, column=0, sticky="w", pady=(10, 0))
    ttk.Entry(controls, textvariable=window.base_trading_lot_var, width=8).grid(row=1, column=1, padx=(6, 14), pady=(10, 0), sticky="w")

    ttk.Label(controls, text="Баров в 1 свече").grid(row=1, column=2, sticky="w", pady=(10, 0))
    ttk.Entry(controls, textvariable=window.aggregate_bars_var, width=8).grid(row=1, column=3, padx=(6, 14), pady=(10, 0), sticky="w")

    coeff = ttk.LabelFrame(controls, text="Коэффициент стоимости", padding=8)
    coeff.grid(row=1, column=4, columnspan=6, rowspan=2, sticky="w", padx=(0, 14), pady=(10, 0))

    ttk.Checkbutton(coeff, variable=window.cost_coeff_1_enabled_var, command=window.controller.on_cost_coeff_changed).grid(row=0, column=0, sticky="w")
    ttk.Label(coeff, textvariable=window.action_pair_1_var).grid(row=0, column=1, sticky="w", padx=(2, 6))
    ttk.Entry(coeff, textvariable=window.cost_coeff_1_var, width=8).grid(row=0, column=2, sticky="w", padx=(0, 14))

    ttk.Checkbutton(coeff, variable=window.cost_coeff_2_enabled_var, command=window.controller.on_cost_coeff_changed).grid(row=0, column=3, sticky="w")
    ttk.Label(coeff, textvariable=window.action_pair_2_var).grid(row=0, column=4, sticky="w", padx=(2, 6))
    ttk.Entry(coeff, textvariable=window.cost_coeff_2_var, width=8).grid(row=0, column=5, sticky="w")

    ttk.Label(controls, textvariable=window.manual_lot_1_label_var).grid(row=2, column=0, pady=(10, 0), sticky="w")
    ttk.Label(controls, textvariable=window.final_lot_1_var).grid(row=2, column=1, pady=(10, 0), sticky="w")
    ttk.Label(controls, textvariable=window.manual_lot_2_label_var).grid(row=2, column=2, pady=(10, 0), sticky="w")
    ttk.Label(controls, textvariable=window.final_lot_2_var).grid(row=2, column=3, pady=(10, 0), sticky="w")

    ttk.Checkbutton(controls, text="Взаимоисключение движения", variable=window.mutual_exclusion_var, command=window.controller.on_toggle_mutual_exclusion).grid(row=2, column=10, columnspan=2, pady=(10, 0), sticky="w")

    ttk.Button(controls, text="Подключить MT5", command=window.controller.connect_mt5).grid(row=2, column=12, pady=(10, 0), sticky="w")
    ttk.Button(controls, text="Старт", command=window.controller.start_live).grid(row=2, column=13, pady=(10, 0), sticky="w")
    ttk.Button(controls, text="Стоп", command=window.controller.stop_live).grid(row=2, column=14, pady=(10, 0), sticky="w")
    ttk.Button(controls, text="Разовый рендер", command=window.controller.render_once).grid(row=2, column=15, pady=(10, 0), sticky="w")
