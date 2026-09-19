"""Unpredictable mouse jiggler engine."""

from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from pynput.mouse import Controller

from app.utils.timing import (
    AutoStopConfig,
    DurationParts,
    IntervalConfig,
    auto_stop_reached,
)


@dataclass
class JigglerConfig:
    radius_px: int = 40
    min_step_px: int = 2
    max_step_px: int = 18
    micro_moves: int = 3  # random sub-steps per jiggle burst
    interval: IntervalConfig = field(
        default_factory=lambda: IntervalConfig(
            mode="random",
            fixed=DurationParts(milliseconds=800),
            minimum=DurationParts(milliseconds=400),
            maximum=DurationParts(milliseconds=1800),
        )
    )
    start_delay: float = 0.0
    auto_stop: AutoStopConfig = field(default_factory=AutoStopConfig)
    keep_near_start: bool = True
    restore_on_stop: bool = True


class JigglerEngine:
    def __init__(
        self,
        on_tick: Callable[[int], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        on_stopped: Callable[[], None] | None = None,
    ) -> None:
        self._mouse = Controller()
        self._rng = random.SystemRandom()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._on_tick = on_tick
        self._on_status = on_status
        self._on_stopped = on_stopped
        self.move_count = 0
        self._origin: tuple[float, float] | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, config: JigglerConfig) -> None:
        if self._running:
            return
        self._stop_event.clear()
        self._running = True
        self.move_count = 0
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

    def _clamp_to_radius(
        self, x: float, y: float, ox: float, oy: float, radius: int
    ) -> tuple[float, float]:
        dx = x - ox
        dy = y - oy
        dist = math.hypot(dx, dy)
        if dist <= radius or dist == 0:
            return x, y
        scale = radius / dist
        return ox + dx * scale, oy + dy * scale

    def _next_target(
        self, config: JigglerConfig, ox: float, oy: float, cx: float, cy: float
    ) -> tuple[float, float]:
        radius = max(1, int(config.radius_px))
        # Occasionally drift back toward origin so path isn't a steady outward spiral
        if config.keep_near_start and self._rng.random() < 0.28:
            pull = self._rng.uniform(0.15, 0.85)
            tx = cx + (ox - cx) * pull + self._rng.uniform(-3, 3)
            ty = cy + (oy - cy) * pull + self._rng.uniform(-3, 3)
            return self._clamp_to_radius(tx, ty, ox, oy, radius)

        # Random angle + non-uniform distance for less predictable hops
        angle = self._rng.uniform(0, 2 * math.pi)
        unit = self._rng.random() ** self._rng.uniform(0.35, 2.2)
        max_dist = min(radius, max(int(config.max_step_px), int(config.min_step_px)))
        min_dist = min(int(config.min_step_px), max_dist)
        dist = min_dist + unit * max(max_dist - min_dist, 1)
        # Mix absolute-from-origin vs relative-from-current
        if self._rng.random() < 0.55:
            tx = cx + math.cos(angle) * dist
            ty = cy + math.sin(angle) * dist
        else:
            tx = ox + math.cos(angle) * self._rng.uniform(0, radius)
            ty = oy + math.sin(angle) * self._rng.uniform(0, radius)
        return self._clamp_to_radius(tx, ty, ox, oy, radius)

    def _jiggle_burst(self, config: JigglerConfig, ox: float, oy: float) -> None:
        cx, cy = self._mouse.position
        steps = self._rng.randint(1, max(1, int(config.micro_moves)))
        for _ in range(steps):
            if self._stop_event.is_set():
                return
            tx, ty = self._next_target(config, ox, oy, cx, cy)
            # Optional mid-point wobble so path isn't a straight line
            if self._rng.random() < 0.45:
                mx = (cx + tx) / 2 + self._rng.uniform(-4, 4)
                my = (cy + ty) / 2 + self._rng.uniform(-4, 4)
                mx, my = self._clamp_to_radius(mx, my, ox, oy, config.radius_px)
                self._mouse.position = (mx, my)
                if self._stop_event.wait(self._rng.uniform(0.008, 0.045)):
                    return
            self._mouse.position = (tx, ty)
            cx, cy = tx, ty
            if self._stop_event.wait(self._rng.uniform(0.01, 0.06)):
                return

    def _run(self, config: JigglerConfig) -> None:
        try:
            if config.start_delay > 0:
                self._emit_status(f"Jiggler starts in {config.start_delay:.1f}s…")
                if self._stop_event.wait(config.start_delay):
                    return

            ox, oy = self._mouse.position
            self._origin = (ox, oy)
            started_at = time.monotonic()
            self._emit_status("Jiggling")

            while not self._stop_event.is_set():
                if auto_stop_reached(started_at, config.auto_stop, time.monotonic()):
                    self._emit_status("Auto-stopped")
                    break

                self._jiggle_burst(config, ox, oy)
                self.move_count += 1
                if self._on_tick:
                    self._on_tick(self.move_count)

                if self._stop_event.wait(config.interval.next_seconds()):
                    break
        finally:
            if config.restore_on_stop and self._origin is not None:
                try:
                    self._mouse.position = self._origin
                except Exception:
                    pass
            self._running = False
            self._emit_status("Stopped")
            if self._on_stopped:
                self._on_stopped()
