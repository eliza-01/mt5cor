from __future__ import annotations

import pandas as pd

from src.broker.mt5_client import MT5Client, SymbolMeta


def load_two_symbols(
    client: MT5Client,
    symbol_1: str,
    symbol_2: str,
    timeframe: str,
    bars: int,
) -> tuple[pd.DataFrame, SymbolMeta, SymbolMeta]:
    frame_1 = client.copy_rates(symbol_1, timeframe, bars).copy()
    frame_2 = client.copy_rates(symbol_2, timeframe, bars).copy()

    meta_1 = client.symbol_meta(symbol_1)
    meta_2 = client.symbol_meta(symbol_2)

    frame_1 = frame_1.rename(columns={"open": "open_1", "high": "high_1", "low": "low_1", "close": "close_1", "tick_volume": "tick_volume_1"})
    frame_2 = frame_2.rename(columns={"open": "open_2", "high": "high_2", "low": "low_2", "close": "close_2", "tick_volume": "tick_volume_2"})

    merged = pd.merge(
        frame_1[["time", "open_1", "high_1", "low_1", "close_1", "tick_volume_1"]],
        frame_2[["time", "open_2", "high_2", "low_2", "close_2", "tick_volume_2"]],
        on="time",
        how="inner",
    )
    if merged.empty:
        raise RuntimeError("Не удалось выровнять историю двух символов по времени")

    return merged.reset_index(drop=True), meta_1, meta_2
