from __future__ import annotations

import time

import MetaTrader5 as mt5

DEAL_ENTRY_OUT = int(getattr(mt5, "DEAL_ENTRY_OUT", 1))
DEAL_ENTRY_OUT_BY = int(getattr(mt5, "DEAL_ENTRY_OUT_BY", 3))
DEAL_ENTRY_INOUT = int(getattr(mt5, "DEAL_ENTRY_INOUT", 2))
CLOSE_ENTRIES = {DEAL_ENTRY_OUT, DEAL_ENTRY_OUT_BY, DEAL_ENTRY_INOUT}


def position_deals(ticket: int) -> list:
    deals = mt5.history_deals_get(position=int(ticket))
    return list(deals or [])


def has_close_deal(deals: list) -> bool:
    for deal in deals:
        if int(getattr(deal, "entry", -1)) in CLOSE_ENTRIES:
            return True
    return False


def wait_closed_position_deals(ticket: int, timeout_sec: float = 10.0, sleep_sec: float = 0.2) -> list:
    deadline = time.time() + timeout_sec
    last_deals: list = []

    while time.time() < deadline:
        deals = position_deals(ticket)
        if deals:
            last_deals = deals
            if has_close_deal(deals):
                return deals
        if not mt5.positions_get(ticket=int(ticket)) and deals:
            return deals
        time.sleep(sleep_sec)

    return last_deals


def sum_deals(deals: list) -> tuple[float, float, float, float]:
    profit_usd = 0.0
    commission_usd = 0.0
    swap_usd = 0.0
    fee_usd = 0.0

    for deal in deals:
        profit_usd += float(getattr(deal, "profit", 0.0) or 0.0)
        commission_usd += float(getattr(deal, "commission", 0.0) or 0.0)
        swap_usd += float(getattr(deal, "swap", 0.0) or 0.0)
        fee_usd += float(getattr(deal, "fee", 0.0) or 0.0)

    return profit_usd, commission_usd, swap_usd, fee_usd
