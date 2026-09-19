"""Interval and auto-stop timing helpers."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class DurationParts:
    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    milliseconds: int = 0

    def total_ms(self) -> int:
        total = (
            int(self.hours) * 3_600_000
            + int(self.minutes) * 60_000
            + int(self.seconds) * 1_000
            + int(self.milliseconds)
        )
        return max(total, 1)

    def total_seconds(self) -> float:
        return self.total_ms() / 1000.0

    def to_dict(self) -> dict[str, int]:
        return {
            "hours": int(self.hours),
            "minutes": int(self.minutes),
            "seconds": int(self.seconds),
            "milliseconds": int(self.milliseconds),
        }

    @classmethod
    def from_dict(cls, data: dict | None, fallback_ms: int = 100) -> DurationParts:
        data = data or {}
        return cls(
            hours=int(data.get("hours", 0) or 0),
            minutes=int(data.get("minutes", 0) or 0),
            seconds=int(data.get("seconds", 0) or 0),
            milliseconds=int(data.get("milliseconds", fallback_ms) or fallback_ms),
        )


@dataclass
class IntervalConfig:
    mode: str = "fixed"  # fixed | random
    fixed: DurationParts = field(default_factory=lambda: DurationParts(milliseconds=100))
    minimum: DurationParts = field(default_factory=lambda: DurationParts(milliseconds=50))
    maximum: DurationParts = field(default_factory=lambda: DurationParts(milliseconds=200))

    def next_seconds(self) -> float:
        if self.mode == "random":
            lo = self.minimum.total_ms()
            hi = self.maximum.total_ms()
            if hi < lo:
                lo, hi = hi, lo
            return random.randint(lo, max(hi, lo)) / 1000.0
        return self.fixed.total_seconds()

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "fixed": self.fixed.to_dict(),
            "minimum": self.minimum.to_dict(),
            "maximum": self.maximum.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> IntervalConfig:
        data = data or {}
        # Backward compat: flat hours/minutes/seconds/milliseconds
        if "fixed" not in data and any(
            key in data for key in ("hours", "minutes", "seconds", "milliseconds")
        ):
            fixed = DurationParts.from_dict(data, fallback_ms=int(data.get("milliseconds", 100)))
            return cls(mode="fixed", fixed=fixed, minimum=fixed, maximum=fixed)
        return cls(
            mode=str(data.get("mode", "fixed")),
            fixed=DurationParts.from_dict(data.get("fixed"), 100),
            minimum=DurationParts.from_dict(data.get("minimum"), 50),
            maximum=DurationParts.from_dict(data.get("maximum"), 200),
        )


@dataclass
class AutoStopConfig:
    enabled: bool = False
    hours: int = 0
    minutes: int = 0
    seconds: int = 30

    def duration_seconds(self) -> float | None:
        if not self.enabled:
            return None
        total = int(self.hours) * 3600 + int(self.minutes) * 60 + int(self.seconds)
        return float(total) if total > 0 else None

    def to_dict(self) -> dict:
        return {
            "enabled": bool(self.enabled),
            "hours": int(self.hours),
            "minutes": int(self.minutes),
            "seconds": int(self.seconds),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> AutoStopConfig:
        data = data or {}
        return cls(
            enabled=bool(data.get("enabled", False)),
            hours=int(data.get("hours", 0) or 0),
            minutes=int(data.get("minutes", 0) or 0),
            seconds=int(data.get("seconds", 30) or 30),
        )


def auto_stop_reached(started_at: float, auto_stop: AutoStopConfig, now: float) -> bool:
    limit = auto_stop.duration_seconds()
    if limit is None:
        return False
    return (now - started_at) >= limit


def ms_to_parts(total_ms: int) -> DurationParts:
    total_ms = max(1, int(total_ms))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, milliseconds = divmod(rem, 1_000)
    return DurationParts(
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds,
    )


def format_ms(total_ms: int) -> str:
    total_ms = max(0, int(total_ms))
    if total_ms < 1000:
        return f"{total_ms} ms"
    seconds = total_ms / 1000.0
    if seconds < 60:
        return f"{seconds:.2f} s ({total_ms} ms)"
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)}m {secs:.1f}s ({total_ms} ms)"
