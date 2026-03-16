from __future__ import annotations

import pandas as pd

from .common import pip_size_from_digits


def build_relative_bars(frame: pd.DataFrame, digits_1: int, digits_2: int, ratio_1_to_2: float) -> pd.DataFrame:
    pip_1 = pip_size_from_digits(digits_1)
    pip_2 = pip_size_from_digits(digits_2)

    out = frame.copy()
    out["p1_high"] = (out["high_1"] - out["open_1"]) / pip_1
    out["p1_low"] = (out["low_1"] - out["open_1"]) / pip_1
    out["p1_close"] = (out["close_1"] - out["open_1"]) / pip_1
    out["p2_high"] = ((out["high_2"] - out["open_2"]) / pip_2) * ratio_1_to_2
    out["p2_low"] = ((out["low_2"] - out["open_2"]) / pip_2) * ratio_1_to_2
    out["p2_close"] = ((out["close_2"] - out["open_2"]) / pip_2) * ratio_1_to_2
    out["p1_body_abs"] = out["p1_close"].abs()
    out["p2_body_abs"] = out["p2_close"].abs()

    return out[["time", "open_1", "close_1", "open_2", "close_2", "p1_high", "p1_low", "p1_close", "p2_high", "p2_low", "p2_close", "p1_body_abs", "p2_body_abs"]].reset_index(drop=True)
