from __future__ import annotations

from .controller.base import RelativeCompareController


def main() -> None:
    controller = RelativeCompareController()
    controller.run()
