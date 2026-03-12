# src/app/ui_relative_compare/services/ui_state.py
# Saves and loads persistent UI state for the relative compare window.
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

from src.common.settings import Settings


@dataclass(slots=True)
class UIState:
    symbol_1: str = "EURUSD"
    symbol_2: str = "AUDUSD"
    timeframe: str = "M1"
    calc_bars: str = "1440"
    visible_bars: str = "120"
    refresh_ms: str = "250"
    aggregate_bars: str = "1"
    use_ratio_in_divergence: bool = False
    width_adjust_px: int = 0
    height_adjust_px: int = 0
    pair_gap_adjust_px: int = 0
    window_geometry: str = "1380x980"


def _state_path(cfg: Settings) -> Path:
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    return cfg.data_dir / "ui_relative_compare_state.json"


def load_ui_state(cfg: Settings) -> UIState:
    path = _state_path(cfg)
    if not path.exists():
        return UIState()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return UIState()

    try:
        return UIState(
            symbol_1=str(raw.get("symbol_1", "EURUSD") or "EURUSD"),
            symbol_2=str(raw.get("symbol_2", "AUDUSD") or "AUDUSD"),
            timeframe=str(raw.get("timeframe", "M1") or "M1"),
            calc_bars=str(raw.get("calc_bars", "1440") or "1440"),
            visible_bars=str(raw.get("visible_bars", "120") or "120"),
            refresh_ms=str(raw.get("refresh_ms", "250") or "250"),
            aggregate_bars=str(raw.get("aggregate_bars", "1") or "1"),
            use_ratio_in_divergence=bool(raw.get("use_ratio_in_divergence", False)),
            width_adjust_px=int(raw.get("width_adjust_px", 0) or 0),
            height_adjust_px=int(raw.get("height_adjust_px", 0) or 0),
            pair_gap_adjust_px=int(raw.get("pair_gap_adjust_px", 0) or 0),
            window_geometry=str(raw.get("window_geometry", "1380x980") or "1380x980"),
        )
    except Exception:
        return UIState()


def save_ui_state(cfg: Settings, state: UIState) -> None:
    path = _state_path(cfg)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)