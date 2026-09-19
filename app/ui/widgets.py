"""Reusable UI helpers."""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from app.ui.theme import COLORS, FONTS


def section_label(parent: ctk.CTkBaseClass, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text.upper(),
        font=FONTS["section"],
        text_color=COLORS["muted"],
        anchor="w",
    )


def field_label(parent: ctk.CTkBaseClass, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        font=FONTS["body"],
        text_color=COLORS["text"],
        anchor="w",
    )


def int_entry(
    parent: ctk.CTkBaseClass,
    width: int = 72,
    default: str = "0",
) -> ctk.CTkEntry:
    entry = ctk.CTkEntry(
        parent,
        width=width,
        height=34,
        font=FONTS["mono"],
        fg_color=COLORS["surface_alt"],
        border_color=COLORS["border"],
        text_color=COLORS["text"],
        justify="center",
    )
    entry.insert(0, default)
    return entry


def safe_int(value: str, fallback: int = 0, minimum: int = 0) -> int:
    try:
        return max(minimum, int(value.strip()))
    except (TypeError, ValueError):
        return fallback


def safe_float(value: str, fallback: float = 0.0, minimum: float = 0.0) -> float:
    try:
        return max(minimum, float(value.strip()))
    except (TypeError, ValueError):
        return fallback


class ToolTip:
    """Simple hover tooltip for CTk / Tk widgets."""

    def __init__(self, widget: Any, text: str = "") -> None:
        self.widget = widget
        self.text = text
        self._tip: tk.Toplevel | None = None
        self._after_id: str | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def set_text(self, text: str) -> None:
        self.text = text
        if self._tip is not None:
            self._hide()

    def _schedule(self, _event: Any = None) -> None:
        self._cancel()
        if not self.text:
            return
        self._after_id = self.widget.after(350, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        if self._tip is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        try:
            self._tip.attributes("-topmost", True)
        except Exception:
            pass
        label = tk.Label(
            self._tip,
            text=self.text,
            justify="left",
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 10),
            padx=10,
            pady=6,
        )
        label.pack()

    def _hide(self, _event: Any = None) -> None:
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None
