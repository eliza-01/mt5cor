# src/app/ui_relative_compare/services/trading.py
# Sends opposite market orders for an explicitly selected symbol direction,
# and closes all positions for the selected pair with PnL summary from actual MT5 deal history.
from __future__ import annotations

from dataclasses import dataclass
import math
import time

import MetaTrader5 as mt5

from src.broker.mt5_client import MT5Client
from src.common.settings import Settings


CLIENT_DISABLES_AT = 10027
MIN_ORDER_LOTS = 0.01

DEAL_ENTRY_OUT = int(getattr(mt5, "DEAL_ENTRY_OUT", 1))
DEAL_ENTRY_OUT_BY = int(getattr(mt5, "DEAL_ENTRY_OUT_BY", 3))
DEAL_ENTRY_INOUT = int(getattr(mt5, "DEAL_ENTRY_INOUT", 2))
CLOSE_ENTRIES = {DEAL_ENTRY_OUT, DEAL_ENTRY_OUT_BY, DEAL_ENTRY_INOUT}


@dataclass(slots=True)
class OrderSendSummary:
    sell_retcode: int
    buy_retcode: int
    sell_order: int
    buy_order: int
    sell_volume: float
    buy_volume: float


@dataclass(slots=True)
class ClosePairSummary:
    closed_count: int
    deals_count: int
    profit_usd: float
    commission_usd: float
    swap_usd: float
    fee_usd: float
    total_pnl_usd: float


def _terminal_flags() -> dict:
    info = mt5.terminal_info()
    if info is None:
        return {}
    try:
        return info._asdict()
    except Exception:
        return {}


def _ensure_python_trading_enabled() -> None:
    flags = _terminal_flags()

    if bool(flags.get("tradeapi_disabled", False)):
        raise RuntimeError(
            "В MT5 запрещена торговля через внешний Python API. "
            "Открой Tools -> Options -> Expert Advisors и отключи "
            "'Disable automatic trading via external Python API'. "
            "Также проверь, что кнопка Algo Trading включена."
        )

    if "trade_allowed" in flags and not bool(flags.get("trade_allowed")):
        raise RuntimeError(
            "В MT5 выключена автоматическая торговля. "
            "Включи кнопку Algo Trading в терминале."
        )


def _normalize_volume(volume: float, symbol: str) -> float:
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"Не удалось получить symbol_info для {symbol}")

    step = float(getattr(info, "volume_step", 0.0) or MIN_ORDER_LOTS)
    minimum = float(getattr(info, "volume_min", 0.0) or MIN_ORDER_LOTS)
    maximum = float(getattr(info, "volume_max", 0.0) or 0.0)

    raw = float(volume)
    if raw <= 0:
        raise RuntimeError(f"Объем для {symbol} должен быть больше 0")

    clamped = max(raw, minimum)
    if maximum > 0:
        clamped = min(clamped, maximum)

    normalized = math.floor((clamped + 1e-12) / step) * step
    digits = max(0, len(str(step).split(".")[-1].rstrip("0"))) if "." in str(step) else 0
    return round(max(normalized, minimum), digits)


def _filling_candidates(symbol: str) -> list[int]:
    info = mt5.symbol_info(symbol)
    candidates: list[int] = []

    if info is not None:
        try:
            filling_mode = int(getattr(info, "filling_mode", 0) or 0)
        except Exception:
            filling_mode = 0

        if filling_mode & 1:
            candidates.append(mt5.ORDER_FILLING_FOK)
        if filling_mode & 2:
            candidates.append(mt5.ORDER_FILLING_IOC)

        trade_exemode = getattr(info, "trade_exemode", None)
        if trade_exemode != getattr(mt5, "SYMBOL_TRADE_EXECUTION_MARKET", None):
            candidates.append(mt5.ORDER_FILLING_RETURN)

    for value in (mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN):
        if value not in candidates:
            candidates.append(value)

    return candidates


