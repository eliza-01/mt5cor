from __future__ import annotations

from tkinter import messagebox

from src.app.ui_relative_compare.services.market.hedge.direction import paired_side
from src.app.ui_relative_compare.services.trading import close_pair_positions, open_pair_legs, reverse_pair_positions


class ControllerTradeMixin:
    def _current_side_relation(self) -> str:
        if self.current_snapshot is not None:
            return self.current_snapshot.trade_plan.side_relation
        return "same" if bool(self.view.negative_correlation_var.get()) else "opposite"

    def build_direct_order(self, symbol_index: int, side: str) -> list[tuple[str, str, float]]:
        symbol_1, symbol_2, _, _, _, _ = self.read_inputs()
        lot_1, lot_2 = self.resolve_pair_lots(strict=True)
        side_relation = self._current_side_relation()

        if symbol_index == 1:
            side_1 = side
            side_2 = paired_side(side, side_relation)
        elif symbol_index == 2:
            side_2 = side
            side_1 = paired_side(side, side_relation)
        else:
            raise RuntimeError("Некорректная команда открытия")

        return [
            (symbol_1, side_1, lot_1),
            (symbol_2, side_2, lot_2),
        ]

    def open_direct_order(self, symbol_index: int, side: str) -> None:
        try:
            self.ensure_connected()
            assert self.client is not None

            legs = self.build_direct_order(symbol_index, side)
            result = open_pair_legs(
                client=self.client,
                cfg=self.base_cfg,
                legs=legs,
            )
            self.view.status_var.set("orders_opened")
            opened_text = "\n".join(
                f"{leg.side.upper()} {leg.symbol} {leg.volume:.2f} order={leg.order} retcode={leg.retcode}"
                for leg in result.legs
            )
            messagebox.showinfo("Позиции открыты", opened_text)
            if self.current_snapshot is not None:
                self.render_once()
        except Exception as exc:
            self.view.status_var.set("order_error")
            messagebox.showerror("Открытие позиций по связке", str(exc))

    def close_current_pair_positions(self) -> None:
        try:
            self.ensure_connected()
            assert self.client is not None
            symbol_1, symbol_2, _, _, _, _ = self.read_inputs()
            summary = close_pair_positions(self.client, self.base_cfg, symbol_1, symbol_2)
            self.view.status_var.set("positions_closed")
            messagebox.showinfo(
                "Позиции закрыты",
                f"Связка: {symbol_1} / {symbol_2}\n"
                f"Закрыто позиций: {summary.closed_count}\n"
                f"Сделок MT: {summary.deals_count}\n"
                f"MT profit: {summary.profit_usd:.2f}\n"
                f"MT commission: {summary.commission_usd:.2f}\n"
                f"MT swap: {summary.swap_usd:.2f}\n"
                f"MT fee: {summary.fee_usd:.2f}\n"
                f"MT total pnl: {summary.total_pnl_usd:.2f}",
            )
            if self.current_snapshot is not None:
                self.render_once()
        except Exception as exc:
            self.view.status_var.set("close_error")
            messagebox.showerror("Закрытие позиций по связке", str(exc))

    def reverse_current_pair_positions(self) -> None:
        try:
            self.ensure_connected()
            assert self.client is not None
            symbol_1, symbol_2, _, _, _, _ = self.read_inputs()
            summary = reverse_pair_positions(self.client, self.base_cfg, symbol_1, symbol_2)
            self.view.status_var.set("positions_reversed")
            reopened_lines = [
                f"{leg.side.upper()} {leg.symbol} {leg.volume:.2f} order={leg.order} retcode={leg.retcode}"
                for leg in summary.reopened_legs
            ]
            messagebox.showinfo(
                "Позиции развернуты",
                f"Связка: {symbol_1} / {symbol_2}\n"
                f"Закрыто позиций: {summary.close_summary.closed_count}\n"
                f"Сделок MT: {summary.close_summary.deals_count}\n"
                f"MT total pnl: {summary.close_summary.total_pnl_usd:.2f}\n\n"
                f"Открыто в обратную сторону:\n" + "\n".join(reopened_lines),
            )
            if self.current_snapshot is not None:
                self.render_once()
        except Exception as exc:
            self.view.status_var.set("reverse_error")
            messagebox.showerror("Разворот позиций по связке", str(exc))
