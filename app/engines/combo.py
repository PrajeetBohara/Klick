"""Custom combo engine: click, type, scroll, wait sequences."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key
from pynput.mouse import Button, Controller as MouseController

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
class ComboStep:
    action: str = "click"  # click | type | scroll | wait
    button: str = "left"
    click_type: str = "single"
    position_mode: str = "current"
    fixed_x: int = 0
    fixed_y: int = 0
    text: str = ""
    press_enter: bool = False
    scroll_direction: str = "down"
    scroll_amount: int = 3
    wait_ms: int = 500

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "button": self.button,
            "click_type": self.click_type,
            "position_mode": self.position_mode,
            "fixed_x": self.fixed_x,
            "fixed_y": self.fixed_y,
            "text": self.text,
            "press_enter": self.press_enter,
            "scroll_direction": self.scroll_direction,
            "scroll_amount": self.scroll_amount,
            "wait_ms": self.wait_ms,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> ComboStep:
        data = data or {}
        return cls(
            action=str(data.get("action", "click")),
            button=str(data.get("button", "left")),
            click_type=str(data.get("click_type", "single")),
            position_mode=str(data.get("position_mode", "current")),
            fixed_x=int(data.get("fixed_x", 0) or 0),
            fixed_y=int(data.get("fixed_y", 0) or 0),
            text=str(data.get("text", "")),
            press_enter=bool(data.get("press_enter", False)),
            scroll_direction=str(data.get("scroll_direction", "down")),
            scroll_amount=int(data.get("scroll_amount", 3) or 3),
            wait_ms=int(data.get("wait_ms", 500) or 500),
        )


@dataclass
class ComboConfig:
    steps: list[ComboStep] = field(default_factory=list)
    interval: IntervalConfig = field(default_factory=IntervalConfig)
    repeat_mode: str = "once"  # once | unlimited | count
    repeat_count: int = 1
    start_delay: float = 2.0
    auto_stop: AutoStopConfig = field(default_factory=AutoStopConfig)


class ComboEngine:
    def __init__(
        self,
        on_tick: Callable[[int], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        on_stopped: Callable[[], None] | None = None,
    ) -> None:
        self._mouse = MouseController()
        self._keyboard = KeyboardController()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._on_tick = on_tick
        self._on_status = on_status
        self._on_stopped = on_stopped
        self.action_count = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, config: ComboConfig) -> None:
        if self._running:
            return
        if not config.steps:
            self._emit_status("No combo steps")
            return
        self._stop_event.clear()
        self._running = True
        self.action_count = 0
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

    def _execute_step(self, step: ComboStep) -> None:
        if step.action == "wait":
            self._stop_event.wait(max(int(step.wait_ms), 1) / 1000.0)
            return

        if step.action == "click":
            if step.position_mode == "fixed":
                self._mouse.position = (int(step.fixed_x), int(step.fixed_y))
            button = BUTTON_MAP.get(step.button, Button.left)
            clicks = CLICK_COUNTS.get(step.click_type, 1)
            self._mouse.click(button, clicks)
            return

        if step.action == "scroll":
            if step.position_mode == "fixed":
                self._mouse.position = (int(step.fixed_x), int(step.fixed_y))
            amount = abs(max(1, int(step.scroll_amount)))
            delta = amount if step.scroll_direction == "up" else -amount
            self._mouse.scroll(0, delta)
            return

        if step.action == "type":
            if step.text:
                self._keyboard.type(step.text)
            if step.press_enter:
                self._keyboard.press(Key.enter)
                self._keyboard.release(Key.enter)

    def _run(self, config: ComboConfig) -> None:
        try:
            if config.repeat_mode == "once":
                runs = 1
            elif config.repeat_mode == "unlimited":
                runs = None
            else:
                runs = max(1, int(config.repeat_count))

            if config.start_delay > 0:
                self._emit_status(f"Combo starts in {config.start_delay:.1f}s…")
                if self._stop_event.wait(config.start_delay):
                    return

            started_at = time.monotonic()
            self._emit_status("Running combo")
            completed_runs = 0

            while not self._stop_event.is_set():
                if auto_stop_reached(started_at, config.auto_stop, time.monotonic()):
                    self._emit_status("Auto-stopped")
                    break

                for step in config.steps:
                    if self._stop_event.is_set():
                        break
                    if auto_stop_reached(started_at, config.auto_stop, time.monotonic()):
                        self._emit_status("Auto-stopped")
                        return

                    self._execute_step(step)
                    self.action_count += 1
                    if self._on_tick:
                        self._on_tick(self.action_count)

                    if step.action != "wait":
                        if self._stop_event.wait(config.interval.next_seconds()):
                            break

                if self._stop_event.is_set():
                    break

                completed_runs += 1
                if runs is not None and completed_runs >= runs:
                    break
        finally:
            self._running = False
            self._emit_status("Stopped")
            if self._on_stopped:
                self._on_stopped()
