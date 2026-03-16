from __future__ import annotations

from src.app.ui_relative_compare.domain import RenderSnapshot
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
    invert_second: bool = False,
) -> RenderSnapshot:
    raw_frame, meta_1, meta_2 = load_two_symbols(client, symbol_1, symbol_2, timeframe, bars_count)
    render_frame = aggregate_pair_frame(raw_frame, bars_per_candle)
    bars = build_relative_bars(render_frame, meta_1.digits, meta_2.digits, ratio_1_to_2, invert_second)

    tick_1 = client.tick(symbol_1)
    tick_2 = client.tick(symbol_2)
    divergence_series, divergence_stats = build_divergence_series(
        frame=render_frame,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        ratio_1_to_2=ratio_1_to_2,
        invert_second=invert_second,
        bid_1=float(tick_1["bid"]),
        bid_2=float(tick_2["bid"]),
    )

    trade_plan = build_trade_plan(bars, symbol_1, symbol_2, meta_1, meta_2, cfg, ratio_1_to_2)
    return RenderSnapshot(
        bars=bars,
        divergence_stats=divergence_stats,
        divergence_series=divergence_series,
        trade_plan=trade_plan,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        ratio_1_to_2=ratio_1_to_2,
        negative_correlation=invert_second,
    )