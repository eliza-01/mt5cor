from __future__ import annotations

from dataclasses import dataclass

BASE_BODY_HALF = 4.0
BASE_PAIR_GAP = 10.0
LEFT_PAD = 60
RIGHT_PAD = 30
EPS = 1e-12


@dataclass(slots=True)
class PairLayout:
    body_half: float
    pair_gap: float
    pair_width: float


def pair_layout(width_adjust_px: int, pair_gap_adjust_px: int) -> PairLayout:
    body_half = max(2.0, BASE_BODY_HALF + width_adjust_px * 0.35)
    pair_gap = max(0.0, BASE_PAIR_GAP + pair_gap_adjust_px)
    pair_width = body_half * 4.0
    return PairLayout(body_half=body_half, pair_gap=pair_gap, pair_width=pair_width)


def pair_total_width(count: int, pair_width: float, pair_gap: float) -> float:
    if count <= 0:
        return 0.0
    return count * pair_width + max(0, count - 1) * pair_gap


def pair_positions(index: int, left_pad: float, body_half: float, pair_gap: float, pair_width: float) -> tuple[float, float, float]:
    pair_left = left_pad + index * (pair_width + pair_gap)
    p1_x = pair_left + body_half
    p2_x = pair_left + body_half * 3.0
    pair_center_x = pair_left + pair_width / 2.0
    return p1_x, p2_x, pair_center_x
