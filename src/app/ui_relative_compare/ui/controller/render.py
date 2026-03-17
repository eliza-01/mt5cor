from __future__ import annotations

import pandas as pd
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

    def read_signal_params(self) -> tuple[int, int, float, float]:
        fast_window = max(1, int(str(self.view.signal_fast_ma_var.get()).strip() or "8"))
        slow_window = max(fast_window + 1, int(str(self.view.signal_slow_ma_var.get()).strip() or "34"))
        entry_threshold = abs(float(str(self.view.signal_entry_threshold_var.get()).strip().replace(",", ".") or "12.0"))
        exit_threshold = abs(float(str(self.view.signal_exit_threshold_var.get()).strip().replace(",", ".") or "3.0"))
        return fast_window, slow_window, entry_threshold, exit_threshold

    def resolve_pair_lots(self, strict: bool = True) -> tuple[float, float]:
        symbol_1 = self.view.symbol_1_var.get().strip() or "EURUSD"
        symbol_2 = self.view.symbol_2_var.get().strip() or "AUDUSD"

        if self.view.auto_volume_var.get():
            if self.current_snapshot is not None:
                return (
                    float(self.current_snapshot.trade_plan.symbol_1_lots),
                    float(self.current_snapshot.trade_plan.symbol_2_lots),
                )
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

    def _latest_common_bar_time(self, symbol_1: str, symbol_2: str, timeframe: str):
        assert self.client is not None
        frame_1 = self.client.copy_rates(symbol_1, timeframe, 3)[["time"]].copy()
        frame_2 = self.client.copy_rates(symbol_2, timeframe, 3)[["time"]].copy()
        merged = pd.merge(frame_1, frame_2, on="time", how="inner")
        if merged.empty:
            return None
        return merged.iloc[-1]["time"]

    def _count_new_bars(self, previous_time, latest_time, timeframe: str) -> int:
        if previous_time is None or latest_time is None:
            return 0

        prev_ts = pd.Timestamp(previous_time)
        latest_ts = pd.Timestamp(latest_time)
        if latest_ts <= prev_ts:
            return 0

        tf_minutes = TIMEFRAME_MINUTES[timeframe]
        delta = latest_ts - prev_ts
        bars = int(delta / pd.Timedelta(minutes=tf_minutes))
        return max(1, bars)

    def _restore_scroll_after_redraw(self, prev_left: float, prev_right: float, had_snapshot: bool) -> None:
        if not had_snapshot:
            self.sync_canvas_view(1.0)
            return
        if prev_left <= 0.001:
            self.sync_canvas_view(0.0)
            return
        if prev_right >= 0.999:
            self.sync_canvas_view(1.0)
            return
        self.sync_canvas_view(prev_left)

    def render_once(self, from_live: bool = False) -> None:
        try:
            self.ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, timeframe, visible_bars, _, aggregate_bars = self.read_inputs()
            manual_ratio_1_to_2 = self.read_manual_ratio()
            fast_window, slow_window, entry_threshold, exit_threshold = self.read_signal_params()
            invert_second = bool(self.view.negative_correlation_var.get())

            prev_left, prev_right = self.view.candle_canvas.xview()
            had_snapshot = self.current_snapshot is not None

            requested_changed = self.live_base_visible_bars != visible_bars
            full_reset = (not from_live) or (self.current_snapshot is None) or requested_changed

            if full_reset:
                self.live_base_visible_bars = visible_bars
                self.live_effective_bars = visible_bars
            else:
                latest_common_time = self._latest_common_bar_time(symbol_1, symbol_2, timeframe)
                new_bars = self._count_new_bars(self.live_last_bar_time, latest_common_time, timeframe)
                if new_bars <= 0:
                    return
                self.live_effective_bars = int(self.live_effective_bars or visible_bars) + new_bars

            effective_bars_count = int(self.live_effective_bars or visible_bars)

            snapshot = build_render_snapshot(
                client=self.client,
                cfg=self.base_cfg,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                timeframe=timeframe,
                bars_count=effective_bars_count,
                ratio_1_to_2=manual_ratio_1_to_2,
                bars_per_candle=aggregate_bars,
                mutual_exclusion_enabled=bool(self.view.mutual_exclusion_var.get()),
                signal_fast_window=fast_window,
                signal_slow_window=slow_window,
                signal_entry_threshold=entry_threshold,
                signal_exit_threshold=exit_threshold,
                invert_second=invert_second,
            )
            self.current_snapshot = snapshot
            if snapshot.bars.empty:
                return

            self.live_last_bar_time = snapshot.bars.iloc[-1]["time"]

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
                signal_diagnostics=snapshot.signal_diagnostics,
                line_chart_mode=self.view.line_chart_mode_var.get().strip() or "gap_ma",
            )

            self.view.update_idletasks()
            self._restore_scroll_after_redraw(prev_left, prev_right, had_snapshot)
            self.view.status_var.set("live" if from_live else "rendered")
            self.update_trade_hint()
            self.update_selection_stats()
            self.schedule_state_save()
        except Exception as exc:
            self.view.status_var.set("live_error" if from_live else "render_error")
            if not from_live:
                messagebox.showerror("Рендер", str(exc))

    def redraw_current_snapshot(self) -> None:
        if self.current_snapshot is None or self.current_snapshot.bars.empty:
            return

        prev_left, prev_right = self.view.candle_canvas.xview()
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
            signal_diagnostics=self.current_snapshot.signal_diagnostics,
            line_chart_mode=self.view.line_chart_mode_var.get().strip() or "gap_ma",
        )

        self.view.update_idletasks()
        self._restore_scroll_after_redraw(prev_left, prev_right, had_snapshot=True)
        self.update_trade_hint()
        self.update_selection_stats()

    def update_trade_hint(self) -> None:
        snapshot = self.current_snapshot
        if snapshot is None:
            self.view.trade_hint_var.set("-")
            return

        mode_text = "AUTO" if self.view.auto_volume_var.get() else "MANUAL"
        try:
            lot_1, lot_2 = self.resolve_pair_lots(strict=not self.view.auto_volume_var.get())
            hedge = snapshot.hedge_diagnostics
            signal = snapshot.signal_diagnostics
            state_text = "ENTER" if signal.entry_ready else ("EXIT" if signal.exit_ready else "WAIT")
            if snapshot.trade_plan.entry_ready:
                legs_text = (
                    f"{snapshot.trade_plan.symbol_1_side.upper()} {snapshot.trade_plan.symbol_1} {lot_1:.2f} | "
                    f"{snapshot.trade_plan.symbol_2_side.upper()} {snapshot.trade_plan.symbol_2} {lot_2:.2f}"
                )
            else:
                legs_text = "входа нет"
            self.view.trade_hint_var.set(
                f"{mode_text} | {state_text} | gap={signal.gap_last:+.2f} | "
                f"fast={signal.fast_last:+.2f} slow={signal.slow_last:+.2f} | "
                f"diff={signal.ma_diff_last:+.2f} | entry={signal.entry_threshold:.2f} exit={signal.exit_threshold:.2f} | "
                f"q={hedge.execution_ratio:+.4f} relation={hedge.side_relation} | {legs_text}"
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