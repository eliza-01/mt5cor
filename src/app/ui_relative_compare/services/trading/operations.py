from __future__ import annotations

from src.broker.mt5_client import MT5Client
from src.common.settings import Settings
from .history import sum_deals, wait_closed_position_deals
from .models import ClosePairSummary, OrderSendSummary, ReopenedLeg, ReversePairSummary
from .positions import build_reverse_legs_from_positions, symbol_positions
from .requests import close_position_with_fill_fallback, send_market_with_fill_fallback
from .terminal import ensure_python_trading_enabled
from .volume import normalize_volume


def _open_leg(client: MT5Client, cfg: Settings, symbol: str, side: str, volume: float, deviation: int) -> ReopenedLeg:
    client.ensure_symbol(symbol)
    normalized_volume = normalize_volume(volume, symbol)
    result = send_market_with_fill_fallback(symbol=symbol, volume=normalized_volume, side=side, deviation=deviation, magic=cfg.mt5_magic, comment="relative_compare_reverse")
    return ReopenedLeg(symbol=symbol, side=side, volume=normalized_volume, retcode=int(result.retcode), order=int(getattr(result, "order", 0) or 0))


def open_pair_positions(client: MT5Client, cfg: Settings, sell_symbol: str, buy_symbol: str, sell_lots: float, buy_lots: float, deviation: int = 20) -> OrderSendSummary:
    ensure_python_trading_enabled()
    client.ensure_symbol(sell_symbol)
    client.ensure_symbol(buy_symbol)

    normalized_sell_lots = normalize_volume(sell_lots, sell_symbol)
    normalized_buy_lots = normalize_volume(buy_lots, buy_symbol)

    sell_result = send_market_with_fill_fallback(symbol=sell_symbol, volume=normalized_sell_lots, side="sell", deviation=deviation, magic=cfg.mt5_magic, comment="relative_compare_sell")
    buy_result = send_market_with_fill_fallback(symbol=buy_symbol, volume=normalized_buy_lots, side="buy", deviation=deviation, magic=cfg.mt5_magic, comment="relative_compare_buy")

    return OrderSendSummary(sell_retcode=int(sell_result.retcode), buy_retcode=int(buy_result.retcode), sell_order=int(getattr(sell_result, "order", 0) or 0), buy_order=int(getattr(buy_result, "order", 0) or 0), sell_volume=normalized_sell_lots, buy_volume=normalized_buy_lots)


def close_pair_positions(client: MT5Client, cfg: Settings, symbol_1: str, symbol_2: str, deviation: int = 20) -> ClosePairSummary:
    ensure_python_trading_enabled()
    positions = [*symbol_positions(symbol_1), *symbol_positions(symbol_2)]
    if not positions:
        return ClosePairSummary(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

    errors: list[str] = []
    closed_count = 0
    closed_tickets: list[int] = []

    for position in positions:
        try:
            client.ensure_symbol(str(position.symbol))
            close_position_with_fill_fallback(position, deviation=deviation, magic=cfg.mt5_magic)
            closed_count += 1
            closed_tickets.append(int(position.ticket))
        except Exception as exc:
            errors.append(str(exc))

    if errors:
        raise RuntimeError("\n".join(errors))

    all_deals: list = []
    missing_tickets: list[int] = []
    for ticket in closed_tickets:
        deals = wait_closed_position_deals(ticket)
        if not deals:
            missing_tickets.append(ticket)
            continue
        all_deals.extend(deals)

    if missing_tickets:
        missing_text = ", ".join(str(ticket) for ticket in missing_tickets)
        raise RuntimeError("Позиции закрыты, но MT5 пока не отдал историю сделок по position_id: " f"{missing_text}. Повтори через 1-2 секунды.")

    profit_usd, commission_usd, swap_usd, fee_usd = sum_deals(all_deals)
    total_pnl_usd = profit_usd + commission_usd + swap_usd + fee_usd
    return ClosePairSummary(closed_count=closed_count, deals_count=len(all_deals), profit_usd=float(profit_usd), commission_usd=float(commission_usd), swap_usd=float(swap_usd), fee_usd=float(fee_usd), total_pnl_usd=float(total_pnl_usd))


def reverse_pair_positions(client: MT5Client, cfg: Settings, symbol_1: str, symbol_2: str, deviation: int = 20) -> ReversePairSummary:
    ensure_python_trading_enabled()
    positions = [*symbol_positions(symbol_1), *symbol_positions(symbol_2)]
    if not positions:
        raise RuntimeError("Нет открытых позиций по текущей связке для разворота")

    reverse_legs = build_reverse_legs_from_positions(positions)
    if not reverse_legs:
        raise RuntimeError("Не удалось построить обратные позиции для разворота")

    close_summary = close_pair_positions(client=client, cfg=cfg, symbol_1=symbol_1, symbol_2=symbol_2, deviation=deviation)

    reopened_legs: list[ReopenedLeg] = []
    errors: list[str] = []
    for symbol, side, volume in reverse_legs:
        try:
            reopened_legs.append(_open_leg(client=client, cfg=cfg, symbol=symbol, side=side, volume=volume, deviation=deviation))
        except Exception as exc:
            errors.append(f"{side.upper()} {symbol} {volume:.2f}: {exc}")

    if errors:
        opened_text = "\n".join(f"{leg.side.upper()} {leg.symbol} {leg.volume:.2f} order={leg.order} retcode={leg.retcode}" for leg in reopened_legs)
        parts = ["Позиции закрыты, но разворот открыт не полностью."]
        if opened_text:
            parts.extend(["Уже открыто:", opened_text])
        parts.extend(["Ошибки:", "\n".join(errors)])
        raise RuntimeError("\n".join(parts))

    return ReversePairSummary(close_summary=close_summary, reopened_legs=reopened_legs)
