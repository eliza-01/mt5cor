from __future__ import annotations

import pandas as pd

from .common import pip_size_from_digits


def second_pair_direction(invert_second: bool) -> float:
    return -1.0 if invert_second else 1.0


def transform_price_delta_to_pips(
    price_delta: pd.Series | float,
    digits: int,
    ratio: float = 1.0,
    invert: bool = False,
):
    return (price_delta / pip_size_from_digits(digits)) * float(ratio) * second_pair_direction(invert)


def build_relative_bars(
    frame: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    ratio_1_to_2: float,
    invert_second: bool = False,
) -> pd.DataFrame:
    out = frame.copy()

    out["p1_high"] = transform_price_delta_to_pips(
        out["high_1"] - out["open_1"],
        digits_1,
    )
    out["p1_low"] = transform_price_delta_to_pips(
        out["low_1"] - out["open_1"],
        digits_1,
    )
    out["p1_close"] = transform_price_delta_to_pips(
        out["close_1"] - out["open_1"],
        digits_1,
    )

    out["p2_high"] = transform_price_delta_to_pips(
        out["high_2"] - out["open_2"],
        digits_2,
        ratio_1_to_2,
        invert_second,
    )
    out["p2_low"] = transform_price_delta_to_pips(
        out["low_2"] - out["open_2"],
        digits_2,
        ratio_1_to_2,
        invert_second,
    )
    out["p2_close"] = transform_price_delta_to_pips(
        out["close_2"] - out["open_2"],
        digits_2,
        ratio_1_to_2,
        invert_second,
    )

    out["p1_body_abs"] = out["p1_close"].abs()
    out["p2_body_abs"] = out["p2_close"].abs()

    base_columns = [
        "time",
        "open_1",
        "close_1",
        "open_2",
        "close_2",
        "p1_high",
        "p1_low",
        "p1_close",
        "p2_high",
        "p2_low",
        "p2_close",
        "p1_body_abs",
        "p2_body_abs",
    ]
    if "agg_progress" in out.columns:
        base_columns.append("agg_progress")

    return out[base_columns].reset_index(drop=True)