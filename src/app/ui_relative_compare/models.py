# src/app/ui_relative_compare/models.py
# Dataclasses for metrics, render snapshot, divergence stats, and trade plan.
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class RelativeMetrics:
    ppm_1: float
    ppm_2: float
    ratio_1_to_2: float
    ratio_2_to_1: float


@dataclass(slots=True)
class DivergenceStats:
    total_diff_pips: float
    current_bar_diff_pips: float
    live_diff_pips: float
    uses_ratio: bool


@dataclass(slots=True)
class TradePlan:
    sell_symbol: str
    buy_symbol: str
    sell_lots: float
    buy_lots: float
    leader_symbol: str
    follower_symbol: str
    leader_move: float
    follower_move: float
    button_text: str


@dataclass(slots=True)
class RenderSnapshot:
    bars: pd.DataFrame
    metrics: RelativeMetrics
    divergence_stats: DivergenceStats
    divergence_series: pd.Series
    trade_plan: TradePlan
    digits_1: int
    digits_2: int