from __future__ import annotations


def normalize_fx_symbol(symbol: str) -> str:
    letters = "".join(ch for ch in str(symbol).upper() if "A" <= ch <= "Z")
    return letters[:6]


def split_fx_symbol(symbol: str) -> tuple[str, str]:
    normalized = normalize_fx_symbol(symbol)
    if len(normalized) < 6:
        raise RuntimeError(f"Символ {symbol!r} не похож на FX-пару из 6 букв")
    return normalized[:3], normalized[3:6]
