from __future__ import annotations

from src.app.ui_relative_compare.domain import HedgeDiagnostics, RenderSnapshot, SignalDiagnostics
from src.app.ui_relative_compare.services.market.hedge import analyze_pair_hedge
from src.app.ui_relative_compare.services.market.signal import analyze_ma_gap_signal
from src.broker.mt5_client import MT5Client
from src.common.settings import Settings
from .aggregation import aggregate_pair_frame
from .divergence import build_divergence_series
from .loaders import load_two_symbols
from .trade_plan import build_trade_plan
from .transform import build_relative_bars


def build_render_snapshot(
    client: MT5Client,
    cfg: Settings,
    symbol_1: str,
    symbol_2: str,
    timeframe: str,
    bars_count: int,
    ratio_1_to_2: float,
    bars_per_candle: int,
    mutual_exclusion_enabled: bool,
    signal_fast_window: int,
    signal_slow_window: int,
    signal_entry_threshold: float,
    signal_exit_threshold: float,
    invert_second: bool = False,
) -> RenderSnapshot:
    raw_frame, meta_1, meta_2 = load_two_symbols(client, symbol_1, symbol_2, timeframe, bars_count)
    hedge_result = analyze_pair_hedge(
        close_1=raw_frame["close_1"],
        close_2=raw_frame["close_2"],
        symbol_1=symbol_1,
        symbol_2=symbol_2,
        meta_1=meta_1,
        meta_2=meta_2,
    )
    effective_ratio = hedge_result.execution_ratio_abs if hedge_result.execution_ratio_abs > 1e-12 else ratio_1_to_2
    effective_invert_second = hedge_result.side_relation == "same"

    render_frame = aggregate_pair_frame(raw_frame, bars_per_candle)
    bars = build_relative_bars(
        render_frame,
        meta_1.digits,
        meta_2.digits,
        effective_ratio,
        effective_invert_second,
    )

    tick_1 = client.tick(symbol_1)
    tick_2 = client.tick(symbol_2)
    divergence_series, divergence_stats = build_divergence_series(
        frame=render_frame,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        ratio_1_to_2=effective_ratio,
        invert_second=effective_invert_second,
        bid_1=float(tick_1["bid"]),
        bid_2=float(tick_2["bid"]),
    )

    hedge = HedgeDiagnostics(
        window=hedge_result.window,
        correlation=hedge_result.correlation,
        execution_ratio=hedge_result.execution_ratio,
        execution_ratio_abs=hedge_result.execution_ratio_abs,
        side_relation=hedge_result.side_relation,
        spread_beta=hedge_result.spread.beta,
        spread_intercept=hedge_result.spread.intercept,
        spread_last=hedge_result.spread.last,
        spread_mean=hedge_result.spread.mean,
        spread_std=hedge_result.spread.std,
        spread_z=hedge_result.spread.zscore,
        coint_pvalue=hedge_result.spread.coint_pvalue,
        adf_pvalue=hedge_result.spread.adf_pvalue,
        conversion_mode_1=hedge_result.conversion_mode_1,
        conversion_mode_2=hedge_result.conversion_mode_2,
    )

    signal_result = analyze_ma_gap_signal(
        bars=bars,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        ratio_1_to_2=effective_ratio,
        invert_second=effective_invert_second,
        mutual_exclusion_enabled=mutual_exclusion_enabled,
        fast_window=signal_fast_window,
        slow_window=signal_slow_window,
        entry_threshold=signal_entry_threshold,
        exit_threshold=signal_exit_threshold,
    )
    signal = SignalDiagnostics(
        fast_window=signal_result.fast_window,
        slow_window=signal_result.slow_window,
        entry_threshold=signal_result.entry_threshold,
        exit_threshold=signal_result.exit_threshold,
        gap_last=signal_result.gap_last,
        fast_last=signal_result.fast_last,
        slow_last=signal_result.slow_last,
        ma_diff_last=signal_result.ma_diff_last,
        signal_side=signal_result.signal_side,
        entry_ready=signal_result.entry_ready,
        exit_ready=signal_result.exit_ready,
    )

    trade_plan = build_trade_plan(bars, symbol_1, symbol_2, meta_1, meta_2, cfg, hedge, signal)
    return RenderSnapshot(
        bars=bars,
        divergence_stats=divergence_stats,
        divergence_series=divergence_series,
        trade_plan=trade_plan,
        hedge_diagnostics=hedge,
        signal_diagnostics=signal,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        ratio_1_to_2=effective_ratio,
        negative_correlation=effective_invert_second,
    )
