
# src/app/ui_relative_compare/services/trading.py
# Sends opposite market orders for the current relative leader and follower,
# and closes all positions for the selected pair with PnL summary.
from __future__ import annotations

from dataclasses import dataclass

import MetaTrader5 as mt5

from src.app.ui_relative_compare.models import TradePlan
from src.broker.mt5_client import MT5Client
from src.common.settings import Settings
from src.strategy.costs import commission_usd_per_lot_one_way


CLIENT_DISABLES_AT = 10027


@dataclass(slots=True)
class OrderSendSummary:
    sell_retcode: int
    buy_retcode: int
    sell_order: int
    buy_order: int


@dataclass(slots=True)
class ClosePairSummary:
    closed_count: int
    gross_pnl_usd: float
    net_pnl_est_usd: float


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


def _estimated_round_turn_commission_usd(symbol: str, volume: float, cfg: Settings) -> float:
    rate = commission_usd_per_lot_one_way(symbol, cfg)
    if rate is None:
        return 0.0
    return float(rate) * float(volume) * cfg.round_turn_multiplier


def open_opposite_positions(
    client: MT5Client,
    cfg: Settings,
    plan: TradePlan,
    deviation: int = 20,
) -> OrderSendSummary:
    _ensure_python_trading_enabled()

    client.ensure_symbol(plan.sell_symbol)
    client.ensure_symbol(plan.buy_symbol)

    sell_result = _send_market_with_fill_fallback(
        symbol=plan.sell_symbol,
        volume=plan.sell_lots,
        side="sell",
        deviation=deviation,
        magic=cfg.mt5_magic,
        comment="relative_compare_sell",
    )

    buy_result = _send_market_with_fill_fallback(
        symbol=plan.buy_symbol,
        volume=plan.buy_lots,
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
    )


def close_pair_positions(
    client: MT5Client,
    cfg: Settings,
    symbol_1: str,
    symbol_2: str,
    deviation: int = 20,
) -> ClosePairSummary:
    _ensure_python_trading_enabled()

    positions = [* _symbol_positions(symbol_1), * _symbol_positions(symbol_2)]
    if not positions:
        return ClosePairSummary(closed_count=0, gross_pnl_usd=0.0, net_pnl_est_usd=0.0)

    gross_pnl_usd = 0.0
    commission_est_usd = 0.0

    for position in positions:
        gross_pnl_usd += float(getattr(position, "profit", 0.0) or 0.0)
        gross_pnl_usd += float(getattr(position, "swap", 0.0) or 0.0)
        commission_est_usd += _estimated_round_turn_commission_usd(str(position.symbol), float(position.volume), cfg)

    errors: list[str] = []
    closed_count = 0

    for position in positions:
        try:
            client.ensure_symbol(str(position.symbol))
            _close_position_with_fill_fallback(position, deviation=deviation, magic=cfg.mt5_magic)
            closed_count += 1
        except Exception as exc:
            errors.append(str(exc))

    if errors:
        raise RuntimeError("\n".join(errors))

    return ClosePairSummary(
        closed_count=closed_count,
        gross_pnl_usd=float(gross_pnl_usd),
        net_pnl_est_usd=float(gross_pnl_usd - commission_est_usd),
    )
