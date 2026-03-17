from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class UIState:
    symbol_1: str = "EURUSD"
    symbol_2: str = "USDCHF"
    timeframe: str = "M1"
    visible_bars: str = "1200"
    refresh_ms: str = "250"
    aggregate_bars: str = "1"
    base_trading_lot: str = "0.10"
    cost_coeff_1: str = "1.00"
    cost_coeff_2: str = "1.00"
    cost_coeff_1_enabled: bool = True
    cost_coeff_2_enabled: bool = True
    mutual_exclusion_enabled: bool = True
    apply_long_ratio: bool = False
    apply_short_ratio: bool = False
    apply_common_ratio: bool = True
    width_adjust_px: int = 0
    height_adjust_px: int = 0
    pair_gap_adjust_px: int = 0
    chart_split_y: int = 560
    sizing_collapsed: bool = True
    candle_collapsed: bool = False
    line_collapsed: bool = False
    pair_1_up_color: str = "#34d399"
    pair_1_down_color: str = "#f87171"
    pair_2_up_color: str = "#60a5fa"
    pair_2_down_color: str = "#f59e0b"
    window_geometry: str = "1380x980"
    line_zoom: float = 1.0
