#файл для внесения точечных изменений в виде патча

from __future__ import annotations

from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent
APP_PATH = ROOT / "src/app/ui_relative_compare/ui/app.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Не найден фрагмент для замены: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    if not APP_PATH.exists():
        raise RuntimeError(f"Файл не найден: {APP_PATH}")

    text = APP_PATH.read_text(encoding="utf-8")

    text = replace_once(
        text,
        textwrap.dedent(
            """
                    self.selected_start_index: int | None = None
                    self.selected_end_index: int | None = None
            """
        ).strip("\n"),
        textwrap.dedent(
            """
                    self.selected_start_index: int | None = None
                    self.selected_end_index: int | None = None
                    self.selected_start_time = None
                    self.selected_end_time = None
                    self.selected_end_follows_latest = False
            """
        ).strip("\n"),
        "init selection fields",
    )

    text = replace_once(
        text,
        textwrap.dedent(
            """
                def _handle_chart_click(self, widget: tk.Widget, x_local: int) -> None:
                    if self.current_snapshot is None or self.current_snapshot.bars.empty:
                        return

                    canvas = self.candle_canvas if widget is self.candle_canvas else self.line_canvas
                    x_world = float(canvas.canvasx(x_local))
                    index = self.chart.get_index_at_x(
                        bars_count=len(self.current_snapshot.bars),
                        x_world=x_world,
                        width_adjust_px=self.width_adjust_px,
                        pair_gap_adjust_px=self.pair_gap_adjust_px,
                    )
                    if index is None:
                        return

                    if self.selected_start_index is None or self.selected_end_index is not None:
                        self.selected_start_index = index
                        self.selected_end_index = None
                    else:
                        self.selected_end_index = index
                        if self.selected_end_index < self.selected_start_index:
                            self.selected_start_index, self.selected_end_index = self.selected_end_index, self.selected_start_index

                    self._redraw_current_snapshot()
            """
        ).strip("\n"),
        textwrap.dedent(
            """
                def _handle_chart_click(self, widget: tk.Widget, x_local: int) -> None:
                    if self.current_snapshot is None or self.current_snapshot.bars.empty:
                        return

                    canvas = self.candle_canvas if widget is self.candle_canvas else self.line_canvas
                    x_world = float(canvas.canvasx(x_local))
                    index = self.chart.get_index_at_x(
                        bars_count=len(self.current_snapshot.bars),
                        x_world=x_world,
                        width_adjust_px=self.width_adjust_px,
                        pair_gap_adjust_px=self.pair_gap_adjust_px,
                    )
                    if index is None:
                        return

                    bars = self.current_snapshot.bars
                    selected_time = bars.iloc[index]["time"]
                    is_latest = index == len(bars) - 1

                    if self.selected_start_time is None or self.selected_end_time is not None:
                        self.selected_start_time = selected_time
                        self.selected_end_time = None
                        self.selected_end_follows_latest = False
                    else:
                        self.selected_end_time = selected_time
                        self.selected_end_follows_latest = is_latest

                        start_index = self._find_index_by_time(bars, self.selected_start_time)
                        end_index = self._find_index_by_time(bars, self.selected_end_time)
                        if start_index is not None and end_index is not None and end_index < start_index:
                            self.selected_start_time, self.selected_end_time = self.selected_end_time, self.selected_start_time
                            self.selected_end_follows_latest = False

                    self._resolve_selection_indices(bars)
                    self._redraw_current_snapshot()
            """
        ).strip("\n"),
        "_handle_chart_click",
    )

    text = replace_once(
        text,
        "            self._normalize_selection_indices(len(snapshot.bars))",
        "            self._resolve_selection_indices(snapshot.bars)",
        "render_once selection resolve",
    )

    text = replace_once(
        text,
        "        self._normalize_selection_indices(len(self.current_snapshot.bars))",
        "        self._resolve_selection_indices(self.current_snapshot.bars)",
        "_redraw_current_snapshot selection resolve",
    )

    text = replace_once(
        text,
        textwrap.dedent(
            """
                def _normalize_selection_indices(self, bars_count: int) -> None:
                    if bars_count <= 0:
                        self.selected_start_index = None
                        self.selected_end_index = None
                        return

                    if self.selected_start_index is not None:
                        self.selected_start_index = max(0, min(bars_count - 1, int(self.selected_start_index)))

                    if self.selected_end_index is not None:
                        self.selected_end_index = max(0, min(bars_count - 1, int(self.selected_end_index)))

                    if self.selected_start_index is not None and self.selected_end_index is not None:
                        if self.selected_end_index < self.selected_start_index:
                            self.selected_start_index, self.selected_end_index = self.selected_end_index, self.selected_start_index
            """
        ).strip("\n"),
        textwrap.dedent(
            """
                def _find_index_by_time(self, bars, target_time) -> int | None:
                    if target_time is None or bars.empty:
                        return None

                    matches = bars.index[bars["time"] == target_time].tolist()
                    if not matches:
                        return None
                    return int(matches[-1])

                def _resolve_selection_indices(self, bars) -> None:
                    self.selected_start_index = self._find_index_by_time(bars, self.selected_start_time)

                    if self.selected_start_time is not None and self.selected_start_index is None:
                        self.selected_start_time = None
                        self.selected_end_time = None
                        self.selected_end_follows_latest = False
                        self.selected_start_index = None
                        self.selected_end_index = None
                        return

                    if self.selected_end_time is None:
                        self.selected_end_index = None
                        return

                    if self.selected_end_follows_latest:
                        self.selected_end_index = len(bars) - 1 if not bars.empty else None
                        if self.selected_end_index is not None:
                            self.selected_end_time = bars.iloc[self.selected_end_index]["time"]
                    else:
                        self.selected_end_index = self._find_index_by_time(bars, self.selected_end_time)
                        if self.selected_end_index is None:
                            self.selected_end_time = None
                            self.selected_end_index = None
                            self.selected_end_follows_latest = False

                    if self.selected_start_index is not None and self.selected_end_index is not None:
                        if self.selected_end_index < self.selected_start_index:
                            self.selected_start_time, self.selected_end_time = self.selected_end_time, self.selected_start_time
                            self.selected_start_index, self.selected_end_index = self.selected_end_index, self.selected_start_index
                            self.selected_end_follows_latest = self.selected_end_index == len(bars) - 1
            """
        ).strip("\n"),
        "_normalize_selection_indices -> time based selection",
    )

    APP_PATH.write_text(text, encoding="utf-8")
    print("[ok] patched src/app/ui_relative_compare/ui/app.py")


if __name__ == "__main__":
    main()