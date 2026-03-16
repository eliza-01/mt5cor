from __future__ import annotations

from tkinter import messagebox

from src.app.ui_relative_compare.constants import TIMEFRAME_MINUTES
from src.app.ui_relative_compare.services.market import build_render_snapshot


class ControllerRenderMixin:
    def connect_mt5(self) -> None:
        try:
            if self.connected:
                self.view.status_var.set("connected")
                return

            from src.broker.mt5_client import MT5Client

            self.client = MT5Client(self.base_cfg)
            self.client.connect()
            self.connected = True
            self.view.status_var.set("connected")
            self.view.account_var.set(f"{self.base_cfg.mt5_login} @ {self.base_cfg.mt5_server}")
            self.schedule_state_save()
        except Exception as exc:
            self.view.status_var.set("connect_error")
            messagebox.showerror("MT5", str(exc))

    def ensure_connected(self) -> None:
        if not self.connected or self.client is None:
            self.connect_mt5()
        if not self.connected or self.client is None:
            raise RuntimeError("MT5 не подключен")

    def read_inputs(self) -> tuple[str, str, str, int, int, int]:
        symbol_1 = self.view.symbol_1_var.get().strip()
        symbol_2 = self.view.symbol_2_var.get().strip()
        timeframe = self.view.timeframe_var.get().strip()
        if timeframe not in TIMEFRAME_MINUTES:
            raise RuntimeError("Неподдерживаемый timeframe")

        visible_bars = max(20, int(self.view.visible_bars_var.get().strip() or "120"))
        refresh_ms = max(100, int(self.view.refresh_ms_var.get().strip() or "250"))
        aggregate_bars = max(1, int(self.view.aggregate_bars_var.get().strip() or "1"))

        if symbol_1 == symbol_2:
            raise RuntimeError("Нужно выбрать две разные пары")
        return symbol_1, symbol_2, timeframe, visible_bars, refresh_ms, aggregate_bars

    def read_positive_lot(self, raw: str, symbol: str) -> float:
        text = str(raw).strip().replace(",", ".")
        value = float(text)
        if value <= 0:
            raise RuntimeError(f"Объем для {symbol} должен быть больше 0")
        return value

    def read_manual_ratio(self) -> float:
        text = str(self.view.manual_ratio_1_to_2_var.get()).strip().replace(",", ".")
        value = float(text)
        if value <= 0:
            raise RuntimeError("Коэффициент 1/2 должен быть больше 0")
        return value

    def resolve_pair_lots(self, strict: bool = True) -> tuple[float, float]:
        symbol_1 = self.view.symbol_1_var.get().strip() or "EURUSD"
        symbol_2 = self.view.symbol_2_var.get().strip() or "AUDUSD"

        if self.view.auto_volume_var.get():
            ratio_1_to_2 = self.read_manual_ratio()
            return float(self.base_cfg.base_lot_eurusd), float(self.base_cfg.base_lot_eurusd * ratio_1_to_2)

        try:
            return (
                self.read_positive_lot(self.view.manual_lot_1_var.get(), symbol_1),
                self.read_positive_lot(self.view.manual_lot_2_var.get(), symbol_2),
            )
        except Exception:
            if strict:
                raise
            return 0.0, 0.0

    def render_once(self) -> None:
        try:
            self.ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, timeframe, visible_bars, _, aggregate_bars = self.read_inputs()
            ratio_1_to_2 = self.read_manual_ratio()
            invert_second = bool(self.view.negative_correlation_var.get())

            prev_x = self.view.candle_canvas.xview()[0]
            had_snapshot = self.current_snapshot is not None

            snapshot = build_render_snapshot(
                client=self.client,
                cfg=self.base_cfg,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                timeframe=timeframe,
                bars_count=visible_bars,
                ratio_1_to_2=ratio_1_to_2,
                bars_per_candle=aggregate_bars,
                invert_second=invert_second,
            )
            self.current_snapshot = snapshot
            if snapshot.bars.empty:
                return

            self.selection.resolve_indices(snapshot.bars)
            self.view.aggregate_info_var.set(f"{timeframe} x {aggregate_bars} | {len(snapshot.bars)} свечей")
            self.view.last_bar_time_var.set(str(snapshot.bars.iloc[-1]["time"]))

            self.chart.draw(
                bars=snapshot.bars,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                ratio_1_to_2=snapshot.ratio_1_to_2,
                invert_second=snapshot.negative_correlation,
                width_adjust_px=self.view.width_adjust_px,
                height_adjust_px=self.view.height_adjust_px,
                pair_gap_adjust_px=self.view.pair_gap_adjust_px,
                trade_plan=snapshot.trade_plan,
                selected_start_index=self.selection.start_index,
                selected_end_index=self.selection.end_index,
                colors=self.view.chart_colors,
                line_zoom=float(self.view.line_zoom_var.get()),
                digits_1=snapshot.digits_1,
                digits_2=snapshot.digits_2,
                mutual_exclusion_enabled=bool(self.view.mutual_exclusion_var.get()),
            )

            self.view.update_idletasks()
            self.sync_canvas_view(prev_x if had_snapshot else 1.0)
            self.view.status_var.set("rendered")
            self.update_trade_hint()
            self.update_selection_stats()
            self.schedule_state_save()
        except Exception as exc:
            self.view.status_var.set("render_error")
            messagebox.showerror("Рендер", str(exc))

    def redraw_current_snapshot(self) -> None:
        if self.current_snapshot is None or self.current_snapshot.bars.empty:
            return
        prev_x = self.view.candle_canvas.xview()[0]
        self.selection.resolve_indices(self.current_snapshot.bars)

        self.chart.draw(
            bars=self.current_snapshot.bars,
            symbol_1=self.view.symbol_1_var.get().strip(),
            symbol_2=self.view.symbol_2_var.get().strip(),
            ratio_1_to_2=self.current_snapshot.ratio_1_to_2,
            invert_second=self.current_snapshot.negative_correlation,
            width_adjust_px=self.view.width_adjust_px,
            height_adjust_px=self.view.height_adjust_px,
            pair_gap_adjust_px=self.view.pair_gap_adjust_px,
            trade_plan=self.current_snapshot.trade_plan,
            selected_start_index=self.selection.start_index,
            selected_end_index=self.selection.end_index,
            colors=self.view.chart_colors,
            line_zoom=float(self.view.line_zoom_var.get()),
            digits_1=self.current_snapshot.digits_1,
            digits_2=self.current_snapshot.digits_2,
            mutual_exclusion_enabled=bool(self.view.mutual_exclusion_var.get()),
        )

        self.view.update_idletasks()
        self.sync_canvas_view(prev_x)
        self.update_trade_hint()
        self.update_selection_stats()

    def update_trade_hint(self) -> None:
        snapshot = self.current_snapshot
        if snapshot is None:
            self.view.trade_hint_var.set("-")
            return

        mode_text = "AUTO" if self.view.auto_volume_var.get() else "MANUAL"
        try:
            ratio_1_to_2 = self.read_manual_ratio()
            lot_1, lot_2 = self.resolve_pair_lots(strict=not self.view.auto_volume_var.get())
            self.view.trade_hint_var.set(
                f"{mode_text} | coef 1/2 {ratio_1_to_2:.6f} | "
                f"{snapshot.trade_plan.symbol_1} {lot_1:.2f} | {snapshot.trade_plan.symbol_2} {lot_2:.2f} | "
                f"лидер {snapshot.trade_plan.leader_symbol} {snapshot.trade_plan.leader_move:.2f} | "
                f"ведомая {snapshot.trade_plan.follower_symbol} {snapshot.trade_plan.follower_move:.2f} | "
                f"подсказка SELL {snapshot.trade_plan.sell_symbol} / BUY {snapshot.trade_plan.buy_symbol}"
            )
        except Exception as exc:
            self.view.trade_hint_var.set(f"{mode_text} | ошибка параметров: {exc}")

    def on_toggle_negative_correlation(self) -> None:
        self.schedule_state_save()
        if self.current_snapshot is not None:
            self.render_once()

    def on_toggle_mutual_exclusion(self) -> None:
        self.schedule_state_save()
        if self.current_snapshot is not None:
            self.redraw_current_snapshot()

    def on_toggle_auto_volume(self) -> None:
        self.update_manual_volume_state()
        self.schedule_state_save()
        self.update_trade_hint()