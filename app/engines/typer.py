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


def type_units(text: str, mode: str) -> list[str]:
    if mode == "word":
        parts = text.split(" ")
        units: list[str] = []
        for index, part in enumerate(parts):
            units.append(part)
            if index < len(parts) - 1:
                units.append(" ")
        return units
    return list(text)


def average_interval_seconds(interval: IntervalConfig) -> float:
    if interval.mode == "random":
        lo = interval.minimum.total_ms()
        hi = interval.maximum.total_ms()
        if hi < lo:
            lo, hi = hi, lo
        return ((lo + hi) / 2.0) / 1000.0
    return interval.fixed.total_seconds()


def estimate_typing_seconds(config: TyperConfig) -> float | None:
    """
    Estimated active typing duration (intervals between units), not including start delay.
    Returns None when unlimited (no finish time).
    """
    text = config.text
    if not text:
        return 0.0
    units = type_units(text, config.unit_mode)
    if not units:
        return 0.0

    if config.repeat_mode == "once":
        runs = 1
    elif config.repeat_mode == "count":
        runs = max(1, int(config.repeat_count))
    else:
        return None

    # Wait after each unit except we still count n waits in current engine;
    # estimate uses (units * runs) intervals which matches current wait-after-each behavior.
    unit_count = len(units) * runs
    avg = average_interval_seconds(config.interval)
    enter_extra = 0.0  # Enter is instant relative to intervals
    between_runs = max(0, runs - 1) * avg
    # Engine waits after each unit except the final unit of a finite run
    waits = max(0, unit_count - 1)
    return waits * avg + enter_extra + between_runs


def format_duration(seconds: float) -> str:
    seconds = max(0.0, seconds)
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    return f"{minutes}m {secs:02d}s"


class TyperEngine:
    def __init__(
        self,
        on_tick: Callable[[int], None] | None = None,
        on_progress: Callable[[int, int, float | None], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        on_stopped: Callable[[], None] | None = None,
    ) -> None:
        self._keyboard = Controller()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._on_tick = on_tick
        self._on_progress = on_progress
        self._on_status = on_status
        self._on_stopped = on_stopped
        self.key_count = 0
        self.units_done = 0
        self.units_total = 0

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
        self.units_done = 0
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

    def _emit_progress(self, done: int, total: int, eta: float | None) -> None:
        if self._on_progress:
            self._on_progress(done, total, eta)

    def _run(self, config: TyperConfig) -> None:
        completed_cleanly = False
        try:
            units = type_units(config.text, config.unit_mode)

            if config.repeat_mode == "once":
                runs = 1
            elif config.repeat_mode == "unlimited":
                runs = None
            else:
                runs = max(1, int(config.repeat_count))

            total_units = len(units) * runs if runs is not None else 0
            self.units_total = total_units
            avg = average_interval_seconds(config.interval)

            if config.start_delay > 0:
                delay_left = float(config.start_delay)
                self._emit_status(f"Starts in {format_duration(delay_left)}")
                # Tick start-delay countdown roughly every 0.2s
                while delay_left > 0 and not self._stop_event.is_set():
                    step = min(0.2, delay_left)
                    if self._stop_event.wait(step):
                        return
                    delay_left -= step
                    typing_eta = estimate_typing_seconds(config)
                    total_eta = delay_left + (typing_eta or 0.0)
                    self._emit_progress(0, total_units, total_eta if runs is not None else None)
                    self._emit_status(f"Starts in {format_duration(delay_left)}")

            if self._stop_event.is_set():
                return

            started_at = time.monotonic()
            self._emit_status("Typing")
            completed_runs = 0
            done_units = 0

            while not self._stop_event.is_set():
                if auto_stop_reached(started_at, config.auto_stop, time.monotonic()):
                    self._emit_status("Auto-stopped")
                    break

                for index, unit in enumerate(units):
                    if self._stop_event.is_set():
                        break
                    if auto_stop_reached(started_at, config.auto_stop, time.monotonic()):
                        self._emit_status("Auto-stopped")
                        return

                    self._keyboard.type(unit)
                    self.key_count += len(unit)
                    done_units += 1
                    self.units_done = done_units
                    if self._on_tick:
                        self._on_tick(self.key_count)

                    remaining_units = (
                        max(0, total_units - done_units) if runs is not None else None
                    )
                    eta = (
                        remaining_units * avg if remaining_units is not None else None
                    )
                    self._emit_progress(done_units, total_units, eta)

                    # No trailing wait after the very last unit of a finite run
                    is_last_unit = (
                        runs is not None
                        and completed_runs == runs - 1
                        and index == len(units) - 1
                    )
                    if not is_last_unit:
                        if self._stop_event.wait(config.interval.next_seconds()):
                            break

                if self._stop_event.is_set():
                    break

                if config.press_enter:
                    self._keyboard.press(Key.enter)
                    self._keyboard.release(Key.enter)

                completed_runs += 1
                if runs is not None and completed_runs >= runs:
                    completed_cleanly = True
                    break

                if self._stop_event.wait(config.interval.next_seconds()):
                    break
        finally:
            self._running = False
            if completed_cleanly:
                self._emit_status("Completed")
                self._emit_progress(self.units_total, self.units_total, 0.0)
            else:
                self._emit_status("Stopped")
            if self._on_stopped:
                self._on_stopped()
