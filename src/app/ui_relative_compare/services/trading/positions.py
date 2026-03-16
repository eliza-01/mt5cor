from __future__ import annotations

import MetaTrader5 as mt5


def symbol_positions(symbol: str) -> list:
    items = mt5.positions_get(symbol=symbol)
    return list(items or [])


def build_reverse_legs_from_positions(positions: list) -> list[tuple[str, str, float]]:
    aggregated: dict[tuple[str, str], float] = {}

    for position in positions:
        symbol = str(position.symbol)
        volume = float(getattr(position, "volume", 0.0) or 0.0)
        if volume <= 0:
            continue
        current_type = int(getattr(position, "type", -1))
        reverse_side = "sell" if current_type == mt5.ORDER_TYPE_BUY else "buy"
        key = (symbol, reverse_side)
        aggregated[key] = aggregated.get(key, 0.0) + volume

    legs: list[tuple[str, str, float]] = []
    for (symbol, side), volume in sorted(aggregated.items(), key=lambda item: (0 if item[0][1] == "sell" else 1, item[0][0])):
        if volume > 0:
            legs.append((symbol, side, float(volume)))
    return legs
