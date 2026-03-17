from __future__ import annotations

from src.app.ui_relative_compare.constants import PANE_MIN_COLLAPSED, PANE_MIN_EXPANDED_BOTTOM, PANE_MIN_EXPANDED_TOP


class ControllerLayoutMixin:
    def on_line_zoom_changed(self) -> None:
        self.schedule_state_save()
        if self.current_snapshot is not None:
            self.redraw_current_snapshot()

    def on_line_zoom_wheel(self, event) -> str:
        step = 0.2
        if getattr(event, "num", None) == 4:
            direction = 1
        elif getattr(event, "num", None) == 5:
            direction = -1
        else:
            delta = int(getattr(event, "delta", 0) or 0)
            if delta == 0:
                return "break"
            direction = 1 if delta > 0 else -1

        value = float(self.view.line_zoom_var.get() or 1.0) + direction * step
        self.view.line_zoom_var.set(max(1.0, min(8.0, value)))
        self.on_line_zoom_changed()
        return "break"

    def update_pane_toggle_labels(self) -> None:
        self.view.sizing_toggle_var.set("▸" if self.view.sizing_collapsed else "▾")
        self.view.candle_toggle_var.set("▸" if self.view.candle_collapsed else "▾")
        self.view.line_toggle_var.set("▸" if self.view.line_collapsed else "▾")

    def toggle_sizing_panel(self) -> None:
        self.view.sizing_collapsed = not self.view.sizing_collapsed
        self.update_pane_toggle_labels()
        self.view.set_panel_body_visible(self.view.sizing_body, not self.view.sizing_collapsed)
        self.schedule_state_save()

    def toggle_candle_panel(self) -> None:
        if not self.view.candle_collapsed:
            self.view.chart_split_y = self.view.current_chart_split_y()
        self.view.candle_collapsed = not self.view.candle_collapsed
        self.apply_chart_sections_layout()
        self.schedule_state_save()

    def toggle_line_panel(self) -> None:
        if not self.view.line_collapsed:
            self.view.chart_split_y = self.view.current_chart_split_y()
        self.view.line_collapsed = not self.view.line_collapsed
        self.apply_chart_sections_layout()
        self.schedule_state_save()

    def apply_chart_sections_layout(self) -> None:
        try:
            self.view.update_idletasks()
            self.update_pane_toggle_labels()
            self.view.set_panel_body_visible(self.view.candle_body, not self.view.candle_collapsed)
            self.view.set_panel_body_visible(self.view.line_body, not self.view.line_collapsed)
            self.view.set_panel_body_visible(self.view.sizing_body, not self.view.sizing_collapsed)

            total_height = max(int(self.view.chart_panes.winfo_height()), 380)
            candle_min = PANE_MIN_COLLAPSED if self.view.candle_collapsed else PANE_MIN_EXPANDED_TOP
            line_min = PANE_MIN_COLLAPSED if self.view.line_collapsed else PANE_MIN_EXPANDED_BOTTOM

            self.view.chart_panes.paneconfigure(self.view.candle_wrap, minsize=candle_min, height=candle_min if self.view.candle_collapsed else max(candle_min, int(self.view.chart_split_y)), stretch="never" if self.view.candle_collapsed else "always")
            self.view.chart_panes.paneconfigure(self.view.line_wrap, minsize=line_min, height=line_min if self.view.line_collapsed else max(line_min, total_height - int(self.view.chart_split_y)), stretch="never" if self.view.line_collapsed else "always")

            if self.view.candle_collapsed:
                split_y = PANE_MIN_COLLAPSED
            elif self.view.line_collapsed:
                split_y = max(PANE_MIN_EXPANDED_TOP, total_height - PANE_MIN_COLLAPSED)
            else:
                split_y = max(PANE_MIN_EXPANDED_TOP, min(total_height - PANE_MIN_EXPANDED_BOTTOM, int(self.view.chart_split_y or int(total_height * 0.65))))
            self.view.chart_panes.sash_place(0, 0, split_y)
        except Exception:
            return

    def change_size(self, axis: str, delta: int) -> None:
        if axis == "width":
            self.view.width_adjust_px += delta
            self.view.width_size_var.set(f"{self.view.width_adjust_px:+d}px")
        else:
            self.view.height_adjust_px += delta
            self.view.height_size_var.set(f"{self.view.height_adjust_px:+d}px")
        self.schedule_state_save()
        if self.current_snapshot is not None:
            self.redraw_current_snapshot()

    def change_pair_gap(self, delta: int) -> None:
        self.view.pair_gap_adjust_px += delta
        self.view.pair_gap_size_var.set(f"{self.view.pair_gap_adjust_px:+d}px")
        self.schedule_state_save()
        if self.current_snapshot is not None:
            self.redraw_current_snapshot()

    def reset_size(self) -> None:
        self.view.width_adjust_px = 0
        self.view.height_adjust_px = 0
        self.view.pair_gap_adjust_px = 0
        self.view.width_size_var.set("0px")
        self.view.height_size_var.set("0px")
        self.view.pair_gap_size_var.set("0px")
        self.schedule_state_save()
        if self.current_snapshot is not None:
            self.redraw_current_snapshot()
