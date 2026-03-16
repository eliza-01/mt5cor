from __future__ import annotations

import MetaTrader5 as mt5

from .terminal import CLIENT_DISABLES_AT


def filling_candidates(symbol: str) -> list[int]:
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


def build_market_request(symbol: str, volume: float, side: str, deviation: int, magic: int, comment: str, type_filling: int) -> dict:
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


def send_market_with_fill_fallback(symbol: str, volume: float, side: str, deviation: int, magic: int, comment: str):
    last_result = None
    for filling in filling_candidates(symbol):
        request = build_market_request(symbol=symbol, volume=volume, side=side, deviation=deviation, magic=magic, comment=comment, type_filling=filling)
        result = mt5.order_send(request)
        last_result = result

        if result is None:
            continue

        retcode = int(result.retcode)
        if retcode == mt5.TRADE_RETCODE_DONE:
            return result
        if retcode == CLIENT_DISABLES_AT:
            raise RuntimeError("MT5 вернул retcode=10027: торговля из Python запрещена терминалом. Включи Algo Trading и отключи запрет на внешний Python API в Tools -> Options -> Expert Advisors.")

    if last_result is None:
        raise RuntimeError(f"order_send вернул None: {mt5.last_error()}")

    raise RuntimeError(f"{side.upper()} {symbol} не открыт: retcode={int(last_result.retcode)} comment={str(getattr(last_result, 'comment', '') or '')}")


def build_close_request(position, deviation: int, magic: int, type_filling: int) -> dict:
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


def close_position_with_fill_fallback(position, deviation: int, magic: int):
    last_result = None
    for filling in filling_candidates(str(position.symbol)):
        request = build_close_request(position, deviation=deviation, magic=magic, type_filling=filling)
        result = mt5.order_send(request)
        last_result = result

        if result is None:
            continue

        retcode = int(result.retcode)
        if retcode == mt5.TRADE_RETCODE_DONE:
            return result
        if retcode == CLIENT_DISABLES_AT:
            raise RuntimeError("MT5 вернул retcode=10027: торговля из Python запрещена терминалом. Включи Algo Trading и отключи запрет на внешний Python API в Tools -> Options -> Expert Advisors.")

    if last_result is None:
        raise RuntimeError(f"close order_send вернул None: {mt5.last_error()}")

    raise RuntimeError(f"CLOSE {position.symbol} ticket={int(position.ticket)} не выполнен: retcode={int(last_result.retcode)} comment={str(getattr(last_result, 'comment', '') or '')}")
