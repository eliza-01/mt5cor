# src/app/ui_relative_compare/ui/app.py
# Tk application for scrollable fixed-size relative candles, direct per-pair SELL/BUY buttons,
# auto/manual volume mode, close-by-pair with PnL, persistent UI settings, interval selection stats,
# and opposite-position opening.
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.app.ui_relative_compare.constants import COMMON_SYMBOLS, TIMEFRAME_MINUTES
from src.app.ui_relative_compare.models import RelativeMetrics, RenderSnapshot
from src.app.ui_relative_compare.services.market import (
    build_render_snapshot,
    calculate_relative_metrics,
    load_two_symbols,
)
from src.app.ui_relative_compare.services.trading import close_pair_positions, open_pair_positions, reverse_pair_positions
from src.app.ui_relative_compare.services.ui_state import UIState, load_ui_state, save_ui_state
from src.app.ui_relative_compare.ui.chart import RelativeChart
from src.broker.mt5_client import MT5Client
from src.common.settings import load_settings


class RelativeCompareUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MT5 Relative Compare")

        self.base_cfg = load_settings()
        self.saved_state = load_ui_state(self.base_cfg)

        self.geometry(self.saved_state.window_geometry or "1380x980")
        self.minsize(1240, 860)

        self.client: MT5Client | None = None
        self.connected = False
        self.live_job: str | None = None
        self.state_save_job: str | None = None

        self.symbol_1_var = tk.StringVar(value=self.saved_state.symbol_1)
        self.symbol_2_var = tk.StringVar(value=self.saved_state.symbol_2)
        self.timeframe_var = tk.StringVar(value=self.saved_state.timeframe)
        self.calc_bars_var = tk.StringVar(value=self.saved_state.calc_bars)
        self.visible_bars_var = tk.StringVar(value=self.saved_state.visible_bars)
        self.refresh_ms_var = tk.StringVar(value=self.saved_state.refresh_ms)
        self.aggregate_bars_var = tk.StringVar(value=self.saved_state.aggregate_bars)
        self.aggregate_info_var = tk.StringVar(value=f"{self.saved_state.timeframe} x {self.saved_state.aggregate_bars}")
        self.use_ratio_in_divergence_var = tk.BooleanVar(value=self.saved_state.use_ratio_in_divergence)

        self.auto_volume_var = tk.BooleanVar(value=self.saved_state.auto_volume)
        self.manual_lot_1_var = tk.StringVar(value=self.saved_state.manual_lot_1)
        self.manual_lot_2_var = tk.StringVar(value=self.saved_state.manual_lot_2)
        self.manual_lot_1_label_var = tk.StringVar(value="Lot EURUSD")
        self.manual_lot_2_label_var = tk.StringVar(value="Lot AUDUSD")
        self.header_symbol_1_var = tk.StringVar(value="EURO")
        self.header_symbol_2_var = tk.StringVar(value="AUD")

        self.status_var = tk.StringVar(value="idle")
        self.account_var = tk.StringVar(value="-")
        self.ppm_1_var = tk.StringVar(value="-")
        self.ppm_2_var = tk.StringVar(value="-")
        self.ratio_1_to_2_var = tk.StringVar(value="-")
        self.ratio_2_to_1_var = tk.StringVar(value="-")
        self.last_bar_time_var = tk.StringVar(value="-")
        self.trade_hint_var = tk.StringVar(value="-")

        self.selection_range_var = tk.StringVar(value="-")
        self.selection_pair_1_var = tk.StringVar(value="-")
        self.selection_pair_2_var = tk.StringVar(value="-")
        self.selection_diff_var = tk.StringVar(value="-")

        self.width_adjust_px = int(self.saved_state.width_adjust_px)
        self.height_adjust_px = int(self.saved_state.height_adjust_px)
        self.pair_gap_adjust_px = int(self.saved_state.pair_gap_adjust_px)

        self.width_size_var = tk.StringVar(value=f"{self.width_adjust_px:+d}px")
        self.height_size_var = tk.StringVar(value=f"{self.height_adjust_px:+d}px")
        self.pair_gap_size_var = tk.StringVar(value=f"{self.pair_gap_adjust_px:+d}px")

        self.relative_metrics: RelativeMetrics | None = None
        self.current_snapshot: RenderSnapshot | None = None

        self.selected_start_index: int | None = None
        self.selected_end_index: int | None = None

        self.drag_start_x = 0
        self.drag_active = False

        self._build_ui()
        self._bind_state_persistence()
        self._update_symbol_labels()
        self._update_manual_volume_state()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        controls = ttk.LabelFrame(root, text="Параметры", padding=10)
        controls.pack(fill="x")

        ttk.Label(controls, text="Пара 1").grid(row=0, column=0, sticky="w")
        self.symbol_1_box = ttk.Combobox(controls, textvariable=self.symbol_1_var, values=COMMON_SYMBOLS, width=12)
        self.symbol_1_box.grid(row=0, column=1, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Пара 2").grid(row=0, column=2, sticky="w")
        self.symbol_2_box = ttk.Combobox(controls, textvariable=self.symbol_2_var, values=COMMON_SYMBOLS, width=12)
        self.symbol_2_box.grid(row=0, column=3, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Timeframe").grid(row=0, column=4, sticky="w")
        ttk.Combobox(
            controls,
            textvariable=self.timeframe_var,
            values=list(TIMEFRAME_MINUTES.keys()),
            state="readonly",
            width=8,
        ).grid(row=0, column=5, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Баров для расчёта").grid(row=0, column=6, sticky="w")
        ttk.Entry(controls, textvariable=self.calc_bars_var, width=8).grid(row=0, column=7, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Баров в ленте").grid(row=0, column=8, sticky="w")
        ttk.Entry(controls, textvariable=self.visible_bars_var, width=8).grid(row=0, column=9, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Refresh ms").grid(row=0, column=10, sticky="w")
        ttk.Entry(controls, textvariable=self.refresh_ms_var, width=8).grid(row=0, column=11, padx=(6, 14), sticky="w")

        ttk.Checkbutton(
            controls,
            text="Расхождение с коэф",
            variable=self.use_ratio_in_divergence_var,
            command=self.on_toggle_divergence_mode,
        ).grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="w")

        ttk.Checkbutton(
            controls,
            text="Объем автоматически",
            variable=self.auto_volume_var,
            command=self.on_toggle_auto_volume,
        ).grid(row=1, column=2, columnspan=2, pady=(10, 0), sticky="w")

        ttk.Label(controls, textvariable=self.manual_lot_1_label_var).grid(row=1, column=4, pady=(10, 0), sticky="w")
        self.manual_lot_1_entry = ttk.Entry(controls, textvariable=self.manual_lot_1_var, width=8)
        self.manual_lot_1_entry.grid(row=1, column=5, padx=(6, 14), pady=(10, 0), sticky="w")

        ttk.Label(controls, textvariable=self.manual_lot_2_label_var).grid(row=1, column=6, pady=(10, 0), sticky="w")
        self.manual_lot_2_entry = ttk.Entry(controls, textvariable=self.manual_lot_2_var, width=8)
        self.manual_lot_2_entry.grid(row=1, column=7, padx=(6, 14), pady=(10, 0), sticky="w")

        ttk.Button(controls, text="Подключить MT5", command=self.connect_mt5).grid(row=1, column=8, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Рассчитать коэффициент", command=self.calculate_ratio).grid(row=1, column=9, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Старт", command=self.start_live).grid(row=1, column=10, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Стоп", command=self.stop_live).grid(row=1, column=11, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Разовый рендер", command=self.render_once).grid(row=1, column=12, pady=(10, 0), sticky="w")

        sizing = ttk.LabelFrame(root, text="Фиксированные размеры и отступы", padding=10)
        sizing.pack(fill="x", pady=(10, 0))

        ttk.Label(sizing, text="Ширина").grid(row=0, column=0, sticky="w")
        ttk.Button(sizing, text="-1px", command=lambda: self.change_size("width", -1)).grid(row=0, column=1, padx=(6, 4), sticky="w")
        ttk.Button(sizing, text="+1px", command=lambda: self.change_size("width", 1)).grid(row=0, column=2, padx=(0, 10), sticky="w")
        ttk.Label(sizing, textvariable=self.width_size_var).grid(row=0, column=3, padx=(0, 18), sticky="w")

        ttk.Label(sizing, text="Высота").grid(row=0, column=4, sticky="w")
        ttk.Button(sizing, text="-1px", command=lambda: self.change_size("height", -1)).grid(row=0, column=5, padx=(6, 4), sticky="w")
        ttk.Button(sizing, text="+1px", command=lambda: self.change_size("height", 1)).grid(row=0, column=6, padx=(0, 10), sticky="w")
        ttk.Label(sizing, textvariable=self.height_size_var).grid(row=0, column=7, padx=(0, 18), sticky="w")

        ttk.Label(sizing, text="Между парами").grid(row=0, column=8, sticky="w")
        ttk.Button(sizing, text="-1px", command=lambda: self.change_pair_gap(-1)).grid(row=0, column=9, padx=(6, 4), sticky="w")
        ttk.Button(sizing, text="+1px", command=lambda: self.change_pair_gap(1)).grid(row=0, column=10, padx=(0, 10), sticky="w")
        ttk.Label(sizing, textvariable=self.pair_gap_size_var).grid(row=0, column=11, padx=(0, 18), sticky="w")

        ttk.Button(sizing, text="Сбросить", command=self.reset_size).grid(row=0, column=12, sticky="w")

        info = ttk.LabelFrame(root, text="Метрика относительности", padding=10)
        info.pack(fill="x", pady=(10, 0))

        self._kv(info, 0, 0, "Статус", self.status_var)
        self._kv(info, 0, 2, "Аккаунт", self.account_var)
        self._kv(info, 0, 4, "Последний бар", self.last_bar_time_var)

        self._kv(info, 1, 0, "Пара 1 ппм", self.ppm_1_var)
        self._kv(info, 1, 2, "Пара 2 ппм", self.ppm_2_var)
        self._kv(info, 1, 4, "Коэф 1/2", self.ratio_1_to_2_var)
        self._kv(info, 1, 6, "Коэф 2/1", self.ratio_2_to_1_var)

        trade = ttk.LabelFrame(root, text="Текущая логика и объем", padding=10)
        trade.pack(fill="x", pady=(10, 0))
        self._kv(trade, 0, 0, "Состояние", self.trade_hint_var)

        selection = ttk.LabelFrame(root, text="Выбранный отрезок close-to-close", padding=10)
        selection.pack(fill="x", pady=(10, 0))
        self._kv(selection, 0, 0, "Отрезок", self.selection_range_var)
        self._kv(selection, 1, 0, "Пара 1", self.selection_pair_1_var)
        self._kv(selection, 1, 2, "Пара 2", self.selection_pair_2_var)
        self._kv(selection, 1, 4, "Diff", self.selection_diff_var)

        hint = ttk.LabelFrame(root, text="Смысл", padding=10)
        hint.pack(fill="x", pady=(10, 0))
        ttk.Label(
            hint,
            text=(
                "Справа над графиком находятся прямые кнопки SELL/BUY для каждой пары. "
                "Нажатие на кнопку всегда открывает противоположную позицию по второй паре. "
                "Галочка 'Объем автоматически' оставляет текущую логику расчета объема. "
                "При отключении можно задать объем отдельно для каждой пары вручную. "
                "Кнопка 'Закрыть все' закрывает все позиции по двум выбранным символам. "
                "Кнопка 'Развернуть' одновременно закрывает все позиции и открывает их в обратную сторону."
            ),
            wraplength=1300,
        ).pack(anchor="w")

        chart_wrap = ttk.LabelFrame(root, text="Сравнение свечей", padding=8)
        chart_wrap.pack(fill="both", expand=True, pady=(10, 0))

        chart_layout = ttk.Frame(chart_wrap)
        chart_layout.pack(fill="both", expand=True)

        self.left_chart_panel = ttk.Frame(chart_layout, width=200)
        self.left_chart_panel.pack(side="left", fill="y")
        self.left_chart_panel.pack_propagate(False)

        ttk.Label(self.left_chart_panel, text="Агрегация ленты", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 10))
        ttk.Label(self.left_chart_panel, text="Баров в 1 свече").pack(anchor="w")
        ttk.Entry(self.left_chart_panel, textvariable=self.aggregate_bars_var, width=10).pack(anchor="w", pady=(4, 10))
        ttk.Button(self.left_chart_panel, text="Применить", command=self.render_once).pack(anchor="w", pady=(0, 10))
        ttk.Label(self.left_chart_panel, text="Текущая сборка").pack(anchor="w")
        ttk.Label(self.left_chart_panel, textvariable=self.aggregate_info_var).pack(anchor="w", pady=(4, 10))
        ttk.Label(
            self.left_chart_panel,
            text="Итоговая свеча = выбранный timeframe x указанное число баров.",
            wraplength=180,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        ttk.Separator(chart_layout, orient="vertical").pack(side="left", fill="y", padx=8)

        charts_right = ttk.Frame(chart_layout)
        charts_right.pack(side="left", fill="both", expand=True)

        charts_right.columnconfigure(0, weight=1)
        charts_right.rowconfigure(1, weight=1)
        charts_right.rowconfigure(2, weight=0)
        charts_right.rowconfigure(3, weight=0)

        self.chart_header = tk.Frame(charts_right, bg="#111111", height=42)
        self.chart_header.grid(row=0, column=0, sticky="ew")
        self.chart_header.grid_propagate(False)

        header_inner = tk.Frame(self.chart_header, bg="#111111")
        header_inner.pack(side="right", padx=(0, 10), pady=(8, 4))

        self._make_header_label(header_inner, self.header_symbol_1_var).pack(side="left", padx=(0, 6))
        self._make_px_button(header_inner, "SELL", lambda: self.open_direct_order(1, "sell"), 60, 25).pack(side="left", padx=(0, 4))
        self._make_px_button(header_inner, "BUY", lambda: self.open_direct_order(1, "buy"), 60, 25).pack(side="left", padx=(0, 12))

        self._make_header_label(header_inner, self.header_symbol_2_var).pack(side="left", padx=(0, 6))
        self._make_px_button(header_inner, "SELL", lambda: self.open_direct_order(2, "sell"), 60, 25).pack(side="left", padx=(0, 4))
        self._make_px_button(header_inner, "BUY", lambda: self.open_direct_order(2, "buy"), 60, 25).pack(side="left", padx=(0, 16))

        self._make_px_button(header_inner, "ЗАКРЫТЬ ВСЕ", self.close_current_pair_positions, 110, 25).pack(side="left", padx=(0, 8))
        self._make_px_button(header_inner, "РАЗВЕРНУТЬ", self.reverse_current_pair_positions, 110, 25).pack(side="left")

        self.candle_canvas = tk.Canvas(charts_right, bg="#111111", highlightthickness=0)
        self.candle_canvas.grid(row=1, column=0, sticky="nsew")

        self.line_wrap = ttk.Frame(charts_right, height=180)
        self.line_wrap.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.line_wrap.grid_propagate(False)
        self.line_wrap.columnconfigure(0, weight=1)
        self.line_wrap.rowconfigure(0, weight=1)

        self.line_canvas = tk.Canvas(self.line_wrap, bg="#111111", highlightthickness=0, height=180)
        self.line_canvas.grid(row=0, column=0, sticky="nsew")

        self.h_scroll = ttk.Scrollbar(charts_right, orient="horizontal", command=self._on_scrollbar)
        self.h_scroll.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        self.candle_canvas.configure(xscrollcommand=self._set_scrollbar)
        self.line_canvas.configure(xscrollcommand=self._set_scrollbar)

        self.chart = RelativeChart(self.candle_canvas, self.line_canvas)
        self._bind_scroll_events()

    def _make_header_label(self, parent: tk.Widget, text_var: tk.StringVar) -> tk.Label:
        return tk.Label(
            parent,
            textvariable=text_var,
            bg="#111111",
            fg="#d4d4d4",
            font=("Segoe UI", 10, "bold"),
            padx=0,
            pady=0,
        )

    def _make_px_button(
        self,
        parent: tk.Widget,
        text: str,
        command,
        width_px: int,
        height_px: int,
    ) -> tk.Frame:
        frame = tk.Frame(parent, width=width_px, height=height_px, bg="#111111", highlightthickness=0, bd=0)
        frame.pack_propagate(False)

        button = tk.Button(
            frame,
            text=text,
            command=command,
            font=("Segoe UI", 8, "bold"),
            relief="raised",
            bd=1,
            padx=0,
            pady=0,
            cursor="hand2",
        )
        button.pack(fill="both", expand=True)
        return frame

    def _bind_state_persistence(self) -> None:
        tracked = [
            self.symbol_1_var,
            self.symbol_2_var,
            self.timeframe_var,
            self.calc_bars_var,
            self.visible_bars_var,
            self.refresh_ms_var,
            self.aggregate_bars_var,
            self.use_ratio_in_divergence_var,
            self.auto_volume_var,
            self.manual_lot_1_var,
            self.manual_lot_2_var,
        ]
        for var in tracked:
            var.trace_add("write", self._schedule_state_save)

        self.symbol_1_var.trace_add("write", self._on_symbols_changed)
        self.symbol_2_var.trace_add("write", self._on_symbols_changed)
        self.manual_lot_1_var.trace_add("write", self._on_manual_volume_changed)
        self.manual_lot_2_var.trace_add("write", self._on_manual_volume_changed)

        self.bind("<Configure>", self._on_window_configure)

    def _on_window_configure(self, event) -> None:
        if event.widget is self:
            self._schedule_state_save()

    def _schedule_state_save(self, *_args) -> None:
        if self.state_save_job is not None:
            self.after_cancel(self.state_save_job)
        self.state_save_job = self.after(250, self._save_state_now)

    def _save_state_now(self) -> None:
        self.state_save_job = None
        try:
            save_ui_state(self.base_cfg, self._collect_ui_state())
        except Exception:
            pass

    def _collect_ui_state(self) -> UIState:
        return UIState(
            symbol_1=self.symbol_1_var.get().strip() or "EURUSD",
            symbol_2=self.symbol_2_var.get().strip() or "AUDUSD",
            timeframe=self.timeframe_var.get().strip() or "M1",
            calc_bars=self.calc_bars_var.get().strip() or "1440",
            visible_bars=self.visible_bars_var.get().strip() or "120",
            refresh_ms=self.refresh_ms_var.get().strip() or "250",
            aggregate_bars=self.aggregate_bars_var.get().strip() or "1",
            use_ratio_in_divergence=bool(self.use_ratio_in_divergence_var.get()),
            auto_volume=bool(self.auto_volume_var.get()),
            manual_lot_1=self.manual_lot_1_var.get().strip() or "0.10",
            manual_lot_2=self.manual_lot_2_var.get().strip() or "0.10",
            width_adjust_px=int(self.width_adjust_px),
            height_adjust_px=int(self.height_adjust_px),
            pair_gap_adjust_px=int(self.pair_gap_adjust_px),
            window_geometry=str(self.geometry()),
        )

    def _bind_scroll_events(self) -> None:
        for widget in (self.candle_canvas, self.line_canvas):
            widget.bind("<MouseWheel>", self._on_mousewheel_horizontal)
            widget.bind("<Shift-MouseWheel>", self._on_mousewheel_horizontal)
            widget.bind("<Button-4>", self._on_mousewheel_horizontal)
            widget.bind("<Button-5>", self._on_mousewheel_horizontal)
            widget.bind("<ButtonPress-1>", self._on_button_press)
            widget.bind("<B1-Motion>", self._on_scan_drag)
            widget.bind("<ButtonRelease-1>", self._on_button_release)

    def _kv(self, parent: ttk.Widget, row: int, col: int, key: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=key).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
        ttk.Label(parent, textvariable=var).grid(row=row, column=col + 1, sticky="w", padx=(0, 18), pady=4)

    def _set_scrollbar(self, first: str, last: str) -> None:
        self.h_scroll.set(first, last)

    def _on_scrollbar(self, *args) -> None:
        self.candle_canvas.xview(*args)
        self.line_canvas.xview(*args)

    def _sync_canvas_view(self, first_fraction: float) -> None:
        pos = max(0.0, min(1.0, float(first_fraction)))
        self.candle_canvas.xview_moveto(pos)
        self.line_canvas.xview_moveto(pos)

    def _on_mousewheel_horizontal(self, event) -> str:
        if getattr(event, "num", None) == 4:
            delta_units = -3
        elif getattr(event, "num", None) == 5:
            delta_units = 3
        else:
            delta = int(getattr(event, "delta", 0) or 0)
            if delta == 0:
                return "break"
            delta_units = -3 if delta > 0 else 3

        self.candle_canvas.xview_scroll(delta_units, "units")
        self.line_canvas.xview_scroll(delta_units, "units")
        return "break"

    def _on_button_press(self, event) -> str:
        self.drag_start_x = int(event.x)
        self.drag_active = False
        self.candle_canvas.scan_mark(event.x, 0)
        self.line_canvas.scan_mark(event.x, 0)
        return "break"

    def _on_scan_drag(self, event) -> str:
        if abs(int(event.x) - self.drag_start_x) >= 4:
            self.drag_active = True
        self.candle_canvas.scan_dragto(event.x, 0, gain=1)
        self.line_canvas.scan_dragto(event.x, 0, gain=1)
        return "break"

    def _on_button_release(self, event) -> str:
        if not self.drag_active:
            self._handle_chart_click(event.widget, int(event.x))
        self.drag_active = False
        return "break"

    def _handle_chart_click(self, widget: tk.Widget, x_local: int) -> None:
        if self.current_snapshot is None or self.current_snapshot.bars.empty:
            return

        canvas = self.candle_canvas if widget is self.candle_canvas else self.line_canvas
        x_world = float(canvas.canvasx(x_local))
        index = self.chart.get_index_at_x(
            bars_count=len(self.current_snapshot.bars),
            x_world=x_world,
            width_adjust_px=self.width_adjust_px,
            pair_gap_adjust_px=self.pair_gap_adjust_px,
        )
        if index is None:
            return

        if self.selected_start_index is None or self.selected_end_index is not None:
            self.selected_start_index = index
            self.selected_end_index = None
        else:
            self.selected_end_index = index
            if self.selected_end_index < self.selected_start_index:
                self.selected_start_index, self.selected_end_index = self.selected_end_index, self.selected_start_index

        self._redraw_current_snapshot()

    def _normalize_symbol(self, symbol: str) -> str:
        return "".join(ch for ch in symbol.upper() if "A" <= ch <= "Z")[:6] or symbol.upper()

    def _base_label(self, symbol: str) -> str:
        normalized = self._normalize_symbol(symbol)
        base = normalized[:3]
        if base == "EUR":
            return "EURO"
        if base:
            return base
        return symbol.upper()

    def _update_symbol_labels(self) -> None:
        symbol_1 = self.symbol_1_var.get().strip() or "EURUSD"
        symbol_2 = self.symbol_2_var.get().strip() or "AUDUSD"

        self.manual_lot_1_label_var.set(f"Lot {self._normalize_symbol(symbol_1)}")
        self.manual_lot_2_label_var.set(f"Lot {self._normalize_symbol(symbol_2)}")
        self.header_symbol_1_var.set(self._base_label(symbol_1))
        self.header_symbol_2_var.set(self._base_label(symbol_2))

    def _on_symbols_changed(self, *_args) -> None:
        self._update_symbol_labels()
        self._schedule_state_save()

    def _on_manual_volume_changed(self, *_args) -> None:
        if not self.auto_volume_var.get():
            self._update_trade_hint()

    def _update_manual_volume_state(self) -> None:
        state = "disabled" if self.auto_volume_var.get() else "normal"
        self.manual_lot_1_entry.configure(state=state)
        self.manual_lot_2_entry.configure(state=state)

    def connect_mt5(self) -> None:
        try:
            if self.connected:
                self.status_var.set("connected")
                return

            self.client = MT5Client(self.base_cfg)
            self.client.connect()
            self.connected = True
            self.status_var.set("connected")
            self.account_var.set(f"{self.base_cfg.mt5_login} @ {self.base_cfg.mt5_server}")
            self._schedule_state_save()
        except Exception as exc:
            self.status_var.set("connect_error")
            messagebox.showerror("MT5", str(exc))

    def _ensure_connected(self) -> None:
        if not self.connected or self.client is None:
            self.connect_mt5()
        if not self.connected or self.client is None:
            raise RuntimeError("MT5 не подключен")

    def _read_inputs(self) -> tuple[str, str, str, int, int, int, int]:
        symbol_1 = self.symbol_1_var.get().strip()
        symbol_2 = self.symbol_2_var.get().strip()
        timeframe = self.timeframe_var.get().strip()

        if timeframe not in TIMEFRAME_MINUTES:
            raise RuntimeError("Неподдерживаемый timeframe")

        calc_bars = max(20, int(self.calc_bars_var.get().strip() or "1440"))
        visible_bars = max(20, int(self.visible_bars_var.get().strip() or "120"))
        refresh_ms = max(100, int(self.refresh_ms_var.get().strip() or "250"))
        aggregate_bars = max(1, int(self.aggregate_bars_var.get().strip() or "1"))

        if symbol_1 == symbol_2:
            raise RuntimeError("Нужно выбрать две разные пары")

        return symbol_1, symbol_2, timeframe, calc_bars, visible_bars, refresh_ms, aggregate_bars

    def _read_positive_lot(self, raw: str, symbol: str) -> float:
        text = str(raw).strip().replace(",", ".")
        value = float(text)
        if value <= 0:
            raise RuntimeError(f"Объем для {symbol} должен быть больше 0")
        return value

    def _resolve_pair_lots(self, strict: bool = True) -> tuple[float, float]:
        symbol_1 = self.symbol_1_var.get().strip() or "EURUSD"
        symbol_2 = self.symbol_2_var.get().strip() or "AUDUSD"

        if self.auto_volume_var.get():
            if self.current_snapshot is not None:
                return (
                    float(self.current_snapshot.trade_plan.symbol_1_lots),
                    float(self.current_snapshot.trade_plan.symbol_2_lots),
                )

            if self.relative_metrics is None:
                if strict:
                    raise RuntimeError("Для авто-объема сначала нажми 'Рассчитать коэффициент'")
                return self.base_cfg.base_lot_eurusd, self.base_cfg.base_lot_eurusd

            return (
                float(self.base_cfg.base_lot_eurusd),
                float(self.base_cfg.base_lot_eurusd * self.relative_metrics.ratio_1_to_2),
            )

        try:
            return (
                self._read_positive_lot(self.manual_lot_1_var.get(), symbol_1),
                self._read_positive_lot(self.manual_lot_2_var.get(), symbol_2),
            )
        except Exception:
            if strict:
                raise
            return 0.0, 0.0

    def calculate_ratio(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, timeframe, calc_bars, _, _, _ = self._read_inputs()
            frame, meta_1, meta_2 = load_two_symbols(self.client, symbol_1, symbol_2, timeframe, calc_bars)
            self.relative_metrics = calculate_relative_metrics(frame, meta_1.digits, meta_2.digits, timeframe)

            self.ppm_1_var.set(f"{self.relative_metrics.ppm_1:.4f}")
            self.ppm_2_var.set(f"{self.relative_metrics.ppm_2:.4f}")
            self.ratio_1_to_2_var.set(f"{self.relative_metrics.ratio_1_to_2:.6f}")
            self.ratio_2_to_1_var.set(f"{self.relative_metrics.ratio_2_to_1:.6f}")

            self.status_var.set("ratio_ready")
            self._schedule_state_save()
            self.render_once()
        except Exception as exc:
            self.status_var.set("ratio_error")
            messagebox.showerror("Расчёт коэффициента", str(exc))

    def render_once(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            if self.relative_metrics is None:
                raise RuntimeError("Сначала нажми 'Рассчитать коэффициент'")

            symbol_1, symbol_2, timeframe, _, visible_bars, _, aggregate_bars = self._read_inputs()
            prev_x = self.candle_canvas.xview()[0]
            had_snapshot = self.current_snapshot is not None

            snapshot = build_render_snapshot(
                client=self.client,
                cfg=self.base_cfg,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                timeframe=timeframe,
                bars_count=visible_bars,
                ratio_1_to_2=self.relative_metrics.ratio_1_to_2,
                use_ratio_in_divergence=self.use_ratio_in_divergence_var.get(),
                bars_per_candle=aggregate_bars,
            )

            self.current_snapshot = snapshot

            if snapshot.bars.empty:
                return

            self._normalize_selection_indices(len(snapshot.bars))
            self.aggregate_info_var.set(f"{timeframe} x {aggregate_bars} | {len(snapshot.bars)} свечей")
            self.last_bar_time_var.set(str(snapshot.bars.iloc[-1]["time"]))

            self.chart.draw(
                bars=snapshot.bars,
                divergence_series=snapshot.divergence_series,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                ratio_1_to_2=self.relative_metrics.ratio_1_to_2,
                width_adjust_px=self.width_adjust_px,
                height_adjust_px=self.height_adjust_px,
                pair_gap_adjust_px=self.pair_gap_adjust_px,
                divergence_stats=snapshot.divergence_stats,
                trade_plan=snapshot.trade_plan,
                selected_start_index=self.selected_start_index,
                selected_end_index=self.selected_end_index,
            )

            self.update_idletasks()

            if had_snapshot:
                self._sync_canvas_view(prev_x)
            else:
                self._sync_canvas_view(1.0)

            self.status_var.set("rendered")
            self._update_trade_hint()
            self._update_selection_stats()
            self._schedule_state_save()
        except Exception as exc:
            self.status_var.set("render_error")
            messagebox.showerror("Рендер", str(exc))

    def _redraw_current_snapshot(self) -> None:
        if self.current_snapshot is None or self.current_snapshot.bars.empty or self.relative_metrics is None:
            return

        prev_x = self.candle_canvas.xview()[0]
        self._normalize_selection_indices(len(self.current_snapshot.bars))

        symbol_1 = self.symbol_1_var.get().strip()
        symbol_2 = self.symbol_2_var.get().strip()

        self.chart.draw(
            bars=self.current_snapshot.bars,
            divergence_series=self.current_snapshot.divergence_series,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            ratio_1_to_2=self.relative_metrics.ratio_1_to_2,
            width_adjust_px=self.width_adjust_px,
            height_adjust_px=self.height_adjust_px,
            pair_gap_adjust_px=self.pair_gap_adjust_px,
            divergence_stats=self.current_snapshot.divergence_stats,
            trade_plan=self.current_snapshot.trade_plan,
            selected_start_index=self.selected_start_index,
            selected_end_index=self.selected_end_index,
        )

        self.update_idletasks()
        self._sync_canvas_view(prev_x)
        self._update_trade_hint()
        self._update_selection_stats()

    def _normalize_selection_indices(self, bars_count: int) -> None:
        if bars_count <= 0:
            self.selected_start_index = None
            self.selected_end_index = None
            return

        if self.selected_start_index is not None:
            self.selected_start_index = max(0, min(bars_count - 1, int(self.selected_start_index)))

        if self.selected_end_index is not None:
            self.selected_end_index = max(0, min(bars_count - 1, int(self.selected_end_index)))

        if self.selected_start_index is not None and self.selected_end_index is not None:
            if self.selected_end_index < self.selected_start_index:
                self.selected_start_index, self.selected_end_index = self.selected_end_index, self.selected_start_index

    def _update_trade_hint(self) -> None:
        snapshot = self.current_snapshot
        if snapshot is None:
            self.trade_hint_var.set("-")
            return

        mode_text = "AUTO" if self.auto_volume_var.get() else "MANUAL"

        try:
            lot_1, lot_2 = self._resolve_pair_lots(strict=not self.auto_volume_var.get())
            self.trade_hint_var.set(
                f"{mode_text} | {snapshot.trade_plan.symbol_1} {lot_1:.2f} | "
                f"{snapshot.trade_plan.symbol_2} {lot_2:.2f} | "
                f"лидер {snapshot.trade_plan.leader_symbol} {snapshot.trade_plan.leader_move:.2f} | "
                f"ведомая {snapshot.trade_plan.follower_symbol} {snapshot.trade_plan.follower_move:.2f} | "
                f"подсказка SELL {snapshot.trade_plan.sell_symbol} / BUY {snapshot.trade_plan.buy_symbol}"
            )
        except Exception as exc:
            self.trade_hint_var.set(f"{mode_text} | ошибка объема: {exc}")

    def _update_selection_stats(self) -> None:
        if self.current_snapshot is None or self.current_snapshot.bars.empty:
            self.selection_range_var.set("-")
            self.selection_pair_1_var.set("-")
            self.selection_pair_2_var.set("-")
            self.selection_diff_var.set("-")
            return

        if self.selected_start_index is None:
            self.selection_range_var.set("кликни стартовую пару/точку")
            self.selection_pair_1_var.set("-")
            self.selection_pair_2_var.set("-")
            self.selection_diff_var.set("-")
            return

        bars = self.current_snapshot.bars
        start_index = int(self.selected_start_index)
        end_index = start_index if self.selected_end_index is None else int(self.selected_end_index)

        start_row = bars.iloc[start_index]
        end_row = bars.iloc[end_index]

        if self.selected_end_index is None:
            self.selection_range_var.set(f"START: {start_row['time']} | жду END")
            self.selection_pair_1_var.set("-")
            self.selection_pair_2_var.set("-")
            self.selection_diff_var.set("-")
            return

        move_1_pips = (float(end_row["close_1"]) - float(start_row["close_1"])) / self._pip_size(self.current_snapshot.digits_1)
        move_2_pips = (float(end_row["close_2"]) - float(start_row["close_2"])) / self._pip_size(self.current_snapshot.digits_2)
        diff_pips = move_1_pips - move_2_pips

        symbol_1 = self._format_symbol_for_stats(self.symbol_1_var.get().strip())
        symbol_2 = self._format_symbol_for_stats(self.symbol_2_var.get().strip())

        candles_distance = max(0, end_index - start_index)

        self.selection_range_var.set(
            f"{start_row['time']} -> {end_row['time']} | свечей между точками: {candles_distance}"
        )
        self.selection_pair_1_var.set(f"{symbol_1}: {self._format_pips(move_1_pips)} pip")
        self.selection_pair_2_var.set(f"{symbol_2}: {self._format_pips(move_2_pips)} pip")
        self.selection_diff_var.set(f"diff: {self._format_pips(diff_pips)} pip")

    def _pip_size(self, digits: int) -> float:
        return 0.01 if digits in (2, 3) else 0.0001

    def _format_symbol_for_stats(self, symbol: str) -> str:
        letters = "".join(ch for ch in symbol.upper() if "A" <= ch <= "Z")
        if len(letters) >= 6:
            return f"{letters[:3]}/{letters[3:6]}"
        return symbol

    def _format_pips(self, value: float) -> str:
        text = f"{float(value):+.4f}".rstrip("0").rstrip(".")
        return text if text != "-0" else "0"

    def on_toggle_divergence_mode(self) -> None:
        self._schedule_state_save()
        if self.current_snapshot is not None:
            self.render_once()

    def on_toggle_auto_volume(self) -> None:
        self._update_manual_volume_state()
        self._schedule_state_save()
        self._update_trade_hint()

    def change_size(self, axis: str, delta: int) -> None:
        if axis == "width":
            self.width_adjust_px += delta
            self.width_size_var.set(f"{self.width_adjust_px:+d}px")
        else:
            self.height_adjust_px += delta
            self.height_size_var.set(f"{self.height_adjust_px:+d}px")

        self._schedule_state_save()
        if self.current_snapshot is not None:
            self.render_once()

    def change_pair_gap(self, delta: int) -> None:
        self.pair_gap_adjust_px += delta
        self.pair_gap_size_var.set(f"{self.pair_gap_adjust_px:+d}px")

        self._schedule_state_save()
        if self.current_snapshot is not None:
            self.render_once()

    def reset_size(self) -> None:
        self.width_adjust_px = 0
        self.height_adjust_px = 0
        self.pair_gap_adjust_px = 0

        self.width_size_var.set("0px")
        self.height_size_var.set("0px")
        self.pair_gap_size_var.set("0px")

        self._schedule_state_save()
        if self.current_snapshot is not None:
            self.render_once()

    def _build_direct_order(self, symbol_index: int, side: str) -> tuple[str, str, float, float]:
        symbol_1, symbol_2, _, _, _, _, _ = self._read_inputs()
        lot_1, lot_2 = self._resolve_pair_lots(strict=True)

        if symbol_index == 1 and side == "sell":
            return symbol_1, symbol_2, lot_1, lot_2
        if symbol_index == 1 and side == "buy":
            return symbol_2, symbol_1, lot_2, lot_1
        if symbol_index == 2 and side == "sell":
            return symbol_2, symbol_1, lot_2, lot_1
        if symbol_index == 2 and side == "buy":
            return symbol_1, symbol_2, lot_1, lot_2

        raise RuntimeError("Некорректная команда открытия")

    def open_direct_order(self, symbol_index: int, side: str) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            if self.auto_volume_var.get() and self.relative_metrics is None:
                raise RuntimeError("Для авто-объема сначала нажми 'Рассчитать коэффициент'")

            sell_symbol, buy_symbol, sell_lots, buy_lots = self._build_direct_order(symbol_index, side)
            result = open_pair_positions(
                client=self.client,
                cfg=self.base_cfg,
                sell_symbol=sell_symbol,
                buy_symbol=buy_symbol,
                sell_lots=sell_lots,
                buy_lots=buy_lots,
            )

            self.status_var.set("orders_opened")
            messagebox.showinfo(
                "Позиции открыты",
                (
                    f"SELL {sell_symbol} {result.sell_volume:.2f}\n"
                    f"BUY {buy_symbol} {result.buy_volume:.2f}\n"
                    f"sell_order={result.sell_order} retcode={result.sell_retcode}\n"
                    f"buy_order={result.buy_order} retcode={result.buy_retcode}"
                ),
            )
            if self.current_snapshot is not None:
                self.render_once()
        except Exception as exc:
            self.status_var.set("order_error")
            messagebox.showerror("Открытие противоположных позиций", str(exc))

    def close_current_pair_positions(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, _, _, _, _, _ = self._read_inputs()
            summary = close_pair_positions(self.client, self.base_cfg, symbol_1, symbol_2)
            self.status_var.set("positions_closed")
            messagebox.showinfo(
                "Позиции закрыты",
                (
                    f"Связка: {symbol_1} / {symbol_2}\n"
                    f"Закрыто позиций: {summary.closed_count}\n"
                    f"Сделок MT: {summary.deals_count}\n"
                    f"MT profit: {summary.profit_usd:.2f}\n"
                    f"MT commission: {summary.commission_usd:.2f}\n"
                    f"MT swap: {summary.swap_usd:.2f}\n"
                    f"MT fee: {summary.fee_usd:.2f}\n"
                    f"MT total pnl: {summary.total_pnl_usd:.2f}"
                ),
            )
            if self.current_snapshot is not None:
                self.render_once()
        except Exception as exc:
            self.status_var.set("close_error")
            messagebox.showerror("Закрытие позиций по связке", str(exc))

    def reverse_current_pair_positions(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, _, _, _, _, _ = self._read_inputs()
            summary = reverse_pair_positions(self.client, self.base_cfg, symbol_1, symbol_2)
            self.status_var.set("positions_reversed")

            reopened_lines = []
            for leg in summary.reopened_legs:
                reopened_lines.append(
                    f"{leg.side.upper()} {leg.symbol} {leg.volume:.2f} "
                    f"order={leg.order} retcode={leg.retcode}"
                )

            messagebox.showinfo(
                "Позиции развернуты",
                (
                    f"Связка: {symbol_1} / {symbol_2}\n"
                    f"Закрыто позиций: {summary.close_summary.closed_count}\n"
                    f"Сделок MT: {summary.close_summary.deals_count}\n"
                    f"MT total pnl: {summary.close_summary.total_pnl_usd:.2f}\n\n"
                    f"Открыто в обратную сторону:\n"
                    + "\n".join(reopened_lines)
                ),
            )

            if self.current_snapshot is not None:
                self.render_once()
        except Exception as exc:
            self.status_var.set("reverse_error")
            messagebox.showerror("Разворот позиций по связке", str(exc))

    def start_live(self) -> None:
        try:
            if self.relative_metrics is None:
                raise RuntimeError("Сначала нажми 'Рассчитать коэффициент'")
            self.stop_live()
            self.status_var.set("live")
            self._live_tick()
        except Exception as exc:
            self.status_var.set("live_error")
            messagebox.showerror("Старт", str(exc))

    def _live_tick(self) -> None:
        try:
            self.render_once()
        except Exception:
            pass
        finally:
            try:
                _, _, _, _, _, refresh_ms, _ = self._read_inputs()
            except Exception:
                refresh_ms = 250
            self.live_job = self.after(refresh_ms, self._live_tick)

    def stop_live(self) -> None:
        if self.live_job is not None:
            self.after_cancel(self.live_job)
            self.live_job = None
        if self.status_var.get() == "live":
            self.status_var.set("stopped")

    def on_close(self) -> None:
        try:
            self._save_state_now()
            self.stop_live()
            if self.client is not None and self.connected:
                self.client.shutdown()
        finally:
            self.destroy()


def main() -> None:
    app = RelativeCompareUI()
    app.mainloop()