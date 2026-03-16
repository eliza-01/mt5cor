from __future__ import annotations

import tkinter as tk


def draw_marker(canvas: tk.Canvas, x: float, y: float, color: str) -> None:
    radius = 5
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=color, width=2)
    canvas.create_oval(x - 1, y - 1, x + 1, y + 1, outline=color, fill=color)


def draw_body(canvas: tk.Canvas, x: float, y_open: float, y_close: float, half_width: float, color: str) -> None:
    top = min(y_open, y_close)
    bottom = max(y_open, y_close)
    if abs(bottom - top) < 2:
        canvas.create_line(x - half_width, y_close, x + half_width, y_close, fill=color, width=3)
        return
    canvas.create_rectangle(x - half_width, top, x + half_width, bottom, outline=color, fill=color)


def draw_sell_arrow(canvas: tk.Canvas, x: float, y: float, color: str) -> None:
    canvas.create_text(x, max(50.0, y), anchor="s", fill=color, font=("Segoe UI", 12, "bold"), text="↓")


def draw_buy_arrow(canvas: tk.Canvas, x: float, y: float, color: str, height: int) -> None:
    canvas.create_text(x, min(float(height - 20), y), anchor="n", fill=color, font=("Segoe UI", 12, "bold"), text="↑")
