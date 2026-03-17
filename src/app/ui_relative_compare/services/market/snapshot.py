from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.domain.models import (
    DivergenceStats,
    FlowDiagnostics,
    HedgeDiagnostics,
    LiveTailSnapshot,
    RenderSnapshot,
)
from src.app.ui_relative_compare.services.market.hedge import analyze_pair_hedge
from src.app.ui_relative_compare.services.market.signal import analyze_flow_signal
from src.broker.mt5_client import MT5Client
from .aggregation import aggregate_pair_frame
from .divergence import build_divergence_series
from .loaders import load_two_symbols
from .range_stats import build_range_stats
from .trade_plan import build_trade_plan
from .transform import build_relative_bars


def _empty_frame_like(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.iloc[0:0].copy().reset_index(drop=True)


def _apply_live_ticks(raw_frame: pd.DataFrame, tick_1, tick_2) -> pd.DataFrame:
    if raw_frame.empty:
        return raw_frame

    out = raw_frame.copy()
    last = len(out) - 1

    bid_1 = float(tick_1["bid"])
    bid_2 = float(tick_2["bid"])

    out.at[last, "close_1"] = bid_1
    out.at[last, "high_1"] = max(float(out.at[last, "high_1"]), bid_1)
    out.at[last, "low_1"] = min(float(out.at[last, "low_1"]), bid_1)

    out.at[last, "close_2"] = bid_2
    out.at[last, "high_2"] = max(float(out.at[last, "high_2"]), bid_2)
    out.at[last, "low_2"] = min(float(out.at[last, "low_2"]), bid_2)
    return out


def _split_closed_and_live_frames(raw_frame: pd.DataFrame, bars_per_candle: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    if raw_frame.empty:
        empty = _empty_frame_like(raw_frame)
        return empty, empty

    closed_source = raw_frame.iloc[:-1].copy().reset_index(drop=True)
    if closed_source.empty:
        return _empty_frame_like(raw_frame), raw_frame.copy().reset_index(drop=True)

    closed_aggregated = aggregate_pair_frame(closed_source, bars_per_candle).reset_index(drop=True)
    full_progress = f"{int(bars_per_candle)}/{int(bars_per_candle)}"

    if bars_per_candle > 1 and not closed_aggregated.empty:
        if str(closed_aggregated.iloc[-1]["agg_progress"]) != full_progress:
            closed_aggregated = closed_aggregated.iloc[:-1].reset_index(drop=True)

    consumed_raw = int(len(closed_aggregated) * max(1, int(bars_per_candle)))
    live_source = raw_frame.iloc[consumed_raw:].copy().reset_index(drop=True)
    return closed_aggregated, live_source


def _build_zero_divergence(ratio_1_to_2: float) -> tuple[pd.Series, DivergenceStats]:
    return (
        pd.Series(dtype=float),
        DivergenceStats(
            total_diff_pips=0.0,
            current_bar_diff_pips=0.0,
            live_diff_pips=0.0,
            uses_ratio=abs(float(ratio_1_to_2) - 1.0) > 1e-12,
        ),
    )


def _build_flow(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
    range_stats,
    relation_mode: str,
) -> FlowDiagnostics:
    if bars.empty:
        return FlowDiagnostics(
            line_1_last=0.0,
            line_2_last=0.0,
            diff_last=0.0,
            applied_ratio_long=float(range_stats.common_ratio if range_stats.apply_common else (range_stats.long_ratio if range_stats.apply_long else 1.0)),
            applied_ratio_short=float(range_stats.common_ratio if range_stats.apply_common else (range_stats.short_ratio if range_stats.apply_short else 1.0)),
            relation_mode=relation_mode,
        )

    flow_result = analyze_flow_signal(
        bars=bars,
        digits_1=digits_1,
        digits_2=digits_2,
        invert_second=invert_second,
        mutual_exclusion_enabled=mutual_exclusion_enabled,
        range_stats=range_stats,
    )
    return FlowDiagnostics(
        line_1_last=flow_result.line_1_last,
        line_2_last=flow_result.line_2_last,
        diff_last=flow_result.diff_last,
        applied_ratio_long=flow_result.applied_ratio_long,
        applied_ratio_short=flow_result.applied_ratio_short,
        relation_mode=relation_mode,
    )


def build_render_snapshot(
    client: MT5Client,
    symbol_1: str,
    symbol_2: str,
    timeframe: str,
    bars_count: int,
    bars_per_candle: int,
    mutual_exclusion_enabled: bool,
    base_lot: float,
    lot_multiplier_1: float,
    lot_multiplier_2: float,
    apply_long_ratio: bool,
    apply_short_ratio: bool,
    apply_common_ratio: bool,
    use_live_ticks: bool = True,
) -> RenderSnapshot:
    raw_frame, meta_1, meta_2 = load_two_symbols(client, symbol_1, symbol_2, timeframe, bars_count)

    tick_1 = client.tick(symbol_1)
    tick_2 = client.tick(symbol_2)

    if use_live_ticks:
        raw_frame = _apply_live_ticks(raw_frame, tick_1, tick_2)

    hedge_source = raw_frame.iloc[:-1].copy().reset_index(drop=True)
    if len(hedge_source) < 10:
        hedge_source = raw_frame.copy().reset_index(drop=True)

    hedge_result = analyze_pair_hedge(
        close_1=hedge_source["close_1"],
        close_2=hedge_source["close_2"],
        symbol_1=symbol_1,
        symbol_2=symbol_2,
        meta_1=meta_1,
        meta_2=meta_2,
    )
    effective_invert_second = hedge_result.side_relation == "same"

    closed_frame, live_source = _split_closed_and_live_frames(raw_frame, bars_per_candle)

    range_stats = build_range_stats(
        frame=closed_frame,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        apply_long=apply_long_ratio,
        apply_short=apply_short_ratio,
        apply_common=apply_common_ratio,
    )

    effective_ratio = float(range_stats.common_ratio) if range_stats.apply_common else 1.0

    bars = build_relative_bars(
        closed_frame,
        meta_1.digits,
        meta_2.digits,
        effective_ratio,
        effective_invert_second,
    )

    if closed_frame.empty:
        divergence_series, divergence_stats = _build_zero_divergence(effective_ratio)
    else:
        divergence_series, divergence_stats = build_divergence_series(
            frame=closed_frame,
            digits_1=meta_1.digits,
            digits_2=meta_2.digits,
            ratio_1_to_2=effective_ratio,
            invert_second=effective_invert_second,
            bid_1=None,
            bid_2=None,
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

    base_plan_bars = bars
    if base_plan_bars.empty and not live_source.empty:
        live_preview_frame = aggregate_pair_frame(live_source, bars_per_candle).tail(1).reset_index(drop=True)
        base_plan_bars = build_relative_bars(
            live_preview_frame,
            meta_1.digits,
            meta_2.digits,
            effective_ratio,
            effective_invert_second,
        )

    flow = _build_flow(
        bars=bars if not bars.empty else base_plan_bars,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        invert_second=effective_invert_second,
        mutual_exclusion_enabled=mutual_exclusion_enabled,
        range_stats=range_stats,
        relation_mode=hedge.side_relation,
    )

    trade_plan = build_trade_plan(
        bars=base_plan_bars,
        symbol_1=symbol_1,
        symbol_2=symbol_2,
        meta_1=meta_1,
        meta_2=meta_2,
        hedge=hedge,
        flow=flow,
        range_stats=range_stats,
        base_lot=base_lot,
        lot_multiplier_1=lot_multiplier_1,
        lot_multiplier_2=lot_multiplier_2,
    )

    live_tail: LiveTailSnapshot | None = None
    if not live_source.empty:
        live_preview_frame = aggregate_pair_frame(live_source, bars_per_candle).tail(1).reset_index(drop=True)
        live_bar = build_relative_bars(
            live_preview_frame,
            meta_1.digits,
            meta_2.digits,
            effective_ratio,
            effective_invert_second,
        )

        combined_bars = pd.concat([bars, live_bar], ignore_index=True)
        live_flow = _build_flow(
            bars=combined_bars,
            digits_1=meta_1.digits,
            digits_2=meta_2.digits,
            invert_second=effective_invert_second,
            mutual_exclusion_enabled=mutual_exclusion_enabled,
            range_stats=range_stats,
            relation_mode=hedge.side_relation,
        )
        live_trade_plan = build_trade_plan(
            bars=combined_bars,
            symbol_1=symbol_1,
            symbol_2=symbol_2,
            meta_1=meta_1,
            meta_2=meta_2,
            hedge=hedge,
            flow=live_flow,
            range_stats=range_stats,
            base_lot=base_lot,
            lot_multiplier_1=lot_multiplier_1,
            lot_multiplier_2=lot_multiplier_2,
        )

        live_tail = LiveTailSnapshot(
            bar=live_bar,
            flow_diagnostics=live_flow,
            trade_plan=live_trade_plan,
            aggregate_progress=str(live_preview_frame.iloc[-1]["agg_progress"]) if "agg_progress" in live_preview_frame.columns else None,
            source_count=int(len(live_source)),
        )

    return RenderSnapshot(
        bars=bars,
        divergence_stats=divergence_stats,
        divergence_series=divergence_series,
        trade_plan=trade_plan,
        hedge_diagnostics=hedge,
        range_stats=range_stats,
        flow_diagnostics=flow,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        ratio_1_to_2=effective_ratio,
        negative_correlation=effective_invert_second,
        live_tail=live_tail,
    )