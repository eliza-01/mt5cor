from __future__ import annotations


def normalize_symbol(symbol: str) -> str:
    return "".join(ch for ch in symbol.upper() if "A" <= ch <= "Z")[:6] or symbol.upper()


def base_label(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    base = normalized[:3]
    if base == "EUR":
        return "EURO"
    return base or symbol.upper()


def format_symbol_for_stats(symbol: str) -> str:
    letters = "".join(ch for ch in symbol.upper() if "A" <= ch <= "Z")
    return f"{letters[:3]}/{letters[3:6]}" if len(letters) >= 6 else symbol


def format_pips(value: float) -> str:
    text = f"{float(value):+.4f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def pip_size(digits: int) -> float:
    return 0.01 if digits in (2, 3) else 0.0001