def _build_market_request(
    symbol: str,
    volume: float,
    side: str,
    deviation: int,
    magic: int,
    comment: str,
    type_filling: int,
) -> dict:
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"Не удалось получить тик для {symbol}")

    order_type = mt5.ORDER_TYPE_SELL if side == "sell" else mt5.ORDER_TYPE_BUY
    price = float(tick.bid if side == "sell" else tick.ask)

    return {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "price": price,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }


def _send_market_with_fill_fallback(
    symbol: str,
    volume: float,
    side: str,
    deviation: int,
    magic: int,
    comment: str,
):
    last_result = None

    for filling in _filling_candidates(symbol):
        request = _build_market_request(
            symbol=symbol,
            volume=volume,
            side=side,
            deviation=deviation,
            magic=magic,
            comment=comment,
            type_filling=filling,
        )
        result = mt5.order_send(request)
        last_result = result

        if result is None:
            continue

        retcode = int(result.retcode)
        if retcode == mt5.TRADE_RETCODE_DONE:
            return result
        if retcode == CLIENT_DISABLES_AT:
            raise RuntimeError(
                "MT5 вернул retcode=10027: торговля из Python запрещена терминалом. "
                "Включи Algo Trading и отключи запрет на внешний Python API "
                "в Tools -> Options -> Expert Advisors."
            )

    if last_result is None:
        raise RuntimeError(f"order_send вернул None: {mt5.last_error()}")

    raise RuntimeError(
        f"{side.upper()} {symbol} не открыт: retcode={int(last_result.retcode)} "
        f"comment={str(getattr(last_result, 'comment', '') or '')}"
    )


