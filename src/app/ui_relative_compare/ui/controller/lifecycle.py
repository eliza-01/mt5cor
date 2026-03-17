from __future__ import annotations

from tkinter import messagebox


class ControllerLifecycleMixin:
    def start_live(self) -> None:
        try:
            self.stop_live()
            self.view.status_var.set("live")
            self.live_tick()
        except Exception as exc:
            self.view.status_var.set("live_error")
            messagebox.showerror("Старт", str(exc))

    def live_tick(self) -> None:
        try:
            self.render_once(from_live=True)
        except Exception:
            pass
        finally:
            try:
                _, _, _, _, refresh_ms, _ = self.read_inputs()
            except Exception:
                refresh_ms = 250
            self.live_job = self.view.after(refresh_ms, self.live_tick)

    def stop_live(self) -> None:
        if self.live_job is not None:
            self.view.after_cancel(self.live_job)
            self.live_job = None
        if self.view.status_var.get() == "live":
            self.view.status_var.set("stopped")

    def on_close(self) -> None:
        try:
            self.save_state_now()
            self.stop_live()
            if self.client is not None and self.connected:
                self.client.shutdown()
        finally:
            self.view.destroy()