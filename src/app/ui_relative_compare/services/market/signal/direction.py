from __future__ import annotations


def paired_side(primary_side: str, side_relation: str) -> str:
    if side_relation == "same":
        return primary_side
    return "buy" if primary_side == "sell" else "sell"


def build_spread_trade_directions(signal_side: str, side_relation: str) -> tuple[str, str, str]:
    if signal_side == "short":
        symbol_1_side = "sell"
    elif signal_side == "long":
        symbol_1_side = "buy"
    else:
        return "flat", "flat", "flat"

    symbol_2_side = paired_side(symbol_1_side, side_relation)
    return signal_side, symbol_1_side, symbol_2_side
