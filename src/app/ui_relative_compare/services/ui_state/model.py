from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class UIState:
    symbol_1: str = "EURUSD"
    symbol_2: str = "AUDUSD"
    timeframe: str = "M1"
    calc_bars: str = "1440"
    visible_bars: str = "120"
    refresh_ms: str = "250"
    aggregate_bars: str = "1"
    use_ratio_in_divergence: bool = False
    auto_volume: bool = True
    manual_lot_1: str = "0.10"
    manual_lot_2: str = "0.10"
    width_adjust_px: int = 0
    height_adjust_px: int = 0
    pair_gap_adjust_px: int = 0
    chart_split_y: int = 560
    candle_collapsed: bool = False
    line_collapsed: bool = False
    pair_1_up_color: str = "#34d399"
    pair_1_down_color: str = "#f87171"
    pair_2_up_color: str = "#60a5fa"
    pair_2_down_color: str = "#f59e0b"
    window_geometry: str = "1380x980"
    line_zoom: float = 1.0
