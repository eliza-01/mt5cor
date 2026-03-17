from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.services.market.transform import transform_price_delta_to_pips


def build_relative_line_series(
    bars: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    ratio_1_to_2: float,
    invert_second: bool,
    mutual_exclusion_enabled: bool,
) -> tuple[pd.Series, pd.Series]:
    if bars.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    close_to_close_1 = transform_price_delta_to_pips(
        bars["close_1"].astype(float).diff().fillna(0.0),
        digits_1,
    )
    close_to_close_2 = transform_price_delta_to_pips(
        bars["close_2"].astype(float).diff().fillna(0.0),
        digits_2,
        ratio_1_to_2,
        invert_second,
    )

    out_1 = [0.0]
    out_2 = [0.0]
    acc_1 = 0.0
    acc_2 = 0.0

    for i in range(1, len(bars)):
        move_1 = float(close_to_close_1.iloc[i])
        move_2 = float(close_to_close_2.iloc[i])

        if mutual_exclusion_enabled and move_1 * move_2 > 0:
            common = min(abs(move_1), abs(move_2))
            direction = 1.0 if move_1 > 0 else -1.0
            move_1 -= direction * common
            move_2 -= direction * common

        acc_1 += move_1
        acc_2 += move_2
        out_1.append(acc_1)
        out_2.append(acc_2)

    return pd.Series(out_1, dtype=float), pd.Series(out_2, dtype=float)
