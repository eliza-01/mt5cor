from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SelectionState:
    start_index: int | None = None
    end_index: int | None = None
    start_time: object | None = None
    end_time: object | None = None
    end_follows_latest: bool = False

    def clear(self) -> None:
        self.start_index = None
        self.end_index = None
        self.start_time = None
        self.end_time = None
        self.end_follows_latest = False

    def register_click(self, bars, index: int) -> None:
        selected_time = bars.iloc[index]["time"]
        is_latest = index == len(bars) - 1

        if self.start_time is None or self.end_time is not None:
            self.start_time = selected_time
            self.end_time = None
            self.end_follows_latest = False
        else:
            self.end_time = selected_time
            self.end_follows_latest = is_latest

            start_index = self._find_index_by_time(bars, self.start_time)
            end_index = self._find_index_by_time(bars, self.end_time)
            if start_index is not None and end_index is not None and end_index < start_index:
                self.start_time, self.end_time = self.end_time, self.start_time
                self.end_follows_latest = False

        self.resolve_indices(bars)

    def resolve_indices(self, bars) -> None:
        self.start_index = self._find_index_by_time(bars, self.start_time)

        if self.start_time is not None and self.start_index is None:
            self.clear()
            return

        if self.end_time is None:
            self.end_index = None
            return

        if self.end_follows_latest:
            self.end_index = len(bars) - 1 if not bars.empty else None
            if self.end_index is not None:
                self.end_time = bars.iloc[self.end_index]["time"]
        else:
            self.end_index = self._find_index_by_time(bars, self.end_time)
            if self.end_index is None:
                self.end_time = None
                self.end_follows_latest = False
                return

        if self.start_index is not None and self.end_index is not None and self.end_index < self.start_index:
            self.start_time, self.end_time = self.end_time, self.start_time
            self.start_index, self.end_index = self.end_index, self.start_index
            self.end_follows_latest = self.end_index == len(bars) - 1

    def _find_index_by_time(self, bars, target_time) -> int | None:
        if target_time is None or bars.empty:
            return None
        matches = bars.index[bars["time"] == target_time].tolist()
        if not matches:
            return None
        return int(matches[-1])
