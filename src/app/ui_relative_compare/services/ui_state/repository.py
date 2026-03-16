from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

from src.common.settings import Settings
from .model import UIState


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
        return UIState(**{**asdict(UIState()), **raw})
    except Exception:
        return UIState()


def save_ui_state(cfg: Settings, state: UIState) -> None:
    path = _state_path(cfg)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)
