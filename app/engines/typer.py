"""Auto-typer engine."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from pynput.keyboard import Controller, Key

from app.utils.timing import AutoStopConfig, DurationParts, IntervalConfig, auto_stop_reached


@dataclass
class TyperConfig:
    text: str = ""
    interval: IntervalConfig = field(
        default_factory=lambda: IntervalConfig(
            fixed=DurationParts(milliseconds=50),
            minimum=DurationParts(milliseconds=30),
            maximum=DurationParts(milliseconds=120),
        )
    )
    unit_mode: str = "character"  # character | word
    repeat_mode: str = "once"  # once | unlimited | count
    repeat_count: int = 1
    start_delay: float = 2.0
    press_enter: bool = False
    auto_stop: AutoStopConfig = field(default_factory=AutoStopConfig)


class TyperEngine:
    def __init__(
        self,
        on_tick: Callable[[int], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        on_stopped: Callable[[], None] | None = None,
    ) -> None:
        self._keyboard = Controller()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._on_tick = on_tick
        self._on_status = on_status
        self._on_stopped = on_stopped
        self.key_count = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, config: TyperConfig) -> None:
        if self._running:
            return
        if not config.text.strip():
            self._emit_status("No text to type")
            return
        self._stop_event.clear()
        self._running = True
        self.key_count = 0
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

    def _type_units(self, text: str, mode: str) -> list[str]:
        if mode == "word":
            parts = text.split(" ")
            units: list[str] = []
            for index, part in enumerate(parts):
                units.append(part)
                if index < len(parts) - 1:
                    units.append(" ")
            return units
        return list(text)

    def _run(self, config: TyperConfig) -> None:
        try:
            units = self._type_units(config.text, config.unit_mode)

            if config.repeat_mode == "once":
                runs = 1
            elif config.repeat_mode == "unlimited":
                runs = None
            else:
                runs = max(1, int(config.repeat_count))

            if config.start_delay > 0:
                self._emit_status(f"Typing starts in {config.start_delay:.1f}s…")
                if self._stop_event.wait(config.start_delay):
                    return

            started_at = time.monotonic()
            self._emit_status("Typing")
            completed_runs = 0
            while not self._stop_event.is_set():
                if auto_stop_reached(started_at, config.auto_stop, time.monotonic()):
                    self._emit_status("Auto-stopped")
                    break

                for unit in units:
                    if self._stop_event.is_set():
                        break
                    if auto_stop_reached(started_at, config.auto_stop, time.monotonic()):
                        self._emit_status("Auto-stopped")
                        return
                    self._keyboard.type(unit)
                    self.key_count += len(unit)
                    if self._on_tick:
                        self._on_tick(self.key_count)
                    if self._stop_event.wait(config.interval.next_seconds()):
                        break

                if self._stop_event.is_set():
                    break

                if config.press_enter:
                    self._keyboard.press(Key.enter)
                    self._keyboard.release(Key.enter)

                completed_runs += 1
                if runs is not None and completed_runs >= runs:
                    break

                if self._stop_event.wait(config.interval.next_seconds()):
                    break
        finally:
            self._running = False
            self._emit_status("Stopped")
            if self._on_stopped:
                self._on_stopped()
