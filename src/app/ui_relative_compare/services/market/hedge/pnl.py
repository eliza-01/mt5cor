from __future__ import annotations

import pandas as pd

from .models import PnLSeriesResult
from .symbols import split_fx_symbol

DEFAULT_CONTRACT_SIZE = 100000.0


def contract_size_from_meta(meta) -> float:
    return float(getattr(meta, "trade_contract_size", 0.0) or DEFAULT_CONTRACT_SIZE)


def build_pnl_series_per_1lot(close: pd.Series, symbol: str, meta=None) -> PnLSeriesResult:
    base, quote = split_fx_symbol(symbol)
    contract_size = contract_size_from_meta(meta)
    px = close.astype(float)
    delta = px.diff().fillna(0.0)

    if quote == "USD":
        return PnLSeriesResult(values=contract_size * delta, conversion_mode="quote_usd_exact")

    if base == "USD":
        safe_px = px.replace(0.0, pd.NA).ffill().bfill()
        values = (contract_size * delta / safe_px).fillna(0.0)
        return PnLSeriesResult(values=values, conversion_mode="base_usd_exact")

    pct = px.pct_change().replace([pd.NA, float("inf"), float("-inf")], 0.0).fillna(0.0)
    return PnLSeriesResult(values=contract_size * pct, conversion_mode="pct_notional_proxy")
