from __future__ import annotations

from tkinter import ttk


def kv(parent: ttk.Widget, row: int, col: int, key: str, var) -> None:
    ttk.Label(parent, text=key).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
    ttk.Label(parent, textvariable=var).grid(row=row, column=col + 1, sticky="w", padx=(0, 18), pady=4)
