# Minimal desktop UI for live spread/divergence monitoring and quick backtests.
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import math
import tkinter as tk
from tkinter import ttk, messagebox

import pandas as pd

from src.broker.mt5_client import MT5Client
from src.common.settings import load_settings
from src.data.history import load_pair_history
from src.strategy.costs import pip_size
from src.strategy.features import build_feature_frame
from src.strategy.simulator import estimate_live_edge, simulate_trades, summarize_trades


TIMEFRAME_BARS_PER_DAY = {
    "M1": 1440,
    "M5": 288,
    "M15": 96,
    "H1": 24,
}


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MT5 FX Relative Value Monitor")
        self.geometry("1180x760")
        self.minsize(1080, 700)

        self.base_cfg = load_settings()
        self.client = MT5Client(self.base_cfg)
        self.meta_1 = None
        self.meta_2 = None
        self.live_job: str | None = None
        self.is_connected = False

        self.timeframe_var = tk.StringVar(value=self.base_cfg.timeframe)
        self.days_var = tk.StringVar(value="2")
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.refresh_ms_var = tk.StringVar(value=str(max(self.base_cfg.live_poll_ms, 1000)))

        self.status_var = tk.StringVar(value="disconnected")
        self.account_var = tk.StringVar(value="-")
        self.time_var = tk.StringVar(value="-")

        self.price_1_var = tk.StringVar(value="-")
        self.price_2_var = tk.StringVar(value="-")
        self.tick_spread_1_var = tk.StringVar(value="-")
        self.tick_spread_2_var = tk.StringVar(value="-")
        self.synth_var = tk.StringVar(value="-")

        self.beta_var = tk.StringVar(value="-")
        self.corr_var = tk.StringVar(value="-")
        self.spread_raw_var = tk.StringVar(value="-")
        self.spread_z_var = tk.StringVar(value="-")
        self.resid_z_var = tk.StringVar(value="-")
        self.combo_z_var = tk.StringVar(value="-")
        self.live_state_var = tk.StringVar(value="-")

        self.summary_trades_var = tk.StringVar(value="-")
        self.summary_winrate_var = tk.StringVar(value="-")
        self.summary_gross_var = tk.StringVar(value="-")
        self.summary_net_var = tk.StringVar(value="-")
        self.summary_avg_var = tk.StringVar(value="-")
        self.summary_hold_var = tk.StringVar(value="-")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.after(100, self.connect_and_start)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        top = ttk.LabelFrame(root, text="Управление", padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Timeframe").grid(row=0, column=0, sticky="w")
        timeframe_box = ttk.Combobox(
            top,
            textvariable=self.timeframe_var,
            values=list(TIMEFRAME_BARS_PER_DAY.keys()),
            state="readonly",
            width=8,
        )
        timeframe_box.grid(row=0, column=1, padx=(6, 12), sticky="w")

        ttk.Label(top, text="Дней для теста").grid(row=0, column=2, sticky="w")
        ttk.Entry(top, textvariable=self.days_var, width=8).grid(row=0, column=3, padx=(6, 12), sticky="w")

        ttk.Label(top, text="Refresh ms").grid(row=0, column=4, sticky="w")
        ttk.Entry(top, textvariable=self.refresh_ms_var, width=8).grid(row=0, column=5, padx=(6, 12), sticky="w")

        ttk.Checkbutton(top, text="Auto refresh", variable=self.auto_refresh_var, command=self.on_toggle_refresh).grid(
            row=0, column=6, padx=(6, 12), sticky="w"
        )

        ttk.Button(top, text="Обновить live", command=self.refresh_live).grid(row=0, column=7, padx=(6, 6), sticky="w")
        ttk.Button(top, text="Запустить тест", command=self.run_backtest).grid(row=0, column=8, padx=(6, 6), sticky="w")
        ttk.Button(top, text="Переподключить MT5", command=self.reconnect).grid(row=0, column=9, padx=(6, 6), sticky="w")

        info = ttk.LabelFrame(root, text="Статус", padding=10)
        info.pack(fill="x", pady=(10, 0))
        info.columnconfigure(1, weight=1)

        self._kv(info, 0, 0, "Статус", self.status_var)
        self._kv(info, 0, 2, "Аккаунт", self.account_var)
        self._kv(info, 0, 4, "Время бара", self.time_var)

        live = ttk.LabelFrame(root, text="Live", padding=10)
        live.pack(fill="x", pady=(10, 0))

        self._kv(live, 0, 0, self.base_cfg.symbol_leg_1, self.price_1_var)
        self._kv(live, 0, 2, self.base_cfg.symbol_leg_2, self.price_2_var)
        self._kv(live, 0, 4, f"{self.base_cfg.symbol_leg_1} spread pips", self.tick_spread_1_var)
        self._kv(live, 0, 6, f"{self.base_cfg.symbol_leg_2} spread pips", self.tick_spread_2_var)

        self._kv(live, 1, 0, "Synthetic ratio", self.synth_var)
        self._kv(live, 1, 2, "beta", self.beta_var)
        self._kv(live, 1, 4, "corr", self.corr_var)
        self._kv(live, 1, 6, "state", self.live_state_var)

        self._kv(live, 2, 0, "spread raw", self.spread_raw_var)
        self._kv(live, 2, 2, "spread z", self.spread_z_var)
        self._kv(live, 2, 4, "resid z", self.resid_z_var)
        self._kv(live, 2, 6, "combo z", self.combo_z_var)

        bt = ttk.LabelFrame(root, text="Результат теста", padding=10)
        bt.pack(fill="x", pady=(10, 0))

        self._kv(bt, 0, 0, "trades", self.summary_trades_var)
        self._kv(bt, 0, 2, "win rate", self.summary_winrate_var)
        self._kv(bt, 0, 4, "gross pnl usd", self.summary_gross_var)
        self._kv(bt, 0, 6, "net pnl usd", self.summary_net_var)

        self._kv(bt, 1, 0, "avg net pnl usd", self.summary_avg_var)
        self._kv(bt, 1, 2, "median hold bars", self.summary_hold_var)

        bottom = ttk.Panedwindow(root, orient="horizontal")
        bottom.pack(fill="both", expand=True, pady=(10, 0))

        left_frame = ttk.LabelFrame(bottom, text="Последние сделки", padding=8)
        right_frame = ttk.LabelFrame(bottom, text="Лог", padding=8)
        bottom.add(left_frame, weight=3)
        bottom.add(right_frame, weight=2)

        columns = ("entry_time", "side", "combo_z", "hold_bars", "reason", "net_pnl_usd")
        self.trades_table = ttk.Treeview(left_frame, columns=columns, show="headings", height=18)
        self.trades_table.pack(fill="both", expand=True)

        headers = {
            "entry_time": "entry_time",
            "side": "side",
            "combo_z": "combo_z",
            "hold_bars": "hold",
            "reason": "reason",
            "net_pnl_usd": "net_pnl_usd",
        }
        widths = {
            "entry_time": 180,
            "side": 60,
            "combo_z": 90,
            "hold_bars": 60,
            "reason": 80,
            "net_pnl_usd": 100,
        }
        for col in columns:
            self.trades_table.heading(col, text=headers[col])
            self.trades_table.column(col, width=widths[col], anchor="center")

        self.log = tk.Text(right_frame, height=18, wrap="word")
        self.log.pack(fill="both", expand=True)

    def _kv(self, parent: ttk.Widget, row: int, col: int, key: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=key).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
        ttk.Label(parent, textvariable=var).grid(row=row, column=col + 1, sticky="w", padx=(0, 18), pady=4)

    def log_line(self, text: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{now}] {text}\n")
        self.log.see("end")

    def current_cfg(self):
        timeframe = self.timeframe_var.get().strip() or self.base_cfg.timeframe
        if timeframe not in TIMEFRAME_BARS_PER_DAY:
            raise RuntimeError(f"unsupported timeframe: {timeframe}")

        days = max(1, int(self.days_var.get().strip() or "2"))
        bars = max(days * TIMEFRAME_BARS_PER_DAY[timeframe], self.base_cfg.min_warmup_bars * 2)

        cfg = replace(self.base_cfg, timeframe=timeframe, history_bars=bars)
        return cfg, days, bars

    def connect_and_start(self) -> None:
        try:
            if self.is_connected:
                return
            self.client.connect()
            self.meta_1 = self.client.symbol_meta(self.base_cfg.symbol_leg_1)
            self.meta_2 = self.client.symbol_meta(self.base_cfg.symbol_leg_2)
            self.is_connected = True
            self.status_var.set("connected")
            self.account_var.set(f"{self.base_cfg.mt5_login} @ {self.base_cfg.mt5_server}")
            self.log_line("MT5 connected")
            self.refresh_live()
        except Exception as exc:
            self.status_var.set("connect_error")
            self.log_line(f"MT5 connect error: {exc}")
            messagebox.showerror("MT5", str(exc))

    def reconnect(self) -> None:
        try:
            self.stop_refresh()
            if self.is_connected:
                self.client.shutdown()
                self.is_connected = False
            self.client = MT5Client(self.base_cfg)
            self.connect_and_start()
        except Exception as exc:
            self.status_var.set("reconnect_error")
            self.log_line(f"Reconnect error: {exc}")
            messagebox.showerror("Reconnect", str(exc))

    def stop_refresh(self) -> None:
        if self.live_job is not None:
            self.after_cancel(self.live_job)
            self.live_job = None

    def on_toggle_refresh(self) -> None:
        if self.auto_refresh_var.get():
            self.refresh_live()
        else:
            self.stop_refresh()

    def schedule_next(self) -> None:
        self.stop_refresh()
        if self.auto_refresh_var.get():
            delay = max(500, int(self.refresh_ms_var.get().strip() or "1000"))
            self.live_job = self.after(delay, self.refresh_live)

    def _tick_spread_pips(self, symbol: str, digits: int) -> tuple[float, float, float]:
        tick = self.client.tick(symbol)
        bid = float(tick["bid"])
        ask = float(tick["ask"])
        spread = (ask - bid) / pip_size(digits)
        mid = (ask + bid) / 2.0
        return bid, ask, spread if spread >= 0 else 0.0, mid

    def refresh_live(self) -> None:
        try:
            if not self.is_connected:
                self.connect_and_start()
                return

            cfg, _, _ = self.current_cfg()
            raw = load_pair_history(self.client, cfg.symbol_leg_1, cfg.symbol_leg_2, cfg.timeframe, cfg.history_bars)
            feat = build_feature_frame(raw, cfg)
            if feat.empty:
                self.log_line("No features yet")
                self.schedule_next()
                return

            row = feat.iloc[-1]
            trades = simulate_trades(feat, cfg, self.meta_1, self.meta_2)
            live = estimate_live_edge(feat, trades, cfg) or {}

            bid_1, ask_1, spread_1, mid_1 = self._tick_spread_pips(cfg.symbol_leg_1, self.meta_1.digits)
            bid_2, ask_2, spread_2, mid_2 = self._tick_spread_pips(cfg.symbol_leg_2, self.meta_2.digits)

            self.time_var.set(str(row["time"]))
            self.price_1_var.set(f"bid {bid_1:.5f} | ask {ask_1:.5f}")
            self.price_2_var.set(f"bid {bid_2:.5f} | ask {ask_2:.5f}")
            self.tick_spread_1_var.set(f"{spread_1:.2f}")
            self.tick_spread_2_var.set(f"{spread_2:.2f}")
            self.synth_var.set(f"{(mid_1 / mid_2):.6f}" if mid_2 else "-")

            self.beta_var.set(self._fmt(row["beta"]))
            self.corr_var.set(self._fmt(row["corr"]))
            self.spread_raw_var.set(self._fmt(row["spread_raw"], 6))
            self.spread_z_var.set(self._fmt(row["spread_z"]))
            self.resid_z_var.set(self._fmt(row["resid_z"]))
            self.combo_z_var.set(self._fmt(row["combo_z"]))
            self.live_state_var.set(str(live.get("status", "-")))

            self.status_var.set("connected")
            self.log_line(
                f"live status={live.get('status')} combo_z={self._fmt(row['combo_z'])} "
                f"spread_z={self._fmt(row['spread_z'])} resid_z={self._fmt(row['resid_z'])} "
                f"corr={self._fmt(row['corr'])} beta={self._fmt(row['beta'])}"
            )
        except Exception as exc:
            self.status_var.set("live_error")
            self.log_line(f"Live refresh error: {exc}")
        finally:
            self.schedule_next()

    def run_backtest(self) -> None:
        try:
            if not self.is_connected:
                self.connect_and_start()
                if not self.is_connected:
                    return

            cfg, days, bars = self.current_cfg()
            raw = load_pair_history(self.client, cfg.symbol_leg_1, cfg.symbol_leg_2, cfg.timeframe, bars)
            feat = build_feature_frame(raw, cfg)
            trades = simulate_trades(feat, cfg, self.meta_1, self.meta_2)
            summary = summarize_trades(trades)
            live = estimate_live_edge(feat, trades, cfg) or {}

            self.summary_trades_var.set(self._fmt(summary.get("trades", 0), 0))
            self.summary_winrate_var.set(self._fmt_pct(summary.get("win_rate", 0.0)))
            self.summary_gross_var.set(self._fmt(summary.get("gross_pnl_usd", 0.0)))
            self.summary_net_var.set(self._fmt(summary.get("net_pnl_usd", 0.0)))
            self.summary_avg_var.set(self._fmt(summary.get("avg_net_pnl_usd", 0.0)))
            self.summary_hold_var.set(self._fmt(summary.get("median_hold_bars", 0.0), 0))

            self.fill_trades_table(trades.tail(30))
            self.log_line(
                f"backtest done timeframe={cfg.timeframe} days={days} bars={bars} "
                f"trades={summary.get('trades', 0)} net={self._fmt(summary.get('net_pnl_usd', 0.0))} "
                f"live={live.get('status')}"
            )
        except Exception as exc:
            self.log_line(f"Backtest error: {exc}")
            messagebox.showerror("Backtest", str(exc))

    def fill_trades_table(self, trades: pd.DataFrame) -> None:
        for item in self.trades_table.get_children():
            self.trades_table.delete(item)

        if trades.empty:
            return

        for _, row in trades.iterrows():
            side_text = "LONG1/SHORT2" if int(row["side"]) == 1 else "SHORT1/LONG2"
            self.trades_table.insert(
                "",
                "end",
                values=(
                    str(row["entry_time"]),
                    side_text,
                    self._fmt(row["combo_z"]),
                    int(row["hold_bars"]),
                    str(row["reason"]),
                    self._fmt(row["net_pnl_usd"]),
                ),
            )

    def _fmt(self, value: float | int | None, digits: int = 4) -> str:
        if value is None:
            return "-"
        try:
            val = float(value)
        except Exception:
            return str(value)
        if math.isnan(val) or math.isinf(val):
            return "-"
        if digits == 0:
            return str(int(round(val)))
        return f"{val:.{digits}f}"

    def _fmt_pct(self, value: float | int | None) -> str:
        if value is None:
            return "-"
        try:
            val = float(value)
        except Exception:
            return str(value)
        if math.isnan(val) or math.isinf(val):
            return "-"
        return f"{val * 100:.2f}%"

    def on_close(self) -> None:
        try:
            self.stop_refresh()
            if self.is_connected:
                self.client.shutdown()
        finally:
            self.destroy()


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()