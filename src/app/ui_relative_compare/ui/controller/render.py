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
        visible_bars = max(20, int(self.view.visible_bars_var.get().strip() or "1200"))
        refresh_ms = max(100, int(self.view.refresh_ms_var.get().strip() or "250"))
        aggregate_bars = max(1, int(self.view.aggregate_bars_var.get().strip() or "1"))
        if symbol_1 == symbol_2:
            raise RuntimeError("Нужно выбрать две разные пары")
        return symbol_1, symbol_2, timeframe, visible_bars, refresh_ms, aggregate_bars

    def _read_positive_float(self, raw: str, label: str) -> float:
        text = str(raw).strip().replace(",", ".")
        value = float(text)
        if value <= 0:
            raise RuntimeError(f"{label} должен быть больше 0")
        return value

    def _latest_common_bar_time(self, symbol_1: str, symbol_2: str, timeframe: str):
        assert self.client is not None
        frame_1 = self.client.copy_rates(symbol_1, timeframe, 3)[["time"]].copy()
        frame_2 = self.client.copy_rates(symbol_2, timeframe, 3)[["time"]].copy()
        merged = pd.merge(frame_1, frame_2, on="time", how="inner")
        return None if merged.empty else merged.iloc[-1]["time"]

    def _count_new_bars(self, previous_time, latest_time, timeframe: str) -> int:
        if previous_time is None or latest_time is None:
            return 0
        prev_ts = pd.Timestamp(previous_time)
        latest_ts = pd.Timestamp(latest_time)
        if latest_ts <= prev_ts:
            return 0
        return max(1, int((latest_ts - prev_ts) / pd.Timedelta(minutes=TIMEFRAME_MINUTES[timeframe])))

    def _active_plan_side(self) -> str:
        if self.current_snapshot is None:
            return "flat"
        if self.current_snapshot.live_tail is not None:
            return self.current_snapshot.live_tail.trade_plan.symbol_1_side
        return self.current_snapshot.trade_plan.symbol_1_side

    def _ratio_lot_factor_for_side(self, side: str) -> float:
        if self.current_snapshot is None:
            return 1.0
        stats = self.current_snapshot.range_stats
        if stats.apply_common:
            return float(stats.common_ratio)
        if side == "buy" and stats.apply_long:
            return float(stats.long_ratio)
        if side == "sell" and stats.apply_short:
            return float(stats.short_ratio)
        return 1.0

    def resolve_pair_lots(self, side_for_pair_1: str | None = None) -> tuple[float, float]:
        base_lot = self._read_positive_float(self.view.base_trading_lot_var.get(), "Базовый торговый лот")
        cost_1 = self._read_positive_float(self.view.cost_coeff_1_var.get(), "Коэффициент стоимости 1") if self.view.cost_coeff_1_enabled_var.get() else 1.0
        cost_2 = self._read_positive_float(self.view.cost_coeff_2_var.get(), "Коэффициент стоимости 2") if self.view.cost_coeff_2_enabled_var.get() else 1.0
        side = side_for_pair_1 or self._active_plan_side()
        ratio_2 = self._ratio_lot_factor_for_side(side)
        return float(base_lot * cost_1), float(base_lot * cost_2 * ratio_2)

    def _restore_scroll_after_redraw(self, prev_left: float, prev_right: float, had_snapshot: bool) -> None:
        if not had_snapshot:
            self.sync_canvas_view(1.0)
        elif prev_left <= 0.001:
            self.sync_canvas_view(0.0)
        elif prev_right >= 0.999:
            self.sync_canvas_view(1.0)
        else:
            self.sync_canvas_view(prev_left)

    def _should_full_rerender_on_new_raw_bar(self, aggregate_bars: int) -> bool:
        if aggregate_bars <= 1:
            return True
        if self.current_snapshot is None or self.current_snapshot.live_tail is None:
            return True
        return int(self.current_snapshot.live_tail.source_count) >= int(aggregate_bars)

    def _build_snapshot(
        self,
        symbol_1: str,
        symbol_2: str,
        timeframe: str,
        bars_count: int,
        aggregate_bars: int,
        base_lot: float,
        lot_multiplier_1: float,
        lot_multiplier_2: float,
        use_live_ticks: bool,
    ):
        assert self.client is not None
        return build_render_snapshot(
            client=self.client,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            timeframe=timeframe,
            bars_count=bars_count,
            bars_per_candle=aggregate_bars,
            mutual_exclusion_enabled=bool(self.view.mutual_exclusion_var.get()),
            base_lot=base_lot,
            lot_multiplier_1=lot_multiplier_1,
            lot_multiplier_2=lot_multiplier_2,
            apply_long_ratio=bool(self.view.apply_long_ratio_var.get()),
            apply_short_ratio=bool(self.view.apply_short_ratio_var.get()),
            apply_common_ratio=bool(self.view.apply_common_ratio_var.get()),
            use_live_ticks=use_live_ticks,
        )

    def _apply_full_snapshot(self, snapshot, symbol_1: str, symbol_2: str, timeframe: str, aggregate_bars: int, prev_left: float, prev_right: float, had_snapshot: bool, from_live: bool) -> None:
        self.current_snapshot = snapshot
        if snapshot.bars.empty and snapshot.live_tail is None:
            return

        self.selection.resolve_indices(snapshot.bars)
        self.view.aggregate_info_var.set(f"{timeframe} x {aggregate_bars} | {len(snapshot.bars)} закрытых свечей")
        if snapshot.live_tail is not None and not snapshot.live_tail.bar.empty:
            self.view.last_bar_time_var.set(str(snapshot.live_tail.bar.iloc[-1]["time"]))
        elif not snapshot.bars.empty:
            self.view.last_bar_time_var.set(str(snapshot.bars.iloc[-1]["time"]))
        else:
            self.view.last_bar_time_var.set("-")

        self.view.auto_relation_var.set("обратная" if snapshot.negative_correlation else "прямая")
        self.update_range_stats()
        self.update_final_lots_preview()

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
            range_stats=snapshot.range_stats,
            flow_diagnostics=snapshot.flow_diagnostics,
            live_tail=snapshot.live_tail,
        )

        self.view.update_idletasks()
        self._restore_scroll_after_redraw(prev_left, prev_right, had_snapshot)
        self.view.status_var.set("live" if from_live else "rendered")
        self.update_trade_hint()
        self.update_selection_stats()
        self.schedule_state_save()

    def _apply_live_tail_only(self, preview_snapshot, from_live: bool) -> None:
        if self.current_snapshot is None:
            return

        self.current_snapshot.live_tail = preview_snapshot.live_tail

        if self.current_snapshot.live_tail is not None and not self.current_snapshot.live_tail.bar.empty:
            self.view.last_bar_time_var.set(str(self.current_snapshot.live_tail.bar.iloc[-1]["time"]))

        self.chart.update_live_tail(
            bars=self.current_snapshot.bars,
            trade_plan=self.current_snapshot.trade_plan,
            live_tail=self.current_snapshot.live_tail,
            width_adjust_px=self.view.width_adjust_px,
            height_adjust_px=self.view.height_adjust_px,
            pair_gap_adjust_px=self.view.pair_gap_adjust_px,
            line_zoom=float(self.view.line_zoom_var.get()),
            digits_1=self.current_snapshot.digits_1,
            digits_2=self.current_snapshot.digits_2,
            invert_second=self.current_snapshot.negative_correlation,
            mutual_exclusion_enabled=bool(self.view.mutual_exclusion_var.get()),
            range_stats=self.current_snapshot.range_stats,
            flow_diagnostics=self.current_snapshot.flow_diagnostics,
        )
        self.view.status_var.set("live" if from_live else "rendered")
        self.update_trade_hint()

    def render_once(self, from_live: bool = False) -> None:
        try:
            self.ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, timeframe, visible_bars, _, aggregate_bars = self.read_inputs()
            base_lot = self._read_positive_float(self.view.base_trading_lot_var.get(), "Базовый торговый лот")
            lot_multiplier_1 = self._read_positive_float(self.view.cost_coeff_1_var.get(), "Коэффициент стоимости 1") if self.view.cost_coeff_1_enabled_var.get() else 1.0
            lot_multiplier_2 = self._read_positive_float(self.view.cost_coeff_2_var.get(), "Коэффициент стоимости 2") if self.view.cost_coeff_2_enabled_var.get() else 1.0

            prev_left, prev_right = self.view.candle_canvas.xview()
            had_snapshot = self.current_snapshot is not None

            requested_changed = self.live_base_visible_bars != visible_bars
            full_reset = (not from_live) or (self.current_snapshot is None) or requested_changed

            if full_reset:
                self.live_base_visible_bars = visible_bars
                self.live_effective_bars = visible_bars

                snapshot = self._build_snapshot(
                    symbol_1=symbol_1,
                    symbol_2=symbol_2,
                    timeframe=timeframe,
                    bars_count=int(self.live_effective_bars),
                    aggregate_bars=aggregate_bars,
                    base_lot=base_lot,
                    lot_multiplier_1=lot_multiplier_1,
                    lot_multiplier_2=lot_multiplier_2,
                    use_live_ticks=bool(from_live),
                )
                self.live_last_bar_time = self._latest_common_bar_time(symbol_1, symbol_2, timeframe)
                self._apply_full_snapshot(snapshot, symbol_1, symbol_2, timeframe, aggregate_bars, prev_left, prev_right, had_snapshot, from_live)
                return

            latest_common_time = self._latest_common_bar_time(symbol_1, symbol_2, timeframe)
            new_raw_bars = self._count_new_bars(self.live_last_bar_time, latest_common_time, timeframe)

            if new_raw_bars > 0:
                self.live_effective_bars = int(self.live_effective_bars or visible_bars) + int(new_raw_bars)
                self.live_last_bar_time = latest_common_time

            if new_raw_bars > 0 and self._should_full_rerender_on_new_raw_bar(aggregate_bars):
                snapshot = self._build_snapshot(
                    symbol_1=symbol_1,
                    symbol_2=symbol_2,
                    timeframe=timeframe,
                    bars_count=int(self.live_effective_bars or visible_bars),
                    aggregate_bars=aggregate_bars,
                    base_lot=base_lot,
                    lot_multiplier_1=lot_multiplier_1,
                    lot_multiplier_2=lot_multiplier_2,
                    use_live_ticks=True,
                )
                self._apply_full_snapshot(snapshot, symbol_1, symbol_2, timeframe, aggregate_bars, prev_left, prev_right, had_snapshot, from_live)
                return

            preview_snapshot = self._build_snapshot(
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                timeframe=timeframe,
                bars_count=int(self.live_effective_bars or visible_bars),
                aggregate_bars=aggregate_bars,
                base_lot=base_lot,
                lot_multiplier_1=lot_multiplier_1,
                lot_multiplier_2=lot_multiplier_2,
                use_live_ticks=True,
            )
            self._apply_live_tail_only(preview_snapshot, from_live)
        except Exception as exc:
            self.view.status_var.set("live_error" if from_live else "render_error")
            if not from_live:
                messagebox.showerror("Рендер", str(exc))

    def redraw_current_snapshot(self) -> None:
        if self.current_snapshot is None or (self.current_snapshot.bars.empty and self.current_snapshot.live_tail is None):
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
            range_stats=self.current_snapshot.range_stats,
            flow_diagnostics=self.current_snapshot.flow_diagnostics,
            live_tail=self.current_snapshot.live_tail,
        )

        self.view.update_idletasks()
        self._restore_scroll_after_redraw(prev_left, prev_right, had_snapshot=True)
        self.update_trade_hint()
        self.update_selection_stats()

    def update_range_stats(self) -> None:
        if self.current_snapshot is None:
            self.view.range_long_var.set("-")
            self.view.range_short_var.set("-")
            self.view.range_common_var.set("-")
            return

        stats = self.current_snapshot.range_stats
        s1 = self.view.symbol_1_var.get().strip() or "PAIR1"
        s2 = self.view.symbol_2_var.get().strip() or "PAIR2"
        self.view.range_long_var.set(f"LONG:  {s1}: {stats.symbol_1_long_total:.1f} |{stats.long_ratio:.3f}| {stats.symbol_2_long_total:.1f} :{s2}")
        self.view.range_short_var.set(f"SHORT: {s1}: {stats.symbol_1_short_total:.1f} |{stats.short_ratio:.3f}| {stats.symbol_2_short_total:.1f} :{s2}")
        self.view.range_common_var.set(f"common: {stats.common_ratio:.3f}")

    def update_trade_hint(self) -> None:
        snapshot = self.current_snapshot
        if snapshot is None:
            self.view.trade_hint_var.set("-")
            return

        active_flow = snapshot.live_tail.flow_diagnostics if snapshot.live_tail is not None else snapshot.flow_diagnostics
        active_plan = snapshot.live_tail.trade_plan if snapshot.live_tail is not None else snapshot.trade_plan

        try:
            lots = self.resolve_pair_lots(active_plan.symbol_1_side)
            self.view.trade_hint_var.set(
                f"line1={active_flow.line_1_last:+.2f} | line2={active_flow.line_2_last:+.2f} | diff={active_flow.diff_last:+.2f} | "
                f"relation={snapshot.hedge_diagnostics.side_relation} | lots={lots[0]:.2f}/{lots[1]:.2f}"
            )
        except Exception as exc:
            self.view.trade_hint_var.set(f"ошибка параметров: {exc}")

    def on_toggle_mutual_exclusion(self) -> None:
        self.schedule_state_save()
        if self.current_snapshot is not None:
            self.render_once()