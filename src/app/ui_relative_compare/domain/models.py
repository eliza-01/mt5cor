from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class DivergenceStats:
    total_diff_pips: float
    current_bar_diff_pips: float
    live_diff_pips: float
    uses_ratio: bool


@dataclass(slots=True)
class TradePlan:
    symbol_1: str
    symbol_2: str
    symbol_1_lots: float
    symbol_2_lots: float
    sell_symbol: str
    buy_symbol: str
    leader_symbol: str
    follower_symbol: str
    leader_move: float
    follower_move: float


@dataclass(slots=True)
class RenderSnapshot:
    bars: pd.DataFrame
    divergence_stats: DivergenceStats
    divergence_series: pd.Series
    trade_plan: TradePlan
    digits_1: int
    digits_2: int
    ratio_1_to_2: float
    negative_correlation: bool