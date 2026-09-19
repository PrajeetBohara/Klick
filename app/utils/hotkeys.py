"""Global hotkey listener."""

from __future__ import annotations

from typing import Callable

from pynput import keyboard


class HotkeyManager:
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_emergency_stop: Callable[[], None],
        toggle_key: str = "f6",
        emergency_key: str = "f7",
    ) -> None:
        self._on_toggle = on_toggle
        self._on_emergency_stop = on_emergency_stop
        self._toggle_key = toggle_key.lower()
        self._emergency_key = emergency_key.lower()
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def update_keys(self, toggle_key: str, emergency_key: str) -> None:
        self._toggle_key = toggle_key.lower()
        self._emergency_key = emergency_key.lower()

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        name = self._key_name(key)
        if name is None:
            return
        if name == self._toggle_key:
            self._on_toggle()
        elif name == self._emergency_key:
            self._on_emergency_stop()

    @staticmethod
    def _key_name(key: keyboard.Key | keyboard.KeyCode) -> str | None:
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char.lower()
        if isinstance(key, keyboard.Key):
            return key.name.lower() if key.name else None
        return None
