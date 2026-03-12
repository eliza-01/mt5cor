# patch.py
# Updates src.app.ui_relative_compare, adds close-by-pair with PnL, divergence mode checkbox,
# and appends commission env defaults for EURUSD/AUDUSD.
from __future__ import annotations

from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent


FILES: dict[str, str] = {
    "src/__init__.py": """
# src/__init__.py
# Package root.
""",
    "src/app/__init__.py": """
# src/app/__init__.py
# App entrypoints.
""",
    "src/common/settings.py": """
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
""",
    "src/strategy/costs.py": """
# src/strategy/costs.py
# Estimates round-turn trading costs for the two FX legs.
from __future__ import annotations

from dataclasses import dataclass

from src.common.settings import Settings


def pip_size(digits: int) -> float:
    return 0.01 if digits in {2, 3} else 0.0001


def pip_value_usd(contract_size: float, digits: int, lots: float) -> float:
    return contract_size * pip_size(digits) * lots


@dataclass(slots=True)
class CostBreakdown:
    lots_1: float
    lots_2: float
    spread_usd: float
    commission_usd: float
    slippage_usd: float
    total_usd: float


def hedge_lots(base_lot_1: float, beta: float, px_1: float, px_2: float) -> float:
    ratio = abs(beta) * (px_1 / px_2)
    return max(base_lot_1 * ratio, 0.0)


def _symbol_key(symbol: str) -> str:
    letters = "".join(ch for ch in symbol.upper() if "A" <= ch <= "Z")
    return letters[:6]


def commission_usd_per_lot_one_way(symbol: str, cfg: Settings) -> float | None:
    key = _symbol_key(symbol)
    if key == "EURUSD":
        return cfg.commission_eurusd_usd_per_lot_one_way
    if key == "AUDUSD":
        return cfg.commission_audusd_usd_per_lot_one_way
    return None


def estimate_round_turn_cost(
    cfg: Settings,
    symbol_1: str,
    symbol_2: str,
    digits_1: int,
    digits_2: int,
    contract_size_1: float,
    contract_size_2: float,
    px_1: float,
    px_2: float,
    beta: float,
    spread_pips_1: float,
    spread_pips_2: float,
) -> CostBreakdown:
    lots_1 = cfg.base_lot_eurusd
    lots_2 = hedge_lots(lots_1, beta, px_1, px_2)

    spread_usd = (
        pip_value_usd(contract_size_1, digits_1, lots_1) * spread_pips_1
        + pip_value_usd(contract_size_2, digits_2, lots_2) * spread_pips_2
    ) * cfg.round_turn_multiplier

    rate_1 = commission_usd_per_lot_one_way(symbol_1, cfg)
    rate_2 = commission_usd_per_lot_one_way(symbol_2, cfg)

    if rate_1 is not None and rate_2 is not None:
        commission_usd = (rate_1 * lots_1 + rate_2 * lots_2) * cfg.round_turn_multiplier
    else:
        notional_usd = px_1 * contract_size_1 * lots_1 + px_2 * contract_size_2 * lots_2
        commission_usd = cfg.commission_usd_per_million * (notional_usd / 1_000_000.0) * cfg.round_turn_multiplier

    slippage_usd = (
        pip_value_usd(contract_size_1, digits_1, lots_1) * cfg.slippage_pips_per_leg
        + pip_value_usd(contract_size_2, digits_2, lots_2) * cfg.slippage_pips_per_leg
    ) * cfg.round_turn_multiplier

    total_usd = spread_usd + commission_usd + slippage_usd
    return CostBreakdown(lots_1, lots_2, spread_usd, commission_usd, slippage_usd, total_usd)
""",
    "src/strategy/simulator.py": """
# src/strategy/simulator.py
# Runs a simple event-study and estimates current live edge.
from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from src.broker.mt5_client import SymbolMeta
from src.common.settings import Settings
from src.strategy.costs import estimate_round_turn_cost
from src.strategy.decision import entry_side, exit_hit, stop_hit


def _gross_pnl_usd(
    side: int,
    entry_1: float,
    entry_2: float,
    exit_1: float,
    exit_2: float,
    lots_1: float,
    lots_2: float,
    cs_1: float,
    cs_2: float,
) -> float:
    pnl_1 = side * (exit_1 - entry_1) * cs_1 * lots_1
    pnl_2 = -side * (exit_2 - entry_2) * cs_2 * lots_2
    return pnl_1 + pnl_2


def simulate_trades(frame: pd.DataFrame, cfg: Settings, meta_1: SymbolMeta, meta_2: SymbolMeta) -> pd.DataFrame:
    rows: list[dict] = []
    i = 0
    limit = len(frame) - 1

    while i < limit:
        row = frame.iloc[i]
        side = entry_side(row, cfg)
        if not side:
            i += 1
            continue

        spread_1 = cfg.eurusd_spread_pips_assumed
        spread_2 = cfg.audusd_spread_pips_assumed

        costs = estimate_round_turn_cost(
            cfg=cfg,
            symbol_1=meta_1.symbol,
            symbol_2=meta_2.symbol,
            digits_1=meta_1.digits,
            digits_2=meta_2.digits,
            contract_size_1=meta_1.contract_size,
            contract_size_2=meta_2.contract_size,
            px_1=float(row["close_1"]),
            px_2=float(row["close_2"]),
            beta=float(row["beta"]),
            spread_pips_1=spread_1,
            spread_pips_2=spread_2,
        )

        entry_ix = i
        exit_ix = min(i + cfg.time_stop_bars, limit)
        reason = "time"

        for j in range(i + 1, min(i + cfg.time_stop_bars, limit) + 1):
            probe = frame.iloc[j]
            if exit_hit(probe, cfg):
                exit_ix = j
                reason = "exit"
                break
            if stop_hit(probe, side, cfg):
                exit_ix = j
                reason = "stop"
                break

        exit_row = frame.iloc[exit_ix]

        gross = _gross_pnl_usd(
            side=side,
            entry_1=float(row["close_1"]),
            entry_2=float(row["close_2"]),
            exit_1=float(exit_row["close_1"]),
            exit_2=float(exit_row["close_2"]),
            lots_1=costs.lots_1,
            lots_2=costs.lots_2,
            cs_1=meta_1.contract_size,
            cs_2=meta_2.contract_size,
        )

        rows.append(
            {
                "entry_time": row["time"],
                "exit_time": exit_row["time"],
                "hold_bars": int(exit_ix - entry_ix),
                "reason": reason,
                "side": int(side),
                "beta": float(row["beta"]),
                "corr": float(row["corr"]),
                "spread_z": float(row["spread_z"]),
                "resid_z": float(row["resid_z"]),
                "combo_z": float(row["combo_z"]),
                "gross_pnl_usd": float(gross),
                **{f"cost_{k}": v for k, v in asdict(costs).items()},
                "net_pnl_usd": float(gross - costs.total_usd),
            }
        )

        i = exit_ix + cfg.cooldown_bars

    return pd.DataFrame(rows)


def summarize_trades(trades: pd.DataFrame) -> dict[str, float]:
    if trades.empty:
        return {
            "trades": 0.0,
            "win_rate": 0.0,
            "gross_pnl_usd": 0.0,
            "net_pnl_usd": 0.0,
        }

    return {
        "trades": float(len(trades)),
        "win_rate": float((trades["net_pnl_usd"] > 0).mean()),
        "gross_pnl_usd": float(trades["gross_pnl_usd"].sum()),
        "net_pnl_usd": float(trades["net_pnl_usd"].sum()),
        "avg_net_pnl_usd": float(trades["net_pnl_usd"].mean()),
        "median_hold_bars": float(trades["hold_bars"].median()),
    }


def estimate_live_edge(frame: pd.DataFrame, trades: pd.DataFrame, cfg: Settings) -> dict[str, float | int | str] | None:
    if frame.empty:
        return None

    row = frame.iloc[-1]
    side = entry_side(row, cfg)

    combo_z = float(row["combo_z"]) if pd.notna(row["combo_z"]) else float("nan")
    spread_z = float(row["spread_z"]) if pd.notna(row["spread_z"]) else float("nan")
    resid_z = float(row["resid_z"]) if pd.notna(row["resid_z"]) else float("nan")
    corr = float(row["corr"]) if pd.notna(row["corr"]) else float("nan")
    beta = float(row["beta"]) if pd.notna(row["beta"]) else float("nan")

    if not side:
        return {
            "status": "no_entry",
            "combo_z": combo_z,
            "spread_z": spread_z,
            "resid_z": resid_z,
            "corr": corr,
            "beta": beta,
        }

    if trades.empty:
        return {
            "status": "entry_but_no_history",
            "side": int(side),
            "combo_z": combo_z,
            "spread_z": spread_z,
            "resid_z": resid_z,
            "corr": corr,
            "beta": beta,
        }

    sample = trades[trades["side"] == side].copy()
    sample["distance"] = (sample["combo_z"] - combo_z).abs()
    sample = sample.sort_values("distance").head(20)

    if sample.empty:
        return {
            "status": "entry_but_no_matches",
            "side": int(side),
            "combo_z": combo_z,
            "spread_z": spread_z,
            "resid_z": resid_z,
            "corr": corr,
            "beta": beta,
        }

    mean_net = float(sample["net_pnl_usd"].mean())

    return {
        "status": "entry" if mean_net > 0 else "skip",
        "side": int(side),
        "combo_z": combo_z,
        "spread_z": spread_z,
        "resid_z": resid_z,
        "corr": corr,
        "beta": beta,
        "sample_n": int(len(sample)),
        "hist_mean_net_pnl_usd": mean_net,
        "hist_median_net_pnl_usd": float(sample["net_pnl_usd"].median()),
        "hist_win_rate": float((sample["net_pnl_usd"] > 0).mean()),
    }
""",
    "src/app/ui_relative_compare/__init__.py": """
# src/app/ui_relative_compare/__init__.py
# Package entry for the relative compare UI.
""",
    "src/app/ui_relative_compare/__main__.py": """
# src/app/ui_relative_compare/__main__.py
# Runs the standalone UI for relative comparison of two MT5 symbols.
from .ui.app import main


if __name__ == "__main__":
    main()
""",
    "src/app/ui_relative_compare/constants.py": """
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
""",
    "src/app/ui_relative_compare/models.py": """
# src/app/ui_relative_compare/models.py
# Dataclasses for metrics, render snapshot, divergence stats, and trade plan.
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class RelativeMetrics:
    ppm_1: float
    ppm_2: float
    ratio_1_to_2: float
    ratio_2_to_1: float


@dataclass(slots=True)
class DivergenceStats:
    total_diff_pips: float
    current_bar_diff_pips: float
    live_diff_pips: float
    uses_ratio: bool


@dataclass(slots=True)
class TradePlan:
    sell_symbol: str
    buy_symbol: str
    sell_lots: float
    buy_lots: float
    leader_symbol: str
    follower_symbol: str
    leader_move: float
    follower_move: float
    button_text: str


@dataclass(slots=True)
class RenderSnapshot:
    bars: pd.DataFrame
    metrics: RelativeMetrics
    divergence_stats: DivergenceStats
    trade_plan: TradePlan
    digits_1: int
    digits_2: int
""",
    "src/app/ui_relative_compare/services/__init__.py": """
# src/app/ui_relative_compare/services/__init__.py
# Service layer for relative compare.
""",
    "src/app/ui_relative_compare/services/market.py": """
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
""",
    "src/app/ui_relative_compare/services/trading.py": """
# src/app/ui_relative_compare/services/trading.py
# Sends opposite market orders for the current relative leader and follower,
# and closes all positions for the selected pair with PnL summary.
from __future__ import annotations

from dataclasses import dataclass

import MetaTrader5 as mt5

from src.app.ui_relative_compare.models import TradePlan
from src.broker.mt5_client import MT5Client
from src.common.settings import Settings
from src.strategy.costs import commission_usd_per_lot_one_way


CLIENT_DISABLES_AT = 10027


@dataclass(slots=True)
class OrderSendSummary:
    sell_retcode: int
    buy_retcode: int
    sell_order: int
    buy_order: int


@dataclass(slots=True)
class ClosePairSummary:
    closed_count: int
    gross_pnl_usd: float
    net_pnl_est_usd: float


def _terminal_flags() -> dict:
    info = mt5.terminal_info()
    if info is None:
        return {}
    try:
        return info._asdict()
    except Exception:
        return {}


def _ensure_python_trading_enabled() -> None:
    flags = _terminal_flags()

    if bool(flags.get("tradeapi_disabled", False)):
        raise RuntimeError(
            "В MT5 запрещена торговля через внешний Python API. "
            "Открой Tools -> Options -> Expert Advisors и отключи "
            "'Disable automatic trading via external Python API'. "
            "Также проверь, что кнопка Algo Trading включена."
        )

    if "trade_allowed" in flags and not bool(flags.get("trade_allowed")):
        raise RuntimeError(
            "В MT5 выключена автоматическая торговля. "
            "Включи кнопку Algo Trading в терминале."
        )


def _filling_candidates(symbol: str) -> list[int]:
    info = mt5.symbol_info(symbol)
    candidates: list[int] = []

    if info is not None:
        try:
            filling_mode = int(getattr(info, "filling_mode", 0) or 0)
        except Exception:
            filling_mode = 0

        if filling_mode & 1:
            candidates.append(mt5.ORDER_FILLING_FOK)
        if filling_mode & 2:
            candidates.append(mt5.ORDER_FILLING_IOC)

        trade_exemode = getattr(info, "trade_exemode", None)
        if trade_exemode != getattr(mt5, "SYMBOL_TRADE_EXECUTION_MARKET", None):
            candidates.append(mt5.ORDER_FILLING_RETURN)

    for value in (mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN):
        if value not in candidates:
            candidates.append(value)

    return candidates


def _build_market_request(
    symbol: str,
    volume: float,
    side: str,
    deviation: int,
    magic: int,
    comment: str,
    type_filling: int,
) -> dict:
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"Не удалось получить тик для {symbol}")

    order_type = mt5.ORDER_TYPE_SELL if side == "sell" else mt5.ORDER_TYPE_BUY
    price = float(tick.bid if side == "sell" else tick.ask)

    return {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "price": price,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }


def _send_market_with_fill_fallback(
    symbol: str,
    volume: float,
    side: str,
    deviation: int,
    magic: int,
    comment: str,
):
    last_result = None

    for filling in _filling_candidates(symbol):
        request = _build_market_request(
            symbol=symbol,
            volume=volume,
            side=side,
            deviation=deviation,
            magic=magic,
            comment=comment,
            type_filling=filling,
        )
        result = mt5.order_send(request)
        last_result = result

        if result is None:
            continue

        retcode = int(result.retcode)
        if retcode == mt5.TRADE_RETCODE_DONE:
            return result
        if retcode == CLIENT_DISABLES_AT:
            raise RuntimeError(
                "MT5 вернул retcode=10027: торговля из Python запрещена терминалом. "
                "Включи Algo Trading и отключи запрет на внешний Python API "
                "в Tools -> Options -> Expert Advisors."
            )

    if last_result is None:
        raise RuntimeError(f"order_send вернул None: {mt5.last_error()}")

    raise RuntimeError(
        f"{side.upper()} {symbol} не открыт: retcode={int(last_result.retcode)} "
        f"comment={str(getattr(last_result, 'comment', '') or '')}"
    )


def _build_close_request(position, deviation: int, magic: int, type_filling: int) -> dict:
    symbol = str(position.symbol)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"Не удалось получить тик для {symbol}")

    if int(position.type) == mt5.ORDER_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = float(tick.bid)
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = float(tick.ask)

    return {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(position.volume),
        "type": order_type,
        "position": int(position.ticket),
        "price": price,
        "deviation": deviation,
        "magic": magic,
        "comment": "relative_compare_close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }


def _close_position_with_fill_fallback(position, deviation: int, magic: int):
    last_result = None

    for filling in _filling_candidates(str(position.symbol)):
        request = _build_close_request(position, deviation=deviation, magic=magic, type_filling=filling)
        result = mt5.order_send(request)
        last_result = result

        if result is None:
            continue

        retcode = int(result.retcode)
        if retcode == mt5.TRADE_RETCODE_DONE:
            return result
        if retcode == CLIENT_DISABLES_AT:
            raise RuntimeError(
                "MT5 вернул retcode=10027: торговля из Python запрещена терминалом. "
                "Включи Algo Trading и отключи запрет на внешний Python API "
                "в Tools -> Options -> Expert Advisors."
            )

    if last_result is None:
        raise RuntimeError(f"close order_send вернул None: {mt5.last_error()}")

    raise RuntimeError(
        f"CLOSE {position.symbol} ticket={int(position.ticket)} не выполнен: "
        f"retcode={int(last_result.retcode)} comment={str(getattr(last_result, 'comment', '') or '')}"
    )


def _symbol_positions(symbol: str) -> list:
    items = mt5.positions_get(symbol=symbol)
    return list(items or [])


def _estimated_round_turn_commission_usd(symbol: str, volume: float, cfg: Settings) -> float:
    rate = commission_usd_per_lot_one_way(symbol, cfg)
    if rate is None:
        return 0.0
    return float(rate) * float(volume) * cfg.round_turn_multiplier


def open_opposite_positions(
    client: MT5Client,
    cfg: Settings,
    plan: TradePlan,
    deviation: int = 20,
) -> OrderSendSummary:
    _ensure_python_trading_enabled()

    client.ensure_symbol(plan.sell_symbol)
    client.ensure_symbol(plan.buy_symbol)

    sell_result = _send_market_with_fill_fallback(
        symbol=plan.sell_symbol,
        volume=plan.sell_lots,
        side="sell",
        deviation=deviation,
        magic=cfg.mt5_magic,
        comment="relative_compare_sell",
    )

    buy_result = _send_market_with_fill_fallback(
        symbol=plan.buy_symbol,
        volume=plan.buy_lots,
        side="buy",
        deviation=deviation,
        magic=cfg.mt5_magic,
        comment="relative_compare_buy",
    )

    return OrderSendSummary(
        sell_retcode=int(sell_result.retcode),
        buy_retcode=int(buy_result.retcode),
        sell_order=int(getattr(sell_result, "order", 0) or 0),
        buy_order=int(getattr(buy_result, "order", 0) or 0),
    )


def close_pair_positions(
    client: MT5Client,
    cfg: Settings,
    symbol_1: str,
    symbol_2: str,
    deviation: int = 20,
) -> ClosePairSummary:
    _ensure_python_trading_enabled()

    positions = [* _symbol_positions(symbol_1), * _symbol_positions(symbol_2)]
    if not positions:
        return ClosePairSummary(closed_count=0, gross_pnl_usd=0.0, net_pnl_est_usd=0.0)

    gross_pnl_usd = 0.0
    commission_est_usd = 0.0

    for position in positions:
        gross_pnl_usd += float(getattr(position, "profit", 0.0) or 0.0)
        gross_pnl_usd += float(getattr(position, "swap", 0.0) or 0.0)
        commission_est_usd += _estimated_round_turn_commission_usd(str(position.symbol), float(position.volume), cfg)

    errors: list[str] = []
    closed_count = 0

    for position in positions:
        try:
            client.ensure_symbol(str(position.symbol))
            _close_position_with_fill_fallback(position, deviation=deviation, magic=cfg.mt5_magic)
            closed_count += 1
        except Exception as exc:
            errors.append(str(exc))

    if errors:
        raise RuntimeError("\\n".join(errors))

    return ClosePairSummary(
        closed_count=closed_count,
        gross_pnl_usd=float(gross_pnl_usd),
        net_pnl_est_usd=float(gross_pnl_usd - commission_est_usd),
    )
""",
    "src/app/ui_relative_compare/ui/__init__.py": """
# src/app/ui_relative_compare/ui/__init__.py
# UI layer for relative compare.
""",
    "src/app/ui_relative_compare/ui/chart.py": """
# src/app/ui_relative_compare/ui/chart.py
# Draws two non-mirrored relative candle streams side by side on one canvas.
from __future__ import annotations

import tkinter as tk

import pandas as pd

from src.app.ui_relative_compare.constants import (
    CHART_AXIS,
    CHART_BG,
    CHART_GRID,
    CHART_TEXT,
    PAIR_1_DOWN,
    PAIR_1_UP,
    PAIR_2_DOWN,
    PAIR_2_UP,
)
from src.app.ui_relative_compare.models import DivergenceStats


class RelativeChart:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas

    def draw(
        self,
        bars: pd.DataFrame,
        symbol_1: str,
        symbol_2: str,
        ratio_1_to_2: float,
        width_adjust_px: int,
        height_adjust_px: int,
        divergence_stats: DivergenceStats,
    ) -> None:
        self.canvas.update_idletasks()
        width = max(self.canvas.winfo_width(), 400)
        height = max(self.canvas.winfo_height(), 300)

        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, width, height, fill=CHART_BG, outline=CHART_BG)

        center_y = height / 2
        left_pad = 60
        right_pad = 20
        top_pad = 88
        bottom_pad = 34

        max_abs = 1.0
        for col in ["p1_high", "p1_low", "p1_close", "p2_high", "p2_low", "p2_close"]:
            val = bars[col].abs().max()
            if pd.notna(val):
                max_abs = max(max_abs, float(val))

        usable_half = (height - top_pad - bottom_pad) / 2 - 10
        base_scale = usable_half / (max_abs * 1.15)
        scale = max(0.5, base_scale + height_adjust_px)

        self.canvas.create_line(left_pad, center_y, width - right_pad, center_y, fill=CHART_AXIS, width=1)
        self.canvas.create_text(12, center_y, anchor="w", text="OPEN", fill=CHART_AXIS, font=("Segoe UI", 9, "bold"))

        for level in [0.25, 0.5, 0.75, 1.0]:
            dy = max_abs * base_scale * level
            self.canvas.create_line(left_pad, center_y - dy, width - right_pad, center_y - dy, fill=CHART_GRID)
            self.canvas.create_line(left_pad, center_y + dy, width - right_pad, center_y + dy, fill=CHART_GRID)

        n = len(bars)
        step_x = max(10, (width - left_pad - right_pad) / max(n, 1))
        body_half = max(2.0, min(step_x * 0.42, step_x * 0.18 + width_adjust_px))
        wick_offset = max(body_half + 2.0, min(step_x * 0.46, body_half + 3.0))

        for i, row in bars.iterrows():
            x = left_pad + step_x * i + step_x / 2

            p1_high_y = center_y - float(row["p1_high"]) * scale
            p1_low_y = center_y - float(row["p1_low"]) * scale
            p1_close_y = center_y - float(row["p1_close"]) * scale

            p2_high_y = center_y - float(row["p2_high"]) * scale
            p2_low_y = center_y - float(row["p2_low"]) * scale
            p2_close_y = center_y - float(row["p2_close"]) * scale

            p1_color = PAIR_1_UP if float(row["close_1"]) >= float(row["open_1"]) else PAIR_1_DOWN
            p2_color = PAIR_2_UP if float(row["close_2"]) >= float(row["open_2"]) else PAIR_2_DOWN

            self.canvas.create_line(x - wick_offset, p1_high_y, x - wick_offset, p1_low_y, fill=p1_color, width=1)
            self.canvas.create_line(x + wick_offset, p2_high_y, x + wick_offset, p2_low_y, fill=p2_color, width=1)

            self._draw_body(x - wick_offset, center_y, p1_close_y, body_half, p1_color)
            self._draw_body(x + wick_offset, center_y, p2_close_y, body_half, p2_color)

        mode_text = "с коэф" if divergence_stats.uses_ratio else "реал"
        divergence_text = (
            f"Δ режим: {mode_text}\\n"
            f"Лента Δ: {divergence_stats.total_diff_pips:+.2f} п\\n"
            f"Текущая свеча Δ: {divergence_stats.current_bar_diff_pips:+.2f} п\\n"
            f"Live bid Δ: {divergence_stats.live_diff_pips:+.2f} п"
        )

        self.canvas.create_text(left_pad, 10, anchor="nw", fill=CHART_TEXT, font=("Segoe UI", 10, "bold"), text=symbol_1)
        self.canvas.create_text(width / 2, 10, anchor="n", fill=CHART_TEXT, font=("Segoe UI", 10), text="свечи рядом, без зеркала")
        self.canvas.create_text(width - right_pad, 10, anchor="ne", fill=CHART_TEXT, font=("Segoe UI", 10, "bold"), justify="right", text=divergence_text)

        self.canvas.create_text(
            width - right_pad,
            height - 10,
            anchor="se",
            fill=CHART_TEXT,
            font=("Segoe UI", 9),
            text=f"{symbol_2} | scale coef 1/2 = {ratio_1_to_2:.6f} | width={width_adjust_px:+d}px | height={height_adjust_px:+d}px",
        )

    def _draw_body(self, x: float, y_open: float, y_close: float, half_width: float, color: str) -> None:
        top = min(y_open, y_close)
        bottom = max(y_open, y_close)

        if abs(bottom - top) < 2:
            self.canvas.create_line(x - half_width, y_close, x + half_width, y_close, fill=color, width=3)
            return

        self.canvas.create_rectangle(
            x - half_width,
            top,
            x + half_width,
            bottom,
            outline=color,
            fill=color,
        )
""",
    "src/app/ui_relative_compare/ui/app.py": """
# src/app/ui_relative_compare/ui/app.py
# Tk application for non-mirrored relative candles, divergence mode checkbox,
# close-by-pair with PnL, and opposite-position opening.
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.app.ui_relative_compare.constants import COMMON_SYMBOLS, TIMEFRAME_MINUTES
from src.app.ui_relative_compare.models import RelativeMetrics, RenderSnapshot, TradePlan
from src.app.ui_relative_compare.services.market import (
    build_render_snapshot,
    calculate_relative_metrics,
    load_two_symbols,
)
from src.app.ui_relative_compare.services.trading import close_pair_positions, open_opposite_positions
from src.app.ui_relative_compare.ui.chart import RelativeChart
from src.broker.mt5_client import MT5Client
from src.common.settings import load_settings


class RelativeCompareUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MT5 Relative Compare")
        self.geometry("1360x900")
        self.minsize(1220, 800)

        self.base_cfg = load_settings()
        self.client: MT5Client | None = None
        self.connected = False
        self.live_job: str | None = None

        self.symbol_1_var = tk.StringVar(value="EURUSD")
        self.symbol_2_var = tk.StringVar(value="AUDUSD")
        self.timeframe_var = tk.StringVar(value="M1")
        self.calc_bars_var = tk.StringVar(value="240")
        self.visible_bars_var = tk.StringVar(value="40")
        self.refresh_ms_var = tk.StringVar(value="1000")
        self.use_ratio_in_divergence_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value="idle")
        self.account_var = tk.StringVar(value="-")
        self.ppm_1_var = tk.StringVar(value="-")
        self.ppm_2_var = tk.StringVar(value="-")
        self.ratio_1_to_2_var = tk.StringVar(value="-")
        self.ratio_2_to_1_var = tk.StringVar(value="-")
        self.last_bar_time_var = tk.StringVar(value="-")
        self.trade_hint_var = tk.StringVar(value="-")
        self.width_size_var = tk.StringVar(value="0px")
        self.height_size_var = tk.StringVar(value="0px")

        self.relative_metrics: RelativeMetrics | None = None
        self.current_trade_plan: TradePlan | None = None
        self.current_snapshot: RenderSnapshot | None = None
        self.width_adjust_px = 0
        self.height_adjust_px = 0

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        controls = ttk.LabelFrame(root, text="Параметры", padding=10)
        controls.pack(fill="x")

        ttk.Label(controls, text="Пара 1").grid(row=0, column=0, sticky="w")
        self.symbol_1_box = ttk.Combobox(controls, textvariable=self.symbol_1_var, values=COMMON_SYMBOLS, width=12)
        self.symbol_1_box.grid(row=0, column=1, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Пара 2").grid(row=0, column=2, sticky="w")
        self.symbol_2_box = ttk.Combobox(controls, textvariable=self.symbol_2_var, values=COMMON_SYMBOLS, width=12)
        self.symbol_2_box.grid(row=0, column=3, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Timeframe").grid(row=0, column=4, sticky="w")
        ttk.Combobox(
            controls,
            textvariable=self.timeframe_var,
            values=list(TIMEFRAME_MINUTES.keys()),
            state="readonly",
            width=8,
        ).grid(row=0, column=5, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Баров для расчёта").grid(row=0, column=6, sticky="w")
        ttk.Entry(controls, textvariable=self.calc_bars_var, width=8).grid(row=0, column=7, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Видимых свечей").grid(row=0, column=8, sticky="w")
        ttk.Entry(controls, textvariable=self.visible_bars_var, width=8).grid(row=0, column=9, padx=(6, 14), sticky="w")

        ttk.Label(controls, text="Refresh ms").grid(row=0, column=10, sticky="w")
        ttk.Entry(controls, textvariable=self.refresh_ms_var, width=8).grid(row=0, column=11, padx=(6, 14), sticky="w")

        ttk.Checkbutton(
            controls,
            text="Расхождение с коэф",
            variable=self.use_ratio_in_divergence_var,
            command=self.on_toggle_divergence_mode,
        ).grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="w")

        ttk.Button(controls, text="Подключить MT5", command=self.connect_mt5).grid(row=1, column=2, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Рассчитать коэффициент", command=self.calculate_ratio).grid(row=1, column=3, columnspan=2, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Старт", command=self.start_live).grid(row=1, column=5, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Стоп", command=self.stop_live).grid(row=1, column=6, pady=(10, 0), sticky="w")
        ttk.Button(controls, text="Разовый рендер", command=self.render_once).grid(row=1, column=7, pady=(10, 0), sticky="w")

        sizing = ttk.LabelFrame(root, text="Общий размер свечей", padding=10)
        sizing.pack(fill="x", pady=(10, 0))

        ttk.Label(sizing, text="Ширина").grid(row=0, column=0, sticky="w")
        ttk.Button(sizing, text="-1px", command=lambda: self.change_size("width", -1)).grid(row=0, column=1, padx=(6, 4), sticky="w")
        ttk.Button(sizing, text="+1px", command=lambda: self.change_size("width", 1)).grid(row=0, column=2, padx=(0, 10), sticky="w")
        ttk.Label(sizing, textvariable=self.width_size_var).grid(row=0, column=3, padx=(0, 18), sticky="w")

        ttk.Label(sizing, text="Высота").grid(row=0, column=4, sticky="w")
        ttk.Button(sizing, text="-1px", command=lambda: self.change_size("height", -1)).grid(row=0, column=5, padx=(6, 4), sticky="w")
        ttk.Button(sizing, text="+1px", command=lambda: self.change_size("height", 1)).grid(row=0, column=6, padx=(0, 10), sticky="w")
        ttk.Label(sizing, textvariable=self.height_size_var).grid(row=0, column=7, padx=(0, 18), sticky="w")

        ttk.Button(sizing, text="Сбросить", command=self.reset_size).grid(row=0, column=8, sticky="w")

        info = ttk.LabelFrame(root, text="Метрика относительности", padding=10)
        info.pack(fill="x", pady=(10, 0))

        self._kv(info, 0, 0, "Статус", self.status_var)
        self._kv(info, 0, 2, "Аккаунт", self.account_var)
        self._kv(info, 0, 4, "Последний бар", self.last_bar_time_var)

        self._kv(info, 1, 0, "Пара 1 ппм", self.ppm_1_var)
        self._kv(info, 1, 2, "Пара 2 ппм", self.ppm_2_var)
        self._kv(info, 1, 4, "Коэф 1/2", self.ratio_1_to_2_var)
        self._kv(info, 1, 6, "Коэф 2/1", self.ratio_2_to_1_var)

        trade = ttk.LabelFrame(root, text="Текущий opposite-план", padding=10)
        trade.pack(fill="x", pady=(10, 0))
        self._kv(trade, 0, 0, "Логика", self.trade_hint_var)
        self.trade_button = ttk.Button(trade, text="Открыть opposite позиции", command=self.open_current_positions)
        self.trade_button.grid(row=0, column=2, padx=(18, 8), sticky="w")
        self.close_button = ttk.Button(trade, text="Закрыть все по связке", command=self.close_current_pair_positions)
        self.close_button.grid(row=0, column=3, padx=(8, 0), sticky="w")

        hint = ttk.LabelFrame(root, text="Смысл", padding=10)
        hint.pack(fill="x", pady=(10, 0))
        ttk.Label(
            hint,
            text=(
                "Галочка 'Расхождение с коэф' переключает режим расчёта расхождения: "
                "без неё показываются реальные пункты, с ней — пункты с пересчётом по рассчитанному коэффициенту. "
                "В правом верхнем углу ленты показывается сумма по всей видимой ленте, "
                "отдельно текущая свеча и live-расхождение незакрытой свечи по bid. "
                "Кнопка close закрывает все позиции по двум выбранным символам и показывает pnl."
            ),
            wraplength=1280,
        ).pack(anchor="w")

        chart_wrap = ttk.LabelFrame(root, text="Сравнение свечей", padding=8)
        chart_wrap.pack(fill="both", expand=True, pady=(10, 0))

        self.canvas = tk.Canvas(chart_wrap, bg="#111111", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.chart = RelativeChart(self.canvas)

    def _kv(self, parent: ttk.Widget, row: int, col: int, key: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=key).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
        ttk.Label(parent, textvariable=var).grid(row=row, column=col + 1, sticky="w", padx=(0, 18), pady=4)

    def connect_mt5(self) -> None:
        try:
            if self.connected:
                self.status_var.set("connected")
                return

            self.client = MT5Client(self.base_cfg)
            self.client.connect()
            self.connected = True
            self.status_var.set("connected")
            self.account_var.set(f"{self.base_cfg.mt5_login} @ {self.base_cfg.mt5_server}")
        except Exception as exc:
            self.status_var.set("connect_error")
            messagebox.showerror("MT5", str(exc))

    def _ensure_connected(self) -> None:
        if not self.connected or self.client is None:
            self.connect_mt5()
        if not self.connected or self.client is None:
            raise RuntimeError("MT5 не подключен")

    def _read_inputs(self) -> tuple[str, str, str, int, int, int]:
        symbol_1 = self.symbol_1_var.get().strip()
        symbol_2 = self.symbol_2_var.get().strip()
        timeframe = self.timeframe_var.get().strip()

        if timeframe not in TIMEFRAME_MINUTES:
            raise RuntimeError("Неподдерживаемый timeframe")

        calc_bars = max(20, int(self.calc_bars_var.get().strip() or "240"))
        visible_bars = max(5, int(self.visible_bars_var.get().strip() or "40"))
        refresh_ms = max(300, int(self.refresh_ms_var.get().strip() or "1000"))

        if symbol_1 == symbol_2:
            raise RuntimeError("Нужно выбрать две разные пары")

        return symbol_1, symbol_2, timeframe, calc_bars, visible_bars, refresh_ms

    def calculate_ratio(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, timeframe, calc_bars, _, _ = self._read_inputs()
            frame, meta_1, meta_2 = load_two_symbols(self.client, symbol_1, symbol_2, timeframe, calc_bars)
            self.relative_metrics = calculate_relative_metrics(frame, meta_1.digits, meta_2.digits, timeframe)

            self.ppm_1_var.set(f"{self.relative_metrics.ppm_1:.4f}")
            self.ppm_2_var.set(f"{self.relative_metrics.ppm_2:.4f}")
            self.ratio_1_to_2_var.set(f"{self.relative_metrics.ratio_1_to_2:.6f}")
            self.ratio_2_to_1_var.set(f"{self.relative_metrics.ratio_2_to_1:.6f}")

            self.status_var.set("ratio_ready")
            self.render_once()
        except Exception as exc:
            self.status_var.set("ratio_error")
            messagebox.showerror("Расчёт коэффициента", str(exc))

    def render_once(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            if self.relative_metrics is None:
                raise RuntimeError("Сначала нажми 'Рассчитать коэффициент'")

            symbol_1, symbol_2, timeframe, _, visible_bars, _ = self._read_inputs()
            snapshot = build_render_snapshot(
                client=self.client,
                cfg=self.base_cfg,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                timeframe=timeframe,
                bars_count=visible_bars,
                ratio_1_to_2=self.relative_metrics.ratio_1_to_2,
                use_ratio_in_divergence=self.use_ratio_in_divergence_var.get(),
            )

            self.current_snapshot = snapshot
            self.current_trade_plan = snapshot.trade_plan

            if snapshot.bars.empty:
                return

            self.last_bar_time_var.set(str(snapshot.bars.iloc[-1]["time"]))
            self.trade_hint_var.set(
                f"Лидер {snapshot.trade_plan.leader_symbol} {snapshot.trade_plan.leader_move:.2f} | "
                f"ведомая {snapshot.trade_plan.follower_symbol} {snapshot.trade_plan.follower_move:.2f} | "
                f"SELL {snapshot.trade_plan.sell_symbol} {snapshot.trade_plan.sell_lots:.2f} / "
                f"BUY {snapshot.trade_plan.buy_symbol} {snapshot.trade_plan.buy_lots:.2f}"
            )
            self.trade_button.configure(text=snapshot.trade_plan.button_text)

            self.chart.draw(
                bars=snapshot.bars,
                symbol_1=symbol_1,
                symbol_2=symbol_2,
                ratio_1_to_2=self.relative_metrics.ratio_1_to_2,
                width_adjust_px=self.width_adjust_px,
                height_adjust_px=self.height_adjust_px,
                divergence_stats=snapshot.divergence_stats,
            )
            self.status_var.set("rendered")
        except Exception as exc:
            self.status_var.set("render_error")
            messagebox.showerror("Рендер", str(exc))

    def on_toggle_divergence_mode(self) -> None:
        if self.current_snapshot is not None:
            self.render_once()

    def change_size(self, axis: str, delta: int) -> None:
        if axis == "width":
            self.width_adjust_px += delta
            self.width_size_var.set(f"{self.width_adjust_px:+d}px")
        else:
            self.height_adjust_px += delta
            self.height_size_var.set(f"{self.height_adjust_px:+d}px")

        if self.current_snapshot is not None:
            self.render_once()

    def reset_size(self) -> None:
        self.width_adjust_px = 0
        self.height_adjust_px = 0
        self.width_size_var.set("0px")
        self.height_size_var.set("0px")
        if self.current_snapshot is not None:
            self.render_once()

    def open_current_positions(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            if self.current_trade_plan is None:
                raise RuntimeError("Сначала сделай рендер, чтобы появился текущий opposite-план")

            result = open_opposite_positions(self.client, self.base_cfg, self.current_trade_plan)
            self.status_var.set("orders_opened")
            messagebox.showinfo(
                "Позиции открыты",
                (
                    f"SELL {self.current_trade_plan.sell_symbol} {self.current_trade_plan.sell_lots:.2f}\\n"
                    f"BUY {self.current_trade_plan.buy_symbol} {self.current_trade_plan.buy_lots:.2f}\\n"
                    f"sell_order={result.sell_order} retcode={result.sell_retcode}\\n"
                    f"buy_order={result.buy_order} retcode={result.buy_retcode}"
                ),
            )
        except Exception as exc:
            self.status_var.set("order_error")
            messagebox.showerror("Открытие opposite позиций", str(exc))

    def close_current_pair_positions(self) -> None:
        try:
            self._ensure_connected()
            assert self.client is not None

            symbol_1, symbol_2, _, _, _, _ = self._read_inputs()
            summary = close_pair_positions(self.client, self.base_cfg, symbol_1, symbol_2)
            self.status_var.set("positions_closed")
            messagebox.showinfo(
                "Позиции закрыты",
                (
                    f"Связка: {symbol_1} / {symbol_2}\\n"
                    f"Закрыто позиций: {summary.closed_count}\\n"
                    f"gross+swap pnl usd: {summary.gross_pnl_usd:.2f}\\n"
                    f"net est pnl usd: {summary.net_pnl_est_usd:.2f}"
                ),
            )
            self.render_once()
        except Exception as exc:
            self.status_var.set("close_error")
            messagebox.showerror("Закрытие позиций по связке", str(exc))

    def start_live(self) -> None:
        try:
            if self.relative_metrics is None:
                raise RuntimeError("Сначала нажми 'Рассчитать коэффициент'")
            self.stop_live()
            self.status_var.set("live")
            self._live_tick()
        except Exception as exc:
            self.status_var.set("live_error")
            messagebox.showerror("Старт", str(exc))

    def _live_tick(self) -> None:
        try:
            self.render_once()
        except Exception:
            pass
        finally:
            try:
                _, _, _, _, _, refresh_ms = self._read_inputs()
            except Exception:
                refresh_ms = 1000
            self.live_job = self.after(refresh_ms, self._live_tick)

    def stop_live(self) -> None:
        if self.live_job is not None:
            self.after_cancel(self.live_job)
            self.live_job = None
        if self.status_var.get() == "live":
            self.status_var.set("stopped")

    def on_close(self) -> None:
        try:
            self.stop_live()
            if self.client is not None and self.connected:
                self.client.shutdown()
        finally:
            self.destroy()


def main() -> None:
    app = RelativeCompareUI()
    app.mainloop()
""",
}


