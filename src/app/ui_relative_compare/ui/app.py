
# src/app/ui_relative_compare/ui/app.py
# Tk application for non-mirrored relative candles, divergence mode checkbox,
# close-by-pair with PnL, and opposite-position opening.
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.app.ui_relative_compare.constants import COMMON_SYMBOLS, TIMEFRAME_MINUTES
from src.app.ui_relative_compare.models import RelativeMetrics, RenderSnapshot, TradePlan
from src.app.ui_relative_compare.services.market import (
    build_render_snapshot,
    calculate_relative_metrics,
    load_two_symbols,
)
from src.app.ui_relative_compare.services.trading import close_pair_positions, open_opposite_positions
from src.app.ui_relative_compare.ui.chart import RelativeChart
from src.broker.mt5_client import MT5Client
from src.common.settings import load_settings


class RelativeCompareUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MT5 Relative Compare")
        self.geometry("1360x900")
        self.minsize(1220, 800)

        self.base_cfg = load_settings()
        self.client: MT5Client | None = None
        self.connected = False
        self.live_job: str | None = None

        self.symbol_1_var = tk.StringVar(value="EURUSD")
        self.symbol_2_var = tk.StringVar(value="AUDUSD")
        self.timeframe_var = tk.StringVar(value="M1")
        self.calc_bars_var = tk.StringVar(value="240")
        self.visible_bars_var = tk.StringVar(value="40")
        self.refresh_ms_var = tk.StringVar(value="1000")
        self.use_ratio_in_divergence_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value="idle")
        self.account_var = tk.StringVar(value="-")
        self.ppm_1_var = tk.StringVar(value="-")
        self.ppm_2_var = tk.StringVar(value="-")
        self.ratio_1_to_2_var = tk.StringVar(value="-")
        self.ratio_2_to_1_var = tk.StringVar(value="-")
        self.last_bar_time_var = tk.StringVar(value="-")
        self.trade_hint_var = tk.StringVar(value="-")
        self.width_size_var = tk.StringVar(value="0px")
        self.height_size_var = tk.StringVar(value="0px")

        self.relative_metrics: RelativeMetrics | None = None
        self.current_trade_plan: TradePlan | None = None
        self.current_snapshot: RenderSnapshot | None = None
        self.width_adjust_px = 0
        self.height_adjust_px = 0

        self._build_ui()
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

        ttk.Label(controls, text="Видимых свечей").grid(row=0, column=8, sticky="w")
        ttk.Entry(controls, textvariable=self.visible_bars_var, width=8).grid(row=0, column=9, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Refresh ms").grid(row=0, column=10, sticky="w")
        ttk.Entry(controls, textvariable=self.refresh_ms_var, width=8).grid(row=0, column=11, padx=(6, 14), sticky="w")

        ttk.Checkbutton(
            controls,
            text="Расхождение с коэф",
            variable=self.use_ratio_in_divergence_var,
            command=self.on_toggle_divergence_mode,
        ).grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="w")

        ttk.Button(controls, text="Подключить MT5", command=self.connect_mt5).grid(row=1, column=2, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Рассчитать коэффициент", command=self.calculate_ratio).grid(row=1, column=3, columnspan=2, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Старт", command=self.start_live).grid(row=1, column=5, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Стоп", command=self.stop_live).grid(row=1, column=6, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Разовый рендер", command=self.render_once).grid(row=1, column=7, pady=(10, 0), sticky="w")

        sizing = ttk.LabelFrame(root, text="Общий размер свечей", padding=10)
        sizing.pack(fill="x", pady=(10, 0))

        ttk.Label(sizing, text="Ширина").grid(row=0, column=0, sticky="w")
        ttk.Button(sizing, text="-1px", command=lambda: self.change_size("width", -1)).grid(row=0, column=1, padx=(6, 4), sticky="w")
        ttk.Button(sizing, text="+1px", command=lambda: self.change_size("width", 1)).grid(row=0, column=2, padx=(0, 10), sticky="w")
        ttk.Label(sizing, textvariable=self.width_size_var).grid(row=0, column=3, padx=(0, 18), sticky="w")

        ttk.Label(sizing, text="Высота").grid(row=0, column=4, sticky="w")
        ttk.Button(sizing, text="-1px", command=lambda: self.change_size("height", -1)).grid(row=0, column=5, padx=(6, 4), sticky="w")
        ttk.Button(sizing, text="+1px", command=lambda: self.change_size("height", 1)).grid(row=0, column=6, padx=(0, 10), sticky="w")
        ttk.Label(sizing, textvariable=self.height_size_var).grid(row=0, column=7, padx=(0, 18), sticky="w")

        ttk.Button(sizing, text="Сбросить", command=self.reset_size).grid(row=0, column=8, sticky="w")

        info = ttk.LabelFrame(root, text="Метрика относительности", padding=10)
        info.pack(fill="x", pady=(10, 0))

        self._kv(info, 0, 0, "Статус", self.status_var)
        self._kv(info, 0, 2, "Аккаунт", self.account_var)
        self._kv(info, 0, 4, "Последний бар", self.last_bar_time_var)

        self._kv(info, 1, 0, "Пара 1 ппм", self.ppm_1_var)
        self._kv(info, 1, 2, "Пара 2 ппм", self.ppm_2_var)
        self._kv(info, 1, 4, "Коэф 1/2", self.ratio_1_to_2_var)
        self._kv(info, 1, 6, "Коэф 2/1", self.ratio_2_to_1_var)

        trade = ttk.LabelFrame(root, text="Текущий opposite-план", padding=10)
        trade.pack(fill="x", pady=(10, 0))
        self._kv(trade, 0, 0, "Логика", self.trade_hint_var)
        self.trade_button = ttk.Button(trade, text="Открыть opposite позиции", command=self.open_current_positions)
        self.trade_button.grid(row=0, column=2, padx=(18, 8), sticky="w")
        self.close_button = ttk.Button(trade, text="Закрыть все по связке", command=self.close_current_pair_positions)
        self.close_button.grid(row=0, column=3, padx=(8, 0), sticky="w")

        hint = ttk.LabelFrame(root, text="Смысл", padding=10)
        hint.pack(fill="x", pady=(10, 0))
        ttk.Label(
            hint,
            text=(
                "Галочка 'Расхождение с коэф' переключает режим расчёта расхождения: "
                "без неё показываются реальные пункты, с ней — пункты с пересчётом по рассчитанному коэффициенту. "
                "В правом верхнем углу ленты показывается сумма по всей видимой ленте, "
                "отдельно текущая свеча и live-расхождение незакрытой свечи по bid. "
                "Кнопка close закрывает все позиции по двум выбранным символам и показывает pnl."
            ),
            wraplength=1280,
        ).pack(anchor="w")

        chart_wrap = ttk.LabelFrame(root, text="Сравнение свечей", padding=8)
        chart_wrap.pack(fill="both", expand=True, pady=(10, 0))

        self.canvas = tk.Canvas(chart_wrap, bg="#111111", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.chart = RelativeChart(self.canvas)

    def _kv(self, parent: ttk.Widget, row: int, col: int, key: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=key).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
        ttk.Label(parent, textvariable=var).grid(row=row, column=col + 1, sticky="w", padx=(0, 18), pady=4)

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
        except Exception as exc:
            self.status_var.set("connect_error")
            messagebox.showerror("MT5", str(exc))

    def _ensure_connected(self) -> None:
        if not self.connected or self.client is None:
            self.connect_mt5()
        if not self.connected or self.client is None:
            raise RuntimeError("MT5 не подключен")

    def _read_inputs(self) -> tuple[str, str, str, int, int, int]:
        symbol_1 = self.symbol_1_var.get().strip()
        symbol_2 = self.symbol_2_var.get().strip()
        timeframe = self.timeframe_var.get().strip()

        if timeframe not in TIMEFRAME_MINUTES:
            raise RuntimeError("Неподдерживаемый timeframe")

        calc_bars = max(20, int(self.calc_bars_var.get().strip() or "240"))
        visible_bars = max(5, int(self.visible_bars_var.get().strip() or "40"))
        refresh_ms = max(300, int(self.refresh_ms_var.get().strip() or "1000"))

        if symbol_1 == symbol_2:
            raise RuntimeError("Нужно выбрать две разные пары")

        return symbol_1, symbol_2, timeframe, calc_bars, visible_bars, refresh_ms

    def calculate_ratio(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, timeframe, calc_bars, _, _ = self._read_inputs()
            frame, meta_1, meta_2 = load_two_symbols(self.client, symbol_1, symbol_2, timeframe, calc_bars)
            self.relative_metrics = calculate_relative_metrics(frame, meta_1.digits, meta_2.digits, timeframe)

            self.ppm_1_var.set(f"{self.relative_metrics.ppm_1:.4f}")
            self.ppm_2_var.set(f"{self.relative_metrics.ppm_2:.4f}")
            self.ratio_1_to_2_var.set(f"{self.relative_metrics.ratio_1_to_2:.6f}")
            self.ratio_2_to_1_var.set(f"{self.relative_metrics.ratio_2_to_1:.6f}")

            self.status_var.set("ratio_ready")
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

            symbol_1, symbol_2, timeframe, _, visible_bars, _ = self._read_inputs()
            snapshot = build_render_snapshot(
                client=self.client,
                cfg=self.base_cfg,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                timeframe=timeframe,
                bars_count=visible_bars,
                ratio_1_to_2=self.relative_metrics.ratio_1_to_2,
                use_ratio_in_divergence=self.use_ratio_in_divergence_var.get(),
            )

            self.current_snapshot = snapshot
            self.current_trade_plan = snapshot.trade_plan

            if snapshot.bars.empty:
                return

            self.last_bar_time_var.set(str(snapshot.bars.iloc[-1]["time"]))
            self.trade_hint_var.set(
                f"Лидер {snapshot.trade_plan.leader_symbol} {snapshot.trade_plan.leader_move:.2f} | "
                f"ведомая {snapshot.trade_plan.follower_symbol} {snapshot.trade_plan.follower_move:.2f} | "
                f"SELL {snapshot.trade_plan.sell_symbol} {snapshot.trade_plan.sell_lots:.2f} / "
                f"BUY {snapshot.trade_plan.buy_symbol} {snapshot.trade_plan.buy_lots:.2f}"
            )
            self.trade_button.configure(text=snapshot.trade_plan.button_text)

            self.chart.draw(
                bars=snapshot.bars,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                ratio_1_to_2=self.relative_metrics.ratio_1_to_2,
                width_adjust_px=self.width_adjust_px,
                height_adjust_px=self.height_adjust_px,
                divergence_stats=snapshot.divergence_stats,
            )
            self.status_var.set("rendered")
        except Exception as exc:
            self.status_var.set("render_error")
            messagebox.showerror("Рендер", str(exc))

    def on_toggle_divergence_mode(self) -> None:
        if self.current_snapshot is not None:
            self.render_once()

    def change_size(self, axis: str, delta: int) -> None:
        if axis == "width":
            self.width_adjust_px += delta
            self.width_size_var.set(f"{self.width_adjust_px:+d}px")
        else:
            self.height_adjust_px += delta
            self.height_size_var.set(f"{self.height_adjust_px:+d}px")

        if self.current_snapshot is not None:
            self.render_once()

    def reset_size(self) -> None:
        self.width_adjust_px = 0
        self.height_adjust_px = 0
        self.width_size_var.set("0px")
        self.height_size_var.set("0px")
        if self.current_snapshot is not None:
            self.render_once()

    def open_current_positions(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            if self.current_trade_plan is None:
                raise RuntimeError("Сначала сделай рендер, чтобы появился текущий opposite-план")

            result = open_opposite_positions(self.client, self.base_cfg, self.current_trade_plan)
            self.status_var.set("orders_opened")
            messagebox.showinfo(
                "Позиции открыты",
                (
                    f"SELL {self.current_trade_plan.sell_symbol} {self.current_trade_plan.sell_lots:.2f}\n"
                    f"BUY {self.current_trade_plan.buy_symbol} {self.current_trade_plan.buy_lots:.2f}\n"
                    f"sell_order={result.sell_order} retcode={result.sell_retcode}\n"
                    f"buy_order={result.buy_order} retcode={result.buy_retcode}"
                ),
            )
        except Exception as exc:
            self.status_var.set("order_error")
            messagebox.showerror("Открытие opposite позиций", str(exc))

    def close_current_pair_positions(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, _, _, _, _ = self._read_inputs()
            summary = close_pair_positions(self.client, self.base_cfg, symbol_1, symbol_2)
            self.status_var.set("positions_closed")
            messagebox.showinfo(
                "Позиции закрыты",
                (
                    f"Связка: {symbol_1} / {symbol_2}\n"
                    f"Закрыто позиций: {summary.closed_count}\n"
                    f"gross+swap pnl usd: {summary.gross_pnl_usd:.2f}\n"
                    f"net est pnl usd: {summary.net_pnl_est_usd:.2f}"
                ),
            )
            self.render_once()
        except Exception as exc:
            self.status_var.set("close_error")
            messagebox.showerror("Закрытие позиций по связке", str(exc))

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
                _, _, _, _, _, refresh_ms = self._read_inputs()
            except Exception:
                refresh_ms = 1000
            self.live_job = self.after(refresh_ms, self._live_tick)

    def stop_live(self) -> None:
        if self.live_job is not None:
            self.after_cancel(self.live_job)
            self.live_job = None
        if self.status_var.get() == "live":
            self.status_var.set("stopped")

    def on_close(self) -> None:
        try:
            self.stop_live()
            if self.client is not None and self.connected:
                self.client.shutdown()
        finally:
            self.destroy()


def main() -> None:
    app = RelativeCompareUI()
    app.mainloop()
