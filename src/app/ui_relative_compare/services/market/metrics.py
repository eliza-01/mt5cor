from __future__ import annotations

import pandas as pd

from src.app.ui_relative_compare.constants import TIMEFRAME_MINUTES
from src.app.ui_relative_compare.domain import RelativeMetrics
from .common import pip_size_from_digits


def calculate_relative_metrics(frame: pd.DataFrame, digits_1: int, digits_2: int, timeframe: str) -> RelativeMetrics:
    minutes = TIMEFRAME_MINUTES[timeframe]
    pip_1 = pip_size_from_digits(digits_1)
    pip_2 = pip_size_from_digits(digits_2)

    range_1_pips = (frame["high_1"] - frame["low_1"]) / pip_1
    range_2_pips = (frame["high_2"] - frame["low_2"]) / pip_2

    ppm_1 = float((range_1_pips / minutes).mean())
    ppm_2 = float((range_2_pips / minutes).mean())

    if ppm_1 <= 0 or ppm_2 <= 0:
        raise RuntimeError("Одна из пар дала нулевую среднюю волатильность")

    return RelativeMetrics(ppm_1=ppm_1, ppm_2=ppm_2, ratio_1_to_2=ppm_1 / ppm_2, ratio_2_to_1=ppm_2 / ppm_1)
