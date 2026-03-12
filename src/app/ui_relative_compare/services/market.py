
# src/app/ui_relative_compare/services/market.py
# Loads symbol history, computes relative metrics, divergence stats, and prepares render/trade state.
from __future__ import annotations

import math

import pandas as pd

from src.app.ui_relative_compare.constants import TIMEFRAME_MINUTES
from src.app.ui_relative_compare.models import DivergenceStats, RelativeMetrics, RenderSnapshot, TradePlan
from src.broker.mt5_client import MT5Client, SymbolMeta
from src.common.settings import Settings


MIN_ORDER_LOTS = 0.01


def pip_size_from_digits(digits: int) -> float:
    return 0.01 if digits in (2, 3) else 0.0001


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

    frame_1 = frame_1.rename(
        columns={
            "open": "open_1",
            "high": "high_1",
            "low": "low_1",
            "close": "close_1",
            "tick_volume": "tick_volume_1",
        }
    )
    frame_2 = frame_2.rename(
        columns={
            "open": "open_2",
            "high": "high_2",
            "low": "low_2",
            "close": "close_2",
            "tick_volume": "tick_volume_2",
        }
    )

    keep_1 = ["time", "open_1", "high_1", "low_1", "close_1", "tick_volume_1"]
    keep_2 = ["time", "open_2", "high_2", "low_2", "close_2", "tick_volume_2"]

    merged = pd.merge(frame_1[keep_1], frame_2[keep_2], on="time", how="inner")
    if merged.empty:
        raise RuntimeError("Не удалось выровнять историю двух символов по времени")

    return merged.reset_index(drop=True), meta_1, meta_2


def calculate_relative_metrics(
    frame: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    timeframe: str,
) -> RelativeMetrics:
    minutes = TIMEFRAME_MINUTES[timeframe]
    pip_1 = pip_size_from_digits(digits_1)
    pip_2 = pip_size_from_digits(digits_2)

    range_1_pips = (frame["high_1"] - frame["low_1"]) / pip_1
    range_2_pips = (frame["high_2"] - frame["low_2"]) / pip_2

    ppm_1 = float((range_1_pips / minutes).mean())
    ppm_2 = float((range_2_pips / minutes).mean())

    if ppm_1 <= 0 or ppm_2 <= 0:
        raise RuntimeError("Одна из пар дала нулевую среднюю волатильность")

    return RelativeMetrics(
        ppm_1=ppm_1,
        ppm_2=ppm_2,
        ratio_1_to_2=ppm_1 / ppm_2,
        ratio_2_to_1=ppm_2 / ppm_1,
    )


