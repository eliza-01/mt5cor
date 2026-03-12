# src/strategy/decision.py
# Applies entry filters and converts signal sign into leg directions.
from __future__ import annotations

import pandas as pd

from src.common.settings import Settings


def entry_side(row: pd.Series, cfg: Settings) -> int:
    if abs(row["corr"]) < cfg.min_abs_corr:
        return 0
    if not (cfg.min_beta_abs <= abs(row["beta"]) <= cfg.max_beta_abs):
        return 0
    if abs(row["spread_z"]) < cfg.entry_z_spread:
        return 0
    if abs(row["resid_z"]) < cfg.entry_z_resid:
        return 0
    if pd.isna(row["combo_z"]):
        return 0
    return -1 if row["combo_z"] > 0 else 1


def exit_hit(row: pd.Series, cfg: Settings) -> bool:
    return abs(row["combo_z"]) <= cfg.exit_z


def stop_hit(row: pd.Series, side: int, cfg: Settings) -> bool:
    if pd.isna(row["combo_z"]):
        return False
    if side == 1 and row["combo_z"] <= -cfg.stop_z:
        return True
    if side == -1 and row["combo_z"] >= cfg.stop_z:
        return True
    return False
