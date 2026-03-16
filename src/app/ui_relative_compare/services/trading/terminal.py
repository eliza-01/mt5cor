from __future__ import annotations

import MetaTrader5 as mt5

CLIENT_DISABLES_AT = 10027


def terminal_flags() -> dict:
    info = mt5.terminal_info()
    if info is None:
        return {}
    try:
        return info._asdict()
    except Exception:
        return {}


def ensure_python_trading_enabled() -> None:
    flags = terminal_flags()
    if bool(flags.get("tradeapi_disabled", False)):
        raise RuntimeError("В MT5 запрещена торговля через внешний Python API. Открой Tools -> Options -> Expert Advisors и отключи 'Disable automatic trading via external Python API'. Также проверь, что кнопка Algo Trading включена.")
    if "trade_allowed" in flags and not bool(flags.get("trade_allowed")):
        raise RuntimeError("В MT5 выключена автоматическая торговля. Включи кнопку Algo Trading в терминале.")
