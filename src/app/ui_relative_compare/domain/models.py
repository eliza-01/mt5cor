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
class RangeStats:
    symbol_1_long_total: float
    symbol_2_long_total: float
    symbol_1_short_total: float
    symbol_2_short_total: float
    long_ratio: float
    short_ratio: float
    common_ratio: float
    apply_long: bool
    apply_short: bool
    apply_common: bool


@dataclass(slots=True)
class FlowDiagnostics:
    line_1_last: float
    line_2_last: float
    diff_last: float
    applied_ratio_long: float
    applied_ratio_short: float
    relation_mode: str


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
class LiveTailSnapshot:
    bar: pd.DataFrame
    flow_diagnostics: FlowDiagnostics
    trade_plan: TradePlan
    aggregate_progress: str | None
    source_count: int


@dataclass(slots=True)
class RenderSnapshot:
    bars: pd.DataFrame
    divergence_stats: DivergenceStats
    divergence_series: pd.Series
    trade_plan: TradePlan
    hedge_diagnostics: HedgeDiagnostics
    range_stats: RangeStats
    flow_diagnostics: FlowDiagnostics
    digits_1: int
    digits_2: int
    ratio_1_to_2: float
    negative_correlation: bool
    live_tail: LiveTailSnapshot | None = None