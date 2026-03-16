from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OrderSendSummary:
    sell_retcode: int
    buy_retcode: int
    sell_order: int
    buy_order: int
    sell_volume: float
    buy_volume: float


@dataclass(slots=True)
class ClosePairSummary:
    closed_count: int
    deals_count: int
    profit_usd: float
    commission_usd: float
    swap_usd: float
    fee_usd: float
    total_pnl_usd: float


@dataclass(slots=True)
class ReopenedLeg:
    symbol: str
    side: str
    volume: float
    retcode: int
    order: int


@dataclass(slots=True)
class ReversePairSummary:
    close_summary: ClosePairSummary
    reopened_legs: list[ReopenedLeg]