REMOVE_FILES = [
    "src/app/ui_relative_compare.py",
]


ENV_DEFAULTS = {
    "COMMISSION_EURUSD_USD_PER_LOT_ONE_WAY": "2.4",
    "COMMISSION_AUDUSD_USD_PER_LOT_ONE_WAY": "1.5",
}


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\\n"), encoding="utf-8")
    print(f"[write] {relative_path}")


def remove_file(relative_path: str) -> None:
    path = ROOT / relative_path
    if path.exists():
        path.unlink()
        print(f"[remove] {relative_path}")


def append_env_defaults(relative_path: str) -> None:
    path = ROOT / relative_path
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    existing_keys = set()
    for line in lines:
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        existing_keys.add(raw.split("=", 1)[0].strip())

    additions = []
    for key, value in ENV_DEFAULTS.items():
        if key not in existing_keys:
            additions.append(f"{key}={value}")

    if not additions:
        return

    if lines and lines[-1].strip():
        lines.append("")
    lines.append("# Per-lot one-way commissions.")
    lines.extend(additions)
    path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print(f"[env] {relative_path}")


def main() -> None:
    for relative_path in REMOVE_FILES:
        remove_file(relative_path)

    for relative_path, content in FILES.items():
        write_file(relative_path, content)

    append_env_defaults(".env.example")
    if (ROOT / ".env").exists():
        append_env_defaults(".env")

    print("[ok] ui_relative_compare updated")


if __name__ == "__main__":
    main()