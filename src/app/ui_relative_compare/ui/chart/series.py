from __future__ import annotations

import pandas as pd

from .layout import EPS


def estimate_pip_size(price_delta: pd.Series, scaled_delta: pd.Series, factor: float, default: float) -> float:
    candidates: list[float] = []
    for raw_delta, scaled in zip(price_delta.tolist(), scaled_delta.tolist()):
        raw_value = float(raw_delta)
        scaled_value = float(scaled)
        if abs(raw_value) <= EPS or abs(scaled_value) <= EPS:
            continue
        candidates.append(abs((raw_value * factor) / scaled_value))

    if not candidates:
        return default
    candidates.sort()
    return float(candidates[len(candidates) // 2])


def build_relative_line_series(bars: pd.DataFrame, ratio_1_to_2: float) -> tuple[pd.Series, pd.Series]:
    if bars.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    raw_delta_1 = (bars["close_1"] - bars["open_1"]).astype(float)
    raw_delta_2 = (bars["close_2"] - bars["open_2"]).astype(float)

    pip_1 = estimate_pip_size(raw_delta_1, bars["p1_close"].astype(float), factor=1.0, default=0.0001)
    pip_2 = estimate_pip_size(raw_delta_2, bars["p2_close"].astype(float), factor=max(float(ratio_1_to_2), EPS), default=0.0001)

    close_to_close_1 = bars["close_1"].astype(float).diff().fillna(0.0) / pip_1
    close_to_close_2 = bars["close_2"].astype(float).diff().fillna(0.0) / pip_2

    out_1 = [0.0]
    out_2 = [0.0]
    acc_1 = 0.0
    acc_2 = 0.0

    for i in range(1, len(bars)):
        move_1 = float(close_to_close_1.iloc[i])
        move_2 = float(close_to_close_2.iloc[i])
        if move_1 * move_2 > 0:
            common = min(abs(move_1), abs(move_2))
            direction = 1.0 if move_1 > 0 else -1.0
            move_1 -= direction * common
            move_2 -= direction * common
        acc_1 += move_1
        acc_2 += move_2
        out_1.append(acc_1)
        out_2.append(acc_2)

    return pd.Series(out_1, dtype=float), pd.Series(out_2, dtype=float)
