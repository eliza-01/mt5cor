from __future__ import annotations

import math

import MetaTrader5 as mt5

MIN_ORDER_LOTS = 0.01


def normalize_volume(volume: float, symbol: str) -> float:
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"Не удалось получить symbol_info для {symbol}")

    step = float(getattr(info, "volume_step", 0.0) or MIN_ORDER_LOTS)
    minimum = float(getattr(info, "volume_min", 0.0) or MIN_ORDER_LOTS)
    maximum = float(getattr(info, "volume_max", 0.0) or 0.0)

    raw = float(volume)
    if raw <= 0:
        raise RuntimeError(f"Объем для {symbol} должен быть больше 0")

    clamped = max(raw, minimum)
    if maximum > 0:
        clamped = min(clamped, maximum)

    normalized = math.floor((clamped + 1e-12) / step) * step
    digits = max(0, len(str(step).split(".")[-1].rstrip("0"))) if "." in str(step) else 0
    return round(max(normalized, minimum), digits)
