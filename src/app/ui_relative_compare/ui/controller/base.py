from __future__ import annotations

from src.app.ui_relative_compare.domain import RelativeMetrics, RenderSnapshot, SelectionState
from src.app.ui_relative_compare.services.ui_state import load_ui_state
from src.app.ui_relative_compare.ui.chart import RelativeChart
from src.common.settings import load_settings
from .layout import ControllerLayoutMixin
from .lifecycle import ControllerLifecycleMixin
from .render import ControllerRenderMixin
from .selection import ControllerSelectionMixin
from .state import ControllerStateMixin
from .trade import ControllerTradeMixin
from ..view.window import RelativeCompareWindow


class RelativeCompareController(ControllerStateMixin, ControllerLayoutMixin, ControllerSelectionMixin, ControllerRenderMixin, ControllerTradeMixin, ControllerLifecycleMixin):
    def __init__(self) -> None:
        self.base_cfg = load_settings()
        self.saved_state = load_ui_state(self.base_cfg)
        self.view = RelativeCompareWindow(controller=self, saved_state=self.saved_state)

        self.client = None
        self.connected = False
        self.live_job: str | None = None
        self.state_save_job: str | None = None
        self.relative_metrics: RelativeMetrics | None = None
        self.current_snapshot: RenderSnapshot | None = None
        self.selection = SelectionState()

        self.drag_start_x = 0
        self.drag_active = False
        self.chart = RelativeChart(self.view.candle_canvas, self.view.line_canvas)

        self.bind_state_persistence()
        self.bind_scroll_events()
        self.update_symbol_labels()
        self.update_manual_volume_state()
        self.refresh_color_markers()
        self.refresh_action_buttons()
        self.update_pane_toggle_labels()
        self.view.after(120, self.apply_chart_sections_layout)
        self.view.protocol("WM_DELETE_WINDOW", self.on_close)

    def run(self) -> None:
        self.view.mainloop()
