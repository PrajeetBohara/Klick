"""Persisted user settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "clicker": {
        "action": "click",
        "interval": {
            "mode": "fixed",
            "fixed": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 100},
            "minimum": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 50},
            "maximum": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 200},
        },
        "button": "left",
        "click_type": "single",
        "position_mode": "current",
        "fixed_x": 0,
        "fixed_y": 0,
        "scroll_direction": "down",
        "scroll_amount": 3,
        "repeat_mode": "unlimited",
        "repeat_count": 10,
        "start_delay": 0.0,
        "auto_stop": {"enabled": False, "hours": 0, "minutes": 0, "seconds": 30},
    },
    "typer": {
        "text": "",
        "interval": {
            "mode": "fixed",
            "fixed": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 50},
            "minimum": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 30},
            "maximum": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 120},
        },
        "unit_mode": "character",
        "repeat_mode": "once",
        "repeat_count": 1,
        "start_delay": 2.0,
        "press_enter": False,
        "auto_stop": {"enabled": False, "hours": 0, "minutes": 0, "seconds": 30},
    },
    "combo": {
        "steps": [],
        "interval": {
            "mode": "fixed",
            "fixed": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 200},
            "minimum": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 100},
            "maximum": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 400},
        },
        "repeat_mode": "once",
        "repeat_count": 1,
        "start_delay": 2.0,
        "auto_stop": {"enabled": False, "hours": 0, "minutes": 0, "seconds": 30},
    },
    "jiggler": {
        "radius_px": 40,
        "min_step_px": 2,
        "max_step_px": 18,
        "micro_moves": 3,
        "interval": {
            "mode": "random",
            "fixed": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 800},
            "minimum": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 400},
            "maximum": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 1800},
        },
        "start_delay": 0.0,
        "auto_stop": {"enabled": False, "hours": 0, "minutes": 0, "seconds": 30},
        "keep_near_start": True,
        "restore_on_stop": True,
    },
    "hotkeys": {
        "toggle": "f6",
        "emergency_stop": "f7",
    },
    "ui": {
        "theme": "dark",
        "active_tab": "clicker",
    },
}


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        base = Path.home() / ".klick"
        base.mkdir(parents=True, exist_ok=True)
        self.path = path or (base / "settings.json")
        self.data: dict[str, Any] = self._deep_merge(DEFAULTS, self._load())

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            return loaded if isinstance(loaded, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2)

    def get_section(self, name: str) -> dict[str, Any]:
        section = self.data.get(name, {})
        return section if isinstance(section, dict) else {}

    def update_section(self, name: str, values: dict[str, Any]) -> None:
        current = self.get_section(name)
        current.update(values)
        self.data[name] = current
        self.save()

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in base.items():
            if isinstance(value, dict):
                nested = override.get(key, {})
                result[key] = SettingsStore._deep_merge(
                    value, nested if isinstance(nested, dict) else {}
                )
            else:
                result[key] = override.get(key, value)
        for key, value in override.items():
            if key not in result:
                result[key] = value
        return result
