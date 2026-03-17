from __future__ import annotations

import math

import pandas as pd

from src.app.ui_relative_compare.domain import FlowDiagnostics, HedgeDiagnostics, RangeStats, TradePlan
from src.broker.mt5_client import SymbolMeta
from .common import MIN_ORDER_LOTS


def normalize_lot(volume: float, meta: SymbolMeta) -> float:
    step = meta.volume_step or MIN_ORDER_LOTS
    minimum = meta.volume_min or MIN_ORDER_LOTS
    scaled = max(volume, minimum)
    normalized = math.floor((scaled + 1e-12) / step) * step
    digits = max(0, len(str(step).split(".")[-1].rstrip("0"))) if "." in str(step) else 0
    return round(max(normalized, minimum), digits)


def ratio_for_side(side: str, range_stats: RangeStats) -> float:
    if range_stats.apply_common:
        return float(range_stats.common_ratio)
    if side == "buy" and range_stats.apply_long:
        return float(range_stats.long_ratio)
    if side == "sell" and range_stats.apply_short:
        return float(range_stats.short_ratio)
    return 1.0


def build_trade_plan(
    bars: pd.DataFrame,
    symbol_1: str,
    symbol_2: str,
    meta_1: SymbolMeta,
    meta_2: SymbolMeta,
    hedge: HedgeDiagnostics,
    flow: FlowDiagnostics,
    range_stats: RangeStats,
    base_lot: float,
    lot_multiplier_1: float,
    lot_multiplier_2: float,
) -> TradePlan:
    row = bars.iloc[-1]
    move_1 = abs(float(row["p1_close"]))
    move_2 = abs(float(row["p2_close"]))

    signal_value = float(flow.diff_last)
    if signal_value > 0:
        spread_side, symbol_1_side = "short", "sell"
    elif signal_value < 0:
        spread_side, symbol_1_side = "long", "buy"
    else:
        spread_side, symbol_1_side = "flat", "flat"

    if hedge.side_relation == "same":
        symbol_2_side = symbol_1_side
    elif symbol_1_side == "sell":
        symbol_2_side = "buy"
    elif symbol_1_side == "buy":
        symbol_2_side = "sell"
    else:
        symbol_2_side = "flat"

    ratio_1 = 1.0
    ratio_2 = ratio_for_side(symbol_1_side, range_stats) if symbol_1_side != "flat" else (float(range_stats.common_ratio) if range_stats.apply_common else 1.0)

    lot_1 = normalize_lot(float(base_lot) * float(lot_multiplier_1) * ratio_1, meta_1)
    lot_2 = normalize_lot(float(base_lot) * float(lot_multiplier_2) * ratio_2, meta_2)

    if move_1 >= move_2:
        leader_symbol, follower_symbol = symbol_1, symbol_2
        leader_move, follower_move = move_1, move_2
    else:
        leader_symbol, follower_symbol = symbol_2, symbol_1
        leader_move, follower_move = move_2, move_1

    return TradePlan(
        symbol_1=symbol_1,
        symbol_2=symbol_2,
        symbol_1_lots=lot_1,
        symbol_2_lots=lot_2,
        symbol_1_side=symbol_1_side,
        symbol_2_side=symbol_2_side,
        spread_side=spread_side,
        side_relation=hedge.side_relation,
        signal_value=signal_value,
        entry_ready=False,
        leader_symbol=leader_symbol,
        follower_symbol=follower_symbol,
        leader_move=leader_move,
        follower_move=follower_move,
    )
