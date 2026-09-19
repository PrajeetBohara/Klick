"""Auto-clicker / auto-scroll engine."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from pynput.mouse import Button, Controller

from app.utils.timing import AutoStopConfig, IntervalConfig, auto_stop_reached

BUTTON_MAP = {
    "left": Button.left,
    "right": Button.right,
    "middle": Button.middle,
}

CLICK_COUNTS = {
    "single": 1,
    "double": 2,
    "triple": 3,
}


@dataclass
class ClickerConfig:
    action: str = "click"  # click | scroll
    interval: IntervalConfig = field(default_factory=IntervalConfig)
    button: str = "left"
    click_type: str = "single"
    position_mode: str = "current"
    fixed_x: int = 0
    fixed_y: int = 0
    scroll_direction: str = "down"  # up | down
    scroll_amount: int = 3
    repeat_mode: str = "unlimited"
    repeat_count: int = 10
    start_delay: float = 0.0
    auto_stop: AutoStopConfig = field(default_factory=AutoStopConfig)


class ClickerEngine:
    def __init__(
        self,
        on_tick: Callable[[int], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        on_stopped: Callable[[], None] | None = None,
    ) -> None:
        self._mouse = Controller()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._on_tick = on_tick
        self._on_status = on_status
        self._on_stopped = on_stopped
        self.click_count = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, config: ClickerConfig) -> None:
        if self._running:
            return
        self._stop_event.clear()
        self._running = True
        self.click_count = 0
        self._thread = threading.Thread(
            target=self._run, args=(config,), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._running = False

    def _emit_status(self, message: str) -> None:
        if self._on_status:
            self._on_status(message)

    def _run(self, config: ClickerConfig) -> None:
        try:
            button = BUTTON_MAP.get(config.button, Button.left)
            clicks = CLICK_COUNTS.get(config.click_type, 1)
            limit = (
                None
                if config.repeat_mode == "unlimited"
                else max(1, int(config.repeat_count))
            )
            scroll_delta = abs(max(1, int(config.scroll_amount)))
            if config.scroll_direction == "up":
                scroll_delta = scroll_delta
            else:
                scroll_delta = -scroll_delta

            if config.start_delay > 0:
                self._emit_status(f"Starting in {config.start_delay:.1f}s…")
                if self._stop_event.wait(config.start_delay):
                    return

            started_at = time.monotonic()
            status = "Scrolling" if config.action == "scroll" else "Clicking"
            self._emit_status(status)

            while not self._stop_event.is_set():
                if auto_stop_reached(started_at, config.auto_stop, time.monotonic()):
                    self._emit_status("Auto-stopped")
                    break

                if config.position_mode == "fixed":
                    self._mouse.position = (int(config.fixed_x), int(config.fixed_y))

                if config.action == "scroll":
                    self._mouse.scroll(0, scroll_delta)
                else:
                    self._mouse.click(button, clicks)

                self.click_count += 1
                if self._on_tick:
                    self._on_tick(self.click_count)

                if limit is not None and self.click_count >= limit:
                    break

                if self._stop_event.wait(config.interval.next_seconds()):
                    break
        finally:
            self._running = False
            self._emit_status("Stopped")
            if self._on_stopped:
                self._on_stopped()
