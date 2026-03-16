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

    ttk.Label(controls, text="Баров для расчёта").grid(row=0, column=6, sticky="w")
    ttk.Entry(controls, textvariable=window.calc_bars_var, width=8).grid(row=0, column=7, padx=(6, 14), sticky="w")

    ttk.Label(controls, text="Баров в ленте").grid(row=0, column=8, sticky="w")
    ttk.Entry(controls, textvariable=window.visible_bars_var, width=8).grid(row=0, column=9, padx=(6, 14), sticky="w")

    ttk.Label(controls, text="Refresh ms").grid(row=0, column=10, sticky="w")
    ttk.Entry(controls, textvariable=window.refresh_ms_var, width=8).grid(row=0, column=11, padx=(6, 14), sticky="w")

    ttk.Checkbutton(controls, text="Расхождение с коэф", variable=window.use_ratio_in_divergence_var, command=window.controller.on_toggle_divergence_mode).grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="w")
    ttk.Checkbutton(controls, text="Объем автоматически", variable=window.auto_volume_var, command=window.controller.on_toggle_auto_volume).grid(row=1, column=2, columnspan=2, pady=(10, 0), sticky="w")

    ttk.Label(controls, textvariable=window.manual_lot_1_label_var).grid(row=1, column=4, pady=(10, 0), sticky="w")
    window.manual_lot_1_entry = ttk.Entry(controls, textvariable=window.manual_lot_1_var, width=8)
    window.manual_lot_1_entry.grid(row=1, column=5, padx=(6, 14), pady=(10, 0), sticky="w")

    ttk.Label(controls, textvariable=window.manual_lot_2_label_var).grid(row=1, column=6, pady=(10, 0), sticky="w")
    window.manual_lot_2_entry = ttk.Entry(controls, textvariable=window.manual_lot_2_var, width=8)
    window.manual_lot_2_entry.grid(row=1, column=7, padx=(6, 14), pady=(10, 0), sticky="w")

    ttk.Button(controls, text="Подключить MT5", command=window.controller.connect_mt5).grid(row=1, column=8, pady=(10, 0), sticky="w")
    ttk.Button(controls, text="Рассчитать коэффициент", command=window.controller.calculate_ratio).grid(row=1, column=9, pady=(10, 0), sticky="w")
    ttk.Button(controls, text="Старт", command=window.controller.start_live).grid(row=1, column=10, pady=(10, 0), sticky="w")
    ttk.Button(controls, text="Стоп", command=window.controller.stop_live).grid(row=1, column=11, pady=(10, 0), sticky="w")
    ttk.Button(controls, text="Разовый рендер", command=window.controller.render_once).grid(row=1, column=12, pady=(10, 0), sticky="w")
