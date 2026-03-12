# src/broker/mt5_client.py
# Thin MT5 wrapper for account, symbols, bars, and ticks.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import MetaTrader5 as mt5
import pandas as pd

from src.common.settings import Settings


TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
}


@dataclass(slots=True)
class SymbolMeta:
    symbol: str
    digits: int
    point: float
    contract_size: float
    volume_min: float
    volume_step: float
    tick_size: float
    tick_value: float
    swap_long: float
    swap_short: float


class MT5Client:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _normalize_terminal_path(self) -> str | None:
        raw = (self.settings.mt5_terminal_path or "").strip().strip('"').strip("'")
        if not raw:
            return None

        path = Path(raw)

        if path.is_dir():
            for name in ("terminal64.exe", "terminal.exe", "metatrader64.exe", "metatrader.exe"):
                candidate = path / name
                if candidate.exists():
                    return str(candidate)
            raise RuntimeError(
                f"MT5_TERMINAL_PATH points to a directory, but no terminal EXE was found inside: {path}"
            )

        if not path.exists():
            raise RuntimeError(f"MT5 terminal path does not exist: {path}")

        return str(path)

    def connect(self) -> None:
        terminal_path = self._normalize_terminal_path()

        init_kwargs: dict[str, Any] = {
            "timeout": self.settings.mt5_timeout_ms,
            "portable": self.settings.mt5_portable,
        }
        if terminal_path:
            init_kwargs["path"] = terminal_path

        ok = mt5.initialize(**init_kwargs)
        if not ok:
            raise RuntimeError(f"mt5.initialize failed: {mt5.last_error()}")

        if self.settings.mt5_login > 0:
            ok = mt5.login(
                int(self.settings.mt5_login),
                password=self.settings.mt5_password,
                server=self.settings.mt5_server,
                timeout=self.settings.mt5_timeout_ms,
            )
            if not ok:
                raise RuntimeError(f"mt5.login failed: {mt5.last_error()}")

        account = mt5.account_info()
        if account is None:
            raise RuntimeError(f"mt5.account_info failed after login: {mt5.last_error()}")

    def shutdown(self) -> None:
        mt5.shutdown()

    def ensure_symbol(self, symbol: str) -> None:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"symbol not found: {symbol}")
        if not info.visible and not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"symbol_select failed: {symbol}")

    def symbol_meta(self, symbol: str) -> SymbolMeta:
        self.ensure_symbol(symbol)
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"symbol_info failed: {symbol}")
        return SymbolMeta(
            symbol=symbol,
            digits=info.digits,
            point=info.point,
            contract_size=info.trade_contract_size,
            volume_min=info.volume_min,
            volume_step=info.volume_step,
            tick_size=info.trade_tick_size,
            tick_value=info.trade_tick_value,
            swap_long=info.swap_long,
            swap_short=info.swap_short,
        )

    def copy_rates(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        self.ensure_symbol(symbol)
        if timeframe not in TIMEFRAMES:
            raise RuntimeError(f"unsupported timeframe: {timeframe}")

        rates = mt5.copy_rates_from_pos(symbol, TIMEFRAMES[timeframe], 0, bars)
        if rates is None:
            raise RuntimeError(f"copy_rates_from_pos failed for {symbol}: {mt5.last_error()}")

        frame = pd.DataFrame(rates)
        if frame.empty:
            raise RuntimeError(f"no rates returned for {symbol}")

        frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True)
        return frame

    def tick(self, symbol: str) -> dict[str, Any]:
        self.ensure_symbol(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"symbol_info_tick failed for {symbol}: {mt5.last_error()}")
        return tick._asdict()
