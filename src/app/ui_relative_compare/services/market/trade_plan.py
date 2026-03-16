from __future__ import annotations

import math

import pandas as pd

from src.app.ui_relative_compare.domain import TradePlan
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


def build_trade_plan(bars: pd.DataFrame, symbol_1: str, symbol_2: str, meta_1: SymbolMeta, meta_2: SymbolMeta, cfg: Settings, ratio_1_to_2: float) -> TradePlan:
    row = bars.iloc[-1]
    move_1 = abs(float(row["p1_close"]))
    move_2 = abs(float(row["p2_close"]))

    lot_1 = normalize_lot(cfg.base_lot_eurusd, meta_1)
    lot_2 = normalize_lot(cfg.base_lot_eurusd * ratio_1_to_2, meta_2)

    if move_1 >= move_2:
        sell_symbol, buy_symbol = symbol_1, symbol_2
        leader_symbol, follower_symbol = symbol_1, symbol_2
        leader_move, follower_move = move_1, move_2
    else:
        sell_symbol, buy_symbol = symbol_2, symbol_1
        leader_symbol, follower_symbol = symbol_2, symbol_1
        leader_move, follower_move = move_2, move_1

    return TradePlan(symbol_1=symbol_1, symbol_2=symbol_2, symbol_1_lots=lot_1, symbol_2_lots=lot_2, sell_symbol=sell_symbol, buy_symbol=buy_symbol, leader_symbol=leader_symbol, follower_symbol=follower_symbol, leader_move=leader_move, follower_move=follower_move)