def build_relative_bars(
    frame: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    ratio_1_to_2: float,
) -> pd.DataFrame:
    pip_1 = pip_size_from_digits(digits_1)
    pip_2 = pip_size_from_digits(digits_2)

    out = frame.copy()

    out["p1_high"] = (out["high_1"] - out["open_1"]) / pip_1
    out["p1_low"] = (out["low_1"] - out["open_1"]) / pip_1
    out["p1_close"] = (out["close_1"] - out["open_1"]) / pip_1

    # Вторая пара не зеркалится, а только масштабируется коэффициентом 1/2.
    out["p2_high"] = ((out["high_2"] - out["open_2"]) / pip_2) * ratio_1_to_2
    out["p2_low"] = ((out["low_2"] - out["open_2"]) / pip_2) * ratio_1_to_2
    out["p2_close"] = ((out["close_2"] - out["open_2"]) / pip_2) * ratio_1_to_2

    out["p1_body_abs"] = out["p1_close"].abs()
    out["p2_body_abs"] = out["p2_close"].abs()

    return out[
        [
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
    ].reset_index(drop=True)


def calculate_divergence_stats(
    frame: pd.DataFrame,
    digits_1: int,
    digits_2: int,
    ratio_1_to_2: float,
    use_ratio_in_divergence: bool,
    bid_1: float | None = None,
    bid_2: float | None = None,
) -> DivergenceStats:
    pip_1 = pip_size_from_digits(digits_1)
    pip_2 = pip_size_from_digits(digits_2)
    factor = ratio_1_to_2 if use_ratio_in_divergence else 1.0

    diff_series = (
        ((frame["close_1"] - frame["open_1"]) / pip_1)
        - (((frame["close_2"] - frame["open_2"]) / pip_2) * factor)
    )

    total_diff_pips = float(diff_series.sum())
    current_bar_diff_pips = float(diff_series.iloc[-1])

    live_diff_pips = current_bar_diff_pips
    if bid_1 is not None and bid_2 is not None:
        last = frame.iloc[-1]
        live_diff_pips = float(
            ((float(bid_1) - float(last["open_1"])) / pip_1)
            - ((((float(bid_2) - float(last["open_2"])) / pip_2) * factor))
        )

    return DivergenceStats(
        total_diff_pips=total_diff_pips,
        current_bar_diff_pips=current_bar_diff_pips,
        live_diff_pips=live_diff_pips,
        uses_ratio=use_ratio_in_divergence,
    )


def normalize_lot(volume: float, meta: SymbolMeta) -> float:
    step = meta.volume_step or MIN_ORDER_LOTS
    minimum = meta.volume_min or MIN_ORDER_LOTS
    scaled = max(volume, minimum)
    normalized = math.floor((scaled + 1e-12) / step) * step
    digits = max(0, len(str(step).split(".")[-1].rstrip("0"))) if "." in str(step) else 0
    return round(max(normalized, minimum), digits)


def build_trade_plan(
    bars: pd.DataFrame,
    symbol_1: str,
    symbol_2: str,
    meta_1: SymbolMeta,
    meta_2: SymbolMeta,
    cfg: Settings,
    ratio_1_to_2: float,
) -> TradePlan:
    row = bars.iloc[-1]

    move_1 = abs(float(row["p1_close"]))
    move_2 = abs(float(row["p2_close"]))

    base_lot_1 = normalize_lot(cfg.base_lot_eurusd, meta_1)
    base_lot_2 = normalize_lot(cfg.base_lot_eurusd * ratio_1_to_2, meta_2)

    if move_1 >= move_2:
        sell_symbol = symbol_1
        buy_symbol = symbol_2
        sell_lots = base_lot_1
        buy_lots = base_lot_2
        leader_symbol = symbol_1
        follower_symbol = symbol_2
        leader_move = move_1
        follower_move = move_2
    else:
        sell_symbol = symbol_2
        buy_symbol = symbol_1
        sell_lots = base_lot_2
        buy_lots = base_lot_1
        leader_symbol = symbol_2
        follower_symbol = symbol_1
        leader_move = move_2
        follower_move = move_1

    return TradePlan(
        sell_symbol=sell_symbol,
        buy_symbol=buy_symbol,
        sell_lots=sell_lots,
        buy_lots=buy_lots,
        leader_symbol=leader_symbol,
        follower_symbol=follower_symbol,
        leader_move=leader_move,
        follower_move=follower_move,
        button_text=f"Открыть SELL {sell_symbol} / BUY {buy_symbol}",
    )


def build_render_snapshot(
    client: MT5Client,
    cfg: Settings,
    symbol_1: str,
    symbol_2: str,
    timeframe: str,
    bars_count: int,
    ratio_1_to_2: float,
    use_ratio_in_divergence: bool,
) -> RenderSnapshot:
    frame, meta_1, meta_2 = load_two_symbols(client, symbol_1, symbol_2, timeframe, bars_count)
    metrics = calculate_relative_metrics(frame, meta_1.digits, meta_2.digits, timeframe)
    bars = build_relative_bars(frame, meta_1.digits, meta_2.digits, ratio_1_to_2)

    tick_1 = client.tick(symbol_1)
    tick_2 = client.tick(symbol_2)

    divergence_stats = calculate_divergence_stats(
        frame=frame,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
        ratio_1_to_2=ratio_1_to_2,
        use_ratio_in_divergence=use_ratio_in_divergence,
        bid_1=float(tick_1["bid"]),
        bid_2=float(tick_2["bid"]),
    )

    trade_plan = build_trade_plan(bars, symbol_1, symbol_2, meta_1, meta_2, cfg, ratio_1_to_2)
    return RenderSnapshot(
        bars=bars,
        metrics=metrics,
        divergence_stats=divergence_stats,
        trade_plan=trade_plan,
        digits_1=meta_1.digits,
        digits_2=meta_2.digits,
    )
