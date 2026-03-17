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
class RelativeMetrics:
    ppm_1: float
    ppm_2: float
    ratio_1_to_2: float
    ratio_2_to_1: float


@dataclass(slots=True)
class HedgeDiagnostics:
    window: int
    correlation: float
    execution_ratio: float
    execution_ratio_abs: float
    side_relation: str
    spread_beta: float
    spread_intercept: float
    spread_last: float
    spread_mean: float
    spread_std: float
    spread_z: float
    coint_pvalue: float | None
    adf_pvalue: float | None
    conversion_mode_1: str
    conversion_mode_2: str


@dataclass(slots=True)
class SignalDiagnostics:
    fast_window: int
    slow_window: int
    entry_threshold: float
    exit_threshold: float
    gap_last: float
    fast_last: float
    slow_last: float
    ma_diff_last: float
    signal_side: str
    entry_ready: bool
    exit_ready: bool


@dataclass(slots=True)
class TradePlan:
    symbol_1: str
    symbol_2: str
    symbol_1_lots: float
    symbol_2_lots: float
    symbol_1_side: str
    symbol_2_side: str
    spread_side: str
    side_relation: str
    signal_value: float
    entry_ready: bool
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
    hedge_diagnostics: HedgeDiagnostics
    signal_diagnostics: SignalDiagnostics
    digits_1: int
    digits_2: int
    ratio_1_to_2: float
    negative_correlation: bool
