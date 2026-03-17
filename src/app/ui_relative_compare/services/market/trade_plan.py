from __future__ import annotations

import math

import pandas as pd

from src.app.ui_relative_compare.domain import HedgeDiagnostics, SignalDiagnostics, TradePlan
from src.app.ui_relative_compare.services.market.signal import build_spread_trade_directions
from src.broker.mt5_client import SymbolMeta
from src.common.settings import Settings
from .common import MIN_ORDER_LOTS


def normalize_lot(volume: float, meta: SymbolMeta) -> float:
    step = meta.volume_step or MIN_ORDER_LOTS
    minimum = meta.volume_min or MIN_ORDER_LOTS
    scaled = max(volume, minimum)
    normalized = math.floor((scaled + 1e-12) / step) * step
    digits = max(0, len(str(step).split(".")[-1].rstrip("0"))) if "." in str(step) else 0
    return round(max(normalized, minimum), digits)


def build_trade_plan(
    bars: pd.DataFrame,
    symbol_1: str,
    symbol_2: str,
    meta_1: SymbolMeta,
    meta_2: SymbolMeta,
    cfg: Settings,
    hedge: HedgeDiagnostics,
    signal: SignalDiagnostics,
) -> TradePlan:
    row = bars.iloc[-1]
    move_1 = abs(float(row["p1_close"]))
    move_2 = abs(float(row["p2_close"]))

    lot_1 = normalize_lot(cfg.base_lot_eurusd, meta_1)
    ratio_abs = hedge.execution_ratio_abs if hedge.execution_ratio_abs > 1e-12 else 1.0
    lot_2 = normalize_lot(cfg.base_lot_eurusd * ratio_abs, meta_2)

    spread_side, symbol_1_side, symbol_2_side = build_spread_trade_directions(
        signal_side=signal.signal_side,
        side_relation=hedge.side_relation,
    )

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
        signal_value=signal.ma_diff_last,
        entry_ready=signal.entry_ready,
        leader_symbol=leader_symbol,
        follower_symbol=follower_symbol,
        leader_move=leader_move,
        follower_move=follower_move,
    )
