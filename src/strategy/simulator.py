
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
