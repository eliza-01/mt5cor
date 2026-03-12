
# src/app/ui_relative_compare/constants.py
# Shared constants for the relative compare package.
from __future__ import annotations

TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "H1": 60,
}

COMMON_SYMBOLS = [
    "EURUSD",
    "AUDUSD",
    "GBPUSD",
    "NZDUSD",
    "USDJPY",
    "USDCAD",
    "USDCHF",
    "EURAUD",
    "EURAUD.",
    "EURUSD.",
    "AUDUSD.",
]

CHART_BG = "#111111"
CHART_GRID = "#2a2a2a"
CHART_AXIS = "#8a8a8a"
CHART_TEXT = "#d4d4d4"
PAIR_1_UP = "#34d399"
PAIR_1_DOWN = "#f87171"
PAIR_2_UP = "#60a5fa"
PAIR_2_DOWN = "#f59e0b"
