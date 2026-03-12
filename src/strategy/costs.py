
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
