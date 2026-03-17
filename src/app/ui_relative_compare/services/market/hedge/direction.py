from __future__ import annotations


def side_relation_from_ratio(execution_ratio: float) -> str:
    return "same" if float(execution_ratio) >= 0.0 else "opposite"


def paired_side(primary_side: str, side_relation: str) -> str:
    if side_relation == "same":
        return primary_side
    return "buy" if primary_side == "sell" else "sell"


def build_spread_trade_directions(spread_z: float, side_relation: str) -> tuple[str, str, str]:
    spread_side = "short" if float(spread_z) >= 0.0 else "long"
    symbol_1_side = "sell" if spread_side == "short" else "buy"
    symbol_2_side = paired_side(symbol_1_side, side_relation)
    return spread_side, symbol_1_side, symbol_2_side
