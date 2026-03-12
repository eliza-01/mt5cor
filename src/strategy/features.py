# src/strategy/features.py
# Computes rolling beta, spread, residual, and z-scores.
from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.settings import Settings


EPS = 1e-12


def _rolling_z(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window).mean()
    std = series.rolling(window).std(ddof=0).replace(0, np.nan)
    return (series - mean) / std


def _rolling_beta(y: pd.Series, x: pd.Series, window: int) -> pd.Series:
    cov = y.rolling(window).cov(x)
    var = x.rolling(window).var().replace(0, np.nan)
    return cov / var


def build_feature_frame(frame: pd.DataFrame, cfg: Settings) -> pd.DataFrame:
    out = frame.copy()
    out["log_1"] = np.log(out["close_1"].clip(lower=EPS))
    out["log_2"] = np.log(out["close_2"].clip(lower=EPS))
    out["ret_1"] = out["log_1"].diff()
    out["ret_2"] = out["log_2"].diff()
    out["beta"] = _rolling_beta(out["ret_1"], out["ret_2"], cfg.beta_window_bars)
    x_mean = out["ret_2"].rolling(cfg.beta_window_bars).mean()
    y_mean = out["ret_1"].rolling(cfg.beta_window_bars).mean()
    out["alpha"] = y_mean - out["beta"] * x_mean
    out["corr"] = out["ret_1"].rolling(cfg.corr_window_bars).corr(out["ret_2"])
    out["spread_raw"] = out["log_1"] - out["beta"] * out["log_2"]
    out["spread_z"] = _rolling_z(out["spread_raw"], cfg.spread_z_window_bars)
    out["resid_raw"] = out["ret_1"] - (out["alpha"] + out["beta"] * out["ret_2"])
    out["resid_z"] = _rolling_z(out["resid_raw"], cfg.resid_z_window_bars)
    same_sign = np.sign(out["spread_z"]) == np.sign(out["resid_z"])
    out["combo_z"] = np.where(same_sign, (out["spread_z"] + out["resid_z"]) / 2.0, np.nan)
    out["abs_combo_z"] = out["combo_z"].abs()
    out["vol_1"] = out["ret_1"].rolling(cfg.vol_window_bars).std(ddof=0)
    out["vol_2"] = out["ret_2"].rolling(cfg.vol_window_bars).std(ddof=0)
    return out.dropna().reset_index(drop=True)