def _build_close_request(position, deviation: int, magic: int, type_filling: int) -> dict:
    symbol = str(position.symbol)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"Не удалось получить тик для {symbol}")

    if int(position.type) == mt5.ORDER_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = float(tick.bid)
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = float(tick.ask)

    return {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(position.volume),
        "type": order_type,
        "position": int(position.ticket),
        "price": price,
        "deviation": deviation,
        "magic": magic,
        "comment": "relative_compare_close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }


def _close_position_with_fill_fallback(position, deviation: int, magic: int):
    last_result = None

    for filling in _filling_candidates(str(position.symbol)):
        request = _build_close_request(position, deviation=deviation, magic=magic, type_filling=filling)
        result = mt5.order_send(request)
        last_result = result

        if result is None:
            continue

        retcode = int(result.retcode)
        if retcode == mt5.TRADE_RETCODE_DONE:
            return result
        if retcode == CLIENT_DISABLES_AT:
            raise RuntimeError(
                "MT5 вернул retcode=10027: торговля из Python запрещена терминалом. "
                "Включи Algo Trading и отключи запрет на внешний Python API "
                "в Tools -> Options -> Expert Advisors."
            )

    if last_result is None:
        raise RuntimeError(f"close order_send вернул None: {mt5.last_error()}")

    raise RuntimeError(
        f"CLOSE {position.symbol} ticket={int(position.ticket)} не выполнен: "
        f"retcode={int(last_result.retcode)} comment={str(getattr(last_result, 'comment', '') or '')}"
    )


def _symbol_positions(symbol: str) -> list:
    items = mt5.positions_get(symbol=symbol)
    return list(items or [])


def _position_is_closed(ticket: int) -> bool:
    items = mt5.positions_get(ticket=int(ticket))
    return not items


def _position_deals(ticket: int) -> list:
    deals = mt5.history_deals_get(position=int(ticket))
    return list(deals or [])


def _has_close_deal(deals: list) -> bool:
    for deal in deals:
        entry = int(getattr(deal, "entry", -1))
        if entry in CLOSE_ENTRIES:
            return True
    return False


def _wait_closed_position_deals(ticket: int, timeout_sec: float = 10.0, sleep_sec: float = 0.2) -> list:
    deadline = time.time() + timeout_sec
    last_deals: list = []

    while time.time() < deadline:
        closed = _position_is_closed(ticket)
        deals = _position_deals(ticket)

        if deals:
            last_deals = deals
            if _has_close_deal(deals):
                return deals

        if closed and deals:
            return deals

        time.sleep(sleep_sec)

    return last_deals


def _sum_deals(deals: list) -> tuple[float, float, float, float]:
    profit_usd = 0.0
    commission_usd = 0.0
    swap_usd = 0.0
    fee_usd = 0.0

    for deal in deals:
        profit_usd += float(getattr(deal, "profit", 0.0) or 0.0)
        commission_usd += float(getattr(deal, "commission", 0.0) or 0.0)
        swap_usd += float(getattr(deal, "swap", 0.0) or 0.0)
        fee_usd += float(getattr(deal, "fee", 0.0) or 0.0)

    return profit_usd, commission_usd, swap_usd, fee_usd


def open_pair_positions(
    client: MT5Client,
    cfg: Settings,
    sell_symbol: str,
    buy_symbol: str,
    sell_lots: float,
    buy_lots: float,
    deviation: int = 20,
) -> OrderSendSummary:
    _ensure_python_trading_enabled()

    client.ensure_symbol(sell_symbol)
    client.ensure_symbol(buy_symbol)

    normalized_sell_lots = _normalize_volume(sell_lots, sell_symbol)
    normalized_buy_lots = _normalize_volume(buy_lots, buy_symbol)

    sell_result = _send_market_with_fill_fallback(
        symbol=sell_symbol,
        volume=normalized_sell_lots,
        side="sell",
        deviation=deviation,
        magic=cfg.mt5_magic,
        comment="relative_compare_sell",
    )

    buy_result = _send_market_with_fill_fallback(
        symbol=buy_symbol,
        volume=normalized_buy_lots,
        side="buy",
        deviation=deviation,
        magic=cfg.mt5_magic,
        comment="relative_compare_buy",
    )

    return OrderSendSummary(
        sell_retcode=int(sell_result.retcode),
        buy_retcode=int(buy_result.retcode),
        sell_order=int(getattr(sell_result, "order", 0) or 0),
        buy_order=int(getattr(buy_result, "order", 0) or 0),
        sell_volume=normalized_sell_lots,
        buy_volume=normalized_buy_lots,
    )


def close_pair_positions(
    client: MT5Client,
    cfg: Settings,
    symbol_1: str,
    symbol_2: str,
    deviation: int = 20,
) -> ClosePairSummary:
    _ensure_python_trading_enabled()

    positions = [*_symbol_positions(symbol_1), *_symbol_positions(symbol_2)]
    if not positions:
        return ClosePairSummary(
            closed_count=0,
            deals_count=0,
            profit_usd=0.0,
            commission_usd=0.0,
            swap_usd=0.0,
            fee_usd=0.0,
            total_pnl_usd=0.0,
        )

    errors: list[str] = []
    closed_count = 0
    closed_tickets: list[int] = []

    for position in positions:
        try:
            client.ensure_symbol(str(position.symbol))
            _close_position_with_fill_fallback(position, deviation=deviation, magic=cfg.mt5_magic)
            closed_count += 1
            closed_tickets.append(int(position.ticket))
        except Exception as exc:
            errors.append(str(exc))

    if errors:
        raise RuntimeError("\n".join(errors))

    all_deals: list = []
    missing_tickets: list[int] = []

    for ticket in closed_tickets:
        deals = _wait_closed_position_deals(ticket)
        if not deals:
            missing_tickets.append(ticket)
            continue
        all_deals.extend(deals)

    if missing_tickets:
        missing_text = ", ".join(str(ticket) for ticket in missing_tickets)
        raise RuntimeError(
            "Позиции закрыты, но MT5 пока не отдал историю сделок по position_id: "
            f"{missing_text}. Повтори через 1-2 секунды."
        )

    profit_usd, commission_usd, swap_usd, fee_usd = _sum_deals(all_deals)
    total_pnl_usd = profit_usd + commission_usd + swap_usd + fee_usd

    return ClosePairSummary(
        closed_count=closed_count,
        deals_count=len(all_deals),
        profit_usd=float(profit_usd),
        commission_usd=float(commission_usd),
        swap_usd=float(swap_usd),
        fee_usd=float(fee_usd),
        total_pnl_usd=float(total_pnl_usd),
    )