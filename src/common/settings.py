
# src/common/settings.py
# Reads environment variables into a typed settings object.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


@dataclass(slots=True)
class Settings:
    app_env: str
    account_ccy: str
    mt5_login: int
    mt5_password: str
    mt5_server: str
    mt5_terminal_path: str
    mt5_timeout_ms: int
    mt5_reconnect_sec: int
    mt5_portable: bool
    mt5_magic: int
    symbol_leg_1: str
    symbol_leg_2: str
    timeframe: str
    history_bars: int
    min_warmup_bars: int
    beta_window_bars: int
    spread_z_window_bars: int
    resid_z_window_bars: int
    corr_window_bars: int
    vol_window_bars: int
    min_abs_corr: float
    min_beta_abs: float
    max_beta_abs: float
    entry_z_spread: float
    entry_z_resid: float
    exit_z: float
    stop_z: float
    time_stop_bars: int
    cooldown_bars: int
    base_lot_eurusd: float
    risk_per_trade_usd: float
    max_gross_notional_usd: float
    commission_usd_per_million: float
    commission_eurusd_usd_per_lot_one_way: float
    commission_audusd_usd_per_lot_one_way: float
    eurusd_spread_pips_assumed: float
    audusd_spread_pips_assumed: float
    eurusd_spread_pips_max: float
    audusd_spread_pips_max: float
    slippage_pips_per_leg: float
    round_turn_multiplier: float
    include_swap: bool
    live_poll_ms: int
    max_tick_age_ms: int
    log_level: str
    log_dir: Path
    data_dir: Path


def load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        account_ccy=os.getenv("ACCOUNT_CCY", "USD"),
        mt5_login=_int("MT5_LOGIN", 0),
        mt5_password=os.getenv("MT5_PASSWORD", ""),
        mt5_server=os.getenv("MT5_SERVER", ""),
        mt5_terminal_path=os.getenv("MT5_TERMINAL_PATH", ""),
        mt5_timeout_ms=_int("MT5_TIMEOUT_MS", 10000),
        mt5_reconnect_sec=_int("MT5_RECONNECT_SEC", 5),
        mt5_portable=_bool("MT5_PORTABLE", False),
        mt5_magic=_int("MT5_MAGIC", 420001),
        symbol_leg_1=os.getenv("SYMBOL_LEG_1", "EURUSD"),
        symbol_leg_2=os.getenv("SYMBOL_LEG_2", "AUDUSD"),
        timeframe=os.getenv("TIMEFRAME", "M1"),
        history_bars=_int("HISTORY_BARS", 2880),
        min_warmup_bars=_int("MIN_WARMUP_BARS", 720),
        beta_window_bars=_int("BETA_WINDOW_BARS", 1440),
        spread_z_window_bars=_int("SPREAD_Z_WINDOW_BARS", 1440),
        resid_z_window_bars=_int("RESID_Z_WINDOW_BARS", 1440),
        corr_window_bars=_int("CORR_WINDOW_BARS", 1440),
        vol_window_bars=_int("VOL_WINDOW_BARS", 60),
        min_abs_corr=_float("MIN_ABS_CORR", 0.30),
        min_beta_abs=_float("MIN_BETA_ABS", 0.30),
        max_beta_abs=_float("MAX_BETA_ABS", 2.50),
        entry_z_spread=_float("ENTRY_Z_SPREAD", 2.00),
        entry_z_resid=_float("ENTRY_Z_RESID", 2.00),
        exit_z=_float("EXIT_Z", 0.50),
        stop_z=_float("STOP_Z", 3.50),
        time_stop_bars=_int("TIME_STOP_BARS", 30),
        cooldown_bars=_int("COOLDOWN_BARS", 5),
        base_lot_eurusd=_float("BASE_LOT_EURUSD", 0.10),
        risk_per_trade_usd=_float("RISK_PER_TRADE_USD", 20.0),
        max_gross_notional_usd=_float("MAX_GROSS_NOTIONAL_USD", 50000),
        commission_usd_per_million=_float("COMMISSION_USD_PER_MILLION", 20.0),
        commission_eurusd_usd_per_lot_one_way=_float("COMMISSION_EURUSD_USD_PER_LOT_ONE_WAY", 2.4),
        commission_audusd_usd_per_lot_one_way=_float("COMMISSION_AUDUSD_USD_PER_LOT_ONE_WAY", 1.5),
        eurusd_spread_pips_assumed=_float("EURUSD_SPREAD_PIPS_ASSUMED", 0.1),
        audusd_spread_pips_assumed=_float("AUDUSD_SPREAD_PIPS_ASSUMED", 0.3),
        eurusd_spread_pips_max=_float("EURUSD_SPREAD_PIPS_MAX", 1.0),
        audusd_spread_pips_max=_float("AUDUSD_SPREAD_PIPS_MAX", 1.2),
        slippage_pips_per_leg=_float("SLIPPAGE_PIPS_PER_LEG", 0.2),
        round_turn_multiplier=_float("ROUND_TURN_MULTIPLIER", 2.0),
        include_swap=_bool("INCLUDE_SWAP", False),
        live_poll_ms=_int("LIVE_POLL_MS", 250),
        max_tick_age_ms=_int("MAX_TICK_AGE_MS", 1500),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_dir=Path(os.getenv("LOG_DIR", "./logs")),
        data_dir=Path(os.getenv("DATA_DIR", "./data")),
    )
