from __future__ import annotations

import pandas as pd

from .direction import side_relation_from_ratio
from .models import HedgeComputationResult
from .pnl import build_pnl_series_per_1lot
from .ratio import estimate_execution_ratio
from .spread import fit_spread_model


def analyze_pair_hedge(
    close_1: pd.Series,
    close_2: pd.Series,
    symbol_1: str,
    symbol_2: str,
    meta_1=None,
    meta_2=None,
) -> HedgeComputationResult:
    pnl_1 = build_pnl_series_per_1lot(close_1, symbol=symbol_1, meta=meta_1)
    pnl_2 = build_pnl_series_per_1lot(close_2, symbol=symbol_2, meta=meta_2)

    execution_ratio, correlation = estimate_execution_ratio(pnl_1.values, pnl_2.values)
    side_relation = side_relation_from_ratio(execution_ratio)
    spread = fit_spread_model(close_1, close_2, side_relation=side_relation)

    return HedgeComputationResult(
        window=int(min(len(close_1), len(close_2))),
        correlation=float(correlation),
        execution_ratio=float(execution_ratio),
        execution_ratio_abs=abs(float(execution_ratio)),
        side_relation=side_relation,
        spread=spread,
        conversion_mode_1=pnl_1.conversion_mode,
        conversion_mode_2=pnl_2.conversion_mode,
    )
